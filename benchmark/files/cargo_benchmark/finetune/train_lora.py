#!/usr/bin/env python3
"""LoRA fine-tuning of a Qwen2.5-Coder Instruct model on the cargo benchmark (runs on the GPU cluster).

    python finetune/train_lora.py --condition A --model Qwen/Qwen2.5-Coder-7B-Instruct --out finetune/runs/A-7b
    python finetune/train_lora.py --condition B --model Qwen/Qwen2.5-Coder-1.5B-Instruct --out finetune/runs/B-1.5b
    python finetune/train_lora.py --condition A --model ... --out ... --max-steps 20      # quick smoke test

Data: finetune/data/<condition>/{train,dev}.jsonl from finetune/build_dataset.py. Each row is a chat with one user
message (the benchmark prompt) and one assistant message (the answer). The text is formatted with the model's own
chat template, and the loss is computed on the assistant answer only (prompt tokens get label -100).

Defaults follow the fine-tuning plan: LoRA r=16, alpha=32, dropout=0.05 on all attention and MLP projections,
learning rate 2e-4 with cosine decay and 3% warm-up, 3 epochs, effective batch 16 (1 x 16 gradient accumulation),
bf16, gradient checkpointing, seed 42. The dev set is evaluated after every epoch and the epoch with the lowest dev
loss is kept (load_best_model_at_end).

Writes to --out:
  adapter/            the LoRA adapter (+ tokenizer) of the best epoch: input for predict_hf.py and merge_lora.py
  run_config.json     all settings, dataset sizes, token-length statistics, library versions
  trainer_state.json  loss curves (train and dev)

Requirements: see finetune/requirements.txt (torch, transformers, peft, accelerate; bitsandbytes for --load-in-4bit).
"""
import argparse
import json
import os
import random
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def read_jsonl(path, variants):
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(l) for l in f if l.strip()]
    return [r for r in rows if r["variant"] in variants]


def encode(tok, messages, max_len):
    """input_ids and labels for one chat; labels are -100 on the prompt, so only the answer is learned."""
    prompt_ids = tok.apply_chat_template(messages[:-1], tokenize=True, add_generation_prompt=True)
    full_ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=False)
    if hasattr(prompt_ids, "keys"):                                 # some versions return a BatchEncoding
        prompt_ids, full_ids = prompt_ids["input_ids"], full_ids["input_ids"]
    if full_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("chat template: the prompt is not a prefix of the full conversation")
    answer = list(full_ids[len(prompt_ids):])
    # Qwen's template ends a turn with "<|im_end|>\n": learn to stop at <|im_end|>, drop what follows it.
    end_id = tok.convert_tokens_to_ids("<|im_end|>")
    if end_id in answer:
        answer = answer[:len(answer) - answer[::-1].index(end_id)]
    elif tok.eos_token_id is not None:
        answer.append(tok.eos_token_id)
    ids = list(prompt_ids) + answer
    labels = [-100] * len(prompt_ids) + answer
    return {"input_ids": ids, "labels": labels, "too_long": len(ids) > max_len}


class Collator:
    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, batch):
        import torch
        n = max(len(b["input_ids"]) for b in batch)
        ids = [b["input_ids"] + [self.pad_id] * (n - len(b["input_ids"])) for b in batch]
        lab = [b["labels"] + [-100] * (n - len(b["labels"])) for b in batch]
        att = [[1] * len(b["input_ids"]) + [0] * (n - len(b["input_ids"])) for b in batch]
        return {"input_ids": torch.tensor(ids), "labels": torch.tensor(lab), "attention_mask": torch.tensor(att)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--condition", choices=["A", "B"], required=True)
    ap.add_argument("--model", default="Qwen/Qwen2.5-Coder-7B-Instruct", help="HF hub id or local path")
    ap.add_argument("--data", default=os.path.join(HERE, "data"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--variants", default="normal,mixed,cryptic", help="train on these schema variants")
    ap.add_argument("--epochs", type=float, default=3)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=16)
    ap.add_argument("--max-len", type=int, default=6144, help="longest example in tokens (the data is about 4.5k max)")
    ap.add_argument("--lora-r", type=int, default=16)
    ap.add_argument("--lora-alpha", type=int, default=32)
    ap.add_argument("--lora-dropout", type=float, default=0.05)
    ap.add_argument("--warmup-ratio", type=float, default=0.03)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--load-in-4bit", action="store_true", help="QLoRA: 4-bit base model (needs bitsandbytes)")
    ap.add_argument("--no-gradient-checkpointing", action="store_true")
    ap.add_argument("--max-steps", type=int, default=-1, help="stop after this many optimizer steps (smoke test)")
    ap.add_argument("--attn", default="sdpa", help="attn_implementation: sdpa (default), flash_attention_2, eager")
    a = ap.parse_args()

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer, Trainer, TrainingArguments, set_seed
    import peft
    from peft import LoraConfig, get_peft_model

    set_seed(a.seed)
    random.seed(a.seed)
    variants = [v for v in a.variants.split(",") if v]
    tok = AutoTokenizer.from_pretrained(a.model)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token

    data = {}
    for part in ("train", "dev"):
        rows = read_jsonl(os.path.join(a.data, a.condition, f"{part}.jsonl"), variants)
        enc = [encode(tok, r["messages"], a.max_len) for r in rows]
        long = sum(e["too_long"] for e in enc)
        if long:
            sys.exit(f"{part}: {long} examples are longer than --max-len {a.max_len}; raise --max-len")
        data[part] = [{"input_ids": e["input_ids"], "labels": e["labels"]} for e in enc]
    lengths = [len(e["input_ids"]) for e in data["train"]]
    answer = [sum(l != -100 for l in e["labels"]) for e in data["train"]]
    print(f"train {len(data['train'])} / dev {len(data['dev'])} examples; tokens per example: mean "
          f"{statistics.mean(lengths):.0f}, max {max(lengths)}; answer tokens: mean {statistics.mean(answer):.0f}, "
          f"max {max(answer)}", flush=True)

    bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if bf16 else torch.float16
    kw = dict(torch_dtype=dtype, attn_implementation=a.attn)
    if a.load_in_4bit:
        from transformers import BitsAndBytesConfig
        kw["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                                       bnb_4bit_compute_dtype=dtype, bnb_4bit_use_double_quant=True)
    model = AutoModelForCausalLM.from_pretrained(a.model, **kw)
    model.config.use_cache = False
    if a.load_in_4bit:
        model = peft.prepare_model_for_kbit_training(model, use_gradient_checkpointing=not a.no_gradient_checkpointing)
    elif not a.no_gradient_checkpointing:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    lora = LoraConfig(r=a.lora_r, lora_alpha=a.lora_alpha, lora_dropout=a.lora_dropout, bias="none",
                      task_type="CAUSAL_LM",
                      target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"])
    model = get_peft_model(model, lora)
    model.print_trainable_parameters()

    args = TrainingArguments(
        output_dir=a.out, num_train_epochs=a.epochs, max_steps=a.max_steps,
        per_device_train_batch_size=a.batch_size, per_device_eval_batch_size=a.batch_size,
        gradient_accumulation_steps=a.grad_accum, learning_rate=a.lr, lr_scheduler_type="cosine",
        warmup_ratio=a.warmup_ratio, weight_decay=0.0, bf16=bf16, fp16=not bf16,
        logging_steps=5, eval_strategy="epoch" if a.max_steps < 0 else "steps",
        save_strategy="epoch" if a.max_steps < 0 else "steps",
        eval_steps=None if a.max_steps < 0 else a.max_steps, save_steps=None if a.max_steps < 0 else a.max_steps,
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        save_total_limit=2, report_to="none", seed=a.seed, data_seed=a.seed,
        gradient_checkpointing=False,              # already enabled on the model above
        remove_unused_columns=False, group_by_length=False, dataloader_num_workers=2)
    trainer = Trainer(model=model, args=args, train_dataset=data["train"], eval_dataset=data["dev"],
                      data_collator=Collator(tok.pad_token_id))
    trainer.train()
    best = trainer.evaluate()
    adapter_dir = os.path.join(a.out, "adapter")
    trainer.model.save_pretrained(adapter_dir)
    tok.save_pretrained(adapter_dir)
    trainer.state.save_to_json(os.path.join(a.out, "trainer_state.json"))
    cfg = dict(vars(a), variants=variants, train_examples=len(data["train"]), dev_examples=len(data["dev"]),
               tokens_mean=statistics.mean(lengths), tokens_max=max(lengths), best_dev_loss=best.get("eval_loss"),
               best_checkpoint=trainer.state.best_model_checkpoint, bf16=bf16,
               versions={"torch": torch.__version__, "transformers": transformers.__version__,
                         "peft": peft.__version__})
    json.dump(cfg, open(os.path.join(a.out, "run_config.json"), "w"), indent=2)
    print(f"best dev loss {best.get('eval_loss')}; adapter -> {adapter_dir}")


if __name__ == "__main__":
    main()
