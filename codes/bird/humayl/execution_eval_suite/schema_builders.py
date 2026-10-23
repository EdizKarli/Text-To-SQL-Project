import json
import os
import re
from collections import defaultdict, deque
from typing import Optional, Dict, Any, Set, List
from rank_bm25 import BM25Okapi
from rapidfuzz import fuzz


def find_dev_tables_path(custom_path: Optional[str] = None) -> str:
    """Auto-detects the dev_tables.json file path across standard project directories."""
    candidates = [
        custom_path,
        os.path.join("mini_dev_data", "MINIDEV", "dev_tables.json"),
        os.path.join("mini_dev_data", "dev_databases", "minidev", "MINIDEV", "dev_tables.json"),
        os.path.join("data_used_here", "dev_tables.json"),
        os.path.join("data", "dev_tables.json")
    ]
    for p in candidates:
        if p and os.path.exists(p):
            return os.path.abspath(p)
    raise FileNotFoundError(
        "Could not locate 'dev_tables.json'. Please specify its path or ensure "
        "'mini_dev_data/MINIDEV/dev_tables.json' exists."
    )


def tokenize(text: str) -> List[str]:
    """Tokenizes text while splitting camelCase and normalizing non-alphanumeric chars."""
    cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    cleaned = re.sub(r"[_\W]+", " ", cleaned).lower()
    return cleaned.split()


def sanitize_sql(raw_text: str) -> str:
    """Strips markdown code fences, leading labels, quotes, and trailing semicolons."""
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


class FullSchemaBuilder:
    """
    Ported from Ediz's bird_infer_schema.py.
    Builds the complete synthetic DDL schema and foreign-key links for each database.
    """
    def __init__(self, dev_tables_path: Optional[str] = None):
        self.tables_path = find_dev_tables_path(dev_tables_path)
        with open(self.tables_path, "r", encoding="utf-8") as f:
            self.tables_data = json.load(f)
        self.db_schemas = self._build_schemas()

    def _build_schemas(self) -> Dict[str, str]:
        schemas = {}
        for db in self.tables_data:
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

            schemas[db_id] = "\n\n".join(schema_parts)
        return schemas

    def get_schema(self, db_id: str) -> str:
        return self.db_schemas.get(db_id, "-- Schema not found --")


class SafeSchemaPruner:
    """
    Ported from Ediz's bird_infer_pruned_vol2.py.
    Implements BM25 + RapidFuzz table/column ranking, BFS bridge-table resolution,
    and PK/FK key protection.
    """
    def __init__(self, dev_tables_path: Optional[str] = None):
        self.tables_path = find_dev_tables_path(dev_tables_path)
        with open(self.tables_path, "r", encoding="utf-8") as f:
            self.tables_data = {db["db_id"]: db for db in json.load(f)}

    def _find_bridge_tables(self, seed_tables: Set[int], foreign_keys: List, column_names: List, num_tables: int) -> Set[int]:
        adj = defaultdict(set)
        for col_src, col_tgt in foreign_keys:
            t1 = column_names[col_src][0]
            t2 = column_names[col_tgt][0]
            if t1 != -1 and t2 != -1 and t1 != t2:
                adj[t1].add(t2)
                adj[t2].add(t1)

        expanded = set(seed_tables)
        seeds = list(seed_tables)
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

                if found_path and len(found_path) <= 4:
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

        raw_pks = db.get("primary_keys", [])
        primary_keys = set()
        for pk in raw_pks:
            if isinstance(pk, list):
                primary_keys.update(pk)
            elif pk is not None:
                primary_keys.add(pk)

        fk_columns = set()
        for col_src, col_tgt in foreign_keys:
            fk_columns.add(col_src)
            fk_columns.add(col_tgt)

        query_text = f"{question} {evidence}".strip()
        query_tokens = tokenize(query_text)

        # 1. Table Selection
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
            selected_tables = self._find_bridge_tables(seed_tables, foreign_keys, column_names, len(table_names))

        # 2. Column Selection
        table_cols = {idx: [] for idx in selected_tables}
        for col_idx, (tbl_idx, col_name) in enumerate(column_names):
            if tbl_idx in selected_tables and tbl_idx != -1:
                table_cols[tbl_idx].append((col_idx, col_name, column_types[col_idx]))

        final_table_cols = {}
        for tbl_idx, cols in table_cols.items():
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
                    is_key = col_idx in primary_keys or col_idx in fk_columns
                    key_boost = 5.0 if is_key else 0.0
                    scored_cols.append((b_score + (1.5 * f_score) + key_boost, (col_idx, col_name, col_type), is_key))

                scored_cols.sort(key=lambda x: x[0], reverse=True)
                top_selection = {item[1] for item in scored_cols[:16]}
                for _, meta, is_key in scored_cols:
                    if is_key:
                        top_selection.add(meta)

                final_table_cols[tbl_idx] = list(top_selection)

        # 3. DDL Reconstruction
        schema_parts = []
        for tbl_idx in selected_tables:
            col_lines = []
            for col_idx, col_name, col_type in final_table_cols.get(tbl_idx, []):
                is_pk = " PRIMARY KEY" if col_idx in primary_keys else ""
                col_lines.append(f"  {col_name} {col_type}{is_pk}")
            schema_parts.append(f"CREATE TABLE {table_names[tbl_idx]} (\n" + ",\n".join(col_lines) + "\n);")

        # 4. Foreign Key Comments
        fk_lines = []
        for col_src, col_tgt in foreign_keys:
            t_src, c_src = column_names[col_src]
            t_tgt, c_tgt = column_names[col_tgt]
            if t_src in selected_tables and t_tgt in selected_tables:
                fk_lines.append(f"-- FK: {table_names[t_src]}.{c_src} -> {table_names[t_tgt]}.{c_tgt}")

        if fk_lines:
            schema_parts.append("\n".join(fk_lines))

        return "\n\n".join(schema_parts)
