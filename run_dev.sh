#!/usr/bin/env bash
# MediKiosk Concurrent Dev Runner (Bash)
# Launches FastAPI Backend (Port 8000) and Vite React Frontend (Port 3000)

echo "=========================================================="
echo " Starting MediKiosk: Autonomous Clinical Intake & AYUSH "
echo " Ministry of Ayush / AIIA • SIH 2026 Problem Statement 26047"
echo "=========================================================="

# Trap SIGINT to terminate background jobs cleanly
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

# Start Edge FastAPI Backend
echo "Starting Edge API Gateway on http://localhost:8000 ..."
export PYTHONPATH="services/edge-api:services/safety-engine:$PYTHONPATH"
PYTHON_BIN=".venv/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    PYTHON_BIN="python"
fi
$PYTHON_BIN -m uvicorn app.main:app --app-dir services/edge-api --host 0.0.0.0 --port 8000 --reload &

# Start Vite Frontend
echo "Starting Vite Frontend on http://localhost:3000 ..."
npm run dev
