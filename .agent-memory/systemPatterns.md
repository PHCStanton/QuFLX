# System Patterns

## Architecture Overview
QuantumFlux uses a **capabilities-first architecture** with direct integration patterns:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Chrome        │    │   Backend API    │    │   CLI Tool      │
│   (PocketOption)│◄──►│   (FastAPI)      │◄──►│   (qf.py)       │
│   Port 9222     │    │   Port 8000      │    │   Direct Access │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Capabilities Framework                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐│
│  │data_streaming│ │session_scan │ │profile_scan │ │trade_click  ││
│  │(Core Engine)│ │             │ │             │ │             ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘│
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   Data Export   │
│   CSV Files     │
│   Historical/   │
│   data_stream/  │
└─────────────────┘
```

## Key Design Patterns

### 1. Capabilities-First Pattern
- **Direct Import**: Backend imports capabilities directly without adapter layers
- **Core Engine**: `data_streaming.py` serves as the primary data collection engine
- **Unified Context**: Single `Ctx` object provides driver, artifacts, and configuration

### 2. Hybrid Chrome Session Pattern
- **Persistent Session**: Chrome runs with `--remote-debugging-port=9222`
- **Workspace Profile**: Uses `Chrome_profile/` directory for session persistence
- **Remote Attachment**: Selenium attaches to existing Chrome instance instead of launching new one

### 3. Multi-Interface Pattern
- **API Interface**: FastAPI backend for programmatic access
- **CLI Interface**: Typer-based command-line tool for direct operations
- **Smoke Testing**: Automated verification of all system components

### 4. Data Streaming Pattern
- **WebSocket Interception**: Captures real-time market data from PocketOption
- **Candle Formation**: Converts tick data to OHLC candles with configurable timeframes
- **Automatic Export**: CSV files saved to `data/data_output/assets_data/realtime_stream/` (candles: `1M_candle_data`, ticks: `1M_tick_data`)

### 5. Session Role Separation Pattern
- **Collector Session**: `data_stream_collect.py` persists by default (both ticks and closed candles).
- **Strategy/Testing Sessions**: `data_collect_topdown_select.py` and `TF_dropdown_open_close.py` do not persist by default; persistence is opt‑in.

### 6. Opt‑in Persistence Injection Pattern
- **Local Patching**: The persistence layer wraps the stream output only when enabled (CLI flags or env vars), leaving core capability code unchanged.
- **Controls**: `--save-candles`, `--save-ticks`, `--candle-chunk-size`, `--tick-chunk-size`, or env overrides `QF_PERSIST`, `QF_PERSIST_CANDLES`, `QF_PERSIST_TICKS`.

### 7. Chunked Sink Rotation Pattern
- **CSV Sinks**: Thread‑safe writers rotate files deterministically after N rows (default: 100 candles, 1000 ticks).
- **Crash‑safe**: Each write opens/appends/closes; headers are written per file; per‑session prefixes prevent collisions.

## Data Flow

### Real-time Data Collection
1. **Chrome Session**: User navigates to PocketOption in persistent Chrome session
2. **WebSocket Capture**: `data_streaming.py` intercepts WebSocket messages via performance logs
3. **Data Processing**: Raw WebSocket data converted to structured candles
4. **CSV Export**: Processed data automatically saved with timestamps
5. **API Access**: Data available via REST endpoints and WebSocket streaming

### Trading Operations
1. **Session Attachment**: Backend/CLI attaches to Chrome session on port 9222
2. **Capability Execution**: Direct capability calls (profile_scan, trade_click, etc.)
3. **UI Interaction**: Selenium automation interacts with PocketOption interface
4. **Result Processing**: Capability results returned with artifacts and diagnostics

## Significant Technical Decisions

### Decision 1: Eliminate Complex Adapter Layers
**Rationale**: The original CapabilitiesAdapter created unnecessary complexity and caused context object issues. Direct capabilities integration is simpler, more reliable, and easier to maintain.

### Decision 2: Use data_streaming.py as Core Engine
**Rationale**: `data_streaming.py` already works reliably for WebSocket data collection and CSV export. Building the backend around this proven foundation ensures stability.

### Decision 3: Workspace Chrome Profile
**Rationale**: Using a workspace-local `Chrome_profile/` directory keeps all project files contained and ensures consistent session management across different environments.

### Decision 4: Multi-Interface Approach
**Rationale**: Providing both API and CLI interfaces maximizes flexibility - CLI for direct operations and testing, API for GUI integration and external systems.

### Decision 5: Capabilities Framework Foundation
**Rationale**: The existing capabilities framework provides robust, tested functionality for all trading operations. Building on this foundation rather than replacing it ensures reliability.

## Error Handling Patterns
- **Context Validation**: All capabilities verify proper Ctx object before execution
- **Chrome Connection**: Automatic detection and handling of Chrome session availability
- **Graceful Degradation**: System continues operating even if some capabilities fail
- **Comprehensive Logging**: Detailed error messages and diagnostic information

## Testing Patterns
- **Smoke Testing**: `test_smoke.py` verifies all major system components
- **CLI Testing**: Direct capability testing via command-line interface
- **API Testing**: REST endpoint verification and health checks
- **Integration Testing**: End-to-end workflow validation
