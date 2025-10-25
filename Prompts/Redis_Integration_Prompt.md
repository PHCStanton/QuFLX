# Prompt for Coding Agent: Integrating Redis into QuFLX for Real-Time Tick Data Streaming and Caching

**Objective**: Integrate a local Redis instance into the QuFLX trading platform to replace the Map-based buffer in `useDataStream.js` and cache historical data, while using Supabase for persistent tick storage. This is for a single-user, localhost-based prototype streaming OTC currency tick data via WebSocket.

**Context** (from QuFLX Data Handling Report, Oct 25, 2024, and user discussion):
- **Platform**: Binary options trading system with real-time tick data (e.g., `{ pair: "EUR/USD_otc", price: 1.0823, timestamp: 169... }`, ~1000 ticks/min) and historical data storage.
- **Backend**: `streaming_server.py` (Python, Socket.IO) handles WebSocket data via Chrome DevTools or simulated streams. Stores historical data in CSV and Supabase (`historical_ticks` table: `pair VARCHAR`, `price FLOAT`, `timestamp BIGINT`).
- **Frontend**: React with `useDataStream.js` (Map-based buffer, 1000-candle capacity, O(log n) insertion), `MultiPaneChart.jsx` (Lightweight Charts), and `useCsvData` for Supabase/CSV data.
- **Current Buffering**: Optimized Map-based buffer with `requestAnimationFrame`, but report recommends Redis caching for historical data (Section 8, High Priority).
- **Environment**: Localhost, Node.js frontend, Python backend, single user, no external deployment.
- **Decisions**:
  1. Replace Map-based buffer in `useDataStream.js` with Redis for real-time streaming.
  2. Store individual tick data in Supabase `historical_ticks` for flexibility.
  3. Use a single Redis instance for simplicity, no clustering.
  4. Apply automatic cache expiration (1-hour TTL) for historical data.

**Requirements**:
1. **Redis Setup**:
   - Install Redis locally (port 6379, default config).
   - Use Python `redis-py` for backend and Node.js `redis` for frontend.
2. **Backend Modifications**:
   - Update `streaming_server.py` to push ticks to Redis lists (e.g., `ticks:EURUSD`) and publish to pub/sub channels (e.g., `updates:EURUSD`).
   - Batch ticks from Redis to Supabase every 30s.
   - Cache last 200 candles in Redis (e.g., `historical:EURUSD:1M`) with 1-hour expiration.
3. **Frontend Modifications**:
   - Replace `useDataStream.js` Map-based buffer with Redis pub/sub via Socket.IO.
   - Update `useCsvData` to check Redis cache before Supabase queries.
   - Maintain 60fps chart updates and <10ms latency.
4. **Supabase Integration**:
   - Store individual ticks in `historical_ticks` (reuse existing schema).
   - Batch-insert ticks from Redis every 30s.
5. **Performance**:
   - Target <1ms Redis operations, <10ms end-to-end latency.
   - Cap Redis lists at ~1000 ticks, cache at 200 candles.
6. **Error Handling**:
   - Handle Redis connection failures and Supabase insert errors.
   - Log buffer overflows or latency spikes (>10ms).
7. **Future-Proofing**:
   - Modularize Redis logic for Redis Cloud or clustering.
   - Support multi-asset streaming (e.g., `ticks:GBPUSD`).

**Implementation Details**:
- **Redis Installation**:
  - Install: `brew install redis` (MacOS) or `sudo apt-get install redis-server` (Linux).
  - Run: `redis-server` (port 6379). Verify: `redis-cli ping` (returns `PONG`).
  - No persistence needed (Supabase handles it).
- **Backend (`streaming_server.py`)**:
  - Install `redis-py`: `pip install redis`.
  - On `candle_update` (from Chrome or simulated), push to Redis: `LPUSH ticks:EURUSD <tick_json>`, trim with `LTRIM ticks:EURUSD 0 999`.
  - Publish: `PUBLISH updates:EURUSD <tick_json>`.
  - Every 30s, pop ticks (`LRANGE ticks:EURUSD 0 -1`, `DEL ticks:EURUSD`), batch to Supabase via `SupabaseCsvIngestion`.
  - Cache candles: `SET historical:EURUSD:1M <candles_json>`, `EXPIRE historical:EURUSD:1M 3600`.
  - Update `handle_start_stream` to initialize Redis keys per asset.
- **Frontend (`useDataStream.js`)**:
  - Install `redis`: `npm install redis`.
  - Remove Map-based buffer; subscribe to `updates:EURUSD` via Socket.IO.
  - Update `useCsvData` to check Redis (`GET historical:EURUSD:1M`) before Supabase.
  - Use `requestAnimationFrame` for chart updates, merge with `mergeSortedArrays`.
- **Supabase**:
  - Reuse `historical_ticks` (`pair VARCHAR`, `price FLOAT`, `timestamp BIGINT`).
  - Batch-insert: `supabase.table('historical_ticks').insert([...])`.
- **Testing**:
  - Mock 1000 ticks/min (random EUR/USD_otc prices every 60ms).
  - Verify <10ms latency to frontend, 60fps chart rendering.
  - Confirm Supabase stores ticks without duplicates.
  - Test cache hit (<50ms) vs. Supabase query (100-500ms).

**Deliverables**:
1. Updated `streaming_server.py` with Redis and Supabase batch logic.
2. Updated `useDataStream.js` for Redis pub/sub and `useCsvData` for caching.
3. SQL schema for `historical_ticks` (if modified).
4. `README.md` with setup instructions (Redis install, npm/pip packages, Supabase config).
5. Comments explaining Redis buffer/cache and Supabase integration.

**Example Workflow**:
- Tick arrives via WebSocket → `streaming_server.py` pushes to Redis list → Publishes to channel → Frontend updates chart.
- Every 30s, backend pops ticks, inserts to Supabase.
- Frontend queries historical data: checks Redis cache, falls back to Supabase.

**Output**:
Provide code in separate files (`streaming_server.py`, `useDataStream.js`, `useCsvData.js`, `schema.sql`, `README.md`), wrapped in artifact tags, with inline comments. Ensure it runs on localhost with Redis and Supabase client dependencies only.