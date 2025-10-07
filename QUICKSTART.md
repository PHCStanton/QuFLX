# QuantumFlux Trading Platform - Quick Start Guide

## 🎯 Current Status

The platform has **critical architectural improvements complete**! Recent fixes include asset filtering, duplicate candle elimination, and clean API encapsulation. GUI backtesting is fully integrated for testing strategies on historical data through a modern React interface.

## 🚀 Quick Start Options

### Option 1: GUI Backtesting (Recommended for Testing)

Perfect for strategy development and testing without live trading.

**Step 1: Start Backend**
```bash
uv run python streaming_server.py
```

Expected output:
```
Starting streaming server on http://0.0.0.0:3001
(xxxx) wsgi starting up on http://0.0.0.0:3001
```

**Step 2: Start Frontend** (New Terminal)
```bash
cd gui/Data-Visualizer-React
npm install  # First time only
npm run dev
```

Expected output:
```
VITE v5.4.20  ready in 399 ms
➜  Local:   http://localhost:5000/
➜  Network: http://172.31.70.130:5000/
```

**Step 3: Open Dashboard**

Navigate to: **http://localhost:5000**

**Step 4: Run a Backtest**
1. Click **"Strategy Backtest"** in the navigation
2. Select a data file from dropdown (100+ files available)
3. Configure settings (or use defaults)
4. Click **"Run Backtest"**
5. View results instantly!

### Option 2: Full Platform (Live Trading)

For live data collection and automated trading.

**Step 1: Start Chrome Session**
```bash
python start_hybrid_session.py
```
- Chrome will open automatically
- Log into PocketOption
- Navigate to the trading interface

**Step 2: Start Main Backend** (New Terminal)
```bash
python backend.py
```

Expected output:
```
INFO:     Started server process [xxxx]
INFO:     Uvicorn running on http://0.0.0.0:8000
[...] WebDriver initialized successfully
[...] Connected to platform successfully
```

**Step 3: Start GUI Backend** (New Terminal)
```bash
uv run python streaming_server.py
```

**Step 4: Start Frontend** (New Terminal)
```bash
cd gui/Data-Visualizer-React
npm run dev
```

**Step 5: Access Platform**
- Main Backend: http://localhost:8000
- GUI: http://localhost:5000
- API Docs: http://localhost:8000/docs

## 📊 What's Available

### GUI Features
- **Strategy Backtest**: Test strategies on 100+ historical CSV files
- **Live Trading**: Real-time data streaming and signals
- **Data Analysis**: Interactive charts and technical indicators
- **Real-time Updates**: Socket.IO for instant results

### Data Files
Located in `gui/Data-Visualizer-React/data_history/pocket_option/`:
- OTC format: `AUDCAD_otc_otc_1m_2025_10_04...csv`
- HLOC format: In `data_1m/`, `data_5m/` subdirectories
- **Total**: 100+ files automatically discovered

### Strategy
**Quantum Flux Strategy** includes:
- RSI (14 period)
- MACD (12, 26, 9)
- Bollinger Bands (20, 2 std dev)
- EMAs (12, 26)

## 💡 CLI Interface (Advanced)

```bash
# Attach to Chrome session
python qf.py attach --port 9222

# Check status
python qf.py status

# Collect data snapshot
python qf.py stream snapshot --period 1 --mode candle

# Scan profile and favorites
python qf.py quick-scan

# Generate signals
python qf.py signal EURUSD --types SMA,RSI

# Execute trade (dry-run)
python qf.py trade buy --dry-run
```

## 🔧 API Endpoints

### GUI Backend (Port 3001) - Socket.IO
```javascript
// Connect to backend
socket.connect('http://localhost:3001');

// Get available data files
socket.emit('get_available_data');
socket.on('available_data', (data) => {
  console.log(data.files);
});

// Run backtest
socket.emit('run_backtest', {
  file_path: 'path/to/data.csv',
  strategy: 'quantum_flux'
});
socket.on('backtest_complete', (results) => {
  console.log(results);
});

// Generate signal
socket.emit('generate_signal', {
  candles: [...],
  strategy: 'quantum_flux'
});
```

### Main Backend (Port 8000) - REST
```bash
# Health check
curl http://localhost:8000/health

# Get status
curl http://localhost:8000/status

# Get profile
curl http://localhost:8000/api/profile

# Get favorites
curl "http://localhost:8000/api/favorites?min_pct=92"

# Execute trade
curl -X POST http://localhost:8000/api/operations/trade \
  -H "Content-Type: application/json" \
  -d '{"side": "buy", "timeout": 5}'
```

## 📁 File Structure

```
QuantumFlux/
├── gui/Data-Visualizer-React/
│   ├── streaming_server.py        # Flask-SocketIO backend (Port 3001)
│   ├── data_loader.py             # CSV loading & backtest engine
│   ├── data_history/              # Historical data (100+ files)
│   └── src/
│       ├── pages/
│       │   ├── StrategyBacktest.jsx  # Backtesting interface
│       │   ├── LiveTrading.jsx       # Real-time trading
│       │   └── DataAnalysis.jsx      # Data analysis
│       └── services/
│           └── StrategyService.js    # Socket.IO integration
├── strategies/
│   ├── quantum_flux_strategy.py   # Main strategy
│   └── base.py                    # Strategy base class
├── capabilities/
│   ├── data_streaming.py          # WebSocket data collection
│   ├── session_scan.py            # Session monitoring
│   └── trade_click_cap.py         # Trade execution
├── backend.py                     # FastAPI backend (Port 8000)
├── start_hybrid_session.py        # Chrome launcher
└── qf.py                          # CLI interface
```

## 🔍 Troubleshooting

### GUI Backend Not Starting
```bash
# Check Python version
python --version  # Should be 3.11+

# Install/update uv
pip install --upgrade uv

# Try running directly
cd gui/Data-Visualizer-React
python streaming_server.py
```

### Frontend Not Starting
```bash
# Clear cache and reinstall
cd gui/Data-Visualizer-React
rm -rf node_modules package-lock.json
npm install

# Try with pnpm
pnpm install
pnpm dev
```

### No Data Files Found
```bash
# Check if files exist
ls gui/Data-Visualizer-React/data_history/pocket_option/*.csv

# Check subdirectories
ls gui/Data-Visualizer-React/data_history/pocket_option/data_1m/*.csv
ls gui/Data-Visualizer-React/data_history/pocket_option/data_5m/*.csv
```

### Backend Connection Errors
```bash
# Check if ports are available
netstat -an | findstr "3001 8000"

# Kill processes on port (if needed)
# Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 3001).OwningProcess | Stop-Process

# Restart services
```

### Chrome Connection Issues
```bash
# Check Chrome remote debugging port
netstat -an | findstr 9222

# Restart Chrome session
python start_hybrid_session.py

# Test attachment
python qf.py attach --port 9222
```

## 🎯 Usage Examples

### Example 1: Quick Backtest
1. Start both backend and frontend
2. Go to Strategy Backtest page
3. Select first file in dropdown
4. Click "Run Backtest"
5. Review win rate and profit/loss

### Example 2: Live Data Collection
1. Start Chrome and log into PocketOption
2. Start main backend (`python backend.py`)
3. Use CLI: `python qf.py stream snapshot --period 1`
4. CSV files saved to `Historical_Data/data_stream/`

### Example 3: Signal Generation
1. Collect some candle data
2. Use CLI: `python qf.py signal EURUSD`
3. Review BUY/PUT/NEUTRAL signal with confidence

## 📈 Next Steps

1. **Test Backtesting**: Try different CSV files and compare results
2. **Collect Live Data**: Use Chrome session to gather fresh data
3. **Analyze Signals**: Generate signals on various assets
4. **Experiment**: Modify strategy parameters in `quantum_flux_strategy.py`

## ✅ Success Checklist

- [ ] Backend running on port 3001
- [ ] Frontend running on port 5000
- [ ] Can access GUI at http://localhost:5000
- [ ] Data files visible in dropdown
- [ ] Backtest completes successfully
- [ ] Results display correctly

## 🚀 You're Ready!

The platform is fully operational for:
- ✅ Strategy backtesting
- ✅ Historical data analysis
- ✅ Signal generation
- ✅ Live data collection (with Chrome session)
- ✅ Automated trading (with Chrome session)

**Start with backtesting to test strategies risk-free!**
