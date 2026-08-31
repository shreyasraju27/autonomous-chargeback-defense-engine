import sqlglot
from sqlglot import exp
from sqlalchemy import text
from app.database import SessionLocal


class SecurityError(Exception):
    """Raised when a query fails guardrail validation."""
    pass


# Which tables and columns the AI is allowed to touch, and nothing else
ALLOWED_SCHEMA = {
    "orders": {"order_id", "merchant_id", "amount", "status", "created_at"},
    "delivery_logs": {"log_id", "merchant_id", "order_id", "delivered_at", "signature_ref"},
    "chat_messages": {"msg_id", "merchant_id", "order_id", "sender", "body_masked", "sent_at"},
}

DISALLOWED_NODE_TYPES = (
    exp.Insert,
    exp.Update,
    exp.Delete,
    exp.Drop,
    exp.Alter,
    exp.Create,
    exp.TruncateTable,
)


def validate_and_rewrite(sql: str, merchant_id: str, dialect: str = "sqlite") -> str:
    """
    Takes raw AI-generated SQL, validates it against strict rules,
    and returns a rewritten, guaranteed-safe version.
    Raises SecurityError if the query cannot be made safe.
    """

    # 1. Parse - reject if more than one statement (blocks "SELECT ...; DROP ...")
    try:
        statements = sqlglot.parse(sql, dialect=dialect)
    except Exception as e:
        raise SecurityError(f"SQL failed to parse: {e}")

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise SecurityError("Multi-statement queries are not permitted.")

    tree = statements[0]

    # 2. Must be a SELECT at the top level
    if not isinstance(tree, exp.Select):
        raise SecurityError("Only SELECT statements are permitted.")

    # 3. Walk the ENTIRE tree - catch hidden writes inside CTEs/subqueries
    for node in tree.walk():
        if isinstance(node, DISALLOWED_NODE_TYPES):
            raise SecurityError(f"Disallowed statement type found: {type(node).__name__}")
        if isinstance(node, exp.Star):
            raise SecurityError("Wildcard SELECT (*) is not permitted; columns must be explicit.")
        if isinstance(node, exp.Anonymous):
            raise SecurityError(f"Disallowed/unknown function call: {node.name}")

    # 4. Table whitelist check
    tables_used = {t.name for t in tree.find_all(exp.Table)}
    for t in tables_used:
        if t not in ALLOWED_SCHEMA:
            raise SecurityError(f"Table not whitelisted: {t}")

    # 5. Column whitelist check
    for col in tree.find_all(exp.Column):
        table_name = col.table
        col_name = col.name
        if table_name and table_name in ALLOWED_SCHEMA:
            if col_name not in ALLOWED_SCHEMA[table_name]:
                raise SecurityError(f"Column not whitelisted: {table_name}.{col_name}")
        elif not table_name:
            if not any(col_name in ALLOWED_SCHEMA[t] for t in tables_used if t in ALLOWED_SCHEMA):
                raise SecurityError(f"Unqualified column not recognized as safe: {col_name}")

    # 5.5. Reject any explicit merchant_id FILTER written by the AI itself -
    # scoping is applied automatically in step 6. This only checks the WHERE
    # clause (and any nested conditions within it) - merchant_id is still
    # allowed to appear as a normal SELECTed output column.
    where_clause = tree.args.get("where")
    if where_clause is not None:
        for col in where_clause.find_all(exp.Column):
            if col.name == "merchant_id":
                raise SecurityError(
                    "Query must not explicitly filter by merchant_id - scoping is applied automatically."
                )

    # 6. Force-inject merchant scope, parenthesizing existing WHERE to avoid OR-bypass
    scope_filter = sqlglot.condition(f"merchant_id = '{merchant_id}'")
    existing_where = tree.args.get("where")

    if existing_where is not None:
        wrapped_existing = exp.Paren(this=existing_where.this)
        new_condition = exp.And(this=wrapped_existing, expression=scope_filter)
    else:
        new_condition = scope_filter

    tree.set("where", exp.Where(this=new_condition))

    return tree.sql(dialect=dialect)


def execute_safe_query(sql: str, merchant_id: str) -> list[dict]:
    """
    Validates and rewrites the SQL, then actually executes it
    against the real database, returning results as a list of dicts.
    """
    safe_sql = validate_and_rewrite(sql, merchant_id)

    db = SessionLocal()
    try:
        result = db.execute(text(safe_sql))
        rows = result.fetchall()
        columns = result.keys()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        db.close()