"""
scripts/seed_database.py
========================
Deterministic database initialisation and seeding script.

Creates fictional banking records for demonstration purposes ONLY.
No real customer data or actual financial information is used.

Run with:  python scripts/seed_database.py
"""
from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from backend.database import init_db, SessionLocal
from backend.models import (
    Account, AccountStatus, AccountType,
    Customer, KYCRecord, KYCStatus, Loan, LoanStatus, LoanType,
    RiskLevel, Transaction, TransactionCategory, TransactionType,
)


def seed_customers(db) -> None:
    """Seed fictional customer records."""
    customers = [
        Customer(
            customer_id="CUST001",
            first_name="Arjun",
            last_name="Sharma",
            email="arjun.sharma@example.com",
            phone="+91-9876543210",
            date_of_birth="1985-03-15",
            address="42, MG Road, Koramangala",
            city="Bengaluru",
            country="India",
            annual_income=1200000.0,
            credit_score=780,
            employment_status="employed",
            employer_name="TechCorp Solutions Pvt Ltd",
            is_active=True,
        ),
        Customer(
            customer_id="CUST002",
            first_name="Priya",
            last_name="Verma",
            email="priya.verma@example.com",
            phone="+91-9812345678",
            date_of_birth="1990-07-22",
            address="15, Bandra West",
            city="Mumbai",
            country="India",
            annual_income=850000.0,
            credit_score=620,
            employment_status="self_employed",
            employer_name="Verma Enterprises",
            is_active=True,
        ),
        Customer(
            customer_id="CUST003",
            first_name="Rahul",
            last_name="Gupta",
            email="rahul.gupta@example.com",
            phone="+91-9845001234",
            date_of_birth="1978-11-03",
            address="7, Civil Lines",
            city="Delhi",
            country="India",
            annual_income=600000.0,
            credit_score=510,
            employment_status="employed",
            employer_name="Gupta Industries Ltd",
            is_active=True,
        ),
        Customer(
            customer_id="CUST004",
            first_name="Sneha",
            last_name="Patel",
            email="sneha.patel@example.com",
            phone="+91-9901234567",
            date_of_birth="1995-05-18",
            address="101, CG Road",
            city="Ahmedabad",
            country="India",
            annual_income=950000.0,
            credit_score=720,
            employment_status="employed",
            employer_name="InnoSoft Technologies",
            is_active=True,
        ),
        Customer(
            customer_id="CUST005",
            first_name="Vikram",
            last_name="Singh",
            email="vikram.singh@example.com",
            phone=None,          # Missing phone — for KYC test
            date_of_birth=None,  # Missing DOB  — for KYC test
            address=None,        # Missing address — for KYC test
            city="Chennai",
            country="India",
            annual_income=450000.0,
            credit_score=None,   # Missing credit score
            employment_status="unemployed",
            employer_name=None,
            is_active=True,
        ),
    ]
    db.add_all(customers)
    db.flush()
    print(f"  [OK] Seeded {len(customers)} customers")


def seed_accounts(db) -> None:
    """Seed fictional bank accounts."""
    accounts = [
        # CUST001 — two accounts
        Account(
            account_id="ACC001",
            customer_id="CUST001",
            account_type=AccountType.SAVINGS,
            account_number="SB00100012345",
            balance=285400.50,
            currency="INR",
            status=AccountStatus.ACTIVE,
            interest_rate=3.5,
            opened_at=datetime(2018, 6, 10),
        ),
        Account(
            account_id="ACC002",
            customer_id="CUST001",
            account_type=AccountType.CURRENT,
            account_number="CA00100054321",
            balance=52000.00,
            currency="INR",
            status=AccountStatus.ACTIVE,
            interest_rate=None,
            opened_at=datetime(2020, 1, 15),
        ),
        # CUST002 — one account (suspicious transactions)
        Account(
            account_id="ACC003",
            customer_id="CUST002",
            account_type=AccountType.SAVINGS,
            account_number="SB00200067890",
            balance=48200.75,
            currency="INR",
            status=AccountStatus.ACTIVE,
            interest_rate=3.5,
            opened_at=datetime(2019, 9, 5),
        ),
        # CUST003 — one account
        Account(
            account_id="ACC004",
            customer_id="CUST003",
            account_type=AccountType.SAVINGS,
            account_number="SB00300089012",
            balance=31500.00,
            currency="INR",
            status=AccountStatus.ACTIVE,
            interest_rate=3.5,
            opened_at=datetime(2016, 3, 20),
        ),
        # CUST004 — savings + fixed deposit
        Account(
            account_id="ACC005",
            customer_id="CUST004",
            account_type=AccountType.SAVINGS,
            account_number="SB00400011111",
            balance=178900.00,
            currency="INR",
            status=AccountStatus.ACTIVE,
            interest_rate=3.5,
            opened_at=datetime(2021, 4, 1),
        ),
        Account(
            account_id="ACC006",
            customer_id="CUST004",
            account_type=AccountType.FIXED_DEPOSIT,
            account_number="FD00400022222",
            balance=500000.00,
            currency="INR",
            status=AccountStatus.ACTIVE,
            interest_rate=7.0,
            opened_at=datetime(2022, 12, 1),
        ),
        # CUST005 — frozen account (for fraud demo)
        Account(
            account_id="ACC007",
            customer_id="CUST005",
            account_type=AccountType.SAVINGS,
            account_number="SB00500033333",
            balance=1200.00,
            currency="INR",
            status=AccountStatus.FROZEN,
            interest_rate=3.5,
            opened_at=datetime(2023, 1, 10),
        ),
    ]
    db.add_all(accounts)
    db.flush()
    print(f"  [OK] Seeded {len(accounts)} accounts")


def seed_transactions(db) -> None:
    """Seed transactions — includes normal and suspicious patterns."""
    now = datetime.utcnow()

    transactions = [
        # ── CUST001 / ACC001 — normal transactions ────────────────────────
        Transaction(
            transaction_id="TXN001001",
            account_id="ACC001",
            customer_id="CUST001",
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.SALARY,
            amount=100000.0,
            description="Monthly salary credit",
            merchant="TechCorp Solutions Pvt Ltd",
            location="Bengaluru",
            timestamp=now - timedelta(days=5),
            balance_after=285400.50,
        ),
        Transaction(
            transaction_id="TXN001002",
            account_id="ACC001",
            customer_id="CUST001",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.UTILITY,
            amount=3200.0,
            description="Electricity bill payment",
            merchant="BESCOM",
            location="Bengaluru",
            timestamp=now - timedelta(days=8),
            balance_after=182400.50,
        ),
        Transaction(
            transaction_id="TXN001003",
            account_id="ACC001",
            customer_id="CUST001",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.ONLINE_PAYMENT,
            amount=8500.0,
            description="Amazon shopping",
            merchant="Amazon India",
            location="Bengaluru",
            timestamp=now - timedelta(days=12),
            balance_after=179200.50,
        ),
        Transaction(
            transaction_id="TXN001004",
            account_id="ACC001",
            customer_id="CUST001",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.ATM_WITHDRAWAL,
            amount=15000.0,
            description="ATM cash withdrawal",
            merchant="ATM-BLR-0032",
            location="Bengaluru",
            timestamp=now - timedelta(days=15),
            balance_after=170700.50,
        ),
        Transaction(
            transaction_id="TXN001005",
            account_id="ACC001",
            customer_id="CUST001",
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.TRANSFER,
            amount=25000.0,
            description="NEFT transfer received",
            merchant=None,
            location="Bengaluru",
            timestamp=now - timedelta(days=20),
            balance_after=185700.50,
        ),

        # ── CUST002 / ACC003 — suspicious transactions ────────────────────
        Transaction(
            transaction_id="TXN002001",
            account_id="ACC003",
            customer_id="CUST002",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.FOREIGN_TRANSFER,
            amount=480000.0,           # VERY large — suspicious
            description="International wire transfer",
            merchant="SWIFT-OFFSHR",
            location="Grand Cayman",   # Offshore location — suspicious
            timestamp=now - timedelta(days=2),
            balance_after=48200.75,
        ),
        Transaction(
            transaction_id="TXN002002",
            account_id="ACC003",
            customer_id="CUST002",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.ATM_WITHDRAWAL,
            amount=49500.0,            # Just under ₹50 k reporting limit — suspicious
            description="ATM withdrawal",
            merchant="ATM-MUM-9991",
            location="Mumbai",
            timestamp=now - timedelta(days=3),
            balance_after=128200.75,
        ),
        Transaction(
            transaction_id="TXN002003",
            account_id="ACC003",
            customer_id="CUST002",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.ATM_WITHDRAWAL,
            amount=49000.0,            # Repeated structuring pattern
            description="ATM withdrawal",
            merchant="ATM-MUM-9992",
            location="Mumbai",
            timestamp=now - timedelta(days=3, hours=2),
            balance_after=177200.75,
        ),
        Transaction(
            transaction_id="TXN002004",
            account_id="ACC003",
            customer_id="CUST002",
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.UNKNOWN,
            amount=620000.0,           # Large unexplained credit — suspicious
            description="Credit - source unknown",
            merchant=None,
            location=None,
            timestamp=now - timedelta(days=4),
            balance_after=226200.75,
        ),
        Transaction(
            transaction_id="TXN002005",
            account_id="ACC003",
            customer_id="CUST002",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.PURCHASE,
            amount=1200.0,
            description="Grocery shopping",
            merchant="DMart",
            location="Mumbai",
            timestamp=now - timedelta(days=10),
            balance_after=10500.50,
        ),
        Transaction(
            transaction_id="TXN002006",
            account_id="ACC003",
            customer_id="CUST002",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.TRANSFER,
            amount=25000.0,
            description="Peer transfer",
            merchant=None,
            location="Pune",           # Different city in quick succession — suspicious
            timestamp=now - timedelta(days=2, hours=3),
            balance_after=23200.75,
        ),

        # ── CUST003 / ACC004 — normal low activity ────────────────────────
        Transaction(
            transaction_id="TXN003001",
            account_id="ACC004",
            customer_id="CUST003",
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.SALARY,
            amount=50000.0,
            description="Salary credit",
            merchant="Gupta Industries Ltd",
            location="Delhi",
            timestamp=now - timedelta(days=3),
            balance_after=31500.0,
        ),
        Transaction(
            transaction_id="TXN003002",
            account_id="ACC004",
            customer_id="CUST003",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.UTILITY,
            amount=2800.0,
            description="Water & electricity bills",
            merchant="BSES Delhi",
            location="Delhi",
            timestamp=now - timedelta(days=7),
            balance_after=18500.0,
        ),

        # ── CUST004 / ACC005 — normal moderate activity ───────────────────
        Transaction(
            transaction_id="TXN004001",
            account_id="ACC005",
            customer_id="CUST004",
            transaction_type=TransactionType.CREDIT,
            category=TransactionCategory.SALARY,
            amount=79167.0,
            description="Monthly salary",
            merchant="InnoSoft Technologies",
            location="Ahmedabad",
            timestamp=now - timedelta(days=4),
            balance_after=178900.0,
        ),
        Transaction(
            transaction_id="TXN004002",
            account_id="ACC005",
            customer_id="CUST004",
            transaction_type=TransactionType.DEBIT,
            category=TransactionCategory.PURCHASE,
            amount=12000.0,
            description="Electronics purchase",
            merchant="Croma",
            location="Ahmedabad",
            timestamp=now - timedelta(days=9),
            balance_after=99733.0,
        ),
    ]
    db.add_all(transactions)
    db.flush()
    print(f"  [OK] Seeded {len(transactions)} transactions")


def seed_loans(db) -> None:
    """Seed fictional loan records."""
    loans = [
        # CUST001 — home loan (active)
        Loan(
            loan_id="LOAN001",
            customer_id="CUST001",
            loan_type=LoanType.HOME,
            principal_amount=5000000.0,
            outstanding_balance=3850000.0,
            interest_rate=8.5,
            tenure_months=240,
            monthly_emi=43391.0,
            loan_status=LoanStatus.ACTIVE,
            disbursement_date=datetime(2019, 3, 1),
            next_due_date=datetime.utcnow() + timedelta(days=15),
            last_payment_date=datetime.utcnow() - timedelta(days=16),
            missed_payments=0,
            collateral="Residential flat, Koramangala",
            purpose="Purchase of residential property",
        ),
        # CUST001 — personal loan (closed)
        Loan(
            loan_id="LOAN002",
            customer_id="CUST001",
            loan_type=LoanType.PERSONAL,
            principal_amount=200000.0,
            outstanding_balance=0.0,
            interest_rate=13.5,
            tenure_months=24,
            monthly_emi=9540.0,
            loan_status=LoanStatus.CLOSED,
            disbursement_date=datetime(2021, 7, 1),
            next_due_date=None,
            last_payment_date=datetime(2023, 6, 30),
            missed_payments=0,
            collateral=None,
            purpose="Home renovation",
        ),
        # CUST003 — auto loan (active, some missed payments)
        Loan(
            loan_id="LOAN003",
            customer_id="CUST003",
            loan_type=LoanType.AUTO,
            principal_amount=800000.0,
            outstanding_balance=610000.0,
            interest_rate=9.0,
            tenure_months=60,
            monthly_emi=16608.0,
            loan_status=LoanStatus.ACTIVE,
            disbursement_date=datetime(2022, 8, 15),
            next_due_date=datetime.utcnow() + timedelta(days=5),
            last_payment_date=datetime.utcnow() - timedelta(days=46),
            missed_payments=1,
            collateral="Maruti Suzuki Ciaz",
            purpose="Purchase of automobile",
        ),
        # CUST004 — education loan (active)
        Loan(
            loan_id="LOAN004",
            customer_id="CUST004",
            loan_type=LoanType.EDUCATION,
            principal_amount=1200000.0,
            outstanding_balance=980000.0,
            interest_rate=7.5,
            tenure_months=84,
            monthly_emi=18338.0,
            loan_status=LoanStatus.ACTIVE,
            disbursement_date=datetime(2023, 6, 1),
            next_due_date=datetime.utcnow() + timedelta(days=20),
            last_payment_date=datetime.utcnow() - timedelta(days=11),
            missed_payments=0,
            collateral=None,
            purpose="Post-graduate education abroad",
        ),
    ]
    db.add_all(loans)
    db.flush()
    print(f"  [OK] Seeded {len(loans)} loans")


def seed_kyc(db) -> None:
    """Seed KYC / compliance records."""
    now = datetime.utcnow()
    kyc_records = [
        # CUST001 — fully verified
        KYCRecord(
            customer_id="CUST001",
            kyc_status=KYCStatus.VERIFIED,
            pan_number="ABCDE1234F",
            aadhar_number="9876-5432-1098",
            passport_number="Z1234567",
            address_proof="Electricity Bill",
            photo_id_verified=True,
            address_verified=True,
            income_verified=True,
            pep_check=True,
            sanctions_check=True,
            risk_rating=RiskLevel.LOW,
            verified_at=datetime(2023, 1, 10),
            expires_at=datetime(2026, 1, 10),
            notes="Full KYC completed successfully",
        ),
        # CUST002 — verified but medium risk (due to flagged transactions)
        KYCRecord(
            customer_id="CUST002",
            kyc_status=KYCStatus.VERIFIED,
            pan_number="FGHIJ5678K",
            aadhar_number="1234-5678-9012",
            passport_number=None,
            address_proof="Bank Statement",
            photo_id_verified=True,
            address_verified=True,
            income_verified=False,       # Income NOT verified
            pep_check=True,
            sanctions_check=True,
            risk_rating=RiskLevel.MEDIUM,
            verified_at=datetime(2023, 5, 20),
            expires_at=datetime(2025, 5, 20),
            notes="Income verification pending. Enhanced due diligence required.",
        ),
        # CUST003 — pending (partial verification)
        KYCRecord(
            customer_id="CUST003",
            kyc_status=KYCStatus.PENDING,
            pan_number="KLMNO9012P",
            aadhar_number=None,           # Missing Aadhar
            passport_number=None,
            address_proof=None,            # Missing address proof
            photo_id_verified=True,
            address_verified=False,
            income_verified=False,
            pep_check=False,
            sanctions_check=True,
            risk_rating=RiskLevel.MEDIUM,
            verified_at=None,
            expires_at=None,
            notes="Aadhar and address proof submission pending",
        ),
        # CUST004 — verified, low risk
        KYCRecord(
            customer_id="CUST004",
            kyc_status=KYCStatus.VERIFIED,
            pan_number="PQRST3456U",
            aadhar_number="2345-6789-0123",
            passport_number="M7654321",
            address_proof="Utility Bill",
            photo_id_verified=True,
            address_verified=True,
            income_verified=True,
            pep_check=True,
            sanctions_check=True,
            risk_rating=RiskLevel.LOW,
            verified_at=datetime(2024, 2, 14),
            expires_at=datetime(2027, 2, 14),
            notes="All KYC documents verified",
        ),
        # CUST005 — failed (many missing fields)
        KYCRecord(
            customer_id="CUST005",
            kyc_status=KYCStatus.FAILED,
            pan_number=None,              # Missing PAN
            aadhar_number=None,           # Missing Aadhar
            passport_number=None,
            address_proof=None,
            photo_id_verified=False,
            address_verified=False,
            income_verified=False,
            pep_check=False,
            sanctions_check=False,
            risk_rating=RiskLevel.HIGH,
            verified_at=None,
            expires_at=None,
            notes="KYC failed: multiple required documents missing",
        ),
    ]
    db.add_all(kyc_records)
    db.flush()
    print(f"  [OK] Seeded {len(kyc_records)} KYC records")


def run_seeding() -> None:
    """Main seeding entry point."""
    print("\n========================================")
    print("  Multi-Agent Banking Assistant")
    print("  Database Initialisation & Seeding")
    print("========================================\n")

    print("Creating database tables...")
    init_db()
    print("  [OK] Tables created\n")

    db = SessionLocal()
    try:
        # Check if already seeded
        from backend.models import Customer
        existing = db.query(Customer).count()
        if existing > 0:
            print(f"  [INFO] Database already contains {existing} customers.")
            if "--force" not in sys.argv:
                answer = input("  Re-seed? This will clear existing data (y/N): ").strip().lower()
                if answer != "y":
                    print("  Skipping seed - existing data preserved.")
                    return
            # Clear existing data
            print("\nClearing existing data...")
            from backend.models import KYCRecord, Loan, Transaction, Account, Customer
            db.query(KYCRecord).delete()
            db.query(Transaction).delete()
            db.query(Loan).delete()
            db.query(Account).delete()
            db.query(Customer).delete()
            db.commit()
            print("  [OK] Cleared\n")

        print("Seeding data...")
        seed_customers(db)
        seed_accounts(db)
        seed_transactions(db)
        seed_loans(db)
        seed_kyc(db)
        db.commit()

        print("\n[SUCCESS] Database seeded successfully!")
        print("\nSeeded customers:")
        print("  CUST001 - Arjun Sharma    (Good credit, home loan)")
        print("  CUST002 - Priya Verma     (Suspicious transactions, medium KYC risk)")
        print("  CUST003 - Rahul Gupta     (Below-average credit, auto loan, KYC pending)")
        print("  CUST004 - Sneha Patel     (Good credit, education loan, FD)")
        print("  CUST005 - Vikram Singh    (KYC failed, account frozen, multiple missing fields)")
        print()

    except Exception as exc:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seeding()
