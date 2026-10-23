import argparse
import json
import os
import re
import sys
import time
from typing import Dict, Any, List, Optional, Tuple
import requests

from .schema_builders import FullSchemaBuilder, SafeSchemaPruner, sanitize_sql, find_dev_tables_path
from .analyze_failures import execute_query, normalize_rows, run_failure_analysis, classify_sql_error
from .run_official_eval import run_official_evaluation
from .generate import normalize_model_slug


def extract_sql_from_response(raw_text: str) -> str:
    """Extracts SQL query from ```sql ... ``` code block, or falls back to sanitize_sql."""
    match = re.search(r"```sql\s*(.*?)\s*```", raw_text, re.DOTALL | re.IGNORECASE)
    if match:
        return sanitize_sql(match.group(1))
    
    # Check for generic code block ``` ... ```
    match_generic = re.search(r"```\s*(.*?)\s*```", raw_text, re.DOTALL)
    if match_generic:
        return sanitize_sql(match_generic.group(1))
        
    return sanitize_sql(raw_text)


def build_table_columns_map(tables_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, List[str]]]:
    """Builds a fast lookup dictionary: db_id -> {table_name: [col_names]}."""
    db_map = {}
    for db in tables_data:
        db_id = db["db_id"]
        t_names = db["table_names_original"]
        cols_map = {t: [] for t in t_names}
        for col_idx, (t_idx, c_name) in enumerate(db["column_names_original"]):
            if 0 <= t_idx < len(t_names):
                cols_map[t_names[t_idx]].append(c_name)
        db_map[db_id] = cols_map
    return db_map


def generate_targeted_hint(exec_error: str, failure_type: str, table_cols: Dict[str, List[str]]) -> str:
    """Generates an actionable diagnostic hint to guide the LLM's repair reasoning."""
    err_lower = exec_error.lower()
    
    if failure_type == "unknown_column" or "no such column" in err_lower:
        match = re.search(r"no such column:\s*([\w\.\-]+)", exec_error, re.IGNORECASE)
        raw_col = match.group(1) if match else ""
        col_name = raw_col.split(".")[-1] if "." in raw_col else raw_col
        
        matching_tables = [t for t, cols in table_cols.items() if any(c.lower() == col_name.lower() for c in cols)]
        if matching_tables:
            return (
                f"DIAGNOSTIC HINT: Column '{col_name}' is valid in table(s): {matching_tables}. "
                f"Check your table aliases or look for an intermediate bridge table to connect them."
            )
        return (
            f"DIAGNOSTIC HINT: Column '{col_name}' does not exist in the database. "
            f"Check the exact column names defined for each table in the schema above."
        )
        
    if failure_type == "unknown_function" or "no such function" in err_lower:
        return (
            "DIAGNOSTIC HINT: SQLite has a limited set of built-in functions. "
            "Use STRFTIME('%Y', col) instead of YEAR(col), CAST(... AS REAL) instead of CONVERT, "
            "and IIF(cond, a, b) or CASE WHEN instead of IF."
        )
        
    if failure_type == "ambiguous_column" or "ambiguous column" in err_lower:
        match = re.search(r"ambiguous column name:\s*([\w\.\-]+)", exec_error, re.IGNORECASE)
        col_name = match.group(1) if match else "the column"
        return f"DIAGNOSTIC HINT: Prefix '{col_name}' with its specific table alias (e.g. T1.{col_name})."
        
    if failure_type == "syntax_error" or "syntax error" in err_lower:
        return (
            "DIAGNOSTIC HINT: Check for unescaped apostrophes inside string literals (use double single-quotes '' like 'Women''s') "
            "or mismatched parentheses/keywords."
        )
        
    if failure_type == "timeout":
        return (
            "DIAGNOSTIC HINT: The query timed out (likely due to a Cartesian product or unindexed nested subqueries). "
            "Ensure every JOIN has an explicit ON condition, avoid CROSS JOINs, and simplify nested subqueries."
        )
        
    return "DIAGNOSTIC HINT: Ensure all tables and columns strictly match the schema definitions above."


def build_fast_repair_prompt(
    schema: str,
    db_id: str,
    question: str,
    evidence: str,
    failed_sql: str,
    exec_error: str,
    hint: str = ""
) -> str:
    """Builds a fast, direct repair prompt producing single-line SQL without explanation bloat."""
    hint_line = f"HINT: {hint}\n" if hint else ""
    return (
        f"You are an expert SQL assistant. Given the SQLite schema:\n"
        f"```sql\n{schema}\n```\n\n"
        f"Database: {db_id}\n"
        f"Evidence: {evidence}\n"
        f"Question: {question}\n\n"
        f"The previous SQL query failed with an execution error:\n"
        f"Failed SQL: {failed_sql}\n"
        f"SQLite Error: {exec_error}\n"
        f"{hint_line}\n"
        f"Write a corrected valid SQLite query to answer the question using only valid tables and columns from the schema above. "
        f"Output ONLY the SQL statement on a single line. Do not include markdown code fences, comments, or explanations.\n"
        f"SQL:"
    )


def run_self_repair(
    model: str = "qwen2.5-coder:7b",
    setup: str = "schema",
    input_analysis: Optional[str] = None,
    output_dir: str = os.path.join("execution_eval_suite", "results"),
    max_repairs: Optional[int] = None,
    temperature: float = 0.0,
    num_ctx: int = 8192,
    timeout: int = 90,
    ollama_url: str = "http://localhost:11434/api/generate",
    skip_official: bool = False
) -> Dict[str, Any]:
    model_slug = normalize_model_slug(model)
    os.makedirs(output_dir, exist_ok=True)

    # 1. Resolve analysis file
    if not input_analysis:
        input_analysis = os.path.join(output_dir, f"analysis_predict_{setup}_{model_slug}.json")
    if not os.path.exists(input_analysis):
        raise FileNotFoundError(f"Baseline analysis file not found: {input_analysis}. Run baseline pipeline first.")

    base_predict_file = os.path.join(output_dir, f"predict_{setup}_{model_slug}.json")
    if not os.path.exists(base_predict_file):
        raise FileNotFoundError(f"Baseline prediction file not found: {base_predict_file}")

    print("=" * 80)
    print(f"  SELF-REPAIR LOOP: {model} ({setup})")
    print(f"  Source Analysis : {input_analysis}")
    print("=" * 80)

    with open(input_analysis, "r", encoding="utf-8") as f:
        baseline_data = json.load(f)

    with open(base_predict_file, "r", encoding="utf-8") as f:
        base_predictions = json.load(f)

    # Detect DB root directory
    db_root = None
    for cand in [
        os.path.join("mini_dev_data", "MINIDEV", "dev_databases"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_databases"),
        os.path.join("mini_dev_data", "dev_databases")
    ]:
        if os.path.exists(cand):
            db_root = os.path.abspath(cand)
            break

    # Initialize schema handler and column maps
    tables_path = find_dev_tables_path()
    with open(tables_path, "r", encoding="utf-8") as f:
        tables_raw = json.load(f)
    db_table_cols = build_table_columns_map(tables_raw)

    if setup == "schema":
        schema_handler = FullSchemaBuilder(tables_path)
    else:
        schema_handler = SafeSchemaPruner(tables_path)

    # Extract failing queries
    all_details = baseline_data.get("details", [])
    failing_queries = [q for q in all_details if not q.get("is_valid_sql", False)]
    total_failing = len(failing_queries)
    print(f"Total baseline queries : {len(all_details)}")
    print(f"Valid queries (kept)   : {len(all_details) - total_failing} (ZERO RE-COMPUTATION)")
    print(f"Invalid queries to fix : {total_failing}")

    if max_repairs is not None and max_repairs > 0:
        failing_queries = failing_queries[:max_repairs]
        print(f"Capping repair run to first {len(failing_queries)} queries (smoke-test mode).")

    repair_results = []
    repaired_predictions = dict(base_predictions)  # clone original predictions
    repaired_details = {str(d.get("question_id")): dict(d) for d in all_details}

    recovered_valid = 0
    recovered_correct = 0

    t_repair_start = time.time()

    for idx, item in enumerate(failing_queries, 1):
        qid = str(item["question_id"])
        db_id = item["db_id"]
        question = item["question"]
        evidence = item.get("evidence", "")
        failed_sql = item["predicted_sql"]
        exec_error = item.get("exec_error", "Unknown error")
        failure_type = item.get("failure_type", "unknown")
        gold_sql = item.get("gold_sql", "")

        # Get schema
        if setup == "schema":
            schema_text = schema_handler.get_schema(db_id)
        else:
            schema_text = schema_handler.extract_relevant_schema(db_id, question, evidence)

        # Build fast prompt
        table_cols = db_table_cols.get(db_id, {})
        hint = generate_targeted_hint(exec_error, failure_type, table_cols)
        prompt = build_fast_repair_prompt(
            schema=schema_text,
            db_id=db_id,
            question=question,
            evidence=evidence,
            failed_sql=failed_sql,
            exec_error=exec_error,
            hint=hint
        )

        t_gen_start = time.perf_counter()
        raw_response = ""
        prompt_tokens = 0
        eval_tokens = 0

        try:
            resp = requests.post(
                ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": num_ctx
                    }
                },
                timeout=timeout
            )
            resp.raise_for_status()
            res_json = resp.json()
            raw_response = res_json.get("response", "")
            prompt_tokens = res_json.get("prompt_eval_count", 0)
            eval_tokens = res_json.get("eval_count", 0)
        except Exception as e:
            print(f"[{idx}/{len(failing_queries)}] Ollama request error on QID {qid}: {e}")
            raw_response = failed_sql

        gen_time_ms = (time.perf_counter() - t_gen_start) * 1000.0
        repaired_sql = sanitize_sql(raw_response)

        # Quick validation on SQLite (5s timeout to prevent hanging on Cartesian loops)
        db_path = os.path.join(db_root, db_id, f"{db_id}.sqlite") if db_root else ""
        is_now_valid, exec_res, exec_time_ms = execute_query(db_path, repaired_sql, timeout_sec=5.0)

        # Quick correctness check against gold only if valid
        is_now_correct = False
        if is_now_valid and gold_sql:
            g_valid, g_rows, _ = execute_query(db_path, gold_sql, timeout_sec=5.0)
            if g_valid:
                norm_pred = normalize_rows(exec_res)
                norm_gold = normalize_rows(g_rows)
                is_now_correct = (norm_pred == norm_gold)

        if is_now_valid:
            recovered_valid += 1
        if is_now_correct:
            recovered_correct += 1

        status_str = "FIXED (CORRECT)" if is_now_correct else ("FIXED (VALID)" if is_now_valid else "STILL FAILING")
        print(f"[{idx:02d}/{len(failing_queries):02d}] QID {qid} ({db_id}) | Original: {failure_type:<15} -> {status_str} (Gen: {round(gen_time_ms, 1)}ms)")

        # Update prediction record
        repaired_predictions[qid] = f"{repaired_sql}\t----- bird -----\t{db_id}"

        # Update details record
        rec = {
            "question_id": int(qid) if qid.isdigit() else qid,
            "db_id": db_id,
            "failure_type_before": failure_type,
            "exec_error_before": exec_error,
            "failed_sql": failed_sql,
            "repaired_sql": repaired_sql,
            "raw_response": raw_response,
            "is_valid_after": is_now_valid,
            "exec_error_after": None if is_now_valid else str(exec_res),
            "is_correct_after": is_now_correct,
            "gen_time_ms": gen_time_ms,
            "exec_time_ms": exec_time_ms,
            "prompt_tokens": prompt_tokens,
            "eval_tokens": eval_tokens
        }
        repair_results.append(rec)

    total_repair_time = time.time() - t_repair_start

    # Save repaired predictions
    out_predict_repaired = os.path.join(output_dir, f"predict_{setup}_{model_slug}_repaired.json")
    with open(out_predict_repaired, "w", encoding="utf-8") as f:
        json.dump(repaired_predictions, f, indent=2, ensure_ascii=True)

    # Save repair log
    out_repair_log = os.path.join(output_dir, f"repair_log_{setup}_{model_slug}.json")
    with open(out_repair_log, "w", encoding="utf-8") as f:
        json.dump({
            "model": model,
            "setup": setup,
            "total_failing": len(failing_queries),
            "recovered_valid": recovered_valid,
            "recovered_valid_pct": round(recovered_valid / len(failing_queries) * 100, 2) if failing_queries else 0,
            "recovered_correct": recovered_correct,
            "recovered_correct_pct": round(recovered_correct / len(failing_queries) * 100, 2) if failing_queries else 0,
            "total_repair_time_sec": round(total_repair_time, 2),
            "repairs": repair_results
        }, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print(f"  SELF-REPAIR STAGE 1 COMPLETE")
    print(f"  Repaired Predictions : {out_predict_repaired}")
    print(f"  Queries Targeted     : {len(failing_queries)}")
    print(f"  Valid Queries Fixed  : {recovered_valid}/{len(failing_queries)} ({round(recovered_valid/len(failing_queries)*100, 1)}%)")
    print(f"  Correct Queries Gained: +{recovered_correct}")
    print("=" * 80)

    # 3. Update failure analysis records and summary
    print("\n>>> UPDATING EXECUTION FAILURE ANALYSIS ON REPAIRED PREDICTIONS...")
    analysis_repaired = recompute_repaired_analysis(
        baseline_data=baseline_data,
        repair_results=repair_results,
        predicted_path=out_predict_repaired,
        output_dir=output_dir
    )

    # 4. Optional Official BIRD Evaluation
    if not skip_official:
        print("\n>>> RUNNING OFFICIAL BIRD EVALUATION ON REPAIRED PREDICTIONS...")
        try:
            eval_res = run_official_evaluation(
                predicted_sql_path=out_predict_repaired,
                output_log_path=os.path.join(output_dir, f"eval_{setup}_{model_slug}_repaired.txt"),
                num_cpus=4
            )
            print(f"Official Repaired EX Score: {eval_res.get('total_acc')}%")
        except Exception as e:
            print(f"Warning: Official evaluator failed or was interrupted: {e}")

    # Generate Markdown summary comparing baseline vs repaired
    generate_repair_comparison_markdown(
        baseline_analysis=baseline_data,
        repaired_analysis=analysis_repaired,
        repair_log_path=out_repair_log,
        model=model,
        setup=setup,
        output_dir=output_dir
    )

    return {
        "repaired_predict_file": out_predict_repaired,
        "recovered_valid": recovered_valid,
        "recovered_correct": recovered_correct
    }


def recompute_repaired_analysis(
    baseline_data: Dict[str, Any],
    repair_results: List[Dict[str, Any]],
    predicted_path: str,
    output_dir: str
) -> Dict[str, Any]:
    base_name = os.path.splitext(os.path.basename(predicted_path))[0]
    out_json = os.path.join(output_dir, f"analysis_{base_name}.json")
    out_md = os.path.join(output_dir, f"analysis_{base_name}.md")

    rep_map = {str(r["question_id"]): r for r in repair_results}
    records = []
    
    diff_stats = {
        d: {"total": 0, "correct": 0, "valid_sql": 0}
        for d in ["simple", "moderate", "challenging"]
    }
    failure_counts = {}

    for d in baseline_data.get("details", []):
        rec = dict(d)
        qid_str = str(rec["question_id"])
        diff = rec.get("difficulty", "simple")
        if diff in diff_stats:
            diff_stats[diff]["total"] += 1

        if qid_str in rep_map:
            r = rep_map[qid_str]
            rec["predicted_sql"] = r["repaired_sql"]
            rec["is_valid_sql"] = r["is_valid_after"]
            rec["is_correct"] = r["is_correct_after"]
            rec["exec_error"] = r["exec_error_after"]
            if r["is_correct_after"]:
                rec["failure_type"] = "none"
            elif r["is_valid_after"]:
                rec["failure_type"] = "wrong_result"
            else:
                rec["failure_type"] = classify_sql_error(str(r["exec_error_after"]))
            rec["generation_time_ms"] = rec.get("generation_time_ms", 0.0) + r["gen_time_ms"]
            rec["execution_time_ms"] = r["exec_time_ms"]
            rec["total_latency_ms"] = rec["generation_time_ms"] + rec["execution_time_ms"]

        if rec["is_valid_sql"]:
            if diff in diff_stats:
                diff_stats[diff]["valid_sql"] += 1
            if rec["is_correct"]:
                if diff in diff_stats:
                    diff_stats[diff]["correct"] += 1
            else:
                failure_counts["wrong_result"] = failure_counts.get("wrong_result", 0) + 1
        else:
            ft = rec.get("failure_type", "other_sql_error")
            failure_counts[ft] = failure_counts.get(ft, 0) + 1

        records.append(rec)

    total_evaluated = len(records)
    total_correct = sum(1 for r in records if r["is_correct"])
    total_valid = sum(1 for r in records if r["is_valid_sql"])
    overall_ex = (total_correct / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    overall_valid = (total_valid / total_evaluated * 100.0) if total_evaluated > 0 else 0.0

    summary = {
        "benchmark": "BIRD Mini-Dev (Self-Repaired)",
        "predicted_file": predicted_path,
        "total_evaluated": total_evaluated,
        "overall_execution_accuracy": round(overall_ex, 2),
        "overall_valid_sql_percentage": round(overall_valid, 2),
        "total_correct": total_correct,
        "total_valid_sql": total_valid,
        "difficulty_breakdown": {
            d: {
                "total": diff_stats[d]["total"],
                "correct": diff_stats[d]["correct"],
                "accuracy": round((diff_stats[d]["correct"] / diff_stats[d]["total"] * 100.0) if diff_stats[d]["total"] > 0 else 0.0, 2),
                "valid_sql": diff_stats[d]["valid_sql"],
                "valid_percentage": round((diff_stats[d]["valid_sql"] / diff_stats[d]["total"] * 100.0) if diff_stats[d]["total"] > 0 else 0.0, 2)
            } for d in ["simple", "moderate", "challenging"] if diff_stats[d]["total"] > 0
        },
        "failure_breakdown": {
            k: v for k, v in failure_counts.items() if v > 0
        },
        "latency_stats": baseline_data.get("latency_stats", {}),
        "details": records
    }

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Markdown
    md_content = f"# BIRD Mini-Dev: Repaired Execution & Failure Analysis\n"
    md_content += f"**Prediction File:** `{os.path.basename(predicted_path)}`  \n"
    md_content += f"**Total Evaluated:** {total_evaluated} questions  \n"
    md_content += f"**Execution Accuracy (EX):** **{overall_ex:.2f}%** ({total_correct}/{total_evaluated})  \n"
    md_content += f"**Valid SQL Percentage:** **{overall_valid:.2f}%** ({total_valid}/{total_evaluated})  \n\n"
    md_content += "## 1. Difficulty Tier Breakdown\n\n| Difficulty | Count | Correct | Execution Accuracy (EX) | Valid SQL Count | Valid SQL % |\n| :--- | :--- | :--- | :--- | :--- | :--- |\n"
    for d in ["simple", "moderate", "challenging"]:
        if diff_stats[d]["total"] > 0:
            st = summary["difficulty_breakdown"][d]
            md_content += f"| **{d.capitalize()}** | {st['total']} | {st['correct']} | **{st['accuracy']:.2f}%** | {st['valid_sql']} | {st['valid_percentage']:.2f}% |\n"
    md_content += f"| **Total** | **{total_evaluated}** | **{total_correct}** | **{overall_ex:.2f}%** | **{total_valid}** | **{overall_valid:.2f}%** |\n\n"
    md_content += "## 2. Failure Diagnostics Breakdown\n\n| Failure Category | Count | % of All Questions |\n| :--- | :--- | :--- |\n"
    for cat, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
            md_content += f"| `{cat}` | **{count}** | {pct:.2f}% |\n"

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    return summary


def generate_repair_comparison_markdown(
    baseline_analysis: Dict[str, Any],
    repaired_analysis: Dict[str, Any],
    repair_log_path: str,
    model: str,
    setup: str,
    output_dir: str
):
    model_slug = normalize_model_slug(model)
    out_md = os.path.join(output_dir, f"repair_comparison_{setup}_{model_slug}.md")

    with open(repair_log_path, "r", encoding="utf-8") as f:
        r_log = json.load(f)

    base_valid = baseline_analysis.get("overall_valid_sql_percentage", 0)
    rep_valid = repaired_analysis.get("overall_valid_sql_percentage", 0)
    base_ex = baseline_analysis.get("overall_execution_accuracy", 0)
    rep_ex = repaired_analysis.get("overall_execution_accuracy", 0)

    md = [
        f"# Self-Repair Impact Report: {model} ({setup})",
        "",
        "## Executive Summary",
        "",
        f"- **Model**: `{model}`",
        f"- **Prompt Setup**: `{setup}`",
        f"- **Total Evaluated**: {baseline_analysis.get('total_evaluated', 500)} queries",
        f"- **Failing Queries Targeted**: {r_log.get('total_failing', 0)} queries (Zero re-computation of successful queries)",
        f"- **Queries Made Valid**: {r_log.get('recovered_valid', 0)} / {r_log.get('total_failing', 0)} ({r_log.get('recovered_valid_pct', 0)}% recovery rate)",
        f"- **Net Execution Accuracy Gain**: +{r_log.get('recovered_correct', 0)} questions",
        "",
        "## Baseline vs Repaired Comparison",
        "",
        "| Metric | Baseline | Post-Repair | Delta |",
        "|---|---|---|---|",
        f"| **Valid SQL Percentage** | {base_valid:.2f}% | {rep_valid:.2f}% | **{'+' if rep_valid >= base_valid else ''}{rep_valid - base_valid:.2f}%** |",
        f"| **Execution Accuracy (EX)** | {base_ex:.2f}% | {rep_ex:.2f}% | **{'+' if rep_ex >= base_ex else ''}{rep_ex - base_ex:.2f}%** |",
        f"| **Total Correct Queries** | {baseline_analysis.get('total_correct', 0)} | {repaired_analysis.get('total_correct', 0)} | **+{repaired_analysis.get('total_correct', 0) - baseline_analysis.get('total_correct', 0)}** |",
        f"| **Total Runtime Errors** | {baseline_analysis.get('total_evaluated', 500) - baseline_analysis.get('total_valid_sql', 0)} | {repaired_analysis.get('total_evaluated', 500) - repaired_analysis.get('total_valid_sql', 0)} | **-{baseline_analysis.get('total_evaluated', 500) - baseline_analysis.get('total_valid_sql', 0) - (repaired_analysis.get('total_evaluated', 500) - repaired_analysis.get('total_valid_sql', 0))}** |",
        "",
        "## Failure Breakdown Before & After",
        "",
        "| Error Category | Baseline Errors | Post-Repair Errors | Resolved |",
        "|---|---|---|---|"
    ]

    base_fb = baseline_analysis.get("failure_breakdown", {})
    rep_fb = repaired_analysis.get("failure_breakdown", {})
    all_keys = set(base_fb.keys()) | set(rep_fb.keys())

    for k in sorted(all_keys):
        if k == "none":
            continue
        b_cnt = base_fb.get(k, 0)
        r_cnt = rep_fb.get(k, 0)
        diff = b_cnt - r_cnt
        md.append(f"| `{k}` | {b_cnt} | {r_cnt} | {'+' if diff > 0 else ''}{diff} |")

    md.extend([
        "",
        "## Sample Successful Repairs",
        ""
    ])

    sample_fixes = [r for r in r_log.get("repairs", []) if r.get("is_valid_after")][:5]
    for i, s in enumerate(sample_fixes, 1):
        md.extend([
            f"### Sample {i}: QID {s['question_id']} ({s['db_id']}) - `{s['failure_type_before']}`",
            f"- **Error Before**: `{s['exec_error_before']}`",
            f"- **Correct After?**: {'Yes' if s['is_correct_after'] else 'No (Valid SQL, Different Result)'}",
            "```sql",
            f"-- FAILED SQL",
            s['failed_sql'],
            f"-- REPAIRED SQL",
            s['repaired_sql'],
            "```",
            ""
        ])

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    print(f"Saved repair comparison report to {out_md}")


def main():
    parser = argparse.ArgumentParser(description="Self-repair loop for erroneous SQL queries.")
    parser.add_argument("--model", type=str, default="qwen2.5-coder:7b", help="Model name in Ollama")
    parser.add_argument("--setup", type=str, choices=["schema", "pruned_v2"], default="schema", help="Prompt setup")
    parser.add_argument("--input_analysis", type=str, default=None, help="Path to input analysis JSON")
    parser.add_argument("--output_dir", type=str, default=os.path.join("execution_eval_suite", "results"))
    parser.add_argument("--max_repairs", type=int, default=None, help="Max queries to repair (for smoke testing)")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--skip_official", action="store_true", help="Skip official BIRD evaluation")
    args = parser.parse_args()

    run_self_repair(
        model=args.model,
        setup=args.setup,
        input_analysis=args.input_analysis,
        output_dir=args.output_dir,
        max_repairs=args.max_repairs,
        temperature=args.temperature,
        timeout=args.timeout,
        skip_official=args.skip_official
    )


if __name__ == "__main__":
    main()
