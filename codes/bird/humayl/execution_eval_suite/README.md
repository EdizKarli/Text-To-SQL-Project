# Execution Failure & Metrics Evaluation Suite

This directory (`execution_eval_suite/`) provides a clean, modular evaluation framework built specifically to evaluate:
- **Benchmarks:** BIRD Mini-Dev (500 questions) and Spider 2.0-Lite (135 SQLite tasks).
- **Models:** `qwen2.5-coder:7b` and `qwen2.5-coder:1.5b`.
- **Setups:** 
  - `schema`: Full synthetic DDL schema (from `bird_infer_schema.py`)
  - `pruned_v2`: Safe graph-aware BFS schema with foreign-key bridge preservation (from `bird_infer_pruned_vol2.py`)
  *(Note: "No schema" is strictly excluded per Jira specification)*

---

## 1. Directory Structure

```
execution_eval_suite/
├── __init__.py               # Package marker
├── schema_builders.py        # FullSchemaBuilder & SafeSchemaPruner logic
├── generate.py               # Phase 1: Generates SQL via Ollama & logs latency
├── run_official_eval.py      # Phase 2: Runs official BIRD evaluation_ex.py
├── analyze_failures.py       # Phase 3: Evaluates SQLite execution, Valid SQL %, error types
├── run_pipeline.py           # End-to-end master runner (Phase 1 -> 2 -> 3)
├── run_spider_eval.py        # Runner for Spider 2.0-Lite SQLite workflows
├── generate_report.py        # Multi-model comparative report generator
└── results/                  # Generated predictions, timings, and reports
```

---

## 2. Quickstart Commands

### A. Run End-to-End Pipeline on BIRD Mini-Dev

```powershell
# 1. Run 7B model with Full Schema (e.g. smoke test on 10 questions)
.\.venv\Scripts\python.exe -m execution_eval_suite.run_pipeline --model qwen2.5-coder:7b --setup schema --num 10

# 2. Run 7B model with Pruned Schema (all 500 questions)
.\.venv\Scripts\python.exe -m execution_eval_suite.run_pipeline --model qwen2.5-coder:7b --setup pruned_v2 --num 500

# 3. Run 1.5B model with Full Schema (all 500 questions)
.\.venv\Scripts\python.exe -m execution_eval_suite.run_pipeline --model qwen2.5-coder:1.5b --setup schema --num 500

# 4. Run 1.5B model with Pruned Schema (all 500 questions)
.\.venv\Scripts\python.exe -m execution_eval_suite.run_pipeline --model qwen2.5-coder:1.5b --setup pruned_v2 --num 500
```

### B. Run Individual Steps Separately (If Predictions Already Exist)

```powershell
# Phase 1: Only run generation
.\.venv\Scripts\python.exe -m execution_eval_suite.generate --model qwen2.5-coder:7b --setup pruned_v2 --num 500

# Phase 2: Run official BIRD evaluation script
.\.venv\Scripts\python.exe -m execution_eval_suite.run_official_eval --predicted_sql_path execution_eval_suite/results/predict_pruned_v2_qwen2.5-coder-7b.json

# Phase 3: Run execution failure & error classification
.\.venv\Scripts\python.exe -m execution_eval_suite.analyze_failures --predicted_path execution_eval_suite/results/predict_pruned_v2_qwen2.5-coder-7b.json
```

### C. Generate Multi-Run Comparative Markdown Summary

```powershell
.\.venv\Scripts\python.exe -m execution_eval_suite.generate_report
```
*Creates `execution_eval_suite/results/COMPARISON_REPORT.md` comparing all runs across EX, Valid SQL %, latency, and failure breakdown.*

---

## 3. Metrics Recorded

1. **Generation Latency:** Milliseconds spent generating SQL via Ollama API (mean, median, P95).
2. **Execution Latency:** Milliseconds spent executing the query on SQLite.
3. **Valid SQL %:** Percentage of queries that executed without SQLite syntax, table, or column errors.
4. **Execution Accuracy (EX):** Percentage of queries whose result set matches the gold oracle query.
5. **Failure Classification:** Categorization of failures into:
   - `wrong_result`: query ran cleanly, but returned wrong rows
   - `unknown_column`: "no such column"
   - `unknown_table`: "no such table"
   - `syntax_error`: syntax errors or unrecognized tokens
   - `unknown_function`: non-SQLite functions (e.g. ST_Distance)
   - `aggregate_misuse`: misuse of aggregate functions
   - `timeout`: queries exceeding 30s
   - `request_failed`: Ollama connection timeouts
