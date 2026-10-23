# Text-to-SQL Benchmark & Self-Repair Evaluation Report

**Project:** Graduation Project (ENS 491)  
**Benchmark:** BIRD Mini-Dev (500 Questions, SQLite)  
**Models:** `Qwen2.5-Coder-7B-Instruct` & `Qwen2.5-Coder-1.5B-Instruct` (via Ollama)  
**Setups:** Full Schema (Synthetic DDL + FKs) vs. Pruned Schema (`pruned_v2` BFS Graph Pruner)  
**Date:** October 2026  

---

## 1. Executive Summary

This report evaluates SQL generation performance, failure modes, and execution-guided self-repair across 4 baseline configurations (500 questions each) on the BIRD Mini-Dev benchmark.

- **Universal EX Improvement:** 1-turn error-feedback repair improved Official Execution Accuracy (EX) across all configurations by **+2.80% to +4.00%** (+68 net queries solved).
- **Highest Performance:** `Qwen2.5-Coder-7B` with Full Schema reached **51.40% Official EX** and **94.40% Valid SQL** (baseline: 48.00% EX, 86.00% Valid SQL).
- **Pruning Effect on Model Scales:** Schema pruning improved performance for the smaller 1.5B model (**27.60% EX** vs. 26.20% Full Schema), whereas the 7B model performed best with Full Schema (**51.40% EX** vs. 48.60% Pruned).

---

## 2. Benchmark Results (Baseline vs. Post-Repair)

All metrics evaluated across all 500 questions of BIRD Mini-Dev:

| Model | Schema Setup | Baseline Valid SQL % | Post-Repair Valid SQL % | Valid SQL Delta | Baseline Official EX | Post-Repair Official EX | Official EX Delta | Correct Queries (Detailed) | Failing Queries Targeted | Error Recovery Rate |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Qwen 2.5-Coder 7B** | **Full Schema** | 86.00% | **94.40%** | **+8.40%** | 48.00% | **51.40%** | **+3.40%** | 240 $\to$ **257** (+17) | 70 | **60.0%** (42/70) |
| **Qwen 2.5-Coder 7B** | **Pruned v2** | 84.20% | **92.00%** | **+7.80%** | 44.60% | **48.60%** | **+4.00%** | 223 $\to$ **243** (+20) | 79 | **49.4%** (39/79) |
| **Qwen 2.5-Coder 1.5B** | **Full Schema** | 41.20% | **47.60%** | **+6.40%** | 22.80% | **26.20%** | **+3.40%** | 114 $\to$ **131** (+17) | 294 | **10.9%** (32/294) |
| **Qwen 2.5-Coder 1.5B** | **Pruned v2** | 45.00% | **49.80%** | **+4.80%** | 24.80% | **27.60%** | **+2.80%** | 124 $\to$ **138** (+14) | 275 | **8.7%** (24/275) |

*Official EX evaluated with BIRD's official `evaluation_ex.py` with 30s timeout per query.*

---

## 3. Self-Repair Methodology

The self-repair loop provides deterministic execution feedback to queries that fail SQLite execution:

- **Zero-Waste Selective Repair:** Only queries that produce runtime errors (`is_valid_sql == False`) are re-prompted. Already-valid queries are preserved as-is.
- **Compiler Error Injection:** The prompt includes the failed SQL and the exact SQLite runtime error trace (`unknown_column`, `syntax_error`, `unknown_function`, `timeout`).
- **Schema Provenance Hinting:** For `unknown_column` errors, the system inspects `dev_tables.json` and supplies the valid table locations for the missing column to guide join-path correction.
- **Constrained Output:** The model is instructed to output only the corrected single-line SQL statement, maintaining low inference latency (~3–7 seconds per query).
- **Immediate Execution Verification:** Repaired queries are executed against SQLite with a 5-second timeout to verify validity and measure accuracy gains.

---

## 4. Failure Breakdown & Resolution

### Qwen 2.5-Coder 7B (Full Schema)
| Error Category | Baseline Errors | Post-Repair Errors | Resolved | Resolution Rate |
| :--- | :---: | :---: | :---: | :---: |
| `syntax_error` | 2 | **0** | +2 | **100.0%** |
| `unknown_function` | 2 | **0** | +2 | **100.0%** |
| `ambiguous_column` | 3 | **0** | +3 | **100.0%** |
| `unknown_table` | 1 | **0** | +1 | **100.0%** |
| `unknown_column` (Column Hallucination) | 61 | **27** | +34 | **55.7%** |
| `timeout` | 1 | 1 | 0 | 0.0% |
| **Total Execution Errors** | **70** | **28** | **-42** | **60.0%** |

### Qwen 2.5-Coder 1.5B (Pruned v2)
| Error Category | Baseline Errors | Post-Repair Errors | Resolved |
| :--- | :---: | :---: | :---: |
| `syntax_error` | 15 | **11** | +4 |
| `unknown_function` | 11 | **3** | +8 |
| `unknown_column` | 236 | **225** | +11 |
| **Total Execution Errors** | **275** | **251** | **-24** |

---

## 5. Key Findings

1. **Parameter Scale Affects Self-Correction:**
   - The **7B model** corrected **49.4% to 60.0%** of execution failures when provided error feedback.
   - The **1.5B model** corrected only **8.7% to 10.9%** of failures, showing that self-repair capability depends heavily on model capacity.

2. **Schema Pruning Benefits Small Models:**
   - For `1.5B`, **Pruned Schema outperformed Full Schema** across all metrics (27.60% vs. 26.20% EX, 49.80% vs. 47.60% Valid SQL), confirming that reducing distractor schema tokens is beneficial for lower-capacity models.
   - For `7B`, **Full Schema yielded the highest overall ceiling (51.40% EX)**, showing that larger models can effectively exploit complete relational foreign-key context.

3. **Nature of Resolved Errors:**
   - Dialect and syntax errors (`year()` vs. `STRFTIME`, unescaped string literal quotes, missing table aliases) were **100% resolved** in a single repair turn on 7B.
   - Multi-table join hallucinations (`unknown_column`) were reduced by **55.7%** with schema provenance hints.
