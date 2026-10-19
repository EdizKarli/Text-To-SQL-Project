# BIRD mini-dev with 1.5B models (vol 2)

Jira: TTSQL-12

I ran Ediz's four BIRD scripts again with 1.5B models instead of qwen2.5:7b. The prompts and the logic are exactly the same as his. The only thing that changes is the model name. This way we can see how much accuracy we lose when the model gets about 5 times smaller.

## Results (execution accuracy, 500 questions)

| Setup | Model | simple | moderate | challenging | total |
|---|---|---|---|---|---|
| No schema | qwen2.5:7b (Ediz) | 3.38 | 1.20 | 0.98 | 1.80 |
| No schema | qwen2.5:1.5b | 0.68 | 0.40 | 0.00 | **0.40** |
| Schema | qwen2.5:7b (Ediz) | 57.43 | 32.40 | 20.59 | 37.40 |
| Schema | qwen2.5:1.5b | 30.41 | 9.60 | 4.90 | **14.80** |
| Schema | qwen2.5-coder:1.5b | 37.16 | 19.20 | 13.73 | **23.40** |
| Pruned vol1 (BM25 + fuzzy) | qwen2.5:7b (Ediz) | 50.68 | 30.40 | 19.61 | 34.20 |
| Pruned vol1 (BM25 + fuzzy) | qwen2.5:1.5b | 29.05 | 9.60 | 7.84 | **15.00** |
| Pruned vol2 | qwen2.5:7b (Ediz) | 54.73 | 31.60 | 24.51 | 37.00 |
| Pruned vol2 | qwen2.5:1.5b | 35.14 | 11.20 | 9.80 | **18.00** |

Counts: 148 simple, 250 moderate, 102 challenging.

## What I see

1. Going from 7B to 1.5B costs a lot. With the full schema, accuracy drops from 37.4% to 14.8%. Moderate and challenging questions are hit the hardest.
2. The coder version of the same size does much better. qwen2.5-coder:1.5b gets 23.4% with the schema prompt, 8.6 points more than the general 1.5B model. So if we stay at 1.5B, the coder model should be our default.
3. Pruning helps the small model, but it did not help the 7B. For 7B, pruned vol2 was about the same as the full schema (37.0 vs 37.4). For 1.5B, pruned vol2 is 3.2 points better than the full schema (18.0 vs 14.8). A small model seems to get confused by a long schema, so giving it fewer tables and columns matters more. This supports keeping Pass 1 in the pipeline.
4. Without any schema the 1.5B model is basically at zero, same as the 7B. The model has to see the schema.
5. I did not run pruned vol1 and vol2 with the coder model yet. That is the obvious next run, and coder + pruned vol2 will probably be the best 1.5B setup.

## Failed requests

Some questions never got an answer: either the request timed out, or Ollama stopped the model because it kept repeating itself. In that case Ediz's script writes `SELECT 1`, so the question counts as wrong. I kept his rule as it is.

| Setup | Model | Failed | Why |
|---|---|---|---|
| No schema | qwen2.5:1.5b | 4 | timeout (120 s) |
| Schema | qwen2.5:1.5b | 8 | 7 timeout (180 s), 1 "token repeat limit" |
| Schema | qwen2.5-coder:1.5b | 3 | timeout (180 s) |
| Pruned vol1 | qwen2.5:1.5b | 4 | timeout (180 s) |
| Pruned vol2 | qwen2.5:1.5b | 9 | timeout (180 s) |

The timeouts are cases where the small model kept generating text and never stopped. Each one also costs 2 to 3 minutes of waiting, so they make the runs a lot longer.

## Speed

Measured on a MacBook Air, Apple M2, 16 GB RAM. **Important:** Ollama runs the model on the Mac's GPU (Metal) by default (`ollama ps` shows "100% GPU"). So these are not CPU numbers, and we should not compare them with the CPU latency targets in the proposal. Failed requests are left out of the latency numbers.

| Setup | Model | Total time (min) | Mean per question (s) | Median (s) | 95th percentile (s) | Tokens per second |
|---|---|---|---|---|---|---|
| No schema | qwen2.5:1.5b | 17.7 | 1.17 | 0.97 | 2.12 | 50.2 |
| Schema | qwen2.5:1.5b | 34.0 | 1.57 | 1.36 | 2.74 | 51.7 |
| Schema | qwen2.5-coder:1.5b | 23.3 | 1.73 | 1.36 | 3.58 | 49.4 |
| Pruned vol1 | qwen2.5:1.5b | 29.7 | 2.14 | 1.94 | 3.50 | 42.8 |
| Pruned vol2 | qwen2.5:1.5b | 45.6 | 2.27 | 2.08 | 3.93 | 41.3 |

Most of the total time comes from the timeouts, not from normal questions.

## Files

- `run_with_model.py`: runs one of Ediz's scripts with another model and saves timing for every question. It does not change the prompts or the logic.
- `bird_infer*.py`: Ediz's scripts, copied without changes.
- `results_yigit/predict_<setup>_<model>.json`: the predicted SQL for every question.
- `results_yigit/eval_<setup>_<model>.txt`: the accuracy table from the BIRD evaluation script.
- `results_yigit/timings_<setup>_<model>.csv`: time and token counts for every question.
- `results_yigit/summary_<setup>_<model>.json`: short summary of each run (time, failures, machine info).
- `evaluation/`: `evaluation_ex.py` and `evaluation_utils.py` from the official BIRD mini-dev repo (github.com/bird-bench/mini_dev).

## How to run it again

The BIRD databases are not in the repo because they are too big. Download them first:

```
mkdir -p mini_dev_data/dev_databases
curl -L -o minidev.zip https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip
unzip -q minidev.zip -d mini_dev_data/dev_databases/
pip install requests rank_bm25 rapidfuzz func_timeout pymysql psycopg2-binary
ollama pull qwen2.5:1.5b
ollama pull qwen2.5-coder:1.5b
```

Run one setup (choices: `noschema`, `schema`, `pruned_v1`, `pruned_v2`):

```
python run_with_model.py --model qwen2.5:1.5b --variant schema
```

Evaluate it:

```
python evaluation/evaluation_ex.py --predicted_sql_path results_yigit/predict_schema_qwen2.5-1.5b.json --ground_truth_path data/mini_dev_sqlite_gold.sql --db_root_path mini_dev_data/dev_databases/minidev/MINIDEV/dev_databases/ --diff_json_path data/mini_dev_sqlite.json --num_cpus 4
```

## Next steps

- Run pruned vol1 and vol2 with qwen2.5-coder:1.5b.
- Measure real CPU latency on a 50 question subset with the GPU turned off, so we can compare with the targets in the proposal.
- Look at the wrong answers by hand and sort them into groups (wrong table, wrong column, wrong join, wrong filter and so on).
