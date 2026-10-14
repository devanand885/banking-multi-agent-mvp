"""
backend/services/llm_service.py
=================================
LLM Integration Service

Provides:
  - Intent classification from natural-language banking queries
  - Response phrasing using a configured LLM provider
  - Deterministic mock fallback when credentials are missing or calls fail

Supported providers: Google Gemini, OpenAI, Mock (default)

Security:
  - API keys are read from environment variables only
  - Keys are NEVER logged or included in prompts
  - Sensitive customer data is minimised in prompts
  - All LLM outputs are validated against an intent allowlist

The mode ("real" or "mock") is always disclosed in the response.
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.config import settings

logger = logging.getLogger(__name__)

# ──────────────────────────────── Intent Allowlist ────────────────────────────
# The LLM may only return intents from this list.
VALID_INTENTS = {
    "account_inquiry",
    "transaction_inquiry",
    "fraud_risk_analysis",
    "loan_inquiry",
    "loan_eligibility_check",
    "emi_calculation",
    "kyc_verification",
    "combined_inquiry",
    "general_question",
    "unknown",
}

# ──────────────────────────────── Deterministic Keyword Router ────────────────
# Used in mock mode and as a fallback when the LLM result is invalid.

_KEYWORD_RULES: List[Tuple[List[str], str]] = [
    (["emi", "equated monthly", "monthly instalment", "monthly payment", "instalment"], "emi_calculation"),
    (["eligible", "eligibility", "qualify", "can i get a loan", "approve loan"], "loan_eligibility_check"),
    (["loan", "outstanding", "borrowing", "credit", "repay"], "loan_inquiry"),
    (["fraud", "suspicious", "risk", "anomaly", "flag", "unusual", "scam"], "fraud_risk_analysis"),
    (["kyc", "verification", "verify", "compliance", "know your customer", "document", "aml"], "kyc_verification"),
    (["balance", "account", "savings", "current", "fixed deposit", "statement"], "account_inquiry"),
    (["transaction", "payment", "transfer", "history", "recent"], "transaction_inquiry"),
    (["balance", "loan", "fraud"], "combined_inquiry"),
]


def _keyword_intent(message: str) -> str:
    """Deterministic keyword-based intent detection."""
    lower = message.lower()
    # Combined intent — if message mentions multiple banking areas
    areas_mentioned = 0
    area_keywords = [
        ["balance", "account"],
        ["loan", "emi", "credit"],
        ["fraud", "suspicious", "risk"],
    ]
    for kws in area_keywords:
        if any(k in lower for k in kws):
            areas_mentioned += 1
    if areas_mentioned >= 2:
        return "combined_inquiry"

    for keywords, intent in _KEYWORD_RULES:
        if any(k in lower for k in keywords):
            return intent
    return "general_question"


def _extract_customer_id(message: str, provided_customer_id: Optional[str] = None) -> Optional[str]:
    """Extract a customer ID from the message or return the provided one."""
    if provided_customer_id:
        return provided_customer_id
    match = re.search(r"\bCUST[A-Za-z0-9_]+\b", message, re.IGNORECASE)
    return match.group().upper() if match else None


def _extract_emi_params(message: str) -> Dict[str, Any]:
    """Try to extract EMI parameters from natural language."""
    params: Dict[str, Any] = {}

    # Principal / loan amount
    amount_match = re.search(
        r"(?:loan\s+(?:of\s+)?|amount\s+(?:of\s+)?|principal\s+(?:of\s+)?|for\s+|rs\.?\s*|₹\s*|inr\s*)(\d[\d,]*(?:\.\d+)?)\b",
        message, re.IGNORECASE,
    )
    if amount_match:
        params["principal"] = float(amount_match.group(1).replace(",", ""))
    else:
        # Fallback: look for a standalone number >= 1000
        standalone_num = re.search(r"\b(\d{4,9}(?:\.\d+)?)\b", message)
        if standalone_num:
            params["principal"] = float(standalone_num.group(1))

    # Interest rate
    rate_match = re.search(
        r"(\d+(?:\.\d+)?)\s*(?:%|\s*percent|\s*%?\s*(?:per\s+annum|annual|p\.a\.|interest))",
        message, re.IGNORECASE,
    )
    if rate_match:
        params["annual_interest_rate"] = float(rate_match.group(1))

    # Tenure
    tenure_match = re.search(
        r"(\d+)\s*(months?|years?)\b",
        message, re.IGNORECASE,
    )
    if tenure_match:
        n = int(tenure_match.group(1))
        unit = tenure_match.group(2).lower()
        if "year" in unit:
            n *= 12
        params["tenure_months"] = n

    return params


# ──────────────────────────────── LLM Backends ────────────────────────────────

INTENT_SYSTEM_PROMPT = """You are an intent classifier for a banking assistant.
Given a user message, classify it into exactly one of these intents:
  account_inquiry, transaction_inquiry, fraud_risk_analysis,
  loan_inquiry, loan_eligibility_check, emi_calculation,
  kyc_verification, combined_inquiry, general_question, unknown

Also extract:
  - customer_id: any customer ID mentioned (format CUSTXXX) or null
  - parameters: any numeric parameters relevant to the intent

Respond ONLY with valid JSON in this exact format:
{"intent": "<intent>", "customer_id": "<id or null>", "parameters": {}}
"""


def _call_gemini(message: str) -> Optional[Dict[str, Any]]:
    """Call Google Gemini for intent classification."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = f"{INTENT_SYSTEM_PROMPT}\n\nUser message: {message}"
        response = model.generate_content(
            prompt,
            generation_config={"temperature": 0.1, "max_output_tokens": 200},
        )
        text = response.text.strip()
        # Strip markdown code fences if present
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("```").strip()
        return json.loads(text)
    except Exception as exc:
        logger.warning("Gemini call failed: %s", exc)
        return None


def _call_openai(message: str) -> Optional[Dict[str, Any]]:
    """Call OpenAI for intent classification."""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": INTENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.1,
            max_tokens=200,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r"```(?:json)?", "", text).strip().rstrip("```").strip()
        return json.loads(text)
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return None


RESPONSE_SYSTEM_PROMPT = """You are a helpful banking assistant. 
Generate a clear, professional, concise natural-language summary of the banking data provided.
Be factual — use only the data given. Do not invent numbers.
Label all information as simulated banking data.
Keep the response under 200 words."""


def _generate_response_gemini(intent: str, data: Dict[str, Any]) -> Optional[str]:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(settings.gemini_model)
        prompt = (
            f"{RESPONSE_SYSTEM_PROMPT}\n\n"
            f"Intent: {intent}\n"
            f"Data: {json.dumps(data, default=str, indent=2)[:2000]}"
        )
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as exc:
        logger.warning("Gemini response generation failed: %s", exc)
        return None


def _generate_response_openai(intent: str, data: Dict[str, Any]) -> Optional[str]:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": RESPONSE_SYSTEM_PROMPT},
                {"role": "user", "content": (
                    f"Intent: {intent}\nData: {json.dumps(data, default=str, indent=2)[:2000]}"
                )},
            ],
            temperature=0.3,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("OpenAI response generation failed: %s", exc)
        return None


# ──────────────────────────────── Public API ──────────────────────────────────

class LLMService:
    """
    Unified LLM service with real-provider and mock fallback support.
    The mode used is always disclosed in the returned metadata.
    """

    def classify_intent(
        self,
        message: str,
        provided_customer_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify the intent of a banking query.

        Returns:
          {
            "intent": str,
            "customer_id": str | None,
            "parameters": dict,
            "llm_mode": "gemini" | "openai" | "mock",
          }
        """
        provider = settings.effective_llm_provider
        llm_result: Optional[Dict[str, Any]] = None

        if provider == "gemini":
            llm_result = _call_gemini(message)
        elif provider == "openai":
            llm_result = _call_openai(message)

        # Validate LLM result
        if llm_result and isinstance(llm_result, dict):
            intent = llm_result.get("intent", "unknown")
            if intent not in VALID_INTENTS:
                logger.warning("LLM returned invalid intent '%s', falling back", intent)
                intent = _keyword_intent(message)
                llm_result["intent"] = intent
            customer_id = llm_result.get("customer_id") or _extract_customer_id(message, provided_customer_id)
            params = llm_result.get("parameters", {})
            # Always supplement with keyword EMI extraction
            if intent == "emi_calculation" and not params:
                params = _extract_emi_params(message)
            return {
                "intent": intent,
                "customer_id": customer_id,
                "parameters": params,
                "llm_mode": provider,
            }

        # Mock / fallback mode
        intent = _keyword_intent(message)
        customer_id = _extract_customer_id(message, provided_customer_id)
        params = _extract_emi_params(message) if intent == "emi_calculation" else {}

        return {
            "intent": intent,
            "customer_id": customer_id,
            "parameters": params,
            "llm_mode": "mock",
        }

    def generate_response(
        self,
        intent: str,
        structured_data: Dict[str, Any],
        fallback_text: str,
    ) -> Tuple[str, str]:
        """
        Generate a natural-language response from structured data.

        Returns: (response_text, llm_mode_used)
        """
        provider = settings.effective_llm_provider
        response_text: Optional[str] = None

        if provider == "gemini":
            response_text = _generate_response_gemini(intent, structured_data)
        elif provider == "openai":
            response_text = _generate_response_openai(intent, structured_data)

        if response_text:
            return response_text, provider

        return fallback_text, "mock"


# Singleton
llm_service = LLMService()
