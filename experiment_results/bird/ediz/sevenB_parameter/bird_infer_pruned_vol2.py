import json
import os
import re
import requests
from collections import defaultdict, deque
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz


def tokenize(text: str) -> list[str]:
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    cleaned = re.sub(r"[_\W]+", " ", cleaned).lower()
    return cleaned.split()


class SafeSchemaPruner:
    def __init__(self, dev_tables_path: str):
        with open(dev_tables_path, "r", encoding="utf-8") as f:
            self.tables_data = {db["db_id"]: db for db in json.load(f)}

    def _find_bridge_tables(self, seed_tables: set, foreign_keys: list, column_names: list, num_tables: int) -> set:
        """Finds intermediate bridge tables via BFS on the Foreign Key graph."""
        adj = defaultdict(set)
        for col_src, col_tgt in foreign_keys:
            t1 = column_names[col_src][0]
            t2 = column_names[col_tgt][0]
            if t1 != -1 and t2 != -1 and t1 != t2:
                adj[t1].add(t2)
                adj[t2].add(t1)

        expanded = set(seed_tables)
        seeds = list(seed_tables)
        # Find shortest paths between all pairs of seed tables
        for i in range(len(seeds)):
            for j in range(i + 1, len(seeds)):
                src, dst = seeds[i], seeds[j]
                queue = deque([(src, [src])])
                visited = {src}
                found_path = None

                while queue:
                    curr, path = queue.popleft()
                    if curr == dst:
                        found_path = path
                        break
                    for neighbor in adj[curr]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append((neighbor, path + [neighbor]))

                if found_path and len(found_path) <= 4:  # At most 2 intermediate bridge hops
                    expanded.update(found_path)

        return expanded

    def extract_relevant_schema(self, db_id: str, question: str, evidence: str = "") -> str:
        db = self.tables_data.get(db_id)
        if not db:
            return "-- Schema not found --"

        table_names = db["table_names_original"]
        column_names = db["column_names_original"]
        column_types = db["column_types"]
        foreign_keys = db.get("foreign_keys", [])

        # Flatten composite primary keys safely
        raw_pks = db.get("primary_keys", [])
        primary_keys = set()
        for pk in raw_pks:
            if isinstance(pk, list):
                primary_keys.update(pk)
            elif pk is not None:
                primary_keys.add(pk)

        # Build set of all foreign key column indices
        fk_columns = set()
        for col_src, col_tgt in foreign_keys:
            fk_columns.add(col_src)
            fk_columns.add(col_tgt)

        query_text = f"{question} {evidence}".strip()
        query_tokens = tokenize(query_text)

        # 1. Table Selection: Keep all if <= 6 tables, otherwise score + FK-bridge
        if len(table_names) <= 6:
            selected_tables = set(range(len(table_names)))
        else:
            table_corpus = [tokenize(tbl) for tbl in table_names]
            bm25_t = BM25Okapi(table_corpus)
            bm25_scores = bm25_t.get_scores(query_tokens)

            scored_tables = []
            for idx, tbl in enumerate(table_names):
                b_score = bm25_scores[idx]
                f_score = fuzz.partial_ratio(tbl.lower(), query_text.lower()) / 100.0
                scored_tables.append((idx, b_score + (1.5 * f_score)))

            scored_tables.sort(key=lambda x: x[1], reverse=True)
            seed_tables = {idx for idx, _ in scored_tables[:4]}
            # Recover bridge tables via FK graph
            selected_tables = self._find_bridge_tables(seed_tables, foreign_keys, column_names, len(table_names))

        # 2. Column Selection per Table
        table_cols = {idx: [] for idx in selected_tables}
        for col_idx, (tbl_idx, col_name) in enumerate(column_names):
            if tbl_idx in selected_tables and tbl_idx != -1:
                table_cols[tbl_idx].append((col_idx, col_name, column_types[col_idx]))

        final_table_cols = {}
        for tbl_idx, cols in table_cols.items():
            # If table is small, keep all columns to avoid dropping filter targets
            if len(cols) <= 15:
                final_table_cols[tbl_idx] = cols
            else:
                col_corpus = [tokenize(f"{table_names[tbl_idx]} {c[1]}") for c in cols]
                bm25_c = BM25Okapi(col_corpus)
                c_scores = bm25_c.get_scores(query_tokens)

                scored_cols = []
                for i, (col_idx, col_name, col_type) in enumerate(cols):
                    b_score = c_scores[i]
                    f_score = fuzz.partial_ratio(col_name.lower(), query_text.lower()) / 100.0
                    # Critical: Always prioritize PK and FK columns
                    is_key = col_idx in primary_keys or col_idx in fk_columns
                    key_boost = 5.0 if is_key else 0.0
                    scored_cols.append((b_score + (1.5 * f_score) + key_boost, (col_idx, col_name, col_type), is_key))

                # Keep top 16 columns + any mandatory keys
                scored_cols.sort(key=lambda x: x[0], reverse=True)
                top_selection = {item[1] for item in scored_cols[:16]}
                for _, meta, is_key in scored_cols:
                    if is_key:
                        top_selection.add(meta)

                final_table_cols[tbl_idx] = list(top_selection)

        # 3. Assemble Schema DDL
        schema_parts = []
        for tbl_idx in selected_tables:
            col_lines = []
            for col_idx, col_name, col_type in final_table_cols.get(tbl_idx, []):
                is_pk = " PRIMARY KEY" if col_idx in primary_keys else ""
                col_lines.append(f"  {col_name} {col_type}{is_pk}")
            schema_parts.append(f"CREATE TABLE {table_names[tbl_idx]} (\n" + ",\n".join(col_lines) + "\n);")

        fk_lines = []
        for col_src, col_tgt in foreign_keys:
            t_src, c_src = column_names[col_src]
            t_tgt, c_tgt = column_names[col_tgt]
            if t_src in selected_tables and t_tgt in selected_tables:
                fk_lines.append(f"-- FK: {table_names[t_src]}.{c_src} -> {table_names[t_tgt]}.{c_tgt}")

        if fk_lines:
            schema_parts.append("\n".join(fk_lines))

        return "\n\n".join(schema_parts)


def run_inference():
    tables_file = os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_tables.json")
    if not os.path.exists(tables_file):
        tables_file = os.path.join("mini_dev_data", "MINIDEV", "dev_tables.json")

    pruner = SafeSchemaPruner(tables_file)

    with open("data/mini_dev_sqlite.json", "r", encoding="utf-8") as f:
        content = f.read().strip()
        data = json.loads(content) if content.startswith("[") else [json.loads(x) for x in content.splitlines() if x.strip()]

    predictions = {}
    total = len(data)
    print(f"Loaded {total} questions. Starting Safe Graph-Aware Pruned Inference...")

    for idx, item in enumerate(data, 1):
        db_id = item["db_id"]
        qid = str(item.get("question_id", idx))
        question = item["question"]
        evidence = item.get("evidence", "")

        pruned_schema = pruner.extract_relevant_schema(db_id, question, evidence)

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

        try:
            res = requests.post(
                "http://localhost:11434/api/generate",
                json={"model": "qwen2.5:7b", "prompt": prompt, "stream": False, "options": {"temperature": 0.0, "num_ctx": 8192}},
                timeout=180,
            )
            raw = res.json().get("response", "").strip()
        except Exception as e:
            print(f"[{idx}/{total}] Error on QID {qid}: {e}")
            raw = "SELECT 1;"

        clean_sql = raw.replace("```sql", "").replace("```", "").replace("\r", " ").replace("\n", " ").strip()
        predictions[qid] = f"{clean_sql}\t----- bird -----\t{db_id}"
        print(f"[{idx}/{total}] Processed QID: {qid} ({db_id})")

    out_file = "predict_mini_dev_pruned_v2.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

    print(f"\nPredictions written to {out_file}")


if __name__ == "__main__":
    run_inference()