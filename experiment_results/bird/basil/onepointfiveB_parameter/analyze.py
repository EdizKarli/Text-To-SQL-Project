"""
analyze.py: per-question analysis of the BIRD mini-dev runs.

For every run it finds, for each question:
  - whether the prediction is correct, with the same check as the official evaluation_ex.py
    (the set of rows the prediction returns equals the set the gold query returns, both run on
    the same SQLite file, 30 s limit), so the totals must equal its output in eval_*.txt,
  - what went wrong otherwise: request failed or empty answer, not a query, SQL error
    (grouped by SQLite's message), or a query that runs but returns the wrong result,
  - for the pruned setups: whether Ediz's pruner kept every table, and every column name,
    that the gold query uses.
It also compares runs question by question, and splits accuracy by schema length.

Writes results_basil/analysis_bird.md and results_basil/per_question_bird.csv.

Usage (after the runs and the official evaluations, see README.md):
  python analyze.py
  python analyze.py --extra "Yigit coder-1.5B schema (M2 GPU)=path/to/predict_schema_qwen2.5-coder-1.5b.json"
"""
import argparse
import csv
import json
import os
import re
import runpy
import sqlite3
import statistics
import time
from collections import Counter

import sqlglot
from sqlglot import exp

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RESULTS = os.path.join(HERE, "results_basil")
EDIZ = os.path.join(REPO, "experiment_results", "bird", "ediz", "sevenB_parameter")
MINIDEV = os.path.join(HERE, "mini_dev_data", "dev_databases", "minidev", "MINIDEV")
DB_ROOT = os.path.join(MINIDEV, "dev_databases")
LEVELS = ["simple", "moderate", "challenging"]
TIME_LIMIT = 30.0  # seconds, the official meta_time_out

# label -> (prediction file, raw log or None, setup)
RUNS = {
    "coder-1.5B no schema": ("predict_noschema_qwen2.5-coder-1.5b.json", "raw_noschema_qwen2.5-coder-1.5b.jsonl", "noschema"),
    "coder-1.5B schema": ("predict_schema_qwen2.5-coder-1.5b.json", "raw_schema_qwen2.5-coder-1.5b.jsonl", "schema"),
    "coder-1.5B pruned v1": ("predict_pruned_v1_qwen2.5-coder-1.5b.json", "raw_pruned_v1_qwen2.5-coder-1.5b.jsonl", "pruned_v1"),
    "coder-1.5B pruned v2": ("predict_pruned_v2_qwen2.5-coder-1.5b.json", "raw_pruned_v2_qwen2.5-coder-1.5b.jsonl", "pruned_v2"),
    "Ediz 7B no schema": (os.path.join(EDIZ, "predict_mini_dev.json"), None, "noschema"),
    "Ediz 7B schema": (os.path.join(EDIZ, "predict_mini_dev_schema.json"), None, "schema"),
    "Ediz 7B pruned v1": (os.path.join(EDIZ, "predict_mini_dev_pruned.json"), None, "pruned_v1"),
    "Ediz 7B pruned v2": (os.path.join(EDIZ, "predict_mini_dev_pruned_v2.json"), None, "pruned_v2"),
}
COMPARE = [("coder-1.5B schema", "Ediz 7B schema"), ("coder-1.5B pruned v2", "Ediz 7B pruned v2"),
           ("coder-1.5B schema", "coder-1.5B pruned v1"), ("coder-1.5B schema", "coder-1.5B pruned v2"),
           ("coder-1.5B pruned v1", "coder-1.5B pruned v2")]


def load_questions(path):
    raw = open(path, encoding="utf-8").read().strip()
    return json.loads(raw) if raw.startswith("[") else [json.loads(l) for l in raw.splitlines() if l.strip()]


def run_pair(pred, gold, db_path):
    """The official check: set(pred rows) == set(gold rows). Returns (correct, error message or None)."""
    deadline = time.monotonic() + TIME_LIMIT
    conn = sqlite3.connect(db_path)
    conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
    try:
        cur = conn.cursor()
        try:
            cur.execute(pred)
            pred_rows = cur.fetchall()
        except Exception as e:
            return 0, ("timeout" if time.monotonic() > deadline else str(e))
        try:
            cur.execute(gold)
            gold_rows = cur.fetchall()
        except Exception as e:
            return 0, "gold failed: " + ("timeout" if time.monotonic() > deadline else str(e))
        return int(set(pred_rows) == set(gold_rows)), None
    finally:
        conn.close()


def sql_error_kind(message):
    m = message.lower()
    for pattern, kind in [("no such column", "unknown column"), ("no such table", "unknown table"),
                          ("ambiguous column", "ambiguous column"), ("no such function", "unknown function"),
                          ("misuse of aggregate", "aggregate misuse"), ("aggregate functions are not allowed", "aggregate misuse"),
                          ("one statement at a time", "several statements"), ("syntax error", "syntax error"),
                          ("incomplete input", "syntax error"), ("unrecognized token", "syntax error"),
                          ("timeout", "timeout"), ("readonly database", "write attempt")]:
        if pattern in m:
            return kind
    return "other SQL error"


def gold_refs(sql):
    """Tables and column names the gold query uses (lower case), or (None, None) if sqlglot fails."""
    try:
        tree = sqlglot.parse_one(sql, read="sqlite")
    except Exception:
        return None, None
    ctes = {c.alias_or_name.lower() for c in tree.find_all(exp.CTE)}
    aliases = {a.alias.lower() for a in tree.find_all(exp.Alias) if a.alias}
    tables = {t.name.lower() for t in tree.find_all(exp.Table)} - ctes
    cols = {c.name.lower() for c in tree.find_all(exp.Column) if c.name and c.name != "*"} - aliases
    return tables, cols


def schema_refs(text):
    """Tables and column names in one of Ediz's CREATE TABLE prompts (lower case)."""
    tables, cols = set(), set()
    for block in re.findall(r"CREATE TABLE (.+?) \(\n(.*?)\n\);", text, re.S):
        tables.add(block[0].lower())
        for line in block[1].split("\n"):
            line = line.strip().rstrip(",")
            if line.endswith(" PRIMARY KEY"):
                line = line[: -len(" PRIMARY KEY")]
            if " " in line:
                cols.add(line.rsplit(" ", 1)[0].lower())
    return tables, cols


def outcome(pred, raw_row, correct, error):
    if correct:
        return "correct", ""
    if raw_row is not None and raw_row.get("status") != 200:
        return "request failed", raw_row.get("exception") or f"HTTP{raw_row.get('status')}"
    if raw_row is not None and not raw_row.get("response", "").strip():
        return "empty answer", ""
    if raw_row is None and re.fullmatch(r"\s*SELECT 1;?\s*", pred, re.I):
        return "request failed", "SELECT 1 placeholder"
    if not re.match(r"\s*(select|with)\b", pred, re.I):
        return "not a query", pred[:60]
    if error and error.startswith("gold failed"):
        return "gold failed", error
    if error:
        return "SQL error", sql_error_kind(error)
    return "wrong result", ""


def pct(n, d):
    return f"{100 * n / d:.1f}" if d else "-"


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def official_total(pred_name):
    """Total EX from the official evaluator's log file for this prediction file, if it exists."""
    if os.path.isabs(pred_name):
        setup = {"predict_mini_dev.json": "noschema", "predict_mini_dev_schema.json": "schema",
                 "predict_mini_dev_pruned.json": "pruned_v1", "predict_mini_dev_pruned_v2.json": "pruned_v2"}
        path = os.path.join(RESULTS, f"eval_ediz7b_{setup.get(os.path.basename(pred_name), 'x')}.txt")
    else:
        path = os.path.join(RESULTS, pred_name.replace("predict_", "eval_").replace(".json", ".txt"))
    if not os.path.exists(path):
        return None
    rows = [l.split() for l in open(path, encoding="utf-8") if l.startswith("EX ")]
    return float(rows[-1][-1]) if rows else None


def main():
    ap = argparse.ArgumentParser(description="Per-question analysis of the BIRD runs.")
    ap.add_argument("--limit", type=int, help="only the first N questions (to test this script)")
    ap.add_argument("--out_dir", default=RESULTS)
    ap.add_argument("--extra", action="append", default=[], help='"label=path" of another prediction file to include')
    args = ap.parse_args()
    runs_spec = dict(RUNS)
    yigit = os.path.join(REPO, "experiment_results", "bird", "yigit", "onepointfiveB_parameter", "results_yigit",
                         "predict_schema_qwen2.5-coder-1.5b.json")  # in the repo once PR #7 is merged
    if os.path.exists(yigit) and not args.extra:
        args.extra.append(f"Yiğit coder-1.5B schema (M2 GPU)={yigit}")
    for item in args.extra:
        label, path = item.split("=", 1)
        runs_spec[label] = (os.path.abspath(path), None, "extra")
        COMPARE.append(("coder-1.5B schema", label))

    questions = load_questions(os.path.join(HERE, "data", "mini_dev_sqlite.json"))
    gold = [l.rstrip("\r\n").split("\t") for l in open(os.path.join(HERE, "data", "mini_dev_sqlite_gold.sql"), encoding="utf-8") if l.strip()]
    assert len(questions) == len(gold) == 500
    n = args.limit or len(questions)
    questions, gold = questions[:n], gold[:n]

    tables_file = os.path.join(MINIDEV, "dev_tables.json")
    full_schemas = runpy.run_path(os.path.join(EDIZ, "bird_infer_schema.py"), run_name="analysis")["build_schema_prompts"](tables_file)
    v1 = runpy.run_path(os.path.join(EDIZ, "bird_infer_pruned.py"), run_name="analysis")["HybridSchemaPruner"](tables_file)
    v2 = runpy.run_path(os.path.join(EDIZ, "bird_infer_pruned_vol2.py"), run_name="analysis")["SafeSchemaPruner"](tables_file)
    for i, (q, (g_sql, db_id)) in enumerate(zip(questions, gold)):
        assert q["db_id"] == db_id
        q["idx"], q["gold"], q["db_path"] = i, g_sql, os.path.join(DB_ROOT, db_id, db_id + ".sqlite")
        q["gold_tables"], q["gold_cols"] = gold_refs(g_sql)
        q["schema_chars"] = {"schema": len(full_schemas[db_id])}
        for name, text in [("pruned_v1", v1.extract_relevant_schema(db_id=db_id, question=q["question"], evidence=q.get("evidence", ""),
                                                                    top_k_tables=4, top_k_columns_per_table=8)),
                           ("pruned_v2", v2.extract_relevant_schema(db_id, q["question"], q.get("evidence", "")))]:
            t, c = schema_refs(text)
            q["schema_chars"][name] = len(text)
            q[f"{name}_tables_ok"] = None if q["gold_tables"] is None else q["gold_tables"] <= t
            q[f"{name}_cols_ok"] = None if q["gold_cols"] is None else q["gold_cols"] <= c

    runs = {}
    for label, (pred_name, raw_name, setup) in runs_spec.items():
        pred_path = pred_name if os.path.isabs(pred_name) else os.path.join(RESULTS, pred_name)
        if not os.path.exists(pred_path):
            print(f"skip {label}: {pred_path} not found")
            continue
        preds = list(json.load(open(pred_path, encoding="utf-8")).values())
        assert len(preds) == 500, f"{pred_path}: {len(preds)} predictions"
        raw = None
        if raw_name and os.path.exists(os.path.join(RESULTS, raw_name)):
            raw = [json.loads(l) for l in open(os.path.join(RESULTS, raw_name), encoding="utf-8") if l.strip()]
            assert len(raw) == 500, f"{raw_name}: {len(raw)} rows"
        results = []
        for q, p in zip(questions, preds[:n]):
            sql = p.split("\t----- bird -----\t")[0] if isinstance(p, str) else " "
            correct, error = run_pair(sql, q["gold"], q["db_path"])
            kind, detail = outcome(sql, raw[q["idx"]] if raw else None, correct, error)
            results.append({"correct": correct, "outcome": kind, "detail": detail})
        runs[label] = {"results": results, "setup": setup, "official": official_total(pred_name)}
        print(f"{label}: EX {pct(sum(r['correct'] for r in results), len(results))}%")

    lines = ["# BIRD mini-dev: per-question analysis", "",
             "Generated by `analyze.py`; do not edit by hand. EX = execution accuracy (%), "
             "with the official BIRD check (same set of result rows as the gold query).", ""]

    # 1. accuracy by difficulty, next to the official evaluator's total
    rows = []
    for label, run in runs.items():
        res = run["results"]
        by = [pct(sum(r["correct"] for q, r in zip(questions, res) if q["difficulty"] == lv),
                  sum(1 for q in questions if q["difficulty"] == lv)) for lv in LEVELS]
        off = run["official"]
        rows.append([label] + by + [pct(sum(r["correct"] for r in res), len(res)), f"{off:.2f}" if off is not None else "-"])
    counts = [sum(1 for q in questions if q["difficulty"] == lv) for lv in LEVELS]
    lines += ["## Execution accuracy", "",
              md_table(["Run"] + [f"{lv} ({c})" for lv, c in zip(LEVELS, counts)] + [f"total ({len(questions)})",
                       "official evaluation_ex.py"], rows), "",
              "The last column is read from the official evaluator's log; it must equal 'total'.", ""]

    # 2. what went wrong
    kinds = ["correct", "wrong result", "SQL error", "not a query", "empty answer", "request failed", "gold failed"]
    rows = []
    for label, run in runs.items():
        c = Counter(r["outcome"] for r in run["results"])
        rows.append([label] + [f"{c[k]} ({pct(c[k], len(run['results']))}%)" for k in kinds])
    lines += ["## What went wrong", "", md_table(["Run"] + kinds, rows), ""]
    rows = []
    for label, run in runs.items():
        c = Counter(r["detail"] for r in run["results"] if r["outcome"] == "SQL error")
        rows.append([label, sum(c.values()), ", ".join(f"{k} {v}" for k, v in c.most_common(5))])
    lines += ["## SQL errors by SQLite message", "", md_table(["Run", "SQL errors", "most common"], rows), ""]

    # 3. pruning: did the pruner keep what the gold query needs?
    rows = []
    for name, title in [("pruned_v1", "v1 (top 4 tables, 8 columns each)"), ("pruned_v2", "v2 (bridge tables, keys kept)")]:
        known_t = [q for q in questions if q[f"{name}_tables_ok"] is not None]
        known_c = [q for q in questions if q[f"{name}_cols_ok"] is not None]
        both = [q for q in known_c if q[f"{name}_tables_ok"] and q[f"{name}_cols_ok"]]
        rows.append([title, f"{pct(sum(q[f'{name}_tables_ok'] for q in known_t), len(known_t))}",
                     f"{pct(sum(q[f'{name}_cols_ok'] for q in known_c), len(known_c))}",
                     f"{pct(len(both), len(known_c))}",
                     round(statistics.mean(q["schema_chars"][name] for q in questions)),
                     round(statistics.mean(q["schema_chars"]["schema"] for q in questions))])
    lines += ["## Pruning recall (Ediz's pruners)", "",
              md_table(["Pruner", "% questions: all gold tables kept", "% all gold column names kept",
                        "% both", "mean schema chars (pruned)", "mean schema chars (full)"], rows), "",
              "Gold tables and columns are read from the gold SQL with sqlglot; column check is by name only.", ""]
    rows = []
    for label, run in runs.items():
        name = run["setup"]
        if name not in ("pruned_v1", "pruned_v2"):
            continue
        res = run["results"]
        ok = [q for q in questions if q[f"{name}_tables_ok"] and q[f"{name}_cols_ok"]]
        miss = [q for q in questions if q[f"{name}_tables_ok"] is False or q[f"{name}_cols_ok"] is False]
        rows.append([label, f"{pct(sum(res[q['idx']]['correct'] for q in ok), len(ok))} ({len(ok)})",
                     f"{pct(sum(res[q['idx']]['correct'] for q in miss), len(miss))} ({len(miss)})"])
    if rows:
        lines += [md_table(["Run", "EX when everything needed was kept (n)", "EX when a gold table or column was dropped (n)"], rows), ""]

    # 4. accuracy by full-schema length (does a long schema hurt the small model more?)
    sizes = sorted(q["schema_chars"]["schema"] for q in questions)
    cuts = [sizes[len(sizes) // 3], sizes[2 * len(sizes) // 3]]
    buckets = [("short", lambda s: s < cuts[0]), ("medium", lambda s: cuts[0] <= s < cuts[1]), ("long", lambda s: s >= cuts[1])]
    rows = []
    for label, run in runs.items():
        res = run["results"]
        cells = []
        for _, inside in buckets:
            qs = [q for q in questions if inside(q["schema_chars"]["schema"])]
            cells.append(pct(sum(res[q["idx"]]["correct"] for q in qs), len(qs)))
        rows.append([label] + cells)
    names = [f"{b} ({sum(1 for q in questions if inside(q['schema_chars']['schema']))} q)" for b, inside in buckets]
    lines += ["## Accuracy by full-schema length", "",
              f"Questions split into thirds by the length of their database's full schema prompt "
              f"(cuts at {cuts[0]} and {cuts[1]} characters). Same split for every run.", "",
              md_table(["Run"] + names, rows), ""]

    # 5. question-by-question comparisons
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

    # 6. accuracy by database
    cols = [l for l in ("coder-1.5B schema", "coder-1.5B pruned v2", "Ediz 7B schema") if l in runs]
    if cols:
        rows = []
        for db in sorted({q["db_id"] for q in questions}):
            qs = [q for q in questions if q["db_id"] == db]
            rows.append([db, len(qs), round(statistics.mean(q["schema_chars"]["schema"] for q in qs))] +
                        [pct(sum(runs[l]["results"][q["idx"]]["correct"] for q in qs), len(qs)) for l in cols])
        lines += ["## Accuracy by database", "",
                  md_table(["Database", "questions", "full schema chars"] + [f"{l} EX" for l in cols], rows), ""]

    # 7. speed (from the run summaries)
    rows = []
    for label, (pred_name, raw_name, _) in runs_spec.items():
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
    with open(os.path.join(args.out_dir, "analysis_bird.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(args.out_dir, "per_question_bird.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        labels = list(runs)
        w.writerow(["question_id", "db_id", "difficulty", "schema_chars", "pruned_v1_tables_ok", "pruned_v1_cols_ok",
                    "pruned_v2_tables_ok", "pruned_v2_cols_ok"] +
                   [f"{l} | {k}" for l in labels for k in ("correct", "outcome", "detail")])
        for q in questions:
            w.writerow([q["question_id"], q["db_id"], q["difficulty"], q["schema_chars"]["schema"],
                        q["pruned_v1_tables_ok"], q["pruned_v1_cols_ok"], q["pruned_v2_tables_ok"], q["pruned_v2_cols_ok"]] +
                       [runs[l]["results"][q["idx"]][k] for l in labels for k in ("correct", "outcome", "detail")])
    print("wrote", os.path.join(args.out_dir, "analysis_bird.md"))


if __name__ == "__main__":
    main()
