import React, { useRef, useCallback, useImperativeHandle, forwardRef, useEffect } from 'react';
import LightweightChart from '../../../components/charts/LightweightChart';

// Optimized chart component that follows TradingView streaming best practices
const OptimizedTradingChart = forwardRef(({
  data = [],
  isLiveMode = false,
  onChartReady = null,
  height = 500,
  backendIndicators = null
}, ref) => {
  const chartRef = useRef(null);
  const lastBarRef = useRef(null);

  // Expose methods to parent component
  useImperativeHandle(ref, () => ({
    // Direct update method (no state changes)
    updateCandle: (candle) => {
      if (!chartRef.current?.addDataPoint) {
        console.warn('[OptimizedTradingChart] Chart not ready for updateCandle');
        return;
      }

      // Validate candle data
      if (!candle || typeof candle.timestamp !== 'number' || !candle.timestamp) {
        console.warn('[OptimizedTradingChart] Invalid candle data:', candle);
        return;
      }

      // TradingView streaming pattern: Check if updating existing bar or adding new bar
      if (lastBarRef.current && lastBarRef.current.timestamp === candle.timestamp) {
        // Update existing bar (same timestamp)
        chartRef.current.addDataPoint(candle);
      } else if (!lastBarRef.current || candle.timestamp > lastBarRef.current.timestamp) {
        // Add new bar (strictly increasing timestamp)
        chartRef.current.addDataPoint(candle);
        lastBarRef.current = candle;
      }
      // Ignore out-of-order candles (TradingView requirement)
    },

    // Set initial data (for CSV loading)
    setData: (data) => {
      if (!chartRef.current?.updateData) {
        console.warn('[OptimizedTradingChart] Chart not ready for setData');
        return;
      }
      console.log('[OptimizedTradingChart] Setting data:', data.length, 'points');
      chartRef.current.updateData(data);
      lastBarRef.current = data.length > 0 ? data[data.length - 1] : null;
    },

    // Clear chart data
    clear: () => {
      if (!chartRef.current?.updateData) {
        console.warn('[OptimizedTradingChart] Chart not ready for clear');
        return;
      }
      chartRef.current.updateData([]);
      lastBarRef.current = null;
    },

    // Get chart instance
    getChart: () => chartRef.current
  }), []);

  // Handle chart ready callback
  const handleChartReady = useCallback((chart) => {
    console.log('[OptimizedTradingChart] Chart ready, series initialized');
    console.log('[OptimizedTradingChart] Data prop length:', data?.length);
    if (onChartReady) {
      onChartReady();
    }
  }, [onChartReady, data]);

  // Auto-sync data prop changes to chart (for declarative usage from parent)
  useEffect(() => {
    console.log('[OptimizedTradingChart] data prop changed, length:', data?.length);
    if (data && data.length > 0 && chartRef.current?.updateData) {
      console.log('[OptimizedTradingChart] Auto-syncing data to chart');
      chartRef.current.updateData(data);
      lastBarRef.current = data[data.length - 1];
    } else if (data && data.length === 0 && chartRef.current?.updateData) {
      console.log('[OptimizedTradingChart] Clearing chart (empty data array)');
      chartRef.current.updateData([]);
      lastBarRef.current = null;
    }
  }, [data]);

  return (
    <div
      className="glass rounded-xl p-6"
      style={{ borderColor: 'var(--card-border)' }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3
          className="text-xl font-semibold"
          style={{ color: 'var(--text-primary)' }}
        >Chart</h3>
        <span
          className="text-xs px-2 py-1 rounded-full border"
          style={{
            backgroundColor: isLiveMode ? 'var(--accent-green)' : 'var(--card-bg)',
            color: isLiveMode ? 'var(--text-primary)' : 'var(--text-secondary)',
            borderColor: isLiveMode ? 'var(--accent-green)' : 'var(--card-border)'
          }}
        >
          {isLiveMode ? 'Live Streaming' : 'Historical Data'}
        </span>
      </div>

      <LightweightChart
        ref={chartRef}
        data={data}
        height={height}
        onChartReady={handleChartReady}
        enableRealTime={isLiveMode}
        backendIndicators={backendIndicators}
      />
    </div>
  );
});

OptimizedTradingChart.displayName = 'OptimizedTradingChart';

export default OptimizedTradingChart;