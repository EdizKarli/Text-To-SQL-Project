#!/usr/bin/env python3
"""Pack everything the cluster needs into one archive: finetune/cargo_cluster_bundle.tar.gz

    python finetune/pack_for_cluster.py            # rebuilds finetune/data first, then packs
    scp finetune/cargo_cluster_bundle.tar.gz <user>@<cluster>:~/      # then on the cluster: tar xzf ...

Contents (about 25 MB unpacked without data, a few MB packed):
  databases/  schema/  questions/*.json  hints/hints_*.jsonl  splits/  evaluation/ (scripts only)
  finetune/   scripts, SLURM jobs, Modelfile template and the built datasets in finetune/data/
Not included: model weights (downloaded on the cluster), predictions, runs, logs, caches.
"""
import os
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "cargo_cluster_bundle.tar.gz")
INCLUDE = ["databases", "schema", "questions", "hints", "splits", "evaluation", "finetune"]
SKIP_DIRS = {"__pycache__", "predictions", "runs", "logs", "hf_cache", ".venv"}
SKIP_FILES = {"question_bank.py", "build_questions.py", "build_hints.py", "validate_hints.py",
              "hint_bank_easy.py", "hint_bank_moderate.py", "hint_bank_hard.py", os.path.basename(OUT)}


def keep(path):
    parts = set(os.path.relpath(path, ROOT).split(os.sep))
    return not (parts & SKIP_DIRS) and os.path.basename(path) not in SKIP_FILES and not path.endswith(".pyc")


def main():
    if "--no-build" not in sys.argv:
        subprocess.run([sys.executable, os.path.join(HERE, "build_dataset.py")], check=True)
    n = 0
    with tarfile.open(OUT, "w:gz") as tar:
        for top in INCLUDE:
            for d, dirs, files in os.walk(os.path.join(ROOT, top)):
                dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS)
                for f in sorted(files):
                    p = os.path.join(d, f)
                    if keep(p):
                        tar.add(p, arcname=os.path.join("cargo_benchmark", os.path.relpath(p, ROOT)))
                        n += 1
    print(f"{n} files -> {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT) / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
