# Autonomous Chargeback Defense Engine

An autonomous, multi-agent AI system that automatically gathers evidence for payment disputes and chargebacks 

## The Problem

When a customer disputes a payment, the merchant's bank pulls the funds back immediately and gives the merchant a 7-14 day window to submit counter-evidence. Gathering that evidence (order records, delivery confirmation, chat history) manually takes ~45 minutes per case across scattered systems, and small merchants routinely lose legitimate revenue simply because the process is too slow and fragmented.

Generic AI automation isn't safe for this task out of the box - it touches sensitive customer data and real financial outcomes, and carries real risk if the AI hallucinates a fact, leaks cross-merchant data, or executes an unsafe database operation.

## What This Is

A system that automates the evidence-gathering and case-assessment work, while making two things provable, not just claimed:

1. The AI can never access data outside its scope. Every database query it generates is parsed, validated, and rewritten by an AST-based security layer before execution - never trusted as written.
2. The AI can never submit anything without a human. The workflow is a checkpointed state machine with a structural interrupt - no code path reaches a final, submittable state without explicit human approval.

## Security Guarantees

- AST-based SQL guardrail (sqlglot) - blocks writes, wildcards, non-whitelisted tables/columns, multi-statement injection, and forces merchant scoping automatically
- Tier A: 12 hand-crafted adversarial SQL tests - all passing
- Tier B: live-agent adversarial testing - AI never generates malicious SQL even under direct manipulation
- Prompt-injection resistance - verified with planted injection attempts in evidence data
- Human-in-the-loop approval gate - structurally unbypassable, checkpointed, survives restart

## Evaluation Results

Tested against 18 labeled synthetic disputes with known ground-truth outcomes:

- Accuracy: 100% (18/18)
- Precision: 100%
- Recall: 100%
- False Positives: 0

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Agent orchestration: LangGraph (with SQLite checkpointing)
- AI: Google Gemini
- SQL security: sqlglot (AST parsing and rewriting)
- PDF generation: ReportLab
- Dashboard: Streamlit

## Setup

\\\ash
pip install -r requirements.txt
python -m app.seed_data
uvicorn app.main:app --reload
streamlit run streamlit_app.py
\\\

## Why This Approach

Chargeback automation already exists as a commercial product category. Our contribution isn't the underlying business idea - it's a security-first architecture pattern for deploying AI agents in financial workflows: provably scoped data access, auditable and source-cited reasoning, and a human approval gate that cannot be bypassed.
