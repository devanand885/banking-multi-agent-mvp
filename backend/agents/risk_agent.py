"""
backend/agents/risk_agent.py
==============================
Risk / Fraud Agent

Responsibilities:
  - Inspect simulated transaction records
  - Flag suspicious transactions using rule-based logic
  - Calculate and explain a transparent risk score
  - Return flagged transaction IDs, reasons, and risk levels

This agent uses a RULE-BASED approach — it is NOT a trained ML model.
All rules are documented in backend/tools/risk_tools.py.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from backend.tools.registry import tool_registry
from backend.tools.risk_tools import analyze_transaction_risk

logger = logging.getLogger(__name__)

AGENT_NAME = "risk_agent"


class RiskFraudAgent:
    """Agent responsible for fraud detection and risk analysis."""

    name = AGENT_NAME

    def __init__(self):
        self._register_tools()

    def _register_tools(self):
        if not any(t["name"] == "analyze_transaction_risk" for t in tool_registry.list_tools()):
            tool_registry.register_func(
                name="analyze_transaction_risk",
                description=(
                    "Analyse a customer's transactions for suspicious patterns using "
                    "rule-based fraud detection. Returns risk scores and flagged transactions."
                ),
                authorized_agents=[AGENT_NAME, "orchestrator"],
                func=analyze_transaction_risk,
                input_schema={"customer_id": "str", "limit": "int (optional, default 50)"},
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────────

    def analyze_risk(self, customer_id: str, limit: int = 50) -> Dict[str, Any]:
        """Run full risk analysis for a customer."""
        start = time.monotonic()
        result = tool_registry.call(
            "analyze_transaction_risk", AGENT_NAME,
            customer_id=customer_id, limit=limit,
        )
        return self._wrap(result, ["analyze_transaction_risk"], time.monotonic() - start)

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
