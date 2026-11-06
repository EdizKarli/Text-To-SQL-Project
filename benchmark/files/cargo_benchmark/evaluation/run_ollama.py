#!/usr/bin/env python3
"""Ask a local model (served by Ollama) to answer the benchmark questions for one schema variant.

    ollama pull qwen2.5-coder:1.5b
    python evaluation/run_ollama.py --variant normal  --model qwen2.5-coder:1.5b --evaluate
    python evaluation/run_ollama.py --variant mixed   --model qwen2.5-coder:1.5b --evaluate
    python evaluation/run_ollama.py --variant cryptic --model qwen2.5-coder:1.5b --evaluate
    python evaluation/run_ollama.py --variant cryptic --model qwen2.5-coder:1.5b --evidence --evaluate   # + naming hints
    python evaluation/run_ollama.py --variant normal --difficulty easy --style vague         # a slice only
    python evaluation/run_ollama.py --variant normal --print-prompt                          # show a prompt, no model call
    python evaluation/run_ollama.py --variant normal --split test --model cargo-a-7b --evaluate   # fine-tuned, test split
    python evaluation/run_ollama.py --variant normal --split test --model cargo-b-7b --reasoning hint --evaluate

Writes evaluation/predictions/pred_<tag>.json ({"E01-CAS": "SELECT ...", ...}) and pred_<tag>_raw.json with, per
question, the raw model text and Ollama's own counters (eval_count = tokens generated, eval_duration, prompt tokens,
total/load durations) plus the wall-clock latency. evaluate.py reads both files. The run is saved after every
question; re-running the same command resumes where it stopped (use --restart to start over). An untimed warm-up
call loads the model first, so the first question's latency does not include model loading (--no-warmup to skip).

Prompt context: the variant's schema (+ optional evidence) and the question. The answer specification is NOT shown
by default, because it is shared by all four phrasing styles and would hide their differences (show it with
--with-spec). Scoring therefore uses order- and column-order-insensitive result matching (see evaluate.py).

--split train|dev|test runs only that part of splits/split_80_20.json (the fine-tuning split; test = 192 questions
per variant). --reasoning hint asks the model to write the reasoning in the hint format (#schema, #think, #trace)
and then the SQL after a final "#sql" line; this is the prompt that condition B models are trained on
(finetune/build_dataset.py uses build_prompt from this file, so training and test prompts are identical). The
SQL is taken from after the last "#sql"; the full text stays in pred_<tag>_raw.json.

Schema formats (--schema):
  compact (default)  CREATE TABLE with column names, types, PK, FK and the allowed values of coded columns,
                     about 3.0k (normal), 3.2k (cryptic) and 3.3k (mixed) prompt tokens for Qwen2.5-Coder:
                     fits an 8k context window
  full               the variant's schema file as written (too close to 8k for normal: use --num-ctx 16384)
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


def ask(url, model, prompt, num_ctx, timeout, num_predict=None):
    options = {"temperature": 0.0, "num_ctx": num_ctx}
    if num_predict:
        options["num_predict"] = num_predict
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False, "options": options}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


HINT_INSTRUCTION = ("First reason step by step in this format, one line per item: #schema (tables and columns you need), "
                    "#think (Goal, Output columns, Interpretation), #trace (1. Source, 2. Joins, 3. Filters, "
                    "4. Grouping/aggregation, 5. Ordering/limits, 6. Traps). "
                    "Then write #sql followed by one valid SQLite query on a single line, without markdown fences.\n")


def build_prompt(schema, evidence, q, with_spec, reasoning="none"):
    """reasoning='none': answer with the SQL only. reasoning='hint': reasoning in the hint format, then #sql <query>."""
    head = ("You are an expert SQL assistant. Given the following SQLite database schema:\n"
            f"```sql\n{schema}\n```\n\n"
            + (f"{evidence}\n\n" if evidence else "")
            + f"Question: {q['question']}\n"
            + (f"Answer format: {q['answer_spec']}\n" if with_spec else "")
            + "\nWrite one valid SQLite query that answers the question using only the tables and columns above. "
              "Return only the columns the question asks for. ")
    if reasoning == "hint":
        return head + HINT_INSTRUCTION
    return head + "Output ONLY the SQL statement on a single line, without markdown fences, comments or explanations.\nSQL:"


def extract_sql(raw, reasoning="none"):
    """The SQL part of a model answer: everything after the last '#sql' in hint mode, the whole text otherwise."""
    if reasoning == "hint":
        i = raw.rfind("#sql")
        raw = raw[i + 4:] if i >= 0 else ""          # no #sql line -> no answer (scored as missing)
    return sanitize_sql(raw)


def load_split(part):
    """Question ids of one part (train/dev/test) of splits/split_80_20.json."""
    s = json.load(open(os.path.join(ROOT, "splits", "split_80_20.json"), encoding="utf-8"))
    return set(s["questions"][part])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", choices=["normal", "mixed", "cryptic"], required=True)
    ap.add_argument("--model", default="qwen2.5-coder:1.5b")
    ap.add_argument("--schema", choices=["compact", "full"], default="compact")
    ap.add_argument("--evidence", action="store_true", help="add the naming map as hints (mixed/cryptic)")
    ap.add_argument("--with-spec", action="store_true", help="also show the answer specification")
    ap.add_argument("--difficulty", choices=["easy", "moderate", "hard"], help="run one difficulty only")
    ap.add_argument("--style", choices=["casual", "schema_aware", "business_executive", "vague"], help="run one style only")
    ap.add_argument("--ids", help="comma-separated question IDs (e.g. E01-CAS,H07-VAG)")
    ap.add_argument("--split", choices=["train", "dev", "test"], help="run one part of splits/split_80_20.json")
    ap.add_argument("--reasoning", choices=["none", "hint"], default="none",
                    help="hint: reasoning in the hint format before the SQL (fine-tuning condition B)")
    ap.add_argument("--num-predict", type=int, default=None,
                    help="max tokens to generate (default: Ollama's own; 1024 is used for --reasoning hint)")
    ap.add_argument("--url", default="http://localhost:11434/api/generate")
    ap.add_argument("--num-ctx", type=int, default=8192)
    ap.add_argument("--timeout", type=int, default=300)
    ap.add_argument("--out")
    ap.add_argument("--restart", action="store_true", help="ignore an existing partial run and start over")
    ap.add_argument("--evaluate", action="store_true", help="run evaluation/evaluate.py on the result")
    ap.add_argument("--print-prompt", action="store_true", help="show the first prompt and exit (no model call)")
    ap.add_argument("--no-warmup", action="store_true", help="skip the untimed warm-up call that loads the model")
    a = ap.parse_args()

    db = os.path.join(ROOT, "databases", f"cargo_{a.variant}.db")
    ddl_path = os.path.join(ROOT, "schema", "schema.sql" if a.variant == "normal" else f"schema_{a.variant}.sql")
    schema = compact_schema(db, ddl_path) if a.schema == "compact" else open(ddl_path, encoding="utf-8").read()
    evidence = evidence_text(a.variant) if a.evidence else ""
    questions = json.load(open(os.path.join(ROOT, "questions", f"questions_{a.variant}.json"), encoding="utf-8"))
    if a.difficulty:
        questions = [q for q in questions if q["difficulty"] == a.difficulty]
    if a.style:
        questions = [q for q in questions if q["style"] == a.style]
    if a.ids:
        keep = set(a.ids.split(","))
        questions = [q for q in questions if q["id"] in keep]
    if a.split:
        keep = load_split(a.split)
        questions = [q for q in questions if q["id"] in keep]
    if a.reasoning == "hint" and not a.num_predict:
        a.num_predict = 1024

    tag = (f"{a.variant}_{re.sub(r'[^A-Za-z0-9.]+', '-', a.model)}_{a.schema}" + ("_evidence" if a.evidence else "")
           + ("_spec" if a.with_spec else "") + ("_hint" if a.reasoning == "hint" else "")
           + (f"_{a.split}" if a.split else "") + (f"_{a.difficulty}" if a.difficulty else "") + (f"_{a.style}" if a.style else ""))
    out = a.out or os.path.join(ROOT, "evaluation", "predictions", f"pred_{tag}.json")
    raw_path = out[:-5] + "_raw.json"
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)

    if a.print_prompt:
        p = build_prompt(schema, evidence, questions[0], a.with_spec, a.reasoning)
        print(p)
        print(f"\n[{len(p)} characters, roughly {len(p) / 3.5:.0f} tokens]")
        return

    preds, raw_log = {}, {"_run": dict(variant=a.variant, model=a.model, schema=a.schema, evidence=a.evidence,
                                         with_spec=a.with_spec, num_ctx=a.num_ctx,
                                         reasoning=a.reasoning, split=a.split)}
    if not a.restart and os.path.exists(out) and os.path.exists(raw_path):
        preds = json.load(open(out, encoding="utf-8"))
        raw_log = json.load(open(raw_path, encoding="utf-8"))
        print(f"Resuming: {len(preds)} questions already answered (use --restart to start over)")

    todo = [q for q in questions if q["id"] not in preds]
    if todo and not a.no_warmup:
        # Load the model before timing starts, with the same num_ctx (a different num_ctx would make Ollama reload it).
        t0 = time.time()
        try:
            w = ask(a.url, a.model, "SELECT 1;", a.num_ctx, a.timeout)
            print(f"Warm-up: model ready in {time.time() - t0:.1f}s (load {(w.get('load_duration') or 0) / 1e9:.1f}s); "
                  "not included in the results")
        except Exception as e:
            print(f"Warm-up call failed ({e}); continuing")
    for k, q in enumerate(todo, 1):
        prompt = build_prompt(schema, evidence, q, a.with_spec, a.reasoning)
        t0 = time.time()
        try:
            resp = ask(a.url, a.model, prompt, a.num_ctx, a.timeout, a.num_predict)
            raw, err = resp.get("response", ""), None
        except Exception as e:
            resp, raw, err = {}, "", str(e)
        wall = time.time() - t0
        preds[q["id"]] = extract_sql(raw, a.reasoning)
        raw_log[q["id"]] = {
            "raw": raw, "error": err, "latency_s": round(wall, 3),
            "eval_count": resp.get("eval_count"),                         # tokens generated
            "eval_duration_s": (resp.get("eval_duration") or 0) / 1e9 or None,
            "prompt_eval_count": resp.get("prompt_eval_count"),           # prompt tokens processed
            "prompt_eval_duration_s": (resp.get("prompt_eval_duration") or 0) / 1e9 or None,
            "load_duration_s": (resp.get("load_duration") or 0) / 1e9 or None,
            "total_duration_s": (resp.get("total_duration") or 0) / 1e9 or None,
        }
        json.dump(preds, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        json.dump(raw_log, open(raw_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        tok = raw_log[q["id"]]["eval_count"]
        print(f"[{k}/{len(todo)}] {q['id']} {wall:.1f}s {tok or '-'} tok  {err or preds[q['id']][:90]}")

    print(f"\nPredictions -> {out}\nModel stats -> {raw_path}")
    if a.evaluate:
        cmd = [sys.executable, os.path.join(ROOT, "evaluation", "evaluate.py"), out, "--variant", a.variant,
               "--out", out[:-5] + "_results.json"]
        if a.difficulty or a.style or a.ids or a.split:
            cmd.append("--only-predicted")
        subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
