import argparse
import os
import re
import subprocess
import sys
from typing import Dict, Any, Optional


def find_eval_dependencies():
    """Auto-detects paths for official BIRD evaluation."""
    # 1. Evaluation script and utils directory
    eval_script_candidates = [
        os.path.join("mini_dev", "evaluation", "evaluation_ex.py"),
        os.path.join("github_repo", "Text-To-SQL-Project", "experiment_results", "bird", "yigit", "onepointfiveB_parameter", "evaluation", "evaluation_ex.py"),
        os.path.join("github_repo", "Text-To-SQL-Project", "experiment_results", "bird", "basil", "onepointfiveB_parameter", "evaluation", "evaluation_ex.py")
    ]
    eval_script = None
    for p in eval_script_candidates:
        if os.path.exists(p):
            eval_script = os.path.abspath(p)
            break
    if not eval_script:
        raise FileNotFoundError("Could not locate official BIRD 'evaluation_ex.py'.")

    eval_dir = os.path.dirname(eval_script)

    # 2. Database root path
    db_root_candidates = [
        os.path.join("mini_dev_data", "MINIDEV", "dev_databases"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_databases"),
        os.path.join("mini_dev_data", "dev_databases"),
    ]
    db_root = None
    for p in db_root_candidates:
        if os.path.exists(p):
            db_root = os.path.abspath(p) + os.sep
            break
    if not db_root:
        raise FileNotFoundError("Could not locate BIRD 'dev_databases' folder.")

    # 3. Ground truth path
    gt_candidates = [
        os.path.join("mini_dev_data", "MINIDEV", "mini_dev_sqlite_gold.sql"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "mini_dev_sqlite_gold.sql"),
        os.path.join("data_used_here", "mini_dev_sqlite_gold.sql"),
        os.path.join("data", "mini_dev_sqlite_gold.sql"),
    ]
    gt_path = None
    for p in gt_candidates:
        if os.path.exists(p):
            gt_path = os.path.abspath(p)
            break
    if not gt_path:
        raise FileNotFoundError("Could not locate 'mini_dev_sqlite_gold.sql'.")

    # 4. Diff JSON path (.jsonl format is required by BIRD's load_jsonl)
    diff_candidates = [
        os.path.join("mini_dev_data", "MINIDEV", "mini_dev_sqlite.jsonl"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "mini_dev_sqlite.jsonl"),
        os.path.join("data_used_here", "mini_dev_sqlite.jsonl"),
        os.path.join("data", "mini_dev_sqlite.jsonl"),
        os.path.join("mini_dev_data", "MINIDEV", "mini_dev_sqlite.json"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "mini_dev_sqlite.json"),
        os.path.join("data_used_here", "mini_dev_sqlite.json"),
        os.path.join("data", "mini_dev_sqlite.json"),
    ]
    diff_path = None
    for p in diff_candidates:
        if os.path.exists(p):
            diff_path = os.path.abspath(p)
            break
    if not diff_path:
        raise FileNotFoundError("Could not locate 'mini_dev_sqlite.json'.")

    return eval_dir, eval_script, db_root, gt_path, diff_path


def run_official_evaluation(
    predicted_sql_path: str,
    output_log_path: Optional[str] = None,
    num_cpus: int = 4,
    meta_time_out: float = 30.0
) -> Dict[str, Any]:
    predicted_sql_path = os.path.abspath(predicted_sql_path)
    if not os.path.exists(predicted_sql_path):
        raise FileNotFoundError(f"Predicted SQL file not found: {predicted_sql_path}")

    if not output_log_path:
        base_name = os.path.splitext(os.path.basename(predicted_sql_path))[0]
        output_log_path = os.path.join(os.path.dirname(predicted_sql_path), f"eval_{base_name}.txt")

    output_log_path = os.path.abspath(output_log_path)
    eval_dir, eval_script, db_root, gt_path, diff_path = find_eval_dependencies()

    cmd = [
        sys.executable,
        "-u",
        eval_script,
        "--db_root_path", db_root,
        "--predicted_sql_path", predicted_sql_path,
        "--ground_truth_path", gt_path,
        "--diff_json_path", diff_path,
        "--num_cpus", str(num_cpus),
        "--meta_time_out", str(meta_time_out),
        "--sql_dialect", "SQLite",
        "--output_log_path", output_log_path
    ]

    print(f"Running official BIRD evaluation script:\n{' '.join(cmd)}\n")
    proc = subprocess.run(
        cmd,
        cwd=eval_dir,
        capture_output=True,
        text=True
    )

    stdout = proc.stdout
    stderr = proc.stderr

    if proc.returncode != 0:
        print(f"Evaluation error (code {proc.returncode}):\n{stderr}")
        raise RuntimeError(f"Official evaluation script failed: {stderr}")

    print(stdout)
    if os.path.exists(output_log_path):
        print(f"Official evaluation results written to: {output_log_path}")

    # Parse accuracies from output table
    results = {
        "log_path": output_log_path,
        "stdout": stdout,
        "simple_acc": None,
        "moderate_acc": None,
        "challenging_acc": None,
        "total_acc": None
    }

    match = re.search(r"EX\s+([0-9\.]+)\s+([0-9\.]+)\s+([0-9\.]+)\s+([0-9\.]+)", stdout)
    if match:
        results["simple_acc"] = float(match.group(1))
        results["moderate_acc"] = float(match.group(2))
        results["challenging_acc"] = float(match.group(3))
        results["total_acc"] = float(match.group(4))

    return results


def main():
    parser = argparse.ArgumentParser(description="Run official BIRD benchmark evaluator on predicted SQL JSON.")
    parser.add_argument("--predicted_sql_path", type=str, required=True, help="Path to predict_*.json")
    parser.add_argument("--output_log_path", type=str, default=None, help="Path for output log text")
    parser.add_argument("--num_cpus", type=int, default=4, help="Number of worker CPUs")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per-query timeout in seconds")
    args = parser.parse_args()

    run_official_evaluation(
        predicted_sql_path=args.predicted_sql_path,
        output_log_path=args.output_log_path,
        num_cpus=args.num_cpus,
        meta_time_out=args.timeout
    )


if __name__ == "__main__":
    main()
