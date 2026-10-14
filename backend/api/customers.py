"""
backend/api/customers.py
=========================
FastAPI router for customer and account endpoints.
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Account, Customer, Transaction
from backend.schemas import AccountResponse, CustomerResponse, TransactionResponse

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("/{customer_id}", response_model=CustomerResponse, summary="Get customer profile")
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    """Retrieve the profile of a simulated bank customer."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id.upper()).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    return customer


@router.get("/{customer_id}/accounts", response_model=List[AccountResponse], summary="Get customer accounts")
def get_customer_accounts(customer_id: str, db: Session = Depends(get_db)):
    """Retrieve all simulated bank accounts belonging to a customer."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id.upper()).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    accounts = db.query(Account).filter(Account.customer_id == customer_id.upper()).all()
    return accounts


@router.get("/{customer_id}/transactions", response_model=List[TransactionResponse], summary="Get customer transactions")
def get_customer_transactions(
    customer_id: str,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Retrieve simulated recent transactions for a customer (default: last 20)."""
    customer = db.query(Customer).filter(Customer.customer_id == customer_id.upper()).first()
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer '{customer_id}' not found")
    transactions = (
        db.query(Transaction)
        .filter(Transaction.customer_id == customer_id.upper())
        .order_by(Transaction.timestamp.desc())
        .limit(min(limit, 200))
        .all()
    )
    return transactions
