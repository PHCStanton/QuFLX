# QuantumFlux Trading Platform

**Last Updated**: October 9, 2025

## Overview

QuantumFlux is an automated trading platform for PocketOption, integrating real-time WebSocket data streaming, browser automation, and AI-driven technical analysis. It features a React-based GUI for backtesting and live streaming visualization. The platform captures live market data, converts it into OHLC candles, generates trading signals using technical indicators (SMA, RSI, MACD), executes automated trades, and provides a user-friendly interface for strategy development and testing.

**Target Users**: Algorithmic traders, quantitative researchers, and developers needing reliable real-time data, automated execution, and comprehensive market analysis.

## User Preferences

- **Communication style**: Simple, everyday language
- **Technical approach**: Clear separation of concerns, modular architecture
- **Data handling**: Explicit control over data sources (no auto-switching)

## System Architecture

### Core Architecture Pattern: Capabilities-First Design + Dual Data Pipelines

The platform uses a **capabilities-first architecture** with **two distinct data pipelines** for different use cases:

```
┌─────────────────────────────────────────────────────────────────┐
│                    CHROME SESSION (Port 9222)                   │
│                  ← WebSocket Data Interception →                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │      CAPABILITIES FRAMEWORK             │
        ├─────────────────────────────────────────┤
        │  1. RealtimeDataStreaming               │
        │     (data_streaming.py)                 │
        │     - Real-time candle formation        │
        │     - Asset focus filtering             │
        │     - Used by: streaming_server.py      │
        │                                         │
        │  2. RealtimeDataStreaming (CSV Save)    │
        │     (data_streaming_csv_save.py)        │
        │     - Historical topdown collection     │
        │     - Timeframe-organized storage       │
        │     - Used by: favorites_select...py    │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │         MULTIPLE INTERFACES             │
        ├─────────────────────────────────────────┤
        │  • streaming_server.py (Port 3001)      │
        │    → GUI Real-time Streaming            │
        │  • FastAPI Backend (Port 8000)          │
        │    → REST API Endpoints                 │
        │  • React GUI (Port 5000)                │
        │    → User Interface                     │
        │  • CLI Tool (qf.py)                     │
        │    → Command-line Access                │
        └─────────────────────────────────────────┘
```

### Two Distinct Data Pipelines

#### Pipeline 1: Historical/Topdown Collection (Backtesting)
```
capabilities/data_streaming_csv_save.py
        ↓
scripts/custom_sessions/favorites_select_topdown_collect.py
        ↓
Automated TF switching (1H → 15M → 5M → 1M)
        ↓
Captures ~100 candles per timeframe
        ↓
Saves to: data/data_output/assets_data/data_collect/
        ↓
Purpose: Historical backtesting, strategy development
Status: ✅ Working independently
```

#### Pipeline 2: Real-Time Streaming (Live Trading)
```
capabilities/data_streaming.py (RealtimeDataStreaming)
        ↓
streaming_server.py (Flask-SocketIO on port 3001)
        ↓
Socket.IO Events → React Frontend (port 5000)
        ↓
Optional Persistence (--collect-stream flag):
  → data/data_output/assets_data/realtime_stream/1M_candle_data/
  → data/data_output/assets_data/realtime_stream/1M_tick_data/
        ↓
Purpose: Live trading, GUI visualization, real-time analysis
Status: 🚧 Phases 1-4 complete (October 9, 2025)
```

### Key Architectural Decisions

1. **Hybrid Chrome Session Management**: Persistent Chrome session with remote debugging (port 9222) maintains login state and WebSocket connections, allowing Selenium to attach to existing instance.

2. **WebSocket Data Interception**: Intercepts Chrome DevTools Protocol performance logs to capture and decode WebSocket messages from PocketOption.

3. **Dual Data Pipeline Separation**: 
   - **Historical collection** uses `data_streaming_csv_save.py` for topdown data
   - **Real-time streaming** uses `data_streaming.py` for live GUI visualization
   - **No overlap** - completely separate concerns

4. **Dedicated GUI Backend Server** (`streaming_server.py`):
   - Flask-SocketIO server on port 3001
   - Attaches to Chrome (port 9222) with 1-second fast-fail timeout
   - **Delegates all logic to RealtimeDataStreaming capability** (zero code duplication)
   - Uses capability's public API methods:
     - `set_asset_focus(asset)` / `release_asset_focus()` for asset control
     - `set_timeframe(minutes, lock)` / `unlock_timeframe()` for timeframe management
     - `get_latest_candle(asset)` / `get_current_asset()` for data access
   - Delegates to `_decode_and_parse_payload`, `_process_chart_settings`, `_process_realtime_update`
   - Emits fully-formed candles via `candle_update` event
   - **Asset filtering at source**: Capability filters at START of processing
   - **Single source of truth**: Only capability forms candles, frontend displays them
   - **Optional stream persistence**: `--collect-stream {tick,candle,both,none}`
   - **Graceful Chrome handling**: Runs without Chrome, streaming just unavailable

5. **Intelligent Timeframe Detection**: Analyzes timestamp intervals and chart settings from PocketOption to determine candle timeframes reliably.

6. **Modular Capabilities Framework**: Trading operations as self-contained capabilities with standardized `run(ctx, inputs) -> CapResult` interface.

7. **Multi-Interface Access Pattern**: FastAPI backend, Flask-SocketIO GUI backend, React GUI, CLI tool, Pipeline Orchestrator - all consuming same capabilities.

8. **Frontend Data Provider Separation**:
   - **CSV Mode**: Historical data from pre-collected files, all timeframes supported
   - **Platform Mode**: Live WebSocket streaming, 1M timeframe only
   - **Explicit selection required**: No auto-switching between modes
   - **Asset validation**: Prevents invalid assets when switching modes
   - **Connection gating**: Live mode only activates with valid Chrome + backend connections

9. **Chunked CSV Persistence**: Rotating CSV files with configurable chunk sizes (default: 100 candles, 1000 ticks) organized by timeframe.

10. **Strategy Engine with Confidence Scoring**: Modular strategy system (Quantum Flux, Advanced, Alternative, Basic) with multi-indicator signals and confidence scores.

## Data Flow Architecture

### Real-time Streaming Pipeline (Live Trading)
```
PocketOption WebSocket
        ↓
Chrome DevTools Protocol (Port 9222)
        ↓
Performance Log Interception (streaming_server.py)
        ↓
RealtimeDataStreaming Capability:
  - _decode_and_parse_payload (WebSocket frames)
  - Asset Filtering (START - prevents unwanted switches)
  - _process_realtime_update (tick processing)
  - _process_chart_settings (timeframe detection)
  - Candle Formation (OHLC aggregation)
        ↓
API Methods: get_latest_candle(asset)
        ↓
Socket.IO Emit: candle_update event
        ↓
Frontend Display (with 1000-item backpressure buffer)
        ↓
Chart Update (LightweightChart component)
```

**Key Improvements**:
- Asset filtering at START prevents unwanted switches
- Single source of truth for candle formation (capability only)
- Clean API encapsulation (no direct state access)
- Backpressure protection (1000-item buffer limit)

### Historical Data Flow (Backtesting)
```
User Selects Timeframe
        ↓
Backend Filters CSV Files by Directory
        ↓
Frontend Displays Matching Assets
        ↓
User Loads Data
        ↓
Chart Visualization
```

### Trading Execution Flow
```
Signal Generation (Indicators)
        ↓
Confidence Scoring
        ↓
Strategy Validation
        ↓
Trade Click Capability
        ↓
WebDriver Interaction
        ↓
Execution Verification
        ↓
Result Logging
```

### GUI Backtesting Flow
```
User Selects CSV
        ↓
Frontend (Socket.IO Request)
        ↓
Backend Handler (streaming_server.py)
        ↓
Data Loader (CSV parsing)
        ↓
Backtest Engine (Strategy execution)
        ↓
Results Calculation
        ↓
Socket.IO Response
        ↓
Frontend Display
```

### Stream Collection Flow (Optional)
```
User Starts: --collect-stream {tick,candle,both,none}
        ↓
StreamPersistenceManager initialized
        ↓
Real-time data intercepted
        ↓
Tick Persistence: Patches _output_streaming_data method
        ↓
Candle Persistence: extract_candle_for_emit checks for closed candles
        ↓
Rotating CSV Writers (configurable chunk sizes)
        ↓
Files saved with session timestamp naming
        ↓
Output: realtime_stream/1M_candle_data/ or 1M_tick_data/
```

## External Dependencies

### Browser Automation & Session Management
- **Chrome Browser**: PocketOption interaction
- **Selenium WebDriver**: Browser automation
- **Chrome Remote Debugging Protocol (Port 9222)**: WebSocket interception and session attachment
- **Persistent Chrome Profile**: Maintains login state

### Data Processing & Analysis
- **Pandas**: DataFrame operations
- **NumPy**: Numerical operations for indicators
- **SciPy**: Statistical functions

### Web Framework & API
- **FastAPI**: REST API endpoints (Port 8000)
- **Flask**: GUI backend (Port 3001)
- **Flask-SocketIO**: Real-time Socket.IO server for GUI
- **Uvicorn**: ASGI server
- **WebSocket Support**: Real-time communication
- **CORS Support**: Frontend-backend communication

### Frontend Stack
- **React 18**: UI library
- **Vite**: Build tool (port 5000)
- **Socket.IO Client**: Real-time communication
- **Lightweight Charts**: Financial charting library
- **TailwindCSS**: CSS framework
- **React Router**: Client-side routing

### CLI & Automation
- **Typer**: Command-line interface framework
- **asyncio**: Asynchronous operations
- **uv**: Python package installer and runner

### Testing & Quality
- **Pytest**: Testing framework
- **pytest-asyncio**: Async test support

### Platform Integration: PocketOption
- **WebSocket API**: Market data stream (intercepted)
- **Socket.IO Protocol**: Message framing
- **Web UI Elements**: Platform-specific selectors
- **Session Authentication**: Managed via Chrome profile

### Data Storage
- **CSV Files**: Primary persistence for market data
  - Historical: `data/data_output/assets_data/data_collect/`
  - Real-time: `data/data_output/assets_data/realtime_stream/`
- **JSON Files**: Configuration storage
- **File System**: Organized directory structure

## Recent Updates

### October 9, 2025 - Real-Time Streaming Infrastructure
**Phases 1-4 Complete**:
- Fixed eventlet/WebSocket configuration
- Implemented stream data collection with --collect-stream argument
- Frontend data provider separation (CSV vs Platform)
- Asset focus integration verified
- Chrome disconnect handling improved
- Code quality improvements (LSP fixes, semantic corrections)

**Current Status**: Phase 5 (auto-detection) pending user decision

### October 7, 2025 - Critical Architectural Fixes
- Fixed asset filtering bug (filtering at START of processing)
- Eliminated duplicate candle formation (backend emits, frontend displays)
- Added proper API methods to capability
- Refactored streaming_server.py (API methods only, no direct state access)
- Simplified data flow (single source of truth)
- Added backpressure handling (1000-item buffer)
- Fixed Vite port configuration

### October 4-5, 2025 - GUI Backtesting Integration
- Created data_loader.py with CSV loading and backtest engine
- Extended streaming_server.py with Socket.IO handlers
- Smart file discovery (100+ CSV files)
- Built StrategyBacktest.jsx page
- Fixed profit calculation bug

## Project Status

**Overall**: Production-ready with active streaming development

**Components**:
- ✅ Core Infrastructure (Chrome session, WebSocket interception)
- ✅ Capabilities Framework (modular, reusable)
- ✅ GUI Backtesting (fully functional)
- 🚧 Real-Time Streaming (Phases 1-5 complete, Phase 6-7 pending)
- ✅ Reconnection Management (auto-recovery with state reset)
- ✅ Strategy Engine (Quantum Flux working)
- ⏳ Live Trading Integration (planned)

**Next Steps**:
1. User decision on Phase 6 (auto-detection approach)
2. Comprehensive testing (Phase 7)
3. Live trading GUI integration
4. Strategy comparison tool

---

**For detailed development phases, see**: `gui/gui_dev_plan_mvp.md`

**For task tracking, see**: `TODO.md`
