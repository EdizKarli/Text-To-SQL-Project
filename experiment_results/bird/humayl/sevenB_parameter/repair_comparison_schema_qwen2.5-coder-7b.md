# Self-Repair Impact Report: qwen2.5-coder:7b (schema)

## Executive Summary

- **Model**: `qwen2.5-coder:7b`
- **Prompt Setup**: `schema`
- **Total Evaluated**: 500 queries
- **Failing Queries Targeted**: 70 queries (Zero re-computation of successful queries)
- **Queries Made Valid**: 42 / 70 (60.0% recovery rate)
- **Net Execution Accuracy Gain**: +17 questions

## Baseline vs Repaired Comparison

| Metric | Baseline | Post-Repair | Delta |
|---|---|---|---|
| **Valid SQL Percentage** | 86.00% | 94.40% | **+8.40%** |
| **Execution Accuracy (EX)** | 49.20% | 52.60% | **+3.40%** |
| **Total Correct Queries** | 246 | 263 | **+17** |
| **Total Runtime Errors** | 70 | 28 | **-42** |

## Failure Breakdown Before & After

| Error Category | Baseline Errors | Post-Repair Errors | Resolved |
|---|---|---|---|
| `ambiguous_column` | 3 | 0 | +3 |
| `syntax_error` | 2 | 0 | +2 |
| `timeout` | 1 | 1 | 0 |
| `unknown_column` | 61 | 27 | +34 |
| `unknown_function` | 2 | 0 | +2 |
| `unknown_table` | 1 | 0 | +1 |
| `wrong_result` | 182 | 209 | -27 |

## Sample Successful Repairs

### Sample 1: QID 1399 (student_club) - `syntax_error`
- **Error Before**: `near "s": syntax error`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT CASE WHEN T3.first_name = 'Maya' AND T3.last_name = 'Mclean' AND T2.event_name = 'Women's Soccer' THEN 'Yes' ELSE 'No' END AS attended FROM attendance AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id INNER JOIN member AS T3 ON T1.link_to_member = T3.member_id WHERE T2.event_name = 'Women's Soccer' AND T3.first_name = 'Maya' AND T3.last_name = 'Mclean'
-- REPAIRED SQL
SELECT CASE WHEN T3.first_name = 'Maya' AND T3.last_name = 'Mclean' AND T2.event_name = 'Women''s Soccer' THEN 'Yes' ELSE 'No' END AS attended FROM attendance AS T1 INNER JOIN event AS T2 ON T1.link_to_event = T2.event_id INNER JOIN member AS T3 ON T1.link_to_member = T3.member_id WHERE T2.event_name = 'Women''s Soccer' AND T3.first_name = 'Maya' AND T3.last_name = 'Mclean'
```

### Sample 2: QID 1150 (thrombosis_prediction) - `unknown_function`
- **Error Before**: `no such function: year`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT CAST(SUM(CASE WHEN year(Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE SEX = 'F'
-- REPAIRED SQL
SELECT CAST(SUM(CASE WHEN STRFTIME('%Y', Birthday) > '1930' THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(ID) FROM Patient WHERE SEX = 'F'
```

### Sample 3: QID 1166 (thrombosis_prediction) - `ambiguous_column`
- **Error Before**: `ambiguous column name: Diagnosis`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT Symptoms, Diagnosis FROM Examination JOIN Patient ON Examination.ID = Patient.ID WHERE Symptoms IS NOT NULL ORDER BY Patient.Birthday DESC LIMIT 1
-- REPAIRED SQL
SELECT T1.Symptoms, T1.Diagnosis FROM Examination AS T1 JOIN Patient AS T2 ON T1.ID = T2.ID WHERE T1.Symptoms IS NOT NULL ORDER BY T2.Birthday DESC LIMIT 1
```

### Sample 4: QID 1169 (thrombosis_prediction) - `unknown_column`
- **Error Before**: `no such column: UA`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT CAST(SUM(CASE WHEN SEX = 'M' AND UA <= 8.0 THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN SEX = 'F' AND UA <= 6.5 THEN 1 ELSE 0 END) AS Ratio FROM Patient
-- REPAIRED SQL
SELECT CAST(SUM(CASE WHEN SEX = 'M' AND UA <= 8.0 THEN 1 ELSE 0 END) AS REAL) / SUM(CASE WHEN SEX = 'F' AND UA <= 6.5 THEN 1 ELSE 0 END) AS Ratio FROM Patient INNER JOIN Laboratory ON Patient.ID = Laboratory.ID
```

### Sample 5: QID 1175 (thrombosis_prediction) - `unknown_column`
- **Error Before**: `no such column: T1.HGB`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT strftime('%Y', T1.`Examination Date`) - strftime('%Y', T2.Birthday) AS Age, T2.Diagnosis FROM Examination AS T1 JOIN Patient AS T2 ON T1.ID = T2.ID ORDER BY T1.HGB DESC LIMIT 1
-- REPAIRED SQL
SELECT strftime('%Y', T1.`Examination Date`) - strftime('%Y', T2.Birthday) AS Age, T2.Diagnosis FROM Examination AS T1 JOIN Patient AS T2 ON T1.ID = T2.ID JOIN Laboratory AS T3 ON T2.ID = T3.ID ORDER BY T3.HGB DESC LIMIT 1
```
