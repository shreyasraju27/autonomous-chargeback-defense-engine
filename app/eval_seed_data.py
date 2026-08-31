from app.database import SessionLocal, engine, Base
from app.models import Order, DeliveryLog, ChatMessage

Base.metadata.create_all(bind=engine)

db = SessionLocal()
MERCHANT_ID = "acc_CFvOKjkTwf3GQy"

# Clear only eval-prefixed test data (safe to re-run)
db.query(Order).filter(Order.order_id.like("eval_%")).delete(synchronize_session=False)
db.query(DeliveryLog).filter(DeliveryLog.order_id.like("eval_%")).delete(synchronize_session=False)
db.query(ChatMessage).filter(ChatMessage.order_id.like("eval_%")).delete(synchronize_session=False)

orders = []
delivery_logs = []
chat_messages = []

# ---- STRONG CASES (should win) - delivery + positive chat confirmation ----
strong_cases = [f"eval_strong_{i:03d}" for i in range(1, 8)]  # 7 strong cases
for i, oid in enumerate(strong_cases):
    orders.append(Order(order_id=oid, merchant_id=MERCHANT_ID, amount=10000 + i * 500,
                         status="delivered", created_at="2026-08-01"))
    delivery_logs.append(DeliveryLog(log_id=f"log_{oid}", merchant_id=MERCHANT_ID, order_id=oid,
                                      delivered_at="2026-08-04", signature_ref=f"sig_{oid}"))
    chat_messages.append(ChatMessage(msg_id=f"msg_{oid}", merchant_id=MERCHANT_ID, order_id=oid,
                                      sender="customer", body_masked="Got it, thank you!", sent_at="2026-08-04"))

# ---- WEAK CASES (should lose) - no delivery proof, no confirmation ----
weak_cases = [f"eval_weak_{i:03d}" for i in range(1, 8)]  # 7 weak cases
for i, oid in enumerate(weak_cases):
    orders.append(Order(order_id=oid, merchant_id=MERCHANT_ID, amount=8000 + i * 300,
                         status="shipped", created_at="2026-08-05"))
    # deliberately no delivery log, no chat message for most

# ---- BORDERLINE CASES (shipped, no delivery log, but a neutral/ambiguous chat) ----
borderline_cases = [f"eval_border_{i:03d}" for i in range(1, 5)]  # 4 borderline cases
for i, oid in enumerate(borderline_cases):
    orders.append(Order(order_id=oid, merchant_id=MERCHANT_ID, amount=5000 + i * 400,
                         status="shipped", created_at="2026-08-06"))
    chat_messages.append(ChatMessage(msg_id=f"msg_{oid}", merchant_id=MERCHANT_ID, order_id=oid,
                                      sender="customer", body_masked="Is my order coming soon?", sent_at="2026-08-07"))

db.add_all(orders)
db.add_all(delivery_logs)
db.add_all(chat_messages)
db.commit()

# ---- Ground truth labels ----
ground_truth = {}
for oid in strong_cases:
    ground_truth[oid] = "STRONG_CASE"
for oid in weak_cases:
    ground_truth[oid] = "WEAK_CASE"
for oid in borderline_cases:
    ground_truth[oid] = "WEAK_CASE"  # no delivery proof = should not be scored as strong

import json
with open("app/ground_truth.json", "w") as f:
    json.dump(ground_truth, f, indent=2)

print(f"Seeded {len(strong_cases)} strong, {len(weak_cases)} weak, {len(borderline_cases)} borderline cases.")
print(f"Total: {len(ground_truth)} labeled test disputes.")
print("Ground truth saved to app/ground_truth.json")

db.close()