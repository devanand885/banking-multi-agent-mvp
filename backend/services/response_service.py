"""
backend/services/response_service.py
=====================================
Response formatting utilities (lightweight helper module).
"""
from __future__ import annotations

from typing import Any, Dict, List


def format_currency(amount: float, currency: str = "INR") -> str:
    symbol = "₹" if currency == "INR" else currency
    return f"{symbol}{amount:,.2f}"


def format_risk_badge(level: str) -> str:
    badges = {
        "low": "🟢 LOW",
        "medium": "🟡 MEDIUM",
        "high": "🔴 HIGH",
        "critical": "🚨 CRITICAL",
    }
    return badges.get(level.lower(), f"⚪ {level.upper()}")


def summarize_agent_results(results: List[Dict[str, Any]]) -> str:
    lines = []
    for r in results:
        agent = r.get("agent", "unknown")
        duration = r.get("duration_ms", 0)
        tools = r.get("tools_called", [])
        lines.append(
            f"[{agent}] — {duration:.1f}ms — tools: {', '.join(tools) if tools else 'none'}"
        )
    return "\n".join(lines)
