# QuFLX Architecture Documentation

## Core Architecture Principles

✅ **Functional Simplicity**
- Clear, focused components and hooks
- Single responsibility principle
- Explicit data flow

✅ **Sequential Logic**
- Progressive data processing
- Clear state transitions
- Predictable data flow

✅ **Zero Assumptions**
- Explicit error handling
- Proper cleanup
- Defensive programming

✅ **Code Integrity**
- Backward compatible changes
- Consistent error boundaries
- Proper type checking

## WebSocket Architecture

The WebSocket system has been decomposed into focused, specialized hooks:

### 1. useConnection
Handles core WebSocket connection lifecycle:
- Connection establishment and cleanup
- Reconnection logic
- Chrome DevTools status
- Error handling

```javascript
const { socket, state } = useConnection(url);
```

### 2. useStreamControl
Manages streaming state and asset detection:
- Stream lifecycle (start/stop)
- Asset detection and changes
- Reconnection events
- State transitions

```javascript
const { stream, assetDetection, actions } = useStreamControl(socket);
```

### 3. useDataStream
Efficient data processing and management:
- Optimized candle buffering
- O(1) data updates using Map
- Memory-efficient processing
- Proper cleanup of timers and resources

```javascript
const { data, actions } = useDataStream(socket, {
  maxBufferSize: 1000,
  processInterval: 100
});
```

### 4. useIndicators
Centralized indicator management:
- Backend-driven calculations
- Consistent data format
- Efficient updates
- Clear error handling

```javascript
const {
  activeIndicators,
  addIndicator,
  removeIndicator,
  formatIndicatorReading
} = useIndicators(options);
```

## Data Flow

```
WebSocket Connection
      ↓
Stream Control
      ↓
Data Processing
      ↓
Indicator Calculation
      ↓
UI Updates
```

## Memory Management

### Buffer Management
- Fixed-size circular buffer
- Efficient Map-based updates
- Proper cleanup of resources
- Timer optimization

### Event Handling
- Proper event listener cleanup
- Ref-based state for performance
- Optimized re-render cycles

## Performance Optimizations

### 1. Data Processing
- O(1) candle updates using Map
- Batched processing with timer
- Efficient sorting strategies

### 2. State Management
- Focused state updates
- Ref-based mutable state
- Optimized re-renders

### 3. Event Handling
- Proper event cleanup
- Debounced processing
- Memory-efficient buffers

## Error Handling

### 1. Connection Errors
- Explicit error states
- Reconnection handling
- User feedback

### 2. Data Processing Errors
- Validation checks
- Error boundaries
- Graceful degradation

### 3. Indicator Errors
- Backend validation
- Frontend error display
- Clear error messages

## Component Architecture

### DataAnalysis Page
- Manages data source selection
- Coordinates streaming state
- Handles user interactions

### ChartContainer
- Renders chart components
- Manages chart layout
- Handles chart interactions

### IndicatorPanel
- Manages indicator configuration
- Displays indicator readings
- Handles indicator updates

## Future Enhancements

### Phase 6: Chart Optimization
- Layout expansion
- Tooltips and markers
- Visual polish

### Phase 7: Strategy Features
- Replay functionality
- Visual signals
- Parameter adjustment

### Phase 8: Live Trading
- Real-time signals
- Trade execution
- Position monitoring

## Best Practices

1. **State Management**
   - Use appropriate state location
   - Minimize state duplication
   - Clear state transitions

2. **Error Handling**
   - Comprehensive error boundaries
   - Clear error messages
   - Graceful degradation

3. **Performance**
   - Efficient data structures
   - Optimized processing
   - Proper cleanup

4. **Testing**
   - Unit tests for critical paths
   - Integration tests
   - Performance benchmarks

## Conclusion

The new architecture provides:
- Clear separation of concerns
- Efficient data processing
- Robust error handling
- Scalable foundation for future features