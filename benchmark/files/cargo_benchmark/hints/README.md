# Reasoning hints

One hint for every question in the cargo benchmark: 960 questions × 3 variants = 2880 hints.

Each hint uses the same skeleton:

```
#question  the question, exactly as in the benchmark
#schema    the tables and columns the hint uses, with the variant's names
#think     Goal, Output columns, Interpretation
#trace     1. Source  2. Joins  3. Filters  4. Grouping/aggregation  5. Ordering/limits  6. Traps
#sql       the Gold SQL of that variant, unchanged
```

## Files

| file | what it is |
|---|---|
| `hint_bank_easy.py`, `hint_bank_moderate.py`, `hint_bank_hard.py` | the hand-written reasoning, one entry per base question (E01-E80, M01-M80, H01-H80) |
| `build_hints.py` | turns the bank into hints for each variant |
| `validate_hints.py` | checks every hint |
| `hints_normal.jsonl`, `hints_mixed.jsonl`, `hints_cryptic.jsonl` | the hints, one JSON row per question: `id, base_id, variant, style, difficulty, hint` |

## How it works

The reasoning is written once per base question, with normal names inside placeholders
(`[[table]]`, `[[table.column]]`, `{{table.column}}`). `build_hints.py` fills them with the names of
each variant from `schema/naming_map.json`. In mixed and cryptic, the meaning is shown once in the
#schema line, e.g. `sndg (shipments)`.

The four phrasings of a question share the #trace. #question and the Interpretation line follow the
phrasing:
- schema_aware: no interpretation needed, the question names the tables and columns
- vague: the reading taken from the answer_spec
- casual and business_executive: the plain-language meaning of the key words

## Checks

`validate_hints.py` checks that:
- every hint has the full skeleton and each step is one line
- #question is the benchmark text and #sql is exactly the Gold SQL
- #sql runs on the matching database and returns the Gold result
- every table and column in #schema exists in that variant
- no normal name slips into a mixed or cryptic hint
- there are 960 hints per variant

```
cd benchmark/files/cargo_benchmark
python hints/build_hints.py
python hints/validate_hints.py      # all 2880 hints pass
```

The facts the traps rely on (for example: takeoff weight is only filled for completed flights,
each shipment has at most one DLV scan, each incident has at most one claim) were checked on the data.
