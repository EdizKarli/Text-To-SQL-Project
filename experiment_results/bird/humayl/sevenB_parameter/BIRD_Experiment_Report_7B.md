# BIRD Benchmark Evaluation Report: Qwen2.5-Coder-7B
**Project:** Sabancı University ENS 491/492 — Group #3 (Text-to-SQL)  
**Author:** Humayl Hafeez Soomro  
**Model:** `Qwen2.5-Coder-7B` (Ollama local inference)  
**Dataset:** BIRD Mini-Dev Benchmark (500 Questions across 11 Real-World Databases)  
**Date:** October 2026  

---

## 1. Executive Summary & Comparative Results

This report evaluates local text-to-SQL generation using `Qwen2.5-Coder-7B` on the **BIRD Mini-Dev** benchmark (500 questions). We evaluate two setups:
1. **Baseline System:** Direct zero-shot prompt with full schema DDL, explicit foreign-key join hints (`[FK] Table.col -> Target.col`), and BIRD domain evidence.
2. **Improved Full Pipeline:** An agentic text-to-SQL architecture featuring BM25 Schema Pruning, Database Profiler & Value Grounding, Few-Shot Exemplar RAG, Adaptive Consensus, and AST-based Syntax Verification & Self-Repair.

The improved pipeline achieves **61.40% execution accuracy (EX)**, representing an absolute improvement of **+11.20% (+56 additional queries answered correctly)** over the strong 50.20% baseline, while reducing runtime syntax crashes by **82.5%** (from 57 down to 10).

### Key Performance Indicators (500 Benchmark Samples)

| Evaluation Metric | Baseline System | Improved Full Pipeline | Absolute Delta | Relative Gain |
| :--- | :---: | :---: | :---: | :---: |
| **Overall Execution Accuracy (EX)** | **50.20%** (251 / 500) | **61.40%** (307 / 500) | **+11.20%** | **+22.3%** |
| ↳ Simple Tier (148 questions) | 64.86% (96 / 148) | **75.68%** (112 / 148) | +10.82% | +16.7% |
| ↳ Moderate Tier (250 questions) | 46.40% (116 / 250) | **58.00%** (145 / 250) | +11.60% | +25.0% |
| ↳ Challenging Tier (102 questions) | 38.24% (39 / 102) | **49.02%** (50 / 102) | +10.78% | +28.2% |
| **Executable Query Validity Rate** | 88.60% (443 / 500) | **98.00%** (490 / 500) | **+9.40%** | — |
| **Execution Syntax Crashes** | 57 (11.40%) | **10 (2.00%)** | **-47 errors** | **-82.5%** |
| **High Confidence Predictions** | 406 (81.20%) | **472 (94.40%)** | +66 queries | +16.3% |
| **Adaptive Fast-Path Efficiency** | N/A (1 call) | **86.80%** (434 / 500) | — | 868 LLM calls saved |

---

## 2. Terminal Output Snapshots

### 2.1 Baseline System Run (Terminal Output)
```text
(.venv) PS C:\Drive_D\Uni Study\7th_Sem\Graduation_Project_ENS_491\Work> python -m src.baseline --num 500 --model qwen2.5-coder:7b --out results/baseline_500_results.json
[001/500] Q#  25 (moderate   ) | DB: california_schools     | Status: WRONG_RESULT    | Running EX: 0.0%
[002/500] Q#  27 (moderate   ) | DB: california_schools     | Status: WRONG_RESULT    | Running EX: 0.0%
[003/500] Q#  39 (simple     ) | DB: california_schools     | Status: CORRECT         | Running EX: 33.3%
...
[499/500] Q#1528 (simple     ) | DB: toxicology             | Status: CORRECT         | Running EX: 50.3%
[500/500] Q#1534 (challenging) | DB: toxicology             | Status: WRONG_RESULT    | Running EX: 50.2%

===========================================================================
BASELINE EVALUATION COMPLETE - BREAKDOWN BY DIFFICULTY TIER
===========================================================================
Difficulty Tier | Total   | Correct  | Wrong Res  | Exec Error  | Accuracy  
---------------------------------------------------------------------------
Simple          | 148     | 96       | 42         | 10          | 64.9%
Moderate        | 250     | 116      | 104        | 30          | 46.4%
Challenging     | 102     | 39       | 46         | 17          | 38.2%
---------------------------------------------------------------------------
TOTAL           | 500     | 251      | 192        | 57          | 50.2%
===========================================================================
Results saved to: results/baseline_500_results.json
```

### 2.2 Improved Full Pipeline Run (Terminal Output)
```text
(.venv) PS C:\Drive_D\Uni Study\7th_Sem\Graduation_Project_ENS_491\Work> python -m src.evaluate_full_system --model qwen2.5-coder:7b --num 500 --consensus_mode adaptive --out results/full_system_500.json
=====================================================================================
EVALUATING FULL SYSTEM: RETRIEVAL + PROFILER + FEW-SHOT RAG + ADAPTIVE CONSENSUS + AST
Model: qwen2.5-coder:7b | Dataset: 500 samples | Few-Shot: ON | Consensus: ADAPTIVE | AST: ON | Repair: ON
=====================================================================================
[001/500] Q#  25 (moderate   ) | DB: california_schools     | [FAST 1c] |            | [HIGH]   | 11.2s | Status: CORRECT         | Running EX: 100.0%
[002/500] Q#  27 (moderate   ) | DB: california_schools     | [FAST 1c] |            | [HIGH]   |  7.4s | Status: WRONG_RESULT    | Running EX: 50.0%
[003/500] Q#  39 (simple     ) | DB: california_schools     | [FAST 1c] |            | [HIGH]   |  6.1s | Status: CORRECT         | Running EX: 66.7%
...
[500/500] Q#1534 (challenging) | DB: toxicology             | [CONS 3c] | [REPAIRED] | [HIGH]   | 18.3s | Status: CORRECT         | Running EX: 61.4%

=====================================================================================
SUPERVISOR EVALUATION REPORT: 4 CORE EVALUATION CRITERIA
=====================================================================================
[CRITERION 1: QUERY VALIDITY (EXECUTABILITY)]
Total Evaluated Queries   : 500
Valid Executable Queries  : 490 / 500 (98.00%)
Execution Syntax Crashes  : 10 (2.00%)

[CRITERION 2: EXECUTION ACCURACY (CORRECTNESS)]
Tier            |   Baseline EX | Full System EX |      Delta
-----------------------------------------------------------------
Simple          |        64.86% |         75.68% |     +10.8%
Moderate        |        46.40% |         58.00% |     +11.6%
Challenging     |        38.24% |         49.02% |     +10.8%
-----------------------------------------------------------------
OVERALL         |        50.20% |         61.40% |     +11.2%

[CRITERION 3: SINGLE-QUERY LATENCY PROFILING]
Mean Latency (Avg)        : 9.84 s / query
Median Latency (p50)      : 8.21 s / query
95th Percentile (p95)     : 19.45 s / query

[CRITERION 4: BATCH THROUGHPUT & ADAPTIVE EFFICIENCY]
Total Batch Elapsed Time  : 4920.0 s (82.00 min)
Batch Throughput          : 6.10 Queries / Minute (QPM)
Fast-Path Exits Triggered : 434 / 500 (86.8%)
Multi-Candidate Fallbacks : 66 / 500 (13.2%)
Redundant LLM Calls Saved : 868 calls eliminated (57.9% reduction)

=====================================================================================
CONFIDENCE & CLARIFICATION VERIFICATION GATE REPORT
=====================================================================================
High Confidence Queries   : 472 (94.4%)
Medium Confidence (Empty) : 18 (3.6%)
Low Confidence (Syntax)   : 10 (2.0%)
Clarification Triggered   : 28 queries routed to verification gate
=====================================================================================
Results saved to: results/full_system_500.json
```

---

## 3. Technical Breakdown: How the Results Were Achieved

### Why the Baseline Achieved 50.20%
Our baseline does not feed raw database dumps. Instead, it extracts clean DDL table representations with column data types and enriches each table with SQLite foreign key relationships extracted via `PRAGMA foreign_key_list` (`[FK] Table.col -> Target.col`). Coupled with BIRD's `evidence` field (clarifying acronyms and calculation formulas), `Qwen2.5-Coder-7B` handles standard relational queries effectively out-of-the-box.

### How the Improved Pipeline Reached 61.40% (+11.20%)
The pipeline introduces five modular layers specifically designed to eliminate the primary failure modes of open-weight LLMs:

```
[ Natural Language Query + Evidence ]
                 │
                 ▼
1. BM25 Schema Pruning ──────────────► Filters 10–30 tables down to top 2–4 candidates
                 │
                 ▼
2. Profiler & Value Grounding ───────► Injects categorical enums & COLLATE NOCASE guards
                 │
                 ▼
3. Few-Shot Demonstration RAG ───────► Injects top domain-aligned (Question, SQL) exemplars
                 │
                 ▼
4. Adaptive Consensus Engine ────────► Fast-path: 1 call if valid (86.8%) | Fallback: 3 candidates (13.2%)
                 │
                 ▼
5. AST Verification & Self-Repair ───► sqlglot dialect parse + execution self-repair loop
                 │
                 ▼
[ Final Verified Executable SQL: 61.40% EX ]
```

1. **BM25 Schema Pruning:** Large schemas (e.g., 20+ tables in `financial` or `california_schools`) overload the model's context window. BM25 scores question/evidence tokens against table schemas, pruning distractor tables and preventing spurious cross-table JOINs.
2. **Database Profiling & Value Grounding:** String mismatches cause silent `WRONG_RESULT` or empty returns. The profiler samples distinct categorical enumerations and numeric ranges into an active Schema Card, automatically injecting `COLLATE NOCASE` guards to eliminate case-sensitivity failures.
3. **Few-Shot Demonstration RAG:** Instead of zero-shot generation, the system dynamically retrieves 2–3 semantically relevant query-SQL exemplars from a curated vector index, guiding the model on complex subqueries, `strftime` date arithmetic, and window functions.
4. **Adaptive Consensus Engine:** Rather than indiscriminately sampling 3 candidates (which triples latency), candidate 0 is sampled greedily at $T=0.0$. If valid and non-empty, it takes the **Fast-Path** exit (86.8% of queries). If candidate 0 fails or returns empty, the system falls back to sample 3 stochastic candidates ($T=0.7$) and performs majority voting on execution result sets.
5. **AST Verification (`sqlglot`) & Self-Repair:** Every generated SQL is parsed into an abstract syntax tree. If SQLite throws a runtime error (e.g., non-existent column, mismatched grouping), the exact SQLite error and problematic query are fed into an automatic repair loop for targeted correction.

---

## 4. Error Analysis & Remaining Challenges

| Failure Category | Baseline Count | Full System Count | Net Reduction | Root Cause & Remaining Challenge |
| :--- | :---: | :---: | :---: | :--- |
| **Syntax / Execution Errors** | 57 (11.4%) | **10 (2.0%)** | **-82.5%** | AST parsing + self-repair fixed 47 crash cases. Remaining 10 are complex nested subquery syntax issues. |
| **Empty Result Sets (Medium Conf)**| 42 (8.4%) | **18 (3.6%)** | **-57.1%** | Value grounding resolved most string filter mismatches; remaining 18 involve multi-condition `WHERE` logic. |
| **Wrong Result / Logic Discrepancies**| 150 (30.0%)| **165 (33.0%)** | — | Many former syntax crashes now execute successfully into valid queries, shifting errors into semantic nuance. |

**Primary Remaining Bottlenecks:**
- **Compound Mathematical Formulas:** In Challenging queries, complex domain-specific ratios or weighted calculations occasionally select incorrect columns or order of operations.
- **Multi-Hop Unconnected Joins:** Ambiguous schema relationships requiring 4+ table joins without explicit foreign keys remain difficult for a 7B parameter model.

---

## 5. Artifacts & Reproduction Commands

### Included Data Artifacts
- `baseline_500_results.json`: Complete 500-sample query-by-query baseline evaluation record.
- `full_system_500_results.json`: Complete 500-sample query-by-query improved pipeline evaluation record.

### Commands to Reproduce
```bash
# 1. Run Baseline (500 samples)
python -m src.baseline --model qwen2.5-coder:7b --num 500 --out results/baseline_500_results.json

# 2. Run Full Improved Pipeline (500 samples, Adaptive Consensus)
python -m src.evaluate_full_system --model qwen2.5-coder:7b --num 500 --consensus_mode adaptive --out results/full_system_500.json
```
