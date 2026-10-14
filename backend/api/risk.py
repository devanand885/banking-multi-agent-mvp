"""
backend/api/risk.py
====================
FastAPI router for risk and fraud analysis endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas import RiskAnalysisRequest, RiskAnalysisResponse
from backend.tools.risk_tools import analyze_transaction_risk

router = APIRouter(tags=["Risk & Fraud"])


@router.post("/risk/analyze", summary="Analyse customer transaction risk")
def analyze_risk(request: RiskAnalysisRequest):
    """
    Apply rule-based fraud detection to a customer's recent transactions.
    Returns flagged transactions with risk scores and reasons.

    NOTE: This is a deterministic RULE-BASED analysis — not a trained ML model.
    All data is simulated.
    """
    result = analyze_transaction_risk(
        customer_id=request.customer_id.upper(),
        limit=request.limit,
    )
    if "error" in result:
        raise HTTPException(
            status_code=404 if "not found" in result.get("error", "").lower() else 500,
            detail=result["error"],
        )
    return result
