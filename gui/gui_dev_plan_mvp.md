GUI MVP Development Plan (Phased)

Scope
- Implement a minimal, production-friendly MVP focused on:
  - Live streaming of ticks and 1m candles
  - Historical candle loading
  - Client-side SMA/RSI overlays and simple signals
  - Minimal moving parts: a single Socket.IO gateway process + frontend wiring
- Keep server responsibilities narrow: stream raw market structure only; analytics on the frontend.

Repository Alignment (File Context)
- This plan is mapped to your existing structure discovered under gui/Data-Visualizer-React:
  - Pages:
    - src/pages/DataAnalysis.jsx
    - src/pages/LiveTrading.jsx
    - src/pages/StrategyBacktest.jsx
  - Providers and Services:
    - src/services/providers/CSVProvider.js
    - src/services/providers/WebSocketProvider.js
    - src/services/providers/PlatformAPIProvider.js
    - src/services/DataProviderService.js
    - src/services/StrategyService.js
    - src/services/TradingService.js
    - src/services/README.md
  - Hooks:
    - src/hooks/useWebSocket.js
  - Charts and Components:
    - src/components/charts/LightweightChart.jsx
    - src/components/TradingChart.jsx
    - src/components/RealTimeChart.jsx
    - src/components/IndicatorPanel.jsx
    - src/components/BacktestPanel.jsx
  - Static historical data (primary source in MVP):
    - public/data/*.csv
  - Existing React tooling:
    - vite.config.js, index.html, src/main.jsx, src/App.jsx
- Backend-lite gateway target (single file):
  - scripts/custom_sessions/gui_stream_session.py (to be created in repository root, not inside the React app)

Minimal Data Schemas (used across gateway and frontend)
- Candle: { time: number (unix sec), open: number, high: number, low: number, close: number, volume?: 0 }
- PriceTick: { asset: string, tick: { price: number, timestamp: number (ms) }, timestamp: number (ms) }

Socket.IO Contract (matches WebSocketProvider expectations)
- Client emits:
  - start_stream { asset: string, timeframe: "1m"|"5m"|... }
  - stop_stream
  - request_historical { asset: string, timeframe: string, lookback?: number }
- Server emits:
  - price_tick { asset, tick: { price, timestamp(ms) }, timestamp(ms) }
  - candle_update { asset, candle: { time, open, high, low, close } }
  - historical_data { asset, timeframe, data: Candle[] }

Status Legend
- [x] Complete
- [ ] Not Complete

Phase 0 — Environment & Repo Verification
- [x] 0.1 Validate frontend structure and key files (pages, providers, hooks, charts) exist in gui/Data-Visualizer-React
- [ ] 0.2 Confirm React app runs locally (npm install, npm run dev)
- [ ] 0.3 Verify CSV historical files load via CSVProvider.js and render charts
- [ ] 0.4 Confirm WebSocketProvider.js and useWebSocket.js are available and usable as scaffolding
- [ ] 0.5 Align schemas: ensure CSVProvider → Candle[] uses {time (sec), OHLC} format consistent with gateway

Phase 1 — Streaming Gateway (single process) at scripts/custom_sessions/gui_stream_session.py
Responsibilities
- Attach to Chrome hybrid session (9222)
- Instantiate and run RealtimeDataStreaming (from capabilities/data_streaming.py)
- Map timeframe to period seconds (e.g., 1m → 60s)
- Socket.IO server on port 3001 with the contract above
- MVP behaviors:
  - On start_stream:
    - Set cap.PERIOD from timeframe
    - Enable ASSET_FOCUS_MODE and attempt CURRENT_ASSET sync; warn on mismatch but stream anyway
    - Seed: run cap.run(ctx, {period}) once; immediately emit last N candles (e.g., 200) via historical_data
  - Ticks → candles:
    - Emit price_tick on each tick
    - Detect candle boundary rollover; emit candle_update promptly
  - request_historical:
    - Serve last N from in-memory cap.CANDLES[asset] or empty if not available

Tasks
- [ ] 1.1 Create scripts/custom_sessions/gui_stream_session.py
- [ ] 1.2 Initialize Socket.IO server (e.g., python-socketio + ASGI or simple WSGI) on port 3001
- [ ] 1.3 Integrate hybrid session attach (9222) and instantiate RealtimeDataStreaming
- [ ] 1.4 Implement start_stream/stop_stream/request_historical event handlers
- [ ] 1.5 Implement seeding last N candles on start_stream
- [ ] 1.6 Implement tick forwarding (price_tick) and candle rollover detection (candle_update)
- [ ] 1.7 Validate schema consistency and log warnings on asset/timeframe mismatch
- [ ] 1.8 Add basic error handling, logging, and graceful shutdown

Phase 2 — Frontend WebSocket Provider Enablement
DataAnalysis page wiring
- [ ] 2.1 Add/verify "WebSocket" option in provider selector (src/pages/DataAnalysis.jsx)
- [ ] 2.2 On toggling Live Mode with WebSocket provider: connect → subscribe(asset, timeframe)
- [ ] 2.3 Update LightweightChart.jsx or TradingChart.jsx pipeline to handle candle_update and optional price_tick marker
- [ ] 2.4 Ensure unsubscribe/cleanup on toggle off, unmount, or provider switch

Provider/service contracts
- [ ] 2.5 Verify src/services/providers/WebSocketProvider.js exposes connect, subscribe(asset, timeframe), unsubscribe/stop, disconnect, and optional requestHistorical(asset, timeframe, lookback)
- [ ] 2.6 If needed, enhance src/hooks/useWebSocket.js to handle reconnection/backoff and message routing
- [ ] 2.7 Ensure DataProviderService.js cleanly switches between CSVProvider and WebSocketProvider without cross-contamination of state

Phase 3 — Historical Data Loading & Synchronization
- [ ] 3.1 Default historical load: CSVProvider (public/data/*.csv) for initial charts
- [ ] 3.2 When WebSocket provider is active, optionally call request_historical on gateway to hydrate chart from in-memory cap.CANDLES (last N)
- [ ] 3.3 Normalize Candle[] to common schema and ensure correct time units (sec for time, ms for tick timestamps)
- [ ] 3.4 Validate no duplicate bars; correct placement on timeframe boundaries
- [ ] 3.5 Implement data reset/merge policy when switching providers (e.g., replace series on provider change)

Phase 4 — Client-side Indicators and Strategy MVP
- [ ] 4.1 Install/use technicalindicators for SMA/RSI in the frontend
- [ ] 4.2 Overlay SMA/RSI on historical data (DataAnalysis.jsx + LightweightChart overlays)
- [ ] 4.3 Incrementally recompute indicators on candle_update for live mode
- [ ] 4.4 StrategyBacktest.jsx: run simple strategy over currently loaded Candle[] (params for SMA/RSI windows)
- [ ] 4.5 LiveTrading.jsx: compute simple BUY/SELL/NEUTRAL signal on latest candle + indicators; display clearly
- [ ] 4.6 Ensure indicator and signal updates are performant and do not block UI

Phase 5 — QA, Performance, and Stability
- [ ] 5.1 Latency check: price moves render <= 500 ms perceived delay
- [ ] 5.2 Candle rollover correctness: bars align to timeframe; no duplicates
- [ ] 5.3 Stability test: stream runs > 30 minutes without unhandled exceptions
- [ ] 5.4 Provider toggling: CSV → WebSocket → CSV works without stale state or leaks
- [ ] 5.5 Error handling: visible toasts/logs for connection drops, schema errors, or unsupported assets
- [ ] 5.6 Basic metrics/logging in gateway for troubleshooting

Phase 6 — Runbook (PowerShell)
- [ ] 6.1 Start Chrome hybrid session and log into PocketOption:
      python start_hybrid_session.py
- [ ] 6.2 Start streaming gateway (from repo root):
      python scripts/custom_sessions/gui_stream_session.py --port 3001 --period 1
  Notes:
  - --period 1 here means 1 minute timeframe target; internally map to seconds when needed.
  - Alternatively allow --timeframe 1m and convert to seconds.
- [ ] 6.3 Start React app (in a new PowerShell):
      cd gui/Data-Visualizer-React
      npm install
      npm run dev
- [ ] 6.4 In app:
  - Select CSV provider to load historical data
  - Switch to WebSocket provider → enable Live Mode → choose asset/timeframe
  - Validate live candle formation and overlays

Acceptance Criteria
- [ ] A1 Live chart updates within 500 ms perceived latency
- [ ] A2 Candle rollover matches chart timeframe (1m); no duplicate bars
- [ ] A3 Live Mode streams at least one asset (e.g., EURUSD_OTC) reliably
- [ ] A4 SMA/RSI overlays render on historical and live data; simple BUY/SELL/NEUTRAL visible
- [ ] A5 Stream stability > 30 minutes without unhandled exceptions

Out of Scope (MVP)
- [x] S1 Multi-asset simultaneous subscriptions (deferred)
- [x] S2 Server-side strategy engine (frontend only)
- [x] S3 Persistence, rotation, dashboards (deferred)
- [x] S4 Authentication, rate-limits (deferred)
- [x] S5 Trade execution endpoints (deferred)

Deliverables
- [ ] D1 scripts/custom_sessions/gui_stream_session.py (Socket.IO + capability loop; ~200–300 LOC)
- [ ] D2 Updated DataAnalysis.jsx to enable WebSocket provider and Live Mode wiring
- [ ] D3 WebSocketProvider.js updates for subscribe/unsubscribe/requestHistorical as needed
- [ ] D4 Indicator overlays (SMA/RSI) and simple strategies in StrategyBacktest.jsx and LiveTrading.jsx
- [ ] D5 This plan file (gui/gui_dev_plan_mvp.md) and a short README snippet in gui/Data-Visualizer-React/README.md for usage

Immediate Next Actions (Implementation Order)
- [ ] N1 Implement Phase 1 gateway (D1)
- [ ] N2 Wire frontend provider toggle and live subscribe flow (D2, D3)
- [ ] N3 Historical hydration and schema alignment (Phase 3)
- [ ] N4 Indicators + simple strategies (Phase 4)
- [ ] N5 QA against acceptance criteria (Phase 5)

Meta
- [x] M1 Analyze repo structure and align plan
- [x] M2 Create gui/gui_dev_plan_mvp.md (this file)
