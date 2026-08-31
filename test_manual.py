from app.guardrail import validate_and_rewrite, SecurityError

print("=" * 60)
print("TEST 1: A normal, safe query")
print("=" * 60)
sql = "SELECT order_id, amount, status FROM orders WHERE order_id = 'order_123'"
try:
    result = validate_and_rewrite(sql, merchant_id="acc_CFvOKjkTwf3GQy")
    print("ALLOWED. Rewritten query:")
    print(result)
except SecurityError as e:
    print("BLOCKED:", e)

print()
print("=" * 60)
print("TEST 2: Attempted DROP TABLE (should be blocked)")
print("=" * 60)
sql = "SELECT order_id FROM orders; DROP TABLE orders;"
try:
    result = validate_and_rewrite(sql, merchant_id="acc_CFvOKjkTwf3GQy")
    print("ALLOWED (THIS WOULD BE BAD):", result)
except SecurityError as e:
    print("BLOCKED (correct):", e)

print()
print("=" * 60)
print("TEST 3: Wildcard SELECT * (should be blocked)")
print("=" * 60)
sql = "SELECT * FROM orders"
try:
    result = validate_and_rewrite(sql, merchant_id="acc_CFvOKjkTwf3GQy")
    print("ALLOWED (THIS WOULD BE BAD):", result)
except SecurityError as e:
    print("BLOCKED (correct):", e)

print()
print("=" * 60)
print("TEST 4: Table not in whitelist (should be blocked)")
print("=" * 60)
sql = "SELECT id FROM users"
try:
    result = validate_and_rewrite(sql, merchant_id="acc_CFvOKjkTwf3GQy")
    print("ALLOWED (THIS WOULD BE BAD):", result)
except SecurityError as e:
    print("BLOCKED (correct):", e)