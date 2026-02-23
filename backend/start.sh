#!/bin/bash
echo "Activating virtual environment..."
source ../.venv/bin/activate

echo ""
echo "Installing/updating backend dependencies..."
pip install fastapi uvicorn[standard] python-multipart

echo ""
echo "Starting FastAPI server..."
python -m uvicorn main:app --reload
