"""
backend/agents/orchestrator.py
================================
Supervisor / Orchestrator Agent

The central intelligence that:
  1. Classifies user intent (via LLM or deterministic fallback)
  2. Selects the appropriate specialized agent(s)
  3. Executes agents in the right sequence
  4. Aggregates results from multiple agents
  5. Generates a clear natural-language response
  6. Returns a full execution trace

Design principles:
  - LLM is used for intent classification and response phrasing only
  - ALL factual banking data comes from tools / database — never from the LLM
  - Unknown intents and errors are handled gracefully
  - The execution trace is always returned for transparency
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.agents.customer_agent import CustomerBankingAgent
from backend.agents.risk_agent import RiskFraudAgent
from backend.agents.credit_agent import CreditLoanAgent
from backend.agents.compliance_agent import ComplianceAgent
from backend.services.llm_service import llm_service

logger = logging.getLogger(__name__)


# ──────────────────────────────── Response Templates (Mock Mode) ───────────────

def _format_account_response(data: Dict[str, Any]) -> str:
    d = data.get("data", data)
    if "error" in d:
        return f"❌ {d['error']}"
    customer = d.get("customer", {})
    accounts = d.get("accounts", [])
    name = customer.get("full_name", "the customer")
    acc_lines = []
    for a in accounts:
        acc_lines.append(
            f"  • {a['account_type'].title()} ({a['account_id']}): "
            f"₹{a['balance']:,.2f} [{a['status']}]"
        )
    txns = d.get("recent_transactions", [])
    txn_lines = []
    for t in txns[:5]:
        sign = "+" if t["transaction_type"] == "credit" else "-"
        txn_lines.append(
            f"  • {t['timestamp'][:10]} | {sign}₹{t['amount']:,.2f} — {t.get('description', 'N/A')}"
        )
    parts = [
        f"**Account Summary for {name} ({customer.get('customer_id', '')})**",
        f"Credit Score: {customer.get('credit_score', 'N/A')} | "
        f"Employment: {customer.get('employment_status', 'N/A')}",
        "",
        f"**Accounts ({len(accounts)}) — Total Balance: ₹{d.get('total_balance', 0):,.2f}**",
        *acc_lines,
        "",
        "**Recent Transactions:**",
        *(txn_lines if txn_lines else ["  No recent transactions."]),
        "",
        "_⚠️ All data is simulated for demonstration purposes._",
    ]
    return "\n".join(parts)


def _format_risk_response(data: Dict[str, Any]) -> str:
    d = data.get("data", data)
    if "error" in d:
        return f"❌ {d['error']}"
    flagged = d.get("flagged_transactions", [])
    level = d.get("overall_risk_level", "unknown").upper()
    score = d.get("overall_risk_score", 0)
    checked = d.get("total_transactions_checked", 0)
    risk_emoji = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴", "CRITICAL": "🚨"}.get(level, "⚪")
    lines = [
        f"**Risk Analysis — {d.get('customer_id', '')}**",
        f"{risk_emoji} Overall Risk: **{level}** (Score: {score:.0f}/100)",
        f"Transactions analysed: {checked} | Flagged: {len(flagged)}",
        f"Analysis mode: {d.get('analysis_mode', 'rule-based')}",
        "",
    ]
    if flagged:
        lines.append("**Flagged Transactions:**")
        for f in flagged[:5]:
            lines.append(
                f"  🚩 {f['transaction_id']} — ₹{f['amount']:,.2f} "
                f"[{f['risk_level'].upper()}]"
            )
            for r in f.get("reasons", [])[:2]:
                lines.append(f"     → {r}")
    else:
        lines.append("✅ No suspicious transactions detected.")
    lines.append("")
    lines.append("_⚠️ Rule-based analysis — not a trained ML model. Simulated data only._")
    return "\n".join(lines)


def _format_loan_response(data: Dict[str, Any]) -> str:
    d = data.get("data", data)
    if "error" in d:
        return f"❌ {d['error']}"
    loans = d.get("loans", [])
    active = [l for l in loans if l.get("loan_status") == "active"]
    lines = [
        f"**Loan Summary — {d.get('customer_id', '')}**",
        f"Total loans: {len(loans)} | Active: {len(active)}",
        f"Total outstanding: ₹{d.get('total_outstanding_balance', 0):,.2f}",
        f"Total monthly EMI: ₹{d.get('total_monthly_emi', 0):,.2f}",
        "",
    ]
    for l in loans:
        status_emoji = "✅" if l.get("loan_status") == "active" else "⭕"
        lines.append(
            f"{status_emoji} {l.get('loan_type', '').title()} Loan ({l.get('loan_id', '')}): "
            f"₹{l.get('principal_amount', 0):,.2f} @ {l.get('interest_rate', 0)}% | "
            f"Outstanding: ₹{l.get('outstanding_balance', 0):,.2f} | "
            f"EMI: ₹{l.get('monthly_emi', 0):,.2f}/mo"
        )
    lines.append("")
    lines.append("_⚠️ Simulated loan data only._")
    return "\n".join(lines)


def _format_eligibility_response(data: Dict[str, Any]) -> str:
    d = data.get("data", data)
    if "error" in d:
        return f"❌ {d['error']}"
    eligible = d.get("is_eligible", False)
    emoji = "✅" if eligible else "❌"
    lines = [
        f"**Loan Eligibility Assessment — {d.get('customer_id', '')}**",
        f"{emoji} Eligibility: **{'ELIGIBLE' if eligible else 'NOT ELIGIBLE'}**",
        f"Requested: ₹{d.get('requested_amount', 0):,.2f} ({d.get('loan_type', 'personal').title()} Loan)",
        f"Estimated EMI: ₹{d.get('estimated_emi', 0):,.2f}/month",
        "",
        "**Criteria Results:**",
    ]
    for c in d.get("criteria_results", []):
        icon = "✅" if c.get("passed") else "❌"
        lines.append(f"  {icon} {c['criterion']}: {c['actual']} (required: {c['required']})")
    lines.append("")
    lines.append(f"**Decision:** {d.get('decision_reason', '')}")
    lines.append("")
    lines.append(f"_⚠️ {d.get('disclaimer', 'Simulated assessment only.')}_")
    return "\n".join(lines)


def _format_emi_response(data: Dict[str, Any]) -> str:
    d = data.get("data", data)
    if "error" in d:
        return f"❌ {d['error']}"
    lines = [
        "**EMI Calculation Result**",
        f"Principal: ₹{d.get('principal', 0):,.2f}",
        f"Interest Rate: {d.get('annual_interest_rate', 0)}% per annum",
        f"Tenure: {d.get('tenure_months', 0)} months",
        "",
        f"💰 **Monthly EMI: ₹{d.get('monthly_emi', 0):,.2f}**",
        f"Total Payment: ₹{d.get('total_payment', 0):,.2f}",
        f"Total Interest: ₹{d.get('total_interest', 0):,.2f}",
        "",
        f"Formula: {d.get('formula_used', 'Reducing-balance')}",
        "_⚠️ Illustrative calculation only._",
    ]
    return "\n".join(lines)


def _format_kyc_response(data: Dict[str, Any]) -> str:
    d = data.get("data", data)
    if "error" in d:
        return f"❌ {d['error']}"
    status = d.get("kyc_status", "unknown").upper()
    compliance = d.get("compliance_status", "unknown").upper()
    risk = d.get("risk_rating", "unknown").upper()
    missing = d.get("missing_fields", [])
    findings = d.get("compliance_findings", [])
    warnings = d.get("compliance_warnings", [])
    lines = [
        f"**KYC & Compliance Status — {d.get('customer_id', '')}**",
        f"Customer: {d.get('customer_name', 'N/A')}",
        f"KYC Status: **{status}** | Risk Rating: {risk} | Compliance: {compliance}",
        "",
    ]
    verif = d.get("verifications", {})
    if verif:
        lines.append("**Verification Checks:**")
        for k, v in verif.items():
            lines.append(f"  {'✅' if v else '❌'} {k.replace('_', ' ').title()}")
        lines.append("")
    if missing:
        lines.append(f"**Missing Fields ({len(missing)}):** {', '.join(missing)}")
    if findings:
        lines.append("**Compliance Findings:**")
        for f in findings:
            lines.append(f"  ⚠️ {f}")
    if warnings:
        lines.append("**Warnings:**")
        for w in warnings:
            lines.append(f"  ℹ️ {w}")
    lines.append("")
    lines.append("_⚠️ Simulated KYC check — not a real AML/KYC system._")
    return "\n".join(lines)


def _format_combined_response(results: List[Dict[str, Any]]) -> str:
    parts = ["**Combined Banking Request — Results**\n"]
    for r in results:
        agent = r.get("agent", "agent")
        data = r.get("data", {})
        if agent == "customer_agent":
            parts.append(_format_account_response(r))
        elif agent == "risk_agent":
            parts.append(_format_risk_response(r))
        elif agent == "credit_agent":
            parts.append(_format_loan_response(r))
        elif agent == "compliance_agent":
            parts.append(_format_kyc_response(r))
        parts.append("")
    return "\n".join(parts)


# ──────────────────────────────── Orchestrator ────────────────────────────────

class BankingOrchestrator:
    """
    Supervisor / Orchestrator Agent.
    Routes natural-language banking requests to the appropriate specialized agents.
    """

    def __init__(self):
        self.customer_agent = CustomerBankingAgent()
        self.risk_agent = RiskFraudAgent()
        self.credit_agent = CreditLoanAgent()
        self.compliance_agent = ComplianceAgent()

    # ──────────────────────────────────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────────────────────────────────

    def process(self, message: str, customer_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process a natural-language banking request end to end.

        Returns a structured response containing:
          - intent
          - answer (natural language)
          - agents_invoked
          - agent_traces
          - tools_executed
          - structured_data
          - warnings, errors
          - llm_mode
          - execution_duration_ms
        """
        start = time.monotonic()
        warnings: List[str] = []
        errors: List[str] = []

        # ── 1. Classify intent ────────────────────────────────────────────
        classification = llm_service.classify_intent(message, customer_id)
        intent: str = classification["intent"]
        resolved_customer_id: Optional[str] = classification.get("customer_id") or customer_id
        params: Dict[str, Any] = classification.get("parameters", {})
        llm_mode: str = classification.get("llm_mode", "mock")

        logger.info("Intent: %s | Customer: %s | LLM mode: %s", intent, resolved_customer_id, llm_mode)

        # ── 2. Route to agent(s) ──────────────────────────────────────────
        agent_results: List[Dict[str, Any]] = []
        agents_invoked: List[str] = []
        tools_executed: List[str] = []

        try:
            agent_results, agents_invoked, tools_executed = self._route(
                intent=intent,
                customer_id=resolved_customer_id,
                params=params,
                message=message,
            )
        except Exception as exc:
            logger.error("Routing error: %s", exc)
            errors.append(str(exc))

        # ── 3. Build structured data payload ─────────────────────────────
        structured_data: Dict[str, Any] = {
            "intent": intent,
            "customer_id": resolved_customer_id,
            "agent_results": agent_results,
        }

        # ── 4. Generate natural-language answer ───────────────────────────
        fallback_answer = self._build_fallback_answer(intent, agent_results, params)
        answer, response_llm_mode = llm_service.generate_response(
            intent=intent,
            structured_data={"intent": intent, "results": agent_results[:2]},
            fallback_text=fallback_answer,
        )
        if response_llm_mode != "mock":
            llm_mode = response_llm_mode  # Update if real LLM was used

        # ── 5. Build execution trace ──────────────────────────────────────
        agent_traces = [
            {
                "agent_name": r.get("agent", "unknown"),
                "tools_called": r.get("tools_called", []),
                "outcome": "success" if "error" not in r.get("data", {}) else "error",
                "duration_ms": r.get("duration_ms", 0),
            }
            for r in agent_results
        ]

        duration_ms = (time.monotonic() - start) * 1000

        return {
            "intent": intent,
            "answer": answer,
            "agents_invoked": agents_invoked,
            "agent_traces": agent_traces,
            "tools_executed": tools_executed,
            "structured_data": structured_data,
            "warnings": warnings,
            "errors": errors,
            "llm_mode": llm_mode,
            "execution_duration_ms": round(duration_ms, 2),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Internal routing
    # ──────────────────────────────────────────────────────────────────────────

    def _route(
        self,
        intent: str,
        customer_id: Optional[str],
        params: Dict[str, Any],
        message: str,
    ) -> Tuple[List[Dict[str, Any]], List[str], List[str]]:
        """Dispatch to the appropriate agent(s) based on intent."""
        results: List[Dict[str, Any]] = []
        agents: List[str] = []
        tools: List[str] = []

        def add_result(r: Dict[str, Any]):
            results.append(r)
            agents.append(r.get("agent", ""))
            tools.extend(r.get("tools_called", []))

        if intent == "account_inquiry":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["customer_agent"], []
            r = self.customer_agent.get_full_summary(customer_id)
            add_result(r)

        elif intent == "transaction_inquiry":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["customer_agent"], []
            r = self.customer_agent.get_transactions(customer_id, limit=20)
            add_result(r)

        elif intent == "fraud_risk_analysis":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["risk_agent"], []
            # Customer context first, then risk
            cr = self.customer_agent.get_transactions(customer_id, limit=50)
            add_result(cr)
            rr = self.risk_agent.analyze_risk(customer_id, limit=50)
            add_result(rr)

        elif intent == "loan_inquiry":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["credit_agent"], []
            r = self.credit_agent.get_loans(customer_id)
            add_result(r)

        elif intent == "loan_eligibility_check":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["credit_agent"], []
            amount = params.get("requested_amount") or self._extract_amount(message) or 500000.0
            loan_type = params.get("loan_type", "personal")
            tenure = params.get("tenure_months", 36)
            r = self.credit_agent.check_eligibility(
                customer_id, float(amount), str(loan_type), int(tenure)
            )
            add_result(r)

        elif intent == "emi_calculation":
            principal = float(params.get("principal", 0) or self._extract_amount(message) or 300000)
            rate = float(params.get("annual_interest_rate", 10))
            tenure = int(params.get("tenure_months", 36))
            if principal <= 0:
                principal = 300000.0
            r = self.credit_agent.compute_emi(principal, rate, tenure)
            add_result(r)

        elif intent == "kyc_verification":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["compliance_agent"], []
            r = self.compliance_agent.verify_kyc(customer_id)
            add_result(r)

        elif intent == "combined_inquiry":
            if not customer_id:
                results.append(self._no_customer_error())
                return results, ["customer_agent", "risk_agent", "credit_agent"], []
            # Run all three main agents
            add_result(self.customer_agent.get_full_summary(customer_id))
            add_result(self.risk_agent.analyze_risk(customer_id))
            add_result(self.credit_agent.get_loans(customer_id))

        else:
            # general_question or unknown
            results.append({
                "agent": "orchestrator",
                "tools_called": [],
                "duration_ms": 0,
                "data": {
                    "message": (
                        "I can help with: account balances, transaction history, "
                        "fraud analysis, loan details, EMI calculations, loan eligibility, "
                        "and KYC verification. Please specify a customer ID (e.g. CUST001) "
                        "and what you need."
                    )
                },
            })
            agents.append("orchestrator")

        return results, agents, list(set(tools))

    # ──────────────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _no_customer_error() -> Dict[str, Any]:
        return {
            "agent": "orchestrator",
            "tools_called": [],
            "duration_ms": 0,
            "data": {
                "error": (
                    "No customer ID provided or found in the message. "
                    "Please include a customer ID (e.g., CUST001, CUST002) in your request."
                )
            },
        }

    @staticmethod
    def _extract_amount(message: str) -> Optional[float]:
        import re
        match = re.search(r"(\d[\d,]*(?:\.\d+)?)\s*(?:lakh|lakhs)?", message, re.IGNORECASE)
        if match:
            val = float(match.group(1).replace(",", ""))
            if "lakh" in message.lower():
                val *= 100_000
            return val
        return None

    def _build_fallback_answer(
        self,
        intent: str,
        results: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> str:
        """Build the mock-mode natural language answer from structured results."""
        if not results:
            return "I could not process your request. Please try again."

        first = results[0]

        if "error" in first.get("data", {}):
            return f"❌ {first['data']['error']}"

        formatters = {
            "account_inquiry": lambda: _format_account_response(first),
            "transaction_inquiry": lambda: _format_account_response(first),
            "fraud_risk_analysis": lambda: (
                _format_risk_response(results[1]) if len(results) > 1 else _format_risk_response(first)
            ),
            "loan_inquiry": lambda: _format_loan_response(first),
            "loan_eligibility_check": lambda: _format_eligibility_response(first),
            "emi_calculation": lambda: _format_emi_response(first),
            "kyc_verification": lambda: _format_kyc_response(first),
            "combined_inquiry": lambda: _format_combined_response(results),
        }

        formatter = formatters.get(intent)
        if formatter:
            return formatter()

        # General / unknown
        data = first.get("data", {})
        return data.get("message", "Request processed. Please see the structured data below.")


# Singleton
orchestrator = BankingOrchestrator()
