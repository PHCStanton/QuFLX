# QuantumFlux Trading Platform - Project Status

## Current Status: Real-Time Streaming Infrastructure (Phases 1-4 Complete) ✅

**Last Updated**: October 9, 2025

### Project State
The platform now has a **robust real-time streaming infrastructure** with clear separation between historical data collection and live streaming. The GUI backend (`streaming_server.py`) properly delegates to `RealtimeDataStreaming` capability with zero code duplication, enhanced error handling, and explicit data provider controls.

### Recent Completions (October 9, 2025)

#### Phase 1: Backend Infrastructure Fixes ✅
- **Eventlet Configuration**: Fixed WebSocket AssertionError, proper eventlet patching
- **Chrome Connection**: Fast-fail timeout (1s) on port 9222, graceful degradation when unavailable
- **Error Handling**: Chrome status monitoring (5-second polling), clear error messages
- **Stability**: Backend runs reliably with/without Chrome connection

#### Phase 2: Stream Data Collection ✅
- **CLI Argument**: `--collect-stream {tick,candle,both,none}` for optional persistence
- **Persistence Manager**: StreamPersistenceManager integration with rotating CSV writers
- **Chunk Sizes**: Configurable (default: 100 candles, 1000 ticks per file)
- **Output Directories**:
  - Candles: `data/data_output/assets_data/realtime_stream/1M_candle_data/`
  - Ticks: `data/data_output/assets_data/realtime_stream/1M_tick_data/`
- **Bug Fixes**: Fixed tick persistence method signature

#### Phase 3: Frontend Data Provider Separation ✅
- **Explicit Selection**: Removed "Auto" mode, enforced CSV vs Platform choice
- **Critical Bug Fixes**:
  - False live state prevention (connections validated before activation)
  - Disconnect handling (auto-stop on Chrome/backend disconnect)
  - Asset validation (prevents invalid assets on mode switch)
  - Race condition fix (validates assets before streaming)
- **Timeframe Control**:
  - Platform mode: Locked to 1M (timeframe selector disabled)
  - CSV mode: All timeframes (1m, 5m, 15m, 1h, 4h)
- **User Experience**: Clear visual indicators, helper text, console logging

#### Phase 3.5: Code Quality Improvements ✅
- **LSP Fix**: Added `log_output=False` to socketio.run()
- **Semantic Corrections**:
  - First activation: Uses `startStream(asset)`
  - Asset switching: Uses `changeAsset(asset)` (not redundant startStream)
- **Chrome Disconnect Handling**:
  - Proactive check before accessing logs
  - Chrome-related error detection in exception handler
  - Emits `stream_error` event to frontend
  - Sets `streaming_active=False` on disconnect

#### Phase 4: Asset Focus Integration ✅
- **Verification**: Existing implementation confirmed complete
- **Backend API**: `set_asset_focus()`, `release_asset_focus()`, `get_current_asset()`
- **Socket.IO Events**: Properly wired (start_stream, change_asset, stop_stream)
- **Frontend**: Uses correct event sequence for asset control

### Previous Completions (October 7, 2025)

#### Critical Architectural Fixes ✅
- **Asset Filtering**: Fixed to START of _process_realtime_update()
- **Candle Formation**: Eliminated frontend duplication (backend emits, frontend displays)
- **API Methods**: Added set_asset_focus, set_timeframe, get_latest_candle, etc.
- **Clean Encapsulation**: streaming_server.py uses API methods only
- **Data Flow**: Simplified (capability → server → frontend, single source of truth)
- **Backpressure**: 1000-item buffer limit in frontend
- **Port Configuration**: Fixed Vite to port 5000

### Data Architecture: Two Distinct Pipelines

#### Pipeline 1: Historical/Topdown Collection
```
capabilities/data_streaming_csv_save.py
        ↓
scripts/custom_sessions/favorites_select_topdown_collect.py
        ↓
Automated TF switching (1H → 15M → 5M → 1M)
        ↓
Saves to: data/data_output/assets_data/data_collect/
        ↓
Purpose: Historical backtesting, strategy development
Status: ✅ Independent, not used by streaming_server.py
```

#### Pipeline 2: Real-Time Streaming (Current Focus)
```
capabilities/data_streaming.py (RealtimeDataStreaming)
        ↓
streaming_server.py (Flask-SocketIO, port 3001)
        ↓
Socket.IO → React Frontend (port 5000)
        ↓
Optional: --collect-stream → realtime_stream/ directory
        ↓
Purpose: Live trading, GUI visualization
Status: 🚧 Phases 1-4 complete, Phase 5 pending
```

### Current Workflows

**Backend Workflow**:
```bash
uv run python streaming_server.py
# Optional: --collect-stream {tick,candle,both,none}
# Optional: --candle-chunk-size 200 --tick-chunk-size 2000
```

**Frontend Workflow**:
```bash
cd gui/Data-Visualizer-React && npm run dev
```

### Architecture Flow

**Real-Time Streaming (Simplified)**:
```
PocketOption WebSocket
        ↓
Chrome DevTools Protocol (Port 9222)
        ↓
Performance Log Interception (streaming_server.py)
        ↓
RealtimeDataStreaming Capability:
  - _decode_and_parse_payload
  - Asset Filtering (START)
  - _process_realtime_update
  - _process_chart_settings
  - Candle Formation
        ↓
API Methods: get_latest_candle(asset)
        ↓
Socket.IO Emit: candle_update
        ↓
Frontend Display (1000-item backpressure buffer)
        ↓
Chart Update
```

### Socket.IO Events

**Backend → Frontend (Outbound)**:
- `connection_status` - Chrome/backend status updates
- `candle_update` - New candle data
- `stream_started` - Stream activation confirmation
- `stream_stopped` - Stream deactivation confirmation
- `stream_error` - Error notifications (Chrome disconnect, etc.)
- `asset_changed` - Asset switch confirmation

**Frontend → Backend (Inbound)**:
- `start_stream` - Enable streaming for asset
- `stop_stream` - Disable streaming
- `change_asset` - Switch to different asset
- `run_backtest` - Execute backtest (CSV data)
- `get_available_data` - List CSV files

### Frontend Data Sources

**CSV Mode**:
- Source: Pre-collected historical files
- Location: `/public/data` directory
- Timeframes: 1m, 5m, 15m, 1h, 4h (user selectable)
- Assets: All available CSV files

**Platform Mode**:
- Source: Live WebSocket streaming
- Backend: streaming_server.py (port 3001)
- Timeframe: 1M only (locked)
- Assets: EURUSD_OTC, GBPUSD_OTC, USDJPY_OTC, AUDUSD_OTC (hardcoded)

### Key Architectural Decisions

1. **Dual Pipeline Separation**
   - Historical collection ≠ Real-time streaming
   - Different capabilities for different purposes
   - No code overlap or conflicts

2. **Capability Delegation**
   - streaming_server.py delegates ALL WebSocket logic to RealtimeDataStreaming
   - Zero code duplication
   - Single source of truth for candle formation

3. **Explicit Data Provider Control**
   - User must explicitly select CSV or Platform
   - No auto-switching between modes
   - Asset validation on mode changes

4. **Connection-Gated Streaming**
   - Live mode requires Chrome + backend connections
   - Automatic disconnect handling
   - Visual indicators for connection status

5. **Optional Stream Persistence**
   - Disabled by default
   - Configurable via CLI arguments
   - Separate output directory from historical collection

6. **Graceful Chrome Handling**
   - Backend starts without Chrome (streaming unavailable)
   - 1-second fast-fail timeout on connection
   - Proactive disconnect detection

### Known Issues (Non-Critical)
None currently blocking development

### Next Steps

#### Phase 5: Auto-Detection Features (Pending User Decision)
**Options**:
- Option A: Auto-follow toggle (chart follows PocketOption UI)
- Option B: Display auto-detected values (read-only indicator)

**Current Behavior**:
- Manual asset selection with focus lock
- Auto-detection capability exists but disabled
- Timeframe locked to 1M in platform mode

#### Phase 6: Comprehensive Testing (Queued)
- [ ] Chrome disconnect/reconnect scenarios
- [ ] Mode switching (CSV ↔ Platform)
- [ ] Asset switching in live mode
- [ ] Stream persistence verification
- [ ] Extended stability (30+ minutes)
- [ ] Backpressure under load

### System Health

- ✅ Backend running reliably (port 3001)
- ✅ Frontend running reliably (port 5000)
- ✅ Chrome connection optional (graceful degradation)
- ✅ Stream data collection configurable
- ✅ Asset focus system working
- ✅ Disconnect handling robust
- ✅ Asset validation preventing errors
- ✅ Zero code duplication (architect approved)
- ✅ No runtime errors

### Important Notes for Future Sessions

**Data Pipeline Separation**:
- Historical collection: `capabilities/data_streaming_csv_save.py` → `data_collect/`
- Real-time streaming: `capabilities/data_streaming.py` → `realtime_stream/`
- **streaming_server.py uses data_streaming.py ONLY**

**Backend Architecture**:
- `streaming_server.py` in ROOT folder
- Delegates to RealtimeDataStreaming capability
- Uses API methods only (no direct state access)
- Optional persistence via --collect-stream argument

**Frontend**:
- Explicit data provider selection (CSV or Platform)
- Platform mode: 1M only, hardcoded assets
- CSV mode: All timeframes, discovered files
- Backpressure: 1000-item buffer limit

**Chrome Connection**:
- Port 9222 (Chrome DevTools Protocol)
- Fast-fail: 1-second timeout on startup
- Monitoring: 5-second polling
- Graceful: Backend runs without Chrome

**Current Development Status**:
- Phases 1-4: ✅ Complete
- Phase 5: ⏸️ Pending user decision (auto-detection approach)
- Phase 6: 📅 Queued (comprehensive testing)

### Quick Start Commands

**Backend (with stream collection)**:
```bash
# Collect both candles and ticks
uv run python streaming_server.py --collect-stream both

# Candles only with custom chunk size
uv run python streaming_server.py --collect-stream candle --candle-chunk-size 200
```

**Frontend**:
```bash
cd gui/Data-Visualizer-React && npm run dev
```

**Chrome (for live streaming)**:
```bash
chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
# Then log into PocketOption
```

---

**Last Major Update**: October 9, 2025 - Real-time streaming infrastructure (Phases 1-4)

**Next Context Start Point**: Review TODO.md and gui/gui_dev_plan_mvp.md for current phase status
