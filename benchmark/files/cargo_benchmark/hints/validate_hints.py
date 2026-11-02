"""
validate_hints.py: checks every hint in hints/hints_<variant>.jsonl.

For each hint it checks that:
  1. the skeleton is complete (#question, #schema, #think with 3 lines, #trace with 6 lines, #sql) and
     every step is a single line
  2. #question is the exact question text of that variant and phrasing
  3. #sql is exactly the Gold SQL of that variant
  4. running #sql on databases/cargo_<variant>.db gives the same result as the Gold SQL
  5. every table and column named in #schema exists in that variant (no invented names)
  6. no placeholder is left, and in mixed/cryptic no normal name is used where the variant name differs
     (the normal name may only appear once, in brackets, as the meaning)
It also checks that there are 480 hints per variant and 1440 in total.

Usage (from the cargo_benchmark folder):
  python hints/validate_hints.py
"""
import json
import os
import re
import sqlite3
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
VARIANTS = ("normal", "mixed", "cryptic")
EXPECTED_PER_VARIANT = 480
STEP_LABELS = ("Source", "Joins", "Filters", "Grouping/aggregation", "Ordering/limits", "Traps")


def run(con, sql):
    rows = con.execute(sql).fetchall()
    return [tuple(round(v, 6) if isinstance(v, float) else v for v in r) for r in rows]


def check_structure(text):
    lines = text.split("\n")
    errs = []
    if not lines[0].startswith("#question "):
        errs.append("first line is not #question")
    if len(lines) < 2 or not lines[1].startswith("#schema "):
        errs.append("second line is not #schema")
    try:
        t, r, s = lines.index("#think"), lines.index("#trace"), next(i for i, l in enumerate(lines) if l.startswith("#sql "))
    except (ValueError, StopIteration):
        return ["missing #think, #trace or #sql"]
    think, trace = lines[t + 1:r], lines[r + 1:s]
    if [l.split(":")[0] for l in think] != ["- Goal", "- Output columns", "- Interpretation"]:
        errs.append("#think must have Goal, Output columns, Interpretation")
    if len(trace) != 6 or any(not l.startswith(f"{i + 1}. {lab}: ") for i, (l, lab) in enumerate(zip(trace, STEP_LABELS))):
        errs.append("#trace must have the 6 numbered steps, one line each")
    if s != len(lines) - 1:
        errs.append("#sql must be the last line")
    return errs


def schema_names(line):
    """'#schema a(x, y); b(z)' or '#schema a (meaning): x (m), y' -> {table: [columns]}"""
    body = line[len("#schema "):]
    out = {}
    for part in body.split("; "):
        m = re.fullmatch(r"([a-z0-9_]+)\((.*)\)", part)
        if m:
            out[m.group(1)] = [c for c in m.group(2).split(", ") if c]
            continue
        head, _, cols = part.partition(": ")
        table = head.split(" (")[0]
        out[table] = [c.split(" (")[0] for c in cols.split(", ") if c]
    return out


def leaked_normal_names(text, variant, names):
    """normal names (table or column) used in the hint text where the variant uses another name"""
    if variant == "normal":
        return []
    body = text.split("\n#sql ")[0]
    body = body.split("\n", 1)[1]                      # drop #question (it is the benchmark's own text)
    body = re.sub(r" \([a-z0-9_]+\)", "", body)          # the meaning shown once in brackets is allowed
    body = re.sub(r"'[^']*'", "''", body)               # values in quotes are data, not names
    variant_words = set()
    normal_only = set()
    for t, v in names[variant].items():
        variant_words.add(v["name"])
        variant_words.update(v["columns"].values())
    for t, v in names["normal"].items():
        if names[variant][t]["name"] != t:
            normal_only.add(t)
        for c in v["columns"]:
            if names[variant][t]["columns"][c] != c:
                normal_only.add(c)
    normal_only -= variant_words
    words = set(re.findall(r"\b[a-z][a-z0-9_]*\b", body))
    # single plain words (flights, shipments, method) are read as English; identifiers have an underscore
    return sorted(w for w in words & normal_only if "_" in w)


def main():
    names = json.load(open(os.path.join(ROOT, "schema", "naming_map.json"), encoding="utf-8"))
    total, problems = 0, []
    for variant in VARIANTS:
        questions = {q["id"]: q for q in json.load(open(os.path.join(ROOT, "questions", f"questions_{variant}.json"),
                                                        encoding="utf-8"))}
        with open(os.path.join(HERE, f"hints_{variant}.jsonl"), encoding="utf-8") as f:
            hints = [json.loads(l) for l in f if l.strip()]
        con = sqlite3.connect(os.path.join(ROOT, "databases", f"cargo_{variant}.db"))
        tables = {v["name"]: set(v["columns"].values()) for v in names[variant].values()}
        gold_cache = {}
        bad_here = 0
        if len(hints) != EXPECTED_PER_VARIANT:
            problems.append(f"{variant}: {len(hints)} hints, expected {EXPECTED_PER_VARIANT}")
        missing = set(questions) - {h["id"] for h in hints}
        if missing:
            problems.append(f"{variant}: no hint for {len(missing)} questions, e.g. {sorted(missing)[:5]}")
        for h in hints:
            q, text, errs = questions.get(h["id"]), h["hint"], []
            if q is None:
                problems.append(f"{variant} {h['id']}: not a question id")
                continue
            errs += check_structure(text)
            lines = text.split("\n")
            if lines[0] != f"#question {q['question']}":
                errs.append("#question differs from the question text")
            sql = lines[-1][len("#sql "):]
            if sql != q["gold_sql"]:
                errs.append("#sql is not exactly the Gold SQL")
            for t, cs in schema_names(lines[1]).items():
                if t not in tables:
                    errs.append(f"#schema names unknown table {t}")
                    continue
                errs += [f"#schema names unknown column {t}.{c}" for c in cs if c not in tables[t]]
            if "[[" in text or "{{" in text:
                errs.append("placeholder left in text")
            leaks = leaked_normal_names(text, variant, names)
            if leaks:
                errs.append(f"normal names used instead of {variant} names: {', '.join(leaks)}")
            try:
                if q["gold_sql"] not in gold_cache:
                    gold_cache[q["gold_sql"]] = run(con, q["gold_sql"])
                if run(con, sql) != gold_cache[q["gold_sql"]]:
                    errs.append("#sql result differs from the Gold result")
            except sqlite3.Error as e:
                errs.append(f"#sql fails: {e}")
            if errs:
                bad_here += 1
                problems += [f"{variant} {h['id']}: {e}" for e in errs]
        total += len(hints)
        print(f"{variant}: {len(hints)} hints checked, {bad_here} with problems")
    if total != EXPECTED_PER_VARIANT * len(VARIANTS):
        problems.append(f"total {total} hints, expected {EXPECTED_PER_VARIANT * len(VARIANTS)}")
    if problems:
        print(f"\n{len(problems)} problems:")
        for p in problems[:200]:
            print("  " + p)
        sys.exit(1)
    print(f"\nall {total} hints pass")


if __name__ == "__main__":
    main()
