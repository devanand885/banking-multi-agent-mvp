"""
backend/main.py
================
FastAPI application entry point.

Endpoints:
  GET  /health                         — Health check
  GET  /customers/{id}                 — Customer profile
  GET  /customers/{id}/accounts        — Customer accounts
  GET  /customers/{id}/transactions    — Customer transactions
  GET  /customers/{id}/loans           — Customer loans
  GET  /customers/{id}/kyc             — KYC status
  POST /risk/analyze                   — Risk / fraud analysis
  POST /loans/eligibility              — Loan eligibility check
  POST /loans/emi                      — EMI calculation
  POST /chat                           — Natural-language orchestrator

API docs: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.database import init_db
from backend.schemas import ChatRequest, ChatResponse, HealthResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────── App Initialisation ──────────────────────────

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Multi-Agent Banking Assistant backend...")
    init_db()
    logger.info("Database initialised")
    logger.info("LLM mode: %s", settings.effective_llm_provider)
    yield


app = FastAPI(
    title="Multi-Agent Banking Assistant API",
    description=(
        "Simulated banking API powering the Multi-Agent Banking Assistant MVP. "
        "All data is entirely fictional and used for demonstration purposes only. "
        "No real banking operations are performed."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={"name": "Wrench Wise EduTech AI/ML Internship", "email": "demo@example.com"},
    license_info={"name": "MIT"},
    lifespan=lifespan,
)

# CORS — allow Streamlit frontend (localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ──────────────────────────────── Include Routers ─────────────────────────────

from backend.api.customers import router as customers_router
from backend.api.loans import router as loans_router
from backend.api.compliance import router as compliance_router
from backend.api.risk import router as risk_router

app.include_router(customers_router)
app.include_router(loans_router)
app.include_router(compliance_router)
app.include_router(risk_router)

# ──────────────────────────────── Core Endpoints ──────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["System"], summary="Health check")
def health_check():
    """Returns the API health status, LLM mode, and database connectivity."""
    from backend.database import SessionLocal
    db_status = "ok"
    try:
        db = SessionLocal()
        from backend.models import Customer
        db.query(Customer).limit(1).all()
        db.close()
    except Exception as exc:
        db_status = f"error: {exc}"

    return {
        "status": "ok",
        "version": "1.0.0",
        "llm_mode": settings.effective_llm_provider,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc),
    }


@app.post("/chat", tags=["Orchestrator"], summary="Natural-language banking chat")
def chat(request: ChatRequest):
    """
    Submit a natural-language banking request to the Supervisor/Orchestrator Agent.

    The orchestrator will:
    1. Classify the intent
    2. Route to the appropriate specialized agent(s)
    3. Execute tools to retrieve real data from the simulated database
    4. Return a structured response with an execution trace

    Example queries:
    - "Show the account balance for customer CUST001"
    - "Check CUST002 for suspicious transactions"
    - "Is CUST003 eligible for a loan of 500000?"
    - "Calculate EMI for 300000 at 10% for 36 months"
    - "Check KYC status of CUST001"
    """
    from backend.agents.orchestrator import orchestrator

    result = orchestrator.process(
        message=request.message,
        customer_id=request.customer_id,
    )
    return result


@app.get("/", tags=["System"], summary="API root")
def root():
    return {
        "message": "Multi-Agent Banking Assistant API",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0",
        "disclaimer": "All banking data is simulated for demonstration purposes only.",
    }
