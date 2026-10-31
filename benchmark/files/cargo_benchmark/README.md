# Air Cargo Flights – Database & Text-to-SQL Benchmark (v2: 20 tables, 300 columns, 3 schema variants)

A reproducible relational database (SQLite) of freighter-aircraft operations, built following the *Practical Guide to Building a Reliable Database Benchmark*.

**Domain:** five cargo airlines fly freighters between 18 airports. Customers book shipments that travel on one or two flights; shipments are loaded in ULDs, cleared through customs, scanned at warehouses, invoiced and paid; crews are rostered on flights; aircraft are fuelled and maintained; incidents (damage, delay, loss…) may lead to insurance claims. Dataset "now" = **2025-12-20**; flights run Jan–Dec 2025.

## Three schema variants, one dataset
The same rows are published under three naming styles so that the effect of schema naming on text-to-SQL accuracy can be measured in isolation:

| Variant | Example | Schema file | Database | Questions |
|---|---|---|---|---|
| **normal** – human-readable | `shipments.declared_value_usd` | `schema/schema.sql` | `databases/cargo_normal.db` | `questions/questions_normal.json` |
| **mixed** – SAP-style abbreviations, mostly German | `sndg.dekl_wert_usd` | `schema/schema_mixed.sql` | `databases/cargo_mixed.db` | `questions/questions_mixed.json` |
| **cryptic** – meaningless names | `t89v.c16` | `schema/schema_cryptic.sql` | `databases/cargo_cryptic.db` | `questions/questions_cryptic.json` |

* The natural-language questions and answer specifications are **identical** in all three files; only the Gold SQL differs. The Gold *results* are identical too, so accuracies are directly comparable.
* The normal schema is the single source of truth. `scripts/build_variants.py` renames it with the maps in `scripts/naming.py`, copies the data, translates every Gold query with `scripts/sql_translate.py` (sqlglot) and verifies that each translated query returns exactly the normal result.
* `schema/naming_map.json` (and the readable `docs/schema_variants.md`) list every table and column in all three forms, including a glossary of the German abbreviations. They can be given to a model as optional "evidence" in a with-dictionary experiment.
* Cryptic DDL has its comments removed (they would reveal meaning). CHECK constraints and data values (e.g. `'completed'`, `'FRA'`) stay in English in every variant.

## Size
| Table | Rows | Cols | | Table | Rows | Cols |
|---|---:|---:|---|---|---:|---:|
| airports | 18 | 17 | | shipments | 3,110 | 22 |
| airlines | 5 | 14 | | flight_cargo | 3,818 | 12 |
| aircraft_types | 5 | 16 | | invoices | 2,909 | 15 |
| aircraft | 22 | 16 | | payments | 2,544 | 12 |
| customers | 63 | 18 | | incidents | 160 | 15 |
| warehouses | 54 | 16 | | insurance_claims | 78 | 16 |
| crew_members | 235 | 16 | | customs_declarations | 4,181 | 18 |
| flights | 2,252 | 19 | | tracking_events | 22,104 | 12 |
| crew_assignments | 5,630 | 12 | | benchmark_meta | 5 | 2 |
| maintenance_records | 450 | 16 | | | | |
| fuel_uplifts | 2,092 | 16 | | **total: 20 tables** | | **300** |

## Quick start
```bash
pip install sqlglot                               # only needed by build_variants.py (tested with sqlglot 30.20)
python scripts/build_db.py --regenerate           # schema + seed -> databases/cargo_normal.db
python questions/build_questions.py               # -> questions/questions_normal.json
python scripts/build_variants.py                  # -> mixed + cryptic schema, databases, questions (verified)
python scripts/make_docs.py                       # -> docs/ERD.md, docs/schema_variants.md

python validation/run_validation.py               # integrity, 20/300 shape, 94 SQL checks, clean-rebuild test
python validation/test_gold.py                    # Gold SQL: executability, recomputation, edge-case fixtures
python validation/test_checks_catch_errors.py     # mutation test: do the checks catch corrupted data?
python validation/test_variants.py                # variants: same shape, same rows, same Gold results, no name leaks

python evaluation/evaluate.py my_predictions.json --variant cryptic
```
Requires Python 3.8+ and SQLite 3.25+ (window functions). The committed databases and JSON files are already built; the commands above only need to be re-run after a change.

## Layout
```
schema/schema.sql                normal schema (source of truth): tables, keys, CHECK constraints, indexes
schema/schema_mixed.sql          generated
schema/schema_cryptic.sql        generated
schema/naming_map.json           generated: normal -> mixed -> cryptic for every table and column
data/generate_data.py            deterministic generator (seed 42; extension stream seed 43) -> data/seed.sql
data/seed.sql                    generated INSERT statements for the normal schema (do not edit by hand)
databases/cargo_<variant>.db     built databases
questions/build_questions.py     single source for 45 questions + normal Gold SQL -> questions_normal.json
questions/questions_<variant>.json
scripts/build_db.py, build_variants.py, naming.py, sql_translate.py, make_docs.py
validation/                      validation_checks.sql, run_validation.py, test_gold.py, test_checks_catch_errors.py,
                                 test_variants.py, validation_report.txt
evaluation/run_ollama.py         asks a local Ollama model the questions for one variant -> evaluation/predictions/
evaluation/evaluate.py           scores model SQL by execution result (--variant); example_predictions.json (normal)
docs/ERD.md, data_dictionary.md, schema_variants.md
```

## Questions
45 questions (14 easy, 15 medium, 16 hard) with stable IDs `Q01–Q45`, each with difficulty, tested SQL concepts, an answer specification (columns, order, ties, NULL behaviour) and Gold SQL. Q01–Q25 are unchanged from v1 (same answers: the v1 rows are reproduced exactly); Q26–Q45 use the new tables. Skills covered: filtering, aggregation, joins, multi-hop joins, `GROUP BY/HAVING`, `EXISTS / NOT EXISTS`, `LEFT JOIN` + `COALESCE`, CTEs, window functions (`ROW_NUMBER`, `LAG` in checks), date arithmetic, ratios of sums, conditional aggregation, self-joins, join-multiplication traps, tie-breaking.

## Running a local model (Ollama)
`evaluation/run_ollama.py` sends every question to a model served by [Ollama](https://ollama.com) (same setup as the BIRD scripts in `codes/bird`) and writes a predictions file that `evaluate.py` scores. Run it once per variant; the questions are the same, only the schema in the prompt and the target database change.
```bash
ollama pull qwen2.5-coder:1.5b                    # once; keep `ollama serve` running
python evaluation/run_ollama.py --variant normal  --model qwen2.5-coder:1.5b --evaluate
python evaluation/run_ollama.py --variant mixed   --model qwen2.5-coder:1.5b --evaluate
python evaluation/run_ollama.py --variant cryptic --model qwen2.5-coder:1.5b --evaluate
python evaluation/run_ollama.py --variant cryptic --model qwen2.5-coder:1.5b --evidence --evaluate   # + naming-map hints
python evaluation/run_ollama.py --variant normal --print-prompt   # inspect the exact prompt, no model call
```
Prompt = schema of the variant + (optional) evidence + question + answer specification. `--schema compact` (default) lists columns, types, keys and allowed coded values in about 2.4k (cryptic) to 3.4k (normal) tokens, so it fits the 8k context used for small models; `--schema full` sends the whole DDL (normal is about 8.3k tokens). Outputs go to `evaluation/predictions/pred_<variant>_<model>_<schema>[_evidence].json`, plus `_raw.json` (raw model text, seconds per question) and `_results.json` (per-question outcome).

## Evaluation protocol
Model gets the question + the schema of one variant (permitted context only; optionally the naming map as evidence). Its SQL runs read-only with a timeout on that variant's database; the **result** is compared to the Gold result (ordered rows, float tolerance 0.011, column names ignored). Outcomes `correct / wrong_result / execution_error / timeout / missing` are tracked separately. Latency is recorded as a separate metric. Matching on one dataset is evidence, not proof, of equivalence; `validation/test_gold.py` adds tiny constructed datasets for edge cases.

## Assumptions and limitations
* Each shipment leg carries the *entire* shipment in one ULD (no splitting across flights); max two legs.
* Aircraft models, weights, fuel figures and airport facilities are approximate public figures used for realism, not engineering data. Airline codes, tail numbers, people and companies are fictional.
* Flight times use a simple speed model (≈780 km/h + 50 min); delays and weather are random.
* Crew rostering enforces airline, type rating, licence validity and ≥ 12 h rest, but not crew location between duties.
* No flight is airborne at the as-of moment; future flights are `scheduled`, and cargo is only booked on non-cancelled flights.
* `delivered` means the final leg has landed; handover to the consignee is the `DLV` tracking event, which can be blocked by an import customs hold.
* Statuses of shipments/invoices/claims are stored (denormalised) but validated against their underlying rows.
* SQLite stores dates as text; Gold SQL uses `julianday()`/`substr()`. Porting to another engine needs date-function changes.
