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

### October 10, 2025 - Platform Mode State Machine & Bug Fixes
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

**Key Improvements**:
- Sequential logic: Detect → Start → Stream → Visualize (explicit user control at each step)
- No more hardcoded asset defaults or auto-restart on reconnection
- State machine exclusively controls all Platform mode transitions
- Clean separation between CSV (dropdown) and Platform (detection) UI
- Reduced log spam and improved resource usage during Chrome unavailability

**Status**: Production-ready, architect-verified. Pending: TradingView pattern for chart updates, component separation, end-to-end testing.

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
