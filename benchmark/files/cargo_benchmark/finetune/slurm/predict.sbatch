#!/bin/bash
# Answer the TEST questions of all three schema variants with one model and score them.
# Submit from the cargo_benchmark folder:
#   sbatch --export=ALL,SIZE=7b                 finetune/slurm/predict.sbatch    # base model, SQL only (baseline)
#   sbatch --export=ALL,SIZE=7b,COND=A          finetune/slurm/predict.sbatch    # fine-tuned, condition A
#   sbatch --export=ALL,SIZE=7b,COND=B          finetune/slurm/predict.sbatch    # fine-tuned, condition B (hint mode)
#   sbatch --export=ALL,SIZE=7b,REASONING=hint  finetune/slurm/predict.sbatch    # base model asked for hint + SQL
#SBATCH --job-name=cargo-predict
#SBATCH --partition=gpu
#SBATCH --gres=gpu:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=finetune/logs/%x-%j.out
set -euo pipefail
SIZE=${SIZE:-7b}
case "$SIZE" in
  7b)   MODEL=${MODEL:-Qwen/Qwen2.5-Coder-7B-Instruct} ;;
  1.5b) MODEL=${MODEL:-Qwen/Qwen2.5-Coder-1.5B-Instruct} ;;
  *)    echo "SIZE must be 7b or 1.5b"; exit 1 ;;
esac
COND=${COND:-}                                     # empty = base model
SPLIT=${SPLIT:-test}
if [ -n "$COND" ]; then
  ADAPTER=(--adapter "finetune/runs/${COND}-${SIZE}/adapter"); TAG="${COND}-${SIZE}"
  REASONING=${REASONING:-$([ "$COND" = B ] && echo hint || echo none)}
else
  ADAPTER=(); TAG="base-${SIZE}"; REASONING=${REASONING:-none}
fi

cd "${SLURM_SUBMIT_DIR:-.}"
# shellcheck disable=SC1091
source "${VENV:-finetune/.venv}/bin/activate"
export HF_HOME=${HF_HOME:-$PWD/finetune/hf_cache}
export TOKENIZERS_PARALLELISM=false
SUFFIX=$([ "$REASONING" = hint ] && echo "_hint" || echo "")

for V in normal mixed cryptic; do
  python finetune/predict_hf.py --model "$MODEL" ${ADAPTER[@]+"${ADAPTER[@]}"} --variant "$V" --split "$SPLIT" \
         --reasoning "$REASONING" --tag "$TAG" --batch-size "${BATCH:-1}"
  P="evaluation/predictions/pred_${V}_${TAG}_hf${SUFFIX}_${SPLIT}.json"
  python evaluation/evaluate.py "$P" --variant "$V" --split "$SPLIT" --out "${P%.json}_results.json"
done
