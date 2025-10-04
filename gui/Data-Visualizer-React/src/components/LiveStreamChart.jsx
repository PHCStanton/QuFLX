import React, { useEffect, useRef, useState } from 'react';
import PropTypes from 'prop-types';

const LiveStreamChart = ({ data, height = 400, asset }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);
  const candleSeriesRef = useRef(null);
  const [chartReady, setChartReady] = useState(false);
  const lastBarRef = useRef(null);
  const lastBucketTimeRef = useRef(null);

  // Initialize chart
  useEffect(() => {
    if (!chartContainerRef.current || typeof window === 'undefined') return;

    const LightweightCharts = window.LightweightCharts;
    if (!LightweightCharts) {
      console.error('LightweightCharts not loaded');
      return;
    }

    // Create chart
    const chart = LightweightCharts.createChart(chartContainerRef.current, {
      width: chartContainerRef.current.clientWidth,
      height: height,
      layout: {
        background: { color: '#1e293b' },
        textColor: '#cbd5e1',
      },
      grid: {
        vertLines: { color: '#334155' },
        horzLines: { color: '#334155' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: true,
      },
    });

    // Create candlestick series
    const candleSeries = chart.addCandlestickSeries({
      upColor: '#10b981',
      downColor: '#ef4444',
      borderVisible: false,
      wickUpColor: '#10b981',
      wickDownColor: '#ef4444',
    });

    chartRef.current = chart;
    candleSeriesRef.current = candleSeries;
    setChartReady(true);

    // Handle resize
    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({ width: chartContainerRef.current.clientWidth });
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [height]);

  // Update chart with live data
  useEffect(() => {
    if (!chartReady || !candleSeriesRef.current || !data) return;

    const { price, timestamp } = data;
    if (!price || !timestamp) return;

    const time = Math.floor(timestamp / 1000); // Convert to seconds
    const candlePeriod = 60; // 1 minute candles in seconds
    const bucketTime = Math.floor(time / candlePeriod) * candlePeriod;
    
    if (!lastBarRef.current || bucketTime > lastBucketTimeRef.current) {
      // New candle
      const newBar = {
        time: bucketTime,
        open: price,
        high: price,
        low: price,
        close: price,
      };
      lastBarRef.current = newBar;
      lastBucketTimeRef.current = bucketTime;
      candleSeriesRef.current.update(newBar);
    } else {
      // Update current candle
      const updatedBar = {
        time: lastBarRef.current.time,
        open: lastBarRef.current.open,
        high: Math.max(lastBarRef.current.high, price),
        low: Math.min(lastBarRef.current.low, price),
        close: price,
      };
      lastBarRef.current = updatedBar;
      candleSeriesRef.current.update(updatedBar);
    }
  }, [data, chartReady]);

  return (
    <div className="bg-slate-800 rounded-lg p-4">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">{asset || 'Live Stream'}</h3>
        {data && (
          <div className="text-sm text-slate-300">
            Price: <span className="font-mono text-green-400">{data.price?.toFixed(5)}</span>
          </div>
        )}
      </div>
      <div ref={chartContainerRef} style={{ position: 'relative' }} />
    </div>
  );
};

LiveStreamChart.propTypes = {
  data: PropTypes.object,
  height: PropTypes.number,
  asset: PropTypes.string,
};

export default LiveStreamChart;
