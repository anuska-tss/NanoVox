@echo off
echo Activating virtual environment...
call ..\.venv\Scripts\activate.bat

echo.
echo Installing/updating backend dependencies...
pip install -r requirements.txt

echo.
echo Starting FastAPI server...
python -m uvicorn main:app --reload --log-level debug
