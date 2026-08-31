import streamlit as st
import uuid
from app.graph import build_graph
from app.pdf_generator import generate_dispute_pdf

st.set_page_config(
    page_title="Autonomous Chargeback Defense Engine",
    page_icon="C",
    layout="wide",
)

st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 18px;
    }
    h1 {
        font-size: 2.6rem !important;
    }
    h3 {
        font-size: 1.5rem !important;
    }
    .stButton button {
        font-size: 1.1rem !important;
        padding: 0.6rem 1rem !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 1rem !important;
    }
    .stTextInput input {
        font-size: 1.05rem !important;
    }
    p, li, .stMarkdown {
        font-size: 1.05rem !important;
    }
</style>
""", unsafe_allow_html=True)

STATUS_DISPLAY = {
    "NEW": ("New", ""),
    "EVIDENCE_COLLECTED": ("Collecting Evidence", ""),
    "RISK_ANALYZED": ("Analyzing Risk", ""),
    "PENDING_HUMAN_APPROVAL": ("Pending Approval", ""),
    "APPROVED_READY_FOR_SUBMISSION": ("Approved", ""),
}


@st.cache_resource
def get_graph():
    return build_graph()


graph = get_graph()

if "disputes" not in st.session_state:
    st.session_state.disputes = {}

# ---------------- Header ----------------
st.title("Autonomous Chargeback Defense Engine")
st.caption("Multi-agent evidence collection · AST-guarded SQL access · Human-in-the-loop approval")
st.divider()

# ---------------- Layout: two columns instead of sidebar ----------------
left, right = st.columns([1, 2.2], gap="large")

with left:
    st.subheader("Trigger Dispute")
    order_id_input = st.text_input("Order ID", value="", placeholder="Enter order_id")
    merchant_id_input = st.text_input("Merchant ID", value="", placeholder="Enter merchant_id")

    if st.button("Trigger New Dispute", type="primary", use_container_width=True):
        if not order_id_input or not merchant_id_input:
            st.warning("Please enter both an Order ID and a Merchant ID.")
        else:
            thread_id = str(uuid.uuid4())
            config = {"configurable": {"thread_id": thread_id}}
            initial_state = {
                "order_id": order_id_input,
                "merchant_id": merchant_id_input,
                "evidence_result": None,
                "risk_analysis": None,
                "dossier": None,
                "status": "NEW",
            }
            with st.spinner("Running agent pipeline..."):
                result = graph.invoke(initial_state, config=config)

            st.session_state.disputes[thread_id] = {
                "order_id": order_id_input,
                "merchant_id": merchant_id_input,
                "config": config,
                "result": result,
            }
            st.session_state.active_thread = thread_id
            st.rerun()

    st.divider()
    st.subheader("Disputes")

    if not st.session_state.disputes:
        st.caption("No disputes yet. Trigger one above.")
    else:
        for tid, d in st.session_state.disputes.items():
            status = d["result"].get("status")
            label, _ = STATUS_DISPLAY.get(status, (status, ""))
            is_active = st.session_state.get("active_thread") == tid
            btn_label = f"{'> ' if is_active else ''}{d['order_id']}  -  {label}"
            if st.button(btn_label, key=f"select_{tid}", use_container_width=True):
                st.session_state.active_thread = tid
                st.rerun()

# ---------------- Main content ----------------
with right:
    active_thread = st.session_state.get("active_thread")

    if not active_thread or active_thread not in st.session_state.disputes:
        st.info("No dispute selected. Trigger a new dispute on the left to see the agent pipeline run live.")
    else:
        dispute = st.session_state.disputes[active_thread]
        result = dispute["result"]
        config = dispute["config"]
        status = result.get("status")
        label, _ = STATUS_DISPLAY.get(status, (status, ""))

        # --- Overview ---
        st.subheader(result["order_id"])
        c1, c2, c3 = st.columns(3)
        c1.metric("Merchant", result["merchant_id"])
        c2.metric("Status", label)

        risk_analysis = result.get("risk_analysis")
        if risk_analysis:
            c3.metric("Risk Score", f"{risk_analysis.get('risk_score', 'N/A')}/100")

        st.divider()

        # --- Evidence ---
        evidence_result = result.get("evidence_result") or {}
        evidence_items = evidence_result.get("evidence", [])
        blocked = evidence_result.get("blocked_attempts", [])

        if evidence_items or blocked:
            with st.container(border=True):
                st.markdown("### Evidence Collector")
                for item in evidence_items:
                    st.code(item["source_query"], language="sql")
                    st.json(item["data"])

                if blocked:
                    st.markdown("**Blocked by Security Guardrail**")
                    for b in blocked:
                        st.error(f"`{b['query']}`\n\n{b['reason']}")

        # --- Risk analysis ---
        if risk_analysis:
            with st.container(border=True):
                st.markdown("### Risk Analyst")
                rc1, rc2 = st.columns(2)
                rc1.metric("Recommendation", risk_analysis.get("recommendation", "N/A"))
                rc2.metric("Reason Code", risk_analysis.get("reason_code_response", "N/A"))

                if risk_analysis.get("evidence_gaps"):
                    st.warning("**Evidence Gaps:**\n" + "\n".join(f"- {g}" for g in risk_analysis["evidence_gaps"]))

                if risk_analysis.get("injection_attempt_detected"):
                    st.error("Prompt injection attempt detected in evidence data (safely ignored)")

        # --- Dossier ---
        dossier = result.get("dossier")
        if dossier:
            with st.container(border=True):
                st.markdown("### Dossier Writer — Draft Summary")
                st.write(dossier.get("summary"))

        st.divider()

        # --- Approval ---
        if status == "PENDING_HUMAN_APPROVAL":
            st.warning("**Awaiting Human Approval** — review the evidence and dossier above, then approve to finalize.")
            if st.button("Approve Dispute", type="primary"):
                with st.spinner("Resuming graph..."):
                    final_result = graph.invoke(None, config=config)
                st.session_state.disputes[active_thread]["result"] = final_result
                st.rerun()

        # --- PDF download ---
        if status == "APPROVED_READY_FOR_SUBMISSION":
            st.success("**Approved & Finalized**")
            pdf_path = generate_dispute_pdf(result)
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF Dossier",
                    data=f,
                    file_name=f"dispute_{result['order_id']}.pdf",
                    mime="application/pdf",
                    type="primary",
                )