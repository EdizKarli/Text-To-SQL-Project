# Self-Repair Impact Report: qwen2.5-coder:7b (pruned_v2)

## Executive Summary

- **Model**: `qwen2.5-coder:7b`
- **Prompt Setup**: `pruned_v2`
- **Total Evaluated**: 500 queries
- **Failing Queries Targeted**: 79 queries (Zero re-computation of successful queries)
- **Queries Made Valid**: 39 / 79 (49.37% recovery rate)
- **Net Execution Accuracy Gain**: +20 questions

## Baseline vs Repaired Comparison

| Metric | Baseline | Post-Repair | Delta |
|---|---|---|---|
| **Valid SQL Percentage** | 84.20% | 92.00% | **+7.80%** |
| **Execution Accuracy (EX)** | 45.80% | 49.80% | **+4.00%** |
| **Total Correct Queries** | 229 | 249 | **+20** |
| **Total Runtime Errors** | 79 | 40 | **-39** |

## Failure Breakdown Before & After

| Error Category | Baseline Errors | Post-Repair Errors | Resolved |
|---|---|---|---|
| `aggregate_misuse` | 3 | 1 | +2 |
| `ambiguous_column` | 2 | 0 | +2 |
| `syntax_error` | 3 | 2 | +1 |
| `timeout` | 1 | 2 | -1 |
| `unknown_column` | 66 | 33 | +33 |
| `unknown_function` | 2 | 0 | +2 |
| `unknown_table` | 2 | 2 | 0 |
| `wrong_result` | 190 | 211 | -21 |

## Sample Successful Repairs

### Sample 1: QID 1356 (student_club) - `unknown_column`
- **Error Before**: `no such column: T1.department`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT T1.department FROM member AS T1 JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.position = 'President'
-- REPAIRED SQL
SELECT T2.department FROM member AS T1 JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.position = 'President'
```

### Sample 2: QID 1362 (student_club) - `unknown_column`
- **Error Before**: `no such column: state`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT COUNT(*) FROM member WHERE major IN (SELECT major_id FROM major WHERE college IN (SELECT college FROM major WHERE department IN (SELECT department FROM major WHERE college = 'Orange County' AND state = 'Virginia')))
-- REPAIRED SQL
SELECT COUNT(*) FROM member WHERE link_to_major IN (SELECT major_id FROM major WHERE college IN (SELECT college FROM major WHERE department IN (SELECT department FROM major WHERE college = 'Orange County')))
```

### Sample 3: QID 1150 (thrombosis_prediction) - `unknown_function`
- **Error Before**: `no such function: year`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT CAST(SUM(CASE WHEN year(Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE SEX = 'F'
-- REPAIRED SQL
SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE SEX = 'F'
```

### Sample 4: QID 1166 (thrombosis_prediction) - `ambiguous_column`
- **Error Before**: `ambiguous column name: Diagnosis`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT Symptoms, Diagnosis FROM Examination JOIN Patient ON Examination.ID = Patient.ID WHERE Symptoms IS NOT NULL ORDER BY Patient.Birthday DESC LIMIT 1
-- REPAIRED SQL
SELECT T1.Symptoms, T1.Diagnosis FROM Examination AS T1 JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.Symptoms IS NOT NULL ORDER BY T2.Birthday DESC LIMIT 1
```

### Sample 5: QID 1169 (thrombosis_prediction) - `unknown_column`
- **Error Before**: `no such column: UA`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT CAST(SUM(CASE WHEN SEX = 'M' AND UA <= 8.0 THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN SEX = 'F' AND UA <= 6.5 THEN 1 ELSE 0 END) AS Ratio FROM Patient
-- REPAIRED SQL
SELECT CAST(SUM(CASE WHEN P.SEX = 'M' AND L.UA <= 8.0 THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN P.SEX = 'F' AND L.UA <= 6.5 THEN 1 ELSE 0 END) AS Ratio FROM Patient P JOIN Laboratory L ON P.ID = L.ID
```
