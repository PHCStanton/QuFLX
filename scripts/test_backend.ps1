# Simple test script to start backend only
Write-Host "Testing backend startup..." -ForegroundColor Cyan

try {
    # Change to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    Set-Location $projectRoot

    Write-Host "Project root: $projectRoot" -ForegroundColor Gray

    # Start backend with uvicorn
    Write-Host "Starting backend on port 8000..." -ForegroundColor Green

    # Run uvicorn in the foreground so we can see logs
    python -m uvicorn backend:app --host 0.0.0.0 --port 8000 --reload

} catch {
    Write-Host "Failed to start backend: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Backend stopped" -ForegroundColor Yellow
