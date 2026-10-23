import json
import os
import re
import sqlite3
import time
import requests
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz


def sanitize_sql(raw_text: str) -> str:
    cleaned = raw_text.replace("```sql", "").replace("```", "")
    cleaned = " ".join(cleaned.split())
    cleaned = re.sub(r"^(?i:sql\s*:\s*)", "", cleaned.strip())
    if (cleaned.startswith("`") and cleaned.endswith("`")) or \
       (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    cleaned = re.sub(r";+$", "", cleaned).strip()
    return cleaned


def tokenize(text: str) -> list[str]:
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    cleaned = re.sub(r"[_\W]+", " ", cleaned).lower()
    return cleaned.split()


class EvidenceRetriever:
    """Indexes domain notes per database and retrieves relevant rules for each question."""
    def __init__(self, dict_path: str = "evidence_dict.json"):
        self.index = {}
        if not os.path.exists(dict_path):
            print(f"[Warning] '{dict_path}' not found. Running without dictionary retrieval.", flush=True)
            return

        with open(dict_path, "r", encoding="utf-8") as f:
            self.evidence_dict = json.load(f)

        for db_id, rules in self.evidence_dict.items():
            if rules:
                corpus = [tokenize(rule) for rule in rules]
                self.index[db_id] = {
                    "bm25": BM25Okapi(corpus),
                    "rules": rules,
                }

    def search_evidence(self, db_id: str, question: str, top_k: int = 3) -> str:
        if db_id not in self.index:
            return ""

        query_tokens = tokenize(question)
        if not query_tokens:
            return ""

        bm25_model = self.index[db_id]["bm25"]
        rules = self.index[db_id]["rules"]
        scores = bm25_model.get_scores(query_tokens)

        scored = []
        for i, rule in enumerate(rules):
            b_score = scores[i]
            f_score = fuzz.partial_ratio(rule.lower(), question.lower()) / 100.0
            scored.append((b_score + (1.5 * f_score), rule))

        scored.sort(key=lambda x: x[0], reverse=True)
        return "; ".join([rule for _, rule in scored[:top_k]])


def build_db_path_map(root_dir: str = "mini_dev_data") -> dict[str, str]:
    db_map = {}
    if not os.path.exists(root_dir):
        return db_map

    for dirpath, _, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".sqlite"):
                db_name = f[:-7]  # remove '.sqlite' extension
                if db_name not in db_map:
                    db_map[db_name] = os.path.join(dirpath, f)
    return db_map


def locate_tables_json() -> str:
    candidates = [
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_tables.json"),
        os.path.join("mini_dev_data", "MINIDEV", "dev_tables.json"),
        os.path.join("data", "dev_tables.json"),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    for root, _, files in os.walk("mini_dev_data"):
        if "dev_tables.json" in files:
            return os.path.join(root, "dev_tables.json")
    return ""


def build_schema_prompts(tables_path: str):
    if not tables_path or not os.path.exists(tables_path):
        print(f"[Error] tables_path '{tables_path}' does not exist.", flush=True)
        return {}

    with open(tables_path, "r", encoding="utf-8") as f:
        tables_data = json.load(f)

    db_schemas = {}
    for db in tables_data:
        db_id = db["db_id"]
        table_names = db["table_names_original"]
        column_names = db["column_names_original"]
        column_types = db["column_types"]
        primary_keys = db.get("primary_keys", [])
        foreign_keys = db.get("foreign_keys", [])

        tables = {i: [] for i in range(len(table_names))}
        for col_idx, (tbl_idx, col_name) in enumerate(column_names):
            if tbl_idx == -1:
                continue
            col_type = column_types[col_idx]
            is_pk = " PRIMARY KEY" if col_idx in primary_keys else ""
            tables[tbl_idx].append(f"  {col_name} {col_type}{is_pk}")

        schema_parts = []
        for tbl_idx, tbl_name in enumerate(table_names):
            cols_def = ",\n".join(tables[tbl_idx])
            schema_parts.append(f"CREATE TABLE {tbl_name} (\n{cols_def}\n);")

        fk_strings = []
        for col_src, col_tgt in foreign_keys:
            tbl_src_idx, col_src_name = column_names[col_src]
            tbl_tgt_idx, col_tgt_name = column_names[col_tgt]
            fk_strings.append(
                f"-- FK: {table_names[tbl_src_idx]}.{col_src_name} -> {table_names[tbl_tgt_idx]}.{col_tgt_name}"
            )

        if fk_strings:
            schema_parts.append("\n".join(fk_strings))

        db_schemas[db_id] = "\n\n".join(schema_parts)

    return db_schemas


def execute_sqlite_query_with_timeout(db_path: str, query: str, timeout_seconds: float = 8.0):
    """
    Executes a SQLite query in read-only mode and uses set_progress_handler
    to terminate execution if it exceeds timeout_seconds.
    """
    if not db_path or not os.path.exists(db_path):
        return None, f"Database file not found: '{db_path}'"

    start_exec = time.time()

    def progress_callback():
        if time.time() - start_exec > timeout_seconds:
            return 1  # Non-zero return halts execution immediately
        return 0

    conn = None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.set_progress_handler(progress_callback, 1000)
        cursor = conn.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return set(result), None
    except sqlite3.OperationalError as e:
        if "interrupted" in str(e).lower():
            return None, f"Query Timed Out (> {timeout_seconds}s)"
        return None, str(e)
    except Exception as e:
        return None, str(e)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass


def run_bird_inference_with_dict():
    tables_file = locate_tables_json()
    print(f"Loading schema definitions from: {tables_file}", flush=True)
    schemas = build_schema_prompts(tables_file)

    print("Indexing SQLite database files...", flush=True)
    db_paths = build_db_path_map("mini_dev_data")
    print(f"Discovered {len(db_paths)} database files.", flush=True)

    retriever = EvidenceRetriever("evidence_dict.json")

    with open("data/mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
        data = (
            json.loads(content)
            if content.startswith("[")
            else [json.loads(line) for line in content.splitlines() if line.strip()]
        )

    predictions = {}
    latencies = []
    correct_count = 0
    valid_syntax_count = 0
    total = len(data)

    print(f"Loaded {total} questions. Starting inference with qwen2.5-coder:7b...\n", flush=True)

    for idx, item in enumerate(data, 1):
        db_id = item["db_id"]
        qid = str(item.get("question_id", idx))
        question = item["question"]
        gold_sql = item.get("SQL", "")

        print(f"[{idx}/{total}] Processing QID {qid} ({db_id})...", end="", flush=True)

        retrieved_evidence = retriever.search_evidence(db_id, question, top_k=3)
        db_schema = schemas.get(db_id, "-- Schema not found --")

        prompt = (
            f"You are an expert SQL assistant. Given the following SQLite database schema:\n"
            f"```sql\n{db_schema}\n```\n\n"
            f"Database name: {db_id}\n"
            f"Retrieved Domain Notes: {retrieved_evidence}\n"
            f"Question: {question}\n\n"
            f"Write a valid SQLite query to answer the question using only the tables and columns defined above. "
            f"Output ONLY the SQL statement on a single line. Do not include markdown fences, comments, or explanations.\n"
            f"SQL:"
        )

        start_time = time.perf_counter()
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5-coder:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_ctx": 4096,
                    },
                },
                timeout=120,
            )
            response.raise_for_status()
            raw_response = response.json().get("response", "").strip()
        except Exception as e:
            print(f" [Ollama API Error: {e}]", end="", flush=True)
            raw_response = "SELECT 1;"

        elapsed_seconds = time.perf_counter() - start_time
        latencies.append(elapsed_seconds)

        clean_sql = sanitize_sql(raw_response)
        predictions[qid] = f"{clean_sql}\t----- bird -----\t{db_id}"

        # Safe execution check with 8.0s timeout
        db_path = db_paths.get(db_id, "")
        pred_res, pred_err = execute_sqlite_query_with_timeout(db_path, clean_sql, timeout_seconds=8.0)
        gold_res, _ = execute_sqlite_query_with_timeout(db_path, gold_sql, timeout_seconds=8.0)

        is_correct = False
        if pred_err is None:
            valid_syntax_count += 1
            if pred_res is not None and gold_res is not None and pred_res == gold_res:
                is_correct = True
                correct_count += 1

        print(
            f" Done ({elapsed_seconds:.2f}s) | Valid: {'Y' if pred_err is None else 'N'} | Match: {'YES' if is_correct else 'NO'}",
            flush=True
        )

        if not is_correct and idx <= 5:
            if pred_err:
                print(f"   [SQLite Error]: {pred_err}", flush=True)
            print(f"   [Model SQL]   : {clean_sql}", flush=True)
            print(f"   [Gold SQL]    : {gold_sql}", flush=True)

    output_path = "predict_mini_dev_dict.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    acc = (correct_count / total) * 100 if total > 0 else 0.0
    valid_rate = (valid_syntax_count / total) * 100 if total > 0 else 0.0

    print("\n" + "=" * 48, flush=True)
    print("           EVALUATION SUMMARY", flush=True)
    print("=" * 48, flush=True)
    print(f"Total Questions Evaluated : {total}", flush=True)
    print(f"Execution Accuracy (EX)   : {acc:.2f}% ({correct_count}/{total})", flush=True)
    print(f"Valid Execution Rate      : {valid_rate:.2f}% ({valid_syntax_count}/{total})", flush=True)
    print(f"Average Latency / Query   : {avg_latency:.3f} s", flush=True)
    print(f"Predictions Saved To      : {output_path}", flush=True)
    print("=" * 48, flush=True)


if __name__ == "__main__":
    run_bird_inference_with_dict()