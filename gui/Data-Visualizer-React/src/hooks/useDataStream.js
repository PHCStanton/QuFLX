import { useState, useCallback, useEffect, useRef } from 'react';
import { parseTradingData } from '../utils/tradingData';

/**
 * Hook for managing streaming data and candle processing
 * Handles data buffering, processing, and state management
 */
export const useDataStream = (socket, options = {}) => {
  const {
    maxBufferSize = 1000,
    processInterval = 100,
    initialData = []
  } = options;

  const [dataState, setDataState] = useState({
    chartData: initialData,
    lastMessage: null,
    historicalCandles: null,
    isProcessing: false
  });

  // Use refs for mutable state that doesn't need re-renders
  const candleBufferRef = useRef([]);
  const processTimerRef = useRef(null);
  const isProcessingRef = useRef(false);

  // Cleanup function for timers
  const cleanup = useCallback(() => {
    if (processTimerRef.current) {
      cancelAnimationFrame(processTimerRef.current);
      processTimerRef.current = null;
    }
  }, []);

  // Process buffered candles efficiently
  const processBufferedCandles = useCallback(() => {
    // Reset timer id immediately
    processTimerRef.current = null;

    // Skip if already processing or buffer is empty
    if (isProcessingRef.current || candleBufferRef.current.length === 0) {
      return;
    }

    isProcessingRef.current = true;

    try {
      // Take current buffer and clear it
      const buffer = candleBufferRef.current;
      candleBufferRef.current = [];

      setDataState(prev => {
        const A = prev.chartData;
        const B = buffer;
        const merged = [];
        let i = 0, j = 0;

        while (i < A.length && j < B.length) {
          const a = A[i];
          const b = B[j];
          if (a.timestamp === b.timestamp) {
            merged.push(b);
            i++; j++;
          } else if (a.timestamp < b.timestamp) {
            merged.push(a);
            i++;
          } else {
            merged.push(b);
            j++;
          }
        }
        while (i < A.length) merged.push(A[i++]);
        while (j < B.length) merged.push(B[j++]);

        // Trim to maxBufferSize if needed
        if (merged.length > maxBufferSize) {
          merged.splice(0, merged.length - maxBufferSize);
        }

        return {
          ...prev,
          chartData: merged
        };
      });
    } catch (err) {
      console.error('[useDataStream] processBufferedCandles error', err);
    } finally {
      isProcessingRef.current = false;
    }
  }, [maxBufferSize]);

  // Handle incoming messages
  useEffect(() => {
    if (!socket) return;

    const handleCandleUpdate = (data) => {
      // Update last message
      setDataState(prev => ({ ...prev, lastMessage: data }));

      const candle = data?.data || data?.candle;
      // Normalize and validate candle
      const ts = (typeof candle?.time === 'number') ? Math.floor(candle.time) : (typeof candle?.timestamp === 'number' ? Math.floor(candle.timestamp) : NaN);
      if (!candle || Number.isNaN(ts) || typeof candle.close !== 'number') {
        if (process.env.NODE_ENV === 'development') {
          console.warn('[useDataStream] Skipping invalid candle', candle);
        }
        return;
      }

      const normalized = {
        timestamp: ts,
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: typeof candle.volume === 'number' ? candle.volume : 0
      };

      // Binary insert into sorted buffer (replace if same timestamp)
      const arr = candleBufferRef.current;
      let low = 0, high = arr.length;
      while (low < high) {
        const mid = (low + high) >> 1;
        const midTime = arr[mid].timestamp;
        if (midTime < normalized.timestamp) {
          low = mid + 1;
        } else {
          high = mid;
        }
      }
      // If found equal time at position low, replace; else insert
      if (arr[low]?.timestamp === normalized.timestamp) {
        arr[low] = normalized;
      } else {
        arr.splice(low, 0, normalized);
      }

      // Dev-only buffer warnings
      if (process.env.NODE_ENV === 'development' && arr.length > Math.max(10, Math.floor(maxBufferSize * 0.8))) {
        console.warn(`[useDataStream] Buffer size high: ${arr.length}/${maxBufferSize}`);
      }

      // Maintain max buffer size by trimming oldest
      if (arr.length > maxBufferSize) {
        arr.splice(0, arr.length - maxBufferSize);
      }

      // Schedule processing with requestAnimationFrame
      if (!processTimerRef.current) {
        processTimerRef.current = requestAnimationFrame(processBufferedCandles);
      }
    };

    const handleHistoricalCandles = (data) => {
      console.log(`[HistoricalData] Received ${data.count} historical candles for ${data.asset}`);
      
      // Parse and set historical data (normalize to {timestamp,...})
      const parsedData = parseTradingData(data.candles, data.asset);
      setDataState(prev => ({
        ...prev,
        historicalCandles: data,
        chartData: parsedData
      }));
    };

    // Register event handlers
    socket.on('candle_update', handleCandleUpdate);
    socket.on('historical_candles_loaded', handleHistoricalCandles);

    return () => {
      // Cleanup event handlers and timers
      socket.off('candle_update', handleCandleUpdate);
      socket.off('historical_candles_loaded', handleHistoricalCandles);
      cleanup();
    };
  }, [socket, processBufferedCandles, cleanup]);


  // Store CSV candles
  const storeCsvCandles = useCallback((asset, candles) => {
    if (!socket) return;
    
    console.log(`[CSV Storage] Storing ${candles.length} candles for ${asset}`);
    socket.emit('store_csv_candles', {
      asset,
      candles
    });
  }, [socket]);

  return {
    data: {
      chartData: dataState.chartData,
      lastMessage: dataState.lastMessage,
      historicalCandles: dataState.historicalCandles,
      isProcessing: isProcessingRef.current
    },
    actions: {
      storeCsvCandles
    }
  };
};