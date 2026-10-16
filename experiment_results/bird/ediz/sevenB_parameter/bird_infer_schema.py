import json
import os
import re
import requests


def sanitize_sql(raw_text: str) -> str:
    cleaned = raw_text.replace("```sql", "").replace("```", "")
    cleaned = " ".join(cleaned.split())
    cleaned = re.sub(r"^(?i:sql\s*:\s*)", "", cleaned.strip())
    cleaned = cleaned.strip("`'\"").strip()
    cleaned = re.sub(r";+$", "", cleaned).strip()
    return cleaned


def build_schema_prompts(tables_path):
    """Parses dev_tables.json into clean CREATE TABLE-like schema strings keyed by db_id."""
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

        # Group columns by table index
        tables = {i: [] for i in range(len(table_names))}
        for col_idx, (tbl_idx, col_name) in enumerate(column_names):
            if tbl_idx == -1:  # special '*' column
                continue
            col_type = column_types[col_idx]
            is_pk = " PRIMARY KEY" if col_idx in primary_keys else ""
            tables[tbl_idx].append(f"  {col_name} {col_type}{is_pk}")

        # Assemble schema strings
        schema_parts = []
        for tbl_idx, tbl_name in enumerate(table_names):
            cols_def = ",\n".join(tables[tbl_idx])
            schema_parts.append(
                f"CREATE TABLE {tbl_name} (\n{cols_def}\n);"
            )

        # Append Foreign Key constraints if present
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


def run_bird_inference_with_schema():
    # 1. Path setup
    tables_file = os.path.join(
        "mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_tables.json"
    )
    if not os.path.exists(tables_file):
        tables_file = os.path.join("mini_dev_data", "MINIDEV", "dev_tables.json")

    print(f"Loading schema definitions from {tables_file}...")
    schemas = build_schema_prompts(tables_file)

    # 2. Load questions
    with open("data/mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
        data = (
            json.loads(content)
            if content.startswith("[")
            else [json.loads(line) for line in content.splitlines() if line.strip()]
        )

    predictions = {}
    total = len(data)
    print(f"Loaded {total} questions. Starting schema-guided inference with Qwen 2.5 7B...")

    for idx, item in enumerate(data, 1):
        db_id = item["db_id"]
        qid = str(item.get("question_id", idx))
        question = item["question"]
        evidence = item.get("evidence", "")
        db_schema = schemas.get(db_id, "-- Schema not found --")

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
                timeout=180,
            )
            response.raise_for_status()
            raw_response = response.json().get("response", "").strip()
        except Exception as e:
            print(f"[{idx}/{total}] Request failed for QID {qid}: {e}")
            raw_response = "SELECT 1;"

        clean_sql = sanitize_sql(raw_response)

        # Store using the separator required by BIRD package_sqls
        predictions[qid] = f"{clean_sql}\t----- bird -----\t{db_id}"
        print(f"[{idx}/{total}] Processed QID: {qid} ({db_id})")

    # 3. Save directly to predict_mini_dev_schema.json
    output_path = "predict_mini_dev_schema.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    print(f"\nCompleted! Predictions saved to {output_path}")


if __name__ == "__main__":
    run_bird_inference_with_schema()