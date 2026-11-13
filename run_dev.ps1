# MediKiosk Concurrent Dev Runner (PowerShell)
# Starts FastAPI Backend (Port 8000) & Vite React Frontend (Port 3000)

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Starting MediKiosk: Autonomous Clinical Intake & AYUSH " -ForegroundColor Green
Write-Host " Ministry of Ayush / AIIA • SIH 2026 Problem Statement 26047" -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# Set PYTHONPATH to include safety-engine and edge-api
$env:PYTHONPATH = "services/edge-api;services/safety-engine"

# Select Python binary (.venv if available, else python)
$pythonBin = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }

# Start Edge FastAPI Gateway in background job
Write-Host "Starting Edge API Gateway on http://localhost:8000 ..." -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath $pythonBin -ArgumentList "-m uvicorn app.main:app --app-dir services/edge-api --host 0.0.0.0 --port 8000 --reload" -PassThru

# Start Vite Frontend
Write-Host "Starting Vite Frontend on http://localhost:3000 ..." -ForegroundColor Green
npm run dev

# Cleanup on exit
Stop-Process -Id $backendProcess.Id -Force
