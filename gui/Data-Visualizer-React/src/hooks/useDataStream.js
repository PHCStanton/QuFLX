
import { useState, useEffect, useRef, useCallback } from 'react';
import { mergeSortedArrays } from '../utils/chartUtils';

/**
 * Enhanced useDataStream hook with Redis pub/sub integration
 * Replaces Map-based buffer with Redis pub/sub for real-time data streaming
 * Maintains 60fps chart updates with <10ms latency target
 */
export const useDataStream = (socket, options = {}) => {
  const {
    maxBufferSize = 1000,
    processInterval = 100,
    asset = 'EURUSD_otc'
  } = options;

  // State management
  const [data, setData] = useState({
    chartData: [],
    lastMessage: null,
    isConnected: false,
    redisConnected: false,
    error: null,
    bufferStats: {
      size: 0,
      processed: 0,
      dropped: 0
    }
  });

  // Refs for non-react state
  const bufferRef = useRef(new Map());
  const isProcessingRef = useRef(false);
  const animationFrameRef = useRef(null);
  const redisSubscriptionRef = useRef(null);

  // Merge sorted arrays for chart data
  const mergeSortedArrays = useCallback((existing, incoming) => {
    if (!Array.isArray(existing) || !Array.isArray(incoming)) {
      return existing || [];
    }

    // Filter and validate incoming data
    const validIncoming = incoming.filter(item => 
      item && 
      typeof item.timestamp === 'number' && 
      typeof item.close === 'number' && 
      !isNaN(item.close)
    );

    // Merge with existing data, maintaining chronological order
    const merged = mergeSortedArrays(existing, validIncoming);
    
    // Limit buffer size
    if (merged.length > maxBufferSize) {
      return merged.slice(-maxBufferSize);
    }
    
    return merged;
  }, [maxBufferSize]);

  // Process buffered data with requestAnimationFrame
  const processBufferedData = useCallback(() => {
    if (isProcessingRef.current || bufferRef.current.size === 0) {
      return;
    }

    isProcessingRef.current = true;

    try {
      // Get all buffered data
      const allBufferedData = Array.from(bufferRef.current.values())
        .sort((a, b) => a.time - b.time);

      // Merge with existing chart data
      const currentData = data.chartData || [];
      const mergedData = mergeSortedArrays(currentData, allBufferedData);

      // Update state
      setData(prev => ({
        ...prev,
        chartData: mergedData,
        bufferStats: {
          size: bufferRef.current.size,
          processed: prev.bufferStats.processed + allBufferedData.length,
          dropped: prev.bufferStats.dropped
        }
      }));

      // Clear buffer
      bufferRef.current.clear();

    } catch (error) {
      console.error('[useDataStream] Processing error:', error);
      setData(prev => ({
        ...prev,
        error: `Processing error: ${error.message}`
      }));
    } finally {
      isProcessingRef.current = false;
    }
  }, [data.chartData, mergeSortedArrays]);

  // Handle Redis updates
  const handleRedisUpdate = useCallback((message) => {
    try {
      const updateData = message.data;
      
      if (!updateData || !updateData.asset || updateData.asset !== asset) {
        return;
      }

      // Convert to chart format
      const chartData = {
        time: updateData.timestamp,
        open: updateData.open,
        high: updateData.high,
        low: updateData.low,
        close: updateData.close,
        volume: updateData.volume || 0
      };

      // Add to buffer for processing
      const bufferKey = `${asset}_${updateData.timestamp}`;
      bufferRef.current.set(bufferKey, chartData);

    } catch (error) {
      console.error('[useDataStream] Redis update error:', error);
      setData(prev => ({
        ...prev,
        error: `Redis update error: ${error.message}`
      }));
    }
  }, [asset]);

  // Subscribe to Redis updates
  const subscribeToRedis = useCallback(() => {
    if (!socket || !asset) return;

    socket.emit('subscribe_redis_updates', { asset });
    
    socket.on('redis_update', handleRedisUpdate);
    socket.on('redis_subscribed', (data) => {
      console.log(`[useDataStream] Subscribed to Redis updates for ${data.asset}`);
      setData(prev => ({ ...prev, redisConnected: true }));
    });
    
    socket.on('redis_error', (error) => {
      console.error('[useDataStream] Redis error:', error);
      setData(prev => ({ ...prev, error: error.message }));
    });

  }, [socket, asset, handleRedisUpdate]);

  // Unsubscribe from Redis updates
  const unsubscribeFromRedis = useCallback(() => {
    if (!socket) return;

    socket.emit('unsubscribe_redis_updates', { asset });
    socket.off('redis_update', handleRedisUpdate);
    
    setData(prev => ({ ...prev, redisConnected: false }));
  }, [socket, asset, handleRedisUpdate]);

  // Get Redis status
  const getRedisStatus = useCallback(() => {
    if (!socket) return;

    socket.emit('get_redis_status');
    
    socket.on('redis_status', (status) => {
      console.log('[useDataStream] Redis status:', status);
      setData(prev => ({
        ...prev,
        redisConnected: status.connected,
        error: status.error ? status.error.message : null
      }));
    });
  }, [socket]);

  // Setup socket connection and Redis subscription
  useEffect(() => {
    if (!socket) return;

    // Handle socket connection
    const handleConnect = () => {
      console.log('[useDataStream] Socket connected');
      setData(prev => ({ ...prev, isConnected: true }));
      subscribeToRedis();
    };

    const handleDisconnect = () => {
      console.log('[useDataStream] Socket disconnected');
      setData(prev => ({
        ...prev,
        isConnected: false,
        redisConnected: false
      }));
    };

    const handleError = (error) => {
      console.error('[useDataStream] Socket error:', error);
      setData(prev => ({
        ...prev,
        error: `Socket error: ${error.message}`
      }));
    };

    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleError);

    return () => {
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('connect_error', handleError);
      socket.off('redis_update', handleRedisUpdate);
      socket.off('redis_subscribed');
      socket.off('redis_error');
      socket.off('redis_status');
      unsubscribeFromRedis();
    };
  }, [socket, subscribeToRedis, unsubscribeFromRedis, getRedisStatus]);

  // Process buffered data with requestAnimationFrame
  useEffect(() => {
    if (bufferRef.current.size > 0 && !isProcessingRef.current) {
      animationFrameRef.current = requestAnimationFrame(processBufferedData);
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [processBufferedData, bufferRef.current.size]);

  return {
    // State
    chartData: data.chartData,
    isConnected: data.isConnected,
    redisConnected: data.redisConnected,
    error: data.error,
    bufferStats: data.bufferStats,
    
    // Actions
    subscribeToRedis,
    unsubscribeFromRedis,
    getRedisStatus,
    
    // Legacy compatibility
    clearBuffer: () => {
      bufferRef.current.clear();
      setData(prev => ({
        ...prev,
        bufferStats: { ...prev.bufferStats, size: 0 }
      }));
    }
  };
};