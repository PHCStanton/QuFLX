# QuantumFlux Trading Platform - Project Status

## Current Status: Backtesting & Strategy Integration Complete ✅

**Last Updated**: October 4, 2025

### Project State
The system now has a fully functional backtesting and live strategy execution infrastructure integrated into the React GUI. Both historical CSV-based backtesting and real-time WebSocket streaming use the same Quantum Flux strategy codebase.

### Recent Completions (October 4, 2025)

#### 1. Backtesting Infrastructure ✅
- Created `gui/Data-Visualizer-React/data_loader.py` with CSV loading and backtest engine
- Smart file discovery finds 100+ CSV files recursively (both OTC format and HLOC directories)
- Backtest engine simulates trades with win/loss tracking and profit calculation
- Intelligent timeframe detection from filename or parent directory

#### 2. Socket.IO Backend Integration ✅
- Extended `gui/Data-Visualizer-React/streaming_server.py` with 4 Socket.IO handlers:
  - `run_backtest` - Execute strategy backtests on historical data
  - `get_available_data` - List all available CSV files
  - `generate_signal` - Generate trading signals from candle data
  - `execute_strategy` - Execute strategy on live streaming data
- Backend runs on port 3001 (Flask-SocketIO)

#### 3. Frontend Integration ✅
- Updated `src/services/StrategyService.js` to use Socket.IO for all backend communication
- Built fully functional `src/pages/StrategyBacktest.jsx` with:
  - File selection dropdown (auto-populated)
  - Strategy selection (Quantum Flux)
  - Backtest configuration (capital, position size)
  - Live results display with trade history

#### 4. Strategy System ✅
- Simplified `strategies/quantum_flux_strategy.py` for GUI integration
- Core indicators: RSI, MACD, Bollinger Bands, EMAs
- Signal generation with confidence scores
- Both JSON (client-side) and Python (server-side) strategy support

#### 5. Code Quality Improvements ✅
- Fixed type hint error in `quantum_flux_strategy.py` (Optional[Dict] support)
- Removed unused `date` parameter from `load_asset_data()`
- Simplified redundant price_map dictionaries into single `ASSET_PRICES` constant
- All functionality preserved, cleaner codebase

### Current Workflows
- **Backend**: `cd gui/Data-Visualizer-React && uv run python streaming_server.py` (Port 3001)
- **Frontend**: `cd gui/Data-Visualizer-React && npm run dev` (Port 5000)

### Data Organization
```
gui/Data-Visualizer-React/data_history/pocket_option/
├── AUDCAD_otc_otc_1m_2025_10_04_18_57_10.csv    # OTC format files
├── AUDCAD_otc_otc_5m_2025_10_04_18_57_10.csv
└── HLOC/
    ├── data_1m/AUDCAD_2024_2_5_11.csv            # Organized by timeframe
    └── data_5m/AUDCAD_2024_2_5_11.csv
```

### Key Architectural Decisions

1. **Socket.IO for Unified Communication**
   - Both data streaming and strategy execution use Socket.IO
   - Single communication protocol for simplicity
   - Real-time bidirectional updates

2. **CSV Format**: `timestamp,open,close,high,low` (UTC, no volume)
   - Volume defaults to 1000.0 if missing
   - Pandas DataFrame processing

3. **File Discovery**
   - Recursive search with `rglob("*.csv")`
   - Timeframe inference from filename or directory
   - Supports multiple data formats

4. **Data Loading Strategy**
   - `load_asset_data()` accepts file path OR asset name
   - Exact match first, fallback to partial match
   - Returns most recent file when multiple matches

### Known Issues (Non-Critical)
- 7 LSP diagnostics showing (false positives - import resolution)
  - Packages are installed and working (pandas, numpy, flask, eventlet)
  - LSP just can't see them in environment
  - Does not affect runtime

### Next Steps for User
Ready for documentation review and potential deployment preparation.

### System Health
- ✅ Backend running successfully (port 3001)
- ✅ Frontend running successfully (port 5000)
- ✅ 100+ CSV files discovered and accessible
- ✅ Backtest engine functional
- ✅ Strategy execution working
- ✅ No runtime errors

### Important Notes for Future Sessions
- `strategies/strategy_calibration/` is for offline testing only, NOT runtime integration
- Backend uses Flask-SocketIO (not regular Socket.IO server)
- Frontend uses Vite dev server on port 5000
- CSV files must have timestamp column in datetime format
- Quantum Flux strategy requires minimum 50 candles for signal generation
