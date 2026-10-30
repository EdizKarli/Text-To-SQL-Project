#!/usr/bin/env python3
"""Run all validation layers. Exit code 1 if any error-level check fails.

Layers: (1) SQLite integrity + foreign keys, (2) SQL checks in validation_checks.sql,
        (3) clean-rebuild reproducibility (generator run twice + two fresh builds compared).
Runs on the NORMAL database (the MIXED/CRYPTIC databases hold the same rows; see validation/test_variants.py).
Usage: python validation/run_validation.py [--db databases/cargo_normal.db] [--report validation/validation_report.txt]
"""
import argparse, hashlib, os, re, sqlite3, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from build_db import build

def parse_checks(path):
    text = open(path, encoding="utf-8").read()
    parts = re.split(r"^-- @check ", text, flags=re.M)[1:]
    for p in parts:
        head, _, body = p.partition("\n")
        name, level, desc = [x.strip() for x in head.split("|", 2)]
        sql = "\n".join(l for l in body.splitlines() if not l.startswith("-- =====")).strip()
        yield name, level, desc, sql

def digest(con):
    h = hashlib.sha256()
    for line in con.iterdump():
        h.update(line.encode()); h.update(b"\n")
    return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=os.path.join(ROOT, "databases", "cargo_normal.db"))
    ap.add_argument("--report", default=os.path.join(ROOT, "validation", "validation_report.txt"))
    a = ap.parse_args()
    lines, failures = [], 0
    def log(s=""):
        print(s); lines.append(s)

    con = sqlite3.connect(a.db)
    log("== Layer 1: schema integrity ==")
    ic = con.execute("PRAGMA integrity_check").fetchone()[0]
    fk = con.execute("PRAGMA foreign_key_check").fetchall()
    log(f"integrity_check ........ {ic}")
    log(f"foreign_key_check ...... {len(fk)} violations")
    failures += (ic != "ok") + (len(fk) > 0)

    log("\n== Layer 2: size (row and column counts) ==")
    tables = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
    ncols = 0
    for t in tables:
        n = len(con.execute(f"PRAGMA table_info({t})").fetchall()); ncols += n
        log(f"{t:22s}{con.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]:>8d} rows {n:>4d} columns")
    shape_ok = len(tables) == 20 and ncols == 300
    log(f"[{'PASS' if shape_ok else 'FAIL'}] schema size: {len(tables)} tables, {ncols} columns (target 20 / 300)")
    failures += not shape_ok

    log("\n== Layer 3: business-rule, coverage and distribution checks ==")
    for name, level, desc, sql in parse_checks(os.path.join(ROOT, "validation", "validation_checks.sql")):
        val = con.execute(sql).fetchone()[0]
        if level == "error":
            ok = val == 0
            failures += not ok
            tag = "PASS" if ok else "FAIL"
        else:
            tag = level.upper()
        log(f"[{tag:4s}] {name:46s} {val:>6}   {desc}")
    log(f"({sum(1 for _ in parse_checks(os.path.join(ROOT, 'validation', 'validation_checks.sql')))} checks)")

    log("\n== Layer 4: reproducibility (clean rebuild) ==")
    with tempfile.TemporaryDirectory() as d:
        s1, s2 = os.path.join(d, "a.sql"), os.path.join(d, "b.sql")
        gen = os.path.join(ROOT, "data", "generate_data.py")
        subprocess.run([sys.executable, gen, s1], check=True)
        subprocess.run([sys.executable, gen, s2], check=True)
        same_seed = open(s1, "rb").read() == open(s2, "rb").read()
        same_seed_as_repo = open(s1, "rb").read() == open(os.path.join(ROOT, "data", "seed.sql"), "rb").read()
        c1, c2 = build(os.path.join(d, "1.db")), build(os.path.join(d, "2.db"))
        same_db = digest(c1) == digest(c2)
        c1.close(); c2.close()
    for label, ok in [("generator output identical across runs", same_seed),
                      ("generator output matches committed data/seed.sql", same_seed_as_repo),
                      ("two clean builds produce identical databases", same_db)]:
        log(f"[{'PASS' if ok else 'FAIL'}] {label}")
        failures += not ok

    log(f"\nRESULT: {'ALL HARD CHECKS PASSED' if failures == 0 else str(failures) + ' HARD CHECK(S) FAILED'}")
    with open(a.report, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
