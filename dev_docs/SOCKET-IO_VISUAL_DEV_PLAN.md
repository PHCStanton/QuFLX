SOCKET-IO Visual Data Streaming Development Plan

Purpose
- Stabilize and enhance the live data streaming and chart visualization pipeline (Socket.IO + React + Lightweight Charts) to meet TradingView-style real-time requirements, with automatic source sensing and strict asset isolation.

Status Legend
- [x] COMPLETE
- [~] IN PROGRESS
- [ ] INCOMPLETE

Phase 0 — Current Status Snapshot
- [x] End-to-end assessment completed (backend Socket.IO + REST, frontend useWebSocket + DataAnalysis + LightweightChart) against TradingView best practices.
- [x] Live tick ordering guard added in DataAnalysis: older tick timestamps update the last bar instead of appending a new one (prevents time violations).
- [x] Streaming server restarted and confirmed listening (Socket.IO at 0.0.0.0:3001).
- [x] Verified frontend chart rendering and live streaming works (e.g., AEDCNY_OTC) with no assertion errors once connections stabilize.
- [ ] Backend runtime logs analyzed and documented (pending deeper review).

Phase 1 — Connectivity and Data Integrity
Goal: Ensure reliable, strictly ordered real-time updates and minimize transport issues.
Steps:
1) Socket transport hardening
   - Prefer transport=["websocket"] (disable xhr-polling where feasible); align CORS and ports.
   - Acceptance: No recurring xhr-poll error; stable connection under normal network conditions.
   - Status: [ ]
2) Client-side throttling/batching (~10 fps)
   - Coalesce ticks and apply series.update in a scheduled loop; reduce race conditions and UI overhead.
   - Acceptance: Smooth chart updates; CPU usage reduced; no ordering hazards.
   - Status: [ ]
3) Strict time ordering on client (already added)
   - Guard: if incoming time < latest bar time, update last bar instead of append.
   - Acceptance: No time violation errors; chart remains consistent.
   - Status: [x]

Phase 2 — Automatic Source Sensing and Asset Isolation
Goal: Automatically switch between historical CSV and streaming; apply live ticks only for the focused asset.
Steps:
1) Auto source mode (auto/historical/streaming)
   - Auto selects streaming when WebSocket connected and stream_started for current asset; otherwise loads historical CSV.
   - Acceptance: Mode badge shows correct source; seamless switch without user dropdown.
   - Status: [ ]
2) Asset gate on client
   - Process tick_update only when payload.asset === current focused asset.
   - Acceptance: No cross-asset contamination; chart updates only relevant asset.
   - Status: [ ]
3) UI status indicator
   - Small badge or label: "Streaming" vs "Historical" with asset name.
   - Acceptance: Clear, live reflection of source state.
   - Status: [ ]

Phase 3 — REST Endpoint Stability and Fetch Resilience
Goal: Resolve intermittent 500/JSON parse errors; maintain UI responsiveness during backend startup or failures.
Steps:
1) Harden /api/available-csv-files
   - Always return valid JSON; robust error handling on filesystem operations; Windows-safe paths.
   - Acceptance: No "Unexpected end of JSON"; 500 errors replaced by meaningful JSON error responses.
   - Status: [ ]
2) REST retry/backoff + cached fallback
   - Exponential backoff for fetchCurrencyPairs; cache last successful list (localStorage) for fallback.
   - Acceptance: UI remains usable during backend hiccups; eventually recovers with live data.
   - Status: [ ]

Phase 4 — Timeframe Aggregation and Cache Reset
Goal: Align with TradingView resolution switching behavior.
Steps:
1) Timeframe selection (tick/1s/5s/1m)
   - Add timeframe state; user can change or auto-detect.
   - Status: [ ]
2) Bar builder
   - Bucket incoming ticks into current timeframe; update last bar or append new on boundary.
   - Acceptance: Clean OHLC bars per timeframe; no time violations.
   - Status: [ ]
3) Cache reset on timeframe change
   - Clear chart data, rebuild from historical, then resume live updates.
   - Acceptance: No conflicting data; chart remains consistent through resolution changes.
   - Status: [ ]

Phase 5 — Reconnection Lifecycle Management
Goal: Handle disconnects/reconnects gracefully with clear state and clean caches.
Steps:
1) Heartbeat/ping settings
   - Tune pingInterval/pingTimeout to detect dead connections quickly and reconnect.
   - Acceptance: Fast detection; predictable reconnection.
   - Status: [ ]
2) Cache reset on reconnect
   - Clear series and reload initial data upon reconnection to avoid mixed state.
   - Acceptance: Clean state after reconnect; chart integrity preserved.
   - Status: [ ]

Phase 6 — Backend Tick Format and Monotonicity (Per Asset)
Goal: Ensure server emits correct payloads with monotonically increasing timestamps for each asset.
Steps:
1) Verify emission format and rate
   - Confirm payload schema: { asset, timestamp_ms, price } and rate limits; document.
   - Acceptance: Agreed schema; consistent ticks; logs confirm.
   - Status: [ ]
2) Enforce per-asset monotonic ordering
   - Server-side checks or sequencing; optional buffering to reorder if needed.
   - Acceptance: No regressions; client ordering guard rarely triggered.
   - Status: [ ]

Phase 7 — Scaling and Security (Future)
Goal: Prepare for multi-node scale and production hardening.
Steps:
1) Socket.IO rooms per asset
   - Broadcast only to subscribers of asset-specific rooms.
   - Status: [ ]
2) Redis adapter (multi-node)
   - Support horizontal scaling and cross-process broadcasting.
   - Status: [ ]
3) TLS/WSS + tightened CORS + auth tokens
   - Secure external access; restrict origins; authenticate clients.
   - Status: [ ]

Test Plan (Acceptance Scenarios)
- [ ] Asset switch: Change focused asset; chart cache resets; historical preload loads; live stream resumes for new asset.
- [ ] Mode sensing: Stop/start streaming server; auto-switch between historical and streaming; status badge updates correctly.
- [ ] Timeframe change: Switch resolution; cache reset; bar builder outputs consistent OHLC; no time violations.
- [ ] High-frequency ticks: With throttling, chart remains smooth; ordering preserved; no assertion errors.
- [ ] Network interruptions: Simulate disconnect; reconnection with cache reset; UI remains responsive.

References
- TradingView Advanced Charts: Streaming Implementation and Datafeed API (cache reset, symbol/resolution matching, time violation rules)
- Lightweight Charts docs: series.update for real-time updates; strict ascending time requirements
- WebSocket best practices (AlgoCademy): persistent connections, event handling, reconnection/backoff, performance optimization, scaling, and security

Ownership & Next Steps
- Immediate focus: Phase 1 (transport, throttling), Phase 2 (auto sensing + asset gate), Phase 3 (REST hardening).
- Parallel: Phase 6 (backend schema verification), basic heartbeat settings from Phase 5.
- After stabilization: Implement Phase 4 (timeframe aggregation), then Phase 7 (scale/security) as needed.