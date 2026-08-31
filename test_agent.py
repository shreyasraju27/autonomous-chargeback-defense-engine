from app.agents import evidence_collector_agent
import json

result = evidence_collector_agent(
    order_id="order_EFtkA6f5jdkfud",
    merchant_id="acc_CFvOKjkTwf3GQy"
)

print(json.dumps(result, indent=2))

print("\n\n--- Testing weak-evidence order ---\n")
result2 = evidence_collector_agent(
    order_id="order_weak001",
    merchant_id="acc_CFvOKjkTwf3GQy"
)
print(json.dumps(result2, indent=2))

from app.agents import risk_analyst_agent

print("\n\n--- Risk analysis: strong evidence case ---\n")
analysis1 = risk_analyst_agent(result)
print(json.dumps(analysis1, indent=2))

print("\n\n--- Risk analysis: weak evidence case (with injection attempt) ---\n")
analysis2 = risk_analyst_agent(result2)
print(json.dumps(analysis2, indent=2))

from app.agents import dossier_writer_agent

print("\n\n--- Dossier: strong evidence case ---\n")
dossier1 = dossier_writer_agent(result, analysis1)
print(json.dumps(dossier1, indent=2))

print("\n\n--- Dossier: weak evidence case ---\n")
dossier2 = dossier_writer_agent(result2, analysis2)
print(json.dumps(dossier2, indent=2))