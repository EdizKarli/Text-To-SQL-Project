# Quantization experiments with qwen2.5 1.5B (vol 2)

Jira: TTSQL-23

I ran Ediz's schema script (`bird_infer_schema.py`) on BIRD mini-dev with the 1.5B model at four quantization levels: FP16, Q8_0, Q5_K_M and Q4_K_M. The prompt and the logic are exactly the same as his. Only the model changes. Ediz covered the 7B and 14B models in TTSQL-22.

## Accuracy (execution accuracy, 500 questions)

| Quantization | simple | moderate | challenging | total | failed requests |
|---|---|---|---|---|---|
| FP16 | 33.78 | 14.00 | 9.80 | **19.00** | 3 |
| Q8_0 | 31.76 | 14.40 | 9.80 | **18.60** | 3 |
| Q5_K_M | 34.46 | 14.80 | 6.86 | **19.00** | 5 |
| Q4_K_M | 30.41 | 9.60 | 4.90 | **14.80** | 8 |

Counts: 148 simple, 250 moderate, 102 challenging. A failed request means a timeout (180 s) or an Ollama error. Ediz's script writes `SELECT 1` for those, so they count as wrong.

I ran Q4_K_M twice on different days and got exactly the same numbers both times, so the results are reproducible.

## Where the errors come from

Kamer Hoca asked us to check whether the SQL actually runs, and to show the error distribution with percentages. `error_breakdown.py` runs every predicted query on the database and puts it in one group:

| Quantization | correct | ran but wrong result | did not run (SQL error) | timeout | no answer | gold problem |
|---|---|---|---|---|---|---|
| FP16 | 19.0% | 28.2% | **52.0%** | 0.0% | 0.6% | 0.2% |
| Q8_0 | 18.6% | 28.4% | **52.2%** | 0.0% | 0.6% | 0.2% |
| Q5_K_M | 19.0% | 26.4% | **53.4%** | 0.0% | 1.0% | 0.2% |
| Q4_K_M | 14.8% | 22.4% | **60.6%** | 0.4% | 1.6% | 0.2% |

"No answer" means the request failed and the script wrote `SELECT 1`. "Gold problem" is one question whose gold query takes more than 2 minutes. The official EX script also counts it as wrong, and the "correct" column matches the EX numbers exactly.

SQL errors split by type (as a share of all 500 questions):

| Error type | FP16 | Q8_0 | Q5_K_M | Q4_K_M |
|---|---|---|---|---|
| no such column | **41.4%** | **42.0%** | **42.8%** | **46.2%** |
| syntax error | 4.6% | 4.8% | 5.2% | 4.4% |
| no such function | 2.6% | 2.6% | 1.8% | 4.4% |
| misuse of aggregate | 2.2% | 2.0% | 1.6% | 1.6% |
| ambiguous column | 0.8% | 0.6% | 0.8% | 2.4% |
| no such table | 0.4% | 0.2% | 0.8% | 1.6% |

What this shows:

1. **More than half of the answers don't even run.** The model is not mainly writing logically wrong SQL. It is writing SQL that the database rejects.
2. **"No such column" is the biggest problem by far.** It is about 80% of all SQL errors and 41 to 46% of all questions. The model either makes up a column name or uses a real column with the wrong table. So better schema linking (Pass 1 pruning) and a retry after an execution error should help the most.
3. **Q4_K_M loses accuracy mostly because more SQL fails to run** (52% to 61%). It makes more column, table and ambiguous column mistakes. So 4-bit quantization makes the small model worse at copying the exact schema names.
4. Harder questions fail to run more often. For FP16: 32% of simple, 58% of moderate and 66% of challenging questions give an SQL error.

## Speed and memory

Measured on a MacBook Air, Apple M2, 16 GB RAM. Ollama runs the model on the Mac's GPU (Metal), so these are **not CPU numbers**.

For a fair comparison I used the same first 50 questions for every model, loaded the model before measuring, and waited 5 minutes before each model so the Mac could cool down. The MacBook Air has no fan and slows down after long runs, which made my first measurements unreliable.

| Quantization | Memory | Mean per question (s) | Median (s) | 95th percentile (s) | Tokens per second |
|---|---|---|---|---|---|
| FP16 | 3.4 GB | 3.88 | 2.87 | 6.44 | 26.2 |
| Q8_0 | 2.0 GB | 1.98 | 1.55 | 3.19 | 49.7 |
| Q5_K_M | 1.5 GB | 2.28 | 2.13 | 3.38 | 35.5 |
| Q4_K_M | 1.4 GB | 1.50 | 1.10 | 1.97 | 66.8 |

Memory is the SIZE column of `ollama ps` with an 8192 token context. Failed requests are left out of the latency numbers.

## What I see

1. **Q8_0 looks like the best choice for 1.5B.** It keeps almost the same accuracy as FP16 (18.6 vs 19.0), it is about 2 times faster and it needs 2.0 GB instead of 3.4 GB.
2. **Q4_K_M costs about 4 points.** This is Ollama's default for `qwen2.5:1.5b`. It is the fastest and the smallest, but accuracy drops from 19.0 to 14.8, mostly on moderate and challenging questions. So for the small model, 4-bit quantization is not free.
3. **Q5_K_M is slower than Q8_0 on this machine.** It has the same accuracy as FP16, but it only saves 0.5 GB compared to Q8_0 and it is slower. My guess is that unpacking the K-quant format costs more work on the Apple GPU, and for a model this small that extra work matters more than reading less memory. This may be different on a CPU.
4. **FP16 is the slowest** and uses the most memory, and it gives no real accuracy gain over Q8_0.

## Limitations

- Speed was measured on the GPU, not on a CPU. The proposal's 2 to 3 second target is for a CPU, so these numbers can't be compared with it directly.
- The 50 question speed subset only covers two databases (debit_card_specializing and student_club).
- Only the schema prompt was tested. I did not run the pruned scripts at every quantization level.

## Files

- `run_with_model.py`: runs one of Ediz's scripts with another model and saves the timing of every question. The new `--limit N` option stops after N questions and only saves timing, for speed tests.
- `results_yigit/predict_schema_qwen2.5-1.5b-instruct-<quant>.json`: the predicted SQL for every question.
- `results_yigit/eval_schema_qwen2.5-1.5b-instruct-<quant>.txt`: the accuracy table from the BIRD evaluation script.
- `results_yigit/timings_*.csv` and `results_yigit/summary_*.json`: time per question and a short summary of each full run.
- `results_yigit/latency/`: timing and summary files of the 50 question speed test.
- `error_breakdown.py`: runs every predicted query and sorts it into correct, wrong result, SQL error (with the error type), timeout or no answer.
- `results_yigit/error_breakdown/`: one CSV per run with the group of every question, and `summary.json` with all the percentages.

## How to run it again

```
ollama pull qwen2.5:1.5b-instruct-q8_0
python run_with_model.py --model qwen2.5:1.5b-instruct-q8_0 --variant schema
python evaluation/evaluation_ex.py --predicted_sql_path results_yigit/predict_schema_qwen2.5-1.5b-instruct-q8_0.json --ground_truth_path data/mini_dev_sqlite_gold.sql --db_root_path mini_dev_data/dev_databases/minidev/MINIDEV/dev_databases/ --diff_json_path data/mini_dev_sqlite.json --num_cpus 4
```

Error breakdown for all runs:

```
python error_breakdown.py results_yigit/predict_schema_qwen2.5-1.5b-instruct-*.json
```

Speed test for all four levels:

```
for m in fp16 q8_0 q5_K_M q4_K_M; do sleep 300; python run_with_model.py --model qwen2.5:1.5b-instruct-$m --variant schema --limit 50; done
```

## Next steps

- Measure the same four levels on a CPU only setup, to compare with the 2 to 3 second target.
- Try Q8_0 with the coder model (`qwen2.5-coder:1.5b`), since the coder model was 8.6 points better than the general one at Q4_K_M.
- Run `qwen2.5-coder:3b` as Kamer Hoca suggested, to see where it sits between 1.5B and 7B.
- Run `error_breakdown.py` on the pruned and retry experiments, to check if they really reduce the "no such column" errors.
