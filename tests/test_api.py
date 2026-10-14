"""
tests/test_api.py
=================
Tests for the FastAPI REST API endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


class TestAPIEndpoints:
    """Tests covering FastAPI endpoints."""

    def test_root_endpoint(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "disclaimer" in data

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data.get("status") == "ok"
        assert "llm_mode" in data
        assert "database" in data

    def test_get_customer_profile(self, client):
        response = client.get("/customers/CUST001")
        assert response.status_code == 200
        data = response.json()
        assert data.get("customer_id") == "CUST001"
        assert "first_name" in data

    def test_get_unknown_customer_returns_404(self, client):
        response = client.get("/customers/CUST999_UNKNOWN")
        assert response.status_code == 404

    def test_calculate_emi_endpoint(self, client):
        payload = {
            "principal": 300000.0,
            "annual_interest_rate": 10.0,
            "tenure_months": 36,
        }
        response = client.post("/loans/emi", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "monthly_emi" in data
        assert data["monthly_emi"] > 0
        assert "total_interest" in data

    def test_calculate_emi_invalid_input(self, client):
        payload = {
            "principal": -5000.0,
            "annual_interest_rate": 10.0,
            "tenure_months": 36,
        }
        response = client.post("/loans/emi", json=payload)
        assert response.status_code in (400, 422)

    def test_chat_endpoint_balance_query(self, client):
        payload = {
            "message": "Show account balance for CUST001",
            "customer_id": "CUST001",
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "intent" in data
        assert "answer" in data
        assert "agent_traces" in data

    def test_chat_endpoint_emi_query(self, client):
        payload = {
            "message": "Calculate EMI for 500000 at 9.5% for 60 months",
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "emi_calculation"
        assert "credit_agent" in data.get("agents_invoked", [])
