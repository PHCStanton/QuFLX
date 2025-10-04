/**
 * Real-time data streaming utilities for TradingView Lightweight Charts
 * Provides WebSocket-like simulation and live data updates
 */

/**
 * Simulates real-time price data updates
 * In a real application, this would connect to a WebSocket or API
 */
export class RealTimeDataStream {
  constructor(initialData = [], updateInterval = 1000) {
    this.data = [...initialData];
    this.updateInterval = updateInterval;
    this.subscribers = new Set();
    this.isStreaming = false;
    this.intervalId = null;
    this.lastPrice = initialData.length > 0 ? initialData[initialData.length - 1].close : 100;
  }

  /**
   * Subscribe to real-time data updates
   * @param {Function} callback - Function to call when new data arrives
   * @returns {Function} Unsubscribe function
   */
  subscribe(callback) {
    this.subscribers.add(callback);
    return () => {
      this.subscribers.delete(callback);
    };
  }

  /**
   * Start streaming real-time data
   */
  startStreaming() {
    if (this.isStreaming) return;
    
    this.isStreaming = true;
    this.intervalId = setInterval(() => {
      const newDataPoint = this.generateNextDataPoint();
      this.data.push(newDataPoint);
      
      // Notify all subscribers
      this.subscribers.forEach(callback => {
        try {
          callback(newDataPoint, [...this.data]);
        } catch (error) {
          console.error('[RealTimeDataStream] Error in subscriber callback:', error);
        }
      });
    }, this.updateInterval);
    
    console.log('[RealTimeDataStream] Started streaming with interval:', this.updateInterval);
  }

  /**
   * Stop streaming real-time data
   */
  stopStreaming() {
    if (!this.isStreaming) return;
    
    this.isStreaming = false;
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    
    console.log('[RealTimeDataStream] Stopped streaming');
  }

  /**
   * Generate next realistic data point
   * Simulates market price movements
   */
  generateNextDataPoint() {
    const now = Math.floor(Date.now() / 1000);
    
    // Simulate realistic price movement
    const volatility = 0.002; // 0.2% volatility
    const trend = (Math.random() - 0.5) * 0.001; // Small trend component
    const randomChange = (Math.random() - 0.5) * volatility;
    
    const priceChange = trend + randomChange;
    const newPrice = this.lastPrice * (1 + priceChange);
    
    // Generate OHLC data
    const high = newPrice * (1 + Math.random() * 0.001);
    const low = newPrice * (1 - Math.random() * 0.001);
    const open = this.lastPrice;
    const close = newPrice;
    const volume = Math.floor(Math.random() * 1000000) + 100000;
    
    this.lastPrice = close;
    
    return {
      time: now,
      timestamp: now,
      open: parseFloat(open.toFixed(5)),
      high: parseFloat(high.toFixed(5)),
      low: parseFloat(low.toFixed(5)),
      close: parseFloat(close.toFixed(5)),
      volume
    };
  }

  /**
   * Get current data
   */
  getData() {
    return [...this.data];
  }

  /**
   * Update streaming interval
   */
  setUpdateInterval(interval) {
    this.updateInterval = interval;
    if (this.isStreaming) {
      this.stopStreaming();
      this.startStreaming();
    }
  }

  /**
   * Get streaming status
   */
  getStatus() {
    return {
      isStreaming: this.isStreaming,
      updateInterval: this.updateInterval,
      subscriberCount: this.subscribers.size,
      dataPoints: this.data.length
    };
  }

  /**
   * Cleanup resources
   */
  destroy() {
    this.stopStreaming();
    this.subscribers.clear();
    this.data = [];
  }
}

/**
 * Hook for using real-time data in React components
 */
export const useRealTimeData = (initialData = [], updateInterval = 1000) => {
  const [stream] = useState(() => new RealTimeDataStream(initialData, updateInterval));
  const [data, setData] = useState(initialData);
  const [isStreaming, setIsStreaming] = useState(false);

  useEffect(() => {
    const unsubscribe = stream.subscribe((newPoint, allData) => {
      setData(allData);
    });

    return () => {
      unsubscribe();
      stream.destroy();
    };
  }, [stream]);

  const startStreaming = useCallback(() => {
    stream.startStreaming();
    setIsStreaming(true);
  }, [stream]);

  const stopStreaming = useCallback(() => {
    stream.stopStreaming();
    setIsStreaming(false);
  }, [stream]);

  const setUpdateInterval = useCallback((interval) => {
    stream.setUpdateInterval(interval);
  }, [stream]);

  return {
    data,
    isStreaming,
    startStreaming,
    stopStreaming,
    setUpdateInterval,
    status: stream.getStatus()
  };
};

// Import React hooks
import { useState, useEffect, useCallback } from 'react';