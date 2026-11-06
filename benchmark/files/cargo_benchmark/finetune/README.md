# Fine-tuning on the cluster

This folder has everything needed to fine-tune Qwen2.5-Coder (1.5B and 7B) on the cargo benchmark on a GPU
cluster, and to test the result on the same questions as the base model.

## The experiment

| | What the model learns to write | Training prompt |
|---|---|---|
| **Base** | nothing (no training) | the normal benchmark prompt |
| **A: SQL only** | the Gold SQL | the normal benchmark prompt |
| **B: hint + SQL** | the hint (`#schema`, `#think`, `#trace`), then `#sql <Gold SQL>` | the benchmark prompt, asking for the hint format first |

* Data: 960 questions × 3 schema variants. The split is in `splits/split_80_20.json` and is made by **base
  question**: the 4 phrasings and 3 variants of one base question are always on the same side.
  * test: 48 base questions (20%) = 192 questions per variant
  * train: 171 base questions, dev: 21 base questions (dev is used to pick the best epoch)
* One model per condition and size is trained on all three variants together (2052 training rows). Use
  `--variants normal` to train on one variant only.
* The prompt is made by `build_prompt()` in `evaluation/run_ollama.py`, so the training prompt and the test prompt
  are the same. The loss is on the answer only.
* LoRA settings: r 16, alpha 32, dropout 0.05, all attention and MLP layers, learning rate 2e-4 (cosine),
  3 epochs, effective batch 16, bf16, seed 42.

## Files

| File | What it does | Where it runs |
|---|---|---|
| `build_dataset.py` | makes `data/A` and `data/B` (`train`, `dev`, `test` .jsonl) | anywhere (standard Python) |
| `pack_for_cluster.py` | builds the data and packs `cargo_cluster_bundle.tar.gz` | your computer |
| `train_lora.py` | LoRA training | cluster (GPU) |
| `predict_hf.py` | answers the test questions with a base or fine-tuned model | cluster (GPU) |
| `merge_lora.py`, `export_gguf.sh`, `Modelfile.template` | turn a trained adapter into an Ollama model | cluster or your computer |
| `slurm/train.sbatch`, `slurm/predict.sbatch`, `slurm/submit_all.sh` | SLURM jobs | cluster |
| `requirements.txt` | Python packages for the cluster | cluster |

## Step by step

**1. On your computer: pack**

```bash
cd benchmark/files/cargo_benchmark
python finetune/pack_for_cluster.py
scp finetune/cargo_cluster_bundle.tar.gz <user>@<cluster>:~/
```

**2. On the cluster: set up once** (login node, it has internet)

```bash
tar xzf cargo_cluster_bundle.tar.gz && cd cargo_benchmark
python -m venv finetune/.venv && source finetune/.venv/bin/activate
pip install torch --index-url https://download.pytorch.org/whl/cu121     # match the cluster's CUDA
pip install -r finetune/requirements.txt
export HF_HOME=$PWD/finetune/hf_cache
huggingface-cli download Qwen/Qwen2.5-Coder-1.5B-Instruct
huggingface-cli download Qwen/Qwen2.5-Coder-7B-Instruct
mkdir -p finetune/logs
```

GPU nodes often have no internet, so the models are downloaded here first. If your cluster uses `module load`
or conda instead of a venv, change the `source` line in the two `.sbatch` files. Also edit the `#SBATCH` lines
(partition, account, time) for your cluster.

**3. Smoke test** (a few minutes; checks that everything loads)

```bash
srun --gres=gpu:1 --time=00:30:00 --pty bash
source finetune/.venv/bin/activate && export HF_HOME=$PWD/finetune/hf_cache
python finetune/train_lora.py --condition B --model Qwen/Qwen2.5-Coder-1.5B-Instruct --out finetune/runs/smoke --max-steps 5
python finetune/predict_hf.py --model Qwen/Qwen2.5-Coder-1.5B-Instruct --adapter finetune/runs/smoke/adapter \
       --variant normal --split test --reasoning hint --limit 4 --tag smoke
```

**4. Run everything**

```bash
SIZES=1.5b bash finetune/slurm/submit_all.sh      # start with 1.5B
bash finetune/slurm/submit_all.sh                 # both sizes
```

For each size this submits: the base model on the test split (SQL only, and asked for hint + SQL), training of A
and B, and the test run of each trained model after its training ends. Each test job scores all three variants.
Single jobs: `sbatch --export=ALL,COND=A,SIZE=7b finetune/slurm/train.sbatch`.

**5. Results**

Scores are written next to the predictions in `evaluation/predictions/` as `pred_<variant>_<tag>_hf[_hint]_test_results.json`.
Compare them with:

```bash
python evaluation/compare_runs.py "evaluation/predictions/*_test_results.json" --csv finetune_results.csv
```

All runs are scored on the same 192 test questions per variant, so base, A and B can be compared directly.

**6. (Optional) Test with Ollama on your computer**

```bash
python finetune/merge_lora.py --model Qwen/Qwen2.5-Coder-7B-Instruct --adapter finetune/runs/A-7b/adapter --out finetune/runs/A-7b/merged
bash finetune/export_gguf.sh finetune/runs/A-7b/merged cargo-a-7b      # needs llama.cpp, see the script
# copy finetune/runs/A-7b/gguf/ to your computer, then:
ollama create cargo-a-7b -f Modelfile
python evaluation/run_ollama.py --variant normal --split test --model cargo-a-7b --evaluate
python evaluation/run_ollama.py --variant normal --split test --model cargo-b-7b --reasoning hint --evaluate   # B models
```

This gives latency numbers on the same laptop as the base-model runs. Run the base model with `--split test` too,
so both are scored on the same questions.

## Time and memory (rough)

| Model | GPU memory (bf16 LoRA, batch 1, ~4.5k tokens) | Training time, 3 epochs, 2052 rows |
|---|---|---|
| 1.5B | about 16 GB | under 1 hour on an A100 |
| 7B | about 40 GB (about 20 GB with `--load-in-4bit`) | about 3 to 5 hours on an A100 |

These are estimates; check the first job's log and adjust `--time`.

## Notes

* **Leakage**: test questions are never in a training file (`test.jsonl` has no answers). `python splits/check_split.py`
  checks the split.
* **Same prompt everywhere**: training, `predict_hf.py` and `run_ollama.py` all use `build_prompt()`. If you change
  the prompt, rebuild the data (`build_dataset.py`) and retrain.
* **Condition B at test time**: the model must write `#sql` before the query. If it never does (or runs out of
  tokens), the answer counts as missing. The full text is kept in `pred_*_raw.json`.
* **Not included yet**: B3 (the model writes its own hints with no hint training data) and extra training data from
  Spider/BIRD. Both are optional steps in the plan.
