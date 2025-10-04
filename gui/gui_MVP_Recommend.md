MVP production plan (clean core only: streaming, analytics, basic strategy testing)

Goal Deliver a proof-of-concept that:

- Streams live ticks and 1m candles to the React app
- Loads historical candles for analysis
- Runs basic strategies on historical and live data (SMA/RSI overlays + simple signals)
- Uses minimal moving parts, production-stable enough for a demo

Architecture (minimal)

- One streaming gateway with Socket.IO that talks directly to capabilities/data_streaming.py

  - If you want zero backend dependencies: a single “custom session” process that attaches to Chrome and emits Socket.IO events the frontend already expects
  - If you prefer to reuse the existing FastAPI file later, this gateway can be folded in afterward

Core components

1. Streaming gateway (single file)

- Location: scripts/custom_sessions/gui_stream_session.py

- Responsibilities:

  - Attach to Chrome hybrid session (9222)
  - Create RealtimeDataStreaming and run a lightweight loop
  - Socket.IO server on port 3001

- Socket.IO contract (matches WebSocketProvider):

  - Client emits:

    - start_stream {asset: string, timeframe: "1m"|"5m"|...}
    - stop_stream
    - request_historical {asset, timeframe, lookback?: number}

  - Server emits:

    - price_tick {asset, tick: {price:number, timestamp:number}, timestamp:number}
    - candle_update {asset, candle: {time:number, open:number, high:number, low:number, close:number}}
    - historical_data {asset, timeframe, data: Candle[]} (on request_historical)

- MVP behaviors:

  - On start_stream:

    - Set cap.PERIOD from timeframe (1m→60s, etc.)
    - Enable ASSET_FOCUS_MODE and attempt to sync CURRENT_ASSET; if mismatch, still stream but warn
    - Seed: run cap.run(ctx, {period: seconds}) once to populate CANDLES; immediately emit the latest N candles (e.g., last 200)

  - Tick→candle:

    - Forward ticks as price_tick with epoch ms
    - Detect new-candle rollover from data_streaming (when last candle boundary increments) and emit candle_update promptly

  - request_historical:
    - If cap.CANDLES[asset] available, slice last N and emit; otherwise return an empty set (MVP avoids CSV IO at this layer)

2. Frontend wiring (small)

- Enable the WebSocket provider in DataAnalysis.jsx (already scaffolded)

  - Provider selector: add “WebSocket” option

  - On Live mode toggle with WebSocket provider:

    - connect → subscribe(asset, timeframe)
    - update LightweightChart on candle_update; optionally show price_tick as last-trade marker

- Strategy & Backtest (frontend-only in MVP)

  - Use existing technicalindicators library to compute SMA/RSI client-side
  - Backtest page runs simple strategy on currently loaded historical Candle[] (from CSV provider or historical_data event)
  - Live Trading page listens to candle_update and recomputes indicators incrementally to show a basic BUY/SELL/NEUTRAL signal

3. Historical data source (MVP-simple)

- Primary: use existing CSVProvider for historical charts (public/data)
- Secondary: the streaming gateway’s request_historical simply serves the in-memory cap.CANDLES snapshot (no disk IO), good enough for demo

Minimal schemas

- Candle: { time: number (unix sec), open: number, high: number, low: number, close: number, volume?: 0 }
- PriceTick: { asset: string, tick: { price: number, timestamp: number (ms) }, timestamp: number (ms) }

Acceptance criteria

- Live chart updates within 500 ms perceptible latency
- Candle rollover matches chart timeframe (1m); no duplicate bars
- Toggle Live Mode shows streaming for at least one asset (e.g., EURUSD_OTC)
- Basic SMA/RSI overlays render on both historical and live; simple overall signal (BUY/SELL/NEUTRAL) visible
- Stability: stream runs for >30 minutes without unhandled exceptions

Out of scope for MVP (intentionally deferred)

- Multi-asset simultaneous subscriptions
- Server-side strategy engine (use frontend indicators)
- Persistence sinks and rotation
- Authentication, rate-limits, metrics dashboards
- Trade execution endpoints

Runbook (PowerShell)

- Start Chrome hybrid session and log into PocketOption:
  - python start_hybrid_session.py

- Start streaming gateway:
  - python scripts/custom_sessions/gui_stream_session.py --port 3001 --period 1

- Start React app:

  - cd gui/Data-Visualizer-React
  - npm install
  - npm run dev

- In app:

  - Select CSV provider to load historical data
  - Switch to WebSocket provider → enable Live Mode → choose asset/timeframe
  - View live candle formation and indicator overlays

Why this is minimal yet production-friendly

- Single small server process; no extra bridge and no additional REST needed
- Uses your proven RealtimeDataStreaming for session/timeframe sync and candle formation
- Frontend remains provider-agnostic; switching providers is trivial
- Clean separation: backend streams raw market structure; frontend handles simple analytics/backtests

If you approve, I’ll draft:

- scripts/custom_sessions/gui_stream_session.py (Socket.IO + capability loop, 200–300 LOC)
- Minimal tweak in DataAnalysis.jsx to enable the WebSocket provider Live mode and subscribe on toggle