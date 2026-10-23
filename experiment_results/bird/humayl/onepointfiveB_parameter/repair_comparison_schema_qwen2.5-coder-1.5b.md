# Self-Repair Impact Report: qwen2.5-coder:1.5b (schema)

## Executive Summary

- **Model**: `qwen2.5-coder:1.5b`
- **Prompt Setup**: `schema`
- **Total Evaluated**: 500 queries
- **Failing Queries Targeted**: 294 queries (Zero re-computation of successful queries)
- **Queries Made Valid**: 32 / 294 (10.88% recovery rate)
- **Net Execution Accuracy Gain**: +17 questions

## Baseline vs Repaired Comparison

| Metric | Baseline | Post-Repair | Delta |
|---|---|---|---|
| **Valid SQL Percentage** | 41.20% | 47.60% | **+6.40%** |
| **Execution Accuracy (EX)** | 23.60% | 27.00% | **+3.40%** |
| **Total Correct Queries** | 118 | 135 | **+17** |
| **Total Runtime Errors** | 294 | 262 | **-32** |

## Failure Breakdown Before & After

| Error Category | Baseline Errors | Post-Repair Errors | Resolved |
|---|---|---|---|
| `aggregate_misuse` | 6 | 5 | +1 |
| `ambiguous_column` | 0 | 1 | -1 |
| `other_sql_error` | 1 | 1 | 0 |
| `request_failed` | 3 | 0 | +3 |
| `syntax_error` | 17 | 14 | +3 |
| `unknown_column` | 251 | 232 | +19 |
| `unknown_function` | 11 | 4 | +7 |
| `unknown_table` | 5 | 5 | 0 |
| `wrong_result` | 86 | 103 | -17 |

## Sample Successful Repairs

### Sample 1: QID 1317 (student_club) - `syntax_error`
- **Error Before**: `near "s": syntax error`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT COUNT(member.member_id) FROM member JOIN attendance ON member.member_id = attendance.link_to_member JOIN event ON attendance.link_to_event = event.event_id WHERE event.event_name = 'Women's Soccer' AND member.t_shirt_size = 'Medium'
-- REPAIRED SQL
SELECT COUNT(member.member_id) FROM member JOIN attendance ON member.member_id = attendance.link_to_member JOIN event ON attendance.link_to_event = event.event_id WHERE event.event_name = 'Women''s Soccer' AND member.t_shirt_size = 'Medium'
```

### Sample 2: QID 1368 (student_club) - `unknown_column`
- **Error Before**: `no such column: T1.major_name`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT T1.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.phone = '809-555-3360'
-- REPAIRED SQL
SELECT T2.major_name FROM member AS T1 INNER JOIN major AS T2 ON T1.link_to_major = T2.major_id WHERE T1.phone = '809-555-3360'
```

### Sample 3: QID 1375 (student_club) - `unknown_column`
- **Error Before**: `no such column: department`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT first_name, last_name FROM member WHERE department = 'School of Applied Sciences, Technology and Education'
-- REPAIRED SQL
SELECT m.first_name, m.last_name FROM member m JOIN major m2 ON m.link_to_major = m2.major_id WHERE m2.department = 'School of Applied Sciences, Technology and Education'
```

### Sample 4: QID 1399 (student_club) - `syntax_error`
- **Error Before**: `near "s": syntax error`
- **Correct After?**: No (Valid SQL, Different Result)
```sql
-- FAILED SQL
SELECT COUNT(*) FROM attendance WHERE link_to_member = (SELECT member_id FROM member WHERE first_name = 'Maya' AND last_name = 'Mclean') AND link_to_event = (SELECT event_id FROM event WHERE event_name = 'Women's Soccer')
-- REPAIRED SQL
SELECT COUNT(*) FROM attendance WHERE link_to_member = (SELECT member_id FROM member WHERE first_name = 'Maya' AND last_name = 'Mclean') AND link_to_event = (SELECT event_id FROM event WHERE event_name = 'Women''s Soccer')
```

### Sample 5: QID 1432 (student_club) - `unknown_column`
- **Error Before**: `no such column: member_id`
- **Correct After?**: Yes
```sql
-- FAILED SQL
SELECT CAST(SUM(CASE WHEN amount = 50 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(member_id) FROM income WHERE t_shirt_size = 'Medium' AND position = 'Member'
-- REPAIRED SQL
SELECT CAST(SUM(CASE WHEN amount = 50 THEN 1 ELSE 0 END) AS REAL) * 100 / COUNT(member_id) FROM income AS T1 INNER JOIN member AS T2 ON T1.link_to_member = T2.member_id WHERE T2.t_shirt_size = 'Medium' AND T2.position = 'Member'
```
