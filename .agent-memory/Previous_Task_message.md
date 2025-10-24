## Thorough Investigation Report: Lightweight Charts and Indicators Integration Issues

### Critical Issues Identified

#### 1. **WebSocket Event Name Mismatch (CRITICAL)** 🚨
**Location**: [`useIndicatorCalculations.js:50-51`](gui/Data-Visualizer-React/src/hooks/useIndicatorCalculations.js:50) vs [`streaming_server.py:926,933`](streaming_server.py:926)

**Problem**: Frontend listens for wrong event names
- Frontend expects: `indicator_data` and `indicator_error`
- Backend emits: `indicators_calculated` and `indicators_error`

**Impact**: Indicators are calculated but NEVER received by frontend, causing complete indicator failure.

#### 2. **Candle Buffer Processing Race Condition** ⚠️
**Location**: [`DataAnalysis.jsx:173-232`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:173)

**Problem**: Complex buffer management with potential data loss
- Uses both Map and sorted array tracking
- Timer-based processing can miss rapid updates
- `processBufferedCandles` may drop candles during high-frequency streaming

#### 3. **Function Extraction Anti-Pattern** 🔧
**Location**: [`DataAnalysis.jsx:74-87`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:74)

**Problem**: Unsafe destructuring pattern
```javascript
try {
    const { actions: { data: { calculateIndicators: calcFunc } } } = useWebSocket();
    calculateIndicators = calcFunc;
} catch (error) {
    calculateIndicators = null;
}
```
This indicates potential undefined access issues that should be handled within the hook.

#### 4. **Asset Name Normalization Issue** 📝
**Location**: [`streaming_server.py:667-674`](streaming_server.py:667)

**Problem**: CSV file lookup fails due to asset name format mismatch
- Frontend sends: "EURUSD_OTC"
- CSV files named: "EURUSD_otc_1m_2025_10_04.csv"
- Normalization logic doesn't handle underscore removal properly

#### 5. **Chart Update Performance Issue** ⚡
**Location**: [`MultiPaneChart.jsx:296-346`](gui/Data-Visualizer-React/src/components/charts/MultiPaneChart.jsx:296)

**Problem**: Correctly implements performance optimization but timing issues exist
- Uses `setData()` for initial load and `update()` for incremental updates (correct)
- However, the `prevDataLengthRef` tracking can get out of sync during rapid mode switches

#### 6. **Live Streaming Data Flow Issues** 🌊
**Location**: Multiple locations

**Problems**:
- **Duplicate Buffering**: Both `DataAnalysis.jsx` and `useDataStream.js` implement candle buffering
- **State Sync**: `lastMessage` updates don't always trigger chart refreshes
- **Historical Data Loading**: Race condition between CSV load and stream start

#### 7. **Memory Management Concerns** 💾
**Location**: [`DataAnalysis.jsx:106-110`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:106)

**Problem**: Multiple buffers without coordinated cleanup
- `candleBufferRef` Map can grow indefinitely
- `sortedTimesRef` array not cleaned on mode switch
- No cleanup when switching between CSV and Platform modes

### Root Cause Analysis

The primary issue that "other AI models might miss" is the **event name mismatch** between frontend and backend. This is subtle because:
1. The backend successfully calculates indicators
2. The WebSocket connection is established
3. The emission happens without errors
4. But the frontend silently ignores the unrecognized events

### Recommended Fixes

1. **Immediate Fix** (Event Names):
   - Change `useIndicatorCalculations.js` lines 50-51 to:
   ```javascript
   socket.on('indicators_calculated', handleIndicatorData);
   socket.on('indicators_error', handleIndicatorError);
   ```

2. **Refactor WebSocket Hook**:
   - Move function extraction logic inside `useWebSocketV2`
   - Provide safe defaults to prevent undefined access

3. **Consolidate Buffer Management**:
   - Use only `useDataStream` for candle buffering
   - Remove duplicate buffer in `DataAnalysis.jsx`

4. **Fix Asset Normalization**:
   - Update CSV lookup logic to handle different asset formats
   - Add fallback patterns for file matching

5. **Improve State Management**:
   - Add proper cleanup in useEffect returns
   - Clear buffers on mode switches
   - Reset chart references when changing data sources

### Key Principle Violations

- **Functional Simplicity**: Over-complicated buffer management
- **Code Integrity**: Event name mismatch breaks integration
- **Separation of Concerns**: Duplicate buffering logic in multiple components

The most critical fix is the WebSocket event name mismatch - without this, no indicators will ever display regardless of other optimizations.