"""
evaluate.py: scores every prediction file with the official BIRD evaluator, then runs analyze.py.

For each run it writes results_basil/eval_<setup>_<model>.txt (the evaluator's own log).

Usage (from any folder, after the runs):
  python evaluate.py
  python evaluate.py --num_cpus 1     (slower, but leaves the CPU free for other work)
"""
import argparse
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RESULTS = os.path.join(HERE, "results_basil")
EDIZ = os.path.join(REPO, "experiment_results", "bird", "ediz", "sevenB_parameter")
DB_ROOT = os.path.join(HERE, "mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_databases") + os.sep
EDIZ_FILES = {"predict_mini_dev.json": "noschema", "predict_mini_dev_schema.json": "schema",
              "predict_mini_dev_pruned.json": "pruned_v1", "predict_mini_dev_pruned_v2.json": "pruned_v2"}


def main():
    ap = argparse.ArgumentParser(description="Score all BIRD prediction files with the official evaluator.")
    ap.add_argument("--num_cpus", type=int, default=4)
    args = ap.parse_args()

    targets = [(p, os.path.basename(p)[len("predict_"):-len(".json")])
               for p in sorted(glob.glob(os.path.join(RESULTS, "predict_*.json")))]
    targets += [(os.path.join(EDIZ, f), f"ediz7b_{setup}") for f, setup in EDIZ_FILES.items()]
    for pred, base in targets:
        out = os.path.join(RESULTS, f"eval_{base}.txt")
        if os.path.exists(out):
            os.remove(out)  # the evaluator appends to its log
        cmd = [sys.executable, "-X", "utf8", os.path.join(HERE, "evaluation", "evaluation_ex.py"),
               "--predicted_sql_path", pred, "--ground_truth_path", os.path.join(HERE, "data", "mini_dev_sqlite_gold.sql"),
               "--db_root_path", DB_ROOT, "--diff_json_path", os.path.join(HERE, "data", "mini_dev_sqlite.json"),
               "--num_cpus", str(args.num_cpus), "--output_log_path", out]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            sys.exit(f"evaluator failed on {pred}:\n{res.stderr[-2000:]}")
        print(f"{base}: {[l for l in res.stdout.splitlines() if l.startswith('EX ')]}")
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "analyze.py")], check=True)


if __name__ == "__main__":
    main()
