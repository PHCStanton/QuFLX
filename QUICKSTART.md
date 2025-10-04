# QuantumFlux Trading Platform - Quick Start Guide

## 🚀 Simplified Architecture Solution

The backend integration issues have been resolved with a **capabilities-first approach** that eliminates complex adapter layers and uses `data_streaming.py` as the core engine.

### ✅ What's Fixed

- **Direct Capabilities Integration**: Backend imports capabilities directly, no complex adapters
- **Chrome Session Management**: Simplified attachment using workspace `Chrome_profile`
- **Data Streaming Core**: `RealtimeDataStreaming` handles all WebSocket data collection and CSV export
- **Clean API Endpoints**: Minimal FastAPI backend with essential trading operations
- **CLI Interface**: Simple `qf.py` command-line tool for all operations

### 🎯 Best Solution: Minimal Complexity

Instead of fixing complex architectural conflicts, we've created a **clean, minimal solution**:

1. **New `backend.py`**: Direct capabilities integration, no adapter complexity
2. **PowerShell Launcher**: `scripts/start_all.ps1` starts Chrome + backend together
3. **CLI Tool**: `qf.py` provides command-line access to all capabilities
4. **Smoke Test**: `test_smoke.py` verifies everything works

## 🏃‍♂️ Quick Start (3 Steps)

### Step 1: Start the Platform
```powershell
# Option A: Start everything together (recommended)
.\scripts\start_all.ps1

# Option B: Start components separately
python start_hybrid_session.py  # Start Chrome
python backend.py               # Start API (in another terminal)
```

### Step 2: Test the System
```powershell
# Run smoke test to verify everything works
python test_smoke.py

# Or test individual components
python qf.py attach --port 9222
python qf.py status
python qf.py stream snapshot --period 1
```

### Step 3: Use the Platform
```powershell
# CLI Operations
python qf.py profile                    # Scan user profile
python qf.py favorites --min-pct 92     # Scan favorites
python qf.py session                    # Check session state
python qf.py signal EURUSD              # Generate signals
python qf.py trade buy --dry-run        # Test trade (safe)

# API Operations (if backend running)
curl http://localhost:8000/status       # Check status
curl http://localhost:8000/health       # Health check
```

## 📊 Core Capabilities

### Data Streaming (`data_streaming.py`)
- **WebSocket Data Collection**: Real-time market data from PocketOption
- **Candle Formation**: OHLC candles with configurable timeframes
- **CSV Export**: Automatic data persistence to `Historical_Data/data_stream/`
- **Session Sync**: Detects user's selected asset and timeframe

### Trading Operations
- **Profile Scan**: Account info, balance, user details
- **Favorites Scan**: Find assets with payout ≥ threshold
- **Session Scan**: Current account state and trade amount
- **Trade Execution**: BUY/SELL with confirmation and diagnostics
- **Signal Generation**: Technical analysis (SMA, RSI, MACD)

### Chrome Session Management
- **Hybrid Approach**: Persistent Chrome session with remote debugging
- **Workspace Profile**: Uses `Chrome_profile/` directory for session persistence
- **Auto-Attachment**: Backend and CLI automatically connect to existing session

## 🔧 API Endpoints

### Session Management
- `POST /session/attach` - Attach to Chrome session
- `POST /session/disconnect` - Disconnect from Chrome
- `GET /status` - System status and connection info

### Data Operations
- `POST /stream/snapshot` - Collect data snapshot
- `GET /stream/status` - Streaming status
- `GET /candles/{asset}` - Get candle data
- `GET /assets` - List available assets

### Trading Operations
- `GET /operations/profile` - Scan user profile
- `GET /operations/favorites` - Scan favorites bar
- `GET /operations/session` - Scan current session
- `POST /operations/trade` - Execute trade

### Analysis
- `GET /signal/{asset}` - Generate trading signals
- `GET /health` - Health check
- `WebSocket /ws/data` - Real-time data stream

## 💡 Usage Examples

### CLI Workflow
```powershell
# 1. Start platform
.\scripts\start_all.ps1

# 2. In another terminal, test connection
python qf.py attach
python qf.py status

# 3. Collect data
python qf.py stream snapshot --period 1 --mode candle

# 4. Analyze account
python qf.py quick-scan

# 5. Generate signals
python qf.py signal EURUSD --types SMA,RSI

# 6. Execute trade (with confirmation)
python qf.py trade buy
```

### API Workflow
```bash
# 1. Check if backend is running
curl http://localhost:8000/health

# 2. Attach to Chrome session
curl -X POST http://localhost:8000/session/attach

# 3. Collect data snapshot
curl -X POST "http://localhost:8000/stream/snapshot?period=1&mode=candle"

# 4. Get profile info
curl http://localhost:8000/operations/profile

# 5. Generate signals
curl http://localhost:8000/signal/EURUSD
```

### Continuous Data Streaming
```powershell
# Stream real-time data to terminal
python qf.py stream continuous --period 1 --mode candle

# Or use data_streaming.py directly
python capabilities/data_streaming.py --stream --period 1 --candle_only
```

## 📁 File Structure

```
QuFLX/
├── backend.py                 # New minimal FastAPI backend
├── qf.py                     # CLI interface
├── test_smoke.py             # Smoke test
├── start_hybrid_session.py   # Chrome session starter
├── scripts/
│   └── start_all.ps1         # Platform launcher
├── capabilities/
│   ├── data_streaming.py     # Core data engine
│   ├── session_scan.py       # Session operations
│   ├── profile_scan.py       # Profile operations
│   ├── favorite_select.py    # Favorites operations
│   ├── trade_click_cap.py    # Trade execution
│   └── signal_generation.py  # Signal analysis
├── Chrome_profile/           # Persistent Chrome session
└── Historical_Data/
    └── data_stream/          # CSV exports
```

## 🔍 Troubleshooting

### Chrome Connection Issues
```powershell
# Check if Chrome is running with remote debugging
netstat -an | findstr 9222

# Restart Chrome session
python start_hybrid_session.py

# Test attachment
python qf.py attach --port 9222
```

### Backend Issues
```powershell
# Check if backend is running
curl http://localhost:8000/health

# Start backend manually
python backend.py

# Check logs for errors
```

### Data Collection Issues
```powershell
# Test data streaming directly
python capabilities/data_streaming.py --verbose

# Check CSV output
dir Historical_Data\data_stream\*.csv

# Run smoke test
python test_smoke.py
```

## 🎯 Key Benefits

1. **Minimal Complexity**: Direct capabilities integration, no complex adapters
2. **Proven Foundation**: Uses existing `data_streaming.py` that already works
3. **Easy Testing**: Simple CLI and smoke test for verification
4. **Clean Architecture**: Eliminates architectural conflicts and confusion
5. **Immediate Usability**: Works out of the box with existing Chrome sessions

## 🚀 Next Steps

1. **Test the Solution**: Run `python test_smoke.py` to verify everything works
2. **Collect Real Data**: Use `python qf.py stream snapshot` to collect market data
3. **Explore Capabilities**: Try `python qf.py --help` to see all available commands
4. **API Integration**: Use the FastAPI backend for GUI or external integrations
5. **Extend as Needed**: Add new capabilities or endpoints based on requirements

This solution provides a **clean, working foundation** that eliminates the backend integration complexity while maintaining all the powerful capabilities of the QuantumFlux platform.
