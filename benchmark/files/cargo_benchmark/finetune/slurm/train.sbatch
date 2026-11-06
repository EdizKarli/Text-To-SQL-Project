#!/bin/bash
# LoRA fine-tuning job. Submit from the cargo_benchmark folder:
#   sbatch --export=ALL,COND=A,SIZE=7b  finetune/slurm/train.sbatch
#   sbatch --export=ALL,COND=B,SIZE=1.5b finetune/slurm/train.sbatch
# Edit the #SBATCH lines (partition, account, GPU type, time) for your cluster. One GPU with 40-80 GB is enough
# for 7B in bf16 with gradient checkpointing; on a 24 GB GPU add EXTRA="--load-in-4bit" (QLoRA).
#SBATCH --job-name=cargo-lora
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=12:00:00
#SBATCH --output=finetune/logs/%x-%j.out
set -euo pipefail
COND=${COND:?set COND=A or COND=B}
SIZE=${SIZE:-7b}                                   # 7b or 1.5b
case "$SIZE" in
  7b)   MODEL=${MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct} ;;
  1.5b) MODEL=${MODEL:-Qwen/Qwen2.5-Coder-1.5B-Instruct} ;;
  *)    echo "SIZE must be 7b or 1.5b"; exit 1 ;;
esac
VARIANTS=${VARIANTS:-normal,mixed,cryptic}
OUT=${OUT:-finetune/runs/${COND}-${SIZE}}
EXTRA=${EXTRA:-}

cd "${SLURM_SUBMIT_DIR:-.}"
# shellcheck disable=SC1091
source "${VENV:-finetune/.venv}/bin/activate"      # or: module load ... / conda activate ...
export HF_HOME=${HF_HOME:-$PWD/finetune/hf_cache}  # models downloaded beforehand on the login node (see README)
export TOKENIZERS_PARALLELISM=false

echo "condition=$COND model=$MODEL variants=$VARIANTS out=$OUT host=$(hostname)"
nvidia-smi || true
python finetune/train_lora.py --condition "$COND" --model "$MODEL" --variants "$VARIANTS" --out "$OUT" $EXTRA
