#!/usr/bin/env python3
"""Merge a LoRA adapter into its base model and save a normal Hugging Face model folder (input for export_gguf.sh).

    python finetune/merge_lora.py --model Qwen/Qwen2.5-Coder-7B-Instruct \
        --adapter finetune/runs/A-7b/adapter --out finetune/runs/A-7b/merged

The merge is done in bf16 on the CPU by default (no GPU needed; about 2x the model size in RAM, ~32 GB for 7B).
"""
import argparse


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", required=True)
    ap.add_argument("--adapter", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cpu", help="cpu (default) or auto")
    a = ap.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    base = AutoModelForCausalLM.from_pretrained(a.model, torch_dtype=torch.bfloat16, device_map=a.device)
    merged = PeftModel.from_pretrained(base, a.adapter).merge_and_unload()
    merged.save_pretrained(a.out, safe_serialization=True)
    AutoTokenizer.from_pretrained(a.adapter).save_pretrained(a.out)
    print(f"merged model -> {a.out}")


if __name__ == "__main__":
    main()
