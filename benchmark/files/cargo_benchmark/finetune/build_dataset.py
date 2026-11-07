#!/usr/bin/env python3
"""Build the fine-tuning datasets (chat JSONL) from the questions, hints and the 80/20 split.

Two conditions (see the fine-tuning plan):
  A  "SQL only"      user = the benchmark prompt            assistant = the Gold SQL (one line)
  B  "hint + SQL"    user = the benchmark prompt in hint mode assistant = the hint without its #question line:
                                                                         #schema / #think / #trace / #sql <Gold SQL>
The user prompt is built by evaluation/run_ollama.py (build_prompt, compact schema), the same function that is used
at test time, so the model is trained on exactly the prompt it will see later.

Output (default finetune/data/):
  A/train.jsonl  A/dev.jsonl  A/test.jsonl   B/train.jsonl  B/dev.jsonl  B/test.jsonl
One line per (question, variant):
  {"id": "E07-BIZ", "base_id": "E07", "variant": "mixed", "difficulty": "easy", "style": "business_executive",
   "condition": "A", "messages": [{"role": "user", "content": ...}, {"role": "assistant", "content": ...}]}
test.jsonl rows have only the user message (the answer is never written into a test file) plus "gold_sql" for
reference; scoring is done by evaluation/evaluate.py on the database.

Sizes with the default split (all three variants): train 684 x 3 = 2052 rows, dev 84 x 3 = 252, test 192 x 3 = 576
per condition.

Usage (from the cargo_benchmark folder; standard library only):
  python finetune/build_dataset.py                          # A and B, all variants
  python finetune/build_dataset.py --conditions A --variants normal
  python finetune/build_dataset.py --stats                  # also print length statistics (chars, ~tokens)
"""
import argparse
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "evaluation"))
from run_ollama import build_prompt, compact_schema  # noqa: E402

VARIANTS = ("normal", "mixed", "cryptic")
PARTS = ("train", "dev", "test")


def schema_for(variant):
    db = os.path.join(ROOT, "databases", f"cargo_{variant}.db")
    ddl = os.path.join(ROOT, "schema", "schema.sql" if variant == "normal" else f"schema_{variant}.sql")
    return compact_schema(db, ddl)


def hint_target(hint_text):
    """The hint without its first line (#question repeats the prompt and is not something to learn)."""
    lines = hint_text.split("\n")
    assert lines[0].startswith("#question ") and lines[1].startswith("#schema ") and lines[-1].startswith("#sql "), \
        "unexpected hint format"
    return "\n".join(lines[1:])


def load_hints(variant):
    with open(os.path.join(ROOT, "hints", f"hints_{variant}.jsonl"), encoding="utf-8") as f:
        return {h["id"]: h["hint"] for h in map(json.loads, f) if h}


def build(conditions, variants, split_path):
    split = json.load(open(split_path, encoding="utf-8"))
    part_of = {qid: p for p in PARTS for qid in split["questions"][p]}
    rows = {(c, p): [] for c in conditions for p in PARTS}
    for v in variants:
        schema = schema_for(v)
        questions = json.load(open(os.path.join(ROOT, "questions", f"questions_{v}.json"), encoding="utf-8"))
        hints = load_hints(v) if "B" in conditions else {}
        for q in questions:
            part = part_of[q["id"]]
            meta = {"id": q["id"], "base_id": q["base_id"], "variant": v, "difficulty": q["difficulty"],
                    "style": q["style"]}
            for c in conditions:
                prompt = build_prompt(schema, "", q, False, "hint" if c == "B" else "none")
                row = dict(meta, condition=c, messages=[{"role": "user", "content": prompt}])
                if part == "test":
                    row["gold_sql"] = q["gold_sql"]
                else:
                    answer = q["gold_sql"] if c == "A" else hint_target(hints[q["id"]])
                    if c == "B":
                        assert answer.endswith("#sql " + q["gold_sql"]), q["id"]
                    row["messages"].append({"role": "assistant", "content": answer})
                rows[(c, part)].append(row)
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conditions", default="A,B", help="comma list of A and/or B")
    ap.add_argument("--variants", default=",".join(VARIANTS), help="comma list of normal, mixed, cryptic")
    ap.add_argument("--split", default=os.path.join(ROOT, "splits", "split_80_20.json"))
    ap.add_argument("--out", default=os.path.join(HERE, "data"))
    ap.add_argument("--stats", action="store_true", help="print length statistics")
    a = ap.parse_args()
    conditions = [c.strip().upper() for c in a.conditions.split(",") if c.strip()]
    variants = [v.strip() for v in a.variants.split(",") if v.strip()]
    assert set(conditions) <= {"A", "B"} and set(variants) <= set(VARIANTS), "unknown condition or variant"

    rows = build(conditions, variants, a.split)
    for (c, p), rs in sorted(rows.items()):
        d = os.path.join(a.out, c)
        os.makedirs(d, exist_ok=True)
        path = os.path.join(d, f"{p}.jsonl")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            for r in rs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        line = f"{c}/{p}.jsonl: {len(rs)} rows"
        if a.stats and rs:
            total = [sum(len(m["content"]) for m in r["messages"]) for r in rs]
            ans = [len(r["messages"][1]["content"]) for r in rs if len(r["messages"]) > 1]
            line += (f"   chars: mean {statistics.mean(total):.0f}, max {max(total)} (~{max(total) / 3.2:.0f} tokens)"
                     + (f"; answer mean {statistics.mean(ans):.0f}, max {max(ans)}" if ans else ""))
        print(line)
    print(f"-> {os.path.relpath(a.out, ROOT)}  (variants: {', '.join(variants)})")


if __name__ == "__main__":
    main()
