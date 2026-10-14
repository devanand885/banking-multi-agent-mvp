"""
backend/agents/credit_agent.py
================================
Credit / Loan Agent

Responsibilities:
  - Retrieve loan details and outstanding balances
  - Check eligibility against configurable sample lending criteria
  - Explain which criteria were met or not met
  - Estimate an illustrative EMI using the standard reducing-balance formula
  - Label all results as simulated assessments
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from backend.tools.registry import tool_registry
from backend.tools.loan_tools import (
    get_customer_loans,
    calculate_emi,
    check_loan_eligibility,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "credit_agent"


class CreditLoanAgent:
    """Agent responsible for loan and credit operations."""

    name = AGENT_NAME

    def __init__(self):
        self._register_tools()

    def _register_tools(self):
        tools = [
            ("get_customer_loans", "Retrieve all loan records for a customer",
             [AGENT_NAME, "orchestrator"], get_customer_loans,
             {"customer_id": "str"}),
            ("calculate_emi", "Calculate EMI using the reducing-balance formula",
             [AGENT_NAME, "orchestrator"], calculate_emi,
             {"principal": "float", "annual_interest_rate": "float", "tenure_months": "int"}),
            ("check_loan_eligibility", "Check if a customer meets sample loan eligibility criteria",
             [AGENT_NAME, "orchestrator"], check_loan_eligibility,
             {"customer_id": "str", "requested_amount": "float",
              "loan_type": "str (optional)", "tenure_months": "int (optional)"}),
        ]
        existing = {t["name"] for t in tool_registry.list_tools()}
        for name, desc, agents, func, schema in tools:
            if name not in existing:
                tool_registry.register_func(
                    name=name, description=desc,
                    authorized_agents=agents, func=func, input_schema=schema,
                )

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────────

    def get_loans(self, customer_id: str) -> Dict[str, Any]:
        start = time.monotonic()
        result = tool_registry.call("get_customer_loans", AGENT_NAME, customer_id=customer_id)
        return self._wrap(result, ["get_customer_loans"], time.monotonic() - start)

    def compute_emi(
        self,
        principal: float,
        annual_interest_rate: float,
        tenure_months: int,
    ) -> Dict[str, Any]:
        start = time.monotonic()
        result = tool_registry.call(
            "calculate_emi", AGENT_NAME,
            principal=principal,
            annual_interest_rate=annual_interest_rate,
            tenure_months=tenure_months,
        )
        return self._wrap(result, ["calculate_emi"], time.monotonic() - start)

    def check_eligibility(
        self,
        customer_id: str,
        requested_amount: float,
        loan_type: str = "personal",
        tenure_months: int = 36,
    ) -> Dict[str, Any]:
        start = time.monotonic()
        result = tool_registry.call(
            "check_loan_eligibility", AGENT_NAME,
            customer_id=customer_id,
            requested_amount=requested_amount,
            loan_type=loan_type,
            tenure_months=tenure_months,
        )
        return self._wrap(result, ["check_loan_eligibility"], time.monotonic() - start)

    # ──────────────────────────────────────────────────────────────────────────
    # Internal
    # ──────────────────────────────────────────────────────────────────────────

    @staticmethod
    def _wrap(data: Dict[str, Any], tools: List[str], elapsed: float) -> Dict[str, Any]:
        return {
            "agent": AGENT_NAME,
            "tools_called": tools,
            "duration_ms": round(elapsed * 1000, 2),
            "data": data,
        }
