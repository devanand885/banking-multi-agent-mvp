"""
tests/test_loans.py
====================
Tests for EMI calculation and loan eligibility tools.
"""
from __future__ import annotations

import pytest


class TestEMICalculation:
    """Unit tests for the EMI calculation tool."""

    def setup_method(self):
        from backend.tools.loan_tools import calculate_emi
        self.calc = calculate_emi

    def test_standard_emi(self):
        """Test standard reducing-balance EMI calculation."""
        result = self.calc(300000, 10, 36)
        assert result.get("success") is True
        # EMI for 3L at 10% for 36 months should be ~₹9,681
        emi = result["monthly_emi"]
        assert 9000 < emi < 11000, f"Unexpected EMI: {emi}"
        assert result["total_payment"] > result["principal"]
        assert result["total_interest"] > 0

    def test_zero_interest(self):
        """Zero-interest loan: EMI = Principal / Tenure."""
        result = self.calc(120000, 0, 12)
        assert result.get("success") is True
        assert abs(result["monthly_emi"] - 10000.0) < 0.01
        assert abs(result["total_interest"]) < 0.01
        assert "Zero-interest" in result["formula_used"]

    def test_large_loan(self):
        """Large home loan calculation."""
        result = self.calc(5000000, 8.5, 240)
        assert result.get("success") is True
        emi = result["monthly_emi"]
        assert 40000 < emi < 50000, f"Unexpected EMI for home loan: {emi}"

    def test_invalid_principal(self):
        """Negative principal should return error."""
        result = self.calc(-100000, 10, 36)
        assert "error" in result

    def test_invalid_tenure(self):
        """Zero tenure should return error."""
        result = self.calc(100000, 10, 0)
        assert "error" in result

    def test_invalid_rate(self):
        """Rate over 100% should return error."""
        result = self.calc(100000, 150, 12)
        assert "error" in result

    def test_short_tenure(self):
        """1-month tenure works correctly."""
        result = self.calc(50000, 12, 1)
        assert result.get("success") is True
        # EMI ≈ principal + one month's interest
        assert result["monthly_emi"] > 50000

    def test_emi_formula_consistency(self):
        """total_payment = monthly_emi × tenure_months (within rounding)."""
        result = self.calc(200000, 9, 24)
        assert result.get("success") is True
        expected_total = result["monthly_emi"] * result["tenure_months"]
        assert abs(result["total_payment"] - expected_total) < 1.0


class TestLoanEligibility:
    """Tests for loan eligibility checking."""

    def setup_method(self):
        from backend.tools.loan_tools import check_loan_eligibility
        self.check = check_loan_eligibility

    def test_unknown_customer(self):
        result = self.check("CUST_DOES_NOT_EXIST", 500000)
        assert "error" in result

    def test_criteria_structure(self):
        """Eligibility result must contain required fields."""
        # Use a known seeded customer if DB is seeded, else expect error
        result = self.check("CUST001", 500000)
        if "error" not in result:
            assert "is_eligible" in result
            assert "criteria_results" in result
            assert "disclaimer" in result
            for c in result["criteria_results"]:
                assert "criterion" in c
                assert "passed" in c

    def test_disclaimer_present(self):
        """Disclaimer must always be present."""
        result = self.check("CUST001", 500000)
        if "error" not in result:
            assert "simulated" in result["disclaimer"].lower()
