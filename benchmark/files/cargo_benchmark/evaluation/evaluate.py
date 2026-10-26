#!/usr/bin/env python3
"""Score model-generated SQL against the Gold results.

Predictions file (JSON):  {"Q01": "SELECT ...", "Q02": "SELECT ...", ...}
Usage: python evaluation/evaluate.py predictions.json [--db cargo_flights.db] [--timeout 30] [--out results.json]

Protocol
 * Each prediction runs on a READ-ONLY connection with a wall-clock timeout; only the first statement is executed.
 * Outcome per question: correct | wrong_result | execution_error | timeout | missing  (errors are tracked separately from wrong answers).
 * Result comparison: same number of rows, same values in the same order (all questions specify ORDER BY),
   floats compared with abs tolerance 0.011, column NAMES are ignored (column ORDER and count must match).
 * Latency (ms) is recorded per query as a separate, informational metric -- it is not part of correctness.
 * Matching on this single dataset is evidence, not proof, of semantic equivalence: see validation/test_gold.py for edge-case fixtures.
"""
import argparse, json, os, sqlite3, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run(db, sql, timeout):
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    start = time.time()
    con.set_progress_handler(lambda: 1 if time.time() - start > timeout else 0, 10000)
    try:
        cur = con.execute(sql.strip().rstrip(";").split(";")[0])
        rows = cur.fetchall()
        return "ok", rows, (time.time() - start) * 1000
    except sqlite3.OperationalError as e:
        return ("timeout" if "interrupted" in str(e) else "error"), str(e), (time.time() - start) * 1000
    except Exception as e:
        return "error", str(e), (time.time() - start) * 1000
    finally:
        con.close()

def same(a, b, tol=0.011):
    if len(a) != len(b): return False
    for ra, rb in zip(a, b):
        if len(ra) != len(rb): return False
        for x, y in zip(ra, rb):
            if isinstance(x, (int, float)) and isinstance(y, (int, float)) and not isinstance(x, bool):
                if abs(x - y) > tol: return False
            elif x != y: return False
    return True

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions"); ap.add_argument("--db", default=os.path.join(ROOT, "cargo_flights.db"))
    ap.add_argument("--timeout", type=float, default=30); ap.add_argument("--out")
    a = ap.parse_args()
    preds = json.load(open(a.predictions))
    questions = json.load(open(os.path.join(ROOT, "questions", "questions.json")))
    results, by_diff = [], {}
    for q in questions:
        _, gold, _ = run(a.db, q["gold_sql"], a.timeout)
        sql = preds.get(q["id"])
        if not sql:
            outcome, ms = "missing", None
        else:
            st, got, ms = run(a.db, sql, a.timeout)
            outcome = "correct" if st == "ok" and same(got, gold) else "wrong_result" if st == "ok" else ("timeout" if st == "timeout" else "execution_error")
        results.append(dict(id=q["id"], difficulty=q["difficulty"], outcome=outcome, latency_ms=ms and round(ms, 1)))
        d = by_diff.setdefault(q["difficulty"], collections_counter()); d[outcome] += 1; d["total"] += 1
    n = len(results); ok = sum(r["outcome"] == "correct" for r in results)
    print(f"Execution-correct answers: {ok}/{n} ({100*ok/n:.1f}%)")
    for diff in ("easy", "medium", "hard"):
        d = by_diff.get(diff)
        if d: print(f"  {diff:7s} correct {d['correct']}/{d['total']}  wrong_result {d['wrong_result']}  errors {d['execution_error']+d['timeout']}  missing {d['missing']}")
    for r in results:
        if r["outcome"] != "correct": print(f"  {r['id']}: {r['outcome']}")
    if a.out: json.dump(results, open(a.out, "w"), indent=2)

def collections_counter():
    import collections; return collections.Counter()

if __name__ == "__main__":
    main()
