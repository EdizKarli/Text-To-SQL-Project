import json
import os
import re
import sqlite3
import time
import requests


def sanitize_sql(raw_text: str) -> str:
    cleaned = raw_text.replace("```sql", "").replace("```", "")
    cleaned = " ".join(cleaned.split())
    cleaned = re.sub(r"^(?i:sql\s*:\s*)", "", cleaned.strip())
    # Only remove quotes/backticks if they surround the entire statement
    if (cleaned.startswith("`") and cleaned.endswith("`")) or \
       (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")):
        cleaned = cleaned[1:-1].strip()
    cleaned = re.sub(r";+$", "", cleaned).strip()
    return cleaned


def find_database_path(db_id: str) -> str:
    candidate_paths = [
        os.path.join("mini_dev_data", "dev_databases", db_id, f"{db_id}.sqlite"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", db_id, f"{db_id}.sqlite"),
        os.path.join("mini_dev_data", "MINIDEV", db_id, f"{db_id}.sqlite"),
        os.path.join("mini_dev_data", db_id, f"{db_id}.sqlite"),
        os.path.join("data", "dev_databases", db_id, f"{db_id}.sqlite"),
    ]
    for path in candidate_paths:
        if os.path.exists(path):
            return path
    return ""


def execute_sqlite_query(db_path: str, query: str):
    """Executes SQL in read-only mode and returns result tuples as a set for comparison."""
    if not db_path or not os.path.exists(db_path):
        return None, "Database file not found"
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5)
        cursor = conn.cursor()
        cursor.execute(query)
        res = cursor.fetchall()
        conn.close()
        return set(res), None
    except Exception as e:
        return None, str(e)


def run_bird_inference():
    # 1. Load questions from data folder
    with open("data/mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
        data = (
            json.loads(content)
            if content.startswith("[")
            else [json.loads(line) for line in content.splitlines() if line.strip()]
        )

    predictions = []
    latencies = []
    successful_blind_guesses = []
    
    correct_count = 0
    valid_syntax_count = 0
    total = len(data)
    
    print(f"Loaded {total} questions. Starting Ollama inference (NO-SCHEMA mode)...")

    for idx, item in enumerate(data, 1):
        db_id = item["db_id"]
        qid = str(item.get("question_id", idx))
        question = item["question"]
        gold_sql = item.get("SQL", "")

        prompt = (
            f"Given the database {db_id}.\n"
            f"Question: {question}\n"
            "Write a SQLite query to answer the question. Output ONLY the SQL query.\n"
            "SQL:"
        )

        start_time = time.perf_counter()
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "qwen2.5:7b",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.0,
                        "num_ctx": 8192,
                    },
                },
                timeout=120,
            )
            response.raise_for_status()
            raw_response = response.json().get("response", "").strip()
        except Exception as e:
            print(f"[{idx}/{total}] Request failed for QID {qid}: {e}")
            raw_response = "SELECT 1;"

        elapsed_time = time.perf_counter() - start_time
        latencies.append(elapsed_time)

        clean_sql = sanitize_sql(raw_response)
        predictions.append(f"{clean_sql}\t----- bird -----\t{db_id}\n")

        # 2. Execution evaluation against SQLite
        db_path = find_database_path(db_id)
        pred_res, pred_err = execute_sqlite_query(db_path, clean_sql)
        gold_res, gold_err = execute_sqlite_query(db_path, gold_sql)

        is_correct = False
        if pred_err is None:
            valid_syntax_count += 1
            if pred_res is not None and gold_res is not None and pred_res == gold_res:
                is_correct = True
                correct_count += 1
                
                # Format gold result sample for inspection
                gold_sample = list(gold_res)[:5]
                guess_record = {
                    "question_id": qid,
                    "db_id": db_id,
                    "question": question,
                    "predicted_sql": clean_sql,
                    "gold_sql": gold_sql,
                    "gold_result": [list(row) for row in gold_sample],
                    "total_rows": len(gold_res)
                }
                successful_blind_guesses.append(guess_record)

                print(f"\n[CORRECT GUESS WITHOUT SCHEMA!] QID: {qid} ({db_id})")
                print(f"  Question : {question}")
                print(f"  Pred SQL : {clean_sql}")
                print(f"  Gold SQL : {gold_sql}")
                print(f"  Gold Res : {gold_sample} (total rows: {len(gold_res)})\n")

        print(
            f"[{idx}/{total}] QID: {qid} | Time: {elapsed_time:.2f}s | "
            f"Valid SQL: {'YES' if pred_err is None else 'NO'} | Match: {'YES' if is_correct else 'NO'}"
        )

    # Save BIRD-formatted predictions
    with open("predict_mini_dev_no_schema.txt", "w", encoding="utf-8") as f:
        f.writelines(predictions)

    # Save detailed correct guesses to JSON for analysis
    with open("successful_no_schema_guesses.json", "w", encoding="utf-8") as f:
        json.dump(successful_blind_guesses, f, indent=2)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    acc = (correct_count / total) * 100 if total > 0 else 0.0
    valid_rate = (valid_syntax_count / total) * 100 if total > 0 else 0.0

    print("\n" + "=" * 50)
    print("      NO-SCHEMA INFERENCE EVALUATION SUMMARY")
    print("=" * 50)
    print(f"Total Questions Evaluated     : {total}")
    print(f"Execution Accuracy (EX)       : {acc:.2f}% ({correct_count}/{total})")
    print(f"Valid Execution Rate          : {valid_rate:.2f}% ({valid_syntax_count}/{total})")
    print(f"Average Latency / Query       : {avg_latency:.3f} s")
    print(f"Total Successful Blind Guesses: {len(successful_blind_guesses)}")
    print("Predictions saved to          : predict_mini_dev_no_schema.txt")
    print("Detailed matches logged to    : successful_no_schema_guesses.json")
    print("=" * 50)


if __name__ == "__main__":
    run_bird_inference()