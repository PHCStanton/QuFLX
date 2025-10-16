// Chart utility functions for common operations

export const createChartConfig = (theme = 'dark', width, height) => ({
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
  width,
  height,
});

export const createCandlestickSeries = (chart, colors = {}) => {
  const defaultColors = {
    upColor: '#10b981',
    downColor: '#ef4444',
    borderUpColor: '#10b981',
    borderDownColor: '#ef4444',
    wickUpColor: '#10b981',
    wickDownColor: '#ef4444',
  };

  return chart.addCandlestickSeries({
    ...defaultColors,
    ...colors,
  });
};

export const createLineSeries = (chart, color, lineWidth = 2, title = '') => {
  return chart.addLineSeries({
    color,
    lineWidth,
    title,
    priceLineVisible: false,
  });
};

export const createHistogramSeries = (chart, color, title = '') => {
  return chart.addHistogramSeries({
    color,
    priceFormat: { type: 'volume' },
    priceScaleId: '',
    title,
  });
};

export const syncTimeScale = (mainChart, targetChart, callback) => {
  if (!mainChart || !targetChart) return null;

  const timeRangeCallback = (timeRange) => {
    if (timeRange) {
      try {
        targetChart.timeScale().setVisibleRange({
          from: timeRange.from,
          to: timeRange.to,
        });
      } catch (e) {
        // Ignore errors when chart doesn't have data yet
      }
    }
  };

  mainChart.timeScale().subscribeVisibleTimeRangeChange(timeRangeCallback);
  return timeRangeCallback;
};

export const cleanupChart = (chartRef, seriesRef = null, overlayRef = null) => {
  if (chartRef?.current) {
    chartRef.current.remove();
    chartRef.current = null;
  }

  if (seriesRef?.current) {
    seriesRef.current = null;
  }

  if (overlayRef?.current) {
    overlayRef.current = {};
  }
};

export const validateContainerDimensions = (containerRef, log) => {
  if (!containerRef?.current) return false;

  const width = containerRef.current.clientWidth;
  const height = containerRef.current.clientHeight;

  if (width <= 0 || height <= 0) {
    log?.warn(`Container has invalid dimensions: ${width}x${height}`);
    return false;
  }

  return { width, height };
};