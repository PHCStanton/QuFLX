# Trading System Refactor TODO

## 🎯 Objective
Refactor the trading system to make `data_streaming.py` the core engine with thin API/CLI layers on top, enabling efficient data collection, backtesting, and system orchestration.

## 📋 Phase 1: Core Infrastructure (Priority: HIGH)

### 🔧 Backend Development (`backend.py`)
- [ ] **Create new backend.py with FastAPI**
  - [ ] Remove adapter indirection - direct WebDriver attachment
  - [ ] Implement capability-focused endpoints
  - [ ] Use `data_streaming` as core engine

#### API Endpoints to Implement:
- [ ] **POST /session/attach**
  - [ ] Accept: `port=9222`, `user_data_dir` (optional, default `./Chrome_profile`)
  - [ ] Action: Attach Selenium to running Chrome via debuggerAddress
  - [ ] Return: `{ connected: true, current_url, attached_at }`

- [ ] **GET /status**
  - [ ] Return: `{ webdriver_connected, session_info, streaming: {...} }`

- [ ] **POST /stream/snapshot**
  - [ ] Accept: `period` (minutes, default 1), `stream_mode` (candle|tick|both), `asset_focus` (bool)
  - [ ] Action: Configure RealtimeDataStreaming, run single batch
  - [ ] Return: JSON summary with candles_summary, current_asset, artifact_path

- [ ] **GET /candles/{asset}**
  - [ ] Query param: `count=100`
  - [ ] Return: Last N candles from in-memory CANDLES

#### Capabilities Wrappers:
- [ ] **GET /operations/profile** → ProfileScan
- [ ] **GET /operations/favorites** → FavoriteSelect
  - [ ] Query params: `min_pct=92`, `select=first|last`
- [ ] **GET /operations/session** → SessionScan
- [ ] **POST /operations/trade** → TradeClick
  - [ ] Body: `{ side: buy|sell, timeout? }`

#### Optional MVP Features:
- [ ] **GET /signal/{asset}** → SignalGeneration
  - [ ] Query params: `min_candles=30`, `types=SMA,RSI`

### 🖥️ CLI Development (`qf.py`)
- [ ] **Create Typer-based CLI utility**
- [ ] **Implement subcommands:**
  - [ ] `python qf.py attach --port 9222`
  - [ ] `python qf.py stream snapshot --period 1 --mode both --asset-focus`
  - [ ] `python qf.py profile`
  - [ ] `python qf.py favorites --min-pct 92 --select first`
  - [ ] `python qf.py trade --side buy --timeout 5`
  - [ ] `python qf.py signal --asset EURUSD --min-candles 30 --types SMA,RSI`

### 🚀 Orchestration Scripts
- [ ] **Create `scripts/start_all.ps1`**
  - [ ] Start Hybrid Chrome Session in separate window
  - [ ] Wait for port 9222 to respond (`Test-NetConnection`)
  - [ ] Start backend via uvicorn
  - [ ] Print next-step commands

### ✅ Phase 1 Validation
- [ ] **Smoke Tests**
  - [ ] Chrome starts and listens on port 9222
  - [ ] Backend attaches successfully via `/session/attach`
  - [ ] Snapshot endpoint creates CSV in `data/Historical_Data/data_stream`
  - [ ] All capability endpoints respond correctly
  - [ ] CLI commands work end-to-end

## 📋 Phase 2: Advanced Features (Priority: MEDIUM)

### 🔄 Real-time Streaming
- [ ] **Background streaming loop with stop event**
  - [ ] Non-blocking stream_continuous() implementation
  - [ ] Internal stop/start controls

- [ ] **WebSocket endpoint `/ws/data`**
  - [ ] Real-time data streaming to clients
  - [ ] Connect to GUI for live updates

### 🎨 User Interface Enhancements
- [ ] **TUI Development (textual)**
  - [ ] Dashboard panels: status, session, stream, logs, actions
  - [ ] Controls: attach, stream start/stop, snapshot, quick ops

- [ ] **GUI Integration Updates**
  - [ ] Replace CSV loading with WebSocket `/ws/data`
  - [ ] Connect to REST `/api` endpoints
  - [ ] Maintain existing functionality at `localhost:5173`

## 📁 File Structure

```
project/
├── backend.py              # ✅ New FastAPI backend
├── qf.py                   # ✅ New CLI utility
├── data_streaming.py       # ✅ Core engine (existing)
├── start_hybrid_session.py # ✅ Chrome launcher (existing)
├── scripts/
│   └── start_all.ps1       # ✅ New orchestration script
├── data/
│   └── Historical_Data/
│       └── data_stream/    # ✅ CSV output location
└── Trading_Data_Visualizer/ # ✅ GUI (no changes Phase 1)
```

## 🎮 Usage Examples

### PowerShell Orchestration
```powershell
# Start everything at once
powershell -ExecutionPolicy Bypass -File .\scripts\start_all.ps1
```

### Individual Components
```bash
# Option A: Manual startup
python start_hybrid_session.py  # Terminal 1
python -m uvicorn backend:app --reload  # Terminal 2

# Option B: CLI usage
python qf.py attach --port 9222
python qf.py stream snapshot --period 1 --mode both --asset-focus
python qf.py favorites --min-pct 95 --select first
```

## 🔍 Success Criteria

### Phase 1 Complete When:
- [ ] All Phase 1 checkboxes completed
- [ ] Can collect data via CLI/API without manual intervention
- [ ] CSVs generate correctly in expected location
- [ ] All capability endpoints functional
- [ ] Orchestration script works reliably

### Phase 2 Complete When:
- [ ] Real-time streaming implemented with proper controls
- [ ] TUI provides intuitive system management
- [ ] GUI receives live data via WebSocket
- [ ] System is production-ready for backtesting workflows

## 🚦 Current Status
- [ ] **Ready to proceed with implementation**
- [ ] Waiting for approval to enter "Act mode"

---

**Next Action**: Generate `backend.py`, `scripts/start_all.ps1`, and `qf.py` files and run smoke tests.