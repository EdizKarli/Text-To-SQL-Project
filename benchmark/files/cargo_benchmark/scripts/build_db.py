#!/usr/bin/env python3
"""Build the NORMAL database from schema/schema.sql + data/seed.sql (regenerating the seed if requested).

Usage: python scripts/build_db.py [--regenerate] [--out databases/cargo_normal.db]
The MIXED and CRYPTIC databases are derived from this one by scripts/build_variants.py.
"""
import argparse, os, sqlite3, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_DIR = os.path.join(ROOT, "databases")
DEFAULT_DB = os.path.join(DB_DIR, "cargo_normal.db")


def db_path(variant="normal"):
    return os.path.join(DB_DIR, f"cargo_{variant}.db")


def build(db_path=DEFAULT_DB, regenerate=False):
    seed = os.path.join(ROOT, "data", "seed.sql")
    if regenerate or not os.path.exists(seed):
        subprocess.run([sys.executable, os.path.join(ROOT, "data", "generate_data.py"), seed], check=True)
    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    if os.path.exists(db_path):
        os.remove(db_path)
    con = sqlite3.connect(db_path)
    for rel in ("schema/schema.sql", "data/seed.sql"):
        with open(os.path.join(ROOT, rel), encoding="utf-8") as fh:
            con.executescript(fh.read())
    con.commit()
    return con


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerate", action="store_true")
    ap.add_argument("--out", default=DEFAULT_DB)
    a = ap.parse_args()
    con = build(a.out, a.regenerate)
    tables = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    ncols = 0
    for t in tables:
        n = len(con.execute(f"PRAGMA table_info({t})").fetchall())
        ncols += n
        print(f"{t:22s}{con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>8d} rows {n:>4d} cols")
    print(f"{len(tables)} tables, {ncols} columns -> {a.out}")
