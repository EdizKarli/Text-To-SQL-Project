"""
error_breakdown.py: splits the wrong answers of a BIRD run into groups, so we can see
whether the SQL failed to run at all or ran and gave the wrong result.

Groups:
  correct        the result matches the gold result (same rule as the BIRD EX script)
  wrong_result   the SQL ran but returned a different result
  exec_error     the SQL did not run (SQLite error); split further by error type
  timeout        the SQL ran longer than --timeout seconds
  no_answer      the model never answered (Ediz's script wrote "SELECT 1")

Usage (from the folder that has data/ and mini_dev_data/):
  python error_breakdown.py results_yigit/predict_schema_qwen2.5-1.5b-instruct-q8_0.json
  python error_breakdown.py results_yigit/predict_schema_*.json      (several files, one table)
"""
import argparse
import collections
import csv
import json
import os
import re
import sqlite3
import sys
import time

SEP = "\t----- bird -----\t"


def load_predictions(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    items = data.values() if isinstance(data, dict) else data
    sqls = []
    for v in items:
        v = str(v)
        sqls.append(v.split(SEP)[0] if SEP in v else v.split("\t")[0])
    return sqls


def load_gold(path):
    gold = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            sql, db = line.rsplit("\t", 1)
            gold.append((sql, db.strip()))
    return gold


def load_difficulty(path):
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()
    data = json.loads(content) if content.startswith("[") else [json.loads(l) for l in content.splitlines() if l.strip()]
    return [d.get("difficulty", "unknown") for d in data]


def run_sql(db_path, sql, timeout):
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    start = time.monotonic()
    conn.set_progress_handler(lambda: 1 if time.monotonic() - start > timeout else 0, 10000)
    try:
        return conn.execute(sql).fetchall()
    finally:
        conn.close()


def error_type(msg):
    msg = msg.lower()
    for key, label in [
        ("no such column", "no such column"),
        ("no such table", "no such table"),
        ("ambiguous column", "ambiguous column"),
        ("syntax error", "syntax error"),
        ("no such function", "no such function"),
        ("misuse of aggregate", "misuse of aggregate"),
        ("incomplete input", "incomplete SQL"),
        ("unrecognized token", "unrecognized token"),
    ]:
        if key in msg:
            return label
    return "other: " + re.sub(r"\s+", " ", msg)[:60]


GOLD_CACHE = {}  # gold results are computed once and reused for every prediction file


def gold_result(i, db_path, gsql, timeout):
    if i not in GOLD_CACHE:
        try:
            GOLD_CACHE[i] = run_sql(db_path, gsql, timeout)
        except Exception as e:
            GOLD_CACHE[i] = e
    return GOLD_CACHE[i]


def analyse(pred_path, gold, diffs, db_root, timeout, gold_timeout):
    preds = load_predictions(pred_path)
    if len(preds) != len(gold):
        sys.exit(f"{pred_path}: {len(preds)} predictions but {len(gold)} gold queries")
    rows = []
    print(f"\n{os.path.basename(pred_path)}: ", end="", flush=True)
    for i, (pred, (gsql, db)) in enumerate(zip(preds, gold)):
        if i % 50 == 0:
            print(f"{i}..", end="", flush=True)
        db_path = os.path.join(db_root, db, f"{db}.sqlite")
        row = {"index": i, "db_id": db, "difficulty": diffs[i] if i < len(diffs) else "unknown", "detail": ""}
        if pred.strip().rstrip(";").strip().upper() == "SELECT 1":
            row["group"] = "no_answer"
            rows.append(row)
            continue
        gres = gold_result(i, db_path, gsql, gold_timeout)
        if isinstance(gres, Exception):
            # The gold query itself is too slow or broken. The official EX script also counts these as wrong.
            row["group"] = "gold_problem"
            row["detail"] = str(gres)[:60]
            rows.append(row)
            continue
        try:
            res = run_sql(db_path, pred, timeout)
        except sqlite3.OperationalError as e:
            if "interrupted" in str(e).lower():
                row["group"] = "timeout"
            else:
                row["group"] = "exec_error"
                row["detail"] = error_type(str(e))
            rows.append(row)
            continue
        except Exception as e:
            row["group"] = "exec_error"
            row["detail"] = error_type(str(e))
            rows.append(row)
            continue
        row["group"] = "correct" if set(res) == set(gres) else "wrong_result"
        rows.append(row)
    return rows


def pct(n, total):
    return f"{100 * n / total:.1f}%" if total else "0%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions", nargs="+")
    ap.add_argument("--gold", default="data/mini_dev_sqlite_gold.sql")
    ap.add_argument("--diff_json", default="data/mini_dev_sqlite.json")
    ap.add_argument("--db_root", default="mini_dev_data/dev_databases/minidev/MINIDEV/dev_databases/")
    ap.add_argument("--timeout", type=float, default=30.0, help="seconds per predicted query")
    ap.add_argument("--gold_timeout", type=float, default=120.0, help="seconds per gold query")
    ap.add_argument("--out_dir", default="results_yigit/error_breakdown")
    args = ap.parse_args()

    gold = load_gold(args.gold)
    diffs = load_difficulty(args.diff_json)
    os.makedirs(args.out_dir, exist_ok=True)
    groups = ["correct", "wrong_result", "exec_error", "timeout", "no_answer", "gold_problem"]
    summary = []

    for path in args.predictions:
        rows = analyse(path, gold, diffs, args.db_root, args.timeout, args.gold_timeout)
        name = os.path.splitext(os.path.basename(path))[0].replace("predict_", "")
        total = len(rows)
        counts = collections.Counter(r["group"] for r in rows)
        err_types = collections.Counter(r["detail"] for r in rows if r["group"] == "exec_error")

        with open(os.path.join(args.out_dir, f"errors_{name}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["index", "db_id", "difficulty", "group", "detail"])
            w.writeheader()
            w.writerows(rows)

        print(f"\n=== {name} ({total} questions) ===")
        for g in groups:
            print(f"  {g:<13} {counts[g]:>4}  {pct(counts[g], total)}")
        if err_types:
            print("  execution errors by type:")
            for t, n in err_types.most_common():
                print(f"    {t:<40} {n:>4}  {pct(n, total)} of all, {pct(n, counts['exec_error'])} of exec errors")
        by_diff = collections.defaultdict(collections.Counter)
        for r in rows:
            by_diff[r["difficulty"]][r["group"]] += 1
        print("  by difficulty (correct / wrong_result / exec_error):")
        for d in ["simple", "moderate", "challenging"]:
            c = by_diff.get(d)
            if c:
                n = sum(c.values())
                print(f"    {d:<12} {pct(c['correct'], n):>6} / {pct(c['wrong_result'], n):>6} / {pct(c['exec_error'], n):>6}")

        summary.append({"run": name, "total": total, **{g: counts[g] for g in groups},
                        **{f"{g}_pct": round(100 * counts[g] / total, 1) for g in groups},
                        "exec_error_types": dict(err_types.most_common())})

    with open(os.path.join(args.out_dir, "summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    if len(summary) > 1:
        print("\n| run | correct | wrong result | execution error | timeout | no answer | gold problem |")
        print("|---|---|---|---|---|---|---|")
        for s in summary:
            print(f"| {s['run']} | " + " | ".join(f"{s[g + '_pct']}%" for g in groups) + " |")


if __name__ == "__main__":
    main()
