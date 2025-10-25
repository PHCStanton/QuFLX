#!/usr/bin/env python3
"""
Comprehensive Test Suite for Redis Integration
Tests Redis integration, batch processing, and performance
"""

import pytest
import redis
import json
import time
import threading
from unittest.mock import Mock, patch
from datetime import datetime, timezone

# Import modules to test
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from capabilities.redis_integration import RedisIntegration
from capabilities.redis_batch_processor import RedisBatchProcessor
from config.redis_config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    TICK_LIST_PATTERN, PUBSUB_CHANNEL_PATTERN, HISTORICAL_CACHE_PATTERN,
    MAX_TICK_BUFFER_SIZE, HISTORICAL_CACHE_TTL, BATCH_PROCESSING_INTERVAL
)

class TestRedisIntegration:
    """Test Redis integration functionality"""
    
    @pytest.fixture
    def redis_client(self):
        """Create Redis client for testing"""
        try:
            client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            # Test connection
            client.ping()
            yield client
            # Cleanup
            client.flushdb()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_redis_connection(self, redis_client):
        """Test Redis connection establishment"""
        assert redis_client.ping() == True
        info = redis_client.info()
        assert 'redis_version' in info
    
    def test_tick_buffer_operations(self, redis_client):
        """Test tick buffer operations"""
        asset = "EURUSD_otc"
        tick_data = {
            'asset': asset,
            'timestamp': int(time.time()),
            'open': 1.0823,
            'high': 1.0825,
            'low': 1.0821,
            'close': 1.0824,
            'volume': 100
        }
        
        # Test adding tick to buffer
        tick_key = TICK_LIST_PATTERN.format(asset=asset)
        redis_client.lpush(tick_key, json.dumps(tick_data))
        
        # Verify tick is in buffer
        buffer_size = redis_client.llen(tick_key)
        assert buffer_size == 1
        
        # Test buffer trimming
        for i in range(MAX_TICK_BUFFER_SIZE + 10):
            redis_client.lpush(tick_key, json.dumps({
                **tick_data,
                'timestamp': tick_data['timestamp'] + i
            }))
        
        # Buffer should be trimmed to max size
        final_size = redis_client.llen(tick_key)
        assert final_size == MAX_TICK_BUFFER_SIZE
    
    def test_pub_sub_functionality(self, redis_client):
        """Test Redis pub/sub functionality"""
        asset = "EURUSD_otc"
        channel = PUBSUB_CHANNEL_PATTERN.format(asset=asset)
        message = {"test": "message", "timestamp": time.time()}
        
        # Create pub/sub connection
        pubsub = redis_client.pubsub()
        pubsub.subscribe(channel)
        
        # Publish message
        redis_client.publish(channel, json.dumps(message))
        
        # Listen for message (with timeout)
        start_time = time.time()
        received_message = None
        
        for msg in pubsub.listen():
            if msg['type'] == 'message':
                received_message = json.loads(msg['data'])
                break
            if time.time() - start_time > 5:  # 5 second timeout
                break
        
        assert received_message is not None
        assert received_message['test'] == "message"
    
    def test_historical_cache_operations(self, redis_client):
        """Test historical data caching"""
        asset = "EURUSD_otc"
        timeframe = "1M"
        cache_key = HISTORICAL_CACHE_PATTERN.format(asset=asset, timeframe=timeframe)
        
        # Test caching historical data
        candles_data = [
            {
                'timestamp': int(time.time()) - i * 60,
                'open': 1.0823 + i * 0.0001,
                'high': 1.0825 + i * 0.0001,
                'low': 1.0821 + i * 0.0001,
                'close': 1.0824 + i * 0.0001,
                'volume': 100 + i
            }
            for i in range(50)
        ]
        
        # Cache data
        redis_client.setex(
            cache_key,
            HISTORICAL_CACHE_TTL,
            json.dumps(candles_data)
        )
        
        # Verify cache exists
        cached_data = redis_client.get(cache_key)
        assert cached_data is not None
        
        # Parse and verify cached data
        parsed_data = json.loads(cached_data)
        assert len(parsed_data) == 50
        
        # Test TTL
        ttl = redis_client.ttl(cache_key)
        assert 0 < ttl <= HISTORICAL_CACHE_TTL

class TestRedisBatchProcessor:
    """Test Redis batch processor functionality"""
    
    @pytest.fixture
    def mock_redis_integration(self):
        """Create mock Redis integration for testing"""
        mock = Mock(spec=RedisIntegration)
        mock.get_ticks_from_buffer.return_value = [
            {
                'asset': 'EURUSD_otc',
                'price': 1.0823,
                'timestamp': int(time.time())
            }
        ]
        return mock
    
    @pytest.fixture
    def batch_processor(self, mock_redis_integration):
        """Create batch processor with mock Redis integration"""
        return RedisBatchProcessor(mock_redis_integration)
    
    def test_batch_processor_initialization(self, batch_processor):
        """Test batch processor initialization"""
        assert batch_processor.redis_integration is not None
        assert batch_processor.active_assets == set()
        assert batch_processor.stop_event.is_set() == False
    
    def test_asset_registration(self, batch_processor):
        """Test asset registration and unregistration"""
        asset = "EURUSD_otc"
        
        # Test asset registration
        batch_processor.register_asset(asset)
        assert asset in batch_processor.active_assets
        
        # Test asset unregistration
        batch_processor.unregister_asset(asset)
        assert asset not in batch_processor.active_assets
    
    def test_tick_processing(self, batch_processor, mock_redis_integration):
        """Test tick processing functionality"""
        asset = "EURUSD_otc"
        batch_processor.register_asset(asset)
        
        # Process asset ticks
        batch_processor._process_asset_ticks(asset)
        
        # Verify Redis methods were called
        mock_redis_integration.get_ticks_from_buffer.assert_called_once_with(asset)
    
    def test_processing_status(self, batch_processor):
        """Test processing status reporting"""
        asset = "EURUSD_otc"
        batch_processor.register_asset(asset)
        
        status = batch_processor.get_processing_status()
        
        assert 'is_running' in status
        assert 'active_assets' in status
        assert asset in status['active_assets']
        assert 'buffer_sizes' in status
        assert 'last_processed_times' in status

class TestRedisPerformance:
    """Test Redis performance characteristics"""
    
    @pytest.fixture
    def redis_client(self):
        """Create Redis client for performance testing"""
        try:
            client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                decode_responses=True
            )
            client.ping()
            yield client
            client.flushdb()
        except Exception as e:
            pytest.skip(f"Redis not available: {e}")
    
    def test_tick_buffer_performance(self, redis_client):
        """Test tick buffer performance (<1ms target)"""
        asset = "EURUSD_otc"
        tick_key = TICK_LIST_PATTERN.format(asset=asset)
        tick_data = {
            'asset': asset,
            'timestamp': int(time.time()),
            'open': 1.0823,
            'high': 1.0825,
            'low': 1.0821,
            'close': 1.0824,
            'volume': 100
        }
        
        # Measure LPUSH performance
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            redis_client.lpush(tick_key, json.dumps(tick_data))
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations * 1000  # Convert to ms
        
        # Performance assertion (<1ms target)
        assert avg_time < 1.0, f"LPUSH performance too slow: {avg_time:.3f}ms"
    
    def test_cache_performance(self, redis_client):
        """Test cache performance (<1ms target)"""
        asset = "EURUSD_otc"
        timeframe = "1M"
        cache_key = HISTORICAL_CACHE_PATTERN.format(asset=asset, timeframe=timeframe)
        candles_data = json.dumps([
            {
                'timestamp': int(time.time()),
                'open': 1.0823,
                'high': 1.0825,
                'low': 1.0821,
                'close': 1.0824,
                'volume': 100
            }
            for _ in range(200)  # 200 candles
        ])
        
        # Measure SETEX performance
        iterations = 100
        start_time = time.time()
        
        for _ in range(iterations):
            redis_client.setex(cache_key, HISTORICAL_CACHE_TTL, candles_data)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations * 1000  # Convert to ms
        
        # Performance assertion (<1ms target)
        assert avg_time < 1.0, f"SETEX performance too slow: {avg_time:.3f}ms"
    
    def test_pub_sub_performance(self, redis_client):
        """Test pub/sub performance (<1ms target)"""
        asset = "EURUSD_otc"
        channel = PUBSUB_CHANNEL_PATTERN.format(asset=asset)
        message = json.dumps({"test": "performance", "timestamp": time.time()})
        
        # Measure PUBLISH performance
        iterations = 1000
        start_time = time.time()
        
        for _ in range(iterations):
            redis_client.publish(channel, message)
        
        end_time = time.time()
        avg_time = (end_time - start_time) / iterations * 1000  # Convert to ms
        
        # Performance assertion (<1ms target)
        assert avg_time < 1.0, f"PUBLISH performance too slow: {avg_time:.3f}ms"

class TestRedisErrorHandling:
    """Test Redis error handling and recovery"""
    
    def test_connection_retry_logic(self):
        """Test connection retry logic"""
        with patch('capabilities.redis_integration.redis.Redis') as mock_redis:
            # Simulate connection failure
            mock_redis.side_effect = [
                redis.ConnectionError("Connection failed"),
                redis.ConnectionError("Connection failed"),
                redis.Redis()  # Third attempt succeeds
            ]
            
            # Should succeed after retries
            redis_integration = RedisIntegration()
            assert redis_integration.redis_client is not None
    
    def test_buffer_overflow_handling(self):
        """Test buffer overflow handling"""
        with patch('capabilities.redis_integration.redis.Redis') as mock_redis:
            mock_client = Mock()
            mock_redis.return_value = mock_client
            
            # Simulate buffer overflow
            mock_client.pipeline.return_value.execute.side_effect = [
                [1],  # LPUSH result
                [0],  # LTRIM result (0 items trimmed)
            ]
            
            redis_integration = RedisIntegration()
            
            # Test buffer overflow handling
            tick_data = {
                'asset': 'EURUSD_otc',
                'timestamp': int(time.time()),
                'open': 1.0823,
                'high': 1.0825,
                'low': 1.0821,
                'close': 1.0824,
                'volume': 100
            }
            
            result = redis_integration.add_tick_to_buffer('EURUSD_otc', tick_data)
            assert result == True  # Should handle overflow gracefully

class TestRedisIntegration:
    """Integration tests for Redis functionality"""
    
    @pytest.mark.integration
    def test_end_to_end_data_flow(self):
        """Test complete data flow from buffer to pub/sub"""
        try:
            # Create Redis integration
            redis_integration = RedisIntegration()
            
            # Create batch processor
            batch_processor = RedisBatchProcessor(redis_integration)
            
            # Test data
            asset = "EURUSD_otc"
            tick_data = {
                'asset': asset,
                'timestamp': int(time.time()),
                'open': 1.0823,
                'high': 1.0825,
                'low': 1.0821,
                'close': 1.0824,
                'volume': 100
            }
            
            # Add tick to buffer
            assert redis_integration.add_tick_to_buffer(asset, tick_data)
            
            # Register asset for processing
            batch_processor.register_asset(asset)
            
            # Process ticks
            batch_processor._process_asset_ticks(asset)
            
            # Verify data flow
            assert redis_integration.get_buffer_size(asset) == 0  # Should be processed and cleared
            
            print("✅ End-to-end data flow test passed")
            
        except Exception as e:
            pytest.fail(f"Integration test failed: {e}")
    
    @pytest.mark.integration
    def test_concurrent_operations(self):
        """Test concurrent Redis operations"""
        try:
            redis_integration = RedisIntegration()
            
            # Test concurrent operations
            assets = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]
            threads = []
            
            def worker(asset):
                tick_data = {
                    'asset': asset,
                    'timestamp': int(time.time()),
                    'open': 1.0823,
                    'high': 1.0825,
                    'low': 1.0821,
                    'close': 1.0824,
                    'volume': 100
                }
                redis_integration.add_tick_to_buffer(asset, tick_data)
            
            # Start concurrent operations
            for asset in assets:
                thread = threading.Thread(target=worker, args=(asset,))
                thread.start()
                threads.append(thread)
            
            # Wait for completion
            for thread in threads:
                thread.join(timeout=5)
            
            # Verify all operations completed
            for asset in assets:
                buffer_size = redis_integration.get_buffer_size(asset)
                assert buffer_size == 1
            
            print("✅ Concurrent operations test passed")
            
        except Exception as e:
            pytest.fail(f"Concurrent operations test failed: {e}")

if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])