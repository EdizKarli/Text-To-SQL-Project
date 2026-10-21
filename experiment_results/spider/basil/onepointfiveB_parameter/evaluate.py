"""
evaluate.py: scores every prediction file with both official Spider evaluators, then runs analyze.py.

For each run it writes into results_basil/:
  eval_<setup>_<model>_testsuite.txt  test-suite-sql-eval: standard execution accuracy (EX)
  eval_<setup>_<model>_original.txt   the original Spider evaluation.py (what Ediz's 7B numbers used)
Ediz's 7B predictions are scored the same way (eval_ediz7b_spider*.txt), so every number
comes from the same evaluators and databases.

Usage (from any folder, after the runs):
  python evaluate.py
"""
import glob
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DATA = os.path.join(HERE, "data")
RESULTS = os.path.join(HERE, "results_basil")
EDIZ = os.path.join(REPO, "experiment_results", "spider", "ediz", "sevenB_parameter")
EVALUATORS = {"testsuite": os.path.join(HERE, "evaluation", "test_suite", "evaluation.py"),
              "original": os.path.join(HERE, "evaluation", "spider_original", "evaluation.py")}


def main():
    targets = [(p, os.path.basename(p)[len("predict_"):-len(".sql")])
               for p in sorted(glob.glob(os.path.join(RESULTS, "predict_*.sql")))]
    targets += [(os.path.join(EDIZ, "predict_spider.sql"), "ediz7b_spider"),
                (os.path.join(EDIZ, "predict_spider_pruned.sql"), "ediz7b_spider_pruned")]
    for pred, base in targets:
        for kind, script in EVALUATORS.items():
            cmd = [sys.executable, "-X", "utf8", script, "--gold", os.path.join(DATA, "dev_gold.sql"), "--pred", pred,
                   "--db", os.path.join(DATA, "database"), "--table", os.path.join(DATA, "tables.json"), "--etype", "exec"]
            res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
            if res.returncode != 0:
                sys.exit(f"{kind} evaluator failed on {pred}:\n{res.stderr[-2000:]}")
            lines = res.stdout.splitlines()
            # keep the score table; drop the progress lines and all but the last parse-error count
            errs = [l for l in lines if l.startswith("eval_err_num")]
            table = [l.rstrip() for l in lines if not l.startswith(("Evaluating", "eval_err_num")) and l.strip()]
            with open(os.path.join(RESULTS, f"eval_{base}_{kind}.txt"), "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(errs[-1:] + table) + "\n")
            print(f"{base} [{kind}]: {[l for l in table if l.startswith('execution')]}")
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "analyze.py")], check=True)


if __name__ == "__main__":
    main()
