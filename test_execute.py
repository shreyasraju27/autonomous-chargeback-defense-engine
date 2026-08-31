from app.guardrail import execute_safe_query

print("Querying strong-evidence order:")
results = execute_safe_query(
    "SELECT order_id, amount, status FROM orders WHERE order_id = 'order_EFtkA6f5jdkfud'",
    merchant_id="acc_CFvOKjkTwf3GQy"
)
print(results)

print()
print("Querying delivery logs for that order:")
results = execute_safe_query(
    "SELECT log_id, delivered_at, signature_ref FROM delivery_logs WHERE order_id = 'order_EFtkA6f5jdkfud'",
    merchant_id="acc_CFvOKjkTwf3GQy"
)
print(results)

print()
print("Querying the weak-evidence order (should show no delivery log exists):")
results = execute_safe_query(
    "SELECT order_id, amount, status FROM orders WHERE order_id = 'order_weak001'",
    merchant_id="acc_CFvOKjkTwf3GQy"
)
print(results)