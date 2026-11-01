# Cargo Benchmark: Question Styles, Evaluation and First Results (03.11)

## 1. The questions

Our cargo database has 20 tables and 300 columns. It comes in three versions with the same data and different names:

| Version | Example table.column |
|---|---|
| Normal | `shipments.declared_value_usd` |
| Mixed (German abbreviations) | `sndg.dekl_wert_usd` |
| Cryptic (meaningless names) | `t89v.c16` |

We wrote 120 base questions: 40 easy, 40 moderate and 40 hard. Each one is written in 4 styles, which gives 480 questions in total. The 4 versions of a question have the same correct SQL, so only the wording changes.

| Style | Example (longest flight distance) |
|---|---|
| Casual | "What's the longest flight distance we have, in km?" |
| Schema Aware | "Return MAX(distance_km) from flights." |
| Business / Executive | "What is the longest sector length in our flight programme, in kilometres?" |
| Vague | "Longest flight?" |

Schema Aware questions use the names of each version. In the cryptic version, the example becomes "Return MAX(c13) from tx7n."

Easy questions use one table. Moderate questions need joins and grouping. Hard questions need CTEs, window functions and several steps.

## 2. How we evaluate

1. The model (Qwen2.5 Coder 7B on Ollama) gets the schema and the question. It does not see the expected answer format.
2. Its SQL runs on the database, and we compare the result with the result of the correct SQL.
3. We measure these values:

| Metric | Meaning |
|---|---|
| EX (execution accuracy) | Share of questions with the correct result. Row order, column order and small rounding are ignored. |
| VER (valid execution rate) | Share of SQL that runs without an error, even if the answer is wrong. |
| Latency | Seconds per question. Timed out calls are not counted. |
| Tokens | Number of tokens the model writes. |
| ms per token | Latency divided by tokens. This includes reading the prompt. |
| Tokens per second | Pure writing speed of the model. |

## 3. Results (Qwen2.5 Coder 7B, 480 questions per version)

| Version | EX % | VER % | Latency (s) | Tokens | ms/token | Tokens/s |
|---|---:|---:|---:|---:|---:|---:|
| Normal | 39.0 | 77.1 | 3.38 | 53.2 | 63.5 | 47.5 |
| Mixed | 34.2 | 70.8 | 3.50 | 59.6 | 58.7 | 47.6 |
| Cryptic | 16.5 | 92.1 | 3.29 | 49.9 | 65.9 | 47.3 |

EX % by difficulty:

| Version | Easy | Moderate | Hard |
|---|---:|---:|---:|
| Normal | 78.8 | 33.8 | 4.4 |
| Mixed | 74.4 | 23.1 | 5.0 |
| Cryptic | 41.9 | 6.2 | 1.2 |

EX % by style:

| Version | Casual | Schema Aware | Business | Vague |
|---|---:|---:|---:|---:|
| Normal | 41.7 | 59.2 | 35.0 | 20.0 |
| Mixed | 36.7 | 53.3 | 32.5 | 14.2 |
| Cryptic | 10.0 | 41.7 | 10.0 | 4.2 |

## 4. What the results show

**Names matter.** Accuracy falls from 39.0% (normal) to 34.2% (mixed) and to 16.5% (cryptic). Abbreviations hurt a little. Meaningless names hurt a lot.

**Cryptic SQL runs but is wrong.** Cryptic has the highest VER (92.1%) but the lowest EX (16.5%). The model writes valid SQL, but it picks the wrong columns because the names give no clue.

**Difficulty is the biggest factor.** The model solves most easy questions, about a third of moderate ones and almost no hard ones.

**Wording matters.** Schema Aware is always the best style, because the question names the columns. Vague is always the worst. Schema Aware questions also help the most on the cryptic version: 41.7% against 10% or less for the other styles.

**Speed is the same in every version.** The model writes about 47 tokens per second and needs about 3.3 to 3.5 seconds per question. Harder questions take longer mainly because the SQL is longer.

## 5. Next steps

1. Run the same tests with the 1.5B model and compare.
2. Give the naming map as a hint (evidence) in the mixed and cryptic versions.
3. Look at the errors in moderate and hard questions.
4. Try to implement Pass 1 and Pass 2 approach with possible model help in Pass 1. 