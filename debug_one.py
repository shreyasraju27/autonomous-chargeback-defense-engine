from app.agents import evidence_collector_agent, risk_analyst_agent
import json

result = evidence_collector_agent("eval_strong_001", "acc_CFvOKjkTwf3GQy")
print("EVIDENCE:")
print(json.dumps(result, indent=2))

print()
analysis = risk_analyst_agent(result)
print("RISK ANALYSIS:")
print(json.dumps(analysis, indent=2))