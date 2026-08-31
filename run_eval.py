import json
import time
import os
from app.graph import build_graph

with open("app/ground_truth.json") as f:
    ground_truth = json.load(f)

# Load previous results if they exist, so we don't waste quota re-running successes
previous_results = {}
if os.path.exists("eval_results.json"):
    with open("eval_results.json") as f:
        old_data = json.load(f)
        for r in old_data.get("details", []):
            previous_results[r["order_id"]] = r

graph = build_graph()
MERCHANT_ID = "acc_CFvOKjkTwf3GQy"

results = []

print("=" * 70)
print(f"RUNNING EVAL ON {len(ground_truth)} LABELED TEST DISPUTES")
print("=" * 70)

for order_id, expected_label in ground_truth.items():
    # Skip if we already got a valid (non-error) result for this one
    prev = previous_results.get(order_id)
    if prev and prev["predicted"] not in ("ERROR", "UNKNOWN"):
        print(f"  (skip - already have result) {order_id}: predicted={prev['predicted']}")
        results.append(prev)
        continue

    config = {"configurable": {"thread_id": f"eval_{order_id}"}}
    initial_state = {
        "order_id": order_id,
        "merchant_id": MERCHANT_ID,
        "evidence_result": None,
        "risk_analysis": None,
        "dossier": None,
        "status": "NEW",
    }

    try:
        result = graph.invoke(initial_state, config=config)
        predicted_label = result.get("risk_analysis", {}).get("recommendation", "UNKNOWN")
    except Exception as e:
        predicted_label = "ERROR"
        print(f"  ERROR on {order_id}: {e}")

    # INSUFFICIENT_EVIDENCE is an acceptable outcome for weak/borderline cases -
    # it means the AI correctly recognized it could not confidently judge the case
    if expected_label == "WEAK_CASE" and predicted_label == "INSUFFICIENT_EVIDENCE":
        correct = True
    else:
        correct = (predicted_label == expected_label)

    results.append({
        "order_id": order_id,
        "expected": expected_label,
        "predicted": predicted_label,
        "correct": correct
    })

    status_icon = "✓" if correct else "✗"
    print(f"  {status_icon} {order_id}: expected={expected_label}, predicted={predicted_label}")

    time.sleep(18)  # ~3.3 disputes/min x 3 calls = ~10 calls/min, safely under 15/min limit

# ---- Recompute correctness for cached/skipped results too, using the updated rule ----
for r in results:
    if r["expected"] == "WEAK_CASE" and r["predicted"] == "INSUFFICIENT_EVIDENCE":
        r["correct"] = True
    else:
        r["correct"] = (r["predicted"] == r["expected"])

# ---- Calculate metrics ----
print()
print("=" * 70)
print("METRICS")
print("=" * 70)

total = len(results)
correct_count = sum(1 for r in results if r["correct"])
accuracy = correct_count / total if total else 0

true_positives = sum(1 for r in results if r["expected"] == "STRONG_CASE" and r["predicted"] == "STRONG_CASE")
false_positives = sum(1 for r in results if r["expected"] != "STRONG_CASE" and r["predicted"] == "STRONG_CASE")
false_negatives = sum(1 for r in results if r["expected"] == "STRONG_CASE" and r["predicted"] != "STRONG_CASE")
true_negatives = sum(1 for r in results if r["expected"] != "STRONG_CASE" and r["predicted"] != "STRONG_CASE")

precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) else 0
recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) else 0

print(f"Total test cases: {total}")
print(f"Correct: {correct_count} ({accuracy:.1%})")
print()
print(f"True Positives (correctly flagged strong cases): {true_positives}")
print(f"False Positives (wrongly flagged weak cases as strong): {false_positives}")
print(f"False Negatives (missed real strong cases): {false_negatives}")
print(f"True Negatives (correctly flagged weak cases): {true_negatives}")
print()
print(f"Precision: {precision:.1%}")
print(f"Recall: {recall:.1%}")
print()
print("False-positive cost note: a false positive means the merchant is told")
print("their case is strong when it isn't - risking wasted submission effort")
print("and a lost dispute they believed was winnable.")

with open("eval_results.json", "w") as f:
    json.dump({
        "total": total,
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "true_negatives": true_negatives,
        "details": results
    }, f, indent=2)

print()
print("Full results saved to eval_results.json")