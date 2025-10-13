# QuantumFlux Trading Platform

## Overview

QuantumFlux is an automated trading platform for PocketOption, integrating real-time WebSocket data, browser automation, and AI-driven technical analysis. It features a React GUI for backtesting and live streaming visualization, capturing market data, forming OHLC candles, generating AI-driven trading signals, and executing automated trades. The platform aims to provide algorithmic traders, quantitative researchers, and developers with reliable real-time data, automated execution, and comprehensive market analysis.

## User Preferences

- **Communication style**: Simple, everyday language
- **Technical approach**: Clear separation of concerns, modular architecture
- **Data handling**: Explicit control over data sources (no auto-switching)

## System Architecture

### Core Architecture Pattern: Capabilities-First Design + Dual Data Pipelines

The platform uses a **capabilities-first architecture** and **two distinct data pipelines** for historical data collection (backtesting) and real-time streaming (live trading and visualization).

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

1.  **Hybrid Chrome Session Management**: Persistent Chrome session with remote debugging (port 9222) for login and WebSocket connections, allowing Selenium to attach.
2.  **WebSocket Data Interception**: Captures and decodes WebSocket messages from PocketOption via Chrome DevTools Protocol.
3.  **Dual Data Pipeline Separation**: Dedicated pipelines for historical data collection and real-time streaming, ensuring no overlap.
4.  **Dedicated GUI Backend Server** (`streaming_server.py`): A Flask-SocketIO server on port 3001 for real-time data streaming to React frontend, delegating core logic to `RealtimeDataStreaming`.
5.  **Intelligent Timeframe Detection**: Analyzes PocketOption's timestamp intervals and chart settings for reliable candle timeframe determination.
6.  **Modular Capabilities Framework**: Trading operations are structured as self-contained capabilities.
7.  **Multi-Interface Access Pattern**: Capabilities are accessible via FastAPI, Flask-SocketIO GUI backend, React GUI, and a CLI tool.
8.  **Frontend Data Provider Separation**: React GUI explicitly distinguishes "CSV Mode" for historical data and "Platform Mode" for live WebSocket streaming.
9.  **Chunked CSV Persistence**: Data saved into rotating CSV files by timeframe.
10. **Strategy Engine with Confidence Scoring**: Modular strategy system generates multi-indicator signals with confidence scores.
11. **Platform Mode State Machine**: Implemented a 6-state machine for robust streaming control (idle, ready, detecting, asset_detected, streaming, error) with explicit asset detection.
12. **Normalized Asset Naming**: Handles asset name variations (e.g., USDJPY_otc vs USDJPYOTC) for consistent data filtering and retrieval.
13. **Candle Timestamp Alignment**: Candles align to minute boundaries (e.g., :00 seconds) to match PocketOption timing.

## External Dependencies

### Browser Automation & Session Management
-   **Chrome Browser**
-   **Selenium WebDriver**
-   **Chrome Remote Debugging Protocol (Port 9222)**

### Data Processing & Analysis
-   **Pandas**
-   **NumPy**

### Web Framework & API
-   **FastAPI** (Port 8000)
-   **Flask / Flask-SocketIO** (Port 3001)
-   **Uvicorn**
-   **WebSocket Support**
-   **CORS Support**

### Frontend Stack
-   **React 18**
-   **Vite** (Port 5000)
-   **Socket.IO Client**
-   **Lightweight Charts**
-   **TailwindCSS**
-   **React Router**

### CLI & Automation
-   **Typer**
-   **asyncio**

### Platform Integration
-   **PocketOption**

### Data Storage
-   **CSV Files**
-   **JSON Files**
-   **File System**