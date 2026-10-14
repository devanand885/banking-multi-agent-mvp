"""
backend/tools/banking_tools.py
==============================
Core banking tools — customer lookup, account info, transaction retrieval.
These functions are registered in the tool registry and called by agents.
All data is read from the SQLite database (simulated banking records).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models import Account, Customer, Transaction

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────────────

def _get_db() -> Session:
    return SessionLocal()


def _customer_to_dict(c: Customer) -> Dict[str, Any]:
    return {
        "customer_id": c.customer_id,
        "first_name": c.first_name,
        "last_name": c.last_name,
        "full_name": f"{c.first_name} {c.last_name}",
        "email": c.email,
        "phone": c.phone,
        "date_of_birth": c.date_of_birth,
        "address": c.address,
        "city": c.city,
        "country": c.country,
        "annual_income": c.annual_income,
        "credit_score": c.credit_score,
        "employment_status": c.employment_status,
        "employer_name": c.employer_name,
        "is_active": c.is_active,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def _account_to_dict(a: Account) -> Dict[str, Any]:
    return {
        "account_id": a.account_id,
        "customer_id": a.customer_id,
        "account_type": a.account_type.value if hasattr(a.account_type, "value") else str(a.account_type),
        "account_number": a.account_number,
        "balance": a.balance,
        "currency": a.currency,
        "status": a.status.value if hasattr(a.status, "value") else str(a.status),
        "interest_rate": a.interest_rate,
        "opened_at": a.opened_at.isoformat() if a.opened_at else None,
    }


def _transaction_to_dict(t: Transaction) -> Dict[str, Any]:
    return {
        "transaction_id": t.transaction_id,
        "account_id": t.account_id,
        "customer_id": t.customer_id,
        "transaction_type": t.transaction_type.value if hasattr(t.transaction_type, "value") else str(t.transaction_type),
        "category": t.category.value if hasattr(t.category, "value") else str(t.category),
        "amount": t.amount,
        "description": t.description,
        "merchant": t.merchant,
        "location": t.location,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
        "balance_after": t.balance_after,
        "is_flagged": t.is_flagged,
        "flag_reason": t.flag_reason,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Customer Tools
# ──────────────────────────────────────────────────────────────────────────────

def get_customer_profile(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve a customer's profile from the database.
    Returns an error dict if the customer is not found.
    """
    db = _get_db()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": f"Customer '{customer_id}' not found", "customer_id": customer_id}
        return {"success": True, "customer": _customer_to_dict(customer)}
    except Exception as exc:
        logger.error("get_customer_profile error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()


def get_customer_accounts(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve all accounts for a customer.
    """
    db = _get_db()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": f"Customer '{customer_id}' not found", "customer_id": customer_id}

        accounts = db.query(Account).filter(Account.customer_id == customer_id).all()
        total_balance = sum(a.balance for a in accounts)
        return {
            "success": True,
            "customer_id": customer_id,
            "accounts": [_account_to_dict(a) for a in accounts],
            "total_balance": total_balance,
            "account_count": len(accounts),
        }
    except Exception as exc:
        logger.error("get_customer_accounts error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()


def get_customer_transactions(customer_id: str, limit: int = 20) -> Dict[str, Any]:
    """
    Retrieve recent transactions for a customer (across all accounts).
    """
    db = _get_db()
    try:
        customer = db.query(Customer).filter(Customer.customer_id == customer_id).first()
        if not customer:
            return {"error": f"Customer '{customer_id}' not found", "customer_id": customer_id}

        transactions = (
            db.query(Transaction)
            .filter(Transaction.customer_id == customer_id)
            .order_by(Transaction.timestamp.desc())
            .limit(limit)
            .all()
        )
        return {
            "success": True,
            "customer_id": customer_id,
            "transactions": [_transaction_to_dict(t) for t in transactions],
            "transaction_count": len(transactions),
        }
    except Exception as exc:
        logger.error("get_customer_transactions error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()


def get_account_details(account_id: str) -> Dict[str, Any]:
    """
    Retrieve details of a specific account.
    """
    db = _get_db()
    try:
        account = db.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return {"error": f"Account '{account_id}' not found", "account_id": account_id}
        return {"success": True, "account": _account_to_dict(account)}
    except Exception as exc:
        logger.error("get_account_details error: %s", exc)
        return {"error": str(exc), "account_id": account_id}
    finally:
        db.close()
