# QuantumFlux Trading Platform

## Overview
QuantumFlux is an automated trading platform for PocketOption, integrating real-time WebSocket data, browser automation, and AI-driven technical analysis. It features a Solana-inspired React GUI with dynamic indicators, multi-pane charting, strategy design, backtesting, and live visualization. The platform's core purpose is to capture market data, form OHLC candles, generate AI-driven trading signals, and offer in-depth market analysis for algorithmic traders, quantitative researchers, and developers.

## User Preferences
- **Communication style**: Simple, everyday language
- **Technical approach**: Clear separation of concerns, modular architecture
- **Data handling**: Explicit control over data sources (no auto-switching)
- **UI/UX**: Solana-inspired dark aesthetic, professional trading terminal

## System Architecture
The platform employs a Capabilities-First Design with Dual Data Pipelines for historical and real-time data.

**Core Architectural Decisions:**
- **Hybrid Chrome Session Management**: Persistent Chrome session with remote debugging for login and WebSocket connections, allowing Selenium attachment.
- **WebSocket Data Interception**: Captures and decodes WebSocket messages from PocketOption via Chrome DevTools Protocol.
- **Dual Data Pipeline Separation**: Dedicated pipelines for historical data collection and real-time streaming.
- **Dedicated GUI Backend Server**: Flask-SocketIO server (`streaming_server.py` on port 3001) for real-time data to the React frontend.
- **Intelligent Timeframe Detection**: Analyzes PocketOption timestamps for reliable candle timeframe determination.
- **Modular Capabilities Framework**: Trading operations structured as self-contained capabilities.
- **Multi-Interface Access Pattern**: Capabilities accessible via FastAPI, Flask-SocketIO GUI backend, React GUI, and CLI.
- **Frontend Data Provider Separation**: React GUI distinguishes "CSV Mode" (historical) and "Platform Mode" (live WebSocket streaming).
- **Chunked CSV Persistence**: Data saved into rotating CSV files by timeframe.
- **Strategy Engine with Confidence Scoring**: Modular system generating multi-indicator signals with confidence scores.
- **Platform Mode State Machine**: 6-state machine for robust streaming control with explicit asset detection.
- **Normalized Asset Naming**: Handles asset name variations for consistent data.
- **Candle Timestamp Alignment**: Candles align to minute boundaries to match PocketOption timing.
- **Dynamic Indicator System**: Frontend supports adding/removing indicators with full time-series data (SMA, EMA, RSI, MACD, Bollinger Bands, etc.).
- **Multi-Pane Chart Architecture**: Main chart for candlesticks with overlay indicators; separate, synchronized panes for oscillators (RSI, MACD).
- **Memory-Safe Resource Management**: Proper cleanup of timers, event listeners, and chart instances.
- **Solana-Inspired UI/UX**: Professional 3-page trading terminal with a cohesive design system and dark aesthetic.

**Frontend Architecture (Solana-Inspired Design):**
- **Expandable Sidebar Navigation**: Retractable sidebar (240px expanded, 64px collapsed) with SVG icons for clean navigation.
- **Data Analysis Page**: For strategy design, chart testing, and indicator configuration.
- **Strategy Lab Page**: For strategy development, validation, and performance analysis.
- **Trading Hub Page**: For real-time signal generation and trade execution.
- **SidebarContext**: Global state management for sidebar expand/collapse state and responsive layout.

**Chart System:**
- **Main Chart**: Candlestick data with overlay indicators.
- **Oscillator Panes**: Separate synchronized panes for RSI and MACD.
- **Time Synchronization**: Ensures alignment across all panes.
- **Dynamic Indicators**: Modal-based configuration with multiple instances.

**Design System:**
- **Color Palette**: Dark theme with base `#10141a`, card backgrounds `#1a1f2e`, borders `#2a2f3e`, and accents like green `#22c55e`.
- **Typography**: Inter font family.
- **Components**: Card-based with glass effects and minimal borders.
- **Design Tokens**: Centralized in `gui/Data-Visualizer-React/src/styles/designTokens.js`.

## External Dependencies

**Browser Automation & Session Management:**
- Chrome Browser
- Selenium WebDriver
- Chrome Remote Debugging Protocol

**Data Processing & Analysis:**
- Pandas
- NumPy

**Web Framework & API:**
- FastAPI (Port 8000)
- Flask / Flask-SocketIO (Port 3001)
- Uvicorn
- WebSocket Support
- CORS Support

**Frontend Stack:**
- React 18
- Vite (Port 5000)
- Socket.IO Client
- Lightweight Charts v4.2.0
- TailwindCSS
- React Router

**CLI & Automation:**
- Typer
- asyncio

**Platform Integration:**
- PocketOption

**Data Storage:**
- CSV Files
- JSON Files
- File System