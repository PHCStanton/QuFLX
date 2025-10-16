import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { createChart } from 'lightweight-charts';
import { createLogger } from '../../utils/logger';
import { getIndicatorDefinition } from '../../constants/indicatorDefinitions';
import {
  createChartConfig,
  createCandlestickSeries,
  createLineSeries,
  createHistogramSeries,
  syncTimeScale,
  cleanupChart,
  validateContainerDimensions
} from '../../utils/chartUtils';

const log = createLogger('MultiPaneChart');

// Helper function to determine if indicator is an oscillator (separate pane)
const isOscillatorIndicator = (indicatorType) => {
  const definition = getIndicatorDefinition(indicatorType);
  if (!definition) return false;
  return definition.category === 'Momentum' || 
         (definition.renderType === 'histogram' && indicatorType !== 'volume');
};

// Helper function to determine if indicator should render on main chart (overlay)
const isOverlayIndicator = (indicatorType) => {
  const definition = getIndicatorDefinition(indicatorType);
  if (!definition) return false;
  
  // Oscillators render in separate panes, not as overlays
  if (isOscillatorIndicator(indicatorType)) return false;
  
  // Everything else that has line or band renderType is an overlay
  return definition.renderType === 'line' || definition.renderType === 'band';
};

const MultiPaneChart = forwardRef(({
  data = [],
  indicators = {},
  backendIndicators = null,
  width = '100%',
  height = 600,
  theme = 'dark',
  className = '',
}, ref) => {
  const mainChartRef = useRef(null);
  const rsiChartRef = useRef(null);
  const macdChartRef = useRef(null);
  
  const mainContainerRef = useRef(null);
  const rsiContainerRef = useRef(null);
  const macdContainerRef = useRef(null);
  
  const mainSeriesRef = useRef(null);
  const overlaySeriesRef = useRef({});
  const rsiSeriesRef = useRef(null);
  const macdSeriesRef = useRef({});
  
  // Track previous data length for performance optimization
  const prevDataLengthRef = useRef(0);

  const hasRSI = React.useMemo(() => {
    if (!backendIndicators?.series) return false;
    // Check for any RSI instance (e.g., 'RSI-14')
    return Object.entries(backendIndicators.series).some(([instanceName, data]) => {
      const type = backendIndicators.indicators?.[instanceName]?.type || instanceName;
      return type.toLowerCase() === 'rsi' && Array.isArray(data) && data.length > 0;
    });
  }, [backendIndicators]);
  const hasMACD = React.useMemo(() => {
    if (!backendIndicators?.series) return false;
    // Check for any MACD instance
    return Object.entries(backendIndicators.series).some(([instanceName, data]) => {
      const type = backendIndicators.indicators?.[instanceName]?.type || instanceName;
      return type.toLowerCase() === 'macd' && data?.macd && data.macd.length > 0;
    });
  }, [backendIndicators]);

  // Calculate heights based on which oscillators are active
  const mainHeight = height * (hasRSI && hasMACD ? 0.6 : hasRSI || hasMACD ? 0.7 : 1.0);
  const oscillatorHeight = height * (hasRSI && hasMACD ? 0.2 : 0.3);

  const chartConfig = React.useMemo(() => createChartConfig(theme), [theme]);

  // Process data
  const processedData = React.useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];
    
    const processed = data
      .filter(item => item && typeof item.timestamp === 'number' && 
              typeof item.close === 'number' && !isNaN(item.close))
      .map(item => ({
        time: item.timestamp,
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close,
      }))
      .sort((a, b) => a.time - b.time)
      .filter((point, i, arr) => i === 0 || point.time > arr[i - 1].time);
    
    // Debug logging
    if (processed.length > 0) {
      log.debug(`[MultiPaneChart] Processed ${processed.length} candles. First: ${JSON.stringify(processed[0])}, Last: ${JSON.stringify(processed[processed.length - 1])}`);
    } else if (data.length > 0) {
      log.warn(`[MultiPaneChart] Had ${data.length} raw data points but 0 after processing. Sample: ${JSON.stringify(data[0])}`);
    }
    
    return processed;
  }, [data]);

  // Initialize main chart
  useEffect(() => {
    if (!mainContainerRef.current) return;

    const initializeChart = () => {
      try {
        const containerWidth = mainContainerRef.current.clientWidth;
        const containerHeight = mainHeight;

        if (containerWidth <= 0 || containerHeight <= 0) {
          log.warn(`[MultiPaneChart] Container has invalid dimensions: ${containerWidth}x${containerHeight}`);
          return;
        }

        log.debug(`[MultiPaneChart] Initializing main chart with dimensions: ${containerWidth}x${containerHeight}`);

        mainChartRef.current = createChart(mainContainerRef.current, {
          ...chartConfig,
          width: containerWidth,
          height: containerHeight,
        });

        mainSeriesRef.current = createCandlestickSeries(mainChartRef.current);

        log.debug('[MultiPaneChart] Main chart initialized successfully');
      } catch (error) {
        log.error('[MultiPaneChart] Failed to initialize main chart:', error);
      }
    };

    const cleanup = () => {
      if (mainChartRef.current) {
        mainChartRef.current.remove();
        mainChartRef.current = null;
      }
      mainSeriesRef.current = null;
      overlaySeriesRef.current = {};
      prevDataLengthRef.current = 0;
    };

    initializeChart();
    return cleanup;
  }, [chartConfig, mainHeight]);

  // Initialize RSI chart
  useEffect(() => {
    if (!rsiContainerRef.current || !hasRSI) return;

    let timeRangeCallback = null;

    const initializeRSI = () => {
      try {
        const containerWidth = rsiContainerRef.current.clientWidth;
        const containerHeight = oscillatorHeight;

        if (containerWidth <= 0 || containerHeight <= 0) {
          log.warn(`[MultiPaneChart] RSI container has invalid dimensions: ${containerWidth}x${containerHeight}`);
          return;
        }

        log.debug(`[MultiPaneChart] Initializing RSI chart with dimensions: ${containerWidth}x${containerHeight}`);

        rsiChartRef.current = createChart(rsiContainerRef.current, {
          ...chartConfig,
          width: containerWidth,
          height: containerHeight,
        });

        rsiSeriesRef.current = createLineSeries(rsiChartRef.current, '#ff6b6b', 2, 'RSI(14)');

        // Add overbought/oversold reference lines
        createLineSeries(rsiChartRef.current, 'rgba(239, 68, 68, 0.3)', 1);
        createLineSeries(rsiChartRef.current, 'rgba(16, 185, 129, 0.3)', 1);

        // Sync time scales
        if (mainChartRef.current) {
          timeRangeCallback = (timeRange) => {
            if (timeRange && rsiChartRef.current && rsiSeriesRef.current) {
              try {
                rsiChartRef.current.timeScale().setVisibleRange({
                  from: timeRange.from,
                  to: timeRange.to,
                });
              } catch (e) {
                // Ignore errors when chart doesn't have data yet
              }
            }
          };
          mainChartRef.current.timeScale().subscribeVisibleTimeRangeChange(timeRangeCallback);
        }
      } catch (error) {
        log.error('[MultiPaneChart] Failed to initialize RSI chart:', error);
      }
    };

    const cleanup = () => {
      if (timeRangeCallback && mainChartRef.current) {
        try {
          mainChartRef.current.timeScale().unsubscribeVisibleTimeRangeChange(timeRangeCallback);
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      if (rsiChartRef.current) {
        rsiChartRef.current.remove();
        rsiChartRef.current = null;
      }
      rsiSeriesRef.current = null;
    };

    initializeRSI();
    return cleanup;
  }, [hasRSI, oscillatorHeight, chartConfig]);

  // Initialize MACD chart
  useEffect(() => {
    if (!macdContainerRef.current || !hasMACD) return;

    let timeRangeCallback = null;

    const initializeMACD = () => {
      try {
        const containerWidth = macdContainerRef.current.clientWidth;
        const containerHeight = oscillatorHeight;

        if (containerWidth <= 0 || containerHeight <= 0) {
          log.warn(`[MultiPaneChart] MACD container has invalid dimensions: ${containerWidth}x${containerHeight}`);
          return;
        }

        log.debug(`[MultiPaneChart] Initializing MACD chart with dimensions: ${containerWidth}x${containerHeight}`);

        macdChartRef.current = createChart(macdContainerRef.current, {
          ...chartConfig,
          width: containerWidth,
          height: containerHeight,
        });

        macdSeriesRef.current.macd = createLineSeries(macdChartRef.current, '#4ecdc4', 2, 'MACD');
        macdSeriesRef.current.signal = createLineSeries(macdChartRef.current, '#ff9f43', 2, 'Signal');
        macdSeriesRef.current.histogram = createHistogramSeries(macdChartRef.current, '#667eea');

        // Sync time scales
        if (mainChartRef.current) {
          timeRangeCallback = (timeRange) => {
            if (timeRange && macdChartRef.current && macdSeriesRef.current.macd) {
              try {
                macdChartRef.current.timeScale().setVisibleRange({
                  from: timeRange.from,
                  to: timeRange.to,
                });
              } catch (e) {
                // Ignore errors when chart doesn't have data yet
              }
            }
          };
          mainChartRef.current.timeScale().subscribeVisibleTimeRangeChange(timeRangeCallback);
        }
      } catch (error) {
        log.error('[MultiPaneChart] Failed to initialize MACD chart:', error);
      }
    };

    const cleanup = () => {
      if (timeRangeCallback && mainChartRef.current) {
        try {
          mainChartRef.current.timeScale().unsubscribeVisibleTimeRangeChange(timeRangeCallback);
        } catch (e) {
          // Ignore cleanup errors
        }
      }
      if (macdChartRef.current) {
        macdChartRef.current.remove();
        macdChartRef.current = null;
      }
      macdSeriesRef.current = {};
    };

    initializeMACD();
    return cleanup;
  }, [hasMACD, oscillatorHeight, chartConfig]);

  // Update main chart data - OPTIMIZED: Use setData() for initial load, update() for incremental changes
  useEffect(() => {
    if (!mainSeriesRef.current) {
      log.debug('[MultiPaneChart] Skipping data update: series not ready');
      return;
    }
    
    try {
      if (processedData.length === 0) {
        mainSeriesRef.current.setData([]);
        prevDataLengthRef.current = 0;
        return;
      }

      const prevLength = prevDataLengthRef.current;
      
      // Initial load or complete data replacement (e.g., switching assets)
      if (prevLength === 0 || processedData.length < prevLength) {
        mainSeriesRef.current.setData(processedData);
        if (mainChartRef.current) {
          mainChartRef.current.timeScale().fitContent();
        }
        log.debug(`[MultiPaneChart] Initial load: ${processedData.length} data points`);
        prevDataLengthRef.current = processedData.length;
        return;
      }

      // Incremental update - use update() for performance (TradingView best practice)
      if (processedData.length > prevLength) {
        // New candle(s) added - update only the new ones
        for (let i = prevLength; i < processedData.length; i++) {
          mainSeriesRef.current.update(processedData[i]);
        }
        // Fit content when adding many new candles (e.g., after hot reload)
        if (processedData.length - prevLength > 10 && mainChartRef.current) {
          mainChartRef.current.timeScale().fitContent();
        }
        log.debug(`[MultiPaneChart] Added ${processedData.length - prevLength} new candle(s) via update()`);
      } else if (processedData.length === prevLength && processedData.length > 0) {
        // Same length - likely updating the last forming candle
        const lastCandle = processedData[processedData.length - 1];
        mainSeriesRef.current.update(lastCandle);
        log.debug(`[MultiPaneChart] Updated last candle via update()`);
      }
      
      prevDataLengthRef.current = processedData.length;
    } catch (error) {
      log.error('[MultiPaneChart] Failed to update main chart data:', error);
    }
  }, [processedData]);

  // Dynamic overlay indicator rendering (SMA, EMA, WMA, Bollinger, SuperTrend, etc.)
  useEffect(() => {
    if (!mainChartRef.current || !backendIndicators?.series) return;

    const series = backendIndicators.series;

    // Clear existing overlays
    Object.keys(overlaySeriesRef.current).forEach(key => {
      if (overlaySeriesRef.current[key]) {
        mainChartRef.current.removeSeries(overlaySeriesRef.current[key]);
        delete overlaySeriesRef.current[key];
      }
    });

    // Dynamically render all overlay indicators
    Object.entries(series).forEach(([instanceName, data]) => {
      // Extract indicator type from metadata (backend now sends instance names as keys)
      const indicatorType = backendIndicators.indicators?.[instanceName]?.type || instanceName;
      const definition = getIndicatorDefinition(indicatorType);
      
      // Skip if not overlay type or no definition
      if (!definition || !isOverlayIndicator(indicatorType)) return;
      
      const params = backendIndicators.indicators?.[instanceName] || {};
      
      // Handle band-type indicators (Bollinger Bands)
      if (definition.renderType === 'band' && typeof data === 'object' && !Array.isArray(data)) {
        const { upper, middle, lower } = data;
        
        // Use band-specific colors if explicitly defined, otherwise use distinct defaults
        const bandColors = definition.bandColors || {
          upper: '#ef5350',   // Red for upper band
          middle: '#ffc107',  // Yellow for middle band
          lower: '#4caf50',   // Green for lower band
        };
        
        if (upper?.length > 0) {
          overlaySeriesRef.current[`${instanceName}_upper`] = mainChartRef.current.addLineSeries({
            color: bandColors.upper,
            lineWidth: 1,
            title: `${instanceName} Upper`,
            priceLineVisible: false,
          });
          overlaySeriesRef.current[`${instanceName}_upper`].setData(upper);
        }

        if (middle?.length > 0) {
          overlaySeriesRef.current[`${instanceName}_middle`] = mainChartRef.current.addLineSeries({
            color: bandColors.middle,
            lineWidth: 1,
            lineStyle: 2,
            title: `${instanceName} Middle`,
            priceLineVisible: false,
          });
          overlaySeriesRef.current[`${instanceName}_middle`].setData(middle);
        }

        if (lower?.length > 0) {
          overlaySeriesRef.current[`${instanceName}_lower`] = mainChartRef.current.addLineSeries({
            color: bandColors.lower,
            lineWidth: 1,
            title: `${instanceName} Lower`,
            priceLineVisible: false,
          });
          overlaySeriesRef.current[`${instanceName}_lower`].setData(lower);
        }
      }
      // Handle line-type indicators (SMA, EMA, WMA, SuperTrend, etc.)
      else if (definition.renderType === 'line' && Array.isArray(data) && data.length > 0) {
        overlaySeriesRef.current[instanceName] = mainChartRef.current.addLineSeries({
          color: definition.color || '#8b5cf6',
          lineWidth: 2,
          title: instanceName,
          priceLineVisible: false,
        });
        overlaySeriesRef.current[instanceName].setData(data);
      }
    });

    log.debug('[MultiPaneChart] Dynamic overlay indicators rendered on main chart');
  }, [backendIndicators]);

  // hasRSI derived from backendIndicators via useMemo above

  // Render oscillator data (RSI and MACD) when ready
  useEffect(() => {
    // Find RSI instance data (e.g., 'RSI-14')
    const rsiInstance = backendIndicators?.series && Object.entries(backendIndicators.series).find(([instanceName, data]) => {
      const type = backendIndicators.indicators?.[instanceName]?.type || instanceName;
      return type.toLowerCase() === 'rsi';
    });
    const rsiData = rsiInstance?.[1];
    
    if (hasRSI && rsiData && rsiData.length > 0 && rsiSeriesRef.current) {
      rsiSeriesRef.current.setData(rsiData);
      log.debug(`[MultiPaneChart] RSI rendered in separate pane: ${rsiData.length} points`);
    }

    // Find MACD instance data
    const macdInstance = backendIndicators?.series && Object.entries(backendIndicators.series).find(([instanceName, data]) => {
      const type = backendIndicators.indicators?.[instanceName]?.type || instanceName;
      return type.toLowerCase() === 'macd';
    });
    const macdData = macdInstance?.[1];
    
    if (hasMACD && macdData?.macd && macdSeriesRef.current.macd) {
      macdSeriesRef.current.macd.setData(macdData.macd);
      if (macdData.signal) {
        macdSeriesRef.current.signal.setData(macdData.signal);
      }
      if (macdData.histogram) {
        const histogramData = macdData.histogram.map(item => ({
          time: item.time,
          value: item.value,
          color: item.value >= 0 ? '#10b981' : '#ef4444'
        }));
        macdSeriesRef.current.histogram.setData(histogramData);
      }
      log.debug('[MultiPaneChart] MACD rendered in separate pane');
    }
  }, [backendIndicators, hasRSI, hasMACD]);

  // Expose methods via ref
  useImperativeHandle(ref, () => ({
    updateData: (newData) => {
      if (!mainSeriesRef.current) return;
      // Process and update
      const processed = newData
        .filter(item => item && typeof item.timestamp === 'number')
        .map(item => ({
          time: item.timestamp,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }))
        .sort((a, b) => a.time - b.time)
        .filter((point, i, arr) => i === 0 || point.time > arr[i - 1].time);
      
      mainSeriesRef.current.setData(processed);
    },
    addDataPoint: (dataPoint) => {
      if (!mainSeriesRef.current) return;
      mainSeriesRef.current.update({
        time: dataPoint.timestamp,
        open: dataPoint.open,
        high: dataPoint.high,
        low: dataPoint.low,
        close: dataPoint.close,
      });
    },
  }), []);

  if (processedData.length === 0) {
    return (
      <div className={`flex items-center justify-center ${className}`} style={{ height }}>
        <div className="text-slate-400">No data available</div>
      </div>
    );
  }

  return (
    <div className={`multi-pane-chart ${className}`} style={{ height }}>
      <div ref={mainContainerRef} style={{ height: mainHeight, width: '100%' }} />
      
      {hasRSI && (
        <div className="rsi-pane" style={{ marginTop: '4px' }}>
          <div className="text-xs text-slate-400 px-2 py-1">RSI</div>
          <div ref={rsiContainerRef} style={{ height: oscillatorHeight - 24, width: '100%' }} />
        </div>
      )}
      
      {hasMACD && (
        <div className="macd-pane" style={{ marginTop: '4px' }}>
          <div className="text-xs text-slate-400 px-2 py-1">MACD</div>
          <div ref={macdContainerRef} style={{ height: oscillatorHeight - 24, width: '100%' }} />
        </div>
      )}
    </div>
  );
});

MultiPaneChart.displayName = 'MultiPaneChart';

export default MultiPaneChart;
