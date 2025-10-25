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
import threading
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timezone
from config.redis_config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD,
    TICK_LIST_PATTERN, PUBSUB_CHANNEL_PATTERN, HISTORICAL_CACHE_PATTERN,
    MAX_TICK_BUFFER_SIZE, HISTORICAL_CACHE_TTL, BATCH_PROCESSING_INTERVAL,
    HISTORICAL_CACHE_SIZE, CONNECTION_POOL_SIZE, SOCKET_TIMEOUT,
    RETRY_ATTEMPTS, RETRY_DELAY
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
    
    def subscribe_to_asset_updates(self, asset: str, callback: Callable) -> bool:
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