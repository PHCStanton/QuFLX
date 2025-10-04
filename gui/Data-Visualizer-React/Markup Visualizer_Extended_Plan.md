# Trading Data Visualizer — Extended Frontend Plan

This document lays out a client-ready UX/UI and frontend engineering plan to evolve the current app while preserving its aesthetic and codebase strengths. It references current components such as [src/components/TradingDashboard.jsx](src/components/TradingDashboard.jsx), [src/components/Header.jsx](src/components/Header.jsx), [src/components/Sidebar.jsx](src/components/Sidebar.jsx), and styles in [src/index.css](src/index.css). Core logic is centered in [JavaScript.TradingDashboard()](src/components/TradingDashboard.jsx:8), [JavaScript.loadTradingData()](src/components/TradingDashboard.jsx:46), [JavaScript.calculateIndicators()](src/components/TradingDashboard.jsx:62), [JavaScript.handleIndicatorToggle()](src/components/TradingDashboard.jsx:104), and [JavaScript.getProcessedDataWithIndicators()](src/components/TradingDashboard.jsx:112).

## Objectives (framed for prospective clientele)
- Clarify workflows: discovery → chart analysis → indicator tuning → backtest → export/report.
- Improve decision speed with better on-chart interactions and KPI visibility.
- Make the product brandable and accessible for B2B clients.
- Add collaboration-ready features (workspaces, exports, shareable context).
- Maintain smooth performance on large datasets.

## Design principles
- Progressive disclosure: default to the most actionable information, advanced details are one click away.
- Consistent hierarchy: global shell for navigation, local tabs for subsections.
- Semantic, accessible, and keyboard-first interactions.
- Motion as feedback, not decoration; honor reduced-motion preferences.
- Stable color semantics for price up/down and indicator families.

## IA and navigation
- Integrate a persistent shell:
  - Top bar for pair/timeframe, status, and primary actions using [src/components/Header.jsx](src/components/Header.jsx).
  - Left navigation for primary sections using [src/components/Sidebar.jsx](src/components/Sidebar.jsx).
- Keep section-level tabs within the content area (e.g., Price Chart, Indicators, Backtest) instead of mixing them with global navigation inside [JavaScript.TradingDashboard()](src/components/TradingDashboard.jsx:8).
- Mobile: collapsible sidebar and command palette for quick pair/indicator changes.

## High‑impact UX enhancements
1) KPI header strip
- Add compact metrics above the chart: Last Price, Day Change, 24h High/Low, Volume.
- Promote the existing Market Info (currently in the right card) to a KPI row; keep extended stats in a side card.

2) Indicator chips and configuration drawer
- Inline toggle chips with color swatches for SMA, EMA, RSI, MACD (no context switch).
- Right-side drawer for parameter tuning (SMA N, EMA N, RSI period, MACD fast/slow/signal).
- Save presets per user/client, applied across sessions.

3) Chart usability upgrades
- Crosshair with synchronized tooltips for all active series at the hovered timestamp.
- Zoom and range presets: 1D, 1W, 1M, 3M, YTD, MAX.
- Timeframe switcher aligned with data availability (e.g., /HLOC/1m, /5m).

4) Backtesting workflow clarity
- Structure Backtest into: Strategy, Parameters, Results.
- Overlay trade markers (buy/sell) on the main chart.
- Results include equity curve, drawdown, Sharpe, win rate, max DD; provide CSV export and one-click PDF.

5) States: empty, loading, error
- Empty-state onboarding for first run: guide to choose a pair.
- Skeleton loaders for chart and KPI cards (reuse animation styles from [src/index.css](src/index.css)).
- Error toast and retry path when CSV fetch fails inside [JavaScript.loadTradingData()](src/components/TradingDashboard.jsx:46).

6) Theming and white‑labeling
- Theme tokens via Tailwind and CSS custom properties.
- Brand presets (Blue, Emerald, Indigo) and light/dark toggle.
- Tenant-level overrides from [template_config.json](template_config.json).

7) Accessibility (WCAG AA)
- Proper roles/aria-attributes for tabs, drawers, toggles; aria-live for tab content changes.
- Keyboard navigation and focus management; modals use focus traps.
- High-contrast palette option; ensure link/label contrast on glass surfaces.

8) Internationalization and locale
- Number/date formatting per locale; currency formatting on metrics.
- Externalize UI strings for translation.

## Architecture and component plan
Extract monolithic elements from [JavaScript.TradingDashboard()](src/components/TradingDashboard.jsx:8) into focused components:
- KPIStatsRow: shows 3–5 KPIs with sparkline optional.
- ChartToolbar: timeframe presets, zoom controls, export buttons.
- IndicatorChips: inline toggles for indicators with color swatch.
- IndicatorDrawer: parameter form and preset management.
- MarketInfoCard: contains extended stats currently rendered in the right column.
- TabsBar: secondary navigation for Price Chart, Indicators, Backtest.
- BacktestPanels: StrategyPanel, ParametersPanel, ResultsPanel (equity curve and summary).
- PairSelector: enhanced selector with search and recent history.

State and data flow
- Persist user context (pair, timeframe, activeIndicators, activeTab) in localStorage.
- Memoize indicator computations from [JavaScript.calculateIndicators()](src/components/TradingDashboard.jsx:62) with useMemo keyed by data and params.
- Debounce recalculation during rapid toggles.
- Consider TanStack Query for fetch caching/retries around CSV requests in [JavaScript.loadTradingData()](src/components/TradingDashboard.jsx:46).
- For large files, offload parsing and indicator math to a Web Worker.

Performance plan
- Avoid O(n×m) recomputations; compute once, cache keyed by (pair, timeframe, params).
- Stream CSV parsing (e.g., Papa Parse) to progressively render.
- Virtualize long lists if introduced (e.g., trade tables).

Theming approach
- Define CSS variables for primary/secondary/positive/negative and glass elevations; map Tailwind config to these tokens.
- Load brand overrides from [template_config.json](template_config.json) at app start; persist selection.

Accessibility checklist
- Tabs: role="tablist", role="tab", aria-selected, aria-controls; arrow-key navigation.
- Drawers/modals: aria-modal, labelledby/ describedby; focus trap and ESC to close.
- Toggle chips: role="switch" or "checkbox", visible focus outlines.
- Announce data loading completion via aria-live="polite".

## Implementation phases and deliverables
Phase 1 — Quick wins (1–2 days)
- Add KPIStatsRow above chart using existing market metrics.
- Inline IndicatorChips with toggles; persist activeIndicators.
- Replace spinner with skeleton loaders and add an empty state.
- Persist selectedPair and activeTab in localStorage.
Acceptance criteria
- Users can toggle indicators without leaving the chart.
- On reload, the app restores last pair, tab, and indicators.
- Loading states use skeletons; empty state guides first-time users.

Phase 2 — Short term (1 week)
- Timeframe switcher and range presets in ChartToolbar.
- Crosshair + synchronized tooltips; on-chart legend.
- IndicatorDrawer with parameter forms and saveable presets.
Acceptance criteria
- Cursor hover shows synchronized values for price and each active indicator.
- Drawer updates indicator math and persists presets; no full-screen navigation needed.

Phase 3 — Medium term (1–2 weeks)
- Backtest UX split into Strategy/Parameters/Results panels.
- Equity curve and drawdown charts; buy/sell markers on main chart.
- Export PNG/CSV; basic PDF report generator.
Acceptance criteria
- Running a backtest yields an equity curve and summary stats; users can export artifacts.

Phase 4 — Client-ready (2–3 weeks)
- Workspaces: save/share layout + presets as links.
- White-label theming and brand presets; light/dark toggle.
- A11y pass for WCAG AA; keyboard coverage and aria semantics.
- Optional workerization of parsing/indicators; adopt TanStack Query for robustness.
Acceptance criteria
- Workspace links reliably hydrate state; theme can be swapped per-tenant without code changes.

## File-by-file change map
- [src/components/TradingDashboard.jsx](src/components/TradingDashboard.jsx)
  - Slim down by delegating tabs, chips, drawers, KPI row, and toolbar to child components.
  - Wrap indicator computation with useMemo; persist user state.
- [src/components/Header.jsx](src/components/Header.jsx)
  - Promote to global top bar; host PairSelector, timeframe, actions (Export, Share).
- [src/components/Sidebar.jsx](src/components/Sidebar.jsx)
  - Use for primary navigation; collapse on small screens.
- New components
  - [src/components/KPIStatsRow.jsx](src/components/KPIStatsRow.jsx)
  - [src/components/ChartToolbar.jsx](src/components/ChartToolbar.jsx)
  - [src/components/IndicatorChips.jsx](src/components/IndicatorChips.jsx)
  - [src/components/IndicatorDrawer.jsx](src/components/IndicatorDrawer.jsx)
  - [src/components/backtest/StrategyPanel.jsx](src/components/backtest/StrategyPanel.jsx)
  - [src/components/backtest/ParametersPanel.jsx](src/components/backtest/ParametersPanel.jsx)
  - [src/components/backtest/ResultsPanel.jsx](src/components/backtest/ResultsPanel.jsx)
  - [src/components/PairSelector.jsx](src/components/PairSelector.jsx)
- [src/index.css](src/index.css)
  - Add CSS variables for theme tokens; define skeleton classes; ensure reduced-motion support.
- [template_config.json](template_config.json)
  - Add brand presets and defaults; load at app start.

## Data contracts and types
tradingData item (current usage)
- { timestamp: number | string, open: number, high: number, low: number, close: number, volume?: number }
indicators (processed)
- { sma?: Record<timestamp, number>, ema?: Record<timestamp, number>, rsi?: Record<timestamp, number>, macd?: Record<timestamp, { macd: number, signal: number, histogram: number }> }
Persisted UI state
- { pairId: string, timeframe: '1m'|'5m'|'1h'|'1D', indicators: string[], activeTab: 'chart'|'indicators'|'backtest', indicatorParams: { sma?: { n: number }, ema?: { n: number }, rsi?: { period: number }, macd?: { fast: number, slow: number, signal: number } } }

## Risks and mitigations
- Large CSVs stall main thread → Move parse + indicators to Web Worker; progressive rendering.
- Over-cluttered chart controls → Consolidate into ChartToolbar and chips; hide advanced options in drawer.
- Brand overrides reduce contrast → Include automated contrast checks and a high-contrast theme.
- State drift across tabs → Centralize persisted state and clear ownership of computations.

## Analytics and telemetry (privacy-respecting)
- Track feature usage: timeframe changes, indicator toggles, backtest runs.
- Track performance: parse time, indicator compute time, render time.
- Error tracking for CSV fetch/parse and indicator math.

## QA plan
- Manual scenarios: first-run empty state; pair change; indicator toggle; timeframe switch; backtest flow; export flows; error retry.
- Cross-browser: Chrome, Edge, Firefox; reduced-motion and high-contrast modes.
- Accessibility: keyboard tab order, focus outline visibility, screen reader labels.

## Deliverables
- Implemented components and screens per phases, theming tokens, and persisted state.
- Export artifacts (PNG/CSV/PDF), shareable workspace links, and documentation.

## Out of scope (initially)
- Live market data ingestion beyond current CSVs.
- Strategy DSL or code-based strategy authoring.

## Reference to current key functions
- [JavaScript.TradingDashboard()](src/components/TradingDashboard.jsx:8) — main container and view logic.
- [JavaScript.loadTradingData()](src/components/TradingDashboard.jsx:46) — data ingestion from CSV.
- [JavaScript.calculateIndicators()](src/components/TradingDashboard.jsx:62) — transforms data into indicator maps.
- [JavaScript.handleIndicatorToggle()](src/components/TradingDashboard.jsx:104) — toggles active indicator set.
- [JavaScript.getProcessedDataWithIndicators()](src/components/TradingDashboard.jsx:112) — materializes series for panels.

## Appendix: visual consistency notes
- Keep glassmorphism but reduce blur on dense screens for readability.
- Limit elevation levels; ensure consistent shadows.
- Assign stable colors to indicators; reflect in legend, chips, and exports.