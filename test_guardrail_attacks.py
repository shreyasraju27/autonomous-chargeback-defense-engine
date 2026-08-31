from app.guardrail import execute_safe_query, SecurityError

# These should all raise SecurityError - genuinely malicious/disallowed
should_block = [
    "DELETE FROM orders WHERE order_id = 'order_EFtkA6f5jdkfud'",
    "DROP TABLE orders",
    "UPDATE orders SET status = 'refunded' WHERE order_id = 'order_EFtkA6f5jdkfud'",
    "SELECT * FROM orders",
    "SELECT order_id, amount FROM orders WHERE merchant_id = 'acc_SOME_OTHER_MERCHANT'",
]

merchant_id = "acc_CFvOKjkTwf3GQy"

print("=== Queries that should be BLOCKED outright ===")
for q in should_block:
    try:
        execute_safe_query(q, merchant_id)
        print(f"❌ FAILED TO BLOCK: {q}")
    except SecurityError as e:
        print(f"✓ Blocked: {q[:55]}... - {e}")

print()
print("=== Unscoped-but-benign query - should be auto-scoped, not blocked ===")
q = "SELECT order_id FROM orders"
try:
    results = execute_safe_query(q, merchant_id)
    print(f"✓ Executed safely, auto-scoped. Returned {len(results)} row(s): {results}")
except SecurityError as e:
    print(f"Blocked (also acceptable): {e}")