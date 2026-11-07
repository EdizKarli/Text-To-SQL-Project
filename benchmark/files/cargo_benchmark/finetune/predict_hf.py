#!/usr/bin/env python3
"""Answer the benchmark questions with a Hugging Face model on the cluster (base model, or base model + LoRA adapter)
and write prediction files that evaluation/evaluate.py scores, in the same format as evaluation/run_ollama.py.

    # base model (the "before" numbers on the same test questions)
    python finetune/predict_hf.py --model Qwen/Qwen2.5-Coder-7B-Instruct --variant normal --split test
    # fine-tuned, condition A (SQL only) and condition B (hint, then SQL)
    python finetune/predict_hf.py --model Qwen/Qwen2.5-Coder-7B-Instruct --adapter finetune/runs/A-7b/adapter \
        --variant cryptic --split test --tag A-7b
    python finetune/predict_hf.py --model Qwen/Qwen2.5-Coder-7B-Instruct --adapter finetune/runs/B-7b/adapter \
        --variant cryptic --split test --reasoning hint --tag B-7b
    # then score (on the cluster or locally):
    python evaluation/evaluate.py evaluation/predictions/pred_cryptic_B-7b_hf_hint_test.json --variant cryptic --split test

The prompt is build_prompt() from evaluation/run_ollama.py (compact schema, no answer spec), formatted with the
model's chat template, decoded greedily. The SQL is taken from the answer (after the last '#sql' with
--reasoning hint). pred_<tag>_raw.json stores the raw text, generated tokens (eval_count), prompt tokens and the
wall-clock time per question. With --batch-size > 1 the time of a batch is shared equally by its questions, so use
--batch-size 1 when latency matters; latency on a cluster GPU is not comparable with Ollama on a laptop.
"""
import argparse
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
from run_ollama import build_prompt, compact_schema, extract_sql, load_split  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True, help="base model (HF id or path), or a merged model")
    ap.add_argument("--adapter", help="LoRA adapter folder from train_lora.py (omit for the base model)")
    ap.add_argument("--variant", choices=["normal", "mixed", "cryptic"], required=True)
    ap.add_argument("--split", choices=["train", "dev", "test", "all"], default="test")
    ap.add_argument("--reasoning", choices=["none", "hint"], default="none")
    ap.add_argument("--max-new-tokens", type=int, default=None, help="default 512, or 1536 with --reasoning hint")
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--tag", help="name used in the output file (default: model name, + '-lora' with an adapter)")
    ap.add_argument("--out", help="predictions file (default evaluation/predictions/pred_<variant>_<tag>_hf[_hint]_<split>.json)")
    ap.add_argument("--limit", type=int, help="only the first N questions (smoke test)")
    a = ap.parse_args()

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    db = os.path.join(ROOT, "databases", f"cargo_{a.variant}.db")
    ddl = os.path.join(ROOT, "schema", "schema.sql" if a.variant == "normal" else f"schema_{a.variant}.sql")
    schema = compact_schema(db, ddl)
    questions = json.load(open(os.path.join(ROOT, "questions", f"questions_{a.variant}.json"), encoding="utf-8"))
    if a.split != "all":
        keep = load_split(a.split)
        questions = [q for q in questions if q["id"] in keep]
    if a.limit:
        questions = questions[:a.limit]
    max_new = a.max_new_tokens or (1536 if a.reasoning == "hint" else 512)

    tag = a.tag or (re.sub(r"[^A-Za-z0-9.]+", "-", os.path.basename(a.model.rstrip("/"))) + ("-lora" if a.adapter else ""))
    out = a.out or os.path.join(ROOT, "evaluation", "predictions",
                                f"pred_{a.variant}_{tag}_hf" + ("_hint" if a.reasoning == "hint" else "")
                                + ("" if a.split == "all" else f"_{a.split}") + ".json")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    tok = AutoTokenizer.from_pretrained(a.adapter or a.model)
    tok.padding_side = "left"
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    dtype = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16
    model = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=dtype, device_map="auto")
    if a.adapter:
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, a.adapter)
    model.eval()
    stop = [i for i in {tok.eos_token_id, tok.convert_tokens_to_ids("<|im_end|>")} if isinstance(i, int) and i >= 0]

    preds = {}
    raw_log = {"_run": dict(variant=a.variant, model=a.model, adapter=a.adapter, schema="compact", evidence=False,
                            with_spec=False, reasoning=a.reasoning, split=a.split, backend="transformers",
                            max_new_tokens=max_new, batch_size=a.batch_size, greedy=True)}
    for k in range(0, len(questions), a.batch_size):
        batch = questions[k:k + a.batch_size]
        texts = [tok.apply_chat_template([{"role": "user", "content": build_prompt(schema, "", q, False, a.reasoning)}],
                                         tokenize=False, add_generation_prompt=True) for q in batch]
        enc = tok(texts, return_tensors="pt", padding=True).to(model.device)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        t0 = time.time()
        with torch.no_grad():
            gen = model.generate(**enc, max_new_tokens=max_new, do_sample=False, temperature=None, top_p=None,
                                 top_k=None, eos_token_id=stop, pad_token_id=tok.pad_token_id)
        if torch.cuda.is_available():
            torch.cuda.synchronize()
        wall = (time.time() - t0) / len(batch)
        for i, q in enumerate(batch):
            new = gen[i, enc["input_ids"].shape[1]:].tolist()
            n_new = next((j for j, t in enumerate(new) if t in stop), len(new))
            raw = tok.decode(new[:n_new], skip_special_tokens=True)
            preds[q["id"]] = extract_sql(raw, a.reasoning)
            raw_log[q["id"]] = {"raw": raw, "error": None if n_new < max_new else "hit max_new_tokens",
                                "latency_s": round(wall, 3), "eval_count": n_new, "eval_duration_s": round(wall, 3),
                                "prompt_eval_count": int(enc["attention_mask"][i].sum()),
                                "prompt_eval_duration_s": None, "load_duration_s": None, "total_duration_s": round(wall, 3)}
        print(f"[{min(k + a.batch_size, len(questions))}/{len(questions)}] {batch[-1]['id']} {wall:.2f}s  "
              f"{preds[batch[-1]['id']][:90]}", flush=True)
        json.dump(preds, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        json.dump(raw_log, open(out[:-5] + "_raw.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nPredictions -> {out}\nScore with: python evaluation/evaluate.py {os.path.relpath(out, ROOT)} "
          f"--variant {a.variant}" + ("" if a.split == "all" else f" --split {a.split}"))


if __name__ == "__main__":
    main()
