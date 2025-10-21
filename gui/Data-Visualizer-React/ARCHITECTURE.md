# QuantumFlux GUI Architecture

## Core Architecture Principles

### 1. Separation of Concerns
- **Data Management**: Centralized in specialized hooks
- **UI Components**: Focus purely on rendering
- **Business Logic**: Isolated in dedicated modules
- **State Management**: Distributed through focused hooks

### 2. Data Flow Architecture
```
Backend (streaming_server.py)
         ↓
WebSocket Connection (useWebSocket)
         ↓
Data Processing Layer
 ├─ Candle Management (useDataStream)
 ├─ Indicator Pipeline (useIndicators)
 └─ CSV Data Handling (useCsvData)
         ↓
UI Components
```

## Key Components

### 1. WebSocket Management
- **useWebSocketV2**: Centralized WebSocket management with improved state handling
  - Connection state management
  - Stream control
  - Data processing
  - Indicator calculations
  - Memoized state objects for performance

### 2. Indicator Pipeline
- **Backend-Driven Calculation**: All indicator calculations performed on backend
- **Generic Indicator Format**: Standardized structure for all indicator types
- **Multi-Instance Support**: Multiple instances of same indicator type
- **Error Handling**: Comprehensive error management and recovery

### 3. Data Management
- **Optimized Buffer Management**: 
  - Map-based storage for O(1) updates
  - Efficient sorting with maintained order
  - Automatic size limiting
  - Memory leak prevention

### 4. State Management
- **Live Mode State**: Managed through useLiveMode hook
- **CSV Data State**: Handled by useCsvData hook
- **Indicator State**: Controlled by useIndicators hook
- **Clear State Boundaries**: Each hook manages its own isolated state

## Performance Optimizations

### 1. Data Processing
- O(1) candle updates using Map data structure
- Maintained sorted order for efficient data insertion
- Batched updates for better performance
- Proper cleanup of timers and event listeners

### 2. State Updates
- Memoized state objects to prevent unnecessary re-renders
- Focused state updates to minimize render impact
- Efficient data structure usage

### 3. Memory Management
- Automatic buffer size limiting
- Proper cleanup of resources
- Event listener management
- Timer cleanup

## Testing Strategy

### 1. Unit Tests
- Individual hook testing
- Component isolation testing
- Mock data validation

### 2. Integration Tests
- Full indicator pipeline testing
- WebSocket communication testing
- Error handling validation
- State consistency verification

## Future Enhancement Paths

### 1. Indicator System
- Support for custom indicators
- Advanced indicator combinations
- Visual indicator configuration
- Indicator performance metrics

### 2. Performance
- WebWorker support for heavy calculations
- Virtual scrolling for large datasets
- Lazy loading of historical data
- Optimized chart rendering

### 3. Features
- Advanced charting tools
- Strategy backtesting integration
- Real-time alerts
- Custom indicator development

## Code Organization

```
src/
├── hooks/
│   ├── useWebSocketV2.js     # WebSocket management
│   ├── useIndicators.js      # Indicator management
│   ├── useLiveMode.js        # Live mode state
│   ├── useCsvData.js         # CSV data handling
│   └── useDataStream.js      # Data streaming
├── components/
│   ├── DataAnalysis.jsx      # Main analysis page
│   ├── ChartContainer.jsx    # Chart rendering
│   └── IndicatorPanel.jsx    # Indicator controls
└── utils/
    ├── indicatorUtils.js     # Indicator helpers
    └── dataProcessing.js     # Data processing
```

## Best Practices

1. **State Management**
   - Use focused hooks for specific concerns
   - Maintain clear state boundaries
   - Implement proper cleanup

2. **Performance**
   - Memoize expensive calculations
   - Batch updates when possible
   - Use efficient data structures

3. **Error Handling**
   - Implement comprehensive error boundaries
   - Provide meaningful error messages
   - Enable graceful degradation

4. **Testing**
   - Maintain high test coverage
   - Use meaningful test cases
   - Test error scenarios

## Architectural Decisions

1. **Backend-Driven Indicators**
   - Reason: Consistency and performance
   - Impact: Reduced frontend complexity
   - Trade-offs: Higher backend load

2. **Modular Hook Structure**
   - Reason: Better maintainability
   - Impact: Clearer code organization
   - Trade-offs: More files to manage

3. **Map-Based Data Storage**
   - Reason: Performance optimization
   - Impact: Faster updates and lookups
   - Trade-offs: Slightly higher memory usage
## Tab Architecture & Separation of Concerns

This section documents the current tab-level architecture and clarifies feature boundaries to maintain a clean separation of concerns and a consistent workflow.

- DataAnalysis ("Analysis" tab)
  - Purpose: Data sourcing, stream control, asset detection, indicator configuration.
  - Ownership: All control surfaces (Detect Asset, Start/Stop Streaming, Add Indicators).
  - Output: Produces the unified application stream state for other tabs to consume.
- LiveTrading ("Live" tab)
  - Purpose: Live monitoring and execution context; read-only visualization of the live stream.
  - Ownership: No control surfaces for stream or indicator setup; focuses on status, chart, signals.
  - Output: Presents the stream produced by Analysis with minimal latency and distraction.
- Backtest (if enabled)
  - Purpose: Strategy backtesting and visualization with historical data.
  - Ownership: Backtest configuration and result rendering; no live control.

UX Guidance
- Controls live exclusively in Analysis; LiveTrading shows status and results.
- Explicit navigation: Live includes a link back to Analysis; Analysis includes a link to open Live when streaming.
- Binary options strategy design is supported by a focused Analysis workflow and a clean Live execution context.

## DataAnalysis – Core Responsibilities and Features

Primary Responsibilities
- Data source selection (CSV vs Platform)
- Asset selection and timeframe control
- Live stream orchestration (detect asset, start/stop)
- Indicator management (ADD INDICATORS)
- Chart rendering via ChartContainer + MultiPaneChart

Feature Implementations
- Detect Asset: actions.stream.detectAsset()
- Start/Stop Streaming: actions.stream.start(asset), actions.stream.stop()
- Indicator Pipeline: useIndicators manages activeIndicators and forwards calculateIndicators to backend
- CSV Integration: useCsvData manages offline datasets; storeCSV action passes candles to backend
- Status Surface: WS connected, Chrome connection, Stream active, current asset

Integration
- useWebSocketV2 provides a single source of truth: { connection, stream, asset, data, actions }
- ChartContainer renders main chart and forwards backendIndicators into MultiPaneChart
- MultiPaneChart interprets overlays vs oscillators, renders RSI/MACD panes, and generic oscillators.
- Analysis links to Live when streamActive to reinforce workflow continuity.

Sizing and Layout
- Explicit chart height for Analysis (600px) ensures deterministic layouts and predictable pane splits.
- Pane heights are computed (MultiPane) with explicit rules; no implicit assumptions.

## LiveTrading – Responsibilities and Behaviors

Primary Responsibilities
- Present the live stream produced in Analysis without duplicating controls.
- Offer a compact status surface and focused visualization for trade decisions.
- Provide navigation back to Analysis for any configuration or control changes.

Current Behavior
- LiveTrading renders read-only chart and informational banner clarifying that controls live in Analysis.
- Socket connection follows the same useWebSocketV2 state, consuming stream status and data.

Why the Separation Matters
- Prevents fragmented control state across tabs.
- Reduces cognitive load during live trading (no accidental restarts or reconfigurations).
- Simplifies testing: Analysis exercises control paths; Live validates consumption/latency.

Future Extensions
- Execution widgets (order ticket, risk panel) belong in Live but should consume the stream and signals without altering source configuration.
- Strategy feedback (alerts, binary decision cues) render as non-intrusive overlays/tiles.

## Integration Points

State and Actions (useWebSocketV2)
- connection: websocket connectivity (vite proxy, backend)
- stream: lifecycle (ready, active), start/stop, live mode
- asset: detectedAsset, streamAsset, selectedAsset
- data: candle and indicator payloads
- actions: detectAsset, start(asset), stop(), storeCSV(candles), calculateIndicators(config)

UI Components
- DataSourceSelector → AssetSelector → PlatformModeControls → TimeframeSelector
- ChartContainer → MultiPaneChart
- IndicatorPanel → add/remove indicators, config propagation
- StatsPanel → latest price, change, volume, indicator readings

Backend
- streaming_server.py hosts Socket.IO/WebSocket capture and indicator adapter
- IndicatorAdapter computes backend indicators and streams results

Testing and Observability
- Live logs show client connects/disconnects, state resets, indicator compute events
- Frontend logs may show vite ws proxy errors during reconnects; typically benign

## Functional Capabilities and Recommendations

Current Capabilities
- Live stream from platform with Chrome WebSocket capture
- Asset detection and stream control in Analysis
- CSV offline analysis and backend CSV storage
- Indicator rendering with overlays and oscillator panes (RSI, MACD, generic oscillators)
- Status surfaces across Analysis and LiveTrading

Recommendations (Prioritized)
1) Optimize tab functionality
   - Keep controls only in Analysis; refine Live to focus on execution and signal review.
   - Show explicit WS/Chrome/Stream/Asset status on both tabs; link between tabs contextually.
2) Enhance user experience
   - Maintain deterministic chart heights; add pane height presets per timeframe.
   - Improve IndicatorPanel with presets for momentum (Schaff TC, DeMarker, CCI) and visibility toggles.
   - When streamActive, surface "Open Live Tab" in Analysis; in Live, surface "Go to Analysis".
3) Improve workflow efficiency
   - Persist last-used indicator set per asset and timeframe.
   - Cache recent streams and enable quick reattach from Live.
   - Add minimal latency mode for Live (skip non-essential UI rerenders).

Core Development Principles applied
- Functional Simplicity: Focused controls and lean Live view
- Sequential Logic: Analysis → configure → start → hand-off → Live → monitor/execute
- Zero Assumptions: Explicit sizes, status surfaces, and pane allocations
- Code Integrity: Backward compatible by extending existing hooks/components
- Clear Separation of Concerns: Distinct tab responsibilities and navigation cues
