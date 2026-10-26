# Air Cargo Flights – Database & Text-to-SQL Benchmark

A reproducible relational database (SQLite) of freighter-aircraft operations, built following the *Practical Guide to Building a Reliable Database Benchmark*.

**Domain:** cargo airlines fly freighters between 18 airports; customers book shipments that travel on one or two flights (connections); shipments are invoiced and paid; incidents (damage, delay, loss…) are recorded. Dataset "now" = **2025-12-20**; flights run Jan–Dec 2025.

## Size
| Table | Rows | | Table | Rows |
|---|---:|---|---|---:|
| airlines | 5 | | shipments | 3,110 |
| airports | 18 | | flight_cargo | 3,818 |
| aircraft_types | 5 | | invoices | 2,909 |
| aircraft | 22 | | payments | 2,544 |
| customers | 63 | | incidents | 160 |
| flights | 2,252 | | benchmark_meta | 4 |

## Quick start
```bash
python scripts/build_db.py --regenerate     # schema + seed -> cargo_flights.db
python validation/run_validation.py          # integrity, 40 SQL checks, clean-rebuild test
python validation/test_gold.py               # Gold SQL: executability, recomputation, edge-case fixtures
python validation/test_checks_catch_errors.py  # mutation test: do the checks catch corrupted data?
python evaluation/evaluate.py evaluation/example_predictions.json
```
Requires Python 3.8+ and SQLite 3.25+ (window functions). Load order: `schema/schema.sql` then `data/seed.sql`.

## Layout
```
schema/schema.sql            tables, keys, CHECK constraints, indexes
data/generate_data.py        deterministic generator (seed 42) -> data/seed.sql
data/seed.sql                generated INSERT statements (do not edit by hand)
questions/build_questions.py single source for 25 questions + Gold SQL -> questions.json
validation/                  validation_checks.sql, run_validation.py, test_gold.py, test_checks_catch_errors.py, report
evaluation/evaluate.py       scores model SQL by execution result; example_predictions.json
docs/ERD.md, data_dictionary.md
```

## Questions
25 questions (8 easy, 9 medium, 8 hard) with stable IDs `Q01–Q25`, each with difficulty, tested SQL concepts, an answer specification (columns, order, ties, NULL behaviour) and Gold SQL. Skills covered: filtering, aggregation, joins, `GROUP BY/HAVING`, `NOT EXISTS`, CTEs, window functions (`ROW_NUMBER`), date arithmetic, self-joins, join-multiplication traps, tie-breaking.

## Evaluation protocol
Model gets the question + schema (permitted context only). Its SQL runs read-only with a timeout; the **result** is compared to the Gold result (ordered rows, float tolerance 0.011, column names ignored). Outcomes `correct / wrong_result / execution_error / timeout / missing` are tracked separately. Latency is recorded as a separate metric. Matching on one dataset is evidence, not proof, of equivalence; `validation/test_gold.py` adds tiny constructed datasets for edge cases.

## Assumptions and limitations
* Each shipment leg carries the *entire* shipment (no splitting across flights); max two legs.
* Aircraft models, payloads, volumes and ranges are approximate public figures used for realism, not engineering data. Airline codes, tail numbers and customers are fictional.
* Flight times use a simple speed model (≈780 km/h + 50 min); delays are random, not weather-driven.
* No flight is airborne at the as-of moment; future flights are `scheduled`, and cargo is only booked on non-cancelled flights.
* Statuses of shipments/invoices are stored (denormalised) but validated against their underlying legs/payments.
* SQLite stores dates as text; Gold SQL uses `julianday()`/`substr()`. Porting to another engine needs date-function changes.
