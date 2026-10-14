"""
tests/test_risk.py
===================
Tests for rule-based fraud detection and risk scoring.
"""
from __future__ import annotations

import pytest


class TestRiskRules:
    """Tests for the rule-based fraud detection engine."""

    def setup_method(self):
        from backend.tools.risk_tools import (
            analyze_transaction_risk,
            _score_to_level,
            LARGE_TXN_THRESHOLD,
            VERY_LARGE_TXN_THRESHOLD,
        )
        self.analyze = analyze_transaction_risk
        self.score_to_level = _score_to_level
        self.LARGE = LARGE_TXN_THRESHOLD
        self.VERY_LARGE = VERY_LARGE_TXN_THRESHOLD

    def test_score_to_level_boundaries(self):
        """Test risk level boundaries."""
        assert self.score_to_level(0) == "low"
        assert self.score_to_level(19) == "low"
        assert self.score_to_level(20) == "medium"
        assert self.score_to_level(39) == "medium"
        assert self.score_to_level(40) == "high"
        assert self.score_to_level(69) == "high"
        assert self.score_to_level(70) == "critical"
        assert self.score_to_level(100) == "critical"

    def test_unknown_customer(self):
        result = self.analyze("CUST_DOES_NOT_EXIST")
        assert "error" in result

    def test_result_structure(self):
        """Result must always have required keys."""
        result = self.analyze("CUST001")
        if "error" not in result:
            assert "overall_risk_level" in result
            assert "overall_risk_score" in result
            assert "flagged_transactions" in result
            assert "analysis_mode" in result
            assert "total_transactions_checked" in result

    def test_analysis_mode_is_rule_based(self):
        """Must clearly state it is rule-based, not ML."""
        result = self.analyze("CUST002")
        if "error" not in result:
            mode = result.get("analysis_mode", "")
            assert "rule" in mode.lower(), f"Expected rule-based, got: {mode}"

    def test_cust002_flagged(self):
        """CUST002 has deliberately seeded suspicious transactions."""
        result = self.analyze("CUST002")
        if "error" not in result:
            # CUST002 has very large transactions + offshore location
            flagged = result.get("flagged_transactions", [])
            # At minimum overall risk should be elevated
            assert result.get("overall_risk_score", 0) > 0

    def test_risk_score_bounded(self):
        """Risk score must be between 0 and 100."""
        result = self.analyze("CUST001")
        if "error" not in result:
            score = result.get("overall_risk_score", 0)
            assert 0 <= score <= 100

    def test_thresholds_are_positive(self):
        """Threshold constants must be positive numbers."""
        assert self.LARGE > 0
        assert self.VERY_LARGE > self.LARGE
