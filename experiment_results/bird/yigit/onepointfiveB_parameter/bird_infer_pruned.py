import json
import os
import re
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


class HybridSchemaPruner:
    def __init__(self, dev_tables_path: str):
        with open(dev_tables_path, "r", encoding="utf-8") as f:
            self.tables_data = {db["db_id"]: db for db in json.load(f)}

    def extract_relevant_schema(
        self,
        db_id: str,
        question: str,
        evidence: str = "",
        top_k_tables: int = 4,
        top_k_columns_per_table: int = 8,
    ) -> str:
        db = self.tables_data.get(db_id)
        if not db:
            return "-- Schema not found --"

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

        query_text = f"{question} {evidence}".strip()
        query_tokens = tokenize(query_text)

        if len(table_names) <= top_k_tables:
            selected_table_indices = set(range(len(table_names)))
        else:
            table_tokenized_corpus = [tokenize(tbl) for tbl in table_names]
            bm25_tables = BM25Okapi(table_tokenized_corpus)
            bm25_scores = bm25_tables.get_scores(query_tokens)

            scored_tables = []
            for tbl_idx, tbl_name in enumerate(table_names):
                b_score = bm25_scores[tbl_idx]
                f_score = fuzz.partial_ratio(tbl_name.lower(), query_text.lower()) / 100.0
                scored_tables.append((tbl_idx, b_score + (1.5 * f_score)))

            scored_tables.sort(key=lambda x: x[1], reverse=True)
            selected_table_indices = {idx for idx, _ in scored_tables[:top_k_tables]}

        table_to_cols = {idx: [] for idx in selected_table_indices}
        for col_idx, (tbl_idx, col_name) in enumerate(column_names):
            if tbl_idx in selected_table_indices and tbl_idx != -1:
                table_to_cols[tbl_idx].append((col_idx, col_name, column_types[col_idx]))

        final_table_cols = {}
        for tbl_idx, cols in table_to_cols.items():
            if len(cols) <= top_k_columns_per_table:
                chosen = cols
            else:
                col_corpus = [tokenize(f"{table_names[tbl_idx]} {c[1]}") for c in cols]
                bm25_cols = BM25Okapi(col_corpus)
                c_scores = bm25_cols.get_scores(query_tokens)

                scored_cols = []
                for i, (col_idx, col_name, col_type) in enumerate(cols):
                    b_score = c_scores[i]
                    f_score = fuzz.partial_ratio(col_name.lower(), query_text.lower()) / 100.0
                    pk_boost = 2.5 if col_idx in primary_keys else 0.0
                    total_score = b_score + (1.5 * f_score) + pk_boost
                    scored_cols.append((total_score, (col_idx, col_name, col_type)))

                scored_cols.sort(key=lambda x: x[0], reverse=True)
                chosen = [c[1] for c in scored_cols[:top_k_columns_per_table]]

            cols_def = []
            for col_idx, col_name, col_type in chosen:
                is_pk = " PRIMARY KEY" if col_idx in primary_keys else ""
                cols_def.append(f"  {col_name} {col_type}{is_pk}")
            final_table_cols[tbl_idx] = cols_def

        schema_parts = []
        for tbl_idx in selected_table_indices:
            cols_str = ",\n".join(final_table_cols.get(tbl_idx, []))
            schema_parts.append(f"CREATE TABLE {table_names[tbl_idx]} (\n{cols_str}\n);")

        fk_strings = []
        for col_src, col_tgt in foreign_keys:
            tbl_src_idx, col_src_name = column_names[col_src]
            tbl_tgt_idx, col_tgt_name = column_names[col_tgt]
            if tbl_src_idx in selected_table_indices and tbl_tgt_idx in selected_table_indices:
                fk_strings.append(
                    f"-- FK: {table_names[tbl_src_idx]}.{col_src_name} -> {table_names[tbl_tgt_idx]}.{col_tgt_name}"
                )

        if fk_strings:
            schema_parts.append("\n".join(fk_strings))

        return "\n\n".join(schema_parts)


def run_pruned_inference():
    tables_file = os.path.join(
        "mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_tables.json"
    )
    if not os.path.exists(tables_file):
        tables_file = os.path.join("mini_dev_data", "MINIDEV", "dev_tables.json")

    print(f"Initializing BM25 + Fuzzy pruner from: {tables_file}")
    pruner = HybridSchemaPruner(tables_file)

    with open("data/mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
        data = (
            json.loads(content)
            if content.startswith("[")
            else [json.loads(x) for x in content.splitlines() if x.strip()]
        )

    predictions = {}
    total = len(data)
    print(f"Loaded {total} questions. Starting hybrid pruned inference with Qwen 2.5 7B...")

    for idx, item in enumerate(data, 1):
        db_id = item["db_id"]
        qid = str(item.get("question_id", idx))
        question = item["question"]
        evidence = item.get("evidence", "")

        pruned_schema = pruner.extract_relevant_schema(
            db_id=db_id,
            question=question,
            evidence=evidence,
            top_k_tables=4,
            top_k_columns_per_table=8,
        )

        prompt = (
            f"You are an expert SQL assistant. Given the relevant SQLite database schema:\n"
            f"```sql\n{pruned_schema}\n```\n\n"
            f"Database name: {db_id}\n"
            f"Evidence: {evidence}\n"
            f"Question: {question}\n\n"
            f"Write a valid SQLite query to answer the question using only the tables and columns defined above. "
            f"Output ONLY the SQL statement on a single line without explanations or markdown.\n"
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
                        "num_ctx": 4096,
                    },
                },
                timeout=180,
            )
            response.raise_for_status()
            raw_response = response.json().get("response", "").strip()
        except Exception as e:
            print(f"[{idx}/{total}] QID {qid} error: {e}")
            raw_response = "SELECT 1;"

        clean_sql = sanitize_sql(raw_response)
        predictions[qid] = f"{clean_sql}\t----- bird -----\t{db_id}"
        print(f"[{idx}/{total}] Processed QID: {qid} ({db_id})")

    output_path = "predict_mini_dev_pruned.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    print(f"\nAll done! Output written to {output_path}")


if __name__ == "__main__":
    run_pruned_inference()