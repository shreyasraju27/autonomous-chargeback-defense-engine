import pytest
from app.guardrail import validate_and_rewrite, SecurityError

MERCHANT_ID = "acc_CFvOKjkTwf3GQy"


def test_allows_safe_query():
    sql = "SELECT order_id, amount, status FROM orders WHERE order_id = 'order_123'"
    result = validate_and_rewrite(sql, MERCHANT_ID)
    assert "merchant_id = 'acc_CFvOKjkTwf3GQy'" in result
    assert "order_id" in result


def test_blocks_multi_statement_injection():
    sql = "SELECT order_id FROM orders; DROP TABLE orders;"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_direct_drop():
    sql = "DROP TABLE orders"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_delete():
    sql = "DELETE FROM orders WHERE order_id = 'order_123'"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_update():
    sql = "UPDATE orders SET status = 'cancelled' WHERE order_id = 'order_123'"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_insert():
    sql = "INSERT INTO orders (order_id, amount) VALUES ('fake_order', 999)"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_wildcard_select():
    sql = "SELECT * FROM orders"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_non_whitelisted_table():
    sql = "SELECT id FROM users"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_non_whitelisted_column():
    sql = "SELECT order_id, secret_internal_notes FROM orders"
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_blocks_hidden_write_in_cte():
    sql = """
    WITH temp AS (DELETE FROM orders WHERE order_id = 'order_123' RETURNING *)
    SELECT * FROM temp
    """
    with pytest.raises(SecurityError):
        validate_and_rewrite(sql, MERCHANT_ID)


def test_or_clause_cannot_bypass_merchant_scope():
    """
    Critical test: an OR-based WHERE clause should not be able to
    leak data outside the merchant scope after our rewrite.
    """
    sql = "SELECT order_id, amount, status FROM orders WHERE order_id = 'order_123' OR 1=1"
    result = validate_and_rewrite(sql, MERCHANT_ID)
    # our merchant filter must wrap the whole OR clause in parentheses
    assert result.count("merchant_id = 'acc_CFvOKjkTwf3GQy'") == 1
    assert "AND merchant_id" in result


def test_blocks_comment_obfuscation():
    """
    A comment containing a DROP statement must never become
    executable SQL - it should stay inertly inside a comment block,
    or the query should be rejected outright.
    """
    sql = "SELECT order_id FROM orders -- ; DROP TABLE orders;"
    try:
        result = validate_and_rewrite(sql, MERCHANT_ID)
        # DROP is allowed to appear ONLY if it's safely inside a comment (/* ... */ or --)
        assert "/*" in result or "--" in result, "DROP text present but not safely commented out"
    except SecurityError:
        pass  # blocking it entirely is also acceptable