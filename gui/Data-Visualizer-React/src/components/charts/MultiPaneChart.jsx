import React, { useEffect, useRef, useState, useImperativeHandle, forwardRef } from 'react';
import { createChart } from 'lightweight-charts';
import { createLogger } from '../../utils/logger';
const log = createLogger('MultiPaneChart');

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
    const rsiData = backendIndicators?.series?.rsi;
    return Array.isArray(rsiData) && rsiData.length > 0;
  }, [backendIndicators]);
  const hasMACD = React.useMemo(() => {
    const macdData = backendIndicators?.series?.macd;
    return !!(macdData?.macd && macdData.macd.length > 0);
  }, [backendIndicators]);

  // Calculate heights based on which oscillators are active
  const mainHeight = height * (hasRSI && hasMACD ? 0.6 : hasRSI || hasMACD ? 0.7 : 1.0);
  const oscillatorHeight = height * (hasRSI && hasMACD ? 0.2 : 0.3);

  const chartConfig = React.useMemo(() => ({
    layout: {
      background: { color: theme === 'dark' ? '#1e293b' : '#ffffff' },
      textColor: theme === 'dark' ? '#94a3b8' : '#333333',
    },
    grid: {
      vertLines: { color: theme === 'dark' ? '#334155' : '#e5e7eb' },
      horzLines: { color: theme === 'dark' ? '#334155' : '#e5e7eb' },
    },
    crosshair: { mode: 1 },
    timeScale: {
      borderColor: theme === 'dark' ? '#475569' : '#d1d5db',
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: theme === 'dark' ? '#475569' : '#d1d5db',
    },
    handleScroll: { mouseWheel: true, pressedMouseMove: true },
    handleScale: { axisPressedMouseMove: true, mouseWheel: true, pinch: true },
  }), [theme]);

  // Process data
  const processedData = React.useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];
    
    return data
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
  }, [data]);

  // Initialize main chart
  useEffect(() => {
    if (!mainContainerRef.current) return;

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

      mainSeriesRef.current = mainChartRef.current.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      log.debug('[MultiPaneChart] Main chart initialized successfully');
    } catch (error) {
      log.error('[MultiPaneChart] Failed to initialize main chart:', error);
    }

    return () => {
      if (mainChartRef.current) {
        mainChartRef.current.remove();
        mainChartRef.current = null;
      }
      mainSeriesRef.current = null;
      overlaySeriesRef.current = {};
    };
  }, [chartConfig, mainHeight]);

  // Initialize RSI chart
  useEffect(() => {
    if (!rsiContainerRef.current || !hasRSI) return;

    // Declare callback outside try block for proper cleanup scope
    let timeRangeCallback = null;

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

      rsiSeriesRef.current = rsiChartRef.current.addLineSeries({
        color: '#ff6b6b',
        lineWidth: 2,
        title: 'RSI(14)',
      });

      // Add overbought/oversold reference lines
      const rsiUpperLine = rsiChartRef.current.addLineSeries({
        color: 'rgba(239, 68, 68, 0.3)',
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
      });
      const rsiLowerLine = rsiChartRef.current.addLineSeries({
        color: 'rgba(16, 185, 129, 0.3)',
        lineWidth: 1,
        lineStyle: 2,
        priceLineVisible: false,
      });

      // Sync time scales using time-based synchronization
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

    return () => {
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
  }, [hasRSI, oscillatorHeight, chartConfig]);

  // Initialize MACD chart
  useEffect(() => {
    if (!macdContainerRef.current || !hasMACD) return;

    // Declare callback outside try block for proper cleanup scope
    let timeRangeCallback = null;

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

      macdSeriesRef.current.macd = macdChartRef.current.addLineSeries({
        color: '#4ecdc4',
        lineWidth: 2,
        title: 'MACD',
      });

      macdSeriesRef.current.signal = macdChartRef.current.addLineSeries({
        color: '#ff9f43',
        lineWidth: 2,
        title: 'Signal',
      });

      macdSeriesRef.current.histogram = macdChartRef.current.addHistogramSeries({
        color: '#667eea',
        priceFormat: { type: 'volume' },
        priceScaleId: '',
      });

      // Sync time scales using time-based synchronization
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

    return () => {
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

  // Render overlay indicators (SMA, EMA, Bollinger) on main chart
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

    // SMA
    if (series.sma && series.sma.length > 0) {
      overlaySeriesRef.current.sma = mainChartRef.current.addLineSeries({
        color: '#8b5cf6',
        lineWidth: 2,
        title: `SMA(${backendIndicators.indicators?.sma?.period || 20})`,
        priceLineVisible: false,
      });
      overlaySeriesRef.current.sma.setData(series.sma);
    }

    // EMA
    if (series.ema && series.ema.length > 0) {
      overlaySeriesRef.current.ema = mainChartRef.current.addLineSeries({
        color: '#06d6a0',
        lineWidth: 2,
        title: `EMA(${backendIndicators.indicators?.ema?.period || 20})`,
        priceLineVisible: false,
      });
      overlaySeriesRef.current.ema.setData(series.ema);
    }

    // Bollinger Bands
    if (series.bollinger) {
      const { upper, middle, lower } = series.bollinger;
      
      if (upper?.length > 0) {
        overlaySeriesRef.current.bb_upper = mainChartRef.current.addLineSeries({
          color: '#ef5350',
          lineWidth: 1,
          title: 'BB Upper',
          priceLineVisible: false,
        });
        overlaySeriesRef.current.bb_upper.setData(upper);
      }

      if (middle?.length > 0) {
        overlaySeriesRef.current.bb_middle = mainChartRef.current.addLineSeries({
          color: '#ffc107',
          lineWidth: 1,
          lineStyle: 2,
          title: 'BB Middle',
          priceLineVisible: false,
        });
        overlaySeriesRef.current.bb_middle.setData(middle);
      }

      if (lower?.length > 0) {
        overlaySeriesRef.current.bb_lower = mainChartRef.current.addLineSeries({
          color: '#4caf50',
          lineWidth: 1,
          title: 'BB Lower',
          priceLineVisible: false,
        });
        overlaySeriesRef.current.bb_lower.setData(lower);
      }
    }

    log.debug('[MultiPaneChart] Overlay indicators rendered on main chart');
  }, [backendIndicators]);

  // hasRSI derived from backendIndicators via useMemo above

  // Render oscillator data (RSI and MACD) when ready
  useEffect(() => {
    // RSI
    const rsiData = backendIndicators?.series?.rsi;
    if (hasRSI && rsiData && rsiData.length > 0 && rsiSeriesRef.current) {
      rsiSeriesRef.current.setData(rsiData);
      log.debug(`[MultiPaneChart] RSI rendered in separate pane: ${rsiData.length} points`);
    }

    // MACD
    const macdData = backendIndicators?.series?.macd;
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
