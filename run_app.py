"""
run_app.py
==========
One-click unified launcher for the Multi-Agent Banking Assistant MVP.

Usage:
  python run_app.py          # Checks/seeds DB and starts Streamlit UI
  python run_app.py --full   # Starts FastAPI in background and launches Streamlit UI
  python run_app.py --api    # Starts FastAPI backend server only
"""
from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "banking.db"


def ensure_database():
    """Ensure SQLite database exists and is populated."""
    if not DB_PATH.exists() or DB_PATH.stat().st_size == 0:
        print("[INFO] Database not found. Initialising and seeding...")
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "seed_database.py"), "--force"], cwd=ROOT)
        if result.returncode != 0:
            print("[ERROR] Database seeding failed.")
            sys.exit(1)
        print("[OK] Database initialised and seeded.")
    else:
        print(f"[OK] Database exists at {DB_PATH}")


def start_api():
    """Start the FastAPI backend with uvicorn."""
    print("[INFO] Starting FastAPI backend on http://127.0.0.1:8000 ...")
    cmd = [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"]
    return subprocess.run(cmd, cwd=ROOT)


def start_frontend():
    """Start the Streamlit frontend."""
    print("[INFO] Starting Streamlit dashboard on http://localhost:8501 ...")
    cmd = [sys.executable, "-m", "streamlit", "run", "app.py"]
    return subprocess.run(cmd, cwd=ROOT)


def start_full():
    """Start both FastAPI in a subprocess and Streamlit in the foreground."""
    print("[INFO] Starting FastAPI backend in background...")
    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT,
    )
    time.sleep(1.5)
    print("[INFO] Starting Streamlit dashboard...")
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], cwd=ROOT)
    finally:
        print("\n[INFO] Shutting down FastAPI backend...")
        api_proc.terminate()
        api_proc.wait()


if __name__ == "__main__":
    ensure_database()
    if "--api" in sys.argv:
        start_api()
    elif "--full" in sys.argv:
        start_full()
    else:
        start_frontend()
