# Trading Dashboard MVP - TODO

## Overview
Streamlined proof-of-concept focused on core trading visualization functionality. Build on existing TradingDashboard.jsx foundation.

## Phase 1: Core Function (3-5 days)

### 1.1 KPI Display
- [ ] Create `KPIStatsRow.jsx` component
- [ ] Display: Last Price, Day Change (%), Volume, High/Low
- [ ] Position above chart in TradingDashboard
- [ ] Use existing market data, simple text formatting

### 1.2 Indicator Controls
- [ ] Replace complex indicator UI with simple checkboxes
- [ ] Create inline toggle row: ☐ SMA ☐ EMA ☐ RSI ☐ MACD
- [ ] Keep existing `calculateIndicators()` function
- [ ] Persist active indicators in localStorage

### 1.3 Chart Enhancements
- [ ] Add crosshair with price tooltip on hover
- [ ] Show values for active indicators at cursor position
- [ ] Keep existing chart library and styling

### 1.4 Data Loading
- [ ] Add loading spinner during CSV fetch
- [ ] Simple error message if data load fails
- [ ] Keep existing `loadTradingData()` function

## Phase 2: Basic UX (3-5 days)

### 2.1 Timeframe Controls
- [ ] Add simple button group: [1D] [1W] [1M] [3M]
- [ ] Connect to existing data loading logic
- [ ] Persist selected timeframe in localStorage

### 2.2 Indicator Parameters
- [ ] Add inline number inputs next to checkboxes
- [ ] SMA Period: [ 20 ], EMA Period: [ 12 ], RSI Period: [ 14 ]
- [ ] MACD: Fast [ 12 ] Slow [ 26 ] Signal [ 9 ]
- [ ] Update calculations when changed

### 2.3 Pair Selection
- [ ] Simple dropdown for currency pairs
- [ ] Default options: EURUSD, GBPUSD, USDJPY, AUDUSD
- [ ] Connect to data loading

### 2.4 Export Function
- [ ] Add "Export CSV" button
- [ ] Download current chart data with indicators
- [ ] Simple filename: `trading_data_EURUSD_1D.csv`

## Technical Guidelines

### File Structure
```
src/components/
├── TradingDashboard.jsx (main - modify existing)
├── KPIStatsRow.jsx (new)
└── IndicatorControls.jsx (new)
```

### State Management
- Use basic React useState hooks
- Persist in localStorage: `selectedPair`, `activeIndicators`, `timeframe`
- No complex state management libraries

### Styling
- Keep existing glassmorphism styles from index.css
- Use existing Tailwind classes
- No theming system - stick with current colors

### Performance
- Use existing useMemo for indicator calculations
- No Web Workers or complex optimizations
- Focus on functional correctness first

## What NOT to Build (MVP Scope)

### Skip These Features
- ❌ Drawer/modal components
- ❌ White-labeling/theming system
- ❌ Complex navigation (sidebar/header changes)
- ❌ PDF exports or reporting
- ❌ Workspace/collaboration features
- ❌ Internationalization
- ❌ Advanced accessibility features
- ❌ Analytics/telemetry
- ❌ Complex backtesting workflow

### Keep Simple
- Single screen layout
- Inline controls only
- Basic loading states
- Simple error handling
- Minimal component extraction

## Acceptance Criteria

### Phase 1 Complete When:
- [ ] KPIs display above chart
- [ ] Indicators can be toggled on/off with checkboxes
- [ ] Chart shows crosshair with price values
- [ ] Settings persist on page reload

### Phase 2 Complete When:
- [ ] Timeframe buttons change data view
- [ ] Indicator parameters can be adjusted
- [ ] Different pairs can be selected
- [ ] Data can be exported to CSV

## Development Notes

### Existing Code to Preserve
- `loadTradingData()` function at line 46
- `calculateIndicators()` function at line 62  
- `handleIndicatorToggle()` function at line 104
- Current chart rendering logic
- Existing CSS styles

### Quick Wins
- Reuse existing indicator calculation logic
- Build on current component structure
- Leverage existing data flow patterns
- Keep current visual design intact

## Success Metrics
- Functional trading dashboard with basic controls
- Clean, simple user interface
- Data persists across sessions
- 1-2 week development timeline
- Foundation for future enhancements