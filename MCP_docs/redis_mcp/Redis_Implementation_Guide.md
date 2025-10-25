
# Redis Integration Implementation Guide

## Overview

This guide provides step-by-step instructions for implementing Redis integration in the QuFLX trading platform, including code examples, configuration details, and testing procedures.

## Prerequisites

### System Requirements
- Windows 11 (or Windows 10 with latest updates)
- Node.js 18+ and npm
- Python 3.8+ and pip
- Redis Server 6.0+
- Supabase account and project

### Required Software
```powershell
# Install Redis for Windows
winget install Redis-Redis

# Verify Redis installation
redis-cli --version

# Start Redis service
Start-Service Redis

# Test Redis connection
redis-cli ping
# Expected response: PONG
```

## Phase 1: Backend Redis Integration

### 1.1 Install Python Dependencies

```bash
pip install redis redis-py
```

### 1.2 Create Redis Configuration

Create `config/redis_config.py`:
```python
# Redis Configuration for QuFLX
import os

# Redis connection settings
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_DB = int(os.getenv('REDIS_DB', 0))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

# Redis key patterns
TICK_LIST_PATTERN = "ticks:{asset}"  # e.g., ticks:EURUSD_otc
PUBSUB_CHANNEL_PATTERN = "updates:{asset}"  # e.g., updates:EURUSD_otc
HISTORICAL_CACHE_PATTERN = "historical:{asset}:{timeframe}"  # e.g., historical:EURUSD_otc:1M

# Redis settings
MAX_TICK_BUFFER_SIZE = 1000
HISTORICAL_CACHE_TTL = 3600  # 1 hour in seconds
BATCH_PROCESSING_INTERVAL = 30  # seconds
HISTORICAL_CACHE_SIZE = 200  # candles

# Performance settings
CONNECTION_POOL_SIZE = 10
SOCKET_TIMEOUT = 5  # seconds
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1  # seconds
```

### 1.3 Create Redis Integration Module

Create `capabilities/redis_integration.py`:
```python
#!/usr/bin/env python3
"""
Redis Integration Module for QuFLX Trading Platform

Handles Redis operations for real-time data streaming, caching,
and batch processing for Supabase persistence.
"""

import redis
import json
import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from config.redis_config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    TICK_LIST_PATTERN, PUBSUB_CHANNEL_PATTERN, HISTORICAL_CACHE_PATTERN,
    MAX_TICK_BUFFER_SIZE, HISTORICAL_CACHE_TTL, BATCH_PROCESSING_INTERVAL,
    CONNECTION_POOL_SIZE, SOCKET_TIMEOUT, RETRY_ATTEMPTS, RETRY_DELAY
)

class RedisIntegration:
    """
    Redis integration class for QuFLX trading platform.
    Handles real-time data streaming, caching, and batch operations.
    """
    
    def __init__(self):
        """Initialize Redis connection and pub/sub."""
        self.logger = logging.getLogger(__name__)
        self.redis_client = None
        self.pubsub = None
        self.connection_pool = None
        self._connect()
    
    def _connect(self):
        """Establish Redis connection with retry logic."""
        for attempt in range(RETRY_ATTEMPTS):
            try:
                self.connection_pool = redis.ConnectionPool(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    socket_timeout=SOCKET_TIMEOUT,
                    max_connections=CONNECTION_POOL_SIZE,
                    retry_on_timeout=True
                )
                
                self.redis_client = redis.Redis(
                    connection_pool=self.connection_pool,
                    decode_responses=True
                )
                
                # Test connection
                self.redis_client.ping()
                
                # Initialize pub/sub
                self.pubsub = self.redis_client.pubsub()
                
                self.logger.info("✅ Redis connection established successfully")
                return True
                
            except Exception as e:
                self.logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < RETRY_ATTEMPTS - 1:
                    time.sleep(RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                else:
                    self.logger.error("❌ Failed to connect to Redis after all attempts")
                    raise
    
    def reconnect(self):
        """Reconnect to Redis if connection is lost."""
        try:
            if self.redis_client:
                self.redis_client.ping()
            return True
        except:
            self.logger.info("Attempting to reconnect to Redis...")
            return self._connect()
    
    def add_tick_to_buffer(self, asset: str, tick_data: Dict[str, Any]) -> bool:
        """
        Add tick data to Redis list buffer.
        
        Args:
            asset: Asset symbol (e.g., 'EURUSD_otc')
            tick_data: Tick data dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            tick_key = TICK_LIST_PATTERN.format(asset=asset)
            tick_json = json.dumps(tick_data)
            
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            pipe.lpush(tick_key, tick_json)
            pipe.ltrim(tick_key, 0, MAX_TICK_BUFFER_SIZE - 1)
            pipe.execute()
            
            # Publish to pub/sub channel
            channel = PUBSUB_CHANNEL_PATTERN.format(asset=asset)
            self.redis_client.publish(channel, tick_json)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add tick to buffer for {asset}: {e}")
            return False
    
    def get_ticks_from_buffer(self, asset: str) -> List[Dict[str, Any]]:
        """
        Get all ticks from buffer and clear the list.
        
        Args:
            asset: Asset symbol
            
        Returns:
            List of tick data dictionaries
        """
        try:
            tick_key = TICK_LIST_PATTERN.format(asset=asset)
            
            # Get all ticks and clear the list
            pipe = self.redis_client.pipeline()
            pipe.lrange(tick_key, 0, -1)
            pipe.delete(tick_key)
            results = pipe.execute()
            
            # Parse JSON data
            ticks = []
            for tick_json in results[0]:
                try:
                    tick = json.loads(tick_json)
                    ticks.append(tick)
                except json.JSONDecodeError as e:
                    self.logger.warning(f"Failed to parse tick JSON: {e}")
            
            return ticks
            
        except Exception as e:
            self.logger.error(f"Failed to get ticks from buffer for {asset}: {e}")
            return []
    
    def cache_historical_candles(self, asset: str, timeframe: str, candles: List[Dict[str, Any]]) -> bool:
        """
        Cache historical candle data in Redis.
        
        Args:
            asset: Asset symbol
            timeframe: Timeframe (e.g., '1M', '5M')
            candles: List of candle data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_key = HISTORICAL_CACHE_PATTERN.format(asset=asset, timeframe=timeframe)
            
            # Limit to cache size
            if len(candles) > HISTORICAL_CACHE_SIZE:
                candles = candles[-HISTORICAL_CACHE_SIZE:]
            
            candles_json = json.dumps(candles)
            
            # Set with expiration
            self.redis_client.setex(
                cache_key, 
                HISTORICAL_CACHE_TTL, 
                candles_json
            )
            
            self.logger.info(f"Cached {len(candles)} candles for {asset} {timeframe}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to cache historical candles for {asset}: {e}")
            return False
    
    def get_cached_historical_candles(self, asset: str, timeframe: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached historical candle data.
        
        Args:
            asset: Asset symbol
            timeframe: Timeframe
            
        Returns:
            List of candle data or None if not cached
        """
        try:
            cache_key = HISTORICAL_CACHE_PATTERN.format(asset=asset, timeframe=timeframe)
            candles_json = self.redis_client.get(cache_key)
            
            if candles_json:
                candles = json.loads(candles_json)
                self.logger.info(f"Cache hit: {len(candles)} candles for {asset} {timeframe}")
                return candles
            else:
                self.logger.info(f"Cache miss: {asset} {timeframe}")
                return None
                
        except Exception as e:
            self.logger.error(f"Failed to get cached candles for {asset}: {e}")
            return None
    
    def subscribe_to_asset_updates(self, asset: str, callback) -> bool:
        """
        Subscribe to real-time updates for an asset.
        
        Args:
            asset: Asset symbol
            callback: Callback function for incoming messages
            
        Returns:
            True if successful, False otherwise
        """
        try:
            channel = PUBSUB_CHANNEL_PATTERN.format(asset=asset)
            self.pubsub.subscribe(**{channel: callback})
            
            # Start pub/sub listener in background thread
            import threading
            thread = threading.Thread(target=self._pubsub_listener, daemon=True)
            thread.start()
            
            self.logger.info(f"Subscribed to updates for {asset}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {asset} updates: {e}")
            return False
    
    def _pubsub_listener(self):
        """Background thread for listening to pub/sub messages."""
        try:
            for message in self.pubsub.listen():
                if message['type'] == 'message':
                    # Messages are handled by the callback function
                    pass
        except Exception as e:
            self.logger.error(f"Pub/sub listener error: {e}")
    
    def get_buffer_size(self, asset: str) -> int:
        """
        Get current buffer size for an asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            Buffer size (number of ticks)
        """
        try:
            tick_key = TICK_LIST_PATTERN.format(asset=asset)
            return self.redis_client.llen(tick_key)
        except Exception as e:
            self.logger.error(f"Failed to get buffer size for {asset}: {e}")
            return 0
    
    def clear_asset_data(self, asset: str) -> bool:
        """
        Clear all Redis data for an asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete tick buffer
            tick_key = TICK_LIST_PATTERN.format(asset=asset)
            self.redis_client.delete(tick_key)
            
            # Delete historical cache for all timeframes
            cache_keys = self.redis_client.keys(f"{HISTORICAL_CACHE_PATTERN.format(asset=asset, timeframe='*')}")
            if cache_keys:
                self.redis_client.delete(*cache_keys)
            
            self.logger.info(f"Cleared all Redis data for {asset}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear data for {asset}: {e}")
            return False
    
    def get_redis_info(self) -> Dict[str, Any]:
        """
        Get Redis server information and statistics.
        
        Returns:
            Dictionary with Redis info
        """
        try:
            info = self.redis_client.info()
            return {
                'version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits'),
                'keyspace_misses': info.get('keyspace_misses')
            }
        except Exception as e:
            self.logger.error(f"Failed to get Redis info: {e}")
            return {}
    
    def close(self):
        """Close Redis connections."""
        try:
            if self.pubsub:
                self.pubsub.close()
            if self.redis_client:
                self.redis_client.close()
            if self.connection_pool:
                self.connection_pool.disconnect()
            self.logger.info("Redis connections closed")
        except Exception as e:
            self.logger.error(f"Error closing Redis connections: {e}")
```

### 1.4 Create Batch Processor

Create `capabilities/redis_batch_processor.py`:
```python
#!/usr/bin/env python3
"""
Redis Batch Processor for QuFLX Trading Platform

Handles batch processing of Redis tick data to Supabase.
Runs at configurable intervals to persist data efficiently.
"""

import time
import threading
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone
from capabilities.redis_integration import RedisIntegration
from capabilities.supabase_csv_ingestion import SupabaseCSVIngestion
from config.redis_config import BATCH_PROCESSING_INTERVAL

class RedisBatchProcessor:
    """
    Batch processor for moving Redis tick data to Supabase.
    """
    
    def __init__(self, redis_integration: RedisIntegration):
        """
        Initialize batch processor.
        
        Args:
            redis_integration: Redis integration instance
        """
        self.redis_integration = redis_integration
        self.supabase_client = SupabaseCSVIngestion()
        self.logger = logging.getLogger(__name__)
        self.processing_thread = None
        self.stop_event = threading.Event()
        self.active_assets = set()
        self.last_processed_times = {}
    
    def start_processing(self):
        """Start the batch processing thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            self.logger.warning("Batch processing already running")
            return
        
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        self.logger.info("✅ Redis batch processing started")
    
    def stop_processing(self):
        """Stop the batch processing thread."""
        if self.processing_thread:
            self.stop_event.set()
            self.processing_thread.join(timeout=5)
            self.logger.info("⏹️ Redis batch processing stopped")
    
    def register_asset(self, asset: str):
        """
        Register an asset for batch processing.
        
        Args:
            asset: Asset symbol to process
        """
        self.active_assets.add(asset)
        self.logger.info(f"Registered asset for batch processing: {asset}")
    
    def unregister_asset(self, asset: str):
        """
        Unregister an asset from batch processing.
        
        Args:
            asset: Asset symbol to stop processing
        """
        self.active_assets.discard(asset)
        self.logger.info(f"Unregistered asset from batch processing: {asset}")
    
    def _processing_loop(self):
        """Main processing loop running in background thread."""
        while not self.stop_event.is_set():
            try:
                start_time = time.time()
                
                # Process all active assets
                for asset in list(self.active_assets):
                    self._process_asset_ticks(asset)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Sleep for remaining time in interval
                sleep_time = max(0, BATCH_PROCESSING_INTERVAL - processing_time)
                if sleep_time > 0:
                    self.stop_event.wait(sleep_time)
                
            except Exception as e:
                self.logger.error(f"Error in batch processing loop: {e}")
                self.stop_event.wait(5)  # Wait 5 seconds before retrying
    
    def _process_asset_ticks(self, asset: str):
        """
        Process ticks for a specific asset.
        
        Args:
            asset: Asset symbol to process
        """
        try:
            # Get ticks from Redis buffer
            ticks = self.redis_integration.get_ticks_from_buffer(asset)
            
            if not ticks:
                return  # No ticks to process
            
            # Convert to Supabase format
            supabase_records = self._convert_ticks_to_supabase_format(asset, ticks)
            
            # Insert into Supabase
            result = self._insert_ticks_to_supabase(supabase_records)
            
            if result['success']:
                self.logger.info(f"✅ Processed {len(ticks)} ticks for {asset}")
                self.last_processed_times[asset] = datetime.now(timezone.utc)
            else:
                self.logger.error(f"❌ Failed to process ticks for {asset}: {result.get('error')}")
                
        except Exception as e:
            self.logger.error(f"Error processing ticks for {asset}: {e}")
    
    def _convert_ticks_to_supabase_format(self, asset: str, ticks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Convert tick data to Supabase format.
        
        Args:
            asset: Asset symbol
            ticks: List of tick data
            
        Returns:
            List of Supabase records
        """
        records = []
        for tick in ticks:
            record = {
                'pair': asset,
                'price': float(tick.get('price', tick.get('close', 0))),
                'timestamp': int(tick.get('timestamp', time.time()))
            }
            records.append(record)
        
        return records
    
    def _insert_ticks_to_supabase(self, records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Insert tick records into Supabase.
        
        Args:
            records: List of tick records
            
        Returns:
            Result dictionary with success status
        """
        try:
            # Use Supabase client for batch insertion
            result = self.supabase_client.supabase.table('historical_ticks').insert(records).execute()
            
            return {
                'success': True,
                'inserted_count': len(result.data) if result.data else 0,
                'records': records
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'records': records
            }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        Get current processing status.
        
        Returns:
            Dictionary with processing status
        """
        status = {
            'is_running': self.processing_thread and self.processing_thread.is_alive(),
            'active_assets': list(self.active_assets),
            'last_processed_times': self.last_processed_times.copy(),
            'buffer_sizes': {}
        }
        
        # Get buffer sizes for all active assets
        for asset in self.active_assets:
            status['buffer_sizes'][asset] = self.redis_integration.get_buffer_size(asset)
        
        return status
    
    def force_process_asset(self, asset: str) -> Dict[str, Any]:
        """
        Force immediate processing of ticks for an asset.
        
        Args:
            asset: Asset symbol to process
            
        Returns:
            Result dictionary
        """
        try:
            self._process_asset_ticks(asset)
            return {
                'success': True,
                'message': f"Force processed ticks for {asset}"
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
```

## Phase 2: Frontend Redis Integration

### 2.1 Install Node.js Dependencies

```bash
cd gui/Data-Visualizer-React
npm install redis
```

### 2.2 Update useDataStream Hook

Modified `gui/Data-Visualizer-React/src/hooks/useDataStream.js`:
```javascript
import { useState, useCallback, useEffect, useRef } from 'react';
import { parseTradingData } from '../utils/tradingData';

/**
 * Enhanced Hook for managing streaming data with Redis pub/sub
 * Handles data buffering, processing, and state management
 */
export const useDataStream = (socket, options = {}) => {
  const {
    maxBufferSize = 1000,
    processInterval = 100,
    initialData = [],
    asset = 'EURUSD_otc'  // Default asset
  } = options;

  const [dataState, setDataState] = useState({
    chartData: initialData,
    lastMessage: null,
    historicalCandles: null,
    isProcessing: false,
    redisConnected: false
  });

  // Use refs for mutable state that doesn't need re-renders
  const candleBufferRef = useRef([]);
  const processTimerRef = useRef(null);
  const isProcessingRef = useRef(false);
  const redisSubscriptionRef = useRef(null);

  // Cleanup function for timers and subscriptions
  const cleanup = useCallback(() => {
    if (processTimerRef.current) {
      cancelAnimationFrame(processTimerRef.current);
      processTimerRef.current = null;
    }
    
    // Unsubscribe from Redis updates
    if (redisSubscriptionRef.current) {
      socket.off('redis_update', redisSubscriptionRef.current);
      redisSubscriptionRef.current = null;
    }
  }, [socket]);

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

        // Merge sorted arrays
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

  // Handle incoming Redis messages via Socket.IO
  useEffect(() => {
    if (!socket) return;

    const handleRedisUpdate = (data) => {
      // Update last message
      setDataState(prev => ({ 
        ...prev, 
        lastMessage: data,
        redisConnected: true 
      }));

      const candle = data?.data || data?.candle || data;
      
      // Normalize and validate candle
      const ts = (typeof candle?.time === 'number') ? Math.floor(candle.time) : 
                  (typeof candle?.timestamp === 'number' ? Math.floor(candle.timestamp) : NaN);
      
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

    const handleRedisStatus = (status) => {
      setDataState(prev => ({
        ...prev,
        redisConnected: status.connected
      }));
    };

    // Register event handlers for Redis integration
    socket.on('redis_update', handleRedisUpdate);
    socket.on('historical_candles_loaded', handleHistoricalCandles);
    socket.on('redis_status', handleRedisStatus);

    // Subscribe to Redis updates for the current asset
    socket.emit('subscribe_redis_updates', { asset });

    return () => {
      // Cleanup event handlers and timers
      socket.off('redis_update', handleRedisUpdate);
      socket.off('historical_candles_loaded', handleHistoricalCandles);
      socket.off('redis_status', handleRedisStatus);
      cleanup();
    };
  }, [socket, asset, processBufferedCandles, cleanup]);

  // Store CSV candles
  const storeCsvCandles = useCallback((asset, candles) => {
    if (!socket) return;
    
    console.log(`[CSV Storage] Storing ${candles.length} candles for ${asset}`);
    socket.emit('store_csv_candles', {
      asset,
      candles
    });
  }, [socket]);

  // Subscribe to Redis updates for different assets
  const subscribeToAsset = useCallback((newAsset) => {
    if (!socket) return;
    
    socket.emit('subscribe_redis_updates', { asset: newAsset });
    console.log(`[Redis] Subscribed to updates for ${newAsset}`);
  }, [socket]);

  // Unsubscribe from Redis updates
  const unsubscribeFromAsset = useCallback((asset) => {
    if (!socket) return;
    
    socket.emit('unsubscribe_redis_updates', { asset });
    console.log(`[Redis] Unsubscribed from updates for ${asset}`);
  }, [socket]);

  return {
    data: {
      chartData: dataState.chartData,
      lastMessage: dataState.lastMessage,
      historicalCandles: dataState.historicalCandles,
      isProcessing: isProcessingRef.current,
      redisConnected: dataState.redisConnected
    },
    actions: {
      storeCsvCandles,
      subscribeToAsset,
      unsubscribeFromAsset
    }
  };
};
```

### 2.3 Update useCsvData Hook

Modified `gui/Data-Visualizer-React/src/hooks/useCsvData.js`:
```javascript
import { useState, useCallback, useEffect } from 'react';
import { loadCsvData } from '../utils/csvDataLoader';
import { detectBackendUrl } from '../utils/urlHelper';
import { parseTradingData } from '../utils/tradingData';

/**
 * Enhanced Custom hook for managing CSV data loading with Redis caching
 * Handles loading, parsing, caching, and error states
 */
export const useCsvData = ({
  dataSource,
  selectedAsset,
  selectedAssetFile,
  timeframe,
  isConnected,
  storeCsvCandles,
  socket
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState([]);
  const [cacheHit, setCacheHit] = useState(false);

  const loadData = useCallback(async () => {
    if (dataSource !== 'csv' || !selectedAsset || !selectedAssetFile) {
      setData([]);
      setCacheHit(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    setCacheHit(false);

    try {
      let parsedData = null;
      let dataSource = 'csv';

      // Step 1: Check Redis cache first
      if (socket && isConnected) {
        try {
          // Request cached data from Redis
          socket.emit('get_cached_historical_data', {
            asset: selectedAsset,
            timeframe: timeframe || '1M'
          });

          // Wait for cache response (with timeout)
          const cacheResponse = await new Promise((resolve) => {
            const timeout = setTimeout(() => resolve(null), 1000); // 1 second timeout
            
            const handleCacheResponse = (response) => {
              clearTimeout(timeout);
              socket.off('cached_historical_data', handleCacheResponse);
              resolve(response);
            };
            
            socket.on('cached_historical_data', handleCacheResponse);
          });

          if (cacheResponse && cacheResponse.data && cacheResponse.data.length > 0) {
            parsedData = cacheResponse.data;
            dataSource = 'redis_cache';
            setCacheHit(true);
            console.log(`[useCsvData] Cache hit for ${selectedAsset} ${timeframe}: ${parsedData.length} candles`);
          }
        } catch (cacheError) {
          console.warn('[useCsvData] Cache check failed:', cacheError);
        }
      }

      // Step 2: Load from CSV if cache miss
      if (!parsedData) {
        parsedData = await loadCsvData(
          selectedAsset,
          selectedAssetFile,
          detectBackendUrl,
          parseTradingData
        );
        dataSource = 'csv';
        console.log(`[useCsvData] Loaded from CSV for ${selectedAsset}: ${parsedData.length} candles`);
      }

      setData(parsedData);

      // Store in backend if connected
      if (isConnected && dataSource === 'csv') {
        storeCsvCandles(selectedAsset, parsedData);
      }

      // Cache the data for future use
      if (socket && isConnected && parsedData && parsedData.length > 0) {
        socket.emit('cache_historical_data', {
          asset: selectedAsset,
          timeframe: timeframe || '1M',
          data: parsedData
        });
      }

    } catch (err) {
      setError(err.message);
      setData([]);
      setCacheHit(false);
    } finally {
      setIsLoading(false);
    }
  }, [
    dataSource,
    selectedAsset,
    selectedAssetFile,
    timeframe,
    isConnected,
    storeCsvCandles,
    socket
  ]);

  // Load data when dependencies change
  useEffect(() => {
    loadData();
  }, [loadData, timeframe]);

  // Refresh data function
  const refreshData = useCallback(() => {
    setCacheHit(false);
    loadData();
  }, [loadData]);

  // Clear cache function
  const clearCache = useCallback(() => {
    if (socket && isConnected && selectedAsset) {
      socket.emit('clear_cached_historical_data', {
        asset: selectedAsset,
        timeframe: timeframe || '1M'
      });
      setCacheHit(false);
      console.log(`[useCsvData] Cleared cache for ${selectedAsset} ${timeframe}`);
    }
  }, [socket, isConnected, selectedAsset, timeframe]);

  return {
    data,
    isLoading,
    error,
    cacheHit,
    loadData,
    refreshData,
    clearCache
  };
};
```

## Phase 3: Database Schema Updates

### 3.1 Update Supabase Schema

Create updated `database_schema.sql` with historical_ticks table:
```sql
-- =====================================================
-- HISTORICAL_TICKS TABLE
-- =====================================================
-- Stores individual tick data for high-resolution analysis
CREATE