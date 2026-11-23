#!/usr/bin/env python3
"""Write questions/gold_links.json: the tables and columns that each Gold SQL query uses (normal names).

    python scripts/make_gold_links.py          # needs sqlglot (like build_variants.py)

{"E01": {"airports": ["is_cargo_hub"]}, "M05": {"flights": [...], "airports": [...]}, ...}

Every column is resolved to its real table with sqlglot (qualify + scopes), so aliases and CTEs are handled.
evaluation/two_pass.py uses this file to score pass 1 (schema linking): did it find the tables and columns that
the Gold query needs? Map to the mixed/cryptic names with schema/naming_map.json.
"""
import json
import os
import sqlite3
import sys

import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sql_translate import _source  # noqa: E402


def links(sql, schema):
    tree = qualify(sqlglot.parse_one(sql, read="sqlite"), schema=schema, dialect="sqlite", quote_identifiers=False,
                   identify=False, validate_qualify_columns=True, expand_alias_refs=False)
    used = {}
    for t in tree.find_all(exp.Table):
        if t.name in schema:
            used.setdefault(t.name, set())
    for scope in traverse_scope(tree):
        for col in scope.columns:
            src = _source(scope, col.table) if col.table else None
            if isinstance(src, exp.Table) and src.name in schema:
                used.setdefault(src.name, set()).add(col.name)
    return {t: sorted(c) for t, c in sorted(used.items())}


def main():
    con = sqlite3.connect(os.path.join(ROOT, "databases", "cargo_normal.db"))
    schema = {t: {r[1]: r[2] for r in con.execute(f"PRAGMA table_info({t})")}
              for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    questions = json.load(open(os.path.join(ROOT, "questions", "questions_normal.json"), encoding="utf-8"))
    gold = {}
    for q in questions:
        if q["base_id"] not in gold:
            gold[q["base_id"]] = links(q["gold_sql"], schema)
    path = os.path.join(ROOT, "questions", "gold_links.json")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(gold, f, indent=1)
    n_t = sum(len(v) for v in gold.values()) / len(gold)
    n_c = sum(len(c) for v in gold.values() for c in v.values()) / len(gold)
    print(f"{len(gold)} base questions: {n_t:.1f} tables and {n_c:.1f} columns per Gold query on average -> "
          f"{os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    main()
