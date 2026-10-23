# Self-Repair Impact Report: qwen2.5-coder:1.5b (pruned_v2)

## Executive Summary

- **Model**: `qwen2.5-coder:1.5b`
- **Prompt Setup**: `pruned_v2`
- **Total Evaluated**: 500 queries
- **Failing Queries Targeted**: 275 queries (Zero re-computation of successful queries)
- **Queries Made Valid**: 24 / 275 (8.73% recovery rate)
- **Net Execution Accuracy Gain**: +14 questions

## Baseline vs Repaired Comparison

| Metric | Baseline | Post-Repair | Delta |
|---|---|---|---|
| **Valid SQL Percentage** | 45.00% | 49.80% | **+4.80%** |
| **Execution Accuracy (EX)** | 25.60% | 28.40% | **+2.80%** |
| **Total Correct Queries** | 128 | 142 | **+14** |
| **Total Runtime Errors** | 275 | 251 | **-24** |

## Failure Breakdown Before & After

| Error Category | Baseline Errors | Post-Repair Errors | Resolved |
|---|---|---|---|
| `aggregate_misuse` | 6 | 7 | -1 |
| `ambiguous_column` | 0 | 1 | -1 |
| `other_sql_error` | 1 | 1 | 0 |
| `request_failed` | 3 | 0 | +3 |
| `syntax_error` | 15 | 11 | +4 |
| `unknown_column` | 236 | 225 | +11 |
| `unknown_function` | 11 | 3 | +8 |
| `unknown_table` | 3 | 3 | 0 |
| `wrong_result` | 95 | 107 | -12 |

## Sample Successful Repairs

### Sample 1: QID 1312 (student_club) - `unknown_column`
- **Error Before**: `no such column: T1.major_name`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT T1.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.first_name = 'Angela' AND T1.last_name = 'Sanders'
-- REPAIRED SQL
SELECT T2.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.first_name = 'Angela' AND T1.last_name = 'Sanders'
```

### Sample 2: QID 1317 (student_club) - `syntax_error`
- **Error Before**: `near "s": syntax error`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT COUNT(T1.member_id) FROM member AS T1 INNER JOIN attendance AS T2 ON T1.member_id = T2.link_to_member INNER JOIN event AS T3 ON T2.link_to_event = T3.event_id WHERE T3.event_name = 'Women's Soccer' AND T1.t_shirt_size = 'Medium'
-- REPAIRED SQL
SELECT COUNT(T1.member_id) FROM member AS T1 INNER JOIN attendance AS T2 ON T1.member_id = T2.link_to_member INNER JOIN event AS T3 ON T2.link_to_event = T3.event_id WHERE T3.event_name = 'Women''s Soccer' AND T1.t_shirt_size = 'Medium'
```

### Sample 3: QID 1368 (student_club) - `unknown_column`
- **Error Before**: `no such column: T1.major_name`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT T1.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.phone = '809-555-3360'
-- REPAIRED SQL
SELECT T2.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.phone = '809-555-3360'
```

### Sample 4: QID 1399 (student_club) - `syntax_error`
- **Error Before**: `near "s": syntax error`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT COUNT(*) FROM attendance WHERE link_to_member IN (SELECT member_id FROM member WHERE first_name = 'Maya' AND last_name = 'Mclean') AND link_to_event IN (SELECT event_id FROM event WHERE event_name = 'Women's Soccer')
-- REPAIRED SQL
SELECT COUNT(*) FROM attendance WHERE link_to_member IN (SELECT member_id FROM member WHERE first_name = 'Maya' AND last_name = 'Mclean') AND link_to_event IN (SELECT event_id FROM event WHERE event_name = 'Women''s Soccer')
```

### Sample 5: QID 1150 (thrombosis_prediction) - `unknown_function`
- **Error Before**: `no such function: year`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT CAST(COUNT(CASE WHEN year(Birthday) > '1930' AND SEX = 'F' THEN ID END) AS REAL) * 100 / COUNT(CASE WHEN SEX = 'F' THEN ID END) FROM Patient
-- REPAIRED SQL
SELECT CAST(COUNT(CASE WHEN STRFTIME('%Y', Birthday) > '1930' AND SEX = 'F' THEN ID END) AS REAL) * 100 / COUNT(CASE WHEN SEX = 'F' THEN ID END) FROM Patient
```
