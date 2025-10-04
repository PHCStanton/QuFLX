# QuantumFlux Trading Platform

## Overview

QuantumFlux is a sophisticated automated trading platform for PocketOption that combines real-time WebSocket data streaming, browser automation, and AI-driven technical analysis. The platform uses a hybrid Chrome session approach to maintain persistent browser state while intercepting and processing live market data from WebSocket streams. It converts raw tick data into structured OHLC candles, generates trading signals using multiple technical indicators (SMA, RSI, MACD), and executes automated trades based on configurable strategies.

The system is designed for algorithmic traders, quantitative researchers, and trading system developers who need reliable real-time data collection, automated strategy execution, and comprehensive market analysis capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Architecture Pattern: Capabilities-First Design

The platform follows a **capabilities-first architecture** where all trading operations are implemented as modular capabilities that can be orchestrated through multiple interfaces:

```
Chrome Session (Port 9222) ←→ Capabilities Framework ←→ Multiple Interfaces
                                                          ├── FastAPI Backend
                                                          ├── CLI Tool (qf.py)
                                                          └── Pipeline Orchestrator
```

**Key Architectural Decisions:**

1. **Hybrid Chrome Session Management**
   - **Problem**: Browser-based trading platforms require persistent login sessions and WebSocket connections
   - **Solution**: Chrome runs with remote debugging enabled (port 9222) using a persistent workspace profile (`Chrome_profile/`)
   - **Rationale**: Selenium attaches to existing Chrome instance instead of launching new sessions, preserving authentication, cookies, and WebSocket connections across restarts
   - **Pros**: Session persistence, reliable WebSocket data collection, no repeated logins
   - **Cons**: Requires Chrome to be running separately, port conflicts if multiple instances

2. **WebSocket Data Interception**
   - **Problem**: PocketOption's market data flows through WebSocket connections that aren't directly accessible
   - **Solution**: Intercept Chrome DevTools Protocol performance logs to capture WebSocket messages, decode base64 Socket.IO frames
   - **Rationale**: Direct WebSocket connection would require reverse-engineering authentication; interception leverages existing authenticated session
   - **Pros**: No authentication complexity, captures all market data automatically, works with existing login
   - **Cons**: Requires Chrome remote debugging, potential performance overhead from log parsing

3. **Intelligent Timeframe Detection**
   - **Problem**: WebSocket metadata for timeframes is unreliable and inconsistent
   - **Solution**: Analyze actual candle timestamp intervals to determine timeframe (e.g., ~60-minute intervals = H1, ~15-minute intervals = 15M)
   - **Rationale**: Timestamp analysis provides 100% reliability regardless of metadata issues
   - **Pros**: Highly reliable, works across all timeframes, self-correcting
   - **Cons**: Requires at least 2 candles for detection, slight computational overhead

4. **Modular Capabilities Framework**
   - **Problem**: Trading operations span diverse concerns (data collection, UI interaction, trade execution, signal generation)
   - **Solution**: Each operation is a self-contained capability with standardized `run(ctx, inputs) -> CapResult` interface
   - **Rationale**: Enables capability composition through pipelines, clean separation of concerns, easy testing
   - **Capabilities Include**:
     - `data_streaming`: Real-time WebSocket data collection and candle formation
     - `session_scan`: Account state monitoring (balance, demo/real mode)
     - `profile_scan`: User profile and account information extraction
     - `favorite_select`: Asset scanning with payout threshold filtering
     - `trade_click_cap`: BUY/SELL trade execution with verification
     - `signal_generation`: Technical indicator analysis (SMA, RSI, MACD)
     - `topdown_select`: Timeframe selection automation
   - **Pros**: Highly composable, testable in isolation, reusable across interfaces
   - **Cons**: Additional abstraction layer, requires capability registration

5. **Multi-Interface Access Pattern**
   - **Problem**: Different use cases require different interaction methods (API, CLI, automation)
   - **Solution**: Three parallel interfaces all consuming the same capabilities:
     - **FastAPI Backend** (`backend.py`): REST/WebSocket API for programmatic access
     - **CLI Tool** (`qf.py`): Typer-based command-line interface for direct operations
     - **Pipeline Orchestrator**: JSON-based workflow automation
   - **Rationale**: Single source of truth (capabilities) with multiple access methods for flexibility
   - **Pros**: Use the right tool for the job, no code duplication, consistent behavior
   - **Cons**: Multiple codebases to maintain for different interfaces

6. **Chunked CSV Persistence with Timeframe Organization**
   - **Problem**: Continuous data streaming generates large datasets; need organized storage
   - **Solution**: Automatic CSV rotation with configurable chunk sizes (candles: 100 rows/file, ticks: 1000 rows/file) organized by timeframe
   - **File Structure**:
     ```
     data/data_output/assets_data/realtime_stream/
     ├── 1M_candles/EURUSD_1m_20250124_120000.csv
     ├── 15M_candles/EURUSD_15m_20250124_120000.csv
     ├── H1_candles/EURUSD_60m_20250124_120000.csv
     └── 1M_ticks/EURUSD_tick_20250124_120000.csv
     ```
   - **Rationale**: Prevents file bloat, enables efficient data loading, organizes by timeframe for analysis
   - **Pros**: Manageable file sizes, easy historical queries, timeframe-specific organization
   - **Cons**: More files to manage, requires file rotation logic

7. **Selenium UI Control Helpers**
   - **Problem**: PocketOption UI requires precise element interaction (dropdowns, buttons, favorites scrolling)
   - **Solution**: `HighPriorityControls` and `ZoomManager` utility classes for robust UI interaction
   - **Rationale**: Centralized UI interaction logic reduces duplication and handles edge cases (stale elements, visibility, zoom levels)
   - **Pros**: Reusable across capabilities, handles UI quirks consistently
   - **Cons**: Platform-specific (tied to PocketOption UI structure)

8. **Strategy Engine with Confidence Scoring**
   - **Problem**: Need systematic approach to evaluate trading signals from multiple indicators
   - **Solution**: Modular strategy system with tiered implementations (Advanced, Alternative, Basic) and confidence-based signal generation
   - **Strategy Tiers**:
     - **Advanced** (`advanced.py`): Most sophisticated with enhanced RSI/EMA calculations
     - **Alternative** (`alternative.py`): Unique approaches with different methodologies
     - **Basic** (`basic.py`): Simple, reliable strategies for consistent performance
   - **Rationale**: Allows A/B testing of different approaches, confidence scoring enables risk management
   - **Pros**: Testable strategies, confidence-based filtering, multi-tier evaluation
   - **Cons**: Requires historical data for backtesting, complex strategy management

### Data Flow Architecture

**Real-time Data Pipeline:**
```
PocketOption WebSocket → Chrome DevTools Protocol → Performance Log Interception → 
Base64 Decode → Socket.IO Frame Parse → Tick Data → Candle Formation → CSV Export
```

**Trading Execution Flow:**
```
Signal Generation (Indicators) → Confidence Scoring → Strategy Validation → 
Trade Click Capability → WebDriver Interaction → Execution Verification → Result Logging
```

## External Dependencies

### Browser Automation & Session Management
- **Chrome Browser**: Required for PocketOption web interface interaction
- **Selenium WebDriver**: Browser automation framework for element interaction and screenshot capture
- **Chrome Remote Debugging Protocol (Port 9222)**: Enables WebSocket interception and persistent session attachment
- **Persistent Chrome Profile**: Workspace directory (`Chrome_profile/`) maintains cookies, login state, and preferences

### Data Processing & Analysis
- **Pandas**: DataFrame operations for CSV export and candle data processing
- **NumPy**: Numerical operations for technical indicator calculations (RSI, SMA, EMA, MACD)
- **SciPy**: Statistical functions for advanced signal analysis

### Web Framework & API
- **FastAPI**: Modern async web framework for REST API endpoints
- **Uvicorn**: ASGI server for serving FastAPI application
- **WebSocket Support**: Real-time bidirectional communication for live data streaming

### CLI & Automation
- **Typer**: Command-line interface framework for `qf.py` tool
- **asyncio**: Asynchronous operations for concurrent data streaming and UI interaction

### Testing & Quality
- **Pytest**: Testing framework for capability validation
- **pytest-asyncio**: Async test support for WebSocket and streaming tests

### Platform Integration: PocketOption
- **WebSocket API**: Real-time market data stream (intercepted via Chrome DevTools)
- **Socket.IO Protocol**: Message framing for WebSocket data (base64 encoded frames)
- **Web UI Elements**: Platform-specific selectors for profile, session state, favorites bar, trade buttons, and timeframe dropdowns
- **Session Authentication**: Login state managed through persistent Chrome profile

### Data Storage
- **CSV Files**: Primary persistence mechanism for historical and real-time market data
- **JSON Files**: Configuration storage for strategies, pipelines, and capability inputs
- **File System**: Organized directory structure for timeframe-specific data (`1M_candles/`, `15M_candles/`, `H1_candles/`, etc.)

**Note**: While the architecture supports future database integration (Drizzle ORM references exist in requirements), current implementation uses file-based persistence exclusively.