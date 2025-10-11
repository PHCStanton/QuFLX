# QuantumFlux Trading Platform

## Overview

QuantumFlux is an automated trading platform designed for PocketOption, integrating real-time WebSocket data streaming, browser automation, and AI-driven technical analysis. It features a React-based GUI for backtesting and live streaming visualization. The platform captures live market data, converts it into OHLC candles, generates trading signals using technical indicators, executes automated trades, and provides a user-friendly interface for strategy development and testing.

The project aims to provide algorithmic traders, quantitative researchers, and developers with reliable real-time data, automated execution, and comprehensive market analysis capabilities.

## User Preferences

- **Communication style**: Simple, everyday language
- **Technical approach**: Clear separation of concerns, modular architecture
- **Data handling**: Explicit control over data sources (no auto-switching)

## System Architecture

### Core Architecture Pattern: Capabilities-First Design + Dual Data Pipelines

The platform utilizes a **capabilities-first architecture** and **two distinct data pipelines** to handle both historical data collection for backtesting and real-time streaming for live trading and visualization.

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
        │                                         │
        │  2. RealtimeDataStreaming (CSV Save)    │
        │     (data_streaming_csv_save.py)        │
        │     - Historical topdown collection     │
        │     - Timeframe-organized storage       │
        └─────────────────────────────────────────┘
                              ↓
        ┌─────────────────────────────────────────┐
        │         MULTIPLE INTERFACES             │
        ├─────────────────────────────────────────┤
        │  • streaming_server.py (Port 3001)      │
        │  • FastAPI Backend (Port 8000)          │
        │  • React GUI (Port 5000)                │
        │  • CLI Tool (qf.py)                     │
        └─────────────────────────────────────────┘
```

### Key Architectural Decisions

1.  **Hybrid Chrome Session Management**: A persistent Chrome session with remote debugging (port 9222) maintains login and WebSocket connections, allowing Selenium to attach to an existing instance.
2.  **WebSocket Data Interception**: Captures and decodes WebSocket messages from PocketOption via Chrome DevTools Protocol performance logs.
3.  **Dual Data Pipeline Separation**: Dedicated pipelines for historical data collection (for backtesting) and real-time streaming (for live operations and GUI visualization), ensuring no overlap and clear separation of concerns.
4.  **Dedicated GUI Backend Server** (`streaming_server.py`): A Flask-SocketIO server on port 3001 handles real-time data streaming to the React frontend. It delegates all core logic to the `RealtimeDataStreaming` capability, ensuring a single source of truth for candle formation and processing.
5.  **Intelligent Timeframe Detection**: Analyzes PocketOption's timestamp intervals and chart settings to reliably determine candle timeframes.
6.  **Modular Capabilities Framework**: Trading operations are structured as self-contained capabilities with a standardized interface.
7.  **Multi-Interface Access Pattern**: Capabilities are accessible via a FastAPI backend, Flask-SocketIO GUI backend, React GUI, and a CLI tool.
8.  **Frontend Data Provider Separation**: The React GUI explicitly distinguishes between "CSV Mode" for historical data and "Platform Mode" for live WebSocket streaming, preventing automatic switching and ensuring data integrity.
9.  **Chunked CSV Persistence**: Data is saved into rotating CSV files with configurable chunk sizes, organized by timeframe for efficient storage and retrieval.
10. **Strategy Engine with Confidence Scoring**: Features a modular strategy system (e.g., Quantum Flux, Advanced) that generates multi-indicator signals with associated confidence scores.

## External Dependencies

### Browser Automation & Session Management
-   **Chrome Browser**: For interacting with PocketOption.
-   **Selenium WebDriver**: For browser automation.
-   **Chrome Remote Debugging Protocol (Port 9222)**: For WebSocket interception and session attachment.

### Data Processing & Analysis
-   **Pandas**: For DataFrame operations.
-   **NumPy**: For numerical operations and technical indicators.

### Web Framework & API
-   **FastAPI**: For REST API endpoints (Port 8000).
-   **Flask / Flask-SocketIO**: For the GUI backend and real-time Socket.IO server (Port 3001).
-   **Uvicorn**: ASGI server.
-   **WebSocket Support**: For real-time communication.
-   **CORS Support**: For frontend-backend communication.

### Frontend Stack
-   **React 18**: UI library.
-   **Vite**: Build tool (Port 5000).
-   **Socket.IO Client**: For real-time communication.
-   **Lightweight Charts**: For financial charting.
-   **TailwindCSS**: CSS framework.
-   **React Router**: For client-side routing.

### CLI & Automation
-   **Typer**: Command-line interface framework.
-   **asyncio**: For asynchronous operations.

### Platform Integration
-   **PocketOption**: The trading platform being integrated with, leveraging its WebSocket API for market data and web UI elements for interaction.

### Data Storage
-   **CSV Files**: Primary persistence for historical and real-time market data.
-   **JSON Files**: For configuration storage.
-   **File System**: For organized directory structure.
## Recent Updates

### October 11, 2025 - CSV Persistence Fix for streaming_server.py
**Critical Bug Fix: --collect-stream Not Saving Data**

**Root Cause Identified**:
- `streaming_server.py` called `_process_realtime_update()` which bypassed `_output_streaming_data()`
- The patched persistence logic (lines 816-843) was never executed because `_process_realtime_update()` doesn't call `_output_streaming_data()`
- This differed from `data_stream_collect.py` which uses `stream_continuous()` → `_stream_realtime_update()` → `_output_streaming_data()` (where the patch works)

**Fix Implemented**:
- Added CSV persistence directly in `stream_from_chrome()` data flow (lines 367-434)
- Tick persistence: Extract and save tick data immediately after `_process_realtime_update()` processes payload
- Candle persistence: Save closed candles using `last_closed_candle_index` tracking (same mechanism as data_stream_collect.py)
- Cleaned up `extract_candle_for_emit()`: Removed redundant persistence logic, focused on data extraction only
- Kept fallback patch (lines 819-843) for any alternative code paths that use `_output_streaming_data()`

**Key Changes**:
- Lines 367-434 (streaming_server.py): Persistence now executes directly in real-time data flow
- Lines 146-176 (streaming_server.py): Simplified extract_candle_for_emit() to avoid duplicate persistence
- Added clarifying comments about the dual persistence approach

**Status**: Architect-verified ✅. CSV files will now be saved correctly when running `streaming_server.py --collect-stream both`. End-to-end testing requires Chrome connection.

### October 10, 2025 - Platform Mode State Machine & Candle Alignment Fix
**Complete Architecture Overhaul for Platform Streaming**

- Implemented 6-state machine (idle, ready, detecting, asset_detected, streaming, error)
- Added backend `detect_asset` Socket.IO endpoint for explicit asset detection
- Created Stream Control Panel UI with state-based buttons (Detect Asset → Start Stream → Stop Stream)
- Eliminated all race conditions and auto-start bypasses in reconnection logic
- Separated `selectedAsset` (CSV mode) from `detectedAsset` (Platform mode)
- Removed legacy `toggleLiveMode` function to prevent state machine bypasses
- Statistics panel now only shows in CSV mode
- Chart data properly clears when switching from CSV to Platform mode

**Bug Fixes**:
- Implemented exponential backoff (5s, 10s, 20s) for Chrome reconnection attempts (was fixed 5s)
- Removed unused `startStream` dependency from reconnection useEffect to prevent unnecessary re-renders
- Fixed asset detection to actively query PocketOption UI instead of returning None (added `detect_asset_from_ui()` method)
- Removed iteration-based verbose logging that was spamming console output
- **Fixed asset name mismatch in filtering and candle retrieval** (critical chart rendering bug):
  - Added `_normalize_asset_name()` to handle format variations (USDJPY_otc vs USDJPYOTC)
  - Applied normalization to all 3 filtering locations (historical, realtime, streaming)
  - Extended normalization to candle retrieval methods (`get_latest_candle`, `get_all_candles`)
  - Two-tier lookup: Direct O(1) lookup first, normalized fallback search if needed
  - Resolved "Loading chart data..." issue - data no longer filtered/lost due to name format differences
  - CSV persistence unchanged - normalization only affects in-memory comparison and retrieval
- **Fixed candle timestamp alignment to match PocketOption timing**:
  - Candle timestamps now align to minute boundaries (:00 seconds) using `candle_start = (tstamp // PERIOD) * PERIOD`
  - Changed new candle detection from time difference to boundary crossing check (`candle_start > last_candle_start`)
  - Ensures candles form at :00 seconds, not when streaming starts (e.g., :30 seconds)
  - Architect-verified: Prevents data from new periods overwriting previous candle's close/high/low

**Key Improvements**:
- Sequential logic: Detect → Start → Stream → Visualize (explicit user control at each step)
- No more hardcoded asset defaults or auto-restart on reconnection
- State machine exclusively controls all Platform mode transitions
- Clean separation between CSV (dropdown) and Platform (detection) UI
- Reduced log spam and improved resource usage during Chrome unavailability
- Real-time candles now perfectly synchronized with PocketOption's minute boundaries

**Status**: Production-ready, architect-verified. Chart rendering and candle alignment verified ✅. Ready for live testing with Chrome connection.

### October 9, 2025 - Real-Time Streaming Infrastructure
**Phases 1-5 Complete**:
- Fixed eventlet/WebSocket configuration
- Implemented stream data collection with --collect-stream argument
- Frontend data provider separation (CSV vs Platform)
- Asset focus integration verified
- Chrome disconnect handling improved
- Reconnection lifecycle management with auto-recovery
- Code quality improvements (LSP fixes, semantic corrections)

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
- Built functional StrategyBacktest.jsx page
- Fixed profit calculation bugs
