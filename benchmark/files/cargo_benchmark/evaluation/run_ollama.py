#!/usr/bin/env python3
"""Ask a local model (served by Ollama) to answer the benchmark questions for one schema variant.

    ollama pull qwen2.5-coder:1.5b
    python evaluation/run_ollama.py --variant normal  --model qwen2.5-coder:1.5b
    python evaluation/run_ollama.py --variant mixed   --model qwen2.5-coder:1.5b
    python evaluation/run_ollama.py --variant cryptic --model qwen2.5-coder:1.5b --evidence   # + naming map hints
    python evaluation/evaluate.py evaluation/predictions/<file>.json --variant cryptic

Writes evaluation/predictions/pred_<variant>_<model>_<schema>[_evidence].json in the {"Q01": "SELECT ..."} format
that evaluation/evaluate.py scores. Use --evaluate to score immediately.

Prompt context (the only things the model sees): the variant's schema, optional evidence, the question and its
answer specification. The answer spec names the expected output columns, ordering and rounding, so execution
match is fair; drop it with --no-spec to test the bare question.

Schema formats (--schema):
  compact (default)  CREATE TABLE with column names, types, PK, FK and the allowed values of coded columns,
                     about 3-4k tokens: fits an 8k context window, which matters for 1.5B models
  full               the variant's schema file as written (CHECKs, comments in normal); about 5-9k tokens
"""
import argparse, json, os, re, sqlite3, subprocess, sys, time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def compact_schema(db_path, ddl_path):
    con = sqlite3.connect(db_path)
    ddl = open(ddl_path, encoding="utf-8").read()
    tables = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY rowid")]
    parts = []
    for t in tables:
        body = re.search(rf"CREATE TABLE {t} \((.*?)\n\);", ddl, re.S).group(1)
        allowed = {c: v for c, v in re.findall(r"\b(\w+) IN\s*\(([^()]*)\)", body)}     # coded values from CHECK ... IN (...)
        fks = {r[3]: f"{r[2]}({r[4]})" for r in con.execute(f"PRAGMA foreign_key_list({t})")}
        cols = []
        for _, name, typ, notnull, _, pk in con.execute(f"PRAGMA table_info({t})"):
            line = f"  {name} {typ}"
            if pk:
                line += " PRIMARY KEY"
            if name in fks:
                line += f" REFERENCES {fks[name]}"
            cols.append((line, f" -- values: {' '.join(allowed[name].split())}" if name in allowed else ""))
        body_lines = [decl + ("," if i < len(cols) - 1 else "") + note for i, (decl, note) in enumerate(cols)]
        parts.append(f"CREATE TABLE {t} (\n" + "\n".join(body_lines) + "\n);")
    return "\n".join(parts)


def evidence_text(variant):
    """Optional hints for mixed/cryptic: what every table and column means (from schema/naming_map.json)."""
    if variant == "normal":
        return ""
    m = json.load(open(os.path.join(ROOT, "schema", "naming_map.json"), encoding="utf-8"))[variant]
    lines = []
    for normal_t, x in m.items():
        cols = ", ".join(f"{new}={old}" for old, new in x["columns"].items())
        lines.append(f"{x['name']} = {normal_t}: {cols}")
    return "Meaning of the table and column names:\n" + "\n".join(lines)


def sanitize_sql(raw):
    s = raw.replace("```sql", "").replace("```", "")
    s = " ".join(s.split())
    s = re.sub(r"^(?i:sql\s*:\s*)", "", s.strip())
    if len(s) > 1 and s[0] == s[-1] and s[0] in "`\"'":
        s = s[1:-1].strip()
    return re.sub(r";+$", "", s).strip()


def ask(url, model, prompt, num_ctx, timeout):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False,
                          "options": {"temperature": 0.0, "num_ctx": num_ctx}}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())["response"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["normal", "mixed", "cryptic"], required=True)
    ap.add_argument("--model", default="qwen2.5-coder:1.5b")
    ap.add_argument("--schema", choices=["compact", "full"], default="compact")
    ap.add_argument("--evidence", action="store_true", help="add the naming map as hints (mixed/cryptic)")
    ap.add_argument("--no-spec", action="store_true", help="do not show the answer specification")
    ap.add_argument("--ids", help="comma-separated question IDs to run (default: all)")
    ap.add_argument("--url", default="http://localhost:11434/api/generate")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=180)
    ap.add_argument("--out")
    ap.add_argument("--evaluate", action="store_true", help="run evaluation/evaluate.py on the result")
    ap.add_argument("--print-prompt", action="store_true", help="show the first prompt and exit (no model call)")
    a = ap.parse_args()

    db = os.path.join(ROOT, "databases", f"cargo_{a.variant}.db")
    ddl_path = os.path.join(ROOT, "schema", "schema.sql" if a.variant == "normal" else f"schema_{a.variant}.sql")
    schema = compact_schema(db, ddl_path) if a.schema == "compact" else open(ddl_path, encoding="utf-8").read()
    evidence = evidence_text(a.variant) if a.evidence else ""
    questions = json.load(open(os.path.join(ROOT, "questions", f"questions_{a.variant}.json"), encoding="utf-8"))
    if a.ids:
        keep = set(a.ids.split(","))
        questions = [q for q in questions if q["id"] in keep]

    tag = f"{a.variant}_{re.sub(r'[^A-Za-z0-9.]+', '-', a.model)}_{a.schema}{'_evidence' if a.evidence else ''}{'_nospec' if a.no_spec else ''}"
    out = a.out or os.path.join(ROOT, "evaluation", "predictions", f"pred_{tag}.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    preds, raw_log = {}, {}
    for k, q in enumerate(questions, 1):
        prompt = (
            "You are an expert SQL assistant. Given the following SQLite database schema:\n"
            f"```sql\n{schema}\n```\n\n"
            + (f"{evidence}\n\n" if evidence else "")
            + f"Question: {q['question']}\n"
            + ("" if a.no_spec else f"Answer format: {q['answer_spec']}\n")
            + "\nWrite one valid SQLite query that answers the question using only the tables and columns above. "
              "Output ONLY the SQL statement on a single line, without markdown fences, comments or explanations.\nSQL:"
        )
        if a.print_prompt:
            print(prompt)
            print(f"\n[{len(prompt)} characters, roughly {len(prompt) // 3.5:.0f} tokens]")
            return
        t0 = time.time()
        try:
            raw = ask(a.url, a.model, prompt, a.num_ctx, a.timeout)
        except Exception as e:
            print(f"[{k}/{len(questions)}] {q['id']} request failed: {e}")
            raw = ""
        preds[q["id"]] = sanitize_sql(raw)
        raw_log[q["id"]] = {"raw": raw, "seconds": round(time.time() - t0, 2)}
        print(f"[{k}/{len(questions)}] {q['id']} ({time.time() - t0:.1f}s) {preds[q['id']][:100]}")

    json.dump(preds, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    json.dump(raw_log, open(out.replace(".json", "_raw.json"), "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"\nPredictions -> {out}")
    if a.evaluate:
        subprocess.run([sys.executable, os.path.join(ROOT, "evaluation", "evaluate.py"), out, "--variant", a.variant,
                        "--out", out.replace(".json", "_results.json")], check=False)


if __name__ == "__main__":
    main()
