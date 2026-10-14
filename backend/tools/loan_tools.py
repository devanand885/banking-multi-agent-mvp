"""
backend/tools/loan_tools.py
============================
Loan and credit tools — eligibility checks, EMI calculation, loan retrieval.

EMI Formula (Reducing-Balance / Standard):
    M = P × r × (1 + r)^n  /  ((1 + r)^n − 1)
    where:
      P = principal amount
      r = monthly interest rate  (annual rate / 12 / 100)
      n = tenure in months

Special case: r = 0 → M = P / n
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List, Optional

from backend.database import SessionLocal
from backend.models import Customer, Loan, LoanStatus

logger = logging.getLogger(__name__)

# ──────────────────────────────── Eligibility Criteria ────────────────────────
# These are configurable sample lending criteria — not actual bank policy.

ELIGIBILITY_CRITERIA = {
    "min_credit_score": 650,
    "min_annual_income": 300_000,   # ₹3 lakh p.a.
    "max_debt_to_income_ratio": 0.5,
    "employment_statuses_allowed": ["employed", "self_employed"],
    "max_loan_to_income_multiple": 10,
    "min_kyc_status": "verified",
}

INTEREST_RATES = {
    "personal": 13.5,
    "home": 8.5,
    "auto": 9.0,
    "education": 7.5,
    "business": 14.0,
}


def _loan_to_dict(loan: Loan) -> Dict[str, Any]:
    return {
        "loan_id": loan.loan_id,
        "customer_id": loan.customer_id,
        "loan_type": loan.loan_type.value if hasattr(loan.loan_type, "value") else str(loan.loan_type),
        "principal_amount": loan.principal_amount,
        "outstanding_balance": loan.outstanding_balance,
        "interest_rate": loan.interest_rate,
        "tenure_months": loan.tenure_months,
        "monthly_emi": loan.monthly_emi,
        "loan_status": loan.loan_status.value if hasattr(loan.loan_status, "value") else str(loan.loan_status),
        "disbursement_date": loan.disbursement_date.isoformat() if loan.disbursement_date else None,
        "next_due_date": loan.next_due_date.isoformat() if loan.next_due_date else None,
        "last_payment_date": loan.last_payment_date.isoformat() if loan.last_payment_date else None,
        "missed_payments": loan.missed_payments,
        "collateral": loan.collateral,
        "purpose": loan.purpose,
    }


# ──────────────────────────────── Loan Retrieval ──────────────────────────────

def get_customer_loans(customer_id: str) -> Dict[str, Any]:
    """Retrieve all loans for a customer."""
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": f"Customer '{customer_id}' not found", "customer_id": customer_id}

        loans = db.query(Loan).filter(Loan.customer_id == customer_id).all()
        active_loans = [l for l in loans if l.loan_status == LoanStatus.ACTIVE]
        total_outstanding = sum(l.outstanding_balance for l in active_loans)
        total_emi = sum(l.monthly_emi for l in active_loans)

        return {
            "success": True,
            "customer_id": customer_id,
            "loans": [_loan_to_dict(l) for l in loans],
            "loan_count": len(loans),
            "active_loan_count": len(active_loans),
            "total_outstanding_balance": total_outstanding,
            "total_monthly_emi": total_emi,
        }
    except Exception as exc:
        logger.error("get_customer_loans error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()


# ──────────────────────────────── EMI Calculation ─────────────────────────────

def calculate_emi(principal: float, annual_interest_rate: float, tenure_months: int) -> Dict[str, Any]:
    """
    Calculate EMI using the standard reducing-balance formula.

    Args:
        principal: Loan principal in INR
        annual_interest_rate: Annual interest rate as a percentage (e.g. 10 for 10%)
        tenure_months: Loan tenure in months

    Returns:
        Dictionary with monthly_emi, total_payment, total_interest, formula description
    """
    if principal <= 0:
        return {"error": "Principal must be greater than zero"}
    if tenure_months <= 0:
        return {"error": "Tenure must be at least 1 month"}
    if annual_interest_rate < 0 or annual_interest_rate > 100:
        return {"error": "Interest rate must be between 0% and 100%"}

    r = annual_interest_rate / 12 / 100  # monthly interest rate

    if r == 0:
        # Zero-interest loan — simple division
        monthly_emi = principal / tenure_months
        formula = "Zero-interest: EMI = P / n"
    else:
        # Standard reducing-balance formula
        monthly_emi = principal * r * (1 + r) ** tenure_months / ((1 + r) ** tenure_months - 1)
        formula = "Reducing-balance: EMI = P × r × (1+r)^n / ((1+r)^n − 1)"

    total_payment = monthly_emi * tenure_months
    total_interest = total_payment - principal

    return {
        "success": True,
        "principal": round(principal, 2),
        "annual_interest_rate": annual_interest_rate,
        "tenure_months": tenure_months,
        "monthly_emi": round(monthly_emi, 2),
        "total_payment": round(total_payment, 2),
        "total_interest": round(total_interest, 2),
        "formula_used": formula,
    }


# ──────────────────────────────── Eligibility Check ───────────────────────────

def check_loan_eligibility(
    customer_id: str,
    requested_amount: float,
    loan_type: str = "personal",
    tenure_months: int = 36,
) -> Dict[str, Any]:
    """
    Check whether a customer meets the sample lending criteria for a loan.
    This is a SIMULATED assessment — not an actual bank approval.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": f"Customer '{customer_id}' not found", "customer_id": customer_id}

        # KYC check
        kyc = customer.kyc_record
        kyc_status = kyc.kyc_status.value if kyc else "missing"

        # Existing loan obligations
        active_loans = db.query(Loan).filter(
            Loan.customer_id == customer_id,
            Loan.loan_status == LoanStatus.ACTIVE,
        ).all()
        monthly_obligations = sum(l.monthly_emi for l in active_loans)
        annual_obligations = monthly_obligations * 12
        annual_income = customer.annual_income or 0

        # Compute estimated EMI for requested loan
        rate = INTEREST_RATES.get(loan_type.lower(), 13.5)
        emi_result = calculate_emi(requested_amount, rate, tenure_months)
        estimated_emi = emi_result.get("monthly_emi", 0)
        total_monthly_obligations = monthly_obligations + estimated_emi
        dti_ratio = (total_monthly_obligations * 12) / annual_income if annual_income else 999

        # Evaluate criteria
        criteria: List[Dict[str, Any]] = []

        def add_criterion(name: str, required: str, actual: str, passed: bool):
            criteria.append({"criterion": name, "required": required, "actual": actual, "passed": passed})

        # 1. Credit score
        cs = customer.credit_score or 0
        add_criterion(
            "Minimum credit score",
            f">= {ELIGIBILITY_CRITERIA['min_credit_score']}",
            str(cs) if cs else "Not available",
            cs >= ELIGIBILITY_CRITERIA["min_credit_score"],
        )

        # 2. Annual income
        add_criterion(
            "Minimum annual income",
            f">= ₹{ELIGIBILITY_CRITERIA['min_annual_income']:,.0f}",
            f"₹{annual_income:,.0f}" if annual_income else "Not available",
            annual_income >= ELIGIBILITY_CRITERIA["min_annual_income"],
        )

        # 3. Employment status
        emp = customer.employment_status or "unknown"
        add_criterion(
            "Employment status",
            f"One of: {', '.join(ELIGIBILITY_CRITERIA['employment_statuses_allowed'])}",
            emp,
            emp in ELIGIBILITY_CRITERIA["employment_statuses_allowed"],
        )

        # 4. Debt-to-income ratio
        add_criterion(
            "Debt-to-income ratio",
            f"<= {ELIGIBILITY_CRITERIA['max_debt_to_income_ratio'] * 100:.0f}%",
            f"{dti_ratio * 100:.1f}%" if annual_income else "Cannot compute (no income data)",
            dti_ratio <= ELIGIBILITY_CRITERIA["max_debt_to_income_ratio"],
        )

        # 5. Loan-to-income multiple
        lti = requested_amount / annual_income if annual_income else 999
        add_criterion(
            "Loan-to-income multiple",
            f"<= {ELIGIBILITY_CRITERIA['max_loan_to_income_multiple']}x annual income",
            f"{lti:.1f}x" if annual_income else "Cannot compute",
            lti <= ELIGIBILITY_CRITERIA["max_loan_to_income_multiple"],
        )

        # 6. KYC
        add_criterion(
            "KYC status",
            ELIGIBILITY_CRITERIA["min_kyc_status"],
            kyc_status,
            kyc_status == ELIGIBILITY_CRITERIA["min_kyc_status"],
        )

        all_passed = all(c["passed"] for c in criteria)
        failed = [c for c in criteria if not c["passed"]]

        max_eligible = (
            min(
                annual_income * ELIGIBILITY_CRITERIA["max_loan_to_income_multiple"],
                annual_income * (1 - ELIGIBILITY_CRITERIA["max_debt_to_income_ratio"]) / (rate / 12 / 100 + 1e-9) * 0.4,
            )
            if all_passed and annual_income
            else None
        )

        decision_reason = (
            f"All {len(criteria)} eligibility criteria passed. Loan appears eligible for processing."
            if all_passed
            else f"{len(failed)} criterion/criteria not met: {', '.join(c['criterion'] for c in failed)}."
        )

        return {
            "success": True,
            "customer_id": customer_id,
            "customer_name": f"{customer.first_name} {customer.last_name}",
            "requested_amount": requested_amount,
            "loan_type": loan_type,
            "tenure_months": tenure_months,
            "is_eligible": all_passed,
            "criteria_results": criteria,
            "estimated_emi": estimated_emi,
            "interest_rate_used": rate,
            "max_eligible_amount": round(max_eligible, 2) if max_eligible else None,
            "decision_reason": decision_reason,
            "disclaimer": (
                "This is a simulated assessment for demonstration purposes only. "
                "It does not constitute an actual bank approval or credit offer."
            ),
        }
    except Exception as exc:
        logger.error("check_loan_eligibility error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()


# ──────────────────────────────── KYC / Compliance Tools ──────────────────────

def get_kyc_status(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve the KYC record and identify any missing required fields.
    """
    db = SessionLocal()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": f"Customer '{customer_id}' not found", "customer_id": customer_id}

        kyc = customer.kyc_record

        # Fields required for full KYC
        required_customer_fields = {
            "phone": customer.phone,
            "date_of_birth": customer.date_of_birth,
            "address": customer.address,
            "annual_income": customer.annual_income,
            "credit_score": customer.credit_score,
        }
        required_kyc_fields = {}
        if kyc:
            required_kyc_fields = {
                "pan_number": kyc.pan_number,
                "aadhar_number": kyc.aadhar_number,
                "address_proof": kyc.address_proof,
            }

        missing_customer = [k for k, v in required_customer_fields.items() if not v]
        missing_kyc = [k for k, v in required_kyc_fields.items() if not v]
        all_missing = missing_customer + missing_kyc

        # Verification status details
        verifications = {}
        if kyc:
            verifications = {
                "photo_id_verified": kyc.photo_id_verified,
                "address_verified": kyc.address_verified,
                "income_verified": kyc.income_verified,
                "pep_check_completed": kyc.pep_check,
                "sanctions_check_completed": kyc.sanctions_check,
            }

        return {
            "success": True,
            "customer_id": customer_id,
            "customer_name": f"{customer.first_name} {customer.last_name}",
            "kyc_status": kyc.kyc_status.value if kyc else "no_record",
            "risk_rating": kyc.risk_rating.value if kyc else "unknown",
            "verified_at": kyc.verified_at.isoformat() if kyc and kyc.verified_at else None,
            "expires_at": kyc.expires_at.isoformat() if kyc and kyc.expires_at else None,
            "missing_fields": all_missing,
            "missing_customer_fields": missing_customer,
            "missing_kyc_fields": missing_kyc,
            "verifications": verifications,
            "notes": kyc.notes if kyc else "No KYC record found",
            "is_complete": len(all_missing) == 0,
            "disclaimer": "Simulated KYC verification — not a production AML/KYC compliance system.",
        }
    except Exception as exc:
        logger.error("get_kyc_status error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()
