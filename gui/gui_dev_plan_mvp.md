# QuantumFlux GUI Development Plan - Trading Platform Redesign

**Last Updated**: October 15, 2025

## 🎯 Vision: Professional Trading Platform

A Solana-inspired, minimalist trading terminal focused on **backtesting, signal generation, and automated trading** on the Pocket Option platform.

### Core Philosophy
- **Functional Simplicity**: Clean, focused interfaces without bloat
- **Backtesting First**: Strategy validation is the primary workflow
- **Live Trading Ready**: Real-time signal generation and execution
- **Professional Aesthetic**: Dark theme with green accents, inspired by Solana-UI

---

## 📐 New Architecture: 3-Page System

### 1. **Chart Viewer** (Development/Testing Tab)
**Purpose**: Test chart functionalities and indicator rendering

- Real-time chart with lightweight-charts v4.2
- Data source toggle: CSV (historical) vs Platform (live WebSocket)
- Dynamic indicator testing with modal-based configuration
- **Role**: Development sandbox, not primary user interface

### 2. **Strategy Lab** (Core: Backtesting & Analysis)
**Purpose**: Strategy development, backtesting, and performance analysis

**Left Sidebar:**
- Strategy selector (Quantum Flux, Neural Beast, custom uploads)
- Data file picker (CSV historical data)
- Backtest configuration (capital, position size, risk params)
- Quick metrics cards (Total Trades, Win Rate, P/L, Sharpe)

**Center Panel:**
- Large equity curve chart (profit over time)
- Performance metrics grid with card-based layout
- Trade history table with expandable details

**Right Sidebar:**
- Strategy parameters editor
- Indicator configuration
- Export/save results

**Key Features:**
- Upload custom strategies (.py, .json)
- Compare multiple strategies side-by-side
- Monte Carlo simulation
- Walk-forward optimization
- Export reports (PDF, CSV)

### 3. **Trading Hub** (Core: Live Trading Execution)
**Purpose**: Real-time signal generation and trade execution

**Left Sidebar:**
- Active positions monitor
- Signal log with confidence scores
- P/L tracker (real-time)

**Center Panel:**
- Live candlestick chart with strategy signals
- Signal overlay badges (CALL/PUT with confidence %)
- Current asset display with timeframe

**Right Sidebar:**
- Live signal panel with:
  - Current signal (CALL/PUT/NEUTRAL)
  - Confidence score (0-100%)
  - Indicator metrics (RSI, MACD, etc.)
  - Execute trade button (prominent green)
- Risk management controls
- Position sizing calculator

**Key Features:**
- Real-time WebSocket streaming from Pocket Option
- Strategy signal generation on live candles
- One-click trade execution
- Position monitoring with auto-close
- Performance tracking (win rate, profit factor)

---

## 🎨 Design System: Solana-Inspired Aesthetic

### Color Palette
```css
/* Primary Backgrounds */
--bg-primary: #0a0e1a;           /* Deep space */
--bg-secondary: #141824;         /* Slightly lighter */
--card-bg: #1e293b;              /* Card background */
--card-border: #334155;          /* Subtle borders */

/* Accents */
--accent-green: #10b981;         /* Primary green (success, buy) */
--accent-red: #ef4444;           /* Primary red (danger, sell) */
--accent-blue: #3b82f6;          /* Info/highlight */
--accent-purple: #8b5cf6;        /* Secondary accent */

/* Text */
--text-primary: #f8fafc;         /* White text */
--text-secondary: #94a3b8;       /* Muted text */
--text-tertiary: #64748b;        /* Very muted */
```

### Typography
- **Headers**: Inter, 600 weight, tight tracking
- **Body**: Inter, 400 weight
- **Mono**: JetBrains Mono (for prices, metrics)

### Component Style
- **Cards**: Dark glass effect with subtle borders
- **Buttons**: Solid green (#10b981) with hover states
- **Inputs**: Dark background with green focus rings
- **Tables**: Minimal borders, alternating row highlights
- **Badges**: Pill-shaped with background opacity

---

## 🔧 Enhanced Indicator System

### Current Limitations
- Hardcoded indicators (single instance of SMA, EMA, etc.)
- No support for crossover strategies (need SMA-10 AND SMA-20)
- Limited indicator types

### New System: Modal-Based Configuration

**UI Flow:**
1. **Indicator Dropdown** → Select indicator type (SMA, EMA, RSI, etc.)
2. **Modal Opens** → Configure parameters:
   - SMA: Period (default: 20)
   - EMA: Period (default: 20)
   - RSI: Period (default: 14)
   - MACD: Fast (12), Slow (26), Signal (9)
   - Bollinger: Period (20), Std Dev (2)
   - **Schaff Trend Cycle**: Fast (10), Slow (20), %D(MACD) (3), %D(PF) (3)
   - **DeMarker**: Period (10)
   - **CCI**: Period (20)
3. **Add Multiple Instances** → User can add SMA-10, SMA-20, SMA-50 for crossovers
4. **Visual Management** → List of active indicators with edit/remove options

**Backend Support:**
- Dynamic indicator calculation based on user config
- Support for multiple instances of same indicator type
- Full time-series data for all indicators
- Efficient caching to prevent recalculation

**New Indicators to Add:**
1. **Schaff Trend Cycle** - Cycle-based trend indicator
   - Fast Length: 10
   - Slow Length: 20
   - %D(MACD) Length: 3
   - %D(PF) Length: 3

2. **DeMarker** - Price exhaustion indicator
   - Period: 10

3. **CCI (Commodity Channel Index)** - Momentum oscillator
   - Period: 20

---

## 📊 Technical Implementation

### Frontend Stack
- **React 18** with hooks
- **Vite** for fast dev builds
- **TailwindCSS** for styling
- **Lightweight Charts v4.2** for candlestick visualization
- **Socket.IO Client** for real-time data
- **React Router** for navigation

### Backend Stack
- **Flask-SocketIO** (port 3001) for GUI backend
- **RealtimeDataStreaming** capability for WebSocket interception
- **Quantum Flux Strategy** for signal generation
- **Technical Indicators** library for calculations

### Data Flow
```
PocketOption (Browser)
    ↓ (WebSocket via Chrome DevTools)
Chrome Port 9222
    ↓
RealtimeDataStreaming Capability
    ↓
streaming_server.py (Flask-SocketIO)
    ↓
Socket.IO Events → Frontend
    ↓
React Components (Chart Viewer, Strategy Lab, Trading Hub)
```

---

## 🚀 Development Phases

### Phase 1: Design System Foundation ✅ (Current)
- [x] Create design tokens file
- [x] Build core UI components (Card, Button, Badge, Input)
- [x] Setup Solana color palette
- [x] Typography and spacing system

### Phase 2: Enhanced Indicator System
- [ ] Backend: Add Schaff Trend Cycle calculation
- [ ] Backend: Add DeMarker indicator
- [ ] Backend: Add CCI indicator
- [ ] Frontend: Indicator dropdown component
- [ ] Frontend: Modal configuration UI
- [ ] Frontend: Multiple instance management
- [ ] Integration: Connect to backend calculation endpoints

### Phase 3: Chart Viewer Refinement
- [ ] Apply new design system to existing DataAnalysis page
- [ ] Rename to "Chart Viewer" (dev/test focus)
- [ ] Implement modal-based indicator configuration
- [ ] Clean up redundant code
- [ ] Focus on functionality testing only

### Phase 4: Strategy Lab (Backtesting Core)
- [ ] Design new StrategyBacktest page with 3-column layout
- [ ] Build strategy selector with upload capability
- [ ] Create equity curve chart component
- [ ] Build performance metrics dashboard
- [ ] Implement trade history table
- [ ] Add strategy comparison tools
- [ ] Integration testing with backend backtest engine

### Phase 5: Trading Hub (Live Execution)
- [ ] Design new LiveTrading page with signal-focused layout
- [ ] Build live signal panel with confidence display
- [ ] Create position monitor component
- [ ] Implement trade execution controls
- [ ] Add P/L tracker with real-time updates
- [ ] Risk management UI
- [ ] Integration with Pocket Option trade execution

### Phase 6: Testing & Refinement
- [ ] End-to-end testing of all workflows
- [ ] Performance optimization
- [ ] UI/UX polish
- [ ] Documentation updates
- [ ] Production deployment preparation

---

## 📋 Key Design Decisions

### 1. DataAnalysis → Chart Viewer
- **Purpose Shift**: From primary interface to dev/test sandbox
- **Focus**: Indicator testing and chart functionality validation
- **User Expectation**: Not the main trading interface

### 2. Strategy Lab as Core
- **Primary Workflow**: Strategy → Data → Backtest → Analyze → Refine
- **Goal**: Fast iteration on strategy development
- **Output**: Validated strategies ready for live trading

### 3. Trading Hub as Execution Layer
- **Primary Workflow**: Live Data → Strategy Signals → Execute → Monitor
- **Goal**: Real-time signal generation and trade execution
- **Safety**: Confirmation modals, risk controls, position limits

### 4. Indicator System Flexibility
- **Multiple Instances**: Essential for crossover strategies
- **Modal Configuration**: Cleaner UI, less clutter
- **Extensibility**: Easy to add new indicators

---

## 🎯 Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Backtest Execution Time | <5 seconds for 1000 candles | Pending |
| Signal Generation Latency | <100ms | Pending |
| UI Responsiveness | 60fps chart rendering | ✅ Achieved |
| Trade Execution Speed | <500ms click-to-API | Pending |
| Indicator Calculation | <50ms per indicator | Pending |
| Strategy Win Rate Display | Real-time accuracy | Pending |

---

## 📝 Next Immediate Steps

1. **Update Documentation** ✅ (This file)
2. **Create Design Tokens** → `src/styles/designTokens.js`
3. **Build Core Components** → `src/components/ui/`
4. **Implement Indicator Modal** → `src/components/indicators/IndicatorModal.jsx`
5. **Add Backend Indicators** → `strategies/technical_indicators.py`
6. **Rebuild Pages** → Chart Viewer, Strategy Lab, Trading Hub

---

**Development Status**: Design System → Component Library → Page Rebuild 🚀

**Last Reviewed**: October 15, 2025
