from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

from app.agents import evidence_collector_agent, risk_analyst_agent, dossier_writer_agent


class DisputeState(TypedDict):
    order_id: str
    merchant_id: str
    evidence_result: Optional[dict]
    risk_analysis: Optional[dict]
    dossier: Optional[dict]
    status: str


def evidence_node(state: DisputeState) -> DisputeState:
    print(f"[Evidence Collector] Gathering evidence for {state['order_id']}...")
    result = evidence_collector_agent(state["order_id"], state["merchant_id"])
    return {**state, "evidence_result": result, "status": "EVIDENCE_COLLECTED"}


def risk_node(state: DisputeState) -> DisputeState:
    print(f"[Risk Analyst] Analyzing evidence for {state['order_id']}...")
    analysis = risk_analyst_agent(state["evidence_result"])
    return {**state, "risk_analysis": analysis, "status": "RISK_ANALYZED"}


def dossier_node(state: DisputeState) -> DisputeState:
    print(f"[Dossier Writer] Writing summary for {state['order_id']}...")
    dossier = dossier_writer_agent(state["evidence_result"], state["risk_analysis"])
    return {**state, "dossier": dossier, "status": "PENDING_HUMAN_APPROVAL"}


def finalize_node(state: DisputeState) -> DisputeState:
    print(f"[System] Dispute {state['order_id']} approved and finalized.")
    return {**state, "status": "APPROVED_READY_FOR_SUBMISSION"}


def build_graph():
    graph = StateGraph(DisputeState)

    graph.add_node("evidence_collector", evidence_node)
    graph.add_node("risk_analyst", risk_node)
    graph.add_node("dossier_writer", dossier_node)
    graph.add_node("finalize", finalize_node)

    graph.set_entry_point("evidence_collector")
    graph.add_edge("evidence_collector", "risk_analyst")
    graph.add_edge("risk_analyst", "dossier_writer")
    graph.add_edge("dossier_writer", "finalize")
    graph.add_edge("finalize", END)

    conn = sqlite3.connect("dispute_graph_checkpoints.db", check_same_thread=False)
    checkpointer = SqliteSaver(conn)

    compiled = graph.compile(checkpointer=checkpointer, interrupt_after=["dossier_writer"])
    return compiled