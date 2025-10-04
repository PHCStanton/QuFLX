# QuantumFlux Trading Platform - Startup Script
# Starts Chrome session and backend API in one PowerShell instance

param(
    [int]$Port = 9222,
    [int]$BackendPort = 8000,
    [string]$ChromeProfile = "Chrome_profile",
    [switch]$SkipChromeStart,
    [switch]$BackendOnly
)

Write-Host "QuantumFlux Trading Platform Startup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan

# Function to test if port is open
function Test-Port {
    param([string]$Host, [int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName $Host -Port $Port -WarningAction SilentlyContinue
        return $connection.TcpTestSucceeded
    } catch {
        return $false
    }
}

# Function to find Chrome executable
function Find-Chrome {
    $chromePaths = @(
        "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "chrome.exe"
    )
    
    foreach ($path in $chromePaths) {
        if (Test-Path $path) {
            return $path
        }
    }
    return $null
}

# Check if Chrome is already running on the port
if (Test-Port "127.0.0.1" $Port) {
    Write-Host "Chrome already running on port $Port" -ForegroundColor Green
    $SkipChromeStart = $true
}

# Start Chrome session if needed
if (-not $SkipChromeStart -and -not $BackendOnly) {
    Write-Host "Starting Chrome with remote debugging..." -ForegroundColor Yellow

    $chromeExe = Find-Chrome
    if (-not $chromeExe) {
        Write-Host "Chrome executable not found!" -ForegroundColor Red
        Write-Host "Please install Chrome or add it to PATH" -ForegroundColor Red
        exit 1
    }

    Write-Host "Chrome executable: $chromeExe" -ForegroundColor Gray

    # Create Chrome profile directory
    $profilePath = Join-Path $PSScriptRoot ".." $ChromeProfile
    if (-not (Test-Path $profilePath)) {
        New-Item -ItemType Directory -Path $profilePath -Force | Out-Null
    }

    Write-Host "Chrome profile: $profilePath" -ForegroundColor Gray

    # Chrome arguments
    $chromeArgs = @(
        "--remote-debugging-port=$Port",
        "--user-data-dir=`"$profilePath`"",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-default-apps",
        "--disable-popup-blocking",
        "--disable-web-security",
        "--allow-running-insecure-content",
        "https://pocket2.click/cabinet/demo-quick-high-low"
    )

    # Start Chrome in background
    try {
        Start-Process -FilePath $chromeExe -ArgumentList $chromeArgs -WindowStyle Normal
        Write-Host "Waiting for Chrome to start..." -ForegroundColor Yellow

        # Wait for Chrome to be ready (max 30 seconds)
        $timeout = 30
        $elapsed = 0
        while (-not (Test-Port "127.0.0.1" $Port) -and $elapsed -lt $timeout) {
            Start-Sleep -Seconds 1
            $elapsed++
            Write-Host "." -NoNewline -ForegroundColor Yellow
        }
        Write-Host ""

        if (Test-Port "127.0.0.1" $Port) {
            Write-Host "Chrome started successfully on port $Port" -ForegroundColor Green
        } else {
            Write-Host "Chrome failed to start within $timeout seconds" -ForegroundColor Red
            exit 1
        }
    } catch {
        Write-Host "Failed to start Chrome: $_" -ForegroundColor Red
        exit 1
    }
}

# Check if backend port is available
if (Test-Port "127.0.0.1" $BackendPort) {
    Write-Host "Backend port $BackendPort is already in use" -ForegroundColor Yellow
    Write-Host "Stopping existing backend..." -ForegroundColor Yellow

    # Try to stop any existing uvicorn process
    try {
        Get-Process -Name "python" | Where-Object { $_.CommandLine -like "*uvicorn*backend*" } | Stop-Process -Force
        Start-Sleep -Seconds 2
    } catch {
        # Ignore errors
    }
}

# Start backend
Write-Host "Starting QuantumFlux backend..." -ForegroundColor Yellow

try {
    # Change to script directory
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
    $projectRoot = Split-Path -Parent $scriptDir
    Set-Location $projectRoot

    Write-Host "Project root: $projectRoot" -ForegroundColor Gray

    # Start backend with uvicorn
    Write-Host "Starting backend on port $BackendPort..." -ForegroundColor Green

    # Run uvicorn in the foreground so we can see logs
    python -m uvicorn backend:app --host 0.0.0.0 --port $BackendPort --reload

} catch {
    Write-Host "Failed to start backend: $_" -ForegroundColor Red
    exit 1
}

Write-Host "Backend stopped" -ForegroundColor Yellow
