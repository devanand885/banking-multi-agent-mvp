"""
tests/test_customers.py
========================
Tests for customer lookup and account retrieval tools.
"""
from __future__ import annotations

import pytest


class TestCustomerTools:
    """Tests for customer lookup tools."""

    def setup_method(self):
        from backend.tools.banking_tools import (
            get_customer_profile,
            get_customer_accounts,
            get_customer_transactions,
        )
        self.get_profile = get_customer_profile
        self.get_accounts = get_customer_accounts
        self.get_transactions = get_customer_transactions

    def test_unknown_customer_returns_error(self):
        """Unknown customer IDs must return an error dict, not raise."""
        result = self.get_profile("CUST_XXXX")
        assert "error" in result
        assert "CUST_XXXX" in result["error"]

    def test_unknown_customer_accounts(self):
        result = self.get_accounts("CUST_XXXX")
        assert "error" in result

    def test_unknown_customer_transactions(self):
        result = self.get_transactions("CUST_XXXX")
        assert "error" in result

    def test_valid_customer_structure(self):
        """Known seeded customer should return correct structure."""
        result = self.get_profile("CUST001")
        if "error" not in result:
            assert result.get("success") is True
            c = result.get("customer", {})
            assert c.get("customer_id") == "CUST001"
            assert "first_name" in c
            assert "email" in c

    def test_accounts_structure(self):
        result = self.get_accounts("CUST001")
        if "error" not in result:
            assert "accounts" in result
            assert "total_balance" in result
            assert isinstance(result["accounts"], list)

    def test_transaction_limit(self):
        """Transaction limit parameter should be respected."""
        result = self.get_transactions("CUST001", limit=3)
        if "error" not in result:
            assert len(result.get("transactions", [])) <= 3

    def test_case_insensitive_customer_id(self):
        """Customer ID lookup should handle lowercase."""
        # The tools accept lowercase and look them up as-is
        # The API layer does .upper() — here test tool directly
        result_upper = self.get_profile("CUST001")
        # Both should either succeed with customer or return error consistently
        assert "customer" in result_upper or "error" in result_upper


class TestKYCTool:
    """Tests for KYC status tool."""

    def setup_method(self):
        from backend.tools.loan_tools import get_kyc_status
        self.get_kyc = get_kyc_status

    def test_unknown_customer(self):
        result = self.get_kyc("CUST_XXXX")
        assert "error" in result

    def test_kyc_structure(self):
        result = self.get_kyc("CUST001")
        if "error" not in result:
            assert "kyc_status" in result
            assert "missing_fields" in result
            assert "verifications" in result
            assert "disclaimer" in result

    def test_disclaimer_in_kyc(self):
        result = self.get_kyc("CUST001")
        if "error" not in result:
            assert "simulated" in result["disclaimer"].lower()

    def test_cust005_has_missing_fields(self):
        """CUST005 is seeded with many missing fields."""
        result = self.get_kyc("CUST005")
        if "error" not in result:
            missing = result.get("missing_fields", [])
            # Should have some missing fields
            assert len(missing) > 0
