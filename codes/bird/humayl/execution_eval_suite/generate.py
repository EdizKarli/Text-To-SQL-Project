import argparse
import csv
import json
import os
import time
from typing import Dict, Any, List, Optional
import requests

from .schema_builders import FullSchemaBuilder, SafeSchemaPruner, sanitize_sql, find_dev_tables_path


def find_dataset_path(custom_path: Optional[str] = None) -> str:
    candidates = [
        custom_path,
        os.path.join("mini_dev_data", "MINIDEV", "mini_dev_sqlite.json"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "mini_dev_sqlite.json"),
        os.path.join("data_used_here", "mini_dev_sqlite.json"),
        os.path.join("data", "mini_dev_sqlite.json")
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(
        "Could not find 'mini_dev_sqlite.json'. Please specify via --data_file or ensure "
        "'mini_dev_data/MINIDEV/mini_dev_sqlite.json' exists."
    )


def normalize_model_slug(model_name: str) -> str:
    """Replaces : and / with hyphen for safe filenames (e.g. qwen2.5-coder:7b -> qwen2.5-coder-7b)."""
    return model_name.replace(":", "-").replace("/", "-")


def run_generation(
    model: str = "qwen2.5-coder:7b",
    setup: str = "schema",
    num: Optional[int] = None,
    data_file: Optional[str] = None,
    dev_tables_file: Optional[str] = None,
    output_dir: str = os.path.join("execution_eval_suite", "results"),
    save_freq: int = 5,
    temperature: float = 0.0,
    num_ctx: int = 8192,
    timeout: int = 180,
    ollama_url: str = "http://localhost:11434/api/generate",
    resume: bool = True
) -> Dict[str, Any]:
    if setup not in ["schema", "pruned_v2"]:
        raise ValueError(f"Invalid setup '{setup}'. Must be 'schema' or 'pruned_v2'. ('no_schema' is excluded).")

    os.makedirs(output_dir, exist_ok=True)
    model_slug = normalize_model_slug(model)
    predict_file = os.path.join(output_dir, f"predict_{setup}_{model_slug}.json")
    details_file = os.path.join(output_dir, f"details_{setup}_{model_slug}.json")
    timings_csv_file = os.path.join(output_dir, f"timings_{setup}_{model_slug}.csv")
    checkpoint_file = os.path.join(output_dir, f"checkpoint_{setup}_{model_slug}.json")

    # 1. Initialize schema builder / pruner
    tables_path = find_dev_tables_path(dev_tables_file)
    print(f"[{setup.upper()}] Loading schema definitions from {tables_path}...")
    if setup == "schema":
        schema_handler = FullSchemaBuilder(tables_path)
    else:
        schema_handler = SafeSchemaPruner(tables_path)

    # 2. Load dataset
    dataset_path = find_dataset_path(data_file)
    print(f"Loading dataset from {dataset_path}...")
    with open(dataset_path, "r", encoding="utf-8") as f:
        content = f.read().strip()
        data: List[Dict[str, Any]] = (
            json.loads(content)
            if content.startswith("[")
            else [json.loads(line) for line in content.splitlines() if line.strip()]
        )

    if num is not None and num > 0:
        data = data[:num]

    total = len(data)
    print(f"Target model: '{model}' | Setup: '{setup}' | Questions to process: {total}")

    # Check for resume
    predictions: Dict[str, str] = {}
    details: List[Dict[str, Any]] = []
    processed_qids = set()

    if resume and os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, "r", encoding="utf-8") as f:
                ckpt = json.load(f)
                predictions = ckpt.get("predictions", {})
                details = ckpt.get("details", [])
                processed_qids = {str(d["question_id"]) for d in details}
                print(f"Resuming from checkpoint: {len(processed_qids)} questions already processed.")
        except Exception as e:
            print(f"Warning: Could not load checkpoint ({e}). Starting fresh.")

    start_total_time = time.time()

    for idx, item in enumerate(data, 1):
        qid = str(item.get("question_id", idx))
        if qid in processed_qids:
            continue

        db_id = item["db_id"]
        question = item["question"]
        evidence = item.get("evidence", "")
        difficulty = item.get("difficulty", "unknown")

        # Build schema text for prompt
        if setup == "schema":
            db_schema = schema_handler.get_schema(db_id)
            prompt = (
                f"You are an expert SQL assistant. Given the following SQLite database schema:\n"
                f"```sql\n{db_schema}\n```\n\n"
                f"Database name: {db_id}\n"
                f"Evidence: {evidence}\n"
                f"Question: {question}\n\n"
                f"Write a valid SQLite query to answer the question using only the tables and columns defined above. "
                f"Output ONLY the SQL statement on a single line. Do not include markdown fences, comments, or explanations.\n"
                f"SQL:"
            )
        else:
            pruned_schema = schema_handler.extract_relevant_schema(db_id, question, evidence)
            prompt = (
                f"You are an expert SQL assistant. Given the SQLite database schema:\n"
                f"```sql\n{pruned_schema}\n```\n\n"
                f"Database name: {db_id}\n"
                f"Evidence: {evidence}\n"
                f"Question: {question}\n\n"
                f"Write a valid SQLite query to answer the question using only the tables and columns defined above. "
                f"Output ONLY the SQL statement on a single line without explanations or markdown.\n"
                f"SQL:"
            )

        # Call Ollama with latency measurement
        t_gen_start = time.perf_counter()
        req_failed = False
        raw_response = ""
        prompt_tokens = 0
        eval_tokens = 0
        tokens_per_sec = 0.0

        try:
            resp = requests.post(
                ollama_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_ctx": num_ctx,
                    },
                },
                timeout=timeout,
            )
            resp.raise_for_status()
            resp_data = resp.json()
            raw_response = resp_data.get("response", "").strip()
            prompt_tokens = resp_data.get("prompt_eval_count", 0)
            eval_tokens = resp_data.get("eval_count", 0)
            eval_duration_ns = resp_data.get("eval_duration", 0)
            if eval_duration_ns > 0:
                tokens_per_sec = eval_tokens / (eval_duration_ns / 1e9)
        except Exception as e:
            req_failed = True
            print(f"[{idx}/{total}] Ollama error on QID {qid} ({db_id}): {e}")
            raw_response = "SELECT 1;"

        gen_time_ms = (time.perf_counter() - t_gen_start) * 1000.0
        clean_sql = sanitize_sql(raw_response)

        # BIRD official mapping: <SQL>\t----- bird -----\t<db_id>
        predictions[qid] = f"{clean_sql}\t----- bird -----\t{db_id}"

        detail_record = {
            "question_id": int(qid) if qid.isdigit() else qid,
            "db_id": db_id,
            "difficulty": difficulty,
            "question": question,
            "evidence": evidence,
            "gold_sql": item.get("SQL", item.get("query", "")),
            "predicted_sql": clean_sql,
            "raw_response": raw_response,
            "generation_time_ms": round(gen_time_ms, 2),
            "prompt_tokens": prompt_tokens,
            "eval_tokens": eval_tokens,
            "tokens_per_sec": round(tokens_per_sec, 2),
            "request_failed": req_failed
        }
        details.append(detail_record)
        processed_qids.add(qid)

        print(
            f"[{len(details):03d}/{total:03d}] Q#{qid:4s} ({difficulty:<11}) | "
            f"DB: {db_id:<22} | Latency: {gen_time_ms / 1000.0:5.2f}s | "
            f"Status: {'FAILED' if req_failed else 'OK'}",
            flush=True
        )

        # Periodic checkpoint
        if len(details) % save_freq == 0 or len(details) == total:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                json.dump({"predictions": predictions, "details": details}, f, indent=2)

    total_time = time.time() - start_total_time

    # Final saves
    with open(predict_file, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    with open(details_file, "w", encoding="utf-8") as f:
        json.dump(details, f, indent=2)

    with open(timings_csv_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["question_id", "db_id", "difficulty", "generation_time_ms", "eval_tokens", "tokens_per_sec", "request_failed"])
        for d in details:
            writer.writerow([
                d["question_id"], d["db_id"], d["difficulty"],
                d["generation_time_ms"], d["eval_tokens"], d["tokens_per_sec"], d["request_failed"]
            ])

    # Clean up checkpoint on complete success
    if os.path.exists(checkpoint_file):
        os.remove(checkpoint_file)

    print(f"\n[DONE] Finished {len(details)} questions in {total_time / 60:.2f} minutes.")
    print(f"Official predictions saved to: {predict_file}")
    print(f"Detailed metadata saved to:    {details_file}")
    print(f"Timings CSV saved to:          {timings_csv_file}")

    return {
        "predict_file": predict_file,
        "details_file": details_file,
        "timings_csv_file": timings_csv_file,
        "total_evaluated": len(details),
        "total_time_sec": total_time
    }


def main():
    parser = argparse.ArgumentParser(description="Generate SQL predictions for BIRD Mini-Dev (schema or pruned_v2).")
    parser.add_argument("--model", type=str, default="qwen2.5-coder:7b", help="Model name in Ollama")
    parser.add_argument("--setup", type=str, choices=["schema", "pruned_v2"], default="schema", help="Prompt setup")
    parser.add_argument("--num", type=int, default=None, help="Number of questions to evaluate (default all)")
    parser.add_argument("--data_file", type=str, default=None, help="Path to mini_dev_sqlite.json")
    parser.add_argument("--dev_tables", type=str, default=None, help="Path to dev_tables.json")
    parser.add_argument("--output_dir", type=str, default=os.path.join("execution_eval_suite", "results"))
    parser.add_argument("--save_freq", type=int, default=5, help="Checkpoint frequency")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--no_resume", action="store_true", help="Do not resume from checkpoint")
    args = parser.parse_args()

    run_generation(
        model=args.model,
        setup=args.setup,
        num=args.num,
        data_file=args.data_file,
        dev_tables_file=args.dev_tables,
        output_dir=args.output_dir,
        save_freq=args.save_freq,
        temperature=args.temperature,
        timeout=args.timeout,
        resume=not args.no_resume
    )


if __name__ == "__main__":
    main()
