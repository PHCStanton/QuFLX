# QuantumFlux Trading Platform

## Overview
QuantumFlux is an automated trading platform designed for PocketOption. It integrates real-time WebSocket data, browser automation, and AI-driven technical analysis to provide a comprehensive solution for algorithmic traders, quantitative researchers, and developers. The platform features a Solana-inspired React GUI with dynamic indicators, multi-pane charting, strategy design tools, backtesting capabilities, and live streaming visualization. Its core purpose is to capture market data, form OHLC candles, generate AI-driven trading signals, and offer in-depth market analysis.

## User Preferences
- **Communication style**: Simple, everyday language
- **Technical approach**: Clear separation of concerns, modular architecture
- **Data handling**: Explicit control over data sources (no auto-switching)
- **UI/UX**: Solana-inspired dark aesthetic, professional trading terminal

## Recent Changes

### Phase 6.1: Layout Expansion - Improved Flexibility (Completed - October 15, 2025)
**Goal**: Maximize chart space and create flexible layouts that adapt to different screen sizes without squishing panels.

**Changes Implemented:**
- Converted all three main pages (DataAnalysis, LiveTrading, StrategyBacktest) to flexible CSS Grid layouts using `minmax()` and `1fr` units
- **Flexible Grid Strategy**:
  - Left sidebar: `minmax(200px-280px)` (prevents squishing, varies by breakpoint)
  - Center chart: `1fr` (takes all remaining space for maximum chart area)
  - Right sidebar: `minmax(220px-320px)` (content-aware sizing, varies by breakpoint)
- **Responsive Breakpoints**:
  - 1440px+ (large desktop): Wider minimum widths for optimal viewing
  - 1280px+ (desktop): Balanced sidebar/chart proportions
  - 1024px+ (tablet horizontal): Optimized for tablet screens
  - <1024px (smaller screens): Compact but usable layout
- **Space Optimization**:
  - Reduced grid gap from `spacing.lg` to `spacing.md`
  - Optimized padding: `spacing.md` vertical, `spacing.lg` horizontal
  - Less wasted margin space, more usable screen area
- Dynamic resize listeners update grid on viewport changes
- SSR-safe with proper window guards

**Impact**: 
- Chart area maximizes available space across all screen sizes
- Sidebars maintain readable content without squishing
- Better flexibility for manual window resizing
- More professional, space-efficient trading terminal layout

## System Architecture
The platform utilizes a **Capabilities-First Design** with **Dual Data Pipelines** for historical data collection (backtesting) and real-time streaming (live trading and visualization).

**Core Architectural Decisions:**
- **Hybrid Chrome Session Management**: Persistent Chrome session with remote debugging (port 9222) for login and WebSocket connections, allowing Selenium to attach.
- **WebSocket Data Interception**: Captures and decodes WebSocket messages from PocketOption via Chrome DevTools Protocol.
- **Dual Data Pipeline Separation**: Dedicated pipelines for historical data collection and real-time streaming.
- **Dedicated GUI Backend Server**: A Flask-SocketIO server (`streaming_server.py` on port 3001) for real-time data streaming to the React frontend.
- **Intelligent Timeframe Detection**: Analyzes PocketOption's timestamp intervals for reliable candle timeframe determination.
- **Modular Capabilities Framework**: Trading operations are structured as self-contained capabilities.
- **Multi-Interface Access Pattern**: Capabilities accessible via FastAPI, Flask-SocketIO GUI backend, React GUI, and a CLI tool.
- **Frontend Data Provider Separation**: React GUI distinguishes "CSV Mode" for historical data and "Platform Mode" for live WebSocket streaming.
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
- **Data Analysis Page**: For strategy design, chart testing, and indicator configuration. Features a 3-column layout with data source toggles, asset selector, indicator manager, live chart, and quick stats.
- **Strategy Lab Page**: For strategy development, validation, and performance analysis. Includes strategy selection, data picking, an equity curve chart, performance metrics, and trade history.
- **Trading Hub Page**: For real-time signal generation and trade execution. Displays active positions, a live chart with strategy signal overlays, and a live signal panel with execution controls.

**Chart System:**
- **Main Chart**: Candlestick data with overlay indicators.
- **Oscillator Panes**: Separate synchronized panes for RSI and MACD.
- **Time Synchronization**: Ensures alignment across all panes.
- **Dynamic Indicators**: Modal-based configuration with multiple instances support for various trend, momentum, and volatility indicators.

**Design System:**
- **Color Palette**: Dark theme with base `#0b0f19`, card backgrounds `#1e293b`, borders `#334155`, and accents like green `#22c55e`, red `#ef4444`, and blue `#3b82f6`.
- **Typography**: Inter font family.
- **Components**: Card-based with glass effects and minimal borders.
- **Design Tokens**: Centralized in `gui/Data-Visualizer-React/src/styles/designTokens.js` for consistent styling.

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
- TailwindCSS (legacy components only)
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