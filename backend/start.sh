#!/bin/bash
set -e

echo "================================================"
echo "  CogniCare Backend Startup"
echo "================================================"

echo "Waiting for MySQL to be ready..."
sleep 5

echo "Running database seed / initial data..."
python -m app.initial_data

echo "Starting FastAPI server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
