from app.graph import build_graph
import json

graph = build_graph()

config = {"configurable": {"thread_id": "dispute_test_001"}}

initial_state = {
    "order_id": "order_EFtkA6f5jdkfud",
    "merchant_id": "acc_CFvOKjkTwf3GQy",
    "evidence_result": None,
    "risk_analysis": None,
    "dossier": None,
    "status": "NEW"
}

print("=" * 60)
print("STARTING GRAPH RUN")
print("=" * 60)

result = graph.invoke(initial_state, config=config)

print()
print("=" * 60)
print("GRAPH PAUSED - current state:")
print("=" * 60)
print(json.dumps(result, indent=2, default=str))

print()
print("Status:", result.get("status"))
print()
print("If status is PENDING_HUMAN_APPROVAL, the graph correctly")
print("stopped and is waiting for a human to approve before continuing.")

print()
print("=" * 60)
print("SIMULATING HUMAN APPROVAL - resuming the graph")
print("=" * 60)

final_result = graph.invoke(None, config=config)

print()
print("Final status:", final_result.get("status"))
print()
print("Final dossier summary:")
print(final_result["dossier"]["summary"])