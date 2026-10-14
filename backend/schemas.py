"""
backend/schemas.py
==================
Pydantic schemas for API request/response validation.
These are separate from the SQLAlchemy ORM models.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─────────────────────────────── Customer Schemas ─────────────────────────────

class CustomerBase(BaseModel):
    customer_id: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "India"
    annual_income: Optional[float] = None
    credit_score: Optional[int] = None
    employment_status: Optional[str] = None
    employer_name: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────── Account Schemas ──────────────────────────────

class AccountBase(BaseModel):
    account_id: str
    customer_id: str
    account_type: str
    account_number: str
    balance: float
    currency: str = "INR"
    status: str
    interest_rate: Optional[float] = None


class AccountResponse(AccountBase):
    id: int
    opened_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────── Transaction Schemas ──────────────────────────

class TransactionBase(BaseModel):
    transaction_id: str
    account_id: str
    customer_id: str
    transaction_type: str
    category: str
    amount: float
    description: Optional[str] = None
    merchant: Optional[str] = None
    location: Optional[str] = None
    timestamp: datetime
    balance_after: Optional[float] = None
    is_flagged: bool = False
    flag_reason: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: int
    reference_id: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────── Loan Schemas ─────────────────────────────────

class LoanBase(BaseModel):
    loan_id: str
    customer_id: str
    loan_type: str
    principal_amount: float
    outstanding_balance: float
    interest_rate: float
    tenure_months: int
    monthly_emi: float
    loan_status: str
    missed_payments: int = 0


class LoanResponse(LoanBase):
    id: int
    disbursement_date: datetime
    next_due_date: Optional[datetime] = None
    last_payment_date: Optional[datetime] = None
    collateral: Optional[str] = None
    purpose: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────── KYC Schemas ──────────────────────────────────

class KYCResponse(BaseModel):
    id: int
    customer_id: str
    kyc_status: str
    pan_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    passport_number: Optional[str] = None
    address_proof: Optional[str] = None
    photo_id_verified: bool = False
    address_verified: bool = False
    income_verified: bool = False
    pep_check: bool = False
    sanctions_check: bool = False
    risk_rating: str
    verified_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None

    model_config = {"from_attributes": True}


# ─────────────────────────────── Risk Analysis Schemas ────────────────────────

class RiskAnalysisRequest(BaseModel):
    customer_id: str
    limit: int = Field(default=50, ge=1, le=200)


class FlaggedTransaction(BaseModel):
    transaction_id: str
    amount: float
    description: Optional[str]
    timestamp: datetime
    risk_level: str
    reasons: List[str]
    risk_score: float


class RiskAnalysisResponse(BaseModel):
    customer_id: str
    overall_risk_level: str
    overall_risk_score: float
    total_transactions_checked: int
    flagged_transactions: List[FlaggedTransaction]
    summary: str
    analysis_mode: str = "rule-based"


# ─────────────────────────────── Loan Eligibility Schemas ─────────────────────

class LoanEligibilityRequest(BaseModel):
    customer_id: str
    requested_amount: float = Field(gt=0)
    loan_type: str = "personal"
    tenure_months: int = Field(default=36, ge=1, le=360)


class CriterionResult(BaseModel):
    criterion: str
    required: str
    actual: str
    passed: bool


class LoanEligibilityResponse(BaseModel):
    customer_id: str
    requested_amount: float
    loan_type: str
    is_eligible: bool
    criteria_results: List[CriterionResult]
    max_eligible_amount: Optional[float] = None
    recommended_tenure_months: Optional[int] = None
    estimated_emi: Optional[float] = None
    decision_reason: str
    disclaimer: str = (
        "This is a simulated assessment for demonstration purposes only. "
        "It does not constitute an actual bank approval or credit offer."
    )


# ─────────────────────────────── EMI Calculation Schemas ──────────────────────

class EMIRequest(BaseModel):
    principal: float = Field(gt=0, description="Loan principal amount in INR")
    annual_interest_rate: float = Field(ge=0, le=100, description="Annual interest rate in percent")
    tenure_months: int = Field(ge=1, le=360, description="Loan tenure in months")


class EMIResponse(BaseModel):
    principal: float
    annual_interest_rate: float
    tenure_months: float
    monthly_emi: float
    total_payment: float
    total_interest: float
    formula_used: str


# ─────────────────────────────── Chat / Orchestrator Schemas ──────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    customer_id: Optional[str] = None
    session_id: Optional[str] = None


class AgentTrace(BaseModel):
    agent_name: str
    tools_called: List[str]
    outcome: str
    duration_ms: float


class ChatResponse(BaseModel):
    intent: str
    answer: str
    agents_invoked: List[str]
    agent_traces: List[AgentTrace]
    tools_executed: List[str]
    structured_data: Optional[Dict[str, Any]] = None
    warnings: List[str] = []
    errors: List[str] = []
    llm_mode: str
    execution_duration_ms: float
    session_id: Optional[str] = None


# ─────────────────────────────── Health Schema ────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    llm_mode: str
    database: str
    timestamp: datetime
