#!/usr/bin/env python3
"""Check splits/split_80_20.json.

  1. train, dev and test share no base question and no question id
  2. together they cover all 240 base questions and all 960 question ids, with 4 phrasings per base
  3. sizes: test 48 bases (16 per difficulty, 8 from 01-40 and 8 from 41-80), dev 21 (7 per difficulty), train 171
  4. every style is equally present in each part (each base brings all 4 styles)
  5. no Gold query of a test base also appears as the Gold query of a train/dev base (exact text, all 3 variants)
  6. the file is what make_split.py produces with the stored seed (nobody edited it by hand)

Usage: python splits/check_split.py
"""
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_split  # noqa: E402

fails = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + ("" if ok else f"  {detail}"))
    if not ok:
        fails.append(label)


def main():
    s = json.load(open(make_split.OUT, encoding="utf-8"))
    b, q = s["bases"], s["questions"]
    parts = ("train", "dev", "test")
    for i, x in enumerate(parts):
        for y in parts[i + 1:]:
            check(f"no base question in both {x} and {y}", not set(b[x]) & set(b[y]), sorted(set(b[x]) & set(b[y]))[:5])
            check(f"no question id in both {x} and {y}", not set(q[x]) & set(q[y]))
    questions = json.load(open(os.path.join(ROOT, "questions", "questions_normal.json"), encoding="utf-8"))
    all_bases = {x["base_id"] for x in questions}
    check("all 240 base questions covered", set().union(*map(set, b.values())) == all_bases and len(all_bases) == 240)
    check("all 960 question ids covered", set().union(*map(set, q.values())) == {x["id"] for x in questions})
    for p in parts:
        check(f"{p}: 4 question ids per base", len(q[p]) == 4 * len(b[p]))
    want = {"train": 57, "dev": 7, "test": 16}
    for p in parts:
        per = collections.Counter(x[0] for x in b[p])
        check(f"{p}: {want[p]} bases per difficulty", all(per[d] == want[p] for d in "EMH"), dict(per))
    for d in "EMH":
        old = sum(1 for x in b["test"] if x[0] == d and int(x[1:]) <= 40)
        check(f"test {d}: 8 bases from 01-40 and 8 from 41-80", old == 8, old)
    style_of = {x["id"]: x["style"] for x in questions}
    for p in parts:
        c = collections.Counter(style_of[i] for i in q[p])
        check(f"{p}: the 4 styles are equally present", len(set(c.values())) == 1, dict(c))
    for v in ("normal", "mixed", "cryptic"):
        qs = json.load(open(os.path.join(ROOT, "questions", f"questions_{v}.json"), encoding="utf-8"))
        gold = collections.defaultdict(set)
        for x in qs:
            gold[x["gold_sql"]].add(x["base_id"])
        test = set(b["test"])
        shared = [g for g, bs in gold.items() if bs & test and bs - test]
        check(f"{v}: no Gold query shared between a test base and a train/dev base", not shared)
    again = make_split.make(s["seed"])
    check("file equals make_split.py output for its seed", again["bases"] == b and again["questions"] == q)
    print("\nRESULT: " + ("SPLIT OK" if not fails else f"{len(fails)} FAILED"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
