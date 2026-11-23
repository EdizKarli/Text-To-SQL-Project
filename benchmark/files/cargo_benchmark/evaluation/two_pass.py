#!/usr/bin/env python3
"""Two-pass text-to-SQL: pass 1 finds the relevant tables and columns, pass 2 writes the SQL from them.

PASS 1 (schema linking), two options:
  --linker llm     a model reads the question, the schema and the data dictionary and answers with the relevant
                   tables, the columns to show (#output) and the columns to filter/join/group on (#filter).
                   No SQL and no hint (hints invented joins and lowered accuracy in tests).    (option 1)
  --linker bm25    no model: BM25 search over the data dictionary (every column is a small document: its meaning,
                   its table's meaning, its allowed and example values) plus fuzzy matching of the question's words
                   against the values stored in the database (e.g. 'Japan', 'FRA', 'Skyline Fuels').  (option 2)
  Both then add the tables that are needed to JOIN the chosen tables (shortest foreign-key path) and their keys.

PASS 2 (SQL writing): another model gets the question, the schema of the chosen tables only, the list of relevant
  columns and the values found. It first writes two short lines (tables it will use, what the answer returns) and
  then the SQL (--no-reasoning: SQL only). The SQL is taken from after "SQL:"; an answer without SQL is retried. Each attempt has a timeout
  (--timeout, default 8 s). If the SQL does not run (error), or the attempt timed out, the model gets another
  chance with the error message (--retries, default 1, same timeout).

Usage (from the cargo_benchmark folder; Ollama running; standard library only):
  ollama pull qwen2.5-coder:7b && ollama pull qwen2.5-coder:1.5b
  Default models: option 1 = 7B coder finds the tables (qwen2.5-coder:7b), 1.5B coder writes the SQL (qwen2.5-coder:1.5b);
                  option 2 = BM25 finds the tables, 7B writes the SQL (qwen2.5-coder:7b). Change with --sql-model.
  python evaluation/two_pass.py --variant cryptic --linker bm25 --bases-per-difficulty 10 --evaluate
  python evaluation/two_pass.py --variant cryptic --linker llm --bases-per-difficulty 10 --evaluate
  python evaluation/two_pass.py --variant cryptic --linker bm25 --link-only     # pass 1 only, scored, no model needed

The run is done in two stages: pass 1 for all questions, then pass 2 for all questions, so only one model is in
memory at a time (two 7B models rarely fit together on a laptop GPU; switching per question would reload a model
every time and break the 8 s limit). Both stages are saved after every question and resume when re-run.

Outputs in evaluation/predictions/ (scored by evaluate.py like any other run):
  pred_<tag>_pass1.json   pass 1 per question: chosen tables and columns, values found, time, and recall
                          against the Gold query (questions/gold_links.json)
  pred_<tag>.json         final SQL per question
  pred_<tag>_raw.json     per question: every pass-2 attempt (raw text, SQL, error, time, tokens), pass-1 time.
                          latency_s = pass 1 + all pass-2 attempts (end-to-end), so the latency numbers of
                          evaluate.py are for the whole pipeline; the pass-2 part is reported separately here.
"""
import argparse
import collections
import difflib
import json
import math
import os
import re
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from run_ollama import ask, compact_schema, dictionary_for, extract_sql, load_split, model_missing  # noqa: E402
from evaluate import run as run_sql  # noqa: E402

STOP = set("""a an the of in on at to for from by with and or is are was were be been being do does did what which who
whom whose how many much is it its this that these those there their our we us you your me my i give show list tell
find get return each per all any every some than then as into over under between about please just only also have
has had can could would should will total number count value values one two three five top first last most more
less""".split())
# a few everyday words and the dictionary words they usually mean (edit freely; used by the bm25 linker only)
SYNONYMS = {"plane": "aircraft", "planes": "aircraft", "jet": "aircraft", "fleet": "aircraft", "tail": "registration",
            "pilot": "crew captain first_officer", "pilots": "crew captain first_officer", "staff": "crew",
            "client": "customer", "clients": "customer", "account": "customer", "accounts": "customer",
            "revenue": "invoice amount", "billed": "invoice amount", "owe": "invoice paid payment",
            "late": "delay", "delayed": "delay", "punctuality": "delay", "route": "origin destination",
            "routes": "origin destination", "station": "airport", "stations": "airport", "hub": "hub airport",
            "cargo": "shipment", "consignment": "shipment", "booking": "shipment booked", "kilos": "kg",
            "weight": "weight kg", "heavy": "weight kg", "cost": "usd", "spend": "cost usd", "price": "usd",
            "dg": "dangerous goods", "hazardous": "dangerous goods", "cold": "temperature",
            "pharma": "pharmaceuticals", "scan": "tracking event", "scans": "tracking event",
            "handed": "delivered DLV", "handover": "delivered DLV", "claim": "insurance claim",
            "repair": "maintenance", "mro": "maintenance", "fuel": "fuel", "saf": "sustainable aviation fuel"}


def norm(word):
    w = re.sub(r"[^a-z0-9_]", "", word.lower())
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        return w[:-1]
    return w


def tokens(text):
    out = []
    for w in re.findall(r"[A-Za-z0-9_]+", text):
        for part in [w] + w.split("_"):
            n = norm(part)
            if n and n not in STOP and not n.isdigit():
                out.append(n)
    return out


class Schema:
    """Tables, columns, keys, dictionary and some stored values of one variant."""

    def __init__(self, variant):
        self.variant = variant
        self.db = os.path.join(ROOT, "databases", f"cargo_{variant}.db")
        self.ddl = os.path.join(ROOT, "schema", "schema.sql" if variant == "normal" else f"schema_{variant}.sql")
        self.dic = dictionary_for(variant)
        con = sqlite3.connect(f"file:{self.db}?mode=ro", uri=True)
        self.tables = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid")]
        self.cols, self.pk, self.fks, self.values = {}, {}, collections.defaultdict(list), {}
        for t in self.tables:
            info = list(con.execute(f"PRAGMA table_info({t})"))
            self.cols[t] = [r[1] for r in info]
            self.pk[t] = [r[1] for r in info if r[5]]
            for r in con.execute(f"PRAGMA foreign_key_list({t})"):
                self.fks[t].append((r[3], r[2], r[4]))                 # (column, referenced table, referenced column)
            for _, c, typ, *_ in info:
                if typ.upper() == "TEXT":
                    n = con.execute(f"SELECT COUNT(DISTINCT {c}) FROM {t}").fetchone()[0]
                    if 0 < n <= 300:
                        self.values[(t, c)] = [v for (v,) in con.execute(
                            f"SELECT DISTINCT {c} FROM {t} WHERE {c} IS NOT NULL") if isinstance(v, str) and len(v) <= 40]
        con.close()
        self.graph = collections.defaultdict(set)
        for t, fl in self.fks.items():
            for c, rt, rc in fl:
                if rt != t:
                    self.graph[t].add(rt)
                    self.graph[rt].add(t)

    def join_path(self, a, b):
        """Shortest chain of tables connecting a and b through foreign keys."""
        prev, todo = {a: None}, collections.deque([a])
        while todo:
            x = todo.popleft()
            if x == b:
                path = []
                while x is not None:
                    path.append(x)
                    x = prev[x]
                return path[::-1]
            for y in sorted(self.graph[x]):
                if y not in prev:
                    prev[y] = x
                    todo.append(y)
        return [a, b]

    def complete(self, tables, columns):
        """Add the tables that connect the chosen ones, and the key columns used to join them."""
        tables = [t for t in self.tables if t in set(tables)]
        if not tables:
            return [], []
        connected = [tables[0]]
        for t in tables[1:]:
            best = min((self.join_path(c, t) for c in connected), key=len)
            for x in best:
                if x not in connected:
                    connected.append(x)
        keep = set(connected)
        cols = list(dict.fromkeys(columns))
        for t in keep:
            cols += [f"{t}.{c}" for c in self.pk[t]]
            cols += [f"{t}.{c}" for c, rt, _ in self.fks[t] if rt in keep]
        cols = [c for c in dict.fromkeys(cols) if c.split(".")[0] in keep]
        return [t for t in self.tables if t in keep], cols


class BM25:
    def __init__(self, docs, k1=1.2, b=0.75):
        self.docs, self.k1, self.b = docs, k1, b
        self.df = collections.Counter(w for d in docs.values() for w in set(d))
        self.avg = sum(len(d) for d in docs.values()) / len(docs)
        self.n = len(docs)

    def score(self, q, key):
        doc = self.docs[key]
        tf, s = collections.Counter(doc), 0.0
        for w in q:
            if w in tf:
                idf = math.log(1 + (self.n - self.df[w] + 0.5) / (self.df[w] + 0.5))
                s += idf * tf[w] * (self.k1 + 1) / (tf[w] + self.k1 * (1 - self.b + self.b * len(doc) / self.avg))
        return s


class BM25Linker:
    """Two BM25 indexes over the data dictionary: one document per table (its meaning) and one per column (its
    meaning, its table's meaning, allowed and example values). A table scores by its own document (weighted
    TABLE_WEIGHT) plus its best column, so 'warehouses' finds the warehouse table rather than every table that has
    a column 'warehouse where ...'."""
    TABLE_WEIGHT = 2.0

    def __init__(self, schema, max_tables=6, cols_per_table=6, keep_ratio=0.3):
        self.s, self.max_tables, self.cols_per_table, self.keep_ratio = schema, max_tables, cols_per_table, keep_ratio
        cdocs, tdocs = {}, {}
        for t in schema.tables:
            tdesc, cdesc = schema.dic[t]
            tdocs[t] = tokens(f"{t} {tdesc}")
            for c in schema.cols[t]:
                vals = " ".join(schema.values.get((t, c), [])[:12])
                cdocs[(t, c)] = tokens(f"{c} {cdesc[c]} {cdesc[c]} {tdesc} {vals}")
        self.cols_index, self.tables_index = BM25(cdocs), BM25(tdocs)
        self.lower_values = {k: [(v, v.lower().replace("_", " ")) for v in vs] for k, vs in schema.values.items()}

    def value_matches(self, question):
        """Words of the question that are (almost) a value stored in the database, e.g. 'Japan' or 'FRA'."""
        words = re.findall(r"[A-Za-z0-9][A-Za-z0-9\-]*", question)
        grams = {" ".join(words[i:i + n]) for n in (1, 2, 3) for i in range(len(words) - n + 1)}
        grams = {g for g in grams if len(g) >= 3 and norm(g) not in STOP}
        lgrams = [(g, g.lower()) for g in grams]
        found = []
        for (t, c), vals in self.lower_values.items():
            for v, lv in vals:
                for g, lg in lgrams:
                    if lg == lv or (v.isupper() and len(v) <= 4 and g == v):
                        hit = True
                    elif len(lv) >= 5 and lv[0] == lg[0] and abs(len(lv) - len(lg)) <= max(2, len(lv) // 5):
                        m = difflib.SequenceMatcher(None, lg, lv)
                        hit = m.quick_ratio() >= 0.88 and m.ratio() >= 0.88
                    else:
                        hit = False
                    if hit:
                        found.append((t, c, v))
                        break
        return found

    def link(self, question):
        q = tokens(question)
        q += [norm(w) for x in q for w in SYNONYMS.get(x, "").split()]
        scores = {k: self.cols_index.score(q, k) for k in self.cols_index.docs}
        matches = self.value_matches(question)
        for t, c, _ in matches:
            scores[(t, c)] += 3.0
        by_table = {t: self.TABLE_WEIGHT * self.tables_index.score(q, t) for t in self.s.tables}
        for t in self.s.tables:
            by_table[t] += max(scores[(t, c)] for c in self.s.cols[t])
        ranked = sorted(by_table, key=lambda t: -by_table[t])
        top = by_table[ranked[0]] or 1.0
        tables = [t for t in ranked[:self.max_tables] if by_table[t] >= self.keep_ratio * top] or ranked[:1]
        tables += [t for t, _, _ in matches if t not in tables][:2]
        cols = []
        for t in tables:
            best = sorted(self.s.cols[t], key=lambda c: -scores[(t, c)])[:self.cols_per_table]
            cols += [f"{t}.{c}" for c in best if scores[(t, c)] > 0]
        cols += [f"{t}.{c}" for t, c, _ in matches]
        return {"tables": tables, "columns": cols, "matches": [list(m) for m in matches], "hint": None}


LINK_INSTRUCTION = ("Find what is needed to answer the question. Do not write SQL.\n"
                    "Answer in exactly these three lines, using only names from the schema above:\n"
                    "#tables <every table the query needs, also tables that are only used to join>\n"
                    "#output <table>.<column>, ... (the columns the answer shows, or counts, sums or averages)\n"
                    "#filter <table>.<column>, ... (the columns used to filter, join, group or sort; 'none' if none)\n")


def parse_columns(schema, text):
    return [f"{t}.{c}" for t, c in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)", text)
            if t in schema.cols and c in schema.cols[t]]


def llm_link(schema, full_schema_text, q, url, model, timeout, num_ctx):
    prompt = ("You are an expert database analyst. Given the following SQLite database schema:\n"
              f"```sql\n{full_schema_text}\n```\n\nQuestion: {q['question']}\n\n" + LINK_INSTRUCTION)
    resp = ask(url, model, prompt, num_ctx, timeout, 300)
    raw = resp.get("response", "")
    tables, cols = [], []
    m = re.search(r"#tables?\s*:?\s*(.*)", raw)
    if m:
        tables = [t for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", m.group(1)) if t in schema.cols]
    m = re.search(r"#output\s*:?\s*(.*)", raw)
    out_text = m.group(1).strip()[:300] if m else ""
    out_cols = parse_columns(schema, out_text)
    m = re.search(r"#filter\s*:?\s*(.*)", raw)
    filter_text = m.group(1).strip()[:300] if m else ""
    filter_cols = parse_columns(schema, filter_text)
    if filter_text.lower().strip(" .'\"") in ("none", "") or not filter_cols:
        filter_text = ""
    for c in out_cols + filter_cols:
        if c.split(".")[0] not in tables:
            tables.append(c.split(".")[0])
    cols = list(dict.fromkeys(out_cols + filter_cols))
    return {"tables": tables, "columns": cols, "output_columns": out_cols, "filter_columns": filter_cols,
            "output_text": out_text if out_cols else "", "filter_text": filter_text,
            "matches": [], "hint": None, "raw": raw, "eval_count": resp.get("eval_count")}


def gold_recall(schema, link, gold_normal):
    """Share of the Gold query's tables / columns that pass 1 kept (names mapped to this variant)."""
    names = json.load(open(os.path.join(ROOT, "schema", "naming_map.json"), encoding="utf-8"))[schema.variant]
    gt = {names[t]["name"] for t in gold_normal}
    gc = {f"{names[t]['name']}.{names[t]['columns'][c]}" for t, cs in gold_normal.items() for c in cs}
    kept_t, listed_c = set(link["tables"]), set(link["columns"])
    return {"tables_found": len(gt & kept_t) / len(gt), "all_tables_found": gt <= kept_t,
            "columns_listed": len(gc & listed_c) / len(gc) if gc else 1.0,
            "columns_in_schema": len({c for c in gc if c.split(".")[0] in kept_t}) / len(gc) if gc else 1.0,
            "tables_kept": len(kept_t)}


REASON_FORMAT = ("Answer in exactly this format, three lines. The SQL line is required:\n"
                 "Tables: <the tables you will use; leave out tables you do not need>\n"
                 "Output: <what the answer returns, with COUNT/SUM/AVG if needed, nothing more>\n"
                 "SQL: <one valid SQLite query on a single line>")


def sql_prompt(schema_text, link, q, previous=None, reasoning=True):
    lines = ["You are an expert SQL assistant. Given the following SQLite database schema "
             "(tables that may be needed; you do not have to use all of them):", f"```sql\n{schema_text}\n```", ""]
    if link.get("output_text") or link.get("filter_text"):          # pass 1 lines as written, e.g. COUNT(t.c01)
        if link.get("output_text"):
            lines.append("Suggested output: " + link["output_text"])
        if link.get("filter_text"):
            lines.append("Suggested filters, joins, grouping or sorting: " + link["filter_text"])
    elif link.get("output_columns") or link.get("filter_columns"):
        if link.get("output_columns"):
            lines.append("Suggested output columns: " + ", ".join(link["output_columns"]))
        if link.get("filter_columns"):
            lines.append("Suggested columns to filter, join, group or sort on: " + ", ".join(link["filter_columns"]))
    elif link["columns"]:
        lines.append("Columns that may be relevant: " + ", ".join(link["columns"]))
    if link["matches"]:
        lines.append("Values found in the database: " + "; ".join(f"'{v}' in {t}.{c}" for t, c, v in link["matches"][:8]))
    lines += [f"Question: {q['question']}", "",
              "Write one SQLite query that answers the question using only the tables and columns above. "
              "Return only the columns the question asks for."]
    if previous:
        lines += [f"Your previous query was: {previous[0]}", f"It failed: {previous[1]}", "Write a corrected query."]
    if reasoning:
        return "\n".join(lines + [REASON_FORMAT])
    return "\n".join(lines + ["Output ONLY the SQL statement on a single line, without markdown fences, "
                               "comments or explanations."]) + "\nSQL:"


def answer_sql(raw):
    """The SQL in a model answer: after the last 'SQL:' line, else from the first SELECT/WITH; cut at ';' or a
    blank line, so reasoning or explanations around the query are dropped."""
    text = raw.replace("```sql", "\n").replace("```", "\n")
    marks = list(re.finditer(r"(?im)^\s*\**\s*SQL\s*\**\s*:\s*\**\s*", text))
    if marks:
        text = text[marks[-1].end():]
    else:
        m = re.search(r"(?is)\b(WITH|SELECT)\b", text)
        if not m:
            return ""
        text = text[m.start():]
    text = re.split(r"\n\s*\n", text.strip())[0]
    text = text.split(";")[0]
    return extract_sql(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["normal", "mixed", "cryptic"], required=True)
    ap.add_argument("--linker", choices=["llm", "bm25"], required=True, help="pass 1: option 1 (llm) or option 2 (bm25)")
    ap.add_argument("--link-model", default="qwen2.5-coder:7b", help="pass 1 model for --linker llm")
    ap.add_argument("--sql-model", default=None,
                    help="pass 2 model (default qwen2.5-coder:1.5b with --linker llm, qwen2.5-coder:7b with --linker bm25)")
    ap.add_argument("--timeout", type=float, default=8, help="seconds per pass-2 attempt (default 8)")
    ap.add_argument("--retries", type=int, default=1, help="extra pass-2 attempts after an invalid SQL or a timeout")
    ap.add_argument("--link-timeout", type=float, default=60, help="seconds for a pass-1 model call")
    ap.add_argument("--no-dictionary", action="store_true", help="pass 2 schema without the data dictionary comments")
    ap.add_argument("--no-reasoning", action="store_true",
                    help="pass 2 answers with the SQL only (default: 3 short lines - tables, output, plan - then SQL)")
    ap.add_argument("--max-tables", type=int, default=6, help="bm25: at most this many tables before join completion")
    ap.add_argument("--keep-ratio", type=float, default=0.3,
                    help="bm25: keep a table if its score is at least this share of the best table's score")
    ap.add_argument("--bases-per-difficulty", type=int, choices=range(1, 81), metavar="1-80")
    ap.add_argument("--split", choices=["train", "dev", "test"])
    ap.add_argument("--ids", help="comma-separated question ids")
    ap.add_argument("--stage", choices=["both", "1", "2"], default="both")
    ap.add_argument("--link-only", action="store_true", help="run and score pass 1 only")
    # 127.0.0.1, not localhost: on Windows "localhost" first tries IPv6, which fails after ~2 s on every call
    ap.add_argument("--url", default="http://127.0.0.1:11434/api/generate")
    ap.add_argument("--num-ctx", type=int, default=16384)
    ap.add_argument("--restart", action="store_true")
    ap.add_argument("--evaluate", action="store_true")
    ap.add_argument("--print-prompt", action="store_true", help="show the pass-2 prompt of the first question and exit")
    a = ap.parse_args()
    if a.sql_model is None:
        a.sql_model = "qwen2.5-coder:1.5b" if a.linker == "llm" else "qwen2.5-coder:7b"

    schema = Schema(a.variant)
    questions = json.load(open(os.path.join(ROOT, "questions", f"questions_{a.variant}.json"), encoding="utf-8"))
    if a.bases_per_difficulty:
        questions = [q for q in questions if int(q["base_id"][1:]) <= a.bases_per_difficulty]
    if a.split:
        keep = load_split(a.split)
        questions = [q for q in questions if q["id"] in keep]
    if a.ids:
        keep = set(a.ids.split(","))
        questions = [q for q in questions if q["id"] in keep]
    gold_links = json.load(open(os.path.join(ROOT, "questions", "gold_links.json"), encoding="utf-8"))

    clean = lambda m: re.sub(r"[^A-Za-z0-9.]+", "-", m)  # noqa: E731
    # "-v3": pass 1 output/filter lines are passed on as written (no hint); keeps these runs apart from older ones
    linker_tag = "bm25" if a.linker == "bm25" else f"llm-{clean(a.link_model)}-v3"
    tag = (f"{a.variant}_2pass-{linker_tag}_{clean(a.sql_model)}" + ("" if a.no_dictionary else "_dict") + ("" if a.no_reasoning else "_reason")
           + (f"_{a.split}" if a.split else "") + (f"_b{a.bases_per_difficulty}" if a.bases_per_difficulty else ""))
    out = os.path.join(ROOT, "evaluation", "predictions", f"pred_{tag}.json")
    raw_path, pass1_path = out[:-5] + "_raw.json", out[:-5] + "_pass1.json"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    load = lambda p: json.load(open(p, encoding="utf-8")) if os.path.exists(p) and not a.restart else {}  # noqa: E731

    # ---------------- pass 1: schema linking
    links = load(pass1_path)
    todo = [q for q in questions if q["id"] not in links]
    if a.stage in ("both", "1") and todo:
        print(f"Pass 1 ({linker_tag}): {len(todo)} questions")
        bm25 = BM25Linker(schema, a.max_tables, keep_ratio=a.keep_ratio) if a.linker == "bm25" else None
        full_text = compact_schema(schema.db, schema.ddl, schema.dic) if a.linker == "llm" else None
        if a.linker == "llm":
            try:
                ask(a.url, a.link_model, "SELECT 1;", a.num_ctx, 300, 1)        # warm-up: load the model
            except Exception as e:
                if model_missing(e):
                    sys.exit(f"Ollama does not have the model {a.link_model}. Install it first:  ollama pull {a.link_model}")
                print(f"Warm-up failed ({e}); continuing")
        for k, q in enumerate(todo, 1):
            t0 = time.time()
            try:
                link = bm25.link(q["question"]) if bm25 else llm_link(schema, full_text, q, a.url, a.link_model,
                                                                       a.link_timeout, a.num_ctx)
                link["error"] = None
            except Exception as e:                                   # failed model call: pass 2 gets all tables
                link = {"tables": [], "columns": [], "matches": [], "hint": None, "error": str(e)}
            link["seconds"] = round(time.time() - t0, 3)
            link["tables"], link["columns"] = schema.complete(link["tables"], link["columns"])
            if not link["tables"]:                                   # nothing usable found: fall back to everything
                link["tables"], link["fallback_all_tables"] = list(schema.tables), True
            link["recall"] = gold_recall(schema, link, gold_links[q["base_id"]])
            links[q["id"]] = link
            json.dump(links, open(pass1_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            r = link["recall"]
            print(f"[{k}/{len(todo)}] {q['id']} {link['seconds']:.1f}s tables {r['tables_kept']:2d} "
                  f"gold tables found {r['tables_found']:.0%}  {','.join(link['tables'])[:70]}")
    summarize_pass1(links, questions)
    if a.link_only or a.stage == "1":
        print(f"Pass 1 -> {pass1_path}")
        return

    # ---------------- pass 2: SQL writing, with a timeout per attempt and a retry on invalid SQL
    missing = [q["id"] for q in questions if q["id"] not in links]
    if missing:
        sys.exit(f"pass 1 is missing for {len(missing)} questions; run --stage 1 first")
    use_dic = None if a.no_dictionary else schema.dic
    if a.print_prompt:
        q = questions[0]
        p = sql_prompt(compact_schema(schema.db, schema.ddl, use_dic, links[q["id"]]["tables"]), links[q["id"]], q,
                       None, not a.no_reasoning)
        print(p + f"\n\n[{len(p)} characters, roughly {len(p) / 3.5:.0f} tokens]")
        return
    preds, raw = load(out), load(raw_path)
    raw["_run"] = dict(variant=a.variant, model=a.sql_model, schema="compact-pruned", evidence=False,
                       dictionary=not a.no_dictionary, with_spec=False, num_ctx=a.num_ctx, pipeline="two_pass",
                       linker=linker_tag, timeout_s=a.timeout, retries=a.retries)
    # questions without an answer, plus those whose model calls all failed last time (e.g. model not installed)
    todo = [q for q in questions if q["id"] not in preds
            or (not preds[q["id"]] and all(x.get("model_error") for x in (raw.get(q["id"]) or {}).get("attempts", [{}])))]
    if todo:
        t0 = time.time()
        try:
            ask(a.url, a.sql_model, "SELECT 1;", a.num_ctx, 300, 1)      # warm-up: load the model, not timed
            print(f"Pass 2 ({a.sql_model}): model ready in {time.time() - t0:.1f}s; {len(todo)} questions, "
                  f"{a.timeout:g}s per attempt, {a.retries} retry")
        except Exception as e:
            if model_missing(e):
                sys.exit(f"Ollama does not have the model {a.sql_model}. Install it first:  ollama pull {a.sql_model}")
            print(f"Warm-up failed ({e}); continuing")
    for k, q in enumerate(todo, 1):
        link = links[q["id"]]
        text = compact_schema(schema.db, schema.ddl, use_dic, link["tables"])
        attempts, previous, sql = [], None, ""
        for n in range(1 + a.retries):
            prompt = sql_prompt(text, link, q, previous, not a.no_reasoning)
            t1 = time.time()
            try:
                resp = ask(a.url, a.sql_model, prompt, a.num_ctx, a.timeout, 300 if a.no_reasoning else 450)
                answer, err = resp.get("response", ""), None
            except Exception as e:
                resp, answer, err = {}, "", ("timeout" if "timed out" in str(e).lower() else str(e))
            wall = time.time() - t1
            if err is None and wall > a.timeout:
                err = "timeout"
            sql = (extract_sql(answer) if a.no_reasoning else answer_sql(answer)) if err is None else ""
            if err:
                status, detail = "error", err
            elif not sql.strip():                      # empty SQL "runs" in SQLite, so check it first
                status, detail = "error", "no SQL query in the answer"
            else:
                status, detail = run_sql(schema.db, sql, 10)[:2]
            attempts.append({"raw": answer, "sql": sql, "model_error": err, "exec": status,
                             "exec_error": detail if status != "ok" else None, "latency_s": round(wall, 3),
                             "eval_count": resp.get("eval_count"),
                             "eval_duration_s": (resp.get("eval_duration") or 0) / 1e9 or None,
                             "prompt_eval_count": resp.get("prompt_eval_count")})
            if status == "ok":
                break
            if err == "timeout":
                previous = ("(no answer within the time limit)", "timed out")
            elif not sql.strip():
                previous = ("(none)", "your answer had no SQL query; write it on the line that starts with 'SQL:'")
            else:
                previous = (sql, detail)
        final = attempts[-1]
        if final["exec"] != "ok":                     # keep the last SQL that was produced, if any
            sql = next((x["sql"] for x in reversed(attempts) if x["sql"]), "")
        preds[q["id"]] = sql
        p2 = sum(x["latency_s"] for x in attempts)
        toks = [x["eval_count"] for x in attempts if x["eval_count"]]
        durs = [x["eval_duration_s"] for x in attempts if x["eval_duration_s"]]
        raw[q["id"]] = {"raw": final["raw"], "error": final["model_error"] if not sql else None,
                        "latency_s": round(link["seconds"] + p2, 3), "pass1_s": link["seconds"],
                        "pass2_s": round(p2, 3), "attempts": attempts, "retried": len(attempts) > 1,
                        "eval_count": sum(toks) if toks else None, "eval_duration_s": sum(durs) if durs else None,
                        "prompt_eval_count": attempts[0]["prompt_eval_count"]}
        json.dump(preds, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        json.dump(raw, open(raw_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"[{k}/{len(todo)}] {q['id']} pass2 {p2:.1f}s attempts {len(attempts)} {final['exec']:7s} {sql[:80]}")
    summarize_pass2(raw, questions)
    print(f"\nPass 1 -> {pass1_path}\nPredictions -> {out}\nModel stats -> {raw_path}")
    if a.evaluate:
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "evaluate.py"), out, "--variant", a.variant,
                        "--out", out[:-5] + "_results.json", "--only-predicted"], check=False)


def summarize_pass1(links, questions):
    rs = [links[q["id"]]["recall"] for q in questions if q["id"] in links]
    if not rs:
        return
    by = collections.defaultdict(list)
    for q in questions:
        if q["id"] in links:
            by[q["difficulty"]].append(links[q["id"]]["recall"])
    print("\nPass 1 (schema linking) against the Gold query:")
    print("                    n  all gold tables kept  gold columns listed  gold columns in schema  tables kept")
    for name, group in [("all", rs)] + [(d, by[d]) for d in ("easy", "moderate", "hard") if by[d]]:
        mean = lambda k: sum(r[k] for r in group) / len(group)  # noqa: E731
        print(f"  {name:12s} {len(group):5d}  {100 * mean('all_tables_found'):19.1f}%  {100 * mean('columns_listed'):18.1f}%"
              f"  {100 * mean('columns_in_schema'):21.1f}%  {mean('tables_kept'):11.1f}")
    secs = [links[q["id"]]["seconds"] for q in questions if q["id"] in links]
    print(f"  pass 1 time per question: mean {sum(secs) / len(secs):.2f}s, max {max(secs):.2f}s")


def summarize_pass2(raw, questions):
    rows = [raw[q["id"]] for q in questions if q["id"] in raw]
    if not rows:
        return
    first_ok = sum(r["attempts"][0]["exec"] == "ok" for r in rows)
    final_ok = sum(r["attempts"][-1]["exec"] == "ok" for r in rows)
    timeouts = sum(x["model_error"] == "timeout" for r in rows for x in r["attempts"])
    att = sorted(x["latency_s"] for r in rows for x in r["attempts"] if not x["model_error"])
    print(f"\nPass 2: valid SQL on the first attempt {100 * first_ok / len(rows):.1f}%, after retries "
          f"{100 * final_ok / len(rows):.1f}%; retried {sum(r['retried'] for r in rows)} of {len(rows)} questions; "
          f"{timeouts} attempts timed out")
    if att:
        print(f"  time per attempt: mean {sum(att) / len(att):.2f}s, median {att[len(att) // 2]:.2f}s, "
              f"max {att[-1]:.2f}s;  end-to-end per question: mean "
              f"{sum(r['latency_s'] for r in rows) / len(rows):.2f}s")


if __name__ == "__main__":
    main()
