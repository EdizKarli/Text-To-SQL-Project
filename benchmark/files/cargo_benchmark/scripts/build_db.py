#!/usr/bin/env python3
"""Build cargo_flights.db from schema/schema.sql + data/seed.sql (regenerating the seed if requested).

Usage: python scripts/build_db.py [--regenerate] [--out cargo_flights.db]
"""
import argparse, os, sqlite3, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def build(db_path, regenerate=False):
    seed = os.path.join(ROOT, "data", "seed.sql")
    if regenerate or not os.path.exists(seed):
        subprocess.run([sys.executable, os.path.join(ROOT, "data", "generate_data.py"), seed], check=True)
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
    ap.add_argument("--out", default=os.path.join(ROOT, "cargo_flights.db"))
    a = ap.parse_args()
    con = build(a.out, a.regenerate)
    for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        print(f"{t:18s}{con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>8d}")
