# QuantumFlux Trading Platform

## Overview

QuantumFlux is an automated trading platform for PocketOption, integrating real-time WebSocket data streaming, browser automation, and AI-driven technical analysis. It features a React-based GUI for backtesting and strategy execution. The platform captures live market data, converts it into OHLC candles, generates trading signals using technical indicators (SMA, RSI, MACD), executes automated trades, and provides a user-friendly interface for strategy development and testing. It targets algorithmic traders, quantitative researchers, and developers needing reliable real-time data, automated execution, and comprehensive market analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern: Capabilities-First Design + GUI Integration

The platform uses a **capabilities-first architecture** where all trading operations are modular and orchestrated through multiple interfaces, including a React-based GUI.

```
Chrome Session (Port 9222) ←→ Capabilities Framework ←→ Multiple Interfaces
                            ↓                              ├── FastAPI Backend (Port 8000)
                    GUI Backend (Port 3001)               ├── React GUI (Port 5000)
                    streaming_server.py                    ├── CLI Tool (qf.py)
                            ↓                              └── Pipeline Orchestrator
                    React Frontend (Port 5000)
```

**Key Architectural Decisions:**

1.  **Hybrid Chrome Session Management**: Uses a persistent Chrome session with remote debugging (port 9222) to maintain login state and WebSocket connections, allowing Selenium to attach to an existing instance.
2.  **WebSocket Data Interception**: Intercepts Chrome DevTools Protocol performance logs to capture and decode WebSocket messages from PocketOption, leveraging the existing authenticated session.
3.  **Dedicated GUI Backend Server** (`streaming_server.py` in root): Flask-SocketIO server that attaches to Chrome (port 9222) and **delegates all WebSocket interception to the RealtimeDataStreaming capability** to avoid code duplication. Uses capability's public API methods for clean encapsulation:
    - `set_asset_focus(asset)` / `release_asset_focus()` for asset control
    - `set_timeframe(minutes, lock)` / `unlock_timeframe()` for timeframe management
    - `get_latest_candle(asset)` / `get_current_asset()` for data access
    - Delegates to `_decode_and_parse_payload`, `_process_chart_settings`, `_process_realtime_update`
    - Emits fully-formed candles via `candle_update` event (no tick extraction)
    - Handles CSV serving, backtesting, and real-time candle streaming
    - **Asset filtering at source**: Capability filters assets at start of processing to prevent unwanted switches
    - **Single source of truth**: Only capability forms candles, frontend displays them
    - **No simulated data** - all data comes from Chrome/PocketOption WebSocket interception through the capability's vetted logic
4.  **Intelligent Timeframe Detection**: Determines candle timeframes by analyzing actual timestamp intervals and chart settings from PocketOption, ensuring reliability regardless of metadata inconsistencies.
5.  **Modular Capabilities Framework**: Trading operations are implemented as self-contained capabilities with a standardized `run(ctx, inputs) -> CapResult` interface, promoting composability and reusability. Capabilities include data streaming, session scanning, trade execution, and signal generation.
6.  **Multi-Interface Access Pattern**: Provides access via a FastAPI backend, Flask-SocketIO GUI backend, React GUI, CLI tool, and a Pipeline Orchestrator, all consuming the same core capabilities or Chrome session.
7.  **GUI Data Analysis with Timeframe Filtering**: React frontend filters available assets by selected timeframe (1m, 5m, 15m, 1h, 4h), showing only assets with matching data in corresponding directories. Complete CSV filenames preserved in dropdowns for clarity. Frontend implements backpressure handling with 1000-item buffer limit to prevent memory overflow.
8.  **Chunked CSV Persistence with Timeframe Organization**: Automatically rotates CSV files based on configurable chunk sizes and organizes them by timeframe (e.g., `1M_candles/`, `15M_candles/`) to manage large datasets and facilitate analysis.
9.  **Selenium UI Control Helpers**: Utility classes (`HighPriorityControls`, `ZoomManager`) centralize robust UI interaction logic for PocketOption, handling specific element interactions and platform quirks.
10. **Strategy Engine with Confidence Scoring**: A modular strategy system (Quantum Flux, Advanced, Alternative, Basic) generates trading signals from multiple indicators with confidence scoring for risk management, allowing A/B testing of different approaches.

### Data Flow Architecture

*   **Real-time Data Pipeline (SIMPLIFIED)**: PocketOption WebSocket → Chrome DevTools Protocol → Performance Log Interception (streaming_server.py) → **RealtimeDataStreaming Capability** (_decode_and_parse_payload → **Asset Filtering (START)** → _process_realtime_update → _process_chart_settings → **Candle Formation**) → **API Methods** (get_latest_candle) → Socket.IO Emit (`candle_update`) → Frontend Display (with backpressure) → Chart Update.
    - **Key Improvement**: Asset filtering at START of processing prevents unwanted asset switches
    - **Single Source of Truth**: Only capability forms candles, frontend displays them directly
    - **Clean Encapsulation**: Server uses public API methods, no internal state access
    - **Backpressure Protection**: Frontend limits buffer to 1000 items to prevent memory issues
*   **Historical Data Flow**: User Selects Timeframe → Backend Filters CSV Files by Directory → Frontend Displays Matching Assets → User Loads Data → Chart Visualization.
*   **Trading Execution Flow**: Signal Generation (Indicators) → Confidence Scoring → Strategy Validation → Trade Click Capability → WebDriver Interaction → Execution Verification → Result Logging.
*   **GUI Backtesting Flow**: User Selects CSV → Frontend (Socket.IO) → Backend Handler → Data Loader → Backtest Engine → Strategy Execution → Results Calculation → Socket.IO Response → Frontend Display.
*   **GUI Real-time Streaming Flow**: User Focuses Asset → Frontend Sets Focus (Socket.IO) → Backend Calls `set_asset_focus(asset)` → Capability Filters at Start → Processes & Forms Candles → Backend Calls `get_latest_candle()` → Emits `candle_update` → Frontend Displays (with backpressure) → Chart Updates.

## External Dependencies

### Browser Automation & Session Management
-   **Chrome Browser**: For PocketOption interaction.
-   **Selenium WebDriver**: Browser automation.
-   **Chrome Remote Debugging Protocol (Port 9222)**: For WebSocket interception and session attachment.
-   **Persistent Chrome Profile**: Maintains login state.

### Data Processing & Analysis
-   **Pandas**: DataFrame operations.
-   **NumPy**: Numerical operations for indicators.
-   **SciPy**: Statistical functions.

### Web Framework & API
-   **FastAPI**: REST API endpoints (Port 8000).
-   **Flask**: GUI backend (Port 3001).
-   **Flask-SocketIO**: Real-time Socket.IO server for GUI.
-   **Uvicorn**: ASGI server.
-   **WebSocket Support**: Real-time communication.
-   **CORS Support**: For frontend-backend communication.

### Frontend Stack
-   **React 18**: UI library.
-   **Vite**: Build tool.
-   **Socket.IO Client**: Real-time communication.
-   **Recharts**: Charting library.
-   **TailwindCSS**: CSS framework.
-   **React Router**: Client-side routing.

### CLI & Automation
-   **Typer**: Command-line interface framework.
-   **asyncio**: Asynchronous operations.
-   **uv**: Python package installer and runner.

### Testing & Quality
-   **Pytest**: Testing framework.
-   **pytest-asyncio**: Async test support.

### Platform Integration: PocketOption
-   **WebSocket API**: Market data stream (intercepted).
-   **Socket.IO Protocol**: Message framing.
-   **Web UI Elements**: Platform-specific selectors.
-   **Session Authentication**: Managed via Chrome profile.

### Data Storage
-   **CSV Files**: Primary persistence for market data.
-   **JSON Files**: Configuration storage.
-   **File System**: Organized directory structure for data.