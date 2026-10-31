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

* The natural-language questions and answer specifications are **identical** in all three files, except that *schema-aware* questions name the tables and columns of their own variant. Only the Gold SQL differs, and the Gold *results* are identical, so accuracies are directly comparable.
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
python questions/build_questions.py               # question_bank.py -> questions/questions_normal.json (480 questions)
python scripts/build_variants.py                  # -> mixed + cryptic schema, databases, questions (verified)
python scripts/make_docs.py                       # -> docs/ERD.md, docs/schema_variants.md

python validation/run_validation.py               # integrity, 20/300 shape, 94 SQL checks, clean-rebuild test
python validation/test_gold.py                    # Gold SQL: executability, recomputation, edge-case fixtures
python validation/test_checks_catch_errors.py     # mutation test: do the checks catch corrupted data?
python validation/test_variants.py                # variants: same shape, same rows, same Gold results, no name leaks

python evaluation/run_ollama.py --variant cryptic --model qwen2.5-coder:1.5b --evaluate   # ask a local model + score
python evaluation/compare_runs.py "evaluation/predictions/*_results.json" --csv comparison.csv
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
questions/question_bank.py       single source: 120 base questions, Gold SQL, answer specs and 4 phrasings each
questions/build_questions.py     question_bank.py -> questions_normal.json (480 questions)
questions/questions_<variant>.json
scripts/build_db.py, build_variants.py, naming.py, sql_translate.py, make_docs.py
validation/                      validation_checks.sql, run_validation.py, test_gold.py, test_checks_catch_errors.py,
                                 test_variants.py, validation_report.txt
evaluation/run_ollama.py         asks a local Ollama model the questions for one variant -> evaluation/predictions/
evaluation/evaluate.py           EX, strict EX, valid execution rate, latency, tokens, ms/token, tokens/s by difficulty x style
evaluation/compare_runs.py       side-by-side table of several *_results.json (variants, models)
evaluation/example_predictions.json   normal-schema example with a few deliberate mistakes
docs/ERD.md, data_dictionary.md, schema_variants.md
```

## Questions
**480 questions = 120 base questions × 4 phrasing styles**: 40 easy, 40 moderate and 40 hard base questions, so each difficulty has 160 questions (40 per style). Every base question has one Gold SQL query and one answer specification; its four phrasings ask for exactly the same thing, so the effect of *how* a question is asked can be measured directly. (Run `python questions/build_questions.py --bases-per-difficulty 30` for 360 questions: 120 per difficulty, 30 per style.)

| Style | ID suffix | What it sounds like (E14, longest flight distance) |
|---|---|---|
| Casual Talk | `-CAS` | "What's the longest flight distance we have, in km?" |
| Schema Aware Talk | `-SCH` | "Return MAX(distance_km) from flights." (rendered with each variant's names: `MAX(entf_km) from flug`, `MAX(c13) from tx7n`) |
| Business Metric / Executive Talk | `-BIZ` | "What is the longest sector length in our flight programme, in kilometres?" |
| Vague Talk | `-VAG` | "Longest flight?" |

IDs look like `E14-VAG` (base question `E14`, vague phrasing); each entry also has `base_id`, `difficulty`, `style`, `concepts`, `answer_spec` (the intended reading, important for vague questions) and `question_template`. Easy questions use one table with a filter or aggregate; moderate ones add joins, `GROUP BY/HAVING`, anti-joins and date arithmetic; hard ones need CTEs, window functions (`ROW_NUMBER`, `DENSE_RANK`, `NTILE`, `LAG`, running `SUM`), relational division, self-joins, delay propagation, Pareto shares and join-multiplication traps. Every `LIMIT` cut-off is tie-free (checked by `validation/test_gold.py`). The 45 v1/v2 questions were retired.

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
Add `--difficulty easy|moderate|hard`, `--style casual|schema_aware|business_executive|vague` or `--ids E01-CAS,H07-VAG` to run a slice. A run is saved after every question and resumes automatically if interrupted (`--restart` to start over).

Prompt = schema of the variant + (optional) evidence + question. The answer specification is **not** shown by default (it is the same for all four styles and would erase their differences); `--with-spec` adds it. `--schema compact` (default) lists columns, types, keys and allowed coded values in about 2.4k (cryptic) to 3.4k (normal) tokens, so it fits the 8k context used for small models; `--schema full` sends the whole DDL (normal is about 8.3k tokens, use `--num-ctx 16384`). Outputs in `evaluation/predictions/`: `pred_<tag>.json` (SQL), `pred_<tag>_raw.json` (raw text + Ollama counters per question) and `pred_<tag>_results.json` (scores).

## Evaluation protocol and metrics
The model gets the question and the schema of one variant (permitted context only; optionally the naming map as evidence). Its SQL runs read-only with a timeout on that variant's database. `evaluate.py` reports, overall, by difficulty, by style and as a difficulty × style grid:

| Metric | Definition |
|---|---|
| **Execution accuracy (EX)** | share of questions whose result matches the Gold result: same rows and columns, row order and column order ignored, numbers equal to the precision shown in the Gold result (62.2 matches 62.23, not 62.3), text exact |
| EX strict | rows in Gold order, columns in Gold order, tolerance 0.011 (meaningful for `--with-spec` runs) |
| **Valid execution rate (VER)** | share of questions whose SQL ran without error or timeout, right or wrong |
| **Latency** | wall-clock seconds per question for the model call: mean, median, p95, total |
| **Tokens created** | tokens generated by the model (Ollama `eval_count`): mean and total; prompt tokens are reported too |
| **Latency per token** | total latency / total tokens created, in ms/token (includes prompt processing and loading) |
| **Tokens per second** | total tokens created / total generation time (Ollama `eval_duration`): pure decoding speed |

Outcomes `correct / wrong_result / execution_error / timeout / missing` are kept per question in the results file. `compare_runs.py` puts several runs side by side (e.g. normal vs mixed vs cryptic, 1.5B vs 7B). Matching on one dataset is evidence, not proof, of equivalence; `validation/test_gold.py` adds tiny constructed datasets for edge cases.

## Assumptions and limitations
* Each shipment leg carries the *entire* shipment in one ULD (no splitting across flights); max two legs.
* Aircraft models, weights, fuel figures and airport facilities are approximate public figures used for realism, not engineering data. Airline codes, tail numbers, people and companies are fictional.
* Flight times use a simple speed model (≈780 km/h + 50 min); delays and weather are random.
* Crew rostering enforces airline, type rating, licence validity and ≥ 12 h rest, but not crew location between duties.
* No flight is airborne at the as-of moment; future flights are `scheduled`, and cargo is only booked on non-cancelled flights.
* `delivered` means the final leg has landed; handover to the consignee is the `DLV` tracking event, which can be blocked by an import customs hold.
* Statuses of shipments/invoices/claims are stored (denormalised) but validated against their underlying rows.
* SQLite stores dates as text; Gold SQL uses `julianday()`/`substr()`. Porting to another engine needs date-function changes.
