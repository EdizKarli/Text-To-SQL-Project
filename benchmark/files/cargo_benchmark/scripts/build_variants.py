#!/usr/bin/env python3
"""Generate the MIXED and CRYPTIC schema variants from the NORMAL schema.

For each variant this script writes
  schema/schema_<variant>.sql          DDL with renamed tables/columns/indexes (comments stripped: they would leak meaning)
  databases/cargo_<variant>.db         same rows as the normal database, copied table by table
  questions/questions_<variant>.json   same questions, Gold SQL translated with scripts/sql_translate.py
and schema/naming_map.json (normal -> mixed -> cryptic for every table and column).
Every translated Gold query is executed on its variant database and must return exactly the normal Gold result.

Requires: pip install sqlglot     Usage: python scripts/build_variants.py [--skip-questions]
"""
import argparse, json, os, re, sqlite3, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_db import build, db_path                     # noqa: E402
from naming import MIXED, cryptic_map, index_name       # noqa: E402

VARIANTS = ("mixed", "cryptic")
TOKEN = re.compile(r"--[^\n]*|'(?:[^']|'')*'|[A-Za-z_][A-Za-z0-9_]*|\s+|.", re.S)


def normal_structure(con):
    tables = [t for (t,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY rowid")]
    cols = {t: [r[1] for r in con.execute(f"PRAGMA table_info({t})")] for t in tables}
    types = {t: {r[1]: (r[2] or "TEXT") for r in con.execute(f"PRAGMA table_info({t})")} for t in tables}
    return tables, cols, types


def mappings(tables, cols):
    maps = {"cryptic": cryptic_map(tables, cols)}
    mixed = {}
    for t in tables:
        new_t, cm = MIXED[t]
        missing = set(cols[t]) ^ set(cm)
        assert not missing, f"mixed map for {t} does not match schema: {missing}"
        assert len(set(cm.values())) == len(cm), f"duplicate mixed column names in {t}"
        mixed[t] = (new_t, cm)
    assert len({v[0] for v in mixed.values()}) == len(mixed), "duplicate mixed table names"
    maps["mixed"] = mixed
    return maps


def rename_ddl(ddl, mapping, variant):
    """Token-level rename of schema.sql. Column names are resolved in the scope of the table being created;
    REFERENCES t(c) and CREATE INDEX ... ON t(c) use the referenced table's map. Comments are dropped."""
    out, cur_table, expect, ref_table, paren_depth_ref = [], None, None, None, None
    sig = []                          # recent significant tokens (upper-cased)
    idx_count = {}
    depth = 0
    for m in TOKEN.finditer(ddl):
        tok = m.group(0)
        if tok.startswith("--"):
            continue
        if tok.isspace() or tok.startswith("'"):
            out.append(tok)
            continue
        up = tok.upper()
        if re.match(r"[A-Za-z_]", tok):
            prev = sig[-1] if sig else ""
            prev2 = sig[-2] if len(sig) > 1 else ""
            if prev == "TABLE" and prev2 == "CREATE":
                cur_table = tok
                tok = mapping[tok][0]
            elif prev == "INDEX" and prev2 == "CREATE":
                expect = "index_name"
                idx_tok_pos = len(out)
            elif prev == "ON" and expect == "index_name":
                ref_table = tok
                tn = mapping[tok][0]
                idx_count[tn] = idx_count.get(tn, 0) + 1
                out[idx_tok_pos] = index_name(variant, tn, idx_count[tn])
                tok, expect, paren_depth_ref = tn, "ref_cols", depth
            elif prev == "REFERENCES":
                ref_table = tok
                tok = mapping[tok][0]
                expect, paren_depth_ref = "ref_cols", depth
            elif expect == "ref_cols" and ref_table and tok in mapping[ref_table][1]:
                tok = mapping[ref_table][1][tok]
            elif cur_table and tok in mapping[cur_table][1]:
                tok = mapping[cur_table][1][tok]
            sig.append(up)
            out.append(tok)
            continue
        if tok == "(":
            depth += 1
        elif tok == ")":
            depth -= 1
            if expect == "ref_cols" and depth == paren_depth_ref:
                expect, ref_table = None, None
        elif tok == ";":
            cur_table, expect, ref_table = None, None, None
        sig.append(up)
        out.append(tok)
    text = "".join(out)
    text = "\n".join(line.rstrip() for line in text.splitlines())
    text = re.sub(r"(?m)^(CREATE INDEX \S+) +ON ", r"\1 ON ", text)
    blocks = re.split(r"(?m)(?=^CREATE TABLE )", text)
    col_line = re.compile(r"^    ([A-Za-z_][A-Za-z0-9_]*) +(INTEGER|TEXT|REAL)\b(.*)$")
    for k, b in enumerate(blocks):
        lines = b.split("\n")
        width = max([len(col_line.match(l).group(1)) for l in lines if col_line.match(l)] or [0])
        blocks[k] = "\n".join(f"    {m.group(1).ljust(width)} {m.group(2)}{m.group(3)}" if (m := col_line.match(l)) else l
                              for l in lines)
    text = "".join(blocks)
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    return text


def build_variant_db(variant, ddl, mapping, tables, normal_db):
    path = db_path(variant)
    if os.path.exists(path):
        os.remove(path)
    con = sqlite3.connect(path)
    con.executescript(ddl)
    con.execute("ATTACH DATABASE ? AS n", (normal_db,))
    con.execute("PRAGMA foreign_keys = ON")
    for t in tables:
        con.execute(f"INSERT INTO main.{mapping[t][0]} SELECT * FROM n.{t}")
    con.commit()
    con.execute("DETACH DATABASE n")
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    assert not fk, f"{variant}: foreign key violations {fk[:3]}"
    return con


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-questions", action="store_true")
    a = ap.parse_args()
    normal_db = db_path("normal")
    ncon = build(normal_db) if not os.path.exists(normal_db) else sqlite3.connect(normal_db)
    tables, cols, types = normal_structure(ncon)
    maps = mappings(tables, cols)
    ddl_src = open(os.path.join(ROOT, "schema", "schema.sql"), encoding="utf-8").read()

    naming = {"normal": {t: {"name": t, "columns": {c: c for c in cols[t]}} for t in tables}}
    for v in VARIANTS:
        naming[v] = {t: {"name": maps[v][t][0], "columns": dict(maps[v][t][1])} for t in tables}
        header = (f"-- Air Cargo Flights benchmark -- {v.upper()} schema (generated by scripts/build_variants.py "
                  f"from schema/schema.sql; do not edit)\n")
        ddl = header + rename_ddl(ddl_src, maps[v], v)
        with open(os.path.join(ROOT, "schema", f"schema_{v}.sql"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(ddl)
        vcon = build_variant_db(v, ddl, maps[v], tables, normal_db)
        nt = vcon.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        nc = sum(len(vcon.execute(f"PRAGMA table_info({maps[v][t][0]})").fetchall()) for t in tables)
        print(f"[{v}] {nt} tables, {nc} columns -> {db_path(v)}")
        vcon.close()
    with open(os.path.join(ROOT, "schema", "naming_map.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(naming, fh, indent=1, ensure_ascii=False)

    if a.skip_questions:
        return
    from sql_translate import translate
    qpath = os.path.join(ROOT, "questions", "questions_normal.json")
    questions = json.load(open(qpath, encoding="utf-8"))
    failures = 0
    for v in VARIANTS:
        vcon = sqlite3.connect(db_path(v))
        out = []
        for q in questions:
            gold = ncon.execute(q["gold_sql"]).fetchall()
            sql = q.get(f"gold_sql_{v}") or translate(q["gold_sql"], maps[v], types)
            try:
                got = vcon.execute(sql).fetchall()
                ok = got == gold
            except sqlite3.Error as e:
                ok, got = False, str(e)
            if not ok:
                failures += 1
                print(f"[{v}] {q['id']} translation mismatch: {str(got)[:200]}\n{sql}")
            nq = {k: val for k, val in q.items() if not k.startswith("gold_sql_")}
            nq["gold_sql"] = sql
            nq["schema_variant"] = v
            out.append(nq)
        with open(os.path.join(ROOT, "questions", f"questions_{v}.json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(out, fh, indent=2, ensure_ascii=False)
        print(f"[{v}] {len(out)} Gold queries translated and verified against the normal results")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
