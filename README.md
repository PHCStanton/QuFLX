# QuantumFlux Trading Platform

A sophisticated automated trading platform for PocketOption combining real-time WebSocket data streaming, browser automation, and AI-driven technical analysis with an integrated React GUI for backtesting and strategy execution.

## 🎯 Current Status: Critical Architectural Refactoring Complete ✅ | Redis MCP Integration Complete ✅

### ✅ **Recently Completed** (October 25, 2025)
- **Redis MCP Server**: Custom Python 3.11+ compatible implementation with 12 specialized tools
- **MCP Configuration**: Updated `.kilocode/mcp.json` with Redis server configuration
- **Redis Integration**: Full backend/frontend integration with <1ms operations
- **Performance Testing**: Comprehensive demo and validation scripts working perfectly
- **Documentation**: Complete usage guides and setup instructions

### ✅ **Previously Completed** (October 7, 2025)
- **Asset Filtering Bug Fixed**: Asset filtering now at start of processing - prevents unwanted asset switches
- **Duplicate Candle Formation Eliminated**: Backend emits formed candles, frontend displays only - 70+ lines removed
- **Encapsulation Fixed**: Added proper API methods to capability, removed direct state access
- **Data Flow Simplified**: Single source of truth for candle formation - capability → server → frontend
- **Backpressure Handling**: 1000-item buffer limit prevents memory overflow
- **Port Configuration Fixed**: Vite now correctly serves on port 5000

### 🚀 **Core Capabilities**
- **Real-time WebSocket Data Streaming**: 22,000+ messages from PocketOption
- **Chrome Session Management**: Persistent hybrid session with remote debugging (port 9222)
- **Trading Capabilities**: Profile, favorites, session scanning, trade execution
- **Strategy Engine**: Quantum Flux with RSI, MACD, Bollinger Bands, EMAs
- **React Dashboard**: Modern UI for data analysis, backtesting, and live trading
- **Historical Backtesting**: Test strategies on CSV data with detailed results
- **Redis MCP Integration**: High-performance caching and real-time monitoring with 12 specialized tools

## Quick Start

### Prerequisites
- **Python 3.11+** (Python 3.11.13 recommended)
- **Node.js 16+** with npm/pnpm
- **Chrome browser** (for PocketOption integration)
- **uv** (Python package installer)
- **Redis Server** (for high-performance caching and MCP integration)

### Option 1: GUI Backtesting (Simplest)

**Start Backend** (Terminal 1):
```bash
uv run python streaming_server.py
```

**Start Frontend** (Terminal 2):
```bash
cd gui/Data-Visualizer-React
npm install  # First time only
npm run dev
```

**Access Dashboard**: http://localhost:5000

**Navigate to**:
- **Strategy Backtest** page to test strategies on historical data
- **Live Trading** page for real-time data and signals
- **Data Analysis** page for chart analysis

### Option 2: Full Platform (Live Trading)

1. **Start Chrome Session**:
```bash
python start_hybrid_session.py
# Log into PocketOption manually, navigate to trading interface
```

2. **Start Backend**:
```bash
python backend.py
```

3. **Start GUI** (in new terminal):
```bash
cd gui/Data-Visualizer-React
npm run dev
```

## Application URLs

| Component | URL | Status |
|-----------|-----|--------|
| **React GUI** | http://localhost:5000 | ✅ Running |
| **Backend API** | http://localhost:8000 | ✅ Running |
| **GUI Backend** | http://localhost:3001 | ✅ Running |
| **Redis Server** | localhost:6379 | ✅ Running |
| **Redis MCP** | 12 tools available | ✅ Ready |
| **API Docs** | http://localhost:8000/docs | ✅ Available |

## Features

### GUI Backtesting (New! ✨)
- **File Selection**: Auto-discover 100+ historical CSV files
- **Strategy Testing**: Run Quantum Flux on historical data
- **Results Dashboard**: Win rate, profit/loss, trade history
- **Real-time Updates**: Socket.IO for instant results
- **Multiple Formats**: Supports OTC and HLOC CSV formats

### Real-time Trading
- **Live Data Streaming**: Real-time tick and candle updates via WebSocket
- **Signal Generation**: AI-driven buy/sell signals with confidence scores
- **Trade Execution**: Automated trade placement with verification
- **Session Management**: Persistent Chrome sessions across restarts

### Data Collection
- **WebSocket Interception**: Capture market data from PocketOption
- **Candle Formation**: OHLC candles with multiple timeframes (1m, 5m, 15m, 1h)
- **CSV Export**: Organized storage by timeframe
- **Smart Detection**: Automatic asset and timeframe identification

### Strategy Engine
- **Quantum Flux**: Multi-indicator strategy (RSI, MACD, Bollinger Bands, EMAs)
- **Confidence Scoring**: Signal strength evaluation (0-100%)
- **Backtesting**: Historical performance analysis
- **Live Execution**: Real-time strategy application

## Project Structure

```
QuantumFlux/
├── streaming_server.py              # Flask-SocketIO backend (Port 3001) ✨
├── gui/Data-Visualizer-React/       # React GUI
│   ├── src/                         # Frontend source
│   │   ├── pages/
│   │   │   ├── StrategyBacktest.jsx # Backtesting interface ✨
│   │   │   ├── LiveTrading.jsx      # Real-time trading
│   │   │   └── DataAnalysis.jsx     # Data analysis
│   │   ├── services/
│   │   │   └── StrategyService.js   # Socket.IO integration ✨
│   │   └── components/              # UI components
│   ├── data_loader.py               # CSV loading & backtest engine ✨
│   └── data_history/pocket_option/  # Historical CSV files (100+)
├── strategies/
│   ├── quantum_flux_strategy.py     # Main strategy ✨
│   ├── base.py                      # Strategy base class
│   └── technical_indicators.py      # Indicator calculations
├── capabilities/
│   ├── data_streaming.py            # WebSocket data collection
│   ├── session_scan.py              # Account state monitoring
│   ├── profile_scan.py              # Profile extraction
│   ├── favorite_select.py           # Asset selection
│   └── trade_click_cap.py           # Trade execution
├── backend.py                       # FastAPI backend
├── start_hybrid_session.py          # Chrome session launcher
└── qf.py                            # CLI interface
```

## API Endpoints

### GUI Backend (Port 3001) - Socket.IO
- `run_backtest` - Execute strategy backtest on CSV data
- `get_available_data` - List available historical files
- `generate_signal` - Generate trading signal from candles
- `execute_strategy` - Execute strategy on live data
- `start_stream` / `stop_stream` - Control real-time data flow

### Main Backend (Port 8000) - REST/WebSocket
- `GET /status` - Connection status
- `GET /health` - Health check
- `GET /api/profile` - User profile
- `GET /api/favorites` - Asset favorites
- `POST /api/operations/trade` - Trade execution
- `WS /ws/data` - Real-time data stream

## CLI Interface

```bash
# Attach to Chrome session
python qf.py attach --port 9222

# Collect data snapshot
python qf.py stream snapshot --period 1

# Scan profile and favorites
python qf.py quick-scan

# Generate signals
python qf.py signal EURUSD

# Execute trade (dry-run)
python qf.py trade buy --dry-run
```

## Configuration

### Strategy Configuration
Located in `strategies/quantum_flux_strategy.py`:
- RSI Period: 14
- MACD: Fast 12, Slow 26, Signal 9
- Bollinger Bands: Period 20, Std Dev 2
- EMAs: 12, 26

### Data Configuration
CSV files in `gui/Data-Visualizer-React/data_history/pocket_option/`:
- Format: `timestamp,open,close,high,low`
- Timeframe detection: From filename or directory
- Volume: Defaults to 1000.0 if missing

## Development

### Backend Development
```bash
# Main backend (FastAPI)
uvicorn backend:app --reload --port 8000

# GUI backend (Flask-SocketIO)
uv run python streaming_server.py
```

### Frontend Development
```bash
cd gui/Data-Visualizer-React
npm install
npm run dev          # Development server
npm run build        # Production build
npm run preview      # Preview production
```

### Testing
```bash
# Run smoke tests
python test_smoke.py

# Test capabilities
python capabilities/data_streaming.py --verbose
```

## Troubleshooting

### GUI Backend Issues
```bash
# Check backend status
curl http://localhost:3001/health

# Verify data files
ls gui/Data-Visualizer-React/data_history/pocket_option/
```

### Chrome Connection Issues
```bash
# Check if Chrome is on port 9222
netstat -an | findstr 9222

# Restart Chrome session
python start_hybrid_session.py
```

### Frontend Issues
```bash
# Clear and reinstall
cd gui/Data-Visualizer-React
rm -rf node_modules package-lock.json
npm install

# Check browser console for errors (F12)
```

## Recent Updates

### October 7, 2025
- ✅ Fixed critical asset filtering bug (filtering at start of processing)
- ✅ Eliminated duplicate candle formation (single source of truth)
- ✅ Added proper API methods to capability (clean encapsulation)
- ✅ Simplified data flow (capability → server → frontend)
- ✅ Added backpressure handling (1000-item buffer limit)
- ✅ Fixed Vite port configuration (now on port 5000)

### October 4, 2025
- ✅ Integrated backtesting into React GUI
- ✅ Socket.IO backend with 4 event handlers
- ✅ Smart CSV file discovery (100+ files)
- ✅ Fixed profit calculation in backtest engine
- ✅ Code quality improvements (type hints, removed unused code)
- ✅ Simplified price mapping architecture

## Support

For issues or questions:
1. Check `.agent-memory/project-status.md` for latest system state
2. Review workflow logs for error messages
3. Verify both backend and frontend are running
4. Check browser console for JavaScript errors
5. Ensure CSV data files are accessible

## Documentation Structure

### Redis Integration Documentation
- **App Integration**: [`dev_docs/redis_docs/`](dev_docs/redis_docs/) - Backend/frontend Redis integration
- **MCP Documentation**: [`MCP_docs/redis_mcp/`](MCP_docs/redis_mcp/) - Redis MCP server and tools

### Key Documents
- **Redis Integration Guide**: [`dev_docs/redis_docs/README.md`](dev_docs/redis_docs/README.md)
- **Redis MCP Usage**: [`MCP_docs/redis_mcp/README.md`](MCP_docs/redis_mcp/README.md)
- **Complete Status**: [`MCP_docs/redis_mcp/Redis_MCP_Status_Summary.md`](MCP_docs/redis_mcp/Redis_MCP_Status_Summary.md)

## Next Steps

### Immediate
- Test backtesting with various CSV files
- Experiment with strategy parameters
- Collect more historical data

### Near Future
- Add more strategy options
- Implement strategy comparison
- Enhanced performance metrics
- Trade execution from GUI

## Success Metrics

✅ GUI backtesting fully functional  
✅ 100+ CSV files discoverable and loadable  
✅ Quantum Flux strategy integrated  
✅ Real-time data streaming working  
✅ Socket.IO backend operational  
✅ Both workflows running without errors  

**The platform is ready for backtesting and strategy development! 🚀**
