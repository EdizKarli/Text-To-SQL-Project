import json
import os
import re
import requests


def sanitize_sql(raw_text: str) -> str:
    # 1. Remove markdown fences (```sql and ```)
    cleaned = raw_text.replace("```sql", "").replace("```", "")
    
    # 2. Collapse internal newlines, tabs, and multiple spaces into a single line
    cleaned = " ".join(cleaned.split())
    
    # 3. Strip leading 'SQL:' or 'sql:' label if model echoed the prompt
    cleaned = re.sub(r"^(?i:sql\s*:\s*)", "", cleaned.strip())
    
    # 4. Strip trailing semicolons FIRST before checking boundaries
    cleaned = re.sub(r";+$", "", cleaned).strip()
    
    # 5. ONLY strip enclosing markdown backticks if they wrap the entire query
    if cleaned.startswith("`") and cleaned.endswith("`"):
        cleaned = cleaned[1:-1].strip()
        
    return cleaned


def build_spider_schemas(tables_path: str) -> dict:
    with open(tables_path, "r", encoding="utf-8") as f:
        tables_data = json.load(f)

    db_schemas = {}
    for db in tables_data:
        db_id = db["db_id"]
        table_names = db["table_names_original"]
        column_names = db["column_names_original"]
        column_types = db["column_types"]

        raw_pks = db.get("primary_keys", [])
        primary_keys = set()
        for pk in raw_pks:
            if isinstance(pk, list):
                primary_keys.update(pk)
            elif pk is not None:
                primary_keys.add(pk)

        foreign_keys = db.get("foreign_keys", [])

        # Group columns by table index
        tables = {i: [] for i in range(len(table_names))}
        for col_idx, (tbl_idx, col_name) in enumerate(column_names):
            if tbl_idx == -1:
                continue
            col_type = column_types[col_idx]
            is_pk = " PRIMARY KEY" if col_idx in primary_keys else ""
            tables[tbl_idx].append(f"  {col_name} {col_type}{is_pk}")

        # Assemble CREATE TABLE statements
        schema_parts = []
        for tbl_idx, tbl_name in enumerate(table_names):
            cols_def = ",\n".join(tables[tbl_idx])
            schema_parts.append(f"CREATE TABLE {tbl_name} (\n{cols_def}\n);")

        # Assemble Foreign Key references
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


def run_spider_inference(limit: int | None = None):
    tables_path = "data/tables.json"
    dev_path = "data/dev.json"

    print(f"Parsing schemas from {tables_path}...")
    schemas = build_spider_schemas(tables_path)

    with open(dev_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if limit is not None:
        data = data[:limit]

    total = len(data)
    predictions = []
    print(f"Loaded {total} questions. Starting schema-aware inference with Qwen 2.5 7B...")

    for idx, item in enumerate(data, 1):
        db_id = item["db_id"]
        question = item["question"]
        db_schema = schemas.get(db_id, "-- Schema not found --")

        prompt = (
            f"You are an expert SQL assistant. Given the following SQLite database schema:\n"
            f"```sql\n{db_schema}\n```\n\n"
            f"Database name: {db_id}\n"
            f"Question: {question}\n\n"
            f"Write a valid SQLite query to answer the question using only the tables and columns defined above. "
            f"Output ONLY the SQL statement on a single line. Do not include markdown fences, comments, or explanations.\n"
            f"SQL:"
        )

        try:
            res = requests.post(
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
            res.raise_for_status()
            raw = res.json().get("response", "").strip()
        except Exception as e:
            print(f"[{idx}/{total}] Error on question {idx}: {e}")
            raw = "SELECT 1;"

        clean_sql = sanitize_sql(raw)
        predictions.append(clean_sql)
        print(f"[{idx}/{total}] Processed ({db_id})")

    output_file = "predict_spider.sql"
    with open(output_file, "w", encoding="utf-8") as f:
        for sql in predictions:
            f.write(f"{sql}\n")

    print(f"\nInference completed! Saved {len(predictions)} predictions to {output_file}")


if __name__ == "__main__":
    run_spider_inference(limit=None)