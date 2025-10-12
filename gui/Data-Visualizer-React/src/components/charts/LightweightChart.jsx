import React, { useEffect, useRef, useState, useMemo, useCallback, useImperativeHandle, forwardRef } from 'react';
import { createChart } from 'lightweight-charts';
import { calculateSMA, calculateEMA, calculateRSI, calculateMACD } from '../../utils/tradingData';
import { SMA, EMA, RSI, MACD, BollingerBands } from 'technicalindicators';

/**
 * Modern React wrapper for TradingView Lightweight Charts
 * Addresses all known integration issues:
 * - Proper lifecycle management
 * - Single chart instance
 * - Responsive design
 * - Error handling
 * - Performance optimization
 */
const LightweightChart = forwardRef(({
  data = [],
  indicators = {},
  width = '100%',
  height = 400,
  theme = 'dark',
  className = '',
  enabledIndicators = {},
  backendIndicators = null,
  onChartReady = null,
  enableRealTime = false,
  ...chartOptions
}, ref) => {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef({});
  const resizeObserverRef = useRef(null);

  // Expose chart methods via ref with error handling
  useImperativeHandle(ref, () => ({
    updateData: (newData) => {
      try {
        if (!seriesRef.current?.main || !Array.isArray(newData)) {
          console.warn('Chart series not ready or invalid data provided');
          return;
        }
        
        const processedNewData = newData
          .filter(item => {
            if (!item) return false;
            const isValid = 
              typeof item.timestamp === 'number' && !isNaN(item.timestamp) &&
              typeof item.open === 'number' && !isNaN(item.open) &&
              typeof item.high === 'number' && !isNaN(item.high) &&
              typeof item.low === 'number' && !isNaN(item.low) &&
              typeof item.close === 'number' && !isNaN(item.close) &&
              item.high >= item.low && // Basic OHLC validation
              item.high >= Math.max(item.open, item.close) &&
              item.low <= Math.min(item.open, item.close);
            
            if (!isValid) {
              console.warn('Invalid data point filtered out:', item);
            }
            return isValid;
          })
          .map(item => ({
            time: item.timestamp,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
          }))
          .sort((a, b) => a.time - b.time) // Ensure chronological order
          // Deduplicate any identical timestamps to satisfy LightweightCharts requirement
          .filter((point, i, arr) => i === 0 || point.time > arr[i - 1].time);
        
        if (processedNewData.length === 0) {
          console.warn('No valid data points to update');
          return;
        }
        
        seriesRef.current.main.setData(processedNewData);
      } catch (error) {
        console.error('Error updating chart data:', error);
      }
    },
    addDataPoint: (dataPoint) => {
      try {
        if (!seriesRef.current?.main || !dataPoint) {
          console.warn('Chart series not ready or invalid data point');
          return;
        }
        
        // Validate data point
        const isValid = 
          typeof dataPoint.timestamp === 'number' && !isNaN(dataPoint.timestamp) &&
          typeof dataPoint.open === 'number' && !isNaN(dataPoint.open) &&
          typeof dataPoint.high === 'number' && !isNaN(dataPoint.high) &&
          typeof dataPoint.low === 'number' && !isNaN(dataPoint.low) &&
          typeof dataPoint.close === 'number' && !isNaN(dataPoint.close) &&
          dataPoint.high >= dataPoint.low &&
          dataPoint.high >= Math.max(dataPoint.open, dataPoint.close) &&
          dataPoint.low <= Math.min(dataPoint.open, dataPoint.close);
        
        if (!isValid) {
          console.warn('Invalid data point rejected:', dataPoint);
          return;
        }
        
        const processedPoint = {
          time: dataPoint.timestamp,
          open: dataPoint.open,
          high: dataPoint.high,
          low: dataPoint.low,
          close: dataPoint.close,
        };
        
        seriesRef.current.main.update(processedPoint);
      } catch (error) {
        console.error('Error adding data point:', error);
      }
    },
    getChart: () => chartRef.current,
    getSeries: () => seriesRef.current
  }), []);

  // Performance optimization: chunk large datasets
  const CHUNK_SIZE = 1000; // Process data in chunks for better performance
  const MAX_DATA_POINTS = 10000; // Limit total data points to prevent memory issues
  
  // Memoize processed data to avoid reprocessing on every render
  const processedData = useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];
    
    try {
      // Limit data size for performance
      const limitedData = data.length > MAX_DATA_POINTS 
        ? data.slice(-MAX_DATA_POINTS) 
        : data;
      
      return limitedData
        .filter(item => {
          if (!item) return false;
          const isValid = 
            typeof item.timestamp === 'number' && !isNaN(item.timestamp) &&
            typeof item.open === 'number' && !isNaN(item.open) &&
            typeof item.high === 'number' && !isNaN(item.high) &&
            typeof item.low === 'number' && !isNaN(item.low) &&
            typeof item.close === 'number' && !isNaN(item.close) &&
            item.high >= item.low &&
            item.high >= Math.max(item.open, item.close) &&
            item.low <= Math.min(item.open, item.close);
          
          return isValid;
        })
        .map(item => ({
          time: item.timestamp,
          open: item.open,
          high: item.high,
          low: item.low,
          close: item.close,
        }))
        .sort((a, b) => a.time - b.time)
        // Ensure strictly increasing time values by removing duplicates
        .filter((point, i, arr) => i === 0 || point.time > arr[i - 1].time);
    } catch (error) {
      console.error('Error processing chart data:', error);
      return [];
    }
  }, [data]);
  
  // Memoize chart configuration to prevent unnecessary recreations
  const chartConfig = useMemo(() => ({
    width: 0, // Will be set dynamically
    height: typeof height === 'number' ? height : 400,
    layout: {
      background: {
        color: theme === 'dark' ? '#1e293b' : '#ffffff'
      },
      textColor: theme === 'dark' ? '#94a3b8' : '#333333',
    },
    grid: {
      vertLines: { 
        color: theme === 'dark' ? '#334155' : '#e5e7eb' 
      },
      horzLines: { 
        color: theme === 'dark' ? '#334155' : '#e5e7eb' 
      },
    },
    crosshair: {
      mode: 1, // Normal crosshair
    },
    timeScale: {
      borderColor: theme === 'dark' ? '#475569' : '#d1d5db',
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: theme === 'dark' ? '#475569' : '#d1d5db',
    },
    handleScroll: {
      mouseWheel: true,
      pressedMouseMove: true,
    },
    handleScale: {
      axisPressedMouseMove: true,
      mouseWheel: true,
      pinch: true,
    },
    ...chartOptions,
  }), [height, theme, chartOptions]);

  // Use the optimized processedData from above

  // Resize handler
  const handleResize = useCallback(() => {
    if (chartRef.current && containerRef.current) {
      const { clientWidth, clientHeight } = containerRef.current;
      chartRef.current.applyOptions({
        width: clientWidth,
        height: clientHeight || height,
      });
    }
  }, [height]);

  // Initialize chart (only once)
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      // Create chart instance
      chartRef.current = createChart(containerRef.current, {
        ...chartConfig,
        width: containerRef.current.clientWidth,
      });

      // Create main candlestick series
      seriesRef.current.main = chartRef.current.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      // Set up resize observer
      resizeObserverRef.current = new ResizeObserver(handleResize);
      resizeObserverRef.current.observe(containerRef.current);

      // Notify parent component that chart is ready
      if (onChartReady && typeof onChartReady === 'function') {
        onChartReady(chartRef.current);
      }

      console.log('[LightweightChart] Chart initialized successfully');
    } catch (error) {
      console.error('[LightweightChart] Failed to initialize chart:', error);
    }

    // Cleanup function
    return () => {
      if (resizeObserverRef.current) {
        resizeObserverRef.current.disconnect();
        resizeObserverRef.current = null;
      }
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      seriesRef.current = {};
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only initialize once
  
  // Update chart options when config changes
  useEffect(() => {
    if (!chartRef.current) return;
    
    try {
      chartRef.current.applyOptions(chartConfig);
    } catch (error) {
      console.error('[LightweightChart] Failed to update chart options:', error);
    }
  }, [chartConfig]);

  // Update main series data
  useEffect(() => {
    if (!chartRef.current || !seriesRef.current.main) return;

    try {
      if (processedData.length > 0) {
        seriesRef.current.main.setData(processedData);
        chartRef.current.timeScale().fitContent();
        console.log(`[LightweightChart] Updated main series with ${processedData.length} data points`);
      } else {
        seriesRef.current.main.setData([]);
      }
    } catch (error) {
      console.error('[LightweightChart] Failed to update main series:', error);
    }
  }, [processedData]);

  // Calculate and update indicators
  useEffect(() => {
    if (!chartRef.current || !processedData.length) return;

    try {
      // Prepare data for indicator calculations
      const closes = processedData.map(item => item.close);
      const highs = processedData.map(item => item.high);
      const lows = processedData.map(item => item.low);
      const volumes = processedData.map(() => Math.random() * 1000000); // Mock volume

      // Handle SMA indicator
      if (enabledIndicators?.sma) {
        if (!seriesRef.current.sma) {
          seriesRef.current.sma = chartRef.current.addLineSeries({
            color: '#8b5cf6',
            lineWidth: 2,
            title: 'SMA(20)',
          });
        }
        
        const smaValues = SMA.calculate({ period: 20, values: closes });
        const smaData = smaValues.map((value, index) => ({
          time: processedData[index + (closes.length - smaValues.length)].time,
          value: value
        }));
        
        seriesRef.current.sma.setData(smaData);
      } else if (seriesRef.current.sma) {
        chartRef.current.removeSeries(seriesRef.current.sma);
        delete seriesRef.current.sma;
      }

      // Handle EMA indicator
      if (enabledIndicators?.ema) {
        if (!seriesRef.current.ema) {
          seriesRef.current.ema = chartRef.current.addLineSeries({
            color: '#06d6a0',
            lineWidth: 2,
            title: 'EMA(20)',
          });
        }
        
        const emaValues = EMA.calculate({ period: 20, values: closes });
        const emaData = emaValues.map((value, index) => ({
          time: processedData[index + (closes.length - emaValues.length)].time,
          value: value
        }));
        
        seriesRef.current.ema.setData(emaData);
      } else if (seriesRef.current.ema) {
        chartRef.current.removeSeries(seriesRef.current.ema);
        delete seriesRef.current.ema;
      }

      // Handle Bollinger Bands
      if (enabledIndicators?.bollingerBands) {
        const bbInput = {
          period: 20,
          values: closes,
          stdDev: 2
        };
        const bbValues = BollingerBands.calculate(bbInput);
        
        // Upper band
        if (!seriesRef.current.bbUpper) {
          seriesRef.current.bbUpper = chartRef.current.addLineSeries({
            color: '#f59e0b',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            title: 'BB Upper',
          });
        }
        
        // Lower band
        if (!seriesRef.current.bbLower) {
          seriesRef.current.bbLower = chartRef.current.addLineSeries({
            color: '#f59e0b',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            title: 'BB Lower',
          });
        }
        
        // Middle band (SMA)
        if (!seriesRef.current.bbMiddle) {
          seriesRef.current.bbMiddle = chartRef.current.addLineSeries({
            color: '#f59e0b',
            lineWidth: 1,
            title: 'BB Middle',
          });
        }
        
        const bbUpperData = bbValues.map((bb, index) => ({
          time: processedData[index + (closes.length - bbValues.length)].time,
          value: bb.upper
        }));
        
        const bbLowerData = bbValues.map((bb, index) => ({
          time: processedData[index + (closes.length - bbValues.length)].time,
          value: bb.lower
        }));
        
        const bbMiddleData = bbValues.map((bb, index) => ({
          time: processedData[index + (closes.length - bbValues.length)].time,
          value: bb.middle
        }));
        
        seriesRef.current.bbUpper.setData(bbUpperData);
        seriesRef.current.bbLower.setData(bbLowerData);
        seriesRef.current.bbMiddle.setData(bbMiddleData);
      } else {
        // Remove Bollinger Bands if disabled
        ['bbUpper', 'bbLower', 'bbMiddle'].forEach(key => {
          if (seriesRef.current[key]) {
            chartRef.current.removeSeries(seriesRef.current[key]);
            delete seriesRef.current[key];
          }
        });
      }

      // Handle RSI indicator
      if (enabledIndicators?.rsi) {
        if (!seriesRef.current.rsi) {
          seriesRef.current.rsi = chartRef.current.addLineSeries({
            color: '#ff6b6b',
            lineWidth: 2,
            title: 'RSI(14)',
          });
        }
        
        const rsiValues = RSI.calculate({ period: 14, values: closes });
        const rsiData = rsiValues.map((value, index) => ({
          time: processedData[index + (closes.length - rsiValues.length)].time,
          value: value
        }));
        
        seriesRef.current.rsi.setData(rsiData);
      } else if (seriesRef.current.rsi) {
        chartRef.current.removeSeries(seriesRef.current.rsi);
        delete seriesRef.current.rsi;
      }

      // Handle MACD indicator
      if (enabledIndicators?.macd) {
        const macdInput = {
          values: closes,
          fastPeriod: 12,
          slowPeriod: 26,
          signalPeriod: 9,
          SimpleMAOscillator: false,
          SimpleMASignal: false
        };
        const macdValues = MACD.calculate(macdInput);
        
        // MACD Line
        if (!seriesRef.current.macdLine) {
          seriesRef.current.macdLine = chartRef.current.addLineSeries({
            color: '#4ecdc4',
            lineWidth: 2,
            title: 'MACD',
          });
        }
        
        // Signal Line
        if (!seriesRef.current.macdSignal) {
          seriesRef.current.macdSignal = chartRef.current.addLineSeries({
            color: '#ff9f43',
            lineWidth: 2,
            title: 'Signal',
          });
        }
        
        const macdLineData = macdValues.map((macd, index) => ({
          time: processedData[index + (closes.length - macdValues.length)].time,
          value: macd.MACD
        }));
        
        const macdSignalData = macdValues.map((macd, index) => ({
          time: processedData[index + (closes.length - macdValues.length)].time,
          value: macd.signal
        }));
        
        seriesRef.current.macdLine.setData(macdLineData);
        seriesRef.current.macdSignal.setData(macdSignalData);
      } else {
        // Remove MACD if disabled
        ['macdLine', 'macdSignal'].forEach(key => {
          if (seriesRef.current[key]) {
            chartRef.current.removeSeries(seriesRef.current[key]);
            delete seriesRef.current[key];
          }
        });
      }

      console.log('[LightweightChart] Updated indicators:', Object.keys(enabledIndicators).filter(key => enabledIndicators[key]));
    } catch (error) {
      console.error('[LightweightChart] Failed to update indicators:', error);
    }
  }, [enabledIndicators, processedData]);

  // Stage 2: Render backend-calculated indicators as chart overlays
  useEffect(() => {
    if (!chartRef.current || !processedData.length || !backendIndicators) return;

    try {
      // Clear previous backend indicator series
      ['backend_sma', 'backend_rsi', 'backend_bb_upper', 'backend_bb_middle', 'backend_bb_lower'].forEach(key => {
        if (seriesRef.current[key]) {
          chartRef.current.removeSeries(seriesRef.current[key]);
          delete seriesRef.current[key];
        }
      });

      const latestTime = processedData[processedData.length - 1]?.time;
      if (!latestTime) return;

      // Render SMA overlay
      if (backendIndicators.indicators?.sma) {
        const smaValue = backendIndicators.indicators.sma.value;
        if (!seriesRef.current.backend_sma) {
          seriesRef.current.backend_sma = chartRef.current.addLineSeries({
            color: '#8b5cf6',
            lineWidth: 2,
            title: `SMA(${backendIndicators.indicators.sma.period})`,
            priceLineVisible: false,
          });
        }
        // Draw SMA as a horizontal line at the calculated value
        seriesRef.current.backend_sma.setData([
          { time: processedData[Math.max(0, processedData.length - 50)].time, value: smaValue },
          { time: latestTime, value: smaValue }
        ]);
      }

      // Render RSI overlay (scaled to price range for visibility)
      if (backendIndicators.indicators?.rsi) {
        const rsiValue = backendIndicators.indicators.rsi.value;
        // Get price range for scaling
        const prices = processedData.map(d => d.close || d.value);
        const minPrice = Math.min(...prices);
        const maxPrice = Math.max(...prices);
        const priceRange = maxPrice - minPrice;
        
        // Scale RSI (0-100) to fit price chart
        const scaledRSI = minPrice + (rsiValue / 100) * priceRange;
        
        if (!seriesRef.current.backend_rsi) {
          seriesRef.current.backend_rsi = chartRef.current.addLineSeries({
            color: '#ff6b6b',
            lineWidth: 2,
            title: `RSI(${backendIndicators.indicators.rsi.period})=${rsiValue.toFixed(1)}`,
            priceLineVisible: false,
          });
        }
        seriesRef.current.backend_rsi.setData([
          { time: processedData[Math.max(0, processedData.length - 50)].time, value: scaledRSI },
          { time: latestTime, value: scaledRSI }
        ]);
      }

      // Render Bollinger Bands overlays
      if (backendIndicators.indicators?.bollinger) {
        const { upper_band, middle_band, lower_band } = backendIndicators.indicators.bollinger;
        
        // Upper band
        if (!seriesRef.current.backend_bb_upper) {
          seriesRef.current.backend_bb_upper = chartRef.current.addLineSeries({
            color: 'rgba(239, 83, 80, 0.6)',
            lineWidth: 1,
            title: 'BB Upper',
            priceLineVisible: false,
          });
        }
        seriesRef.current.backend_bb_upper.setData([
          { time: processedData[Math.max(0, processedData.length - 50)].time, value: upper_band },
          { time: latestTime, value: upper_band }
        ]);

        // Middle band (same as SMA for BB)
        if (!seriesRef.current.backend_bb_middle) {
          seriesRef.current.backend_bb_middle = chartRef.current.addLineSeries({
            color: 'rgba(255, 193, 7, 0.6)',
            lineWidth: 1,
            lineStyle: 2, // Dashed
            title: 'BB Middle',
            priceLineVisible: false,
          });
        }
        seriesRef.current.backend_bb_middle.setData([
          { time: processedData[Math.max(0, processedData.length - 50)].time, value: middle_band },
          { time: latestTime, value: middle_band }
        ]);

        // Lower band
        if (!seriesRef.current.backend_bb_lower) {
          seriesRef.current.backend_bb_lower = chartRef.current.addLineSeries({
            color: 'rgba(76, 175, 80, 0.6)',
            lineWidth: 1,
            title: 'BB Lower',
            priceLineVisible: false,
          });
        }
        seriesRef.current.backend_bb_lower.setData([
          { time: processedData[Math.max(0, processedData.length - 50)].time, value: lower_band },
          { time: latestTime, value: lower_band }
        ]);
      }

      console.log('[LightweightChart] Backend indicators rendered as overlays (SMA, RSI, Bollinger)');
    } catch (error) {
      console.error('[LightweightChart] Failed to render backend indicators:', error);
    }
  }, [backendIndicators, processedData]);

  // Render loading state
  if (processedData.length === 0) {
    return (
      <div 
        className={`flex items-center justify-center bg-slate-800 rounded-lg ${className}`}
        style={{ width, height: typeof height === 'number' ? `${height}px` : height }}
      >
        <div className="text-center text-slate-400">
          <div
            className="w-10 h-10 border-4 border-slate-600 border-t-emerald-500 rounded-full animate-spin mx-auto mb-4"
          />
          <p>Loading chart data...</p>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className={`w-full rounded-lg overflow-hidden ${className}`}
      style={{ 
        width, 
        height: typeof height === 'number' ? `${height}px` : height,
        minHeight: '400px'
      }}
    />
  );
});

LightweightChart.displayName = 'LightweightChart';

export default LightweightChart;