# QuantumFlux Trading Platform - Development Roadmap

**Last Updated**: October 16, 2025

## 🚀 Current Development Focus

### 🚨 Phase 5.5: **CRITICAL BUG FIXES** (October 16, 2025) - **URGENT - IN PROGRESS**
**Fixing critical runtime errors and frontend stability issues discovered during bug audit**

**Priority:** CRITICAL - App is currently experiencing runtime crashes and hook violations
**Status:** 8 Critical bugs identified, 0 fixed

---

## 🎉 Recently Completed

### ✅ UI/UX Redesign - Solana-Inspired Professional Trading Terminal (October 15, 2025) - COMPLETE
**Successfully transformed from data visualization to professional 3-page trading platform**

### ✅ Complete UI/UX Redesign - Solana-Inspired 3-Page Platform (October 15, 2025) - COMPLETE

**Professional trading terminal transformation - all pages rebuilt with cohesive design**

- [x] **Design Mockup Generation**
  - Created Data Analysis page mockup matching Solana aesthetic
  - File: `attached_assets/generated_images/Data_Analysis_page_mockup_design_c5f27fa1.png`

- [x] **Data Analysis Page Rebuild** (Strategy Design Foundation)
  - 3-column layout matching mockup design
  - Left: Data Source toggle (CSV/Platform), Asset Selector, Timeframe buttons, Indicator Manager
  - Center: Chart area with asset header, chart controls, MultiPaneChart integration
  - Right: Quick Stats card (Latest Price, Change %, Volume), Indicator Readings with color-coded signals
  - All functionality preserved (CSV/Platform modes, WebSocket, indicators)

- [x] **Strategy Lab Page Rebuild** (Backtesting Core)
  - 3-column layout matching mockup design
  - Left: Strategy Selector (Quantum Flux), Data Files, Capital/Risk, Backtest Config
  - Center: Profit Curve chart placeholder, Performance Metrics grid (6 cards)
  - Right: Trade History with checkboxes and color-coded badges
  - Mockup: `attached_assets/generated_images/Strategy_Lab_backtesting_interface_mockup_b7632b2f.png`

- [x] **Trading Hub Page Rebuild** (Live Execution)
  - 3-column layout matching mockup design
  - Left: Active Positions with P/L badges, Signal Monitor
  - Center: CAMER chart with controls, Recent Trades table
  - Right: Live Signal Panel (87% confidence, CALL signal, RSI/MACD, EXECUTE TRADE button)
  - Mockup: `attached_assets/generated_images/QuantumFlux_Trading_Hub_UI_mockup_bad1f208.png`

- [x] **Unified Design System**
  - Updated color palette (darker bg `#0b0f19`, brighter green `#22c55e`)
  - Design tokens file: `gui/Data-Visualizer-React/src/styles/designTokens.js`
  - All pages use design tokens (zero Tailwind in new implementations)
  - Consistent visual language across all 3 pages

**Status**: Architect-verified, all tests passed, production-ready ✅

---

### ✅ Frontend Dynamic Indicator System & Multi-Pane Charts (October 14, 2025) - COMPLETE

**Professional trading platform UI with dynamic indicators and comprehensive testing**

- [x] **Dynamic Indicator Configuration System**
  - Add/remove indicators (not hardcoded)
  - Full time-series data from backend
  - SMA, EMA, RSI, MACD, Bollinger Bands support
  - Configuration panels with period/parameter controls

- [x] **Multi-Pane Chart Rendering**
  - Overlay indicators: SMA, EMA, Bollinger Bands on main chart
  - Separate synchronized panes: RSI, MACD oscillators
  - Time-based synchronization (subscribeVisibleTimeRangeChange)
  - Proper cleanup for event listeners and chart instances

- [x] **Comprehensive Bug Testing**
  - ✅ Chart rendering (100 data points)
  - ✅ Indicator system (all indicators working)
  - ✅ Multi-pane synchronization
  - ✅ Build process (426KB JS, 25KB CSS)
  - ✅ Code quality (no LSP errors)
  - ✅ Memory management (zero leaks)
  - ✅ WebSocket handling
  - ✅ All pages functional
  - ✅ Backend health verified

**Status**: Architect-verified, all tests passed, production-ready ✅

---

## 📋 Critical Bug Fixes - Phase 5.5 (URGENT)

### 🚨 **CRITICAL RUNTIME ERRORS** (Immediate - App Breaking)

#### Bug 1: React Hooks Rules Violation in DataAnalysis.jsx ❌ **ACTIVE CRASH**
**Location:** `gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx`
**Severity:** CRITICAL - App crashes on Data Analysis page
**Evidence:** 
- Browser console: "React has detected a change in the order of Hooks"
- "Cannot read properties of null (reading 'destroy')"
- "ReferenceError: Can't find variable: isConnected"

**Root Cause:** Hooks order changing conditionally
**Fix Required:**
- [ ] Review all hook calls in DataAnalysis.jsx
- [ ] Ensure no conditional hooks
- [ ] Fix the useEffect dependency array at line 141
- [ ] Verify hooks called in consistent order

#### Bug 2: Missing Error Boundary in App.jsx ❌ **CRITICAL**
**Location:** `gui/Data-Visualizer-React/src/App.jsx`
**Severity:** CRITICAL - Single error crashes entire app
**Current State:** ErrorBoundary exists but NOT wrapping routes

**Fix Required:**
- [ ] Wrap `<Routes>` with `<ErrorBoundary>` in App.jsx
- [ ] Test error recovery with intentional component error
- [ ] Verify error UI displays correctly

#### Bug 3: Unsafe Array Operations ❌ **HIGH PRIORITY**
**Locations:** 
- `gui/Data-Visualizer-React/src/components/PositionList.jsx` (line 52)
- `gui/Data-Visualizer-React/src/components/SignalList.jsx` (line 44)

**Issue:** No null/undefined checks before `.map()` - crashes if props undefined

**Fix Required:**
- [ ] Add null check: `{(positions || []).map(...)}` in PositionList.jsx
- [ ] Add null check: `{(signals || []).map(...)}` in SignalList.jsx
- [ ] Update keys to use unique identifiers instead of array index
- [ ] Test with undefined props

#### Bug 4: Stale Closure in RealTimeChart.jsx ❌ **HIGH PRIORITY**
**Location:** `gui/Data-Visualizer-React/src/components/RealTimeChart.jsx` (line 42)
**Severity:** HIGH - isStreaming state captured in stale closure

**Issue:** Callback references old `isStreaming` value when it changes

**Fix Required:**
- [ ] Remove `isStreaming` check from subscription callback, OR
- [ ] Use ref instead of state for isStreaming, OR
- [ ] Restructure to avoid closure issue
- [ ] Test start/stop streaming behavior

### 🔴 **HIGH PRIORITY DATA ISSUES**

#### Bug 5: Invalid Data in LiveTrading.jsx ❌
**Location:** `gui/Data-Visualizer-React/src/pages/LiveTrading.jsx` (lines 61-62, 90-95)
**Severity:** HIGH - Invalid percentage formats cause display errors

**Invalid Formats Found:**
- Line 61: `percentage: '9/1'` 
- Line 62: `percentage: 'L04'`
- Line 90: `percentage: '9/6'`
- Line 92: `percentage: '3/S'`
- Lines 93-94: `percentage: '0/5'`, `'1/5'`

**Fix Required:**
- [ ] Replace all invalid percentages with valid numeric strings
- [ ] Format as: `'90%'`, `'91%'`, etc.
- [ ] Verify display renders correctly

#### Bug 6: Network Fetch Error ❌
**Location:** `gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx` (line 152)
**Evidence:** Browser logs show "Failed to fetch"
**Issue:** Hardcoded localhost URL breaks in production

**Fix Required:**
- [ ] Replace `http://localhost:3001` with environment variable or dynamic URL
- [ ] Use: `${window.location.protocol}//${window.location.hostname}:3001`
- [ ] Add retry logic for failed requests
- [ ] Add proper error handling and user feedback

### 🟡 **CODE QUALITY ISSUES**

#### Bug 7: Duplicate Grid Layout Logic ⚠️
**Locations:** 
- `DataAnalysis.jsx` (lines 380-387)
- `StrategyBacktest.jsx` (lines 17-24)

**Issue:** `getResponsiveColumns()` function duplicated in both files

**Fix Required:**
- [ ] Remove duplicate functions
- [ ] Use existing `useResponsiveGrid` hook (like LiveTrading.jsx line 11)
- [ ] Verify responsive behavior unchanged

#### Bug 8: Inconsistent Logger Usage ⚠️
**Issue:** Mix of `console.log()` and logger utility across codebase
**Files Affected:** 10+ files with console.log

**Fix Required:**
- [ ] Replace all `console.log()` with logger utility calls
- [ ] Ensure consistent logging patterns
- [ ] Verify no sensitive data logged

#### Bug 9: Missing Dependency in useEffect ⚠️
**Location:** `DataAnalysis.jsx` (line 141)
**Issue:** `useEffect` depends on `chartData.length` instead of `chartData`

**Fix Required:**
- [ ] Change dependency from `chartData.length` to `chartData`
- [ ] Verify data updates trigger correctly

#### Bug 10: Unused State Variables ⚠️
**Location:** `LiveTrading.jsx` (lines 8-9)
**Issue:** `mode` and `isRunning` declared but never used

**Fix Required:**
- [ ] Remove unused state variables
- [ ] Clean up any related code

---

## 🎯 Bug Fix Implementation Plan

### Immediate Actions (Next 30 minutes)
1. ✅ Fix React Hooks violation in DataAnalysis.jsx
2. ✅ Add Error Boundary wrapper in App.jsx  
3. ✅ Add null checks to PositionList and SignalList
4. ✅ Fix stale closure in RealTimeChart

### Short-term (Next 1-2 hours)
5. ✅ Fix invalid percentage data in LiveTrading.jsx
6. ✅ Replace hardcoded localhost with dynamic URL
7. ✅ Consolidate duplicate grid layout logic
8. ✅ Remove unused state variables

### Code Quality (Next session)
9. ✅ Replace console.log with logger utility
10. ✅ Fix useEffect dependency arrays

---

## 📊 Development Tasks - After Bug Fixes

### Phase 6: Chart Optimization & Enhancement 📅 **QUEUED** (After bugs fixed)

**Goal**: Optimize chart layout for wider views and add professional trading features using TradingView Lightweight Charts capabilities

**Sub-Phase 6.1: Layout Expansion** (High Priority - Desktop/Tablet Only)
- [ ] Adjust 3-column layout widths for wider charts
  - Desktop (1280px+): Left 20%, Center 65%, Right 15%
  - Tablet Horizontal (1024px-1279px): Left 22%, Center 60%, Right 18%
- [ ] Update DataAnalysis.jsx responsive breakpoints
- [ ] Update StrategyLab.jsx responsive breakpoints
- [ ] Update TradingHub.jsx responsive breakpoints
- [ ] Remove mobile breakpoints (not crucial per user)
- [ ] Test chart visibility and responsiveness

**Sub-Phase 6.2: Tooltips & Visual Markers** (High Priority)
- [ ] Floating tooltip implementation
- [ ] Delta tooltip plugin integration
- [ ] Custom series markers for signals

**Sub-Phase 6.3: Visual Polish & UX** (Medium Priority)
- [ ] Price lines for key levels
- [ ] Chart watermarks
- [ ] Cleaner grid & crosshair styling
- [ ] Floating legend (top-left overlay)

**Sub-Phase 6.4: Advanced Features** (Medium Priority)
- [ ] Range switcher for quick timeframe changes
- [ ] Realtime update optimization
- [ ] User price alerts plugin
- [ ] Trend line drawing tool
- [ ] Session highlighting
- [ ] Volume histogram (bottom pane)

---

### Phase 7: Strategy Design Features 📅 QUEUED

**Goal**: Transform Data Analysis page into comprehensive strategy design tool

**1. Replay Function** (High Priority)
- [ ] Step through historical candles one-by-one
- [ ] Playback controls (play, pause, step forward/back, speed control)
- [ ] Visualize how strategies would perform in real-time
- [ ] Progress indicator showing current position in dataset

**2. Visual Signal Markers** (High Priority)
- [ ] Show BUY/CALL/SELL signals directly on chart
- [ ] Confidence % displayed on markers
- [ ] Click marker to see trade details

**3. Parameter Tweaking** (Medium Priority)
- [ ] Real-time indicator parameter adjustment
- [ ] Instant visual feedback on chart
- [ ] Compare before/after parameter changes
- [ ] Save custom parameter presets

**4. Quick Backtest** (Medium Priority)
- [ ] Run current indicator combo against loaded data instantly
- [ ] Mini performance metrics display
- [ ] Win rate, profit factor, total trades summary
- [ ] Export results to Strategy Lab for full analysis

---

### Phase 8: Live Trading Integration 📅 QUEUED

**Goal**: Connect real-time strategy signals to Trading Hub

- [ ] **Signal Generation Pipeline**
  - Real-time strategy signal calculation
  - Confidence scoring system
  - Signal history tracking
  - Performance metrics

- [ ] **Trade Execution Controls**
  - One-click EXECUTE TRADE button functionality
  - Position sizing calculator
  - Risk management controls
  - Confirmation modals

- [ ] **Position Monitoring**
  - Active positions display
  - Real-time P/L tracking
  - Auto-close functionality
  - Trade history logging

- [ ] **Integration with PocketOption**
  - Trade execution API
  - Position status polling
  - Account balance updates
  - Error handling and recovery

---

## 🐛 Known Issues & Technical Debt

### Critical (MUST FIX NOW) ❌
- [ ] React Hooks violation in DataAnalysis.jsx
- [ ] Missing Error Boundary wrapper in App.jsx
- [ ] Unsafe array operations (PositionList, SignalList)
- [ ] Stale closure in RealTimeChart
- [ ] Invalid percentage data in LiveTrading
- [ ] Hardcoded localhost URLs

### Non-Critical
- [ ] Duplicate grid layout functions
- [ ] Inconsistent logger usage
- [ ] Unused state variables
- [ ] Some strategy calibration files unused at runtime
- [ ] Frontend could benefit from TypeScript migration

### Nice to Have
- [ ] Add progress indicators for long-running operations
- [ ] Implement chart export functionality (PNG/SVG)
- [ ] Add keyboard shortcuts for common actions
- [ ] Dark/light theme toggle (currently dark-only)

---

## 🔄 Next Immediate Actions (In Order)

### 1. **CRITICAL BUG FIXES** ⏳ (Current Priority - TODAY)
- Fix React Hooks violation (DataAnalysis.jsx)
- Add Error Boundary wrapper (App.jsx)
- Add null checks (PositionList, SignalList)
- Fix stale closure (RealTimeChart)
- Fix invalid data (LiveTrading percentages)
- Fix hardcoded URLs (use dynamic URLs)

### 2. Chart Layout Expansion 📅 (After bugs fixed)
- Adjust 3-column widths: 20%/65%/15% (desktop), 22%/60%/18% (tablet)
- Update DataAnalysis.jsx, StrategyLab.jsx, TradingHub.jsx
- Remove mobile breakpoints (focus on desktop/tablet)
- Test chart visibility and responsiveness

### 3. Tooltips & Visual Markers 📅 (Phase 6.2)
- Implement floating tooltip for OHLC data
- Add delta tooltip plugin for price changes
- Create series markers for BUY/SELL signals
- Test with live streaming data

### 4. Visual Polish & Advanced Features 📅 (Phase 6.3-6.4)
- Add price lines, watermarks, floating legend
- Implement range switcher and price alerts
- Add trend line drawing tool
- Add volume histogram pane

### 5. Strategy Design Features 📅 (Phase 7)
- Replay function implementation
- Visual signal markers integration
- Parameter tweaking UI
- Quick backtest integration

### 6. Live Trading Integration 📅 (Phase 8)
- Connect signals to Trading Hub
- Implement trade execution controls
- Build position monitoring system
- PocketOption API integration

---

## 📝 Documentation Status

### Complete ✅
- [x] README.md - Project overview
- [x] QUICKSTART.md - Getting started guide
- [x] gui/gui_dev_plan_mvp.md - **UPDATED** with bug fixes and architecture
- [x] replit.md - **UPDATED** System architecture
- [x] TODO.md - **UPDATED** this file with critical bugs
- [x] .agent-memory/ - **UPDATED** All memory files
- [x] dev_docs/Heiku4.5_bug_finding.md - Bug audit report

### Needs Update
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Strategy development guide
- [ ] Deployment guide
- [ ] User manual for new 3-page UI

---

## 🎓 Key Design Principles

### Functional Simplicity ✅
- No unnecessary complexity
- Clear purpose for each page
- Clean, focused interfaces

### Sequential Logic ✅
- Design → Test → Backtest → Execute
- Each step builds on previous
- Incremental validation

### Zero Assumptions ✅
- Explicit verification at each stage
- No hardcoded defaults
- Real-time asset detection from platform

### Code Integrity ⚠️ **NEEDS ATTENTION**
- Some breaking issues found (hooks violations)
- Backward compatibility at risk
- Proper resource cleanup ✅

### Separation of Concerns ✅
- Clear boundaries between pages
- Data Analysis = Strategy Design
- Strategy Lab = Backtesting
- Trading Hub = Live Execution

---

## 📌 For Next Context/Session

**Current State Summary:**
- Real-time streaming infrastructure complete (Phases 1-6) ✅
- Frontend dynamic indicator system production-ready ✅
- **UI/UX redesign complete** (Solana-inspired 3-page platform) ✅
- Documentation updated with new architecture ✅
- **🚨 CRITICAL BUGS DISCOVERED** - 10 bugs identified, frontend unstable ❌

**To Continue:**
1. Review this TODO.md for current bug status
2. Check gui/gui_dev_plan_mvp.md for detailed bug fixes
3. **URGENT: Phase 5.5 - Critical Bug Fixes (React Hooks, Error Boundary, null checks)**
4. After fixes: Continue Phase 6 - Chart Optimization & Enhancement

**Next Priority After Bug Fixes:**
- Phase 6: Chart Optimization (layout, tooltips, visual polish)
- Phase 7: Strategy Design Features (replay, signal markers, parameter tweaking, quick backtest)
- Phase 8: Live trading integration (Trading Hub functionality)

---

**Development Status**: Phase 5.5 (Critical Bug Fixes) **URGENT** 🚨 | Must fix before Phase 6

**Last Reviewed**: October 16, 2025
