# Redis Integration Implementation Guide (Complete)

## Phase 3: Database Schema Updates (Continued)

### 3.1 Update Supabase Schema

Create updated `database_schema.sql` with historical_ticks table:
```sql
-- =====================================================
-- HISTORICAL_TICKS TABLE
-- =====================================================
-- Stores individual tick data for high-resolution analysis
CREATE TABLE IF NOT EXISTS historical_ticks (
    id BIGSERIAL PRIMARY KEY,
    pair VARCHAR(20) NOT NULL,        -- e.g., 'EURUSD_otc'
    price DECIMAL(20,10) NOT NULL,    -- Tick price
    timestamp BIGINT NOT NULL,        -- Unix timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEXES FOR HISTORICAL_TICKS
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_historical_ticks_pair_timestamp 
    ON historical_ticks (pair, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_historical_ticks_timestamp 
    ON historical_ticks (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_historical_ticks_pair 
    ON historical_ticks (pair);

-- =====================================================
-- ROW LEVEL SECURITY (RLS) POLICIES FOR HISTORICAL_TICKS
-- =====================================================
ALTER TABLE historical_ticks ENABLE ROW LEVEL SECURITY;

-- Policies for historical_ticks table
CREATE POLICY "Historical ticks are viewable by everyone" ON historical_ticks
    FOR SELECT USING (true);

CREATE POLICY "Historical ticks are insertable by authenticated users" ON historical_ticks
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');
```

## Phase 4: Modified Streaming Server

### 4.1 Updated streaming_server.py

Key modifications to integrate Redis:
```python
# Add these imports at the top
import redis
from capabilities.redis_integration import RedisIntegration
from capabilities.redis_batch_processor import RedisBatchProcessor

# Add Redis integration to global state
redis_integration = None
batch_processor = None

# Initialize Redis in main function
def initialize_redis():
    """Initialize Redis integration and batch processor."""
    global redis_integration, batch_processor
    
    try:
        redis_integration = RedisIntegration()
        batch_processor = RedisBatchProcessor(redis_integration)
        batch_processor.start_processing()
        
        print("[Redis] ✓ Redis integration initialized successfully")
        return True
    except Exception as e:
        print(f"[Redis] ✗ Failed to initialize Redis: {e}")
        return False

# Modify extract_candle_for_emit function
def extract_candle_for_emit(asset: str) -> Optional[Dict]:
    """
    Extract latest formed candle and push to Redis.
    """
    global data_streamer, redis_integration
    
    try:
        # Use capability's public API method
        latest_candle = data_streamer.get_latest_candle(asset)
        
        if latest_candle:
            timestamp, open_price, close_price, high_price, low_price = latest_candle
            
            candle_data = {
                'asset': asset,
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': 0,
                'date': datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
            }
            
            # Push to Redis for real-time streaming
            if redis_integration:
                redis_integration.add_tick_to_buffer(asset, candle_data)
            
            return candle_data
    
    except Exception as e:
        print(f"❌ Error extracting candle: {e}")
    
    return None

# Add new Socket.IO event handlers
@socketio.on('subscribe_redis_updates')
def handle_subscribe_redis_updates(data):
    """Subscribe client to Redis updates for an asset."""
    global redis_integration
    
    try:
        asset = data.get('asset')
        if not asset:
            emit('error', {'message': 'No asset specified'})
            return
        
        # Register asset for batch processing
        if batch_processor:
            batch_processor.register_asset(asset)
        
        # Subscribe to Redis pub/sub
        def redis_callback(message):
            # Forward Redis message to client
            emit('redis_update', {'data': json.loads(message['data'])})
        
        if redis_integration.subscribe_to_asset_updates(asset, redis_callback):
            emit('redis_subscribed', {'asset': asset})
            print(f"[Redis] Client subscribed to {asset} updates")
        else:
            emit('error', {'message': f'Failed to subscribe to {asset} updates'})
            
    except Exception as e:
        emit('error', {'message': f'Subscription error: {str(e)}'})

@socketio.on('unsubscribe_redis_updates')
def handle_unsubscribe_redis_updates(data):
    """Unsubscribe client from Redis updates for an asset."""
    global batch_processor
    
    try:
        asset = data.get('asset')
        if not asset:
            emit('error', {'message': 'No asset specified'})
            return
        
        # Unregister from batch processing
        if batch_processor:
            batch_processor.unregister_asset(asset)
        
        emit('redis_unsubscribed', {'asset': asset})
        print(f"[Redis] Client unsubscribed from {asset} updates")
        
    except Exception as e:
        emit('error', {'message': f'Unsubscription error: {str(e)}'})

@socketio.on('get_cached_historical_data')
def handle_get_cached_historical_data(data):
    """Get cached historical data from Redis."""
    global redis_integration
    
    try:
        asset = data.get('asset')
        timeframe = data.get('timeframe', '1M')
        
        if not asset:
            emit('error', {'message': 'No asset specified'})
            return
        
        # Get cached data from Redis
        cached_data = redis_integration.get_cached_historical_candles(asset, timeframe)
        
        if cached_data:
            emit('cached_historical_data', {
                'asset': asset,
                'timeframe': timeframe,
                'data': cached_data,
                'source': 'redis_cache'
            })
        else:
            emit('cached_historical_data', {
                'asset': asset,
                'timeframe': timeframe,
                'data': None,
                'source': 'cache_miss'
            })
            
    except Exception as e:
        emit('error', {'message': f'Cache retrieval error: {str(e)}'})

@socketio.on('cache_historical_data')
def handle_cache_historical_data(data):
    """Cache historical data in Redis."""
    global redis_integration
    
    try:
        asset = data.get('asset')
        timeframe = data.get('timeframe', '1M')
        candles_data = data.get('data', [])
        
        if not asset or not candles_data:
            emit('error', {'message': 'Invalid cache request'})
            return
        
        # Cache data in Redis
        if redis_integration.cache_historical_candles(asset, timeframe, candles_data):
            emit('historical_data_cached', {
                'asset': asset,
                'timeframe': timeframe,
                'count': len(candles_data)
            })
        else:
            emit('error', {'message': 'Failed to cache historical data'})
            
    except Exception as e:
        emit('error', {'message': f'Cache storage error: {str(e)}'})

@socketio.on('clear_cached_historical_data')
def handle_clear_cached_historical_data(data):
    """Clear cached historical data for an asset."""
    global redis_integration
    
    try:
        asset = data.get('asset')
        timeframe = data.get('timeframe', '1M')
        
        if not asset:
            emit('error', {'message': 'No asset specified'})
            return
        
        # Clear specific cache key
        cache_key = f"historical:{asset}:{timeframe}"
        redis_integration.redis_client.delete(cache_key)
        
        emit('historical_data_cache_cleared', {
            'asset': asset,
            'timeframe': timeframe
        })
        
    except Exception as e:
        emit('error', {'message': f'Cache clear error: {str(e)}'})

@socketio.on('get_redis_status')
def handle_get_redis_status():
    """Get Redis server status and statistics."""
    global redis_integration, batch_processor
    
    try:
        redis_info = redis_integration.get_redis_info()
        batch_status = batch_processor.get_processing_status() if batch_processor else {}
        
        emit('redis_status', {
            'connected': True,
            'redis_info': redis_info,
            'batch_status': batch_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        emit('redis_status', {
            'connected': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

# Modify handle_start_stream function
@socketio.on('start_stream')
def handle_start_stream(data):
    """Start streaming with Redis integration."""
    global current_asset, streaming_active, data_streamer, chrome_reconnect_enabled, batch_processor
    
    # Existing logic for asset and streaming setup
    if data and 'asset' in data:
        current_asset = data['asset']
        
        # Register asset for batch processing
        if batch_processor:
            batch_processor.register_asset(current_asset)
        
        # Existing streaming logic...
        if is_simulated_mode_global:
            data_streamer.start_streaming([current_asset])
        else:
            chrome_reconnect_enabled = True
            if not chrome_driver:
                emit('stream_error', {
                    'error': 'Chrome not connected',
                    'timestamp': datetime.now().isoformat()
                })
                return
            data_streamer.set_asset_focus(current_asset)
            data_streamer.set_timeframe(minutes=1, lock=True)
    
    streaming_active = True
    
    print(f"[Stream] Started for {current_asset}")
    emit('stream_started', {
        'asset': current_asset,
        'timestamp': datetime.now().isoformat()
    })
    
    # Existing historical candle loading logic...
    # (Keep the existing historical candle loading code)

# Modify handle_stop_stream function
@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop streaming and clean up Redis resources."""
    global streaming_active, current_asset, batch_processor

    streaming_active = False
    
    # Unregister asset from batch processing
    if batch_processor and current_asset:
        batch_processor.unregister_asset(current_asset)
    
    print(f"[Stream] Stopped")
    emit('stream_stopped', {'timestamp': datetime.now().isoformat()})
    
    # Existing cleanup logic...
    if is_simulated_mode_global:
        data_streamer.stop_streaming(current_asset)
    else:
        data_streamer.release_asset_focus()
        data_streamer.unlock_timeframe()

# Update main function to initialize Redis
if __name__ == '__main__':
    # Existing argument parsing and setup...
    
    # Initialize Redis integration
    if not initialize_redis():
        print("[Startup] ⚠️ Redis integration failed - continuing without Redis")
    
    # Existing startup logic...
    print(f"\n[Startup] Starting server on http://0.0.0.0:3001")
    print("=" * 60)
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=3001,
        debug=False,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
        log_output=False
    )
```

## Phase 5: Testing and Validation

### 5.1 Create Test Suite

Create `tests/test_redis_integration.py`:
```python
#!/usr/bin/env python3
"""
Test Suite for Redis Integration in QuFLX Trading Platform
"""

import pytest
import time
import json
from unittest.mock import Mock, patch
from capabilities.redis_integration import RedisIntegration
from capabilities.redis_batch_processor import RedisBatchProcessor

class TestRedisIntegration:
    """Test cases for Redis integration module."""
    
    @pytest.fixture
    def redis_client(self):
        """Create Redis integration client for testing."""
        with patch('capabilities.redis_integration.redis.Redis') as mock_redis:
            mock_instance = Mock()
            mock_redis.return_value = mock_instance
            
            # Mock successful connection
            mock_instance.ping.return_value = True
            mock_instance.pubsub.return_value = Mock()
            
            client = RedisIntegration()
            return client, mock_instance
    
    def test_redis_connection(self, redis_client):
        """Test Redis connection establishment."""
        client, mock_redis = redis_client
        assert client.redis_client is not None
        assert client.pubsub is not None
        mock_redis.ping.assert_called_once()
    
    def test_add_tick_to_buffer(self, redis_client):
        """Test adding tick data to Redis buffer."""
        client, mock_redis = redis_client
        
        tick_data = {
            'asset': 'EURUSD_otc',
            'price': 1.0823,
            'timestamp': int(time.time())
        }
        
        # Mock Redis operations
        mock_redis.pipeline.return_value.execute.return_value = None
        mock_redis.publish.return_value = None
        
        result = client.add_tick_to_buffer('EURUSD_otc', tick_data)
        
        assert result is True
        mock_redis.pipeline.assert_called_once()
        mock_redis.publish.assert_called_once()
    
    def test_cache_historical_candles(self, redis_client):
        """Test caching historical candle data."""
        client, mock_redis = redis_client
        
        candles = [
            {'timestamp': 1000, 'open': 1.08, 'close': 1.082, 'high': 1.083, 'low': 1.079},
            {'timestamp': 2000, 'open': 1.082, 'close': 1.084, 'high': 1.085, 'low': 1.081}
        ]
        
        mock_redis.setex.return_value = True
        
        result = client.cache_historical_candles('EURUSD_otc', '1M', candles)
        
        assert result is True
        mock_redis.setex.assert_called_once()
    
    def test_get_cached_historical_candles_hit(self, redis_client):
        """Test getting cached historical candles (cache hit)."""
        client, mock_redis = redis_client
        
        candles_json = json.dumps([
            {'timestamp': 1000, 'open': 1.08, 'close': 1.082, 'high': 1.083, 'low': 1.079}
        ])
        
        mock_redis.get.return_value = candles_json
        
        result = client.get_cached_historical_candles('EURUSD_otc', '1M')
        
        assert result is not None
        assert len(result) == 1
        assert result[0]['timestamp'] == 1000
    
    def test_get_cached_historical_candles_miss(self, redis_client):
        """Test getting cached historical candles (cache miss)."""
        client, mock_redis = redis_client
        
        mock_redis.get.return_value = None
        
        result = client.get_cached_historical_candles('EURUSD_otc', '1M')
        
        assert result is None

class TestRedisBatchProcessor:
    """Test cases for Redis batch processor."""
    
    @pytest.fixture
    def batch_processor(self):
        """Create batch processor for testing."""
        mock_redis = Mock()
        mock_supabase = Mock()
        
        processor = RedisBatchProcessor(mock_redis)
        processor.supabase_client = mock_supabase
        
        return processor, mock_redis, mock_supabase
    
    def test_register_asset(self, batch_processor):
        """Test registering an asset for batch processing."""
        processor, _, _ = batch_processor
        
        processor.register_asset('EURUSD_otc')
        
        assert 'EURUSD_otc' in processor.active_assets
    
    def test_unregister_asset(self, batch_processor):
        """Test unregistering an asset from batch processing."""
        processor, _, _ = batch_processor
        
        processor.register_asset('EURUSD_otc')
        processor.unregister_asset('EURUSD_otc')
        
        assert 'EURUSD_otc' not in processor.active_assets
    
    def test_convert_ticks_to_supabase_format(self, batch_processor):
        """Test converting tick data to Supabase format."""
        processor, _, _ = batch_processor
        
        ticks = [
            {'price': 1.0823, 'timestamp': 1000},
            {'price': 1.0825, 'timestamp': 2000}
        ]
        
        records = processor._convert_ticks_to_supabase_format('EURUSD_otc', ticks)
        
        assert len(records) == 2
        assert records[0]['pair'] == 'EURUSD_otc'
        assert records[0]['price'] == 1.0823
        assert records[0]['timestamp'] == 1000

class TestPerformance:
    """Performance tests for Redis integration."""
    
    def test_tick_processing_latency(self):
        """Test tick processing latency under 1ms target."""
        client = RedisIntegration()
        
        tick_data = {
            'asset': 'EURUSD_otc',
            'price': 1.0823,
            'timestamp': int(time.time())
        }
        
        start_time = time.perf_counter()
        client.add_tick_to_buffer('EURUSD_otc', tick_data)
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 1.0, f"Latency {latency_ms}ms exceeds 1ms target"
    
    def test_cache_retrieval_latency(self):
        """Test cache retrieval latency under 1ms target."""
        client = RedisIntegration()
        
        start_time = time.perf_counter()
        client.get_cached_historical_candles('EURUSD_otc', '1M')
        end_time = time.perf_counter()
        
        latency_ms = (end_time - start_time) * 1000
        assert latency_ms < 1.0, f"Latency {latency_ms}ms exceeds 1ms target"

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

### 5.2 Frontend Testing

Create `gui/Data-Visualizer-React/src/tests/useDataStream.test.js`:
```javascript
import { renderHook, act } from '@testing-library/react';
import { useDataStream } from '../hooks/useDataStream';
import { parseTradingData } from '../utils/tradingData';

// Mock Socket.IO
const mockSocket = {
  on: jest.fn(),
  off: jest.fn(),
  emit: jest.fn()
};

describe('useDataStream with Redis Integration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('should handle Redis updates correctly', () => {
    const { result } = renderHook(() => useDataStream(mockSocket, {
      asset: 'EURUSD_otc'
    }));

    // Simulate Redis update
    const redisData = {
      asset: 'EURUSD_otc',
      timestamp: Date.now() / 1000,
      open: 1.0820,
      high: 1.0825,
      low: 1.0818,
      close: 1.0823,
      volume: 100
    };

    act(() => {
      // Simulate socket event
      const redisUpdateHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'redis_update'
      )?.[1];
      
      if (redisUpdateHandler) {
        redisUpdateHandler(redisData);
      }
    });

    expect(result.current.data.lastMessage).toEqual(redisData);
    expect(result.current.data.redisConnected).toBe(true);
  });

  test('should maintain buffer size limits', () => {
    const { result } = renderHook(() => useDataStream(mockSocket, {
      maxBufferSize: 5,
      asset: 'EURUSD_otc'
    }));

    // Add more candles than buffer size
    for (let i = 0; i < 10; i++) {
      act(() => {
        const redisUpdateHandler = mockSocket.on.mock.calls.find(
          call => call[0] === 'redis_update'
        )?.[1];
        
        if (redisUpdateHandler) {
          redisUpdateHandler({
            timestamp: Date.now() / 1000 + i,
            close: 1.0820 + i * 0.0001
          });
        }
      });
    }

    expect(result.current.data.chartData.length).toBeLessThanOrEqual(5);
  });

  test('should handle Redis connection status', () => {
    const { result } = renderHook(() => useDataStream(mockSocket));

    // Simulate Redis status update
    act(() => {
      const statusHandler = mockSocket.on.mock.calls.find(
        call => call[0] === 'redis_status'
      )?.[1];
      
      if (statusHandler) {
        statusHandler({ connected: true });
      }
    });

    expect(result.current.data.redisConnected).toBe(true);
  });
});
```

## Phase 6: Setup and Deployment

### 6.1 PowerShell Setup Script

Create `scripts/setup_redis.ps1`:
```powershell
# Redis Setup Script for QuFLX Trading Platform
# Windows PowerShell script for Redis installation and configuration

Write-Host "🚀 Setting up Redis for QuFLX Trading Platform..." -ForegroundColor Green

# Check if Redis is already installed
try {
    $redisVersion = redis-cli --version 2>$null
    if ($redisVersion) {
        Write-Host "✅ Redis is already installed: $redisVersion" -ForegroundColor Green
    } else {
        throw "Redis not found"
    }
} catch {
    Write-Host "📦 Installing Redis..." -ForegroundColor Yellow
    
    # Install Redis using winget
    winget install Redis-Redis --accept-package-agreements --accept-source-agreements
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Redis installed successfully" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to install Redis" -ForegroundColor Red
        exit 1
    }
}

# Start Redis service
Write-Host "🔄 Starting Redis service..." -ForegroundColor Yellow
try {
    Start-Service Redis -ErrorAction Stop
    Write-Host "✅ Redis service started" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Redis service may already be running" -ForegroundColor Yellow
}

# Test Redis connection
Write-Host "🔍 Testing Redis connection..." -ForegroundColor Yellow
try {
    $pong = redis-cli ping
    if ($pong -eq "PONG") {
        Write-Host "✅ Redis connection successful" -ForegroundColor Green
    } else {
        Write-Host "❌ Redis connection failed" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Cannot connect to Redis" -ForegroundColor Red
    Write-Host "Please ensure Redis is installed and running" -ForegroundColor Yellow
    exit 1
}

# Install Python dependencies
Write-Host "📦 Installing Python dependencies..." -ForegroundColor Yellow
pip install redis redis-py

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}

# Install Node.js dependencies
Write-Host "📦 Installing Node.js dependencies..." -ForegroundColor Yellow
Set-Location gui/Data-Visualizer-React
npm install redis

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Node.js dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ Failed to install Node.js dependencies" -ForegroundColor Red
    exit 1
}

# Return to root directory
Set-Location ../../

Write-Host "🎉 Redis setup completed successfully!" -ForegroundColor Green
Write-Host "You can now start the QuFLX platform with Redis integration" -ForegroundColor Cyan
```

### 6.2 Environment Configuration

Create `.env.redis` file:
```bash
# Redis Configuration for QuFLX
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Redis Performance Settings
REDIS_CONNECTION_POOL_SIZE=10
REDIS_SOCKET_TIMEOUT=5
REDIS_RETRY_ATTEMPTS=3
REDIS_RETRY_DELAY=1

# Redis Data Settings
REDIS_MAX_TICK_BUFFER_SIZE=1000
REDIS_HISTORICAL_CACHE_TTL=3600
REDIS_BATCH_PROCESSING_INTERVAL=30
REDIS_HISTORICAL_CACHE_SIZE=200
```

### 6.3 Updated Package.json

Add Redis dependencies to `gui/Data-Visualizer-React/package.json`:
```json
{
  "dependencies": {
    "redis": "^4.6.10",
    "socket.io-client": "^4.8.1",
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "lightweight-charts": "^4.2.0"
  },
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "test": "vitest",
    "test:redis": "vitest src/tests/useDataStream.test.js"
  }
}
```

## Phase 7: Monitoring and Maintenance

### 7.1 Performance Monitoring

Create `scripts/monitor_redis_performance.py`:
```python
#!/usr/bin/env python3
"""
Redis Performance Monitoring Script for QuFLX Trading Platform
"""

import time
import json
from datetime import datetime
from capabilities.redis_integration import RedisIntegration

class RedisPerformanceMonitor:
    """Monitor Redis performance and health."""
    
    def __init__(self):
        self.redis_integration = RedisIntegration()
        self.metrics_history = []
    
    def collect_metrics(self):
        """Collect current Redis metrics."""
        try:
            start_time = time.perf_counter()
            
            # Get Redis info
            redis_info = self.redis_integration.get_redis_info()
            
            # Test operation latency
            test_start = time.perf_counter()
            self.redis_integration.redis_client.ping()
            ping_latency = (time.perf_counter() - test_start) * 1000
            
            # Test cache operation latency
            cache_start = time.perf_counter()
            self.redis_integration.get_cached_historical_candles('EURUSD_otc', '1M')
            cache_latency = (time.perf_counter() - cache_start) * 1000
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'ping_latency_ms': round(ping_latency, 3),
                'cache_latency_ms': round(cache_latency, 3),
                'used_memory': redis_info.get('used_memory', 'N/A'),
                'connected_clients': redis_info.get('connected_clients', 0),
                'keyspace_hits': redis_info.get('keyspace_hits', 0),
                'keyspace_misses': redis_info.get('keyspace_misses', 0),
                'total_commands': redis_info.get('total_commands_processed', 0)
            }
            
            self.metrics_history.append(metrics)
            
            # Keep only last 1000 metrics
            if len(self.metrics_history) > 1000:
                self.metrics_history = self.metrics_history[-1000:]
            
            return metrics
            
        except Exception as e:
            print(f"Error collecting metrics: {e}")
            return None
    
    def print_metrics(self, metrics):
        """Print current metrics in a formatted way."""
        if not metrics:
            return
        
        print(f"\n📊 Redis Performance Metrics - {metrics['timestamp']}")
        print("=" * 60)
        print(f"🏓 Ping Latency:     {metrics['ping_latency_ms']} ms")
        print(f"💾 Cache Latency:    {metrics['cache_latency_ms']} ms")
        print(f"🧠 Memory Usage:      {metrics['used_memory']}")
        print(f"👥 Connected Clients: {metrics['connected_clients']}")
        print(f"🎯 Keyspace Hits:     {metrics['keyspace_hits']}")
        print(f"❌ Keyspace Misses:   {metrics['keyspace_misses']}")
        print(f"📈 Total Commands:    {metrics['total_commands']}")
        
        # Performance alerts
        if metrics['ping_latency_ms'] > 1.0:
            print(f"⚠️  WARNING: High ping latency (>1ms)")
        
        if metrics['cache_latency_ms'] > 1.0:
            print(f"⚠️  WARNING: High cache latency (>1ms)")
        
        hit_ratio = 0
        if metrics['keyspace_hits'] + metrics['keyspace_misses'] > 0:
            hit_ratio = metrics['keyspace_hits'] / (metrics['keyspace_hits'] + metrics['keyspace_misses']) * 100
        
        if hit_ratio < 80:
            print(f"⚠️  WARNING: Low cache hit ratio ({hit_ratio:.1f}%)")
    
    def monitor_continuously(self, interval=30):
        """Monitor Redis performance continuously."""
        print(f"🔍 Starting Redis performance monitoring (interval: {interval}s)")
        print("Press Ctrl+C to stop monitoring")
        
        try:
            while True:
                metrics = self.collect_metrics()
                if metrics:
                    self.print_metrics(metrics)
                
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped")
    
    def export_metrics(self, filename='redis_metrics.json'):
        """Export metrics history to JSON file."""
        try:
            with open(filename, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)
            print(f"📄 Metrics exported to {filename}")
        except Exception as e:
            print(f"Error exporting metrics: {e}")

if __name__ == '__main__':
    monitor = RedisPerformanceMonitor()
    
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'export':
        monitor.export_metrics()
    else:
        monitor.monitor_continuously()
```

### 7.2 Health Check Script

Create `scripts/redis_health_check.py`:
```python
#!/usr/bin/env python3
"""
Redis Health Check Script for QuFLX Trading Platform
"""

import sys
import time
from capabilities.redis_integration import RedisIntegration
from capabilities.redis_batch_processor import RedisBatchProcessor

def check_redis_health():
    """Perform comprehensive Redis health check."""
    print("🔍 Performing Redis Health Check...")
    print("=" * 50)
    
    health_status = {
        'redis_connection': False,
        'pub_sub_functionality': False,
        'cache_operations': False,
        'batch_processor': False,
        'overall_status': 'UNHEALTHY'
    }
    
    try:
        # Test Redis connection
        redis_integration = RedisIntegration()
        health_status['redis_connection'] = True
        print("✅ Redis Connection: OK")
        
        # Test cache operations
        test_data = [{'timestamp': int(time.time()), 'close': 1.0823}]
        if redis_integration.cache_historical_candles('EURUSD_otc', '1M', test_data):
            cached_data = redis_integration.get_cached_historical_candles('EURUSD_otc', '1M')
            if cached_data:
                health_status['cache_operations'] = True
                print("✅ Cache Operations: OK")
            else:
                print("❌ Cache Operations: FAILED")
        else:
            print("❌ Cache Operations: FAILED")
        
        # Test pub/sub functionality
        test_received = False
        def test_callback(message):
            nonlocal test_received
            test_received = True
        
        if redis_integration.subscribe_to_asset_updates('EURUSD_otc', test_callback):
            # Publish test message
            redis_integration.add_tick_to_buffer('EURUSD_otc', {
                'timestamp': int(time.time()),
                'close': 1.0823
            })
            
            # Wait for message
            time.sleep(0.1)
            
            if test_received:
                health_status['pub_sub_functionality'] = True
                print("✅ Pub/Sub Functionality: OK")
            else:
                print("❌ Pub/Sub Functionality: FAILED")
        else:
            print("❌ Pub/Sub Functionality: FAILED")
        
        # Test batch processor
        batch_processor = RedisBatchProcessor(redis_integration)
        batch_processor.register_asset('EURUSD_otc')
        
        if batch_processor.get_processing_status()['is_running']:
            health_status['batch_processor'] = True
            print("✅ Batch Processor: OK")
        else:
            print("❌ Batch Processor: FAILED")
        
        # Determine overall status
        if all(health_status.values()):
            health_status['overall_status'] = 'HEALTHY'
            print("\n🎉 Overall Redis Status: HEALTHY")
        else:
            failed_checks = [k for k, v in health_status.items() if not v and k != 'overall_status']
            print(f"\n⚠️  Overall Redis Status: UNHEALTHY")
            print(f"Failed checks: {', '.join(failed_checks)}")
        
        # Cleanup
        batch_processor.stop_processing()
        redis_integration.close()
        
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        health_status['overall_status'] = 'ERROR'
    
    return health_status

if __name__ == '__main__':
    status = check_redis_health()
    
    # Exit with appropriate code
    if status['overall_status'] == 'HEALTHY':
        sys.exit(0)
    else:
        sys.exit(1)
```

## Phase 8: Documentation and README

### 8.1 Updated README.md

Create comprehensive documentation in `README_Redis_Integration.md`:
```markdown
# QuFLX Trading Platform with Redis Integration

## Overview

This document describes the QuFLX trading platform with Redis integration for high-performance real-time data streaming and historical data caching.

## Features

### Real-Time Data Streaming
- **Redis Pub/Sub**: Sub-millisecond latency for tick updates
- **Efficient Buffering**: O(log n) insertion with 1000-tick capacity
- **Multi-Asset Support**: Concurrent streaming for multiple currency pairs
- **Automatic Fallback**: Graceful degradation if Redis is unavailable

### Historical Data Caching
- **Redis Cache**: 1-hour TTL for frequently accessed historical data
- **Smart Caching**: Cache hit ratio >80% for optimal performance
- **Automatic Refresh**: Background cache updates and invalidation
- **Supabase Fallback**: Seamless fallback to persistent storage

### Batch Processing
- **30-Second Intervals**: Efficient batch processing to Supabase
- **Error Recovery**: Automatic retry logic with exponential backoff
- **Duplicate Prevention**: Intelligent duplicate detection and handling
- **Performance Monitoring**: Real-time metrics and alerting

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │     Redis       │    │   Supabase     │
│   (Chrome)     │───▶│   Pub/Sub       │───▶│  Historical     │
│                 │    │   + Cache       │    │    Ticks       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Streaming      │    │   Frontend      │    │   Analytics     │
│  Server        │    │   (React)       │    │   & Reports     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Performance Specifications

### Latency Targets
- **Redis Operations**: <1ms
- **End-to-End Latency**: <10ms
- **Chart Updates**: 60fps (16.67ms per frame)

### Throughput Targets
- **Tick Processing**: ~1000 ticks/minute
- **Batch Processing**: 30-second intervals
- **Cache Hit Ratio**: >80% for historical data

### Memory Management
- **Redis Lists**: Cap at 1000 ticks per asset
- **Redis Cache**: 200 candles per asset/timeframe
- **Frontend Buffer**: Maintain 1000-candle capacity

## Installation and Setup

### Prerequisites
- Windows 11 (or Windows 10 with latest updates)
- Node.js 18+ and npm
- Python 3.8+ and pip
- Redis Server 6.0+
- Supabase account and project

### Quick Start

1. **Install Redis**:
   ```powershell
   winget install Redis-Redis
   Start-Service Redis
   redis-cli ping  # Should return PONG
   ```

2. **Install Dependencies**:
   ```bash
   # Python dependencies
   pip install redis redis-py
   
   # Node.js dependencies
   cd gui/Data-Visualizer-React
   npm install redis
   ```

3. **Configure Environment**:
   ```bash
   cp .env.redis .env
   # Edit .env with your Redis and Supabase settings
   ```

4. **Start the Platform**:
   ```bash
   # Start backend
   python streaming_server.py
   
   # Start frontend (new terminal)
   cd gui/Data-Visualizer-React
   npm run dev
   ```

### Detailed Setup

For detailed setup instructions, see:
- `dev_docs/Redis_Integration_Architecture_Plan.md`
- `dev_docs/Redis_Implementation_Guide.md`
- `scripts/setup_redis.ps1`

## Usage

### Real-Time Streaming
1. Start the backend server with Redis integration
2. Open the frontend application
3. Select an asset (e.g., EURUSD_otc)
4. Click "Start Stream" to begin real-time data streaming
5. View live chart updates with <10ms latency

### Historical Data Analysis
1. Select "CSV" data source
2. Choose an asset and timeframe
3. Data is automatically cached in Redis for fast access
4. Subsequent loads use Redis cache (sub-50ms response time)

### Performance Monitoring
1. Run Redis performance monitor:
   ```bash
   python scripts/monitor_redis_performance.py
   ```
2. Check Redis health status:
   ```bash
   python scripts/redis_health_check.py
   ```

## Configuration

### Redis Settings
Edit `config/redis_config.py`:
```python
# Connection settings
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0

# Performance settings
MAX_TICK_BUFFER_SIZE = 1000
HISTORICAL_CACHE_TTL = 3600  # 1 hour
BATCH_PROCESSING_INTERVAL = 30  # seconds
```

### Frontend Settings
Edit `gui/Data-Visualizer-React/src/hooks/useDataStream.js`:
```javascript
const options = {
  maxBufferSize: 1000,
  processInterval: 100,
  asset: 'EURUSD_otc'
};
```

## Troubleshooting

### Common Issues

1. **Redis Connection Failed**:
   - Ensure Redis service is running: `Get-Service Redis`
   - Check Redis configuration: `redis-cli ping`
   - Verify firewall settings for port 6379

2. **High Latency**:
   - Check Redis memory usage: `redis-cli info memory`
   - Monitor network connectivity
   - Verify system resources (CPU, RAM)

3. **Cache Misses**:
   - Check cache TTL settings
   - Verify cache key patterns
   - Monitor cache hit ratio

### Performance Optimization

1. **Redis Configuration**:
   ```bash
   # Edit redis.conf
   maxmemory 256mb
   maxmemory-policy allkeys-lru
   ```

2. **System Optimization**:
   - Use SSD for Redis persistence
   - Allocate sufficient RAM
   - Optimize network configuration

## Development

### Running Tests
```bash
# Backend tests
python -m pytest tests/test_redis_integration.py -v

# Frontend tests
cd gui/Data-Visualizer-React
npm run test:redis
```

### Code Structure
```
capabilities/
├── redis_integration.py          # Redis client and operations
├── redis_batch_processor.py      # Batch processing logic
└── supabase_csv_ingestion.py   # Supabase integration

gui/Data-Visualizer-React/src/hooks/
├── useDataStream.js             # Enhanced with Redis pub/sub
└── useCsvData.js              # Enhanced with Redis caching

scripts/
├── setup_redis.ps1             # PowerShell setup script
├── monitor_redis_performance.py  # Performance monitoring
└── redis_health_check.py        # Health check utility
```

## Support and Maintenance

### Monitoring
- Use `monitor_redis_performance.py` for real-time metrics
- Check `redis_health_check.py` for system health
- Monitor Supabase for batch processing status

### Maintenance Tasks
- Weekly: Review Redis memory usage and performance metrics
- Monthly: Clean up old cache keys and optimize configuration
- Quarterly: Update Redis version and review security settings

### Backup and Recovery
- Redis: No persistence needed (data cached from Supabase)
- Supabase: Automatic backups and point-in-time recovery
- Configuration: Version control for all configuration files

## License and Support

This Redis integration is part of the QuFLX trading platform and follows the same licensing terms.

For support and questions:
- Review the documentation in `dev_docs/`
- Check the troubleshooting section above
- Monitor system health using provided scripts
```

## Conclusion

This comprehensive Redis integration provides the QuFLX trading platform with:

1. **High Performance**: Sub-millisecond latency for real-time data
2. **Scalability**: Support for multiple assets and future growth
3. **Reliability**: Robust error handling and automatic recovery
4. **Maintainability**: Clean, modular code with comprehensive documentation
5. **Monitoring**: Built-in performance monitoring and health checks

The implementation follows all key principles and provides a solid foundation for future enhancements while maintaining backward compatibility with existing systems.