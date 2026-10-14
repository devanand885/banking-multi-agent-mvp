# ============================================================
# Multi-Agent Banking Assistant — Application Entry Point
# ============================================================
# This is the Streamlit frontend application.
# Run with: streamlit run app.py
# ============================================================

import streamlit as st
import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from frontend.streamlit_app import main

if __name__ == "__main__":
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "selected_customer" not in st.session_state:
        st.session_state["selected_customer"] = "CUST001"
    if "last_response" not in st.session_state:
        st.session_state["last_response"] = None
    main()
