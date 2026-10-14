"""
backend/agents/compliance_agent.py
=====================================
Compliance Agent

Responsibilities:
  - Perform simulated KYC verification checks
  - Check whether required customer profile fields are present
  - Identify missing information and return a clear status
  - Use a locally stored set of mock compliance policies

DISCLAIMER:
  This is a simulated compliance check for demonstration only.
  It does NOT constitute a real AML/KYC compliance system.
"""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from backend.tools.registry import tool_registry
from backend.tools.loan_tools import get_kyc_status

logger = logging.getLogger(__name__)

AGENT_NAME = "compliance_agent"

# ──────────────────────────────── Mock Compliance Policies ────────────────────
COMPLIANCE_POLICIES = {
    "kyc_required_for_account_opening": True,
    "kyc_required_for_loan": True,
    "minimum_kyc_level": "verified",
    "pep_enhanced_due_diligence": True,
    "large_transaction_reporting_threshold_inr": 50_000,
    "annual_kyc_renewal": True,
    "aml_monitoring_enabled": True,
    "version": "MockPolicy-v1.0",
    "disclaimer": (
        "These are sample mock compliance policies for demonstration. "
        "They do not represent real regulatory requirements."
    ),
}


class ComplianceAgent:
    """Agent responsible for simulated KYC and compliance checks."""

    name = AGENT_NAME

    def __init__(self):
        self._register_tools()

    def _register_tools(self):
        if not any(t["name"] == "get_kyc_status" for t in tool_registry.list_tools()):
            tool_registry.register_func(
                name="get_kyc_status",
                description=(
                    "Retrieve the KYC/compliance status of a customer, "
                    "including any missing required documents or information."
                ),
                authorized_agents=[AGENT_NAME, "orchestrator", "credit_agent"],
                func=get_kyc_status,
                input_schema={"customer_id": "str"},
            )

    # ──────────────────────────────────────────────────────────────────────────
    # Public interface
    # ──────────────────────────────────────────────────────────────────────────

    def verify_kyc(self, customer_id: str) -> Dict[str, Any]:
        """Perform simulated KYC verification and compliance check."""
        start = time.monotonic()
        kyc_result = tool_registry.call("get_kyc_status", AGENT_NAME, customer_id=customer_id)

        if "error" in kyc_result:
            return self._wrap(kyc_result, ["get_kyc_status"], time.monotonic() - start)

        # Additional policy checks
        compliance_findings: List[str] = []
        warnings: List[str] = []

        kyc_status = kyc_result.get("kyc_status", "unknown")
        risk_rating = kyc_result.get("risk_rating", "unknown")

        if kyc_status != "verified":
            compliance_findings.append(
                f"KYC status is '{kyc_status}' — must be 'verified' per policy."
            )

        missing = kyc_result.get("missing_fields", [])
        if missing:
            compliance_findings.append(
                f"Missing required fields: {', '.join(missing)}."
            )

        verifications = kyc_result.get("verifications", {})
        if verifications.get("photo_id_verified") is False:
            compliance_findings.append("Photo ID not verified.")
        if verifications.get("address_verified") is False:
            compliance_findings.append("Address not verified.")
        if verifications.get("income_verified") is False:
            warnings.append("Income not verified — enhanced due diligence may apply.")
        if verifications.get("pep_check_completed") is False:
            compliance_findings.append("PEP (Politically Exposed Person) check not completed.")
        if verifications.get("sanctions_check_completed") is False:
            compliance_findings.append("Sanctions check not completed.")

        if risk_rating in ("high", "critical"):
            warnings.append(
                f"Customer risk rating is '{risk_rating}' — "
                "enhanced due diligence required per policy."
            )

        overall_status = "compliant" if not compliance_findings else "non_compliant"

        combined = {
            **kyc_result,
            "compliance_status": overall_status,
            "compliance_findings": compliance_findings,
            "compliance_warnings": warnings,
            "applicable_policies": COMPLIANCE_POLICIES,
        }

        return self._wrap(combined, ["get_kyc_status"], time.monotonic() - start)

    def get_policies(self) -> Dict[str, Any]:
        """Return the mock compliance policies."""
        return {
            "agent": AGENT_NAME,
            "tools_called": [],
            "duration_ms": 0,
            "data": {"policies": COMPLIANCE_POLICIES},
        }

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
