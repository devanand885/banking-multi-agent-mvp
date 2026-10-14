"""
backend/agents/customer_agent.py
==================================
Customer Banking Agent

Responsibilities:
  - Retrieve customer profiles
  - Retrieve account details and balances
  - Retrieve recent transactions
  - Summarize account activity
  - Answer basic banking questions using actual simulated records
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from backend.tools.registry import tool_registry
from backend.tools.banking_tools import (
    get_customer_profile,
    get_customer_accounts,
    get_customer_transactions,
)

logger = logging.getLogger(__name__)

AGENT_NAME = "customer_agent"


class CustomerBankingAgent:
    """Agent responsible for customer profile, accounts, and transaction data."""

    name = AGENT_NAME

    def __init__(self):
        self._register_tools()

    def _register_tools(self):
        """Register this agent's tools in the global registry."""
        tools_to_register = [
            ("get_customer_profile", "Look up a customer's profile by ID", get_customer_profile,
             {"customer_id": "str"}),
            ("get_customer_accounts", "Retrieve all accounts and balances for a customer",
             get_customer_accounts, {"customer_id": "str"}),
            ("get_customer_transactions", "Retrieve recent transactions for a customer",
             get_customer_transactions, {"customer_id": "str", "limit": "int (optional)"}),
        ]
        for name, desc, func, schema in tools_to_register:
            if not any(t["name"] == name for t in tool_registry.list_tools()):
                tool_registry.register_func(
                    name=name,
                    description=desc,
                    authorized_agents=[AGENT_NAME, "orchestrator", "risk_agent"],
                    func=func,
                    input_schema=schema,
                )

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────────

    def get_profile(self, customer_id: str) -> Dict[str, Any]:
        start = time.monotonic()
        result = tool_registry.call("get_customer_profile", AGENT_NAME, customer_id=customer_id)
        return self._wrap(result, ["get_customer_profile"], time.monotonic() - start)

    def get_accounts(self, customer_id: str) -> Dict[str, Any]:
        start = time.monotonic()
        result = tool_registry.call("get_customer_accounts", AGENT_NAME, customer_id=customer_id)
        return self._wrap(result, ["get_customer_accounts"], time.monotonic() - start)

    def get_transactions(self, customer_id: str, limit: int = 20) -> Dict[str, Any]:
        start = time.monotonic()
        result = tool_registry.call(
            "get_customer_transactions", AGENT_NAME,
            customer_id=customer_id, limit=limit,
        )
        return self._wrap(result, ["get_customer_transactions"], time.monotonic() - start)

    def get_full_summary(self, customer_id: str) -> Dict[str, Any]:
        """Return profile + accounts + recent transactions in a single call."""
        start = time.monotonic()
        tools_called = []

        profile_result = tool_registry.call("get_customer_profile", AGENT_NAME, customer_id=customer_id)
        tools_called.append("get_customer_profile")

        if "error" in profile_result:
            return self._wrap(profile_result, tools_called, time.monotonic() - start)

        accounts_result = tool_registry.call("get_customer_accounts", AGENT_NAME, customer_id=customer_id)
        tools_called.append("get_customer_accounts")

        txn_result = tool_registry.call("get_customer_transactions", AGENT_NAME, customer_id=customer_id, limit=10)
        tools_called.append("get_customer_transactions")

        combined = {
            "success": True,
            "customer": profile_result.get("customer", {}),
            "accounts": accounts_result.get("accounts", []),
            "total_balance": accounts_result.get("total_balance", 0),
            "account_count": accounts_result.get("account_count", 0),
            "recent_transactions": txn_result.get("transactions", []),
            "transaction_count": txn_result.get("transaction_count", 0),
        }
        return self._wrap(combined, tools_called, time.monotonic() - start)

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
