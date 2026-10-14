"""
tests/test_compliance.py
=========================
Tests for KYC compliance checks.
"""
from __future__ import annotations

import pytest


class TestComplianceAgent:
    """Tests for the Compliance Agent."""

    def setup_method(self):
        from backend.agents.compliance_agent import ComplianceAgent
        self.agent = ComplianceAgent()

    def test_unknown_customer(self):
        result = self.agent.verify_kyc("CUST_FAKE")
        data = result.get("data", {})
        assert "error" in data

    def test_result_structure(self):
        """verify_kyc must return agent metadata."""
        result = self.agent.verify_kyc("CUST001")
        assert result.get("agent") == "compliance_agent"
        assert "tools_called" in result
        assert "data" in result

    def test_compliance_fields_present(self):
        result = self.agent.verify_kyc("CUST001")
        data = result.get("data", {})
        if "error" not in data:
            assert "kyc_status" in data
            assert "compliance_status" in data
            assert "missing_fields" in data
            assert "disclaimer" in data

    def test_policies_returned(self):
        result = self.agent.get_policies()
        data = result.get("data", {})
        assert "policies" in data
        assert "disclaimer" in data["policies"]

    def test_cust005_non_compliant(self):
        """CUST005 has KYC failed — should be non-compliant."""
        result = self.agent.verify_kyc("CUST005")
        data = result.get("data", {})
        if "error" not in data:
            status = data.get("compliance_status", "")
            assert status == "non_compliant"
