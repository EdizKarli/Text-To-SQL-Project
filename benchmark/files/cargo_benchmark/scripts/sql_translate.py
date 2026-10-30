"""Translate SQL written against the NORMAL schema into an equivalent query for another schema variant.

Uses sqlglot (pip install sqlglot) to parse the query, resolve every column to its source table
(qualify + scopes), and rename tables, columns and auto-generated aliases. Also used to translate DDL-free
artefacts such as Gold SQL and validation checks. The result is verified by execution in build_variants.py.
"""
import sqlglot
from sqlglot import exp
from sqlglot.optimizer.qualify import qualify
from sqlglot.optimizer.scope import traverse_scope, Scope


def _source(scope, alias):
    s = scope
    while s is not None:
        if alias in s.sources:
            return s.sources[alias]
        s = s.parent
    return None


def translate(sql, mapping, schema):
    """mapping: {normal_table: (new_table, {normal_col: new_col})}; schema: {table: {col: type}} (normal)."""
    tree = sqlglot.parse_one(sql, read="sqlite")
    tree = qualify(tree, schema=schema, dialect="sqlite", quote_identifiers=False, identify=False,
                   validate_qualify_columns=True, expand_alias_refs=False)

    # aliases that qualify() invented (alias == real table name) are renamed to the new table name
    auto_alias = {}
    for t in tree.find_all(exp.Table):
        if t.name in mapping and t.alias == t.name:
            auto_alias[t.name] = mapping[t.name][0]

    derived = {}                       # id(scope.expression) -> {old output name: new output name}
    done = set()                       # a correlated column can be listed by more than one scope
    for scope in traverse_scope(tree):
        renamed_outputs = {}
        for col in scope.columns:
            if not col.table or id(col) in done:
                continue
            done.add(id(col))
            src = _source(scope, col.table)
            if isinstance(src, exp.Table) and src.name in mapping:
                old = col.name
                new = mapping[src.name][1][old]
                col.set("this", exp.to_identifier(new))
            elif isinstance(src, Scope):
                ren = derived.get(id(src.expression), {})
                if col.name in ren:
                    col.set("this", exp.to_identifier(ren[col.name]))
        # projection aliases that merely repeat a source column name follow the rename
        sel = scope.expression
        if isinstance(sel, exp.Select):
            for proj in sel.expressions:
                if isinstance(proj, exp.Alias) and isinstance(proj.this, exp.Column) and proj.this.name != proj.alias:
                    src = _source(scope, proj.this.table)
                    origin_names = set()
                    if isinstance(src, exp.Table) and src.name in mapping:
                        origin_names = {k for k, v in mapping[src.name][1].items() if v == proj.this.name}
                    elif isinstance(src, Scope):
                        origin_names = {k for k, v in derived.get(id(src.expression), {}).items() if v == proj.this.name}
                    if proj.alias in origin_names:
                        renamed_outputs[proj.alias] = proj.this.name
                        proj.set("alias", exp.to_identifier(proj.this.name))
            order = sel.args.get("order")
            if order is not None and renamed_outputs:
                for c in order.find_all(exp.Column):
                    if not c.table and c.name in renamed_outputs:
                        c.set("this", exp.to_identifier(renamed_outputs[c.name]))
        derived[id(sel)] = renamed_outputs
        # set operations / CTE wrappers expose the outputs of their left-most select
        if isinstance(sel, exp.SetOperation):
            left = sel.left
            derived[id(sel)] = derived.get(id(left), {})

    for c in tree.find_all(exp.Column):
        if c.table in auto_alias:
            c.set("table", exp.to_identifier(auto_alias[c.table]))
    for t in tree.find_all(exp.Table):
        if t.name in mapping:
            alias = t.alias
            t.set("this", exp.to_identifier(mapping[t.name][0]))
            if alias in auto_alias:
                t.set("alias", exp.TableAlias(this=exp.to_identifier(auto_alias[alias])))
    return tree.sql(dialect="sqlite")          # single line, like BIRD gold SQL
