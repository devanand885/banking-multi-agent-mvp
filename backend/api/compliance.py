"""
backend/api/compliance.py
==========================
FastAPI router for KYC and compliance endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from backend.schemas import KYCResponse
from backend.tools.loan_tools import get_kyc_status

router = APIRouter(tags=["Compliance & KYC"])


@router.get("/customers/{customer_id}/kyc", summary="Get KYC status")
def get_kyc(customer_id: str):
    """
    Retrieve simulated KYC / compliance status for a customer.
    Returns verification status, missing fields, and risk rating.

    DISCLAIMER: This is a simulated check — not a real AML/KYC system.
    """
    result = get_kyc_status(customer_id.upper())
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result
