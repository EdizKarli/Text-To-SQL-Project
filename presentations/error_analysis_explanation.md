# BIRD Execution Failure & Self-Repair Experiments

This document provides a concise breakdown of the 4 benchmark experiments conducted on BIRD Mini-Dev (500 questions), covering error analysis, self-repair recovery, and latency measurements.

---

## What the Self-Repair Loop Does

The self-repair loop provides automated, runtime-guided feedback to queries that fail SQLite execution:

- **Selective Filtering:** Filters out and targets only queries that fail SQLite execution (`is_valid_sql == False`). The remaining valid queries are preserved as-is with zero re-computation.
- **Runtime Error Feedback:** Captures the exact SQLite compiler/execution error (e.g., `no such column`, `syntax error`, `no such function`, `timeout`) and feeds it back to the model.
- **Schema Provenance Hinting:** If a column does not exist in the referenced table, the system dynamically checks the schema to locate where that column resides and provides a single-line bridge-table hint.
- **Single-Line Constrained Regeneration:** Prompts enforce direct single-line SQL output (`SQL:`), keeping repair latency fast (~3–7 seconds per query).
- **Automated Verification:** Repaired queries are immediately tested on SQLite (5s timeout) to verify validity and calculate net accuracy gain.

---

## Experiment 1: 7B Model + Full Schema

- **Setup:** `qwen2.5-coder:7b` evaluated on the full database schema (all tables, columns, and foreign keys).
- **Execution & Accuracy:**
  - **Baseline Accuracy:** **48.0%** (240 / 500 correct)
  - **Baseline Valid SQL:** 86.0% (430 / 500)
  - **Crashed Queries:** 70 queries crashed with runtime errors.
  - **Self-Repair Recovery:** Fixed **42 out of 70** failing queries (60.0% recovery rate).
  - **Post-Repair Accuracy:** **51.4%** (257 / 500 correct) $\to$ **+17 new correct queries (+3.4% gain)**
  - **Post-Repair Valid SQL:** **94.4%** (472 / 500)
- **Latency:**
  - Baseline Mean Latency: **5.81s / query** (Median: 5.60s, P95: 8.35s)
  - Full Baseline Run Time: ~45 minutes (500 queries)
  - Self-Repair Run Time: **~8.0 minutes total** (70 queries, avg **6.83s / query**)
- **Key Takeaway:**
  > Giving SQLite compiler errors back to the 7B model resolved 60% of runtime errors and pushed accuracy over 51% without any extra training.

---

## Experiment 2: 7B Model + Pruned Schema (`pruned_v2`)

- **Setup:** `qwen2.5-coder:7b` evaluated on schemas pruned via BFS graph traversal to only include question-relevant tables.
- **Execution & Accuracy:**
  - **Baseline Accuracy:** **44.6%** (223 / 500 correct)
  - **Baseline Valid SQL:** 84.2% (421 / 500)
  - **Crashed Queries:** 79 queries crashed with runtime errors.
  - **Self-Repair Recovery:** Fixed **39 out of 79** failing queries (49.4% recovery rate).
  - **Post-Repair Accuracy:** **48.6%** (243 / 500 correct) $\to$ **+20 new correct queries (+4.0% gain)**
  - **Post-Repair Valid SQL:** **92.0%** (460 / 500)
- **Latency:**
  - Baseline Mean Latency: **6.02s / query** (Median: 5.85s, P95: 8.61s)
  - Full Baseline Run Time: ~45 minutes (500 queries)
  - Self-Repair Run Time: **~9.1 minutes total** (79 queries, avg **6.93s / query**)
- **Key Takeaway:**
  > Full Schema slightly outperforms Pruned Schema for 7B (51.4% vs 48.6%) because 7B can reason across the entire relational graph. However, self-repair produced its largest single accuracy boost here (+20 queries / +4.0%).

---

## Experiment 3: 1.5B Model + Full Schema

- **Setup:** `qwen2.5-coder:1.5b` evaluated on the full database schema.
- **Execution & Accuracy:**
  - **Baseline Accuracy:** **22.8%** (114 / 500 correct)
  - **Baseline Valid SQL:** 41.2% (206 / 500)
  - **Crashed Queries:** **294 queries crashed** (~59% failure rate due to large-schema confusion).
  - **Self-Repair Recovery:** Fixed **32 out of 294** failing queries (10.9% recovery rate).
  - **Post-Repair Accuracy:** **26.2%** (131 / 500 correct) $\to$ **+17 new correct queries (+3.4% gain)**
  - **Post-Repair Valid SQL:** **47.6%** (238 / 500)
- **Latency:**
  - Baseline Mean Latency: **3.95s / query** (Median: 2.83s, P95: 3.33s)
  - Full Baseline Run Time: ~30 minutes (500 queries)
  - Self-Repair Run Time: **~14.4 minutes total** (294 queries, avg **2.95s / query**)
- **Key Takeaway:**
  > The 1.5B model struggles with full schemas, frequently hallucinating column names. Even when given error messages, it often repeats errors due to capacity limits. However, the queries it did fix were high-precision (17 of 32 became correct).

---

## Experiment 4: 1.5B Model + Pruned Schema (`pruned_v2`)

- **Setup:** `qwen2.5-coder:1.5b` evaluated on pruned schemas to remove distractor tables.
- **Execution & Accuracy:**
  - **Baseline Accuracy:** **24.8%** (124 / 500 correct)
  - **Baseline Valid SQL:** 45.0% (225 / 500)
  - **Crashed Queries:** 275 queries crashed.
  - **Self-Repair Recovery:** Fixed **24 out of 275** failing queries (8.7% recovery rate).
  - **Post-Repair Accuracy:** **27.6%** (138 / 500 correct) $\to$ **+14 new correct queries (+2.8% gain)**
  - **Post-Repair Valid SQL:** **49.8%** (249 / 500)
- **Latency:**
  - Baseline Mean Latency: **4.00s / query** (Median: 2.89s, P95: 3.37s)
  - Full Baseline Run Time: ~30 minutes (500 queries)
  - Self-Repair Run Time: **~16.7 minutes total** (275 queries, avg **3.65s / query**)
- **Key Takeaway:**
  > Schema pruning directly benefits the smaller model. The 1.5B model achieved higher accuracy with Pruned Schema than with Full Schema (27.6% vs 26.2%) because removing unused tables reduces hallucination space.

---

## Summary Tables

### 1. Accuracy & Error Recovery Comparison

| Model | Schema Setup | Baseline Accuracy | Post-Repair Accuracy | Accuracy Gain | Valid SQL (Baseline $\to$ Repaired) | Errors Fixed by Repair |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **7B Coder** | **Full Schema** | **48.0%** | **51.4%** | **+3.4% (+17 queries)** | 86.0% $\to$ **94.4%** | **42 / 70** (60.0%) |
| **7B Coder** | **Pruned v2** | **44.6%** | **48.6%** | **+4.0% (+20 queries)** | 84.2% $\to$ **92.0%** | **39 / 79** (49.4%) |
| **1.5B Coder** | **Full Schema** | **22.8%** | **26.2%** | **+3.4% (+17 queries)** | 41.2% $\to$ **47.6%** | **32 / 294** (10.9%) |
| **1.5B Coder** | **Pruned v2** | **24.8%** | **27.6%** | **+2.8% (+14 queries)** | 45.0% $\to$ **49.8%** | **24 / 275** (8.7%) |

---

### 2. Latency & Compute Efficiency Comparison

| Model | Schema Setup | Baseline Mean Latency / Query | Baseline Median Latency | Baseline Total Run Time (500 queries) | Errors Repaired (Count) | Repair Total Run Time | Repair Avg Latency / Query |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **7B Coder** | **Full Schema** | 5.81s | 5.60s | ~45 min | 70 | **~8.0 min** | 6.83s |
| **7B Coder** | **Pruned v2** | 6.02s | 5.85s | ~45 min | 79 | **~9.1 min** | 6.93s |
| **1.5B Coder** | **Full Schema** | 3.95s | 2.83s | ~30 min | 294 | **~14.4 min** | 2.95s |
| **1.5B Coder** | **Pruned v2** | 4.00s | 2.89s | ~30 min | 275 | **~16.7 min** | 3.65s |

- **Per-Query Speed:** Because repair prompts enforce direct single-line SQL without conversational explanations, individual repair queries generate in **~3s (1.5B)** and **~6.8s (7B)**.

---

## Key Conclusions

1. **Self-Repair Universally Boosts Accuracy:** Every configuration gained **+2.8% to +4.0% in Execution Accuracy** (68 total queries rescued across setups) solely through runtime error feedback.
2. **Model Scale Determines Debugging Capacity:** The 7B model successfully resolved **49.4%–60.0%** of runtime errors, whereas the 1.5B model resolved only **8.7%–10.9%**, showing that self-repair capability scales with parameter size.
3. **Pruning is Model-Dependent:**
   - **Large Model (7B):** Prefers Full Schema (**51.4% vs 48.6%**) to exploit all cross-table relationships.
   - **Small Model (1.5B):** Prefers Pruned Schema (**27.6% vs 26.2%**) to prevent hallucination across irrelevant tables.
