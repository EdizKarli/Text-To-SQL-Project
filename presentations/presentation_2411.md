1. Doubled the questions: 480 → 960.
2. Split the questions 80/20 for fine-tuning.
3. Wrote the fine-tuning code for the school's GPU cluster.
4. Built a data dictionary for the cryptic schema and tested it.
5. Built and tested a two-pass pipeline: first find the tables, then write the SQL.


## Twice as many questions: 480 → 960

We wrote 120 new base questions (E41–E80, M41–M80, H41–H80). As before, each one has 4 styles (casual, schema aware, business, vague) and one correct SQL.

| | Base questions | Questions |
|---|---:|---:|
| Easy | 80 | 320 |
| Moderate | 80 | 320 |
| Hard | 80 | 320 |
| **Total** | **240** | **960** |

* **New kinds of questions:** moving averages, medians, streaks of consecutive days, a list of months that includes months with zero, invoice ageing buckets, second-highest per group, `NOT EXISTS` and `DISTINCT`.
* **All three schemas:** the correct SQL was translated to mixed and cryptic and gives the same result in all three.
* **Hints:** every question has a hint in all three schemas, 2,880 hints in total, all checked.

## 3. The 80/20 split

For fine-tuning, the model must be tested on questions it never saw in training. So we split by **base question**: all 4 styles and all 3 schemas of a question are always on the same side. Otherwise the model could learn the casual version and then easily answer the vague one.

| Part | Base questions | Questions per schema | Used for |
|---|---:|---:|---|
| Train | 171 | 684 | learning |
| Dev | 21 | 84 | choosing when to stop training |
| Test | 48 (20%) | 192 | the final score only |

* Each part has the same number of easy, moderate and hard questions.

## 4. Fine-tuning Ideas

We will compare two versions of Qwen2.5 Coder (1.5B and 7B):

| | What the model learns to write |
|---|---|
| **Base** | nothing (no training) |
| **A: SQL only** | the correct SQL |
| **B: hint + SQL** | the hint (schema, reasoning, steps), then the correct SQL |

* **Method:** LoRA (r 16, alpha 32), learning rate 2e-4, 3 epochs, the loss only on the answer.

**Question:** Should it learn the prompts as well?

## 5. Data dictionary

The cryptic schema's names mean nothing, so we wrote a short English meaning for every table and column (`schema/descriptions.json`, readable version `docs/data_dictionary_cryptic.md`). With `--dictionary`, the model sees each meaning next to the name:

```sql
-- t89v: shipments (consignments) booked by customers, one row per shipment
  c16 REAL, -- declared value of the goods in USD
```

**Result** (Qwen2.5 Coder 7B, one pass, the first 120 cryptic questions):

| | EX % | Easy | Moderate | Hard | VER % |
|---|---:|---:|---:|---:|---:|
| Cryptic + dictionary | 41.7 | 90.0 | 27.5 | 7.5 | 90.0 |

Without the dictionary, cryptic scored 16.5% (on the 480 questions). The question sets are different, so this is not an exact comparison, but the jump is large. The prompt gets longer (about 2.4k → 5.5k tokens), so the context window was raised to 16k.

## 6. Two-pass pipeline

**Pass 1 finds the tables and columns the question needs.** We tested two ways:

| | How Pass 1 works |
|---|---|
| **Option 1** | A model (Qwen2.5 Coder 7B) reads the question, the schema and the dictionary. It answers with the tables, what the answer should show (for example `COUNT(t.c01)`) and the columns to filter on. It does not write SQL. |
| **Option 2** | No model. BM25 search over the dictionary, plus fuzzy matching of the question's words against values stored in the database (for example "Japan" or "FRA"). |

Both add the tables that are needed to join the chosen ones.

**Pass 2 writes the SQL.** A model gets the question and only the tables from Pass 1, with the dictionary. It first writes two short lines (the tables it will use, and what the answer returns), then the SQL.

* Each attempt has an 8 second limit.
* If the SQL does not run, the model gets one more try with the error message.

### Problems we found and fixed

| Problem | Fix |
|---|---|
| Pass 1 wrote a "hint" that often described joins that were not needed. Pass 2 followed it. | Hints removed. Hint creation during Pass 1 might be removed, but using hints during fine tuning doesn't seem bad. |
| Pass 1 said `COUNT(t.c01)`, but our code passed only `t.c01` to Pass 2, so the COUNT was lost. | Pass 1's answer is now passed on as written. |
| Pass 2 joined every table it was given, even wrong ones. | The prompt now says the tables are suggestions. So the model reasons, it doesn't have to use all of them. |
| Sometimes the model wrote no SQL at all. An empty query "runs" in SQLite, so it was counted as valid and never retried. | An answer without SQL now gets the retry. |

### Results

**Setup:** the first 120 questions (10 base questions per level × 4 styles), all three schemas, dictionary in every run.

| Setup | Pass 1 | Pass 2 (writes SQL) |
|---|---|---|
| A | Option 1: 7B coder | 1.5B coder |
| B | Option 1: 7B coder | 7B coder |
| C | Option 2: BM25 + fuzzy | 7B coder |
| D | none (one pass, all 20 tables) | 7B coder |

**Accuracy (EX %)**

| Setup | Cryptic | Mixed | Normal |
|---|---:|---:|---:|
| A: 7B → 1.5B | 22.5 | 27.5 | 26.7 |
| B: 7B → 7B | 38.3 | **42.5** | **45.8** |
| C: BM25 → 7B | 36.7 | 39.2 | 35.8 |
| D: one pass, 7B | **41.7** | 38.3 | 41.7 |

**EX % by difficulty (easy / moderate / hard)**

| Setup | Cryptic | Mixed | Normal |
|---|---|---|---|
| A: 7B → 1.5B | 47.5 / 20.0 / 0.0 | 55.0 / 27.5 / 0.0 | 45.0 / 35.0 / 0.0 |
| B: 7B → 7B | 77.5 / 35.0 / 2.5 | 82.5 / 37.5 / 7.5 | 87.5 / 40.0 / 10.0 |
| C: BM25 → 7B | 80.0 / 25.0 / 5.0 | 75.0 / 32.5 / 10.0 | 77.5 / 30.0 / 0.0 |
| D: one pass, 7B | 90.0 / 27.5 / 7.5 | 82.5 / 22.5 / 10.0 | 80.0 / 27.5 / 17.5 |

**Valid SQL (VER %) and time per question (end-to-end)**

| Setup | Cryptic | Mixed | Normal |
|---|---|---|---|
| A: 7B → 1.5B | 90.0%, 1.6 s | 62.5%, 1.8 s | 72.5%, 1.4 s |
| B: 7B → 7B | 98.3%, 2.9 s | 76.7%, 3.6 s | 83.3%, 2.7 s |
| C: BM25 → 7B | 95.0%, 2.4 s | 85.0%, 2.7 s | 83.3%, 2.1 s |
| D: one pass, 7B | 90.0%, 1.3 s | 60.8%, 1.3 s | 78.3%, 1.2 s |

**Pass 1: how often all needed tables were found**

| Pass 1 | Cryptic | Mixed | Normal | Tables kept (of 20) |
|---|---:|---:|---:|---:|
| Option 1 (7B model) | 76.7% | 80.0% | 81.7% | about 2 |
| Option 2 (BM25) | 75.0% | 76.7% | 78.3% | about 5 |

## 7. What we learned

**The dictionary helps the most.** It made cryptic usable: with it, cryptic is close to normal (38.3% against 45.8% in setup B).

**Option 1 is the better Pass 1.** With the same 7B writer, setup B beats setup C on all three schemas, and it is ahead on moderate questions (where joins are needed) in every schema. The model finds the needed tables as often as BM25, but keeps fewer extra tables, so Pass 2 gets a cleaner schema.

**But BM25 is much faster** It can find relevant columns in seconds and the accuracy of tables found is not that different, it is up to discussion.

**Two passes vs one pass: no clear winner yet.** Two passes (B) beat one pass (D) on mixed (42.5 vs 38.3) and normal (45.8 vs 41.7), but not on cryptic (38.3 vs 41.7). Two passes clearly help on moderate questions (35 to 40% vs 22.5 to 27.5%), because a smaller schema makes joins easier. They lose on hard questions, because Pass 1 sometimes misses a needed table, while one pass always sees all tables. One pass is also about twice as fast (1.2 to 1.3 s vs 2.7 to 3.6 s).

**The 1.5B model is fast but too weak.** It answers in about 0.5 s, but accuracy drops by 15 to 19 points, it writes much invalid SQL on mixed and normal, and it gets 0% on hard questions.

**Pass 1 limits the score.** In about 1 of 5 questions a needed table is missing, and then Pass 2 can never be right. This happens mostly on hard questions.

**Hard questions are still unsolved.** At most 17.5% in any setup (one pass, normal). This is where fine-tuning should help.

## 8. Next steps

1. Improve Pass 1 on hard questions, so fewer needed tables are missed.
2. Run the fine-tuning (A and B) on the school's GPU cluster, and score it on the 192 test questions per schema.


EXPERIMENT (PASS1 BM25 Run) = python evaluation/two_pass.py --variant normal  --linker bm25 --bases-per-difficulty 10 --link-only 