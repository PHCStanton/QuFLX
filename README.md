# QuantumFlux Trading Dashboard

A comprehensive trading dashboard for AI-powered binary options trading with real-time data visualization and strategy testing capabilities.

## 🎯 **Current Status: Phase 2.5 COMPLETED - Ready for Phase 3**

### ✅ **Architectural Foundation Solidified**
- **Clean Architecture**: Eliminated dual API confusion, established capabilities-only approach
- **Zero Breaking Changes**: All existing functionality preserved
- **Phase 3 Ready**: Strategy engine and automation development can begin immediately

### 🚀 **Next Phase: Strategy Engine & Automation**
- Signal generation engine implementation
- Automated trading logic development
- Strategy testing and backtesting framework
- A/B testing capabilities

## Features

### ✅ **Completed & Operational**
- **Real-time WebSocket Data Streaming**: Processing 22,000+ messages from PocketOption
- **Chrome Session Management**: Persistent session attachment and reconnection
- **Trading Capabilities**: Profile scanning, favorites management, trade execution with diagnostics
- **FastAPI Backend**: Comprehensive API endpoints with error handling and health monitoring
- **Capabilities Framework**: Clean integration between trading operations and backend
- **Data Collection**: Historical candle data collection (~100 candles capability)

### 🚧 **Phase 3: Strategy Engine & Automation (Next)**
- Signal generation engine implementation
- Automated trading logic development
- Strategy testing and backtesting framework
- A/B testing capabilities

### 🎨 **Frontend (Phase 5)**
- Interactive charts and analytics with TradingView
- Modern React-based UI with Tailwind CSS
- Real-time WebSocket connectivity
- Risk management and trade execution controls

## 🚀 Quick Start Guide

### Prerequisites

- **Python 3.11+** (specifically Python 3.11.13)
- **Node.js 16+** with npm/pnpm
- **Windows PowerShell** (for conda environment)
- **Chrome browser** (for PocketOption integration)

---

## 📋 Step-by-Step Setup Instructions

### Step 1: Activate Conda Environment

**This is CRITICAL - Must be done first in every session:**

```powershell
PS C:\FinRL\quantumFlux> (& C:\Users\piete\anaconda3\shell\condabin\conda-hook.ps1) ; (conda activate quantumFlux)
(quantumFlux) PS C:\FinRL\quantumFlux>
```

**Expected output:**
```
(quantumFlux) PS C:\FinRL\quantumFlux>
```

### Step 2: Start Backend Server

```powershell
(quantumFlux) PS C:\FinRL\quantumFlux> python backend.py
```

**Expected output:**
```
Warning: Could not import MockTradingEngine
INFO:     Started server process [22356]
INFO:     Waiting for application startup.
[2025-08-21 12:20:13] Failed to set registry: [WinError 5] Access is denied
[2025-08-21 12:20:42] WebDriver initialized successfully
[2025-08-21 12:20:42] Connecting to https://pocket2.click/cabinet/demo-quick-high-low
[2025-08-21 12:20:57] Authentication verified - trading interface accessible
[2025-08-21 12:20:57] Connected to platform successfully
[2025-08-21 12:20:57] WebSocket data collection started
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Keep this terminal running!**

### Step 3: Start Frontend Dashboard (New Terminal)

Open a **NEW PowerShell terminal** and run:

```powershell
PS C:\FinRL\quantumFlux> cd dashboard
PS C:\FinRL\quantumFlux\dashboard> pnpm dev
```

**Expected output:**
```
> react-template@0.0.0 dev C:\FinRL\quantumFlux\dashboard
> vite

  VITE v5.4.19  ready in 2085 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Keep this terminal running too!**

### Step 4: Access Your Dashboard

Open your web browser and navigate to:
**http://localhost:5173/**

---

## 🖥️ Application URLs

| Component | URL | Status |
|-----------|-----|--------|
| **Frontend Dashboard** | http://localhost:5173/ | ✅ Running |
| **Backend API** | http://localhost:8000 | ✅ Running |
| **API Documentation** | http://localhost:8000/docs | ✅ Available |

---

## 🛠️ Troubleshooting

### If Backend Fails to Start

1. **Check Python Version:**
```powershell
python --version
# Should show: Python 3.11.13
```

2. **Verify Conda Environment:**
```powershell
conda env list
# Should show quantumFlux environment as active
```

3. **Install Missing Dependencies:**
```powershell
pip install -r requirements.txt
```

### If Frontend Fails to Start

1. **Install Node Dependencies:**
```powershell
cd dashboard
pnpm install
```

2. **Clear Node Modules and Reinstall:**
```powershell
rm -rf node_modules package-lock.json
pnpm install
```

### If Dashboard Won't Load

1. **Check Backend is Running:**
   - Visit http://localhost:8000
   - Should show JSON response with API info

2. **Check CORS Issues:**
   - Backend automatically handles CORS for React frontend

3. **Clear Browser Cache:**
   - Hard refresh: Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)

---

## 📊 API Endpoints

### ✅ **Operational Endpoints**
- `GET /status` - Get connection status ✅
- `GET /health` - Comprehensive health check ✅
- `GET /api/profile` - User profile scanning ✅
- `GET /api/favorites` - Asset favorites scanning ✅
- `POST /api/operations/trade` - Trade execution ✅
- `GET /api/session` - Session status ✅
- `WS /ws/data` - Real-time WebSocket data stream ✅

### 🚧 **Phase 3 Endpoints (Next)**
- `POST /strategies` - Add new trading strategy
- `GET /strategies` - List all strategies
- `GET /trade/signal/{asset}` - Generate trading signals
- `POST /auto-trading/start` - Start automated trading
- `POST /tests/ab` - Start A/B strategy test
- `GET /tests/{test_id}` - Get test status

---

## 🎯 Dashboard Features

### Real-time Features
- Live market data from PocketOption
- Real-time candle updates
- WebSocket connectivity status
- Live strategy performance

### Analytics & Charts
- Interactive charts with Recharts
- Performance metrics visualization
- Strategy comparison tools
- Risk management displays

### Trading Tools
- Strategy testing interface
- Backtesting capabilities
- Trade execution monitoring
- Risk management controls

---

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the root directory:

```env
# API Keys (if needed)
POCKET_OPTION_API_KEY=your_key_here

# Database Configuration
DATABASE_URL=sqlite:///./quantumflux.db

# Trading Configuration
DEFAULT_STRATEGY=quantum_flux
MAX_TRADE_AMOUNT=100.0
RISK_PERCENTAGE=0.02
```

### Strategy Configuration
Strategies are configured in `config/strategies/quantum_flux_1min.json`:

```json
{
  "bot_name": "Quantum-Flux-Binary-Optimized",
  "version": "2.1.0",
  "description": "Binary options optimized version with 63.2% win rate",
  "optimization_date": "2025-08-09",
  "strategy": {
    "name": "Quantum-Flux-Binary-Optimized",
    "type": "multi_phase",
    "target_market": "binary_options_1min",
    "phases": {
      "neural": {
        "weight": 0.4,
        "enabled": true
      },
      "beast": {
        "weight": 0.35,
        "enabled": true
      },
      "quantum": {
        "weight": 0.25,
        "enabled": true
      }
    }
  }
}
```

---

## 🚀 Development

### Backend Development
```powershell
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Run with auto-reload
uvicorn backend:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```powershell
cd dashboard

# Install dependencies
pnpm install

# Start development server
pnpm dev

# Build for production
pnpm build

# Preview production build
pnpm preview
```

---

## 📝 Support

If you encounter issues:

1. **Check the terminals** for error messages
2. **Verify all URLs** are accessible
3. **Check browser console** for JavaScript errors
4. **Ensure conda environment** is activated
5. **Verify Python and Node versions**

For technical support, check the AGENT-MEMORY folder for detailed system status and troubleshooting information.

---

## 🎉 Success!

### ✅ **Current Achievements**
Once both servers are running, you'll have a fully functional trading backend with:
- ✅ Real-time WebSocket data streaming (22,000+ messages processed)
- ✅ Chrome session management and reconnection
- ✅ Complete trading capabilities (profile, favorites, trade execution)
- ✅ Comprehensive API with health monitoring
- ✅ Clean capabilities-only architecture

### 🚀 **Next Phase: Strategy Engine & Automation**
Phase 3 development can begin immediately with:
- Signal generation engine implementation
- Automated trading logic development
- Strategy testing and backtesting framework
- A/B testing capabilities

### 🎨 **Future: GUI Integration (Phase 5)**
- Interactive charts with TradingView
- Modern React-based UI with Tailwind CSS
- Real-time WebSocket connectivity
- Risk management and trade execution controls

**The foundation is solid - Phase 3 development ready to launch! 🚀**
