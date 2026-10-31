#!/usr/bin/env python3
"""Check that the MIXED and CRYPTIC databases are faithful renamings of the NORMAL one.

1. Shape: 20 tables / 300 columns in each variant; same number of foreign keys, CHECK constraints, UNIQUE
   constraints and indexes per table; column types and NOT NULL flags line up.
2. Naming: naming_map.json is complete and one-to-one; no normal table/column name leaks into the cryptic DDL.
3. Data: every table holds exactly the same rows as its normal counterpart (EXCEPT in both directions).
4. Questions: same IDs/styles/specs in every questions_<variant>.json; schema_aware wording uses the variant's names;
   each variant Gold query returns the normal result.
5. Integrity: PRAGMA integrity_check / foreign_key_check on every variant.
Usage: python validation/test_variants.py   (run scripts/build_variants.py first)
"""
import json, os, re, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VARIANTS = ("mixed", "cryptic")
fails = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label} {detail if not ok else ''}")
    if not ok:
        fails.append(label)


def db(v):
    return os.path.join(ROOT, "databases", f"cargo_{v}.db")


def shape(con, table):
    cols = [(r[2].upper(), r[3], r[5]) for r in con.execute(f"PRAGMA table_info({table})")]
    sql = con.execute("SELECT sql FROM sqlite_master WHERE name = ?", (table,)).fetchone()[0]
    fks = len(con.execute(f"PRAGMA foreign_key_list({table})").fetchall())
    idx = len(con.execute(f"PRAGMA index_list({table})").fetchall())
    return cols, fks, idx, len(re.findall(r"\bCHECK\b", sql)), len(re.findall(r"\bUNIQUE\b", sql))


def main():
    naming = json.load(open(os.path.join(ROOT, "schema", "naming_map.json"), encoding="utf-8"))
    normal = sqlite3.connect(db("normal"))
    tables = [t for (t,) in normal.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid")]
    nq = json.load(open(os.path.join(ROOT, "questions", "questions_normal.json"), encoding="utf-8"))
    for v in VARIANTS:
        print(f"== {v} ==")
        con = sqlite3.connect(db(v))
        m = naming[v]
        vt = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
        ncols = sum(len(con.execute(f"PRAGMA table_info({t})").fetchall()) for t in vt)
        check(f"{v}: 20 tables / 300 columns", len(vt) == 20 and ncols == 300, f"{len(vt)} / {ncols}")
        check(f"{v}: naming map covers every table and column one-to-one",
              set(m) == set(tables) and len({x['name'] for x in m.values()}) == len(tables)
              and all(len(set(x["columns"].values())) == len(x["columns"]) for x in m.values()))
        bad_shape = [t for t in tables if shape(normal, t) != shape(con, m[t]["name"])]
        check(f"{v}: column types, NOT NULL, PK, FK, CHECK, UNIQUE and index counts identical per table", not bad_shape, str(bad_shape))
        bad_cols = [t for t in tables if [r[1] for r in con.execute(f"PRAGMA table_info({m[t]['name']})")]
                    != [m[t]["columns"][c] for c in [r[1] for r in normal.execute(f"PRAGMA table_info({t})")]]]
        check(f"{v}: column order follows the naming map", not bad_cols, str(bad_cols))
        if v == "cryptic":
            ddl = open(os.path.join(ROOT, "schema", "schema_cryptic.sql"), encoding="utf-8").read()
            ddl_code = re.sub(r"'(?:[^']|'')*'", "''", "\n".join(l for l in ddl.splitlines() if not l.startswith("--")))
            words = set(re.findall(r"[A-Za-z_][A-Za-z0-9_]*", ddl_code))
            leaks = sorted((set(tables) | {c for t in tables for c in naming["normal"][t]["columns"]}) & words)
            check("cryptic: no normal table or column name appears in the DDL", not leaks, str(leaks))
        con.execute("ATTACH DATABASE ? AS n", (db("normal"),))
        diff = []
        for t in tables:
            vn = m[t]["name"]
            a = con.execute(f"SELECT COUNT(*) FROM (SELECT * FROM n.{t} EXCEPT SELECT * FROM main.{vn})").fetchone()[0]
            b = con.execute(f"SELECT COUNT(*) FROM (SELECT * FROM main.{vn} EXCEPT SELECT * FROM n.{t})").fetchone()[0]
            same_n = (con.execute(f"SELECT COUNT(*) FROM n.{t}").fetchone()[0] == con.execute(f"SELECT COUNT(*) FROM main.{vn}").fetchone()[0])
            if a or b or not same_n:
                diff.append(t)
        check(f"{v}: every table holds exactly the normal rows", not diff, str(diff))
        con.execute("DETACH DATABASE n")
        check(f"{v}: integrity_check ok", con.execute("PRAGMA integrity_check").fetchone()[0] == "ok")
        check(f"{v}: no foreign key violations", not con.execute("PRAGMA foreign_key_check").fetchall())
        vq = json.load(open(os.path.join(ROOT, "questions", f"questions_{v}.json"), encoding="utf-8"))
        meta = lambda q: (q["id"], q["base_id"], q["difficulty"], q["style"], q["answer_spec"], q["question_template"])
        check(f"{v}: same question IDs, styles, templates and answer specs as normal", [meta(q) for q in vq] == [meta(q) for q in nq])
        sys.path.insert(0, os.path.join(ROOT, "questions"))
        from build_questions import render
        wording_ok = all((qv["question"] == render(qv["question_template"], m)) if qv["style"] == "schema_aware"
                         else qv["question"] == qn["question"] for qn, qv in zip(nq, vq))
        check(f"{v}: non-schema-aware wording identical; schema_aware wording uses the {v} names", wording_ok)
        if v == "cryptic":
            sch = [qv["question"] for qv in vq if qv["style"] == "schema_aware"]
            ident = {c for t in tables for c in naming["normal"][t]["columns"] if "_" in c} | {t for t in tables if "_" in t}
            leaks = sorted({w for txt in sch for w in re.findall(r"[a-z_0-9]+", txt) if w in ident})
            check("cryptic: schema_aware questions contain no normal table/column identifiers", not leaks, str(leaks))
        bad_q, seen = [], set()
        for qn, qv in zip(nq, vq):
            if qn["base_id"] in seen:
                continue
            seen.add(qn["base_id"])
            try:
                if normal.execute(qn["gold_sql"]).fetchall() != con.execute(qv["gold_sql"]).fetchall():
                    bad_q.append(qn["base_id"])
            except sqlite3.Error as e:
                bad_q.append(f"{qn['base_id']}: {e}")
        check(f"{v}: all {len(seen)} Gold queries return the normal Gold result", not bad_q, str(bad_q))
    print(f"\nRESULT: {'ALL VARIANT CHECKS PASSED' if not fails else str(len(fails)) + ' FAILED: ' + ', '.join(fails)}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
