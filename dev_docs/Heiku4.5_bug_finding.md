# Code Review: Bugs and Inconsistencies Found

## CRITICAL BUGS

### 1. **Missing Error Boundary in App.jsx** 
**File:** [`src/App.jsx`](gui/Data-Visualizer-React/src/App.jsx:1)
**Severity:** CRITICAL
- No Error Boundary component wrapping routes
- Single component error crashes entire application
- **Impact:** Production outages from unhandled errors

### 2. **Race Condition in RealTimeChart.jsx - Stale Closure**
**File:** [`src/components/RealTimeChart.jsx`](gui/Data-Visualizer-React/src/components/RealTimeChart.jsx:28)
**Severity:** CRITICAL
- Line 54: `useEffect` dependency array includes `isStreaming` but the effect initializes stream only once
- `isStreaming` state is checked inside the subscription callback (line 42) but not in dependency array
- **Bug:** When `isStreaming` changes, the old subscription callback still references stale `isStreaming` value
- **Fix:** Add `isStreaming` to dependency array or restructure logic

### 3. **Unsafe Array Operations in PositionList & SignalList**
**File:** [`src/components/PositionList.jsx`](gui/Data-Visualizer-React/src/components/PositionList.jsx:52) and [`src/components/SignalList.jsx`](gui/Data-Visualizer-React/src/components/SignalList.jsx:44)
**Severity:** HIGH
- No null/undefined checks before `.map()` operations
- If `positions` or `signals` props are undefined, component crashes
- **Fix:** Add default empty array: `(positions || []).map(...)`

### 4. **Duplicate useEffect Cleanup in RealTimeChart.jsx**
**File:** [`src/components/RealTimeChart.jsx`](gui/Data-Visualizer-React/src/components/RealTimeChart.jsx:28)
**Severity:** HIGH
- Lines 28-54: First useEffect with cleanup
- Lines 81-87: Second useEffect with identical cleanup
- **Bug:** Stream destroyed twice, potential memory leak or error
- **Fix:** Consolidate into single useEffect

### 5. **WebSocket Event Listener Memory Leak**
**File:** [`src/services/providers/WebSocketProvider.js`](gui/Data-Visualizer-React/src/services/providers/WebSocketProvider.js:115)
**Severity:** HIGH
- Lines 115-116: Event listeners added but never removed on disconnect
- Multiple subscriptions accumulate listeners without cleanup
- **Bug:** Each subscription adds new listeners without removing old ones
- **Fix:** Store handlers and remove them in `unsubscribe()` method

### 6. **Unhandled Promise in WebSocketProvider.connect()**
**File:** [`src/services/providers/WebSocketProvider.js`](gui/Data-Visualizer-React/src/services/providers/WebSocketProvider.js:12)
**Severity:** HIGH
- Promise never rejects on connection timeout
- If socket never connects, promise hangs indefinitely
- **Fix:** Add timeout mechanism and error handling

## HIGH PRIORITY BUGS

### 7. **Invalid Data in LiveTrading.jsx**
**File:** [`src/pages/LiveTrading.jsx`](gui/Data-Visualizer-React/src/pages/LiveTrading.jsx:59)
**Severity:** HIGH
- Line 61: `percentage: '9/1'` - invalid percentage format (should be numeric or valid string)
- Line 62: `percentage: 'L04'` - invalid percentage format
- Line 90-95: Multiple invalid percentages like `'9/6'`, `'3/S'`, `'0/5'`, `'1/5'`
- **Impact:** Display errors, calculation failures

### 8. **Missing Null Checks in DataAnalysis.jsx**
**File:** [`src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:141)
**Severity:** HIGH
- Line 141: Dependency array missing `selectedAsset` - causes stale data
- Line 289-293: `historicalCandles` could be undefined before accessing `.length`
- Line 340-348: No checks for empty `chartData` before accessing indices
- **Fix:** Add proper null/undefined checks

### 9. **Incorrect Dependency Array in DataAnalysis.jsx**
**File:** [`src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:141)
**Severity:** HIGH
- Line 141: `useEffect` depends on `chartData.length` but should depend on `chartData` itself
- Comparing array length instead of array reference causes missed updates
- **Fix:** Change to `[isConnected, chartData]`

### 10. **Missing Error Handling in CSV Loading**
**File:** [`src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:152)
**Severity:** HIGH
- Line 152: Hardcoded localhost URL - fails in production
- No retry logic for failed requests
- Network errors not properly propagated
- **Fix:** Use environment variables for API URL

## MEDIUM PRIORITY ISSUES

### 11. **Inconsistent Key Usage in Lists**
**File:** [`src/pages/LiveTrading.jsx`](gui/Data-Visualizer-React/src/pages/LiveTrading.jsx:145) and [`src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:680)
**Severity:** MEDIUM
- Using array index as key in `.map()` operations
- **Impact:** React can't properly track list items during reorders
- **Fix:** Use unique identifiers instead of indices

### 12. **Missing PropTypes Validation**
**File:** All component files
**Severity:** MEDIUM
- No PropTypes or TypeScript validation
- Props can be wrong type without warning
- **Fix:** Add PropTypes or migrate to TypeScript

### 13. **Hardcoded API Endpoints**
**File:** [`src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:152)
**Severity:** MEDIUM
- Line 152: `http://localhost:3001/api/csv-data/` hardcoded
- Breaks in production/different environments
- **Fix:** Use environment variables

### 14. **Unused State Variables**
**File:** [`src/pages/LiveTrading.jsx`](gui/Data-Visualizer-React/src/pages/LiveTrading.jsx:8)
**Severity:** LOW
- Lines 8-9: `mode` and `isRunning` state declared but never used
- **Fix:** Remove unused state

### 15. **Inconsistent Error Handling Patterns**
**File:** Multiple files
**Severity:** MEDIUM
- Some functions use try-catch, others use `.catch()`, some have no error handling
- No centralized error handling strategy
- **Fix:** Establish consistent error handling pattern

## INCONSISTENCIES

### 16. **Duplicate Grid Layout Logic**
**File:** [`src/pages/DataAnalysis.jsx`](gui/Data-Visualizer-React/src/pages/DataAnalysis.jsx:380) and [`src/pages/StrategyBacktest.jsx`](gui/Data-Visualizer-React/src/pages/StrategyBacktest.jsx:17)
**Severity:** MEDIUM
- Same `getResponsiveColumns()` function duplicated in multiple pages
- Should be centralized in `useResponsiveGrid` hook
- **Fix:** Use the existing hook instead of duplicating logic

### 17. **Inconsistent Logger Usage**
**File:** Multiple files
**Severity:** MEDIUM
- Mix of `console.log()` and logger utility calls
- Logger utility exists but not used consistently
- **Fix:** Replace all `console.log()` with logger calls

### 18. **Missing Async/Await Error Handling**
**File:** [`src/pages/StrategyBacktest.jsx`](gui/Data-Visualizer-React/src/pages/StrategyBacktest.jsx:42)
**Severity:** MEDIUM
- Line 42-50: `loadDataFiles()` doesn't handle errors
- Line 62: `runBacktest()` uses try-catch but doesn't log errors properly
- **Fix:** Add proper error logging and user feedback

## SPECIFIC CODE ISSUES

### Issue 1: Unsafe Array Map in PositionList
```javascript
// BEFORE (Crashes if positions is undefined)
{positions.map((position, idx) => (
  <PositionItem key={idx} position={position} />
))}

// AFTER (Safe)
{(positions || []).map((position, idx) => (
  <PositionItem key={position.label || idx} position={position} />
))}
```

### Issue 2: Stale Closure in RealTimeChart
```javascript
// BEFORE (isStreaming is stale in callback)
useEffect(() => {
  streamRef.current.subscribe((newPoint, allData) => {
    if (chartRef.current && isStreaming) { // stale isStreaming
      chartRef.current.addDataPoint(newPoint);
    }
  });
}, [initialData, updateInterval, isStreaming]); // isStreaming in deps but used in callback

// AFTER (Proper dependency)
useEffect(() => {
  if (!streamRef.current) {
    streamRef.current = new RealTimeDataStream(initialData, updateInterval);
    const unsubscribe = streamRef.current.subscribe((newPoint, allData) => {
      setData(allData);
    });
    return () => unsubscribe();
  }
}, [initialData, updateInterval]);
```

### Issue 3: WebSocket Memory Leak
```javascript
// BEFORE (Listeners accumulate)
this.socket.on('price_tick', tickHandler);
this.socket.on('candle_update', candleHandler);

// AFTER (Proper cleanup)
async unsubscribe(subscriptionId) {
  const subscription = this.subscriptions.get(subscriptionId);
  if (!subscription) return { success: false, error: 'Subscription not found' };

  this.socket.off('price_tick', subscription.tickHandler);
  this.socket.off('candle_update', subscription.candleHandler);
  this.subscriptions.delete(subscriptionId);

  return { success: true };
}
```

## RECOMMENDATIONS

**Immediate Actions (Critical):**
1. Add Error Boundary to App.jsx
2. Fix WebSocket listener cleanup
3. Add null checks to PositionList/SignalList
4. Fix stale closure in RealTimeChart

**Short-term (Next Sprint):**
1. Consolidate duplicate useEffect hooks
2. Fix invalid percentage data in LiveTrading
3. Add proper error handling to all async operations
4. Use environment variables for API endpoints
5. Replace all console.log with logger utility

**Long-term:**
1. Migrate to TypeScript for type safety
2. Implement centralized error handling
3. Add comprehensive error boundaries
4. Consolidate duplicate code (grid layouts)
5. Add integration tests for WebSocket reconnection