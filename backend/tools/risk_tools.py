"""
backend/tools/risk_tools.py
============================
Risk and fraud analysis tools.

IMPORTANT DISCLAIMER:
The fraud detection in this module is entirely RULE-BASED.
No machine-learning model has been trained. Rules are transparent,
configurable, and clearly documented. This is described accurately
in the README and all output messages.

Rules implemented:
  R1  Large transaction: amount > LARGE_TXN_THRESHOLD
  R2  Very large transaction: amount > VERY_LARGE_TXN_THRESHOLD
  R3  Structuring pattern: two+ transactions just below reporting limits
  R4  Offshore / high-risk location
  R5  Unknown-source large credit (category == UNKNOWN and amount > threshold)
  R6  Multiple locations within short time window (rapid geo-change)
  R7  Transaction outside normal hours (00:00–05:00 local time)
  R8  High transaction frequency: many transactions in a short period
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from backend.database import SessionLocal
from backend.models import Customer, Transaction, TransactionCategory, TransactionType

logger = logging.getLogger(__name__)

# ──────────────────────────────── Configurable Thresholds ─────────────────────
LARGE_TXN_THRESHOLD = 100_000      # ₹ 1 lakh
VERY_LARGE_TXN_THRESHOLD = 400_000  # ₹ 4 lakh
STRUCTURING_WINDOW_HOURS = 24
STRUCTURING_LIMIT = 50_000         # Transactions just below this get flagged
STRUCTURING_TOLERANCE = 3_000      # Within ₹3 k of limit = suspicious
RAPID_GEO_WINDOW_HOURS = 4
HIGH_FREQ_WINDOW_HOURS = 24
HIGH_FREQ_COUNT = 5

OFFSHORE_LOCATIONS = {
    "grand cayman", "cayman islands", "british virgin islands",
    "bermuda", "panama", "seychelles", "isle of man",
}

RISK_WEIGHTS = {
    "very_large_transaction": 40,
    "large_transaction": 20,
    "offshore_location": 35,
    "structuring": 30,
    "unknown_large_credit": 25,
    "rapid_geo_change": 20,
    "off_hours": 10,
    "high_frequency": 15,
}


def _score_to_level(score: float) -> str:
    if score >= 70:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    return "low"


def _transaction_to_dict(t: Transaction) -> Dict[str, Any]:
    return {
        "transaction_id": t.transaction_id,
        "account_id": t.account_id,
        "transaction_type": t.transaction_type.value if hasattr(t.transaction_type, "value") else str(t.transaction_type),
        "category": t.category.value if hasattr(t.category, "value") else str(t.category),
        "amount": t.amount,
        "description": t.description,
        "merchant": t.merchant,
        "location": t.location,
        "timestamp": t.timestamp.isoformat() if t.timestamp else None,
    }


def analyze_transaction_risk(customer_id: str, limit: int = 50) -> Dict[str, Any]:
    """
    Apply rule-based fraud detection to a customer's recent transactions.
    Returns flagged transactions with reasons and a risk score.

    NOTE: This is a deterministic rule-based system — not a trained ML model.
    """
    db = SessionLocal()
    try:
        # Verify customer exists
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

        if not transactions:
            return {
                "success": True,
                "customer_id": customer_id,
                "overall_risk_level": "low",
                "overall_risk_score": 0.0,
                "total_transactions_checked": 0,
                "flagged_transactions": [],
                "summary": "No transactions found to analyse.",
                "analysis_mode": "rule-based",
            }

        flagged: List[Dict[str, Any]] = []
        txn_scores: Dict[str, float] = {}
        txn_reasons: Dict[str, List[str]] = defaultdict(list)

        # ── R1 / R2 — Large transactions ─────────────────────────────────
        for t in transactions:
            if t.amount > VERY_LARGE_TXN_THRESHOLD:
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["very_large_transaction"]
                txn_reasons[t.transaction_id].append(
                    f"Very large transaction: ₹{t.amount:,.2f} (threshold ₹{VERY_LARGE_TXN_THRESHOLD:,})"
                )
            elif t.amount > LARGE_TXN_THRESHOLD:
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["large_transaction"]
                txn_reasons[t.transaction_id].append(
                    f"Large transaction: ₹{t.amount:,.2f} (threshold ₹{LARGE_TXN_THRESHOLD:,})"
                )

        # ── R4 — Offshore location ────────────────────────────────────────
        for t in transactions:
            if t.location and t.location.lower() in OFFSHORE_LOCATIONS:
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["offshore_location"]
                txn_reasons[t.transaction_id].append(
                    f"Offshore/high-risk location: {t.location}"
                )

        # ── R5 — Unknown large credit ─────────────────────────────────────
        for t in transactions:
            if (
                t.category == TransactionCategory.UNKNOWN
                and t.transaction_type == TransactionType.CREDIT
                and t.amount > LARGE_TXN_THRESHOLD
            ):
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["unknown_large_credit"]
                txn_reasons[t.transaction_id].append(
                    f"Large credit from unknown source: ₹{t.amount:,.2f}"
                )

        # ── R3 — Structuring (multiple transactions just below reporting limit) ─
        utc_now = datetime.now(timezone.utc).replace(tzinfo=None)
        debit_amounts_within_window: List[Transaction] = [
            t for t in transactions
            if (
                t.transaction_type == TransactionType.DEBIT
                and t.timestamp >= utc_now - timedelta(hours=STRUCTURING_WINDOW_HOURS)
                and (STRUCTURING_LIMIT - STRUCTURING_TOLERANCE) <= t.amount <= STRUCTURING_LIMIT
            )
        ]
        if len(debit_amounts_within_window) >= 2:
            for t in debit_amounts_within_window:
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["structuring"]
                txn_reasons[t.transaction_id].append(
                    f"Potential structuring: ₹{t.amount:,.2f} just below reporting limit "
                    f"(₹{STRUCTURING_LIMIT:,}) with {len(debit_amounts_within_window)} similar transactions in 24 h"
                )

        # ── R6 — Rapid geo-change ─────────────────────────────────────────
        sorted_txns = sorted(transactions, key=lambda t: t.timestamp)
        for i in range(1, len(sorted_txns)):
            prev = sorted_txns[i - 1]
            curr = sorted_txns[i]
            if (
                prev.location and curr.location
                and prev.location.lower() != curr.location.lower()
                and (curr.timestamp - prev.timestamp) <= timedelta(hours=RAPID_GEO_WINDOW_HOURS)
            ):
                txn_scores[curr.transaction_id] = txn_scores.get(curr.transaction_id, 0) + RISK_WEIGHTS["rapid_geo_change"]
                txn_reasons[curr.transaction_id].append(
                    f"Rapid location change: {prev.location} → {curr.location} within "
                    f"{(curr.timestamp - prev.timestamp).seconds // 3600 + 1} hour(s)"
                )

        # ── R7 — Off-hours transactions (00:00–05:00 UTC) ─────────────────
        for t in transactions:
            if t.timestamp and 0 <= t.timestamp.hour < 5:
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["off_hours"]
                txn_reasons[t.transaction_id].append(
                    f"Off-hours transaction at {t.timestamp.strftime('%H:%M')} UTC"
                )

        # ── R8 — High frequency ───────────────────────────────────────────
        recent_window_start = utc_now - timedelta(hours=HIGH_FREQ_WINDOW_HOURS)
        recent_txns = [t for t in transactions if t.timestamp >= recent_window_start]
        if len(recent_txns) >= HIGH_FREQ_COUNT:
            for t in recent_txns:
                txn_scores[t.transaction_id] = txn_scores.get(t.transaction_id, 0) + RISK_WEIGHTS["high_frequency"]
                txn_reasons[t.transaction_id].append(
                    f"High transaction frequency: {len(recent_txns)} transactions in 24 hours"
                )

        # ── Compile results ───────────────────────────────────────────────
        for t in transactions:
            score = txn_scores.get(t.transaction_id, 0.0)
            if score > 0:
                flagged.append({
                    "transaction_id": t.transaction_id,
                    "amount": t.amount,
                    "description": t.description,
                    "timestamp": t.timestamp.isoformat() if t.timestamp else None,
                    "risk_level": _score_to_level(score),
                    "reasons": txn_reasons[t.transaction_id],
                    "risk_score": min(score, 100),
                    "transaction_details": _transaction_to_dict(t),
                })

        flagged.sort(key=lambda x: x["risk_score"], reverse=True)

        overall_score = min(max((s for s in txn_scores.values()), default=0), 100)
        overall_level = _score_to_level(overall_score)

        summary = (
            f"Analysed {len(transactions)} transactions using rule-based fraud detection. "
            f"Found {len(flagged)} suspicious transaction(s). "
            f"Overall risk level: {overall_level.upper()} (score: {overall_score:.0f}/100). "
            "NOTE: This is a simulated rule-based analysis — not a trained ML classifier."
        )

        return {
            "success": True,
            "customer_id": customer_id,
            "overall_risk_level": overall_level,
            "overall_risk_score": overall_score,
            "total_transactions_checked": len(transactions),
            "flagged_transactions": flagged,
            "summary": summary,
            "analysis_mode": "rule-based (not ML)",
        }

    except Exception as exc:
        logger.error("analyze_transaction_risk error: %s", exc)
        return {"error": str(exc), "customer_id": customer_id}
    finally:
        db.close()
