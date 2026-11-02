"""
build_hints.py: turns the hand-written reasoning steps in hint_bank_*.py into one hint per question
for every schema variant (normal, mixed, cryptic) and writes hints/hints_<variant>.jsonl.

Each hint follows the fixed skeleton:
  #question  the question text of that variant and phrasing
  #schema    tables and columns used, with the variant's own names (meaning shown once for mixed/cryptic)
  #think     Goal, Output columns, Interpretation (vague questions: the reading from the answer_spec)
  #trace     6 steps, shared by the four phrasings of a base question
  #sql       the Gold SQL of that variant, unchanged

Name placeholders in the hint bank (always written with NORMAL names):
  [[table]]          table name
  [[table.column]]   column name only
  {{table.column}}   table.column

Usage (from the cargo_benchmark folder):
  python hints/build_hints.py          build all three variants
  python hints/validate_hints.py       check every hint (see that file)
"""
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from hint_bank_easy import HINTS as EASY  # noqa: E402
from hint_bank_moderate import HINTS as MODERATE  # noqa: E402
from hint_bank_hard import HINTS as HARD  # noqa: E402

VARIANTS = ("normal", "mixed", "cryptic")
STEP_LABELS = ("Source", "Joins", "Filters", "Grouping/aggregation", "Ordering/limits", "Traps")
PLACEHOLDER = re.compile(r"\[\[([a-z_]+)(?:\.([a-z0-9_]+))?\]\]|\{\{([a-z_]+)\.([a-z0-9_]+)\}\}")
SQL_WORDS = set("""select from where and or not in is null as on join left right inner outer cross group by order
having limit offset distinct count sum avg min max round case when then else end with over partition row_number
dense_rank rank ntile lag lead asc desc between like union all except intersect exists cast real integer text
coalesce ifnull nullif substr julianday date strftime abs total printf instr length upper lower trim replace
iif filter rows range unbounded preceding following current row first_value last_value recursive values
""".split())


def bank():
    hints = {}
    for part in (EASY, MODERATE, HARD):
        for h in part:
            if h["id"] in hints:
                raise SystemExit(f"duplicate hint id {h['id']}")
            hints[h["id"]] = h
    return hints


def load_names():
    with open(os.path.join(ROOT, "schema", "naming_map.json"), encoding="utf-8") as f:
        return json.load(f)


def load_questions(variant):
    with open(os.path.join(ROOT, "questions", f"questions_{variant}.json"), encoding="utf-8") as f:
        return json.load(f)


def table_columns(names):
    """normal table -> set of normal column names"""
    return {t: set(v["columns"]) for t, v in names["normal"].items()}


def render(text, variant, names):
    def sub(m):
        if m.group(3):
            t, c, qualified = m.group(3), m.group(4), True
        else:
            t, c, qualified = m.group(1), m.group(2), False
        tv = names[variant][t]["name"]
        if c is None:
            return tv
        cv = names[variant][t]["columns"][c]
        return f"{tv}.{cv}" if qualified else cv
    return PLACEHOLDER.sub(sub, text)


def placeholders(text):
    out = []
    for m in PLACEHOLDER.finditer(text):
        if m.group(3):
            out.append((m.group(3), m.group(4)))
        else:
            out.append((m.group(1), m.group(2)))
    return out


def sql_columns(sql, cols):
    """Tables and columns that the (normal) Gold SQL uses: table -> ordered list of columns."""
    clean = re.sub(r"'[^']*'", "''", sql)
    alias, order = {}, []
    for m in re.finditer(r"\b(?:from|join)\s+([a-z_]+)(?:\s+(?:as\s+)?([a-z_][a-z0-9_]*))?", clean, re.I):
        t, a = m.group(1).lower(), (m.group(2) or "").lower()
        if t in cols:
            if t not in order:
                order.append(t)
            alias[t] = t
            if a and a not in SQL_WORDS:
                alias[a] = t
    used = {t: [] for t in order}

    def add(t, c):
        if c not in used[t]:
            used[t].append(c)

    for m in re.finditer(r"\b([a-z_][a-z0-9_]*)\.([a-z_][a-z0-9_]*)\b", clean, re.I):
        a, c = m.group(1).lower(), m.group(2).lower()
        if a in alias and c in cols[alias[a]]:
            add(alias[a], c)
    outputs = {m.group(1).lower() for m in re.finditer(r"\bas\s+([a-z_][a-z0-9_]*)", clean, re.I)}
    for m in re.finditer(r"(?<![.\w])([a-z_][a-z0-9_]*)\b(?!\s*\.)", clean, re.I):
        w = m.group(1).lower()
        if w in SQL_WORDS or w in alias:
            continue
        owners = [t for t in order if w in cols[t]]
        if len(owners) == 1:
            add(owners[0], w)
        elif len(owners) > 1 and w not in outputs:
            # Unqualified and ambiguous: keep it on every table that has it (all are real columns).
            for t in owners:
                add(t, w)
    return used


def schema_line(used, extra, variant, names):
    tables = list(used)
    for t, c in extra:
        if t not in used:
            used[t] = []
            tables.append(t)
        if c and c not in used[t]:
            used[t].append(c)
    parts = []
    for t in tables:
        tv = names[variant][t]["name"]
        cv = [names[variant][t]["columns"][c] for c in used[t]]
        if variant == "normal":
            parts.append(f"{tv}({', '.join(cv)})")
        else:
            label = ", ".join(f"{v} ({c})" if v != c else v for v, c in zip(cv, used[t]))
            head = f"{tv} ({t})" if tv != t else tv
            parts.append(f"{head}: {label}" if label else head)
    return "; ".join(parts)


def interpretation(h, style, variant, names):
    if style == "schema_aware":
        text = h.get("interp_sch", "none needed, the question names the tables and columns directly.")
    elif style == "vague":
        text = "from the answer spec, " + h.get("interp_vag", h["interp"])
    else:
        text = h.get(f"interp_{style[:3]}", h["interp"])
    return render(text, variant, names)


def build_variant(variant, hints, names, cols):
    out, missing = [], set()
    for q in load_questions(variant):
        h = hints.get(q["base_id"])
        if h is None:
            missing.add(q["base_id"])
            continue
        normal_sql = h["_normal_sql"]
        # #schema = what the Gold SQL uses, plus names the reasoning relies on. The Traps step is left out,
        # because it often names columns that must NOT be used.
        extra = []
        for field, value in h.items():
            if field in ("goal", "out") or field.startswith("interp"):
                extra += placeholders(value)
        for line in h["trace"][:5]:
            extra += placeholders(line)
        used = sql_columns(normal_sql, cols)
        think = [
            f"- Goal: {render(h['goal'], variant, names)}",
            f"- Output columns: {render(h['out'], variant, names)}",
            f"- Interpretation: {interpretation(h, q['style'], variant, names)}",
        ]
        trace = [f"{i + 1}. {label}: {render(step, variant, names)}"
                 for i, (label, step) in enumerate(zip(STEP_LABELS, h["trace"]))]
        text = "\n".join([
            f"#question {q['question']}",
            f"#schema {schema_line(used, extra, variant, names)}",
            "#think", *think,
            "#trace", *trace,
            f"#sql {q['gold_sql']}",
        ])
        out.append({"id": q["id"], "base_id": q["base_id"], "variant": variant, "style": q["style"],
                    "difficulty": q["difficulty"], "hint": text})
    if missing:
        raise SystemExit(f"no hint for {len(missing)} base questions: {', '.join(sorted(missing))}")
    return out


def main():
    hints, names = bank(), load_names()
    cols = table_columns(names)
    for q in load_questions("normal"):
        if q["base_id"] in hints:
            hints[q["base_id"]]["_normal_sql"] = q["gold_sql"]
    for variant in VARIANTS:
        rows = build_variant(variant, hints, names, cols)
        path = os.path.join(HERE, f"hints_{variant}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{variant}: {len(rows)} hints -> {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
