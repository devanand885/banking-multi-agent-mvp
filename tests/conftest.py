"""
tests/conftest.py
==================
Shared pytest fixtures for the banking assistant test suite.
Uses an in-memory SQLite database to avoid touching the real database.
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Project root on path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.models import (
    Base, Account, AccountStatus, AccountType, Customer,
    KYCRecord, KYCStatus, Loan, LoanStatus, LoanType,
    RiskLevel, Transaction, TransactionCategory, TransactionType,
)


@pytest.fixture(scope="session")
def engine():
    """Create an in-memory SQLite engine for tests."""
    return create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})


@pytest.fixture(scope="session")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def db(engine, tables):
    """Yield a fresh database session for each test, rolled back afterwards."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def sample_customer(db) -> Customer:
    c = Customer(
        customer_id="TESTCUST001",
        first_name="Test",
        last_name="User",
        email="test@example.com",
        phone="+91-9999999999",
        date_of_birth="1990-01-01",
        address="123 Test Street",
        city="Testville",
        country="India",
        annual_income=900000.0,
        credit_score=720,
        employment_status="employed",
        employer_name="Test Corp",
        is_active=True,
    )
    db.add(c)
    db.flush()
    return c


@pytest.fixture
def sample_account(db, sample_customer) -> Account:
    a = Account(
        account_id="TESTACC001",
        customer_id="TESTCUST001",
        account_type=AccountType.SAVINGS,
        account_number="SB99999900001",
        balance=150000.0,
        currency="INR",
        status=AccountStatus.ACTIVE,
        interest_rate=3.5,
        opened_at=datetime(2020, 1, 1),
    )
    db.add(a)
    db.flush()
    return a


@pytest.fixture
def sample_transactions(db, sample_account) -> list:
    now = datetime.utcnow()
    txns = [
        Transaction(
            transaction_id="TESTTXN001",
            account_id="TESTACC001",
            customer_id="TESTCUST001",
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.SALARY,
            amount=75000.0,
            description="Salary",
            location="Testville",
            timestamp=now - timedelta(days=3),
            balance_after=150000.0,
        ),
        Transaction(
            transaction_id="TESTTXN002",
            account_id="TESTACC001",
            customer_id="TESTCUST001",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.PURCHASE,
            amount=5000.0,
            description="Shopping",
            location="Testville",
            timestamp=now - timedelta(days=5),
            balance_after=75000.0,
        ),
    ]
    db.add_all(txns)
    db.flush()
    return txns


@pytest.fixture
def sample_loan(db, sample_customer) -> Loan:
    l = Loan(
        loan_id="TESTLOAN001",
        customer_id="TESTCUST001",
        loan_type=LoanType.PERSONAL,
        principal_amount=300000.0,
        outstanding_balance=200000.0,
        interest_rate=13.5,
        tenure_months=36,
        monthly_emi=10000.0,
        loan_status=LoanStatus.ACTIVE,
        disbursement_date=datetime(2023, 1, 1),
    )
    db.add(l)
    db.flush()
    return l


@pytest.fixture
def sample_kyc(db, sample_customer) -> KYCRecord:
    k = KYCRecord(
        customer_id="TESTCUST001",
        kyc_status=KYCStatus.VERIFIED,
        pan_number="TEST12345F",
        aadhar_number="1234-5678-9999",
        address_proof="Utility Bill",
        photo_id_verified=True,
        address_verified=True,
        income_verified=True,
        pep_check=True,
        sanctions_check=True,
        risk_rating=RiskLevel.LOW,
        verified_at=datetime(2023, 6, 1),
    )
    db.add(k)
    db.flush()
    return k
