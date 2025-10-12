# TradingView Lightweight Charts - Strategy Testing Guide

A comprehensive guide for implementing strategy testing and signal generation with Lightweight Charts.

---

## What You Can Achieve

### Performance and Footprint
- **Extremely small bundle size** (~35 KB) with fast HTML5 canvas rendering
- Ideal for real-time/streaming dashboards and low-latency UIs
- Handles **tens of thousands of data points** smoothly with proper update throttling

### Core Chart Types (Series)
- **Candlestick & Bar** - OHLC data visualization
- **Line, Area, Baseline** - Trend and relative comparisons
- **Histogram** - Volume and indicator visualization
- **Baseline series** - Perfect for equity curves and relative performance
- Multiple series per pane with independent price scale behavior

### Multi-Pane Support (v5+)
- Stack panes vertically (price, volume, indicators)
- Separate price scales per pane
- Overlay price scales for independent scaling of overlaid series

### Scales and Layout
- **Price scales**: Left/right positioning, overlay options
- **Autoscale control**: Custom `autoscaleInfoProvider` for margins and range tweaking
- **Time scale**: `fitContent`, visible range shifting, whitespace handling
- **Lazy-loading**: Via visible logical range callbacks
- Grid lines, watermarks, customizable background and text colors

### Interaction Features
- **Crosshair**: Configurable lines and labels with move event subscriptions
- **Markers**: Event visualization (buy/sell signals, anomalies)
- **Programmatic control**: Visible range, auto-scale toggle, tick formatting
- Edge tick mark visibility control

### Streaming Updates
- Append bars via `series.update()`
- `shiftVisibleRangeOnNewBar` behavior for live data tracking
- Subscribe to visible range changes for on-demand data loading

### Extensibility
- Custom series rendering (advanced)
- Primitive plugins (up/down markers for area/line series)

---

## UI/UX Layout Patterns for Strategy Testing

### Multi-Pane Layout
```
┌─────────────────────────────────────┐
│ Pane 1: Price (Candlestick)        │
│ + Signal markers (buy/sell arrows)  │
│ + SL/TP horizontal lines            │
├─────────────────────────────────────┤
│ Pane 2: Volume (Histogram)          │
├─────────────────────────────────────┤
│ Pane 3+: Indicators                 │
│ (MACD, RSI, custom indicators)      │
└─────────────────────────────────────┘
```

### Inspectable Readouts
- **Crosshair-driven tooltip**: OHLC + indicator values at cursor
- **Legend row**: Updates on crosshair move with all series values
- Keep DOM overlays lightweight and cursor-pinned

### Backtest Visualization
- **Equity curve pane**: Area or Baseline series for cumulative PnL
- **Trade markers**: Entries, exits, stops, profit targets
- **Event markers**: Time-based markers for strategy events
- Vertical lines via thin dedicated series or custom overlays

### Strategy Debugging Controls
- **Timeframe dropdown** and asset selector (external UI)
- **Toggle switches** for overlays/indicators
- **"Go to live" button**: Scrolls to latest bar, enables shift-on-new-bar
- Per-indicator visibility controls

### Data Loading & Performance
```javascript
// Lazy-load on scroll
chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
  const info = series.barsInLogicalRange(range);
  if (info && info.barsBefore < 50) {
    // Fetch and prepend older bars
  }
});
```
- Use `autoscaleInfoProvider` for visual margins
- Batch updates and throttle streaming (60-120ms intervals)
- Avoid constant full re-draws

### Visual Clarity Tips
- Distinct colors and marker shapes for signal types
- Enable edge tick marks on critical scales
- Use overlay price scales for series with different magnitudes
- Color-coded levels (SL/TP) with state-based styling

---

## Limitations to Plan Around

### Not a Full Platform
- ❌ No built-in indicators or Pine Script
- ❌ No drawing tools (trendlines, Fibonacci, etc.)
- ✅ Compute indicators externally, render primitives
- ✅ Build custom controls around the canvas

### Minimal Annotation Primitives
- ✅ Horizontal price lines and time-based markers supported
- ⚠️ Vertical lines and arbitrary shapes require custom overlays

### Simple Multi-Pane
- ✅ Vertical pane stacking
- ❌ Complex grids or advanced pane interactions not built-in

### Accessibility & Export
- ⚠️ Canvas-based rendering limits native accessibility
- ⚠️ No built-in screenshot/export (requires custom solution)

### Data Handling Expectations
- **Required**: Time-indexed, ordered data
- **Your responsibility**: Handle gaps with whitespace points
- **Your responsibility**: Timeframe aggregation/resampling

---

## Applying Features to Strategy Testing

### Real-Time Strategy View
```javascript
// Feed live bars
candlestickSeries.update({ time, open, high, low, close });

// Overlay signals
series.setMarkers([
  { time, position: 'belowBar', shape: 'arrowUp', color: 'green' },
  { time, position: 'aboveBar', shape: 'arrowDown', color: 'red' }
]);

// Draw SL/TP levels as price lines
series.createPriceLine({
  price: stopLoss,
  color: 'red',
  lineWidth: 2,
  lineStyle: 2 // dashed
});
```

### Indicator Panes
```javascript
// Compute indicators externally
const rsiSeries = chart.addLineSeries({
  color: 'purple',
  autoscaleInfoProvider: () => ({
    priceRange: { minValue: 0, maxValue: 100 },
    margins: { above: 10, below: 10 }
  })
});
rsiSeries.setData(rsiData);
```

### Backtesting Explorer
```javascript
// Equity curve
const equitySeries = chart.addBaselineSeries({
  baseValue: { type: 'price', price: 0 },
  topLineColor: 'green',
  bottomLineColor: 'red'
});

// Load initial window + lazy-load on scroll
chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
  // Fetch older history when user scrolls back
});
```

### Signal Verification & Debugging
```javascript
// Crosshair tooltip with indicator values
chart.subscribeCrosshairMove(param => {
  if (param.time) {
    const price = param.seriesData.get(candlestickSeries);
    const rsi = param.seriesData.get(rsiSeries);
    // Update tooltip DOM with price and rsi values
  }
});
```

### Multi-Asset/Relative Views
```javascript
// Compare assets with overlay scales
const asset1 = chart.addLineSeries({ priceScaleId: 'left' });
const asset2 = chart.addLineSeries({ priceScaleId: 'right' });

// Baseline for percentage change
const relativePerf = chart.addBaselineSeries({
  baseValue: { type: 'price', price: 100 }
});
```

### Streaming Pipeline Tips
- Maintain rolling buffer per series
- Use `series.update()` for new bars (not full data reset)
- Set `timeScale.shiftVisibleRangeOnNewBar` only when user is "live"
- Turn off shift when user scrolls back in history
- Use `ignoreWhitespaceIndices` to clean grid/crosshair behavior

---

## Minimal Integration Example

```javascript
// Create chart
const chart = createChart(container, {
  layout: {
    background: { type: 'solid', color: '#1e1e1e' },
    textColor: '#d1d4dc'
  },
  timeScale: {
    shiftVisibleRangeOnNewBar: true
  }
});

// Price pane (candlestick)
const candlestickSeries = chart.addCandlestickSeries();
candlestickSeries.setData(priceData);

// Signal markers
candlestickSeries.setMarkers([
  { time: '2024-01-15', position: 'belowBar', shape: 'arrowUp', color: 'green' },
  { time: '2024-01-20', position: 'aboveBar', shape: 'arrowDown', color: 'red' }
]);

// Volume pane
const volumeSeries = chart.addHistogramSeries({
  color: '#26a69a',
  priceFormat: { type: 'volume' },
  priceScaleId: ''
});
volumeSeries.setData(volumeData);

// Lazy-load on scroll
chart.timeScale().subscribeVisibleLogicalRangeChange(range => {
  const info = candlestickSeries.barsInLogicalRange(range);
  if (info && info.barsBefore < 50) {
    // Fetch and prepend historical data
  }
});

// Stream updates
function onNewBar(bar) {
  candlestickSeries.update(bar);
  volumeSeries.update({ time: bar.time, value: bar.volume });
}
```

---

## Key References

- **Official Docs**: [https://tradingview.github.io/lightweight-charts/](https://tradingview.github.io/lightweight-charts/)
- **GitHub Repo**: [https://github.com/tradingview/lightweight-charts](https://github.com/tradingview/lightweight-charts)
- **Series Types**: [https://tradingview.github.io/lightweight-charts/docs/series-types](https://tradingview.github.io/lightweight-charts/docs/series-types)
- **Release Notes**: [https://tradingview.github.io/lightweight-charts/docs/release-notes](https://tradingview.github.io/lightweight-charts/docs/release-notes)
- **Product Page**: [https://www.tradingview.com/lightweight-charts/](https://www.tradingview.com/lightweight-charts/)

---

## Next Steps

Share your specific requirements:
- Data flow architecture (server push vs client pull)
- Signal types you want to visualize
- Performance constraints
- Integration points with your QuFLX stack