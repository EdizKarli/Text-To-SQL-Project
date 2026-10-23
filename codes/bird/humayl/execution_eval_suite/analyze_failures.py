import argparse
import json
import math
import os
import sqlite3
import statistics
import time
from typing import Dict, Any, List, Optional, Tuple


def classify_sql_error(error_msg: str) -> str:
    """Classifies SQLite runtime error message into a standardized failure category."""
    if not error_msg:
        return "none"
    m = error_msg.lower()
    patterns = [
        ("no such column", "unknown_column"),
        ("no such table", "unknown_table"),
        ("ambiguous column", "ambiguous_column"),
        ("no such function", "unknown_function"),
        ("misuse of aggregate", "aggregate_misuse"),
        ("aggregate functions are not allowed", "aggregate_misuse"),
        ("syntax error", "syntax_error"),
        ("incomplete input", "syntax_error"),
        ("unrecognized token", "syntax_error"),
        ("timeout", "timeout"),
        ("readonly database", "write_attempt"),
        ("one statement at a time", "multiple_statements")
    ]
    for pattern, kind in patterns:
        if pattern in m:
            return kind
    return "other_sql_error"


def normalize_value(val: Any) -> Any:
    if isinstance(val, float):
        return round(val, 3)
    if isinstance(val, str):
        return val.strip()
    return val


def normalize_rows(rows: List[Tuple]) -> set:
    if not rows:
        return set()
    norm = []
    for r in rows:
        norm.append(tuple(normalize_value(x) for x in r))
    return set(norm)


def execute_query(db_path: str, sql: str, timeout_sec: float = 30.0) -> Tuple[bool, Any, float]:
    """
    Executes SQL against SQLite in read-only mode with timeout.
    Returns: (success: bool, rows_or_error: Any, exec_time_ms: float)
    """
    if not os.path.exists(db_path):
        return False, f"Database file not found: {db_path}", 0.0

    db_uri = f"file:{os.path.abspath(db_path)}?mode=ro"
    deadline = time.monotonic() + timeout_sec
    start_time = time.perf_counter()

    conn = None
    try:
        conn = sqlite3.connect(db_uri, uri=True, timeout=timeout_sec)
        # Periodic handler to abort runaway queries / infinite loops
        conn.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        return True, rows, exec_time_ms
    except Exception as e:
        exec_time_ms = (time.perf_counter() - start_time) * 1000.0
        msg = "timeout" if time.monotonic() > deadline else str(e)
        return False, msg, exec_time_ms
    finally:
        if conn:
            conn.close()


def run_failure_analysis(
    predicted_path: str,
    details_path: Optional[str] = None,
    db_root_path: Optional[str] = None,
    dataset_path: Optional[str] = None,
    gold_sql_path: Optional[str] = None,
    output_dir: Optional[str] = None,
    timeout_sec: float = 30.0
) -> Dict[str, Any]:
    # 1. Resolve paths
    if not os.path.exists(predicted_path):
        raise FileNotFoundError(f"Predicted SQL file not found: {predicted_path}")

    if not output_dir:
        output_dir = os.path.dirname(predicted_path)
    os.makedirs(output_dir, exist_ok=True)

    base_name = os.path.splitext(os.path.basename(predicted_path))[0]
    out_json = os.path.join(output_dir, f"analysis_{base_name}.json")
    out_md = os.path.join(output_dir, f"analysis_{base_name}.md")

    # Auto-detect db_root
    if not db_root_path:
        for candidate in [
            os.path.join("mini_dev_data", "MINIDEV", "dev_databases"),
            os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_databases"),
            os.path.join("mini_dev_data", "dev_databases")
        ]:
            if os.path.exists(candidate):
                db_root_path = os.path.abspath(candidate)
                break

    # Auto-detect dataset
    if not dataset_path:
        for candidate in [
            os.path.join("mini_dev_data", "MINIDEV", "mini_dev_sqlite.json"),
            os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "mini_dev_sqlite.json"),
            os.path.join("data_used_here", "mini_dev_sqlite.json"),
            os.path.join("data", "mini_dev_sqlite.json")
        ]:
            if os.path.exists(candidate):
                dataset_path = os.path.abspath(candidate)
                break

    # Auto-detect gold sql
    if not gold_sql_path:
        for candidate in [
            os.path.join("mini_dev_data", "MINIDEV", "mini_dev_sqlite_gold.sql"),
            os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "mini_dev_sqlite_gold.sql"),
            os.path.join("data_used_here", "mini_dev_sqlite_gold.sql"),
            os.path.join("data", "mini_dev_sqlite_gold.sql")
        ]:
            if os.path.exists(candidate):
                gold_sql_path = os.path.abspath(candidate)
                break

    # 2. Load predictions
    with open(predicted_path, "r", encoding="utf-8") as f:
        preds_dict = json.load(f)

    # Load details (timings) if exists
    gen_timings = {}
    if details_path and os.path.exists(details_path):
        with open(details_path, "r", encoding="utf-8") as f:
            det_list = json.load(f)
            for item in det_list:
                gen_timings[str(item.get("question_id"))] = item

    # Load gold questions metadata
    with open(dataset_path, "r", encoding="utf-8") as f:
        raw_data = f.read().strip()
        data_list = json.loads(raw_data) if raw_data.startswith("[") else [json.loads(x) for x in raw_data.splitlines() if x.strip()]
    data_by_qid = {str(item.get("question_id", idx)): item for idx, item in enumerate(data_list, 1)}

    # Load gold queries
    gold_by_idx = {}
    with open(gold_sql_path, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            parts = line.strip().split("\t")
            if parts:
                gold_by_idx[idx] = parts[0]

    print(f"Starting execution failure analysis on {len(preds_dict)} predictions...")

    records = []
    diff_stats = {
        d: {"total": 0, "correct": 0, "valid_sql": 0}
        for d in ["simple", "moderate", "challenging", "unknown"]
    }
    failure_counts = {
        "wrong_result": 0,
        "unknown_column": 0,
        "syntax_error": 0,
        "unknown_function": 0,
        "unknown_table": 0,
        "aggregate_misuse": 0,
        "ambiguous_column": 0,
        "timeout": 0,
        "write_attempt": 0,
        "other_sql_error": 0,
        "request_failed": 0
    }

    gen_latencies = []
    exec_latencies = []

    for qid_str, pred_str in preds_dict.items():
        # Format: <sql>\t----- bird -----\t<db_id>
        if "\t----- bird -----\t" in pred_str:
            pred_sql, db_id = pred_str.split("\t----- bird -----\t")
        else:
            pred_sql = pred_str.strip()
            db_id = "unknown"

        meta = data_by_qid.get(qid_str, {})
        difficulty = meta.get("difficulty", "unknown")
        question = meta.get("question", "")
        evidence = meta.get("evidence", "")
        gold_sql = meta.get("SQL", meta.get("query", ""))

        if not gold_sql and qid_str.isdigit() and int(qid_str) in gold_by_idx:
            gold_sql = gold_by_idx[int(qid_str)]

        db_path = os.path.join(db_root_path, db_id, f"{db_id}.sqlite")

        # Execute prediction
        pred_ok, pred_res, exec_time_ms = execute_query(db_path, pred_sql, timeout_sec=timeout_sec)
        exec_latencies.append(exec_time_ms)

        # Get generation time
        timing_meta = gen_timings.get(qid_str, {})
        gen_time_ms = timing_meta.get("generation_time_ms", 0.0)
        req_failed = timing_meta.get("request_failed", False)
        if gen_time_ms > 0:
            gen_latencies.append(gen_time_ms)

        diff_stats[difficulty]["total"] += 1

        is_valid = pred_ok
        is_correct = False
        failure_type = "none"
        exec_error = None

        if req_failed:
            failure_type = "request_failed"
            failure_counts["request_failed"] += 1
            is_valid = False
            exec_error = "Ollama request failed or timed out"
        elif not pred_ok:
            exec_error = str(pred_res)
            failure_type = classify_sql_error(exec_error)
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1
        else:
            # Valid SQL
            diff_stats[difficulty]["valid_sql"] += 1
            # Execute gold SQL
            gold_ok, gold_res, _ = execute_query(db_path, gold_sql, timeout_sec=timeout_sec)
            if gold_ok:
                norm_pred = normalize_rows(pred_res)
                norm_gold = normalize_rows(gold_res)
                if norm_pred == norm_gold:
                    is_correct = True
                    diff_stats[difficulty]["correct"] += 1
                else:
                    failure_type = "wrong_result"
                    failure_counts["wrong_result"] += 1
            else:
                failure_type = "gold_failed"
                exec_error = f"Gold query failed: {gold_res}"

        records.append({
            "question_id": int(qid_str) if qid_str.isdigit() else qid_str,
            "db_id": db_id,
            "difficulty": difficulty,
            "question": question,
            "evidence": evidence,
            "predicted_sql": pred_sql,
            "gold_sql": gold_sql,
            "is_valid_sql": is_valid,
            "is_correct": is_correct,
            "failure_type": failure_type,
            "exec_error": exec_error,
            "generation_time_ms": round(gen_time_ms, 2),
            "execution_time_ms": round(exec_time_ms, 2),
            "total_latency_ms": round(gen_time_ms + exec_time_ms, 2)
        })

    # Summary calculations
    total_evaluated = len(records)
    total_correct = sum(1 for r in records if r["is_correct"])
    total_valid = sum(1 for r in records if r["is_valid_sql"])

    overall_ex = (total_correct / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    overall_valid = (total_valid / total_evaluated * 100.0) if total_evaluated > 0 else 0.0

    summary = {
        "benchmark": "BIRD Mini-Dev",
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
        "latency_stats": {
            "mean_gen_ms": round(statistics.mean(gen_latencies), 2) if gen_latencies else 0.0,
            "median_gen_ms": round(statistics.median(gen_latencies), 2) if gen_latencies else 0.0,
            "p95_gen_ms": round(statistics.quantiles(gen_latencies, n=20)[18], 2) if len(gen_latencies) >= 20 else 0.0,
            "mean_exec_ms": round(statistics.mean(exec_latencies), 2) if exec_latencies else 0.0,
            "median_exec_ms": round(statistics.median(exec_latencies), 2) if exec_latencies else 0.0
        },
        "details": records
    }

    # Save JSON summary
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Build Markdown report
    md_content = f"""# BIRD Mini-Dev: Execution Failure & Performance Report
**Prediction File:** `{os.path.basename(predicted_path)}`  
**Total Evaluated:** {total_evaluated} questions  
**Execution Accuracy (EX):** **{overall_ex:.2f}%** ({total_correct}/{total_evaluated})  
**Valid SQL Percentage:** **{overall_valid:.2f}%** ({total_valid}/{total_evaluated})  

---

## 1. Difficulty Tier Breakdown

| Difficulty | Count | Correct | Execution Accuracy (EX) | Valid SQL Count | Valid SQL % |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for d in ["simple", "moderate", "challenging"]:
        if diff_stats[d]["total"] > 0:
            st = summary["difficulty_breakdown"][d]
            md_content += f"| **{d.capitalize()}** | {st['total']} | {st['correct']} | **{st['accuracy']:.2f}%** | {st['valid_sql']} | {st['valid_percentage']:.2f}% |\n"

    md_content += f"| **Total** | **{total_evaluated}** | **{total_correct}** | **{overall_ex:.2f}%** | **{total_valid}** | **{overall_valid:.2f}%** |\n\n"

    md_content += """---

## 2. Failure Diagnostics Breakdown

| Failure Category | Count | % of All Questions | Explanation |
| :--- | :--- | :--- | :--- |
"""
    explanation_map = {
        "wrong_result": "Query executed cleanly without error, but returned wrong rows",
        "unknown_column": "SQLite threw 'no such column' error",
        "unknown_table": "SQLite threw 'no such table' error",
        "syntax_error": "SQLite syntax error, unrecognized token, or unclosed parenthesis",
        "unknown_function": "Model hallucinated non-SQLite function (e.g. ST_Distance, DATE_ADD)",
        "aggregate_misuse": "Misuse of aggregate functions or missing GROUP BY",
        "ambiguous_column": "Ambiguous column name across joined tables",
        "timeout": f"Execution exceeded {timeout_sec}s safety limit",
        "request_failed": "Ollama network request failed or timed out"
    }

    for cat, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            pct = (count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
            expl = explanation_map.get(cat, "Other runtime error")
            md_content += f"| `{cat}` | **{count}** | {pct:.2f}% | {expl} |\n"

    md_content += f"""
---

## 3. Latency Statistics

* **Generation Latency (Ollama):**
  * **Mean:** {summary['latency_stats']['mean_gen_ms'] / 1000.0:.2f} s
  * **Median:** {summary['latency_stats']['median_gen_ms'] / 1000.0:.2f} s
* **Execution Latency (SQLite):**
  * **Mean:** {summary['latency_stats']['mean_exec_ms']:.2f} ms
  * **Median:** {summary['latency_stats']['median_exec_ms']:.2f} ms
"""

    with open(out_md, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 75)
    print(f"  EXECUTION & FAILURE ANALYSIS SUMMARY: {base_name}")
    print("=" * 75)
    print(f"Total Evaluated        : {total_evaluated}")
    print(f"Execution Accuracy (EX): {overall_ex:.2f}% ({total_correct}/{total_evaluated})")
    print(f"Valid SQL Percentage   : {overall_valid:.2f}% ({total_valid}/{total_evaluated})")
    print("\nFailure breakdown:")
    for cat, count in sorted(failure_counts.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"  - {cat:<20}: {count:3d} ({count / total_evaluated * 100.0:5.1f}%)")
    print(f"\nSaved analysis JSON to: {out_json}")
    print(f"Saved analysis Markdown report to: {out_md}")
    print("=" * 75 + "\n")

    return summary


def main():
    parser = argparse.ArgumentParser(description="Analyze execution failures, validity, and accuracy on BIRD predictions.")
    parser.add_argument("--predicted_path", type=str, required=True, help="Path to predict_*.json")
    parser.add_argument("--details_path", type=str, default=None, help="Path to details_*.json with timings")
    parser.add_argument("--db_root_path", type=str, default=None, help="Directory containing dev_databases")
    parser.add_argument("--dataset_path", type=str, default=None, help="Path to mini_dev_sqlite.json")
    parser.add_argument("--gold_sql_path", type=str, default=None, help="Path to mini_dev_sqlite_gold.sql")
    parser.add_argument("--output_dir", type=str, default=None, help="Output directory for reports")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-query execution timeout in seconds")
    args = parser.parse_args()

    run_failure_analysis(
        predicted_path=args.predicted_path,
        details_path=args.details_path,
        db_root_path=args.db_root_path,
        dataset_path=args.dataset_path,
        gold_sql_path=args.gold_sql_path,
        output_dir=args.output_dir,
        timeout_sec=args.timeout
    )


if __name__ == "__main__":
    main()
