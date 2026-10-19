"""
analyze.py: per-question analysis of the Spider 1.0 dev runs.

For every run it finds, for each question:
  - whether the prediction is correct, using test-suite-sql-eval's own check
    (exec_eval.eval_exec_match, after the same "value" -> "1" replacement its evaluation.py
    does), so the totals must equal the official output in eval_*_testsuite.txt,
  - what went wrong otherwise: request failed or empty answer, not a query, SQL error
    (grouped by SQLite's message), or a query that runs but returns the wrong result,
  - for the pruned setup: whether Ediz's pruner kept every table the gold query uses.
It also compares runs question by question (for example 1.5B vs Ediz's 7B, same prompt).

Writes results_basil/analysis_spider.md and results_basil/per_question_spider.csv.

Usage (after the runs and the official evaluations, see README.md):
  python analyze.py
"""
import argparse
import asyncio
import csv
import importlib.util
import json
import os
import re
import runpy
import sqlite3
import statistics
import sys
from collections import Counter

import sqlglot
from sqlglot import exp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(HERE, "results_basil")
EDIZ = os.path.join(REPO, "experiment_results", "spider", "ediz", "sevenB_parameter")
HARDNESS = ["easy", "medium", "hard", "extra"]

sys.path.insert(0, os.path.join(HERE, "evaluation", "test_suite"))
from process_sql import Schema, get_schema, get_sql  # noqa: E402  (test-suite copy)
from exec_eval import eval_exec_match, exec_on_db, postprocess  # noqa: E402

_spec = importlib.util.spec_from_file_location("ts_evaluation", os.path.join(HERE, "evaluation", "test_suite", "evaluation.py"))
ts_evaluation = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ts_evaluation)

# label -> (prediction file, raw log or None, the pruner it used or None)
RUNS = {
    "coder-1.5B schema": ("predict_schema_qwen2.5-coder-1.5b.sql", "raw_schema_qwen2.5-coder-1.5b.jsonl", None),
    "coder-1.5B pruned": ("predict_pruned_qwen2.5-coder-1.5b.sql", "raw_pruned_qwen2.5-coder-1.5b.jsonl", "pruned"),
    "general-1.5B schema": ("predict_schema_qwen2.5-1.5b.sql", "raw_schema_qwen2.5-1.5b.jsonl", None),
    "Ediz 7B schema": (os.path.join(EDIZ, "predict_spider.sql"), None, None),
    "Ediz 7B pruned": (os.path.join(EDIZ, "predict_spider_pruned.sql"), None, "pruned"),
}
COMPARE = [("coder-1.5B schema", "Ediz 7B schema"), ("general-1.5B schema", "Ediz 7B schema"),
           ("coder-1.5B schema", "general-1.5B schema"), ("coder-1.5B schema", "coder-1.5B pruned")]


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [l.rstrip("\r") for l in lines]


def sql_error_kind(message):
    m = message.lower()
    for pattern, kind in [("no such column", "unknown column"), ("no such table", "unknown table"),
                          ("ambiguous column", "ambiguous column"), ("no such function", "unknown function"),
                          ("misuse of aggregate", "aggregate misuse"), ("aggregate functions are not allowed", "aggregate misuse"),
                          ("one statement at a time", "several statements"), ("syntax error", "syntax error"),
                          ("incomplete input", "syntax error"), ("unrecognized token", "syntax error"),
                          ("timeout", "timeout")]:
        if pattern in m:
            return kind
    return "other SQL error"


def gold_tables(sql):
    try:
        tree = sqlglot.parse_one(sql, read="sqlite")
    except Exception:
        return None
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    return {t.name.lower() for t in tree.find_all(exp.Table)} - ctes


def pruned_tables(pruner, db_id, question):
    text = pruner.extract_relevant_schema(db_id, question)
    return {t.lower() for t in re.findall(r"CREATE TABLE (\S+) \(", text)}


def outcome(pred, raw_row, correct, db_file):
    """One label per question: correct, or the first thing that went wrong."""
    if correct:
        return "correct", ""
    if raw_row is not None and raw_row.get("status") != 200:
        return "request failed", raw_row.get("exception") or f"HTTP{raw_row.get('status')}"
    if raw_row is not None and not raw_row.get("response", "").strip():
        return "empty answer", ""
    if raw_row is None and pred.strip().upper() == "SELECT 1":
        return "request failed", "SELECT 1 placeholder"
    if not re.match(r"\s*(select|with)\b", pred, re.I):
        return "not a query", pred[:60]
    flag, result = asyncio.run(exec_on_db(db_file, postprocess(pred)))
    if flag == "exception":
        return "SQL error", sql_error_kind(str(result))
    return "wrong result", ""


def pct(n, d):
    return f"{100 * n / d:.1f}" if d else "-"


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def official_ex(label):
    """Reads the 'execution' row of the official evaluator outputs, if they exist."""
    found = {}
    for kind in ("testsuite", "original"):
        name = RUNS[label][0]
        if os.path.dirname(name):  # Ediz's predictions: evaluated into this folder too
            base = "ediz7b_" + os.path.basename(name).replace("predict_", "").replace(".sql", "")
        else:
            base = name.replace("predict_", "").replace(".sql", "")
        path = os.path.join(RESULTS, f"eval_{base}_{kind}.txt")
        if os.path.exists(path):
            for line in read_lines(path):
                if line.startswith("execution"):
                    found[kind] = [float(x) for x in line.split()[1:]]
    return found


def main():
    ap = argparse.ArgumentParser(description="Per-question analysis of the Spider runs.")
    ap.add_argument("--limit", type=int, help="only the first N questions (to test this script)")
    ap.add_argument("--out_dir", default=RESULTS)
    args = ap.parse_args()

    dev = json.load(open(os.path.join(DATA, "dev.json"), encoding="utf-8"))
    gold = [l.split("\t") for l in read_lines(os.path.join(DATA, "dev_gold.sql"))]
    assert len(dev) == len(gold) == 1034
    n = args.limit or len(dev)
    dev, gold = dev[:n], gold[:n]

    pruner = runpy.run_path(os.path.join(EDIZ, "spider_infer_pruned.py"), run_name="analysis")["SpiderHybridPruner"](
        os.path.join(DATA, "tables.json"))
    evaluator = ts_evaluation.Evaluator()
    questions = []
    for i, (q, (g_sql, db_id)) in enumerate(zip(dev, gold)):
        db_file = os.path.join(DATA, "database", db_id, db_id + ".sqlite")
        hardness = evaluator.eval_hardness(get_sql(Schema(get_schema(db_file)), g_sql))
        g_tables = gold_tables(g_sql)
        kept = pruned_tables(pruner, db_id, q["question"])
        questions.append({"idx": i, "db_id": db_id, "hardness": hardness, "db_file": db_file, "gold": g_sql,
                          "question": q["question"], "gold_tables": g_tables,
                          "pruned_keeps_gold_tables": None if g_tables is None else g_tables <= kept})

    runs = {}
    for label, (pred_name, raw_name, pruner_used) in RUNS.items():
        pred_path = pred_name if os.path.isabs(pred_name) else os.path.join(RESULTS, pred_name)
        if not os.path.exists(pred_path):
            print(f"skip {label}: {pred_path} not found")
            continue
        preds = read_lines(pred_path)
        assert len(preds) == 1034, f"{pred_path}: {len(preds)} lines"
        preds = preds[:n]
        raw = None
        if raw_name and os.path.exists(os.path.join(RESULTS, raw_name)):
            raw = [json.loads(l) for l in read_lines(os.path.join(RESULTS, raw_name)) if l.strip()]
            assert len(raw) == 1034, f"{raw_name}: {len(raw)} rows"
        results = []
        for q, pred in zip(questions, preds):
            p_str = pred.strip().split("\t")[0].replace("value", "1")  # exactly what test-suite evaluation.py does
            correct = eval_exec_match(db=q["db_file"], p_str=p_str, g_str=q["gold"], plug_value=False,
                                      keep_distinct=False, progress_bar_for_each_datapoint=False)
            kind, detail = outcome(p_str, raw[q["idx"]] if raw else None, correct, q["db_file"])
            results.append({"correct": int(correct), "outcome": kind, "detail": detail})
        runs[label] = {"results": results, "pruner": pruner_used, "raw": raw}
        print(f"{label}: EX {pct(sum(r['correct'] for r in results), len(results))}%")

    lines = ["# Spider 1.0 dev: per-question analysis", "",
             "Generated by `analyze.py`; do not edit by hand. EX = execution accuracy (%), "
             "checked with test-suite-sql-eval's comparison on the original Spider databases.", ""]

    # 1. accuracy by hardness, next to the official evaluator outputs
    rows = []
    for label, run in runs.items():
        res = run["results"]
        by = [pct(sum(r["correct"] for q, r in zip(questions, res) if q["hardness"] == h),
                  sum(1 for q in questions if q["hardness"] == h)) for h in HARDNESS]
        off = official_ex(label)
        ts = f"{100 * off['testsuite'][-1]:.1f}" if "testsuite" in off else "-"
        old = f"{100 * off['original'][-1]:.1f}" if "original" in off else "-"
        rows.append([label] + by + [pct(sum(r["correct"] for r in res), len(res)), ts, old])
    counts = [str(sum(1 for q in questions if q["hardness"] == h)) for h in HARDNESS]
    lines += ["## Execution accuracy", "",
              md_table(["Run"] + [f"{h} ({c})" for h, c in zip(HARDNESS, counts)] +
                       [f"all ({len(questions)})", "official test-suite", "old Spider evaluation.py"], rows), "",
              "The two official columns are read from the evaluators' own output files. The test-suite column must "
              "equal 'all'; the old evaluation.py also marks a prediction wrong when its own SQL parser cannot read "
              "it or when the SELECT list differs from the gold, so it is lower.", ""]

    # 2. what went wrong
    kinds = ["correct", "wrong result", "SQL error", "not a query", "empty answer", "request failed"]
    rows = []
    for label, run in runs.items():
        c = Counter(r["outcome"] for r in run["results"])
        rows.append([label] + [f"{c[k]} ({pct(c[k], len(run['results']))}%)" for k in kinds])
    lines += ["## What went wrong", "", md_table(["Run"] + kinds, rows), ""]
    rows = []
    for label, run in runs.items():
        c = Counter(r["detail"] for r in run["results"] if r["outcome"] == "SQL error")
        rows.append([label, sum(c.values())] + [", ".join(f"{k} {v}" for k, v in c.most_common(5))])
    lines += ["## SQL errors by SQLite message", "", md_table(["Run", "SQL errors", "most common"], rows), ""]

    # 3. pruning: did Ediz's pruner keep the tables the gold query needs?
    known = [q for q in questions if q["pruned_keeps_gold_tables"] is not None]
    kept = [q for q in known if q["pruned_keeps_gold_tables"]]
    lines += ["## Pruning (BM25 + fuzzy, Ediz's spider_infer_pruned.py)", "",
              f"The pruner keeps every table of the gold query for {len(kept)} of {len(known)} questions "
              f"({pct(len(kept), len(known))}%). Gold tables are read from the gold SQL with sqlglot.", ""]
    rows = []
    for label, run in runs.items():
        if run["pruner"] != "pruned":
            continue
        res = run["results"]
        ok_k = sum(res[q["idx"]]["correct"] for q in kept)
        miss = [q for q in known if not q["pruned_keeps_gold_tables"]]
        ok_m = sum(res[q["idx"]]["correct"] for q in miss)
        rows.append([label, f"{pct(ok_k, len(kept))} ({len(kept)})", f"{pct(ok_m, len(miss))} ({len(miss)})"])
    if rows:
        lines += [md_table(["Run", "EX when all gold tables kept (n)", "EX when a gold table was dropped (n)"], rows), ""]

    # 4. question-by-question comparisons
    rows = []
    for a, b in COMPARE:
        if a in runs and b in runs:
            ra, rb = runs[a]["results"], runs[b]["results"]
            both = sum(1 for x, y in zip(ra, rb) if x["correct"] and y["correct"])
            only_a = sum(1 for x, y in zip(ra, rb) if x["correct"] and not y["correct"])
            only_b = sum(1 for x, y in zip(ra, rb) if not x["correct"] and y["correct"])
            rows.append([f"{a} vs {b}", both, only_a, only_b, len(ra) - both - only_a - only_b])
    lines += ["## Question-by-question comparison", "",
              md_table(["Pair (A vs B)", "both correct", "only A", "only B", "both wrong"], rows), ""]

    # 5. accuracy by database for the main run
    main_label = "coder-1.5B schema"
    if main_label in runs:
        res = runs[main_label]["results"]
        rows = []
        for db in sorted({q["db_id"] for q in questions}):
            qs = [q for q in questions if q["db_id"] == db]
            ok = sum(res[q["idx"]]["correct"] for q in qs)
            ok7 = sum(runs["Ediz 7B schema"]["results"][q["idx"]]["correct"] for q in qs) if "Ediz 7B schema" in runs else None
            rows.append([db, len(qs), pct(ok, len(qs)), pct(ok7, len(qs)) if ok7 is not None else "-"])
        lines += ["## Accuracy by database (schema prompt)", "",
                  md_table(["Database", "questions", "coder-1.5B EX", "Ediz 7B EX"], rows), ""]

    # 6. speed (from the run summaries)
    rows = []
    for label, (pred_name, raw_name, _) in RUNS.items():
        if not raw_name:
            continue
        summ = os.path.join(RESULTS, raw_name.replace("raw_", "summary_").replace(".jsonl", ".json"))
        if os.path.exists(summ):
            s = json.load(open(summ, encoding="utf-8"))
            lat = s["latency_wall_s"]
            rows.append([label, s["questions"], s["failed_requests"], lat["mean"], lat["p50"], lat["p95"],
                         s["prompt_tokens_mean"], s["gen_tokens_mean"], s["gen_tokens_per_s_mean"],
                         s["model_minutes_total"], s["ollama"].get("processor", "-")])
    if rows:
        lines += ["## Speed on CPU (Intel Core i7-1185G7, 4 cores, no GPU)", "",
                  md_table(["Run", "questions", "failed requests", "mean s", "median s", "p95 s", "prompt tokens",
                            "generated tokens", "tokens/s", "total min", "processor"], rows), "",
                  "Latency is wall time per question, failed requests left out (same rule as Yiğit's runs).", ""]

    os.makedirs(args.out_dir, exist_ok=True)
    with open(os.path.join(args.out_dir, "analysis_spider.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(args.out_dir, "per_question_spider.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        labels = list(runs)
        w.writerow(["idx", "db_id", "hardness", "pruned_keeps_gold_tables"] +
                   [f"{l} | {k}" for l in labels for k in ("correct", "outcome", "detail")])
        for q in questions:
            w.writerow([q["idx"], q["db_id"], q["hardness"], q["pruned_keeps_gold_tables"]] +
                       [runs[l]["results"][q["idx"]][k] for l in labels for k in ("correct", "outcome", "detail")])
    print("wrote", os.path.join(args.out_dir, "analysis_spider.md"))


if __name__ == "__main__":
    main()
