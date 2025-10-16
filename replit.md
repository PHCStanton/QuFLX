# QuantumFlux Trading Platform

## Overview
QuantumFlux is an automated trading platform designed for PocketOption. It integrates real-time WebSocket data, browser automation, and AI-driven technical analysis to provide a comprehensive solution for algorithmic traders, quantitative researchers, and developers. The platform features a Solana-inspired React GUI with dynamic indicators, multi-pane charting, strategy design tools, backtesting capabilities, and live streaming visualization. Its core purpose is to capture market data, form OHLC candles, generate AI-driven trading signals, and offer in-depth market analysis.

## User Preferences
- **Communication style**: Simple, everyday language
- **Technical approach**: Clear separation of concerns, modular architecture
- **Data handling**: Explicit control over data sources (no auto-switching)
- **UI/UX**: Solana-inspired dark aesthetic, professional trading terminal

## Recent Changes

### Bug Fixes - Performance & Stability Improvements (Completed - October 16, 2025)
**Goal**: Fix bugs affecting app performance, user experience, and resource usage.

**Bugs Fixed:**
1. **Chrome Reconnection Loop**: Backend continuously attempted Chrome reconnection even when not needed (CSV mode)
   - Added `chrome_reconnect_enabled` flag that activates only when Platform mode is used
   - Modified `monitor_chrome_status()` to respect the flag before attempting reconnection
   - Enabled in `handle_start_stream()` and `handle_detect_asset()` when Chrome is needed
   
2. **CSV Error Logging**: Error messages displayed as empty objects `{}`
   - Updated error logging to properly extract `err.message` and `err.stack`
   - Now shows meaningful error messages in console for debugging
   
3. **Missing Data Notification**: Users had no visibility when assets lack data
   - Added visual error notification in Indicator Readings panel
   - Shows user-friendly message: "⚠️ No data available for this asset"
   - Red-bordered alert box for clear visibility
   
4. **WebSocket Cleanup Warnings**: Console showed "WebSocket closed before connection established"
   - Enhanced cleanup logic to check connection state before disconnecting
   - Uses `socket.io.engine.readyState` to determine proper cleanup action
   - Calls `engine.close()` for 'opening' state to prevent zombie connections
   - Calls `disconnect()` only for established connections

**Impact**:
- No more Chrome reconnection spam in backend logs ✅
- Clear error messages for troubleshooting ✅
- Better user experience with visible error notifications ✅
- Cleaner console without WebSocket warnings ✅
- No memory leaks from zombie connections ✅

**Files Modified:**
- `streaming_server.py` - Chrome reconnection control
- `gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx` - Error logging & UI notifications
- `gui/Data-Visualizer-React/src/hooks/useWebSocket.js` - WebSocket cleanup improvements

**Verification**: Logs verified ✅ | Visual confirmation ✅ | No regressions ✅

### Indicator Calculation Race Condition Fix (Completed - October 16, 2025)
**Goal**: Fix bug where indicators failed to display in CSV mode due to WebSocket timing race condition.

**Root Cause Identified:**
- CSV data loaded before WebSocket connection established
- `storeCsvCandles` and `calculateIndicators` checked React state `isConnected` which lagged behind actual socket state
- Functions silently failed when `isConnected` was false but socket was actually connected
- No error logging made debugging difficult

**Changes Implemented:**
- **Direct Socket State Check (useWebSocket.js)**: Modified `storeCsvCandles` and `calculateIndicators` to check `socketRef.current.connected` directly instead of relying on React state variable
  - Eliminates false-negative readiness checks
  - Prevents race condition between state updates and socket connection
- **Automatic Retry Logic (DataAnalysis.jsx)**: Added useEffect that retries indicator calculation when socket connects
  - Triggers when `isConnected` changes to true and chart data exists
  - Resubmits cached candles and indicator calculation requests
  - Ensures indicators display even when CSV loads before socket is ready
- **Enhanced Error Logging**: Added detailed error messages to identify connection state issues
  - Shows socket existence vs actual connection status
  - Helps diagnose timing-related problems

**Impact**: 
- Indicators now display correctly in CSV mode: RSI, Bollinger Bands, SMA all working
- Backend confirms successful calculation of all requested indicators
- Robust handling of WebSocket timing variations
- Improved debugging capabilities with better error messages

**Verification**: Architect-approved ✅ | Visual confirmation ✅ | No regressions ✅

### CSV Chart Rendering Fix (Completed - October 16, 2025)
**Goal**: Fix chart display issue where CSV data loaded correctly but displayed as thin bar.

**Root Cause Identified:**
- React StrictMode double-render caused chart to initialize twice
- First init: Loaded all 101 candles correctly ✅
- Cleanup removed chart but didn't reset `prevDataLengthRef`
- Second init: Created new chart, saw prevDataLengthRef=101, only updated last candle ❌

**Changes Implemented:**
- **Chart State Reset (MultiPaneChart.jsx)**: Added `prevDataLengthRef.current = 0` in cleanup function
  - Ensures re-initialization always loads full dataset
  - Handles React StrictMode double-render correctly
  - Prevents single-candle display bug
- **File Selection Enhancement (fileUtils.js)**: Improved CSV file selection
  - Filters out tick data files (incompatible format)
  - Selects largest candle file per asset
- **Debug Logging**: Added data processing logs for troubleshooting

**Impact**: 
- Charts now display full candlestick data correctly (101 candles)
- Robust handling of React development mode double-renders
- Better file selection prevents format mismatches
- Improved debugging capabilities

**Verification**: Architect-approved ✅ | Visual confirmation ✅ | No regressions ✅

### Bug Fixes & Code Quality (Completed - October 16, 2025)
**Goal**: Fix identified bugs, improve performance consistency, and eliminate memory leaks.

**Changes Implemented:**
- **MultiPaneChart Performance Optimization**: Applied the same setData() vs update() optimization from LightweightChart
  - Added `prevDataLengthRef` tracking for detecting initial vs incremental updates
  - Uses `setData()` only for initial load or asset switches
  - Uses `update()` for incremental candles (10-100x faster rendering)
  - Mirrors proven pattern from LightweightChart.jsx for consistency
- **Type Safety Fix (streaming_server.py)**: Fixed unsafe None handling in volume field conversion
  - Changed `int(row.get('volume', 0))` to `int(row.get('volume', 0) or 0)`
  - Prevents crashes when loading CSV data with missing volume column
- **Memory Leak Fixes (MultiPaneChart.jsx)**: Fixed callback cleanup scope issues
  - Moved timeRangeCallback declarations outside try blocks (RSI and MACD charts)
  - Added safe error handling in cleanup to prevent unsubscribe failures
  - Added chartConfig to dependency arrays for proper effect triggers
- **Dependency Array Fix (DataAnalysis.jsx)**: Fixed stale closure bug
  - Changed useEffect dependency from `[dataSource, timeframe]` to `[loadAvailableAssets]`
  - Ensures assets reload correctly when dependencies change through callback

**Impact**: 
- Consistent high performance across all chart components
- Robust error handling for edge cases
- No memory leaks during long-term usage
- Reliable state management across mode switches

**Verification**: All LSP diagnostics cleared ✅ | Architect-approved ✅ | No regressions ✅

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