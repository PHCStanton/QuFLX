import React, { useEffect, useRef, useMemo } from 'react';
import { createChart } from 'lightweight-charts';
import ErrorBoundary from '../ErrorBoundary';
import { colors } from '../../styles/designTokens';
import { RSI, MACD } from 'technicalindicators';

/**
 * Separate chart component for oscillator indicators like RSI and MACD
 * that require their own price scale
 */
const IndicatorChart = ({ 
  data = [], 
  enabledIndicators = {},
  theme = 'dark',
  height = 150,
  className = ''
}) => {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef({});

  // Memoize chart configuration
  const chartConfig = useMemo(() => ({
    height,
    layout: {
      background: {
        color: colors.cardBg
      },
      textColor: colors.textPrimary,
    },
    grid: {
      vertLines: {
        color: colors.borderPrimary
      },
      horzLines: {
        color: colors.borderPrimary
      },
    },
    crosshair: {
      mode: 1,
    },
    timeScale: {
      borderColor: colors.borderPrimary,
      timeVisible: true,
      secondsVisible: false,
    },
    rightPriceScale: {
      borderColor: colors.borderPrimary,
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
  }), [height]);

  // Memoize processed data
  const processedData = useMemo(() => {
    if (!Array.isArray(data) || data.length === 0) return [];
    
    return data
      .filter(item => 
        item &&
        typeof item.timestamp === 'number' && !isNaN(item.timestamp) &&
        typeof item.close === 'number' && !isNaN(item.close)
      )
      .map(item => ({
        time: item.timestamp,
        close: item.close,
      }))
      .sort((a, b) => a.time - b.time);
  }, [data]);

  // Initialize chart
  useEffect(() => {
    if (!containerRef.current) return;

    try {
      chartRef.current = createChart(containerRef.current, {
        ...chartConfig,
        width: containerRef.current.clientWidth,
      });

      console.log('[IndicatorChart] Oscillator chart initialized');
    } catch (error) {
      console.error('[IndicatorChart] Failed to initialize oscillator chart:', error);
      throw error; // Let ErrorBoundary handle it
    }

    return () => {
      if (chartRef.current) {
        chartRef.current.remove();
        chartRef.current = null;
      }
      seriesRef.current = {};
    };
  }, [chartConfig]);

  // Update indicator data
  useEffect(() => {
    if (!chartRef.current || !processedData.length) return;

    try {
      const closes = processedData.map(item => item.close);

      // Handle RSI indicator
      if (enabledIndicators.rsi) {
        if (!seriesRef.current.rsi) {
          seriesRef.current.rsi = chartRef.current.addLineSeries({
            color: '#f59e0b',
            lineWidth: 2,
            title: 'RSI(14)',
          });

          // Add reference lines for RSI
          seriesRef.current.rsiOverbought = chartRef.current.addLineSeries({
            color: '#ef4444',
            lineWidth: 1,
            lineStyle: 2,
            title: 'Overbought (70)',
            priceLineVisible: false,
            lastValueVisible: false,
          });

          seriesRef.current.rsiOversold = chartRef.current.addLineSeries({
            color: '#10b981',
            lineWidth: 1,
            lineStyle: 2,
            title: 'Oversold (30)',
            priceLineVisible: false,
            lastValueVisible: false,
          });
        }

        const rsiValues = RSI.calculate({ period: 14, values: closes });
        const rsiData = rsiValues.map((value, index) => ({
          time: processedData[index + (closes.length - rsiValues.length)].time,
          value: value
        }));

        seriesRef.current.rsi.setData(rsiData);
        seriesRef.current.rsiOverbought.setData([{ time: processedData[0].time, value: 70 }, { time: processedData[processedData.length - 1].time, value: 70 }]);
        seriesRef.current.rsiOversold.setData([{ time: processedData[0].time, value: 30 }, { time: processedData[processedData.length - 1].time, value: 30 }]);

      } else if (seriesRef.current.rsi) {
        // Remove RSI series if disabled
        chartRef.current.removeSeries(seriesRef.current.rsi);
        chartRef.current.removeSeries(seriesRef.current.rsiOverbought);
        chartRef.current.removeSeries(seriesRef.current.rsiOversold);
        delete seriesRef.current.rsi;
        delete seriesRef.current.rsiOverbought;
        delete seriesRef.current.rsiOversold;
      }

      // Handle MACD indicator
      if (enabledIndicators.macd) {
        // Calculate MACD
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
        if (!seriesRef.current.macd) {
          seriesRef.current.macd = chartRef.current.addLineSeries({
            color: '#ef4444',
            lineWidth: 2,
            title: 'MACD',
          });
        }

        // Signal Line
        if (!seriesRef.current.signal) {
          seriesRef.current.signal = chartRef.current.addLineSeries({
            color: '#3b82f6',
            lineWidth: 2,
            title: 'Signal',
          });
        }

        // Histogram (as area series)
        if (!seriesRef.current.histogram) {
          seriesRef.current.histogram = chartRef.current.addHistogramSeries({
            color: '#8b5cf6',
            title: 'Histogram',
          });
        }

        const macdData = macdValues.map((macd, index) => ({
          time: processedData[index + (closes.length - macdValues.length)].time,
          value: macd.MACD
        }));

        const signalData = macdValues.map((macd, index) => ({
          time: processedData[index + (closes.length - macdValues.length)].time,
          value: macd.signal
        }));

        const histogramData = macdValues.map((macd, index) => ({
          time: processedData[index + (closes.length - macdValues.length)].time,
          value: macd.histogram,
          color: macd.histogram >= 0 ? '#10b981' : '#ef4444'
        }));

        seriesRef.current.macd.setData(macdData);
        seriesRef.current.signal.setData(signalData);
        seriesRef.current.histogram.setData(histogramData);

      } else if (seriesRef.current.macd) {
        // Remove MACD series if disabled
        chartRef.current.removeSeries(seriesRef.current.macd);
        chartRef.current.removeSeries(seriesRef.current.signal);
        chartRef.current.removeSeries(seriesRef.current.histogram);
        delete seriesRef.current.macd;
        delete seriesRef.current.signal;
        delete seriesRef.current.histogram;
      }

      console.log('[IndicatorChart] Updated indicators with', processedData.length, 'data points');
    } catch (error) {
      console.error('[IndicatorChart] Failed to update indicators:', error);
      throw error; // Let ErrorBoundary handle it
    }
  }, [processedData, enabledIndicators]);

  // Render loading state
  if (processedData.length === 0) {
    return (
      <div 
        className={`flex items-center justify-center bg-slate-800 rounded-lg ${className}`}
        style={{ height: `${height}px` }}
      >
        <div className="text-center text-slate-400">
          <div className="w-6 h-6 border-2 border-slate-600 border-t-emerald-500 rounded-full animate-spin mx-auto mb-2" />
          <p className="text-sm">Loading indicators...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary>
      <div
        ref={containerRef}
        className={`w-full rounded-lg overflow-hidden ${className}`}
        style={{ height: `${height}px` }}
      />
    </ErrorBoundary>
  );
};

export default IndicatorChart;