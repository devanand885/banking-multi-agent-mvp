"""
backend/models.py
=================
SQLAlchemy ORM models for the banking database.
All data is entirely fictional and used for demonstration purposes only.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Enum as SAEnum,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ─────────────────────────────── Enums ────────────────────────────────────────

class AccountType(str, enum.Enum):
    SAVINGS = "savings"
    CURRENT = "current"
    FIXED_DEPOSIT = "fixed_deposit"


class AccountStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"


class TransactionType(str, enum.Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class TransactionCategory(str, enum.Enum):
    SALARY = "salary"
    TRANSFER = "transfer"
    PURCHASE = "purchase"
    ATM_WITHDRAWAL = "atm_withdrawal"
    ONLINE_PAYMENT = "online_payment"
    UTILITY = "utility"
    INVESTMENT = "investment"
    FOREIGN_TRANSFER = "foreign_transfer"
    UNKNOWN = "unknown"


class LoanStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    DEFAULTED = "defaulted"
    PENDING = "pending"


class LoanType(str, enum.Enum):
    HOME = "home"
    PERSONAL = "personal"
    AUTO = "auto"
    EDUCATION = "education"
    BUSINESS = "business"


class KYCStatus(str, enum.Enum):
    VERIFIED = "verified"
    PENDING = "pending"
    FAILED = "failed"
    EXPIRED = "expired"


class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─────────────────────────────── Models ───────────────────────────────────────

class Customer(Base):
    """Represents a fictional bank customer."""
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(20), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(200), unique=True, nullable=False)
    phone = Column(String(20), nullable=True)
    date_of_birth = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True, default="India")
    annual_income = Column(Float, nullable=True)
    credit_score = Column(Integer, nullable=True)
    employment_status = Column(String(50), nullable=True)
    employer_name = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationships
    accounts = relationship("Account", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship("Loan", back_populates="customer", cascade="all, delete-orphan")
    kyc_record = relationship("KYCRecord", back_populates="customer", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Customer {self.customer_id}: {self.first_name} {self.last_name}>"


class Account(Base):
    """Represents a fictional bank account."""
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(20), unique=True, index=True, nullable=False)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), nullable=False)
    account_type = Column(SAEnum(AccountType), nullable=False)
    account_number = Column(String(30), unique=True, nullable=False)
    balance = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="INR")
    status = Column(SAEnum(AccountStatus), default=AccountStatus.ACTIVE)
    interest_rate = Column(Float, nullable=True)
    opened_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    customer = relationship("Customer", back_populates="accounts")
    transactions = relationship("Transaction", back_populates="account", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Account {self.account_id}: {self.account_type} ₹{self.balance:,.2f}>"


class Transaction(Base):
    """Represents a fictional bank transaction."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(30), unique=True, index=True, nullable=False)
    account_id = Column(String(20), ForeignKey("accounts.account_id"), nullable=False)
    customer_id = Column(String(20), nullable=False)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)
    category = Column(SAEnum(TransactionCategory), default=TransactionCategory.UNKNOWN)
    amount = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    merchant = Column(String(200), nullable=True)
    location = Column(String(200), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    balance_after = Column(Float, nullable=True)
    is_flagged = Column(Boolean, default=False)
    flag_reason = Column(Text, nullable=True)
    reference_id = Column(String(50), nullable=True)

    # Relationships
    account = relationship("Account", back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction {self.transaction_id}: {self.transaction_type} ₹{self.amount:,.2f}>"


class Loan(Base):
    """Represents a fictional loan record."""
    __tablename__ = "loans"

    id = Column(Integer, primary_key=True, index=True)
    loan_id = Column(String(20), unique=True, index=True, nullable=False)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), nullable=False)
    loan_type = Column(SAEnum(LoanType), nullable=False)
    principal_amount = Column(Float, nullable=False)
    outstanding_balance = Column(Float, nullable=False)
    interest_rate = Column(Float, nullable=False)
    tenure_months = Column(Integer, nullable=False)
    monthly_emi = Column(Float, nullable=False)
    loan_status = Column(SAEnum(LoanStatus), default=LoanStatus.ACTIVE)
    disbursement_date = Column(DateTime, nullable=False)
    next_due_date = Column(DateTime, nullable=True)
    last_payment_date = Column(DateTime, nullable=True)
    missed_payments = Column(Integer, default=0)
    collateral = Column(String(200), nullable=True)
    purpose = Column(Text, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="loans")

    def __repr__(self) -> str:
        return f"<Loan {self.loan_id}: {self.loan_type} ₹{self.principal_amount:,.2f}>"


class KYCRecord(Base):
    """Represents KYC / compliance verification record for a customer."""
    __tablename__ = "kyc_records"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String(20), ForeignKey("customers.customer_id"), unique=True, nullable=False)
    kyc_status = Column(SAEnum(KYCStatus), default=KYCStatus.PENDING)
    pan_number = Column(String(20), nullable=True)
    aadhar_number = Column(String(20), nullable=True)
    passport_number = Column(String(20), nullable=True)
    address_proof = Column(String(200), nullable=True)
    photo_id_verified = Column(Boolean, default=False)
    address_verified = Column(Boolean, default=False)
    income_verified = Column(Boolean, default=False)
    pep_check = Column(Boolean, default=False)   # Politically Exposed Person
    sanctions_check = Column(Boolean, default=False)
    risk_rating = Column(SAEnum(RiskLevel), default=RiskLevel.LOW)
    verified_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="kyc_record")

    def __repr__(self) -> str:
        return f"<KYCRecord {self.customer_id}: {self.kyc_status}>"
