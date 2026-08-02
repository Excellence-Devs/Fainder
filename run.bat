@echo off
echo ==============================================
echo Starting Fainder Application
echo ==============================================

echo [INFO] Checking for virtual environment...
if not exist .venv (
    echo [INFO] Virtual environment not found. Creating one...
    python -m venv .venv
)

echo [INFO] Activating virtual environment...
call .venv\Scripts\activate.bat

echo [INFO] Checking dependencies...
pip install -r requirements.txt

echo [INFO] Starting fainder_test.py...
python fainder_test.py

echo.
echo [INFO] Application has stopped.
pause
