#!/usr/bin/env python3
"""Build questions/questions_normal.json from questions/question_bank.py.

120 base questions x 4 phrasing styles = 480 questions: 160 per difficulty, 40 per style within each difficulty.
Use --bases-per-difficulty 30 for 360 questions (120 per difficulty, 30 per style).
All four phrasings of a base question share one Gold SQL, so their Gold results are identical.

Each entry: id (e.g. 'E07-BIZ'), base_id, difficulty (easy/moderate/hard), style, concepts, question (rendered for
the normal schema), question_template (schema_aware placeholders kept for the other variants), answer_spec, gold_sql.
scripts/build_variants.py derives questions_mixed.json and questions_cryptic.json from this file.
"""
import json, os, re, sqlite3, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import question_bank as qb  # noqa: E402

STYLE_CODE = {"casual": "CAS", "schema_aware": "SCH", "business_executive": "BIZ", "vague": "VAG"}
DIFFICULTY = {"E": "easy", "M": "moderate", "H": "hard"}
PLACEHOLDER = re.compile(r"\[\[([a-z_]+)(?:\.([a-z_0-9]+))?\]\]")


def render(template, naming):
    """naming: {table: {"name": new_table, "columns": {col: new_col}}} ([[t]] -> table, [[t.c]] -> column)."""
    def rep(m):
        t, c = m.group(1), m.group(2)
        return naming[t]["columns"][c] if c else naming[t]["name"]
    return PLACEHOLDER.sub(rep, template)


def normal_naming():
    con = sqlite3.connect(":memory:")
    con.executescript(open(os.path.join(ROOT, "schema", "schema.sql"), encoding="utf-8").read())
    tables = [t for (t,) in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    return {t: {"name": t, "columns": {r[1]: r[1] for r in con.execute(f"PRAGMA table_info({t})")}} for t in tables}


def build(bases_per_difficulty=40):
    naming = normal_naming()
    talk = {**qb.TALK_EASY, **qb.TALK_MODERATE, **qb.TALK_HARD}
    assert len(qb.EASY + qb.MODERATE + qb.HARD) == 120 and len(talk) == 120, "bank incomplete"
    bases = qb.EASY[:bases_per_difficulty] + qb.MODERATE[:bases_per_difficulty] + qb.HARD[:bases_per_difficulty]
    out = []
    for base_id, concepts, spec, sql in bases:
        phr = talk[base_id]
        assert len(phr) == 4, base_id
        for style, template in zip(qb.STYLES, phr):
            for m in PLACEHOLDER.finditer(template):            # every placeholder must exist in the normal schema
                t, c = m.group(1), m.group(2)
                assert t in naming and (c is None or c in naming[t]["columns"]), f"{base_id}/{style}: bad placeholder {m.group(0)}"
            if style != "schema_aware":
                assert not PLACEHOLDER.search(template), f"{base_id}/{style}: placeholders only belong in schema_aware"
            out.append(dict(id=f"{base_id}-{STYLE_CODE[style]}", base_id=base_id, difficulty=DIFFICULTY[base_id[0]],
                            style=style, concepts=concepts, question=render(template, naming),
                            question_template=template, answer_spec=spec,
                            gold_sql=" ".join(sql.split())))  # one line in the JSON
    return out


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--bases-per-difficulty", type=int, default=40, choices=range(1, 41), metavar="1-40",
                    help="40 (default) -> 160 questions per difficulty (40 per style); 30 -> 120 per difficulty (30 per style)")
    qs = build(ap.parse_args().bases_per_difficulty)
    path = os.path.join(HERE, "questions_normal.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(qs, fh, indent=2, ensure_ascii=False)
    from collections import Counter
    print(f"wrote {len(qs)} questions -> {path}")
    for d in ("easy", "moderate", "hard"):
        print(f"  {d:9s}", dict(Counter(q["style"] for q in qs if q["difficulty"] == d)))
