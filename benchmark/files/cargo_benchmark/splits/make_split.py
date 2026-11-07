#!/usr/bin/env python3
"""Make the 80/20 train/test split of the 960 questions for fine-tuning.

The split is made on BASE questions, not on single questions: the 4 phrasings of a base question (casual,
schema_aware, business_executive, vague) and its 3 schema variants share one Gold result, so they must all be on
the same side. Otherwise the model would see the answer of a test question during training.

  240 base questions = 80 easy + 80 moderate + 80 hard
  test   48 bases (20%) = 16 per difficulty                -> 192 questions per variant
  train 192 bases (80%) = 64 per difficulty, of which
        dev 21 bases = 7 per difficulty (held out from training, used for early stopping / choosing the epoch)
        train 171 bases = 57 per difficulty               -> 684 questions per variant

Inside each difficulty the test bases are drawn half from the first 40 bases (01-40, the original 480-question
set) and half from the new ones (41-80), so results on the old questions stay comparable. Seeded, so it is
reproducible: re-running gives the same split.

Writes splits/split_80_20.json:
  {"seed", "counts", "bases": {"train": [...], "dev": [...], "test": [...]},
   "questions": {"train": [...], "dev": [...], "test": [...]}}      (question ids such as "E07-BIZ")

Usage (from the cargo_benchmark folder):
  python splits/make_split.py            # writes the file
  python splits/check_split.py           # checks it (no leaks, sizes, balance)
"""
import argparse
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "split_80_20.json")
DIFFS = (("E", "easy"), ("M", "moderate"), ("H", "hard"))
TEST_PER_HALF = 8      # per difficulty: 8 from 01-40 + 8 from 41-80 = 16
DEV_PER_DIFF = 7


def make(seed):
    questions = json.load(open(os.path.join(ROOT, "questions", "questions_normal.json"), encoding="utf-8"))
    bases = sorted({q["base_id"] for q in questions})
    rng = random.Random(seed)
    split = {"train": [], "dev": [], "test": []}
    for letter, _ in DIFFS:
        old = [b for b in bases if b[0] == letter and int(b[1:]) <= 40]
        new = [b for b in bases if b[0] == letter and int(b[1:]) > 40]
        test = rng.sample(old, TEST_PER_HALF) + rng.sample(new, TEST_PER_HALF)
        rest = [b for b in old + new if b not in test]
        dev = rng.sample(rest, DEV_PER_DIFF)
        split["test"] += sorted(test)
        split["dev"] += sorted(dev)
        split["train"] += sorted(b for b in rest if b not in dev)
    by_base = {}
    for q in questions:
        by_base.setdefault(q["base_id"], []).append(q["id"])
    qsplit = {k: sorted(i for b in v for i in by_base[b]) for k, v in split.items()}
    counts = {k: {"bases": len(v), "questions_per_variant": len(qsplit[k]),
                  **{d: sum(b[0] == letter for b in v) for letter, d in DIFFS}} for k, v in split.items()}
    return {"seed": seed, "note": "split by base question; all 4 phrasings and all 3 schema variants of a base "
                                  "question are on the same side", "counts": counts,
            "bases": split, "questions": qsplit}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=491)
    ap.add_argument("--out", default=OUT)
    a = ap.parse_args()
    s = make(a.seed)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(s, f, indent=1)
    for k, c in s["counts"].items():
        print(f"{k:5s} {c['bases']:3d} bases ({c['easy']} easy, {c['moderate']} moderate, {c['hard']} hard) "
              f"-> {c['questions_per_variant']} questions per variant")
    print(f"-> {os.path.relpath(a.out, ROOT)}")


if __name__ == "__main__":
    main()
