import React, { useEffect, useRef } from 'react';

const SimpleChart = ({ data = [] }) => {
  const containerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    try {
      console.log('[SimpleChart] Initializing chart...');
      console.log('[SimpleChart] Container element:', containerRef.current);
      console.log('[SimpleChart] LightweightCharts global:', typeof window.LightweightCharts);
      
      if (!window.LightweightCharts) {
        const errorMsg = 'LightweightCharts not loaded from CDN';
        console.error('[SimpleChart]', errorMsg);
        throw new Error(errorMsg);
      }
      
      if (!containerRef.current) {
        const errorMsg = 'Container ref is not available';
        console.error('[SimpleChart]', errorMsg);
        throw new Error(errorMsg);
      }
      
      // Create chart with minimal configuration using CDN global
      const chart = window.LightweightCharts.createChart(containerRef.current, {
        width: containerRef.current.clientWidth,
        height: 400,
        layout: {
          background: { color: '#1e293b' },
          textColor: '#94a3b8',
        },
        grid: {
          vertLines: { color: '#334155' },
          horzLines: { color: '#334155' },
        },
        timeScale: {
          timeVisible: true,
          secondsVisible: false,
        },
      });

      console.log('[SimpleChart] Chart created successfully');

      // Create candlestick series
      const candleSeries = chart.addCandlestickSeries({
        upColor: '#10b981',
        downColor: '#ef4444',
        borderUpColor: '#10b981',
        borderDownColor: '#ef4444',
        wickUpColor: '#10b981',
        wickDownColor: '#ef4444',
      });

      console.log('[SimpleChart] Candlestick series created successfully');

      // Set test data if provided
      if (data.length > 0) {
        const processedData = data
          .filter(item => 
            item && 
            typeof item.timestamp === 'number' && 
            typeof item.open === 'number' &&
            typeof item.high === 'number' &&
            typeof item.low === 'number' &&
            typeof item.close === 'number'
          )
          .map(item => ({
            time: item.timestamp,
            open: item.open,
            high: item.high,
            low: item.low,
            close: item.close,
          }))
          .sort((a, b) => a.time - b.time);

        console.log('[SimpleChart] Setting data:', processedData.length, 'points');
        candleSeries.setData(processedData);
        chart.timeScale().fitContent();
      } else {
        // Set sample data for testing
        const sampleData = [
          { time: 1640995200, open: 100, high: 110, low: 95, close: 105 },
          { time: 1641081600, open: 105, high: 115, low: 100, close: 110 },
          { time: 1641168000, open: 110, high: 120, low: 108, close: 118 },
          { time: 1641254400, open: 118, high: 125, low: 115, close: 120 },
        ];
        console.log('[SimpleChart] Setting sample data');
        candleSeries.setData(sampleData);
        chart.timeScale().fitContent();
      }

      chartRef.current = chart;

      console.log('[SimpleChart] Chart initialization complete');
    } catch (error) {
      console.error('[SimpleChart] Initialization error:', {
        message: error?.message || 'Unknown error',
        name: error?.name || 'Error',
        stack: error?.stack || 'No stack trace',
        error: error
      });
      if (error instanceof Error) {
        console.error('[SimpleChart] Error message:', error.message);
        console.error('[SimpleChart] Error stack:', error.stack);
      } else {
        console.error('[SimpleChart] Non-Error object thrown:', String(error));
      }
    }

    // Cleanup
    return () => {
      if (chartRef.current) {
        console.log('[SimpleChart] Cleaning up chart');
        chartRef.current.remove();
        chartRef.current = null;
      }
    };
  }, [data]);

  return (
    <div
      ref={containerRef}
      className="w-full h-96 bg-slate-800 rounded-lg"
      style={{ minHeight: '400px' }}
    />
  );
};

export default SimpleChart;