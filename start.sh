#!/usr/bin/env bash
set -e
python3 -m venv venv || python -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
[ ! -f .env ] && cp .env.example .env || true
streamlit run streamlit_app.py --server.port 8501
