#!/bin/bash
# Submit the whole experiment grid: for each model size, train A and B, then predict + score the test split for
# the base model (SQL only and hint mode) and both fine-tuned models. Prediction jobs wait for their training job.
# Run from the cargo_benchmark folder:   bash finetune/slurm/submit_all.sh            (both sizes)
#                                         SIZES=1.5b bash finetune/slurm/submit_all.sh (start small)
set -euo pipefail
mkdir -p finetune/logs
for SIZE in ${SIZES:-1.5b 7b}; do
  sbatch --export=ALL,SIZE="$SIZE" finetune/slurm/predict.sbatch
  sbatch --export=ALL,SIZE="$SIZE",REASONING=hint finetune/slurm/predict.sbatch
  for COND in A B; do
    JOB=$(sbatch --parsable --export=ALL,COND="$COND",SIZE="$SIZE" finetune/slurm/train.sbatch)
    sbatch --dependency=afterok:"$JOB" --export=ALL,COND="$COND",SIZE="$SIZE" finetune/slurm/predict.sbatch
    echo "$SIZE $COND: train job $JOB (+ predict job after it)"
  done
done
