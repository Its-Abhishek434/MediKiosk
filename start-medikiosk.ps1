# ==============================================================================
# MediKiosk One-Click Autonomous Clinical Intake Launcher (Windows PowerShell)
# Ministry of Ayush / AIIA • Smart India Hackathon 2026 (Problem Statement 26047)
# ==============================================================================

Write-Host "====================================================================" -ForegroundColor Cyan
Write-Host "   MediKiosk: Autonomous First-Mile Clinical Intake & AYUSH System   " -ForegroundColor Green
Write-Host "   Ministry of Ayush / AIIA • SIH 2026 Problem Statement 26047      " -ForegroundColor Yellow
Write-Host "====================================================================" -ForegroundColor Cyan

# 1. Environment & Path Resolution
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

$env:KMP_DUPLICATE_LIB_OK = "TRUE"
$env:PYTHONPATH = "services/edge-api;services/safety-engine"
$pythonBin = if (Test-Path ".venv\Scripts\python.exe") { "$scriptDir\.venv\Scripts\python.exe" } else { "python" }

# 2. Check and Launch Ollama (if installed & not running)
Write-Host "`n[1/4] Checking Ollama AI Service..." -ForegroundColor Cyan
$ollamaRunning = $false
try {
    $res = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($res) { $ollamaRunning = $true }
} catch {
    $ollamaRunning = $false
}

if ($ollamaRunning) {
    Write-Host "  [OK] Ollama is already active on http://localhost:11434" -ForegroundColor Green
} else {
    $ollamaCmd = Get-Command "ollama" -ErrorAction SilentlyContinue
    if ($ollamaCmd) {
        Write-Host "  [START] Launching Ollama in background..." -ForegroundColor Yellow
        Start-Process "ollama" -ArgumentList "serve" -WindowStyle Minimized
        Start-Sleep -Seconds 2
    } else {
        Write-Host "  [NOTICE] Ollama executable not found on PATH. Proceeding with deterministic clinical engine..." -ForegroundColor Gray
    }
}

# 3. Launch FastAPI Edge API Gateway
Write-Host "`n[2/4] Starting Edge API Gateway on http://localhost:8000..." -ForegroundColor Cyan
$backendArgs = "-m uvicorn app.main:app --app-dir services/edge-api --host 0.0.0.0 --port 8000 --reload"
$backendProc = Start-Process -FilePath $pythonBin -ArgumentList $backendArgs -PassThru -NoNewWindow

# 4. Wait for Backend Health Check
Write-Host "`n[3/4] Awaiting Edge API Readiness (/api/health)..." -ForegroundColor Cyan
$retries = 20
$isHealthy = $false
while ($retries -gt 0 -and -not $isHealthy) {
    Start-Sleep -Milliseconds 600
    try {
        $health = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method Get -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($health.status -eq "ok") {
            $isHealthy = $true
            Write-Host "  [READY] Edge API is Online: $($health.message)" -ForegroundColor Green
        }
    } catch {}
    $retries--
}

if (-not $isHealthy) {
    Write-Host "  [WARN] Backend taking longer than expected. Proceeding to frontend..." -ForegroundColor Yellow
}

# 5. Launch Vite React Frontend
Write-Host "`n[4/4] Starting MediKiosk Kiosk & Doctor Studio UI..." -ForegroundColor Green
Write-Host "  -> Patient Kiosk:   http://localhost:3000" -ForegroundColor Cyan
Write-Host "  -> Doctor Studio:   http://localhost:3000/doctor" -ForegroundColor Cyan
Write-Host "  -> Edge Swagger:    http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "`nPress Ctrl+C to terminate all services.`n" -ForegroundColor Yellow

# Launch browser tab after 1 second
Start-Job -ScriptBlock {
    Start-Sleep -Seconds 1
    Start-Process "http://localhost:3000"
} | Out-Null

try {
    npm run dev
} finally {
    Write-Host "`nStopping background processes..." -ForegroundColor Red
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    Write-Host "[SHUTDOWN] MediKiosk services stopped cleanly." -ForegroundColor Green
}
