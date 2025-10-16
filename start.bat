@echo off
setlocal
if not exist venv (python -m venv venv)
call venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (copy .env.example .env >nul)
streamlit run streamlit_app.py --server.port 8501
pause
