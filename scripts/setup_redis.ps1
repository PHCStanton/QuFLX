# Redis Setup Script for QuFLX Trading Platform
# PowerShell script for Windows environment

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "QuFLX Redis Integration Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
if (-NOT ([Security.Principal.WindowsPrincipal]::GetCurrent().IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator))) {
    Write-Host "⚠️  Warning: Running without Administrator privileges" -ForegroundColor Yellow
    Write-Host "   Some operations may require elevated privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if command exists
function Test-Command {
    param ($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

# Step 1: Check if Redis is already installed
Write-Host "Step 1: Checking Redis installation..." -ForegroundColor Green
$redisInstalled = Test-Command "redis-cli"

if ($redisInstalled) {
    try {
        $redisVersion = redis-cli --version
        Write-Host "✅ Redis is already installed: $redisVersion" -ForegroundColor Green
    }
    catch {
        Write-Host "✅ Redis is installed but version check failed" -ForegroundColor Green
    }
}
else {
    Write-Host "❌ Redis is not installed" -ForegroundColor Red
    Write-Host "   Installing Redis..." -ForegroundColor Yellow
    
    # Try winget first (Windows 10/11)
    if (Test-Command "winget") {
        Write-Host "   Using winget to install Redis..." -ForegroundColor Cyan
        try {
            winget install Redis.Redis --accept-package-agreements --accept-source-agreements
            Write-Host "✅ Redis installed via winget" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ winget installation failed" -ForegroundColor Red
            Write-Host "   Please install Redis manually from https://redis.io/download" -ForegroundColor Yellow
            exit 1
        }
    }
    # Fallback to chocolatey
    elseif (Test-Command "choco") {
        Write-Host "   Using chocolatey to install Redis..." -ForegroundColor Cyan
        try {
            choco install redis -y
            Write-Host "✅ Redis installed via chocolatey" -ForegroundColor Green
        }
        catch {
            Write-Host "❌ chocolatey installation failed" -ForegroundColor Red
            Write-Host "   Please install Redis manually from https://redis.io/download" -ForegroundColor Yellow
            exit 1
        }
    }
    else {
        Write-Host "❌ No package manager found (winget/chocolatey)" -ForegroundColor Red
        Write-Host "   Please install Redis manually from https://redis.io/download" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host ""

# Step 2: Check Redis service status
Write-Host "Step 2: Checking Redis service status..." -ForegroundColor Green
$redisService = Get-Service -Name "Redis" -ErrorAction SilentlyContinue

if ($redisService) {
    if ($redisService.Status -eq "Running") {
        Write-Host "✅ Redis service is running" -ForegroundColor Green
    }
    else {
        Write-Host "⚠️  Redis service is stopped (Status: $($redisService.Status))" -ForegroundColor Yellow
        Write-Host "   Starting Redis service..." -ForegroundColor Cyan
        
        try {
            Start-Service -Name "Redis" -ErrorAction Stop
            Start-Sleep -Seconds 3
            
            $redisServiceAfter = Get-Service -Name "Redis" -ErrorAction SilentlyContinue
            if ($redisServiceAfter.Status -eq "Running") {
                Write-Host "✅ Redis service started successfully" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Failed to start Redis service" -ForegroundColor Red
                Write-Host "   Trying manual start..." -ForegroundColor Yellow
                
                # Try manual redis-server start
                try {
                    redis-server --daemonize yes --port 6379
                    Write-Host "✅ Redis started manually" -ForegroundColor Green
                }
                catch {
                    Write-Host "❌ Manual Redis start failed" -ForegroundColor Red
                    Write-Host "   Please start Redis manually: redis-server" -ForegroundColor Yellow
                }
            }
        }
        catch {
            Write-Host "❌ Failed to start Redis service: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
}
else {
    Write-Host "⚠️  Redis service not found" -ForegroundColor Yellow
    Write-Host "   Trying to start Redis manually..." -ForegroundColor Cyan
    
    try {
        # Check if redis-server command works
        $redisTest = redis-cli ping
        if ($redisTest -eq "PONG") {
            Write-Host "✅ Redis is already running manually" -ForegroundColor Green
        }
        else {
            Write-Host "   Starting Redis server..." -ForegroundColor Cyan
            redis-server --daemonize yes --port 6379 --appendonly yes --appendfilename "redis.aof"
            
            Start-Sleep -Seconds 2
            
            # Test connection
            $redisTestAfter = redis-cli ping
            if ($redisTestAfter -eq "PONG") {
                Write-Host "✅ Redis started successfully" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Redis failed to start" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "❌ Failed to start Redis manually" -ForegroundColor Red
        Write-Host "   Please start Redis manually: redis-server" -ForegroundColor Yellow
    }
}

Write-Host ""

# Step 3: Test Redis connection
Write-Host "Step 3: Testing Redis connection..." -ForegroundColor Green
try {
    $redisTest = redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis connection test successful" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Redis connection test failed" -ForegroundColor Red
        Write-Host "   Response: $redisTest" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Redis connection test failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""

# Step 4: Install Python Redis client
Write-Host "Step 4: Installing Python Redis client..." -ForegroundColor Green
try {
    pip install redis redis-py
    Write-Host "✅ Python Redis client installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Failed to install Python Redis client" -ForegroundColor Red
    Write-Host "   Please run: pip install redis redis-py" -ForegroundColor Yellow
}

Write-Host ""

# Step 5: Install Node.js Redis client
Write-Host "Step 5: Installing Node.js Redis client..." -ForegroundColor Green
$frontendPath = "gui\Data-Visualizer-React"
if (Test-Path $frontendPath) {
    Set-Location $frontendPath
    
    try {
        npm install redis
        Write-Host "✅ Node.js Redis client installed" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to install Node.js Redis client" -ForegroundColor Red
        Write-Host "   Please run: cd gui\Data-Visualizer-React && npm install redis" -ForegroundColor Yellow
    }
    
    Set-Location $PSScriptRoot
}
else {
    Write-Host "⚠️  Frontend directory not found: $frontendPath" -ForegroundColor Yellow
    Write-Host "   Please install Node.js Redis client manually" -ForegroundColor Yellow
}

Write-Host ""

# Step 6: Create Redis configuration
Write-Host "Step 6: Creating Redis configuration..." -ForegroundColor Green
$configPath = "config\redis_config.py"

if (-NOT (Test-Path $configPath)) {
    try {
        $configContent = @"
# Redis Configuration for QuFLX
import os

# Redis connection settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis key patterns
TICK_LIST_PATTERN = "ticks:{asset}"  # e.g., ticks:EURUSD_otc
PUBSUB_CHANNEL_PATTERN = "updates:{asset}"  # e.g., updates:EURUSD_otc
HISTORICAL_CACHE_PATTERN = "historical:{asset}:{timeframe}"  # e.g., historical:EURUSD_otc:1M

# Redis settings
MAX_TICK_BUFFER_SIZE = 1000
HISTORICAL_CACHE_TTL = 3600  # 1 hour in seconds
BATCH_PROCESSING_INTERVAL = 30  # seconds
HISTORICAL_CACHE_SIZE = 200  # candles

# Performance settings
CONNECTION_POOL_SIZE = 10
SOCKET_TIMEOUT = 5  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds
"@
        
        $configContent | Out-File -FilePath $configPath -Encoding UTF8
        Write-Host "✅ Redis configuration created: $configPath" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to create Redis configuration" -ForegroundColor Red
    }
}
else {
    Write-Host "✅ Redis configuration already exists: $configPath" -ForegroundColor Green
}

Write-Host ""

# Step 7: Create environment file
Write-Host "Step 7: Creating environment file..." -ForegroundColor Green
$envPath = ".env.redis"

if (-NOT (Test-Path $envPath)) {
    try {
        $envContent = @"
# Redis Environment Configuration for QuFLX
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=
"@
        
        $envContent | Out-File -FilePath $envPath -Encoding UTF8
        Write-Host "✅ Environment file created: $envPath" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ Failed to create environment file" -ForegroundColor Red
    }
}
else {
    Write-Host "✅ Environment file already exists: $envPath" -ForegroundColor Green
}

Write-Host ""

# Step 8: Final verification
Write-Host "Step 8: Final verification..." -ForegroundColor Green
try {
    $redisTest = redis-cli ping
    if ($redisTest -eq "PONG") {
        Write-Host "✅ Redis setup completed successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Start the backend: python streaming_server.py" -ForegroundColor White
        Write-Host "2. Start the frontend: cd gui\Data-Visualizer-React && npm run dev" -ForegroundColor White
        Write-Host "3. Open browser to http://localhost:3000" -ForegroundColor White
        Write-Host ""
        Write-Host "Redis is running on localhost:6379" -ForegroundColor Green
        Write-Host "Configuration files created in config/ directory" -ForegroundColor Green
    }
    else {
        Write-Host "❌ Redis setup verification failed" -ForegroundColor Red
        Write-Host "   Please check Redis installation and service status" -ForegroundColor Yellow
    }
}
catch {
    Write-Host "❌ Final verification failed: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Redis Setup Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan