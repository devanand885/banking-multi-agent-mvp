"""
frontend/streamlit_app.py
==========================
Multi-Agent Banking Assistant — Streamlit Dashboard

A polished, professional UI for the banking AI/ML MVP.
All data displayed is simulated for demonstration purposes only.
"""
from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict, List, Optional

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

# ──────────────────────────────── Page Config ─────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Banking Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Multi-Agent Banking Assistant MVP — Wrench Wise EduTech AI/ML Internship",
    },
)

# ──────────────────────────────── Session State ───────────────────────────────
if "messages" not in st.session_state:
    st.session_state["messages"] = []
if "selected_customer" not in st.session_state:
    st.session_state["selected_customer"] = "CUST001"
if "last_response" not in st.session_state:
    st.session_state["last_response"] = None

# ──────────────────────────────── CSS Styling ─────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* { font-family: 'Inter', sans-serif; }

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 50%, #0a1628 100%);
}

/* Header */
.main-header {
    background: linear-gradient(90deg, #1a237e 0%, #283593 50%, #1565c0 100%);
    padding: 1.5rem 2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    border: 1px solid rgba(100, 160, 255, 0.2);
    box-shadow: 0 8px 32px rgba(0, 100, 255, 0.15);
}

.main-header h1 {
    color: #ffffff !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
    margin: 0 !important;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

.main-header p {
    color: rgba(200, 220, 255, 0.85) !important;
    font-size: 0.9rem !important;
    margin: 0.3rem 0 0 0 !important;
}

/* Chat messages */
.chat-user {
    background: linear-gradient(135deg, #1565c0, #1976d2);
    color: white;
    padding: 0.8rem 1.2rem;
    border-radius: 18px 18px 4px 18px;
    margin: 0.5rem 0;
    max-width: 80%;
    margin-left: auto;
    box-shadow: 0 4px 12px rgba(21, 101, 192, 0.3);
}

.chat-assistant {
    background: linear-gradient(135deg, #1a1f3e, #242a50);
    color: #e8eaf6;
    padding: 0.8rem 1.2rem;
    border-radius: 18px 18px 18px 4px;
    margin: 0.5rem 0;
    max-width: 85%;
    border: 1px solid rgba(100, 120, 255, 0.2);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* Cards */
.metric-card {
    background: linear-gradient(135deg, #1a1f3e, #1e2642);
    border: 1px solid rgba(100, 120, 255, 0.25);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    margin: 0.4rem 0;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(0, 0, 0, 0.3);
}

.metric-value {
    font-size: 1.6rem;
    font-weight: 700;
    color: #64b5f6;
}

.metric-label {
    font-size: 0.8rem;
    color: rgba(180, 200, 255, 0.7);
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

/* Agent trace */
.agent-trace {
    background: linear-gradient(135deg, #0d1b2e, #111f35);
    border: 1px solid rgba(0, 200, 150, 0.2);
    border-left: 3px solid #00c896;
    border-radius: 8px;
    padding: 0.8rem 1rem;
    margin: 0.3rem 0;
    font-family: 'Courier New', monospace;
    font-size: 0.82rem;
    color: #80cbc4;
}

/* Risk badges */
.risk-low    { background: rgba(76, 175, 80, 0.2);  color: #81c784; border: 1px solid #81c784;  border-radius: 20px; padding: 2px 10px; font-size: 0.8rem; font-weight: 600; }
.risk-medium { background: rgba(255, 193, 7, 0.2);  color: #ffd54f; border: 1px solid #ffd54f;  border-radius: 20px; padding: 2px 10px; font-size: 0.8rem; font-weight: 600; }
.risk-high   { background: rgba(244, 67, 54, 0.2);  color: #ef9a9a; border: 1px solid #ef9a9a;  border-radius: 20px; padding: 2px 10px; font-size: 0.8rem; font-weight: 600; }
.risk-critical { background: rgba(156, 39, 176, 0.3); color: #ce93d8; border: 1px solid #ce93d8; border-radius: 20px; padding: 2px 10px; font-size: 0.8rem; font-weight: 600; }

/* Status badges */
.status-badge {
    display: inline-block;
    padding: 3px 12px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.03em;
}

/* Disclaimer */
.disclaimer-box {
    background: linear-gradient(135deg, rgba(255, 152, 0, 0.1), rgba(255, 193, 7, 0.05));
    border: 1px solid rgba(255, 193, 7, 0.3);
    border-radius: 10px;
    padding: 0.7rem 1rem;
    color: #ffc107;
    font-size: 0.8rem;
    margin: 0.5rem 0;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0e1a 0%, #0d1b2a 100%);
    border-right: 1px solid rgba(100, 120, 255, 0.1);
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1565c0, #1976d2);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 1.2rem;
    font-weight: 600;
    transition: all 0.2s ease;
    box-shadow: 0 4px 12px rgba(21, 101, 192, 0.3);
}

.stButton > button:hover {
    background: linear-gradient(135deg, #1976d2, #2196f3);
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(33, 150, 243, 0.4);
}

/* Text input */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(100, 120, 255, 0.3);
    border-radius: 10px;
    color: white;
}

/* Divider */
.section-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(100, 120, 255, 0.3), transparent);
    margin: 1rem 0;
}

/* Scrollable chat */
.chat-container {
    max-height: 500px;
    overflow-y: auto;
    padding-right: 0.5rem;
}

/* LLM mode indicator */
.llm-badge-mock { background: rgba(255, 193, 7, 0.15); color: #ffd54f; border: 1px solid #ffd54f; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
.llm-badge-real { background: rgba(76, 175, 80, 0.15); color: #81c784; border: 1px solid #81c784; border-radius: 20px; padding: 2px 10px; font-size: 0.75rem; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────── Session State ───────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "selected_customer" not in st.session_state:
    st.session_state.selected_customer = "CUST001"
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# ──────────────────────────────── Backend Helpers ─────────────────────────────

def call_orchestrator(message: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
    """Call the orchestrator directly (in-process — no HTTP needed)."""
    from backend.agents.orchestrator import orchestrator
    return orchestrator.process(message=message, customer_id=customer_id)


def get_customer_data(customer_id: str) -> Dict[str, Any]:
    """Fetch customer data directly from tools."""
    from backend.tools.banking_tools import get_customer_profile, get_customer_accounts, get_customer_transactions
    profile = get_customer_profile(customer_id)
    accounts = get_customer_accounts(customer_id)
    transactions = get_customer_transactions(customer_id, limit=5)
    return {
        "profile": profile.get("customer", {}),
        "accounts": accounts.get("accounts", []),
        "total_balance": accounts.get("total_balance", 0),
        "transactions": transactions.get("transactions", []),
    }


# ──────────────────────────────── Sample Prompts ──────────────────────────────

SAMPLE_PROMPTS = [
    ("💰 Account Balance", "Show the account balance and recent transactions for customer {cid}"),
    ("🔍 Fraud Check", "Check customer CUST002 for suspicious transactions and explain the risk"),
    ("📋 Loan Eligibility", "Check whether customer CUST003 is eligible for a loan of 500000"),
    ("🧮 EMI Calculator", "Calculate the monthly EMI for a loan of 300000 at 10 percent interest for 36 months"),
    ("✅ KYC Verification", "Check the KYC status of customer {cid} and list any missing details"),
    ("🔄 Combined Request", "Show CUST001's balance, check for fraud, and summarise outstanding loans"),
]

# ──────────────────────────────── Sidebar ─────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:1rem 0 0.5rem;'>
            <div style='font-size:2.5rem;'>🏦</div>
            <div style='color:#64b5f6; font-weight:700; font-size:1.1rem;'>Banking Assistant</div>
            <div style='color:rgba(180,200,255,0.6); font-size:0.75rem;'>AI/ML MVP Demo</div>
        </div>
        <hr style='border-color:rgba(100,120,255,0.2);'>
        """, unsafe_allow_html=True)

        # Customer selector
        st.markdown("**👤 Customer Profile**")
        customer_options = {
            "CUST001 — Arjun Sharma": "CUST001",
            "CUST002 — Priya Verma": "CUST002",
            "CUST003 — Rahul Gupta": "CUST003",
            "CUST004 — Sneha Patel": "CUST004",
            "CUST005 — Vikram Singh": "CUST005",
        }
        selected_label = st.selectbox(
            "Select customer",
            list(customer_options.keys()),
            index=0,
            label_visibility="collapsed",
        )
        st.session_state.selected_customer = customer_options[selected_label]
        cid = st.session_state.selected_customer

        # Customer profile card
        try:
            cdata = get_customer_data(cid)
            p = cdata["profile"]
            if p:
                credit = p.get("credit_score", "N/A")
                cs_color = "#81c784" if isinstance(credit, int) and credit >= 700 else \
                           "#ffd54f" if isinstance(credit, int) and credit >= 600 else "#ef9a9a"
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='font-weight:600; color:#90caf9;'>{p.get('full_name','N/A')}</div>
                    <div style='color:rgba(180,200,255,0.7); font-size:0.8rem;'>{p.get('email','')}</div>
                    <div style='color:rgba(180,200,255,0.7); font-size:0.8rem;'>📍 {p.get('city','N/A')}</div>
                    <div style='margin-top:0.5rem;'>
                        <span style='color:#ffd54f; font-size:0.8rem;'>💼 {(p.get('employment_status') or 'N/A').replace('_',' ').title()}</span>
                    </div>
                    <div style='margin-top:0.3rem;'>
                        <span style='color:{cs_color}; font-weight:700;'>⭐ Credit Score: {credit}</span>
                    </div>
                    <div style='color:#64b5f6; font-weight:700; font-size:1.1rem; margin-top:0.5rem;'>
                        ₹{cdata['total_balance']:,.2f}
                    </div>
                    <div style='color:rgba(180,200,255,0.6); font-size:0.75rem;'>Total Balance ({len(cdata['accounts'])} account{'s' if len(cdata['accounts'])!=1 else ''})</div>
                </div>
                """, unsafe_allow_html=True)

                # Account details
                if cdata["accounts"]:
                    st.markdown("**🏧 Accounts**")
                    for acc in cdata["accounts"]:
                        status_color = "#81c784" if acc["status"] == "active" else "#ef9a9a"
                        st.markdown(f"""
                        <div style='background:rgba(255,255,255,0.04); border:1px solid rgba(100,120,255,0.15);
                                    border-radius:8px; padding:0.5rem 0.8rem; margin:0.3rem 0;'>
                            <span style='color:{status_color}; font-size:0.7rem;'>●</span>
                            <span style='color:#e3f2fd; font-size:0.82rem; font-weight:500;'>
                                {acc['account_type'].replace('_',' ').title()}
                            </span>
                            <div style='color:#64b5f6; font-weight:600;'>₹{acc['balance']:,.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"Could not load customer data: {e}")

        st.markdown("<hr style='border-color:rgba(100,120,255,0.2);'>", unsafe_allow_html=True)

        # LLM mode
        from backend.config import settings
        mode = settings.effective_llm_provider
        badge_class = "llm-badge-real" if mode != "mock" else "llm-badge-mock"
        badge_text = f"🤖 LLM: {mode.upper()}"
        st.markdown(f"<span class='{badge_class}'>{badge_text}</span>", unsafe_allow_html=True)

        if mode == "mock":
            st.caption("Running in mock mode — add a GEMINI_API_KEY to .env for real LLM responses.")

        st.markdown("<hr style='border-color:rgba(100,120,255,0.2);'>", unsafe_allow_html=True)

        # Clear chat
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_response = None
            st.rerun()

        st.markdown("""
        <div class='disclaimer-box'>
            ⚠️ <strong>Demo Only</strong><br>
            All banking data shown is entirely fictional and simulated.
            No real financial operations are performed.
        </div>
        """, unsafe_allow_html=True)


# ──────────────────────────────── Main Content ────────────────────────────────

def render_header():
    st.markdown("""
    <div class='main-header'>
        <h1>🏦 Multi-Agent Banking Assistant</h1>
        <p>Simulated Banking AI/ML MVP — Wrench Wise EduTech Internship Assignment</p>
        <p style='font-size:0.75rem; opacity:0.6;'>
            Supervisor Agent → Customer Agent | Risk/Fraud Agent | Credit Agent | Compliance Agent
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_sample_prompts():
    """Render clickable sample query buttons."""
    cid = st.session_state.get("selected_customer", "CUST001")
    st.markdown("**💡 Sample Queries** *(click to use)*")
    cols = st.columns(3)
    for i, (label, template) in enumerate(SAMPLE_PROMPTS):
        prompt = template.replace("{cid}", cid)
        if cols[i % 3].button(label, key=f"sample_{i}", use_container_width=True):
            return prompt
    return None


def render_chat():
    """Render the chat history."""
    messages = st.session_state.get("messages", [])
    if messages:
        col_title, col_clear = st.columns([5, 1])
        with col_title:
            st.markdown("**💬 Conversation**")
        with col_clear:
            if st.button("🗑️ Clear", key="clear_chat_btn", use_container_width=True):
                st.session_state.messages = []
                st.session_state.last_response = None
                st.rerun()

        for msg in messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class='chat-user'>
                    <span style='font-size:0.75rem; opacity:0.7;'>👤 You</span><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class='chat-assistant'>
                    <span style='font-size:0.75rem; opacity:0.7;'>🤖 Banking Assistant</span><br>
                    {msg['content']}
                </div>
                """, unsafe_allow_html=True)


def render_response_details(response: Dict[str, Any]):
    """Render the structured response, agent trace, and details."""
    if not response:
        return

    st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

    # ── Response meta info ────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        mode = response.get("llm_mode", "mock")
        badge = "llm-badge-real" if mode != "mock" else "llm-badge-mock"
        st.markdown(f"<span class='{badge}'>🤖 {mode.upper()}</span>", unsafe_allow_html=True)
    with col2:
        duration = response.get("execution_duration_ms", 0)
        st.markdown(f"<span style='color:#90caf9; font-size:0.82rem;'>⏱️ {duration:.0f}ms</span>", unsafe_allow_html=True)
    with col3:
        intent = response.get("intent", "unknown")
        st.markdown(f"<span style='color:#ffd54f; font-size:0.82rem;'>🎯 {intent.replace('_',' ').title()}</span>", unsafe_allow_html=True)
    with col4:
        agents = response.get("agents_invoked", [])
        st.markdown(f"<span style='color:#80cbc4; font-size:0.82rem;'>🤝 {len(agents)} agent(s)</span>", unsafe_allow_html=True)

    # ── Tabs ──────────────────────────────────────────────────────────────
    tab1, tab2, tab3 = st.tabs(["📊 Structured Data", "🔍 Agent Trace", "⚠️ Warnings & Errors"])

    with tab1:
        render_structured_data(response)

    with tab2:
        render_agent_trace(response)

    with tab3:
        warnings = response.get("warnings", [])
        errors = response.get("errors", [])
        if warnings:
            st.warning("\n\n".join(warnings))
        if errors:
            st.error("\n\n".join(errors))
        if not warnings and not errors:
            st.success("✅ No warnings or errors.")


def render_structured_data(response: Dict[str, Any]):
    """Render structured data panels."""
    structured = response.get("structured_data", {})
    agent_results = structured.get("agent_results", [])

    for result in agent_results:
        agent_name = result.get("agent", "unknown")
        data = result.get("data", {})

        if "error" in data:
            st.error(f"**{agent_name}**: {data['error']}")
            continue

        if agent_name == "customer_agent":
            _render_customer_panel(data)
        elif agent_name == "risk_agent":
            _render_risk_panel(data)
        elif agent_name == "credit_agent":
            _render_credit_panel(data)
        elif agent_name == "compliance_agent":
            _render_compliance_panel(data)
        else:
            msg = data.get("message", "")
            if msg:
                st.info(msg)


def _render_customer_panel(data: Dict[str, Any]):
    st.markdown("**👤 Customer & Account Data**")
    customer = data.get("customer", {})
    accounts = data.get("accounts", [])
    transactions = data.get("recent_transactions", data.get("transactions", []))

    if customer:
        cols = st.columns(4)
        cols[0].metric("Credit Score", customer.get("credit_score", "N/A"))
        cols[1].metric("Annual Income", f"₹{(customer.get('annual_income') or 0):,.0f}")
        cols[2].metric("Employment", (customer.get("employment_status") or "N/A").replace("_", " ").title())
        cols[3].metric("Total Balance", f"₹{data.get('total_balance', 0):,.2f}")

    if accounts:
        import pandas as pd
        df = pd.DataFrame([{
            "Account ID": a["account_id"],
            "Type": a["account_type"].replace("_", " ").title(),
            "Balance (₹)": f"{a['balance']:,.2f}",
            "Status": a["status"].upper(),
            "Interest Rate": f"{a.get('interest_rate') or 0:.1f}%",
        } for a in accounts])
        st.dataframe(df, use_container_width=True, hide_index=True)

    if transactions:
        st.markdown("**Recent Transactions**")
        import pandas as pd
        df = pd.DataFrame([{
            "Date": t["timestamp"][:10] if t.get("timestamp") else "",
            "Type": t["transaction_type"].upper(),
            "Amount (₹)": f"{t['amount']:,.2f}",
            "Description": t.get("description", ""),
            "Merchant": t.get("merchant", ""),
        } for t in transactions[:10]])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_risk_panel(data: Dict[str, Any]):
    st.markdown("**🔍 Risk & Fraud Analysis**")
    level = data.get("overall_risk_level", "low")
    score = data.get("overall_risk_score", 0)
    flagged = data.get("flagged_transactions", [])

    col1, col2, col3 = st.columns(3)
    col1.metric("Risk Level", level.upper())
    col2.metric("Risk Score", f"{score:.0f}/100")
    col3.metric("Flagged", f"{len(flagged)} transactions")

    st.caption(f"⚙️ {data.get('analysis_mode', 'rule-based')}")

    if flagged:
        import pandas as pd
        rows = []
        for f in flagged:
            rows.append({
                "Transaction ID": f["transaction_id"],
                "Amount (₹)": f"{f['amount']:,.2f}",
                "Risk Level": f["risk_level"].upper(),
                "Score": f"{f['risk_score']:.0f}",
                "Primary Reason": f["reasons"][0] if f.get("reasons") else "",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No suspicious transactions detected.")


def _render_credit_panel(data: Dict[str, Any]):
    # EMI result
    if "monthly_emi" in data:
        st.markdown("**🧮 EMI Calculation**")
        cols = st.columns(3)
        cols[0].metric("Monthly EMI", f"₹{data['monthly_emi']:,.2f}")
        cols[1].metric("Total Payment", f"₹{data['total_payment']:,.2f}")
        cols[2].metric("Total Interest", f"₹{data['total_interest']:,.2f}")
        st.caption(f"Formula: {data.get('formula_used', '')}")
        return

    # Eligibility result
    if "is_eligible" in data:
        st.markdown("**📋 Loan Eligibility Assessment**")
        eligible = data["is_eligible"]
        color = "#81c784" if eligible else "#ef9a9a"
        verdict = "ELIGIBLE ✅" if eligible else "NOT ELIGIBLE ❌"
        st.markdown(f"<h4 style='color:{color};'>{verdict}</h4>", unsafe_allow_html=True)

        criteria = data.get("criteria_results", [])
        if criteria:
            import pandas as pd
            df = pd.DataFrame([{
                "Criterion": c["criterion"],
                "Required": c["required"],
                "Actual": c["actual"],
                "Result": "✅ Pass" if c["passed"] else "❌ Fail",
            } for c in criteria])
            st.dataframe(df, use_container_width=True, hide_index=True)

        if data.get("estimated_emi"):
            st.metric("Estimated Monthly EMI", f"₹{data['estimated_emi']:,.2f}")
        st.caption(f"⚠️ {data.get('disclaimer', 'Simulated assessment only.')}")
        return

    # Loan list
    loans = data.get("loans", [])
    if loans:
        st.markdown("**📄 Loan Portfolio**")
        cols = st.columns(3)
        cols[0].metric("Active Loans", data.get("active_loan_count", 0))
        cols[1].metric("Total Outstanding", f"₹{data.get('total_outstanding_balance', 0):,.2f}")
        cols[2].metric("Total Monthly EMI", f"₹{data.get('total_monthly_emi', 0):,.2f}")

        import pandas as pd
        df = pd.DataFrame([{
            "Loan ID": l["loan_id"],
            "Type": l["loan_type"].replace("_", " ").title(),
            "Principal (₹)": f"{l['principal_amount']:,.2f}",
            "Outstanding (₹)": f"{l['outstanding_balance']:,.2f}",
            "EMI (₹)": f"{l['monthly_emi']:,.2f}",
            "Rate": f"{l['interest_rate']}%",
            "Status": l["loan_status"].upper(),
            "Missed": l.get("missed_payments", 0),
        } for l in loans])
        st.dataframe(df, use_container_width=True, hide_index=True)


def _render_compliance_panel(data: Dict[str, Any]):
    st.markdown("**✅ KYC & Compliance Status**")
    status = data.get("kyc_status", "unknown")
    risk = data.get("risk_rating", "unknown")
    compliance = data.get("compliance_status", "unknown")

    cols = st.columns(3)
    cols[0].metric("KYC Status", status.upper())
    cols[1].metric("Risk Rating", risk.upper())
    cols[2].metric("Compliance", compliance.replace("_", " ").title())

    verif = data.get("verifications", {})
    if verif:
        st.markdown("**Verification Checks:**")
        vcols = st.columns(5)
        icons = {True: "✅", False: "❌"}
        for i, (k, v) in enumerate(verif.items()):
            vcols[i % 5].markdown(f"{icons.get(v, '?')} {k.replace('_', ' ').title()}")

    missing = data.get("missing_fields", [])
    if missing:
        st.warning(f"Missing fields: {', '.join(missing)}")

    findings = data.get("compliance_findings", [])
    if findings:
        st.error("Compliance Findings:\n" + "\n".join(f"• {f}" for f in findings))

    warnings = data.get("compliance_warnings", [])
    if warnings:
        st.warning("Warnings:\n" + "\n".join(f"• {w}" for w in warnings))

    st.caption("⚠️ Simulated KYC check — not a real AML/KYC system.")


def render_agent_trace(response: Dict[str, Any]):
    """Render the agent execution trace."""
    traces = response.get("agent_traces", [])
    tools = response.get("tools_executed", [])

    st.markdown("**Execution Pipeline:**")

    # Visual pipeline
    agents = response.get("agents_invoked", [])
    if agents:
        agent_labels = {
            "customer_agent": "👤 Customer Agent",
            "risk_agent": "🔍 Risk/Fraud Agent",
            "credit_agent": "💳 Credit/Loan Agent",
            "compliance_agent": "✅ Compliance Agent",
            "orchestrator": "🎯 Orchestrator",
        }
        pipeline = " → ".join([agent_labels.get(a, a) for a in agents])
        st.markdown(f"""
        <div class='agent-trace'>
            🎯 Supervisor Orchestrator → {pipeline}
        </div>
        """, unsafe_allow_html=True)

    # Individual traces
    for trace in traces:
        agent = trace.get("agent_name", "unknown")
        tools_called = trace.get("tools_called", [])
        outcome = trace.get("outcome", "unknown")
        duration = trace.get("duration_ms", 0)
        outcome_icon = "✅" if outcome == "success" else "❌"

        st.markdown(f"""
        <div class='agent-trace'>
            {outcome_icon} <strong>{agent}</strong> 
            [{duration:.1f}ms]<br>
            Tools: {', '.join(tools_called) if tools_called else 'none'}
        </div>
        """, unsafe_allow_html=True)

    if tools:
        st.markdown(f"**Tools Executed:** {', '.join(set(tools))}")


# ──────────────────────────────── Main App ────────────────────────────────────

def init_session_state():
    """Ensure all required session state variables exist."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "selected_customer" not in st.session_state:
        st.session_state.selected_customer = "CUST001"
    if "last_response" not in st.session_state:
        st.session_state.last_response = None


def main():
    init_session_state()
    render_sidebar()
    render_header()

    # Check if database is seeded
    try:
        from backend.database import init_db
        init_db()
        from backend.database import SessionLocal
        from backend.models import Customer
        db = SessionLocal()
        count = db.query(Customer).count()
        db.close()
        if count == 0:
            st.warning(
                "⚠️ Database is empty! Please run: `python scripts/seed_database.py` "
                "to seed sample data, then refresh this page."
            )
    except Exception as e:
        st.error(f"Database error: {e}")
        return

    # Sample prompts
    sample_input = render_sample_prompts()

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    # Chat area
    render_chat()

    # Input
    cid = st.session_state.get("selected_customer", "CUST001")
    with st.form("chat_form", clear_on_submit=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            user_input = st.text_input(
                "Ask the Banking Assistant...",
                value=sample_input or "",
                placeholder=f"e.g. Show account balance for {cid} ...",
                label_visibility="collapsed",
            )
        with col2:
            submitted = st.form_submit_button("Send 🚀", use_container_width=True)

    if submitted and user_input.strip():
        # Add user message
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Process
        with st.spinner("🤖 Agents working..."):
            response = call_orchestrator(user_input, cid)
            st.session_state.last_response = response

        # Add assistant message
        answer = response.get("answer", "I could not process that request.")
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()

    # Response details (below chat)
    last_resp = st.session_state.get("last_response")
    if last_resp:
        render_response_details(last_resp)


if __name__ == "__main__":
    main()
