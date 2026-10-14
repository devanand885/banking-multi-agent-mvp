"""
backend/api/loans.py
=====================
FastAPI router for loan, eligibility, and EMI endpoints.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Customer, Loan
from backend.schemas import (
    EMIRequest, EMIResponse,
    LoanEligibilityRequest, LoanEligibilityResponse,
    LoanResponse,
)
from backend.tools.loan_tools import calculate_emi, check_loan_eligibility

router = APIRouter(tags=["Loans & Credit"])


@router.get("/customers/{customer_id}/loans", response_model=List[LoanResponse], summary="Get customer loans")
def get_customer_loans(customer_id: str, db: Session = Depends(get_db)):
    """Retrieve all simulated loan records for a customer."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id.upper()).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    loans = db.query(Loan).filter(Loan.customer_id == customer_id.upper()).all()
    return loans


@router.post("/loans/emi", response_model=EMIResponse, summary="Calculate EMI")
def compute_emi(request: EMIRequest):
    """
    Calculate the Equated Monthly Instalment (EMI) using the standard reducing-balance formula.

    Formula:  M = P × r × (1+r)^n / ((1+r)^n − 1)
    where r = annual_rate / 12 / 100, n = tenure_months

    Zero-interest special case:  M = P / n
    """
    result = calculate_emi(
        principal=request.principal,
        annual_interest_rate=request.annual_interest_rate,
        tenure_months=request.tenure_months,
    )
    if "error" in result:
        raise HTTPException(status_code=422, detail=result["error"])
    return result


@router.post("/loans/eligibility", response_model=LoanEligibilityResponse, summary="Check loan eligibility")
def loan_eligibility(request: LoanEligibilityRequest):
    """
    Check whether a simulated customer meets the sample loan eligibility criteria.

    DISCLAIMER: This is a simulated assessment for demonstration only.
    It does NOT constitute an actual bank approval or credit offer.
    """
    result = check_loan_eligibility(
        customer_id=request.customer_id.upper(),
        requested_amount=request.requested_amount,
        loan_type=request.loan_type,
        tenure_months=request.tenure_months,
    )
    if "error" in result:
        raise HTTPException(
            status_code=404 if "not found" in result["error"].lower() else 422,
            detail=result["error"],
        )
    return result
