# Active Context

**Last Updated**: October 9, 2025

## Current Work
**STATUS**: Real-Time Streaming Infrastructure - Phases 1-5 Complete ✅

**CURRENT PHASE**: Phase 6 (Auto-Detection Features) - Pending User Decision ⏸️

### Just Completed (October 9, 2025)

#### Phase 1: Backend Infrastructure Fixes ✅
- Fixed eventlet/WebSocket configuration (eliminated AssertionError)
- Added Chrome connection fast-fail (1s timeout on port 9222)
- Graceful degradation when Chrome unavailable
- Chrome status monitoring (5-second polling)

#### Phase 2: Stream Data Collection ✅
- Implemented `--collect-stream {tick,candle,both,none}` CLI argument
- Integrated StreamPersistenceManager with rotating CSV writers
- Configurable chunk sizes (100 candles, 1000 ticks default)
- Output directories: `realtime_stream/1M_candle_data/` and `1M_tick_data/`

#### Phase 3: Frontend Data Provider Separation ✅
- Removed "Auto" mode - enforced explicit CSV vs Platform selection
- Fixed false live state (connections validated before activation)
- Added disconnect handling (auto-stop on Chrome/backend disconnect)
- Asset validation (prevents invalid assets on mode switch)
- Race condition fix (validates assets before streaming)
- Platform mode locked to 1M, CSV mode supports all timeframes

#### Phase 3.5: Code Quality Improvements ✅
- Fixed LSP error (added log_output parameter)
- Semantic asset switching (startStream vs changeAsset)
- Enhanced Chrome disconnect handling (proactive checks + stream_error events)

#### Phase 4: Asset Focus Integration ✅
- Verified existing implementation complete
- Backend API working (set_asset_focus, release_asset_focus)
- Socket.IO events properly wired
- Frontend uses correct event sequence

#### Phase 5: Reconnection Lifecycle Management ✅
- Backend state reset on reconnection (clears candle buffers, persistence tracking)
- Chrome auto-reconnection with rate limiting (3 attempts/min, exponential backoff)
- Socket.IO session tracking for reconnection detection
- Events: backend_reconnected, chrome_reconnected with status
- Frontend reconnection callback for automatic state cleanup
- Automatic data recovery (CSV reload or stream restart)
- Visual UI indicators for reconnection status (auto-hide 3s)
- Comprehensive reconnection logging

## Data Architecture: Two Pipelines

### Pipeline 1: Historical/Topdown (Separate)
```
capabilities/data_streaming_csv_save.py
        ↓
scripts/custom_sessions/favorites_select_topdown_collect.py
        ↓
data/data_output/assets_data/data_collect/
```
**Purpose**: Historical backtesting
**Status**: Independent, not used by streaming_server.py

### Pipeline 2: Real-Time Streaming (Current)
```
capabilities/data_streaming.py
        ↓
streaming_server.py (port 3001)
        ↓
Socket.IO → Frontend (port 5000)
        ↓
Optional: realtime_stream/ (--collect-stream)
```
**Purpose**: Live trading, GUI visualization
**Status**: Phases 1-4 complete

## Architecture Flow

**Real-Time Streaming**:
```
PocketOption WebSocket
        ↓
Chrome DevTools (Port 9222)
        ↓
streaming_server.py
        ↓
RealtimeDataStreaming Capability:
  - Asset Filtering (START)
  - Candle Formation
        ↓
Socket.IO: candle_update
        ↓
Frontend (1000-item buffer)
        ↓
Chart Update
```

**Key Features**:
- Asset filtering at source (prevents unwanted switches)
- Single candle formation point (capability only)
- Clean API boundaries (no direct state access)
- Backpressure protection (1000-item buffer limit)
- Optional persistence (--collect-stream flag)

## Next Steps

### Phase 6: Auto-Detection (Pending User Decision)
**Options**:
- A: Auto-follow toggle (chart follows PocketOption UI)
- B: Display auto-detected values (read-only)

**Current Behavior**:
- Manual asset selection with focus lock
- Auto-detection capability exists but disabled
- Timeframe locked to 1M in platform mode

### Phase 7: Comprehensive Testing (Queued)
- Chrome disconnect/reconnect scenarios (basic testing complete)
- Mode switching (CSV ↔ Platform)
- Asset switching in live mode
- Stream persistence verification
- Extended stability (30+ min)
- Backpressure under load

## Blockers
**NONE** - Waiting for user decision on Phase 6 approach

## Important Notes

**Data Pipeline Separation**:
- Historical: `data_streaming_csv_save.py` → `data_collect/`
- Real-time: `data_streaming.py` → `realtime_stream/`
- streaming_server.py uses `data_streaming.py` ONLY

**Frontend Data Sources**:
- CSV Mode: Historical files, all timeframes
- Platform Mode: Live streaming, 1M only, hardcoded assets

**Chrome Connection**:
- Port 9222 (optional)
- 1-second fast-fail timeout
- 5-second monitoring
- Graceful degradation

**Stream Collection**:
```bash
# Default (no collection)
uv run python streaming_server.py

# Collect both
uv run python streaming_server.py --collect-stream both
```

## System Status
✅ Backend stable (port 3001)
✅ Frontend stable (port 5000)
✅ Chrome optional (graceful degradation)
✅ Stream collection configurable
✅ Asset validation working
✅ Disconnect handling robust
✅ Reconnection auto-recovery implemented
✅ Zero code duplication

**Development Status**: Phases 1-5 Complete ✅ | Phase 6 Pending ⏸️ | Phase 7 Queued 📅
