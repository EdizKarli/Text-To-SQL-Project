#!/usr/bin/env python3
"""Put several evaluation results side by side (e.g. one model on normal / mixed / cryptic, or 1.5B vs 7B).

Usage: python evaluation/compare_runs.py evaluation/predictions/*_results.json [--csv comparison.csv] [--md comparison.md]
Reads the *_results.json files written by evaluate.py --out (run_ollama.py --evaluate writes them automatically).
"""
import argparse, csv, glob, json, os

METRICS = [("EX_pct", "EX %"), ("EX_strict_pct", "EX strict %"), ("VER_pct", "VER %"), ("latency_mean_s", "latency s"),
           ("latency_p95_s", "p95 s"), ("tokens_mean", "tokens"), ("ms_per_token", "ms/token"), ("tokens_per_s", "tokens/s")]
STYLES = ("casual", "schema_aware", "business_executive", "vague")
DIFFS = ("easy", "moderate", "hard")


def label(res, path):
    r = res.get("run") or {}
    extra = "+evidence" if r.get("evidence") else ""
    extra += "+spec" if r.get("with_spec") else ""
    return f"{r.get('model', os.path.basename(path))} | {res['variant']}{(' ' + extra) if extra else ''}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("results", nargs="+")
    ap.add_argument("--csv"); ap.add_argument("--md")
    a = ap.parse_args()
    files = sorted({f for p in a.results for f in glob.glob(p)})
    rows = []
    for f in files:
        res = json.load(open(f, encoding="utf-8"))
        s = res["summary"]
        row = {"run": label(res, f), "questions": s["overall"]["questions"]}
        row.update({h: s["overall"].get(k) for k, h in METRICS})
        row.update({f"EX {d}": s["by_difficulty"].get(d, {}).get("EX_pct") for d in DIFFS})
        row.update({f"EX {st}": s["by_style"].get(st, {}).get("EX_pct") for st in STYLES})
        rows.append(row)
    if not rows:
        raise SystemExit("no results files found")
    cols = list(rows[0])
    widths = {c: max(len(c), *(len(str(r[c])) for r in rows)) for c in cols}
    print("  ".join(c.ljust(widths[c]) for c in cols))
    for r in rows:
        print("  ".join(str("-" if r[c] is None else r[c]).ljust(widths[c]) for c in cols))
    if a.csv:
        with open(a.csv, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
        print(f"\nCSV -> {a.csv}")
    if a.md:
        with open(a.md, "w", encoding="utf-8") as fh:
            fh.write("| " + " | ".join(cols) + " |\n|" + "---|" * len(cols) + "\n")
            for r in rows:
                fh.write("| " + " | ".join("-" if r[c] is None else str(r[c]) for c in cols) + " |\n")
        print(f"Markdown -> {a.md}")


if __name__ == "__main__":
    main()
