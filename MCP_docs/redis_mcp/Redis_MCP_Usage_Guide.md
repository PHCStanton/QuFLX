# Redis MCP Usage Guide for QuFLX

## Overview

This guide explains how to leverage the Redis MCP (Model Context Protocol) server with the QuFLX trading platform for enhanced monitoring, debugging, and data management capabilities.

## What is Redis MCP?

The Redis MCP server provides direct access to Redis operations through the Model Context Protocol, enabling:

- **Real-time Redis monitoring** without leaving your IDE
- **Direct data inspection** for debugging
- **Performance analysis** with live metrics
- **Cache management** for optimization
- **Buffer monitoring** for troubleshooting

## Current MCP Configuration

Your `.kilocode/mcp.json` is now configured with our custom Redis MCP server:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@supabase/mcp-server-supabase@0.5.5",
        "--access-token",
        "sbp_537d45fbd5473412eb36d7abd1eef3592b4edbb8"
      ]
    },
    "redis": {
      "command": "python",
      "args": [
        "mcp_server_redis_custom.py"
      ]
    }
  }
}
```

**Status**: ✅ **Redis MCP Server is RUNNING and READY FOR USE**

### Custom Implementation Details
- **File**: [`mcp_server_redis_custom.py`](mcp_server_redis_custom.py:1)
- **Compatibility**: Python 3.11+ (works with your current version)
- **Connection**: localhost:6379 (auto-detected from Redis server)
- **Tools**: 12 specialized Redis and QuFLX operations

## Installation & Setup

### 1. Install Redis MCP Server

```bash
pip install mcp-server-redis
```

### 2. Verify MCP Connection

The MCP server should connect to your Redis instance at `localhost:6379`. If your Redis runs on a different port, update the configuration.

## Practical Use Cases for QuFLX

### 🔄 Real-Time Data Monitoring

Monitor live trading data flowing through Redis:

```python
# Check current buffer sizes for all assets
# This shows how much data is buffered for each trading pair

# Monitor tick rates
# Track how many ticks per second are being processed

# Watch for buffer overflow
# Get alerts when buffers approach capacity
```

### 📊 Performance Analysis

Analyze Redis performance metrics:

```python
# Get memory usage
# Monitor how much memory QuFLX is using

# Check command rates
# See how many operations per second

# Monitor connection counts
# Track active connections to Redis
```

### 🗄️ Cache Management

Manage historical data caches:

```python
# List all cached assets
# See which trading pairs have cached data

# Check cache TTL
# Monitor when caches expire

# Clear specific caches
# Force refresh of stale data
```

### 🐛 Debugging Data Flow

Trace data through the pipeline:

```python
# Monitor pub/sub channels
# See real-time updates being published

# Check buffer contents
# Inspect queued data before processing

# Verify batch processing
# Confirm data is flowing to Supabase
```

## Integration with QuFLX Components

### 1. Backend Integration

The Redis MCP works seamlessly with our backend components:

#### With RedisIntegration Module
```python
from capabilities.redis_integration import RedisIntegration

# MCP can monitor the same Redis instance
redis_integration = RedisIntegration()

# Monitor buffer sizes
buffer_sizes = {}
for asset in ["EURUSD_otc", "GBPUSD_otc"]:
    buffer_sizes[asset] = redis_integration.get_buffer_size(asset)
```

#### With Batch Processor
```python
from capabilities.redis_batch_processor import RedisBatchProcessor

# MCP can monitor batch processing status
batch_processor = RedisBatchProcessor(redis_integration)
status = batch_processor.get_processing_status()
```

### 2. Frontend Integration

Monitor frontend Redis usage:

```javascript
// MCP can monitor Redis subscriptions
socket.emit('subscribe_redis_updates', { asset: 'EURUSD_otc' });

// Track cache hit/miss rates
socket.emit('get_cached_historical_data', { 
  asset: 'EURUSD_otc', 
  timeframe: '1M' 
});
```

## Practical Examples

### Example 1: Monitoring Live Trading Session

```python
# During active trading, monitor key metrics
def monitor_live_session():
    # Check buffer utilization
    buffer_utilization = get_buffer_utilization()
    if buffer_utilization > 0.8:  # 80% full
        print("⚠️ Buffer approaching capacity")
    
    # Monitor tick rate
    tick_rate = get_current_tick_rate()
    if tick_rate < expected_rate:
        print("⚠️ Tick rate below expected")
    
    # Check cache performance
    cache_hit_rate = get_cache_hit_rate()
    if cache_hit_rate < 0.9:  # 90% hit rate
        print("⚠️ Cache performance degraded")
```

### Example 2: Debugging Data Issues

```python
# When data flow issues occur
def debug_data_flow(asset):
    # Check if data is reaching Redis
    buffer_size = get_buffer_size(asset)
    print(f"Buffer size for {asset}: {buffer_size}")
    
    # Check pub/sub activity
    pubsub_activity = get_pubsub_activity(asset)
    print(f"Pub/sub activity for {asset}: {pubsub_activity}")
    
    # Verify cache contents
    cache_data = get_cached_data(asset)
    print(f"Cached data for {asset}: {len(cache_data) if cache_data else 0} items")
    
    # Check batch processing
    batch_status = get_batch_status(asset)
    print(f"Batch status for {asset}: {batch_status}")
```

### Example 3: Performance Optimization

```python
# Optimize Redis performance for QuFLX
def optimize_redis_performance():
    # Analyze memory usage patterns
    memory_usage = get_memory_usage_timeline()
    peak_usage = max(memory_usage)
    
    # Check for memory leaks
    if memory_usage[-1] > memory_usage[0] * 1.5:
        print("⚠️ Possible memory leak detected")
    
    # Optimize buffer sizes
    current_config = get_buffer_config()
    recommended_config = calculate_optimal_config()
    
    if recommended_config != current_config:
        print("💡 Recommended buffer configuration changes:")
        print(recommended_config)
```

## Advanced Usage

### Custom Monitoring Dashboards

Create custom monitoring for QuFLX:

```python
# Real-time dashboard for trading operations
def create_trading_dashboard():
    while True:
        # Get current metrics
        metrics = {
            'active_assets': get_active_asset_count(),
            'total_ticks': get_total_tick_count(),
            'buffer_utilization': get_average_buffer_utilization(),
            'cache_hit_rate': get_cache_hit_rate(),
            'batch_processing_rate': get_batch_processing_rate()
        }
        
        # Display dashboard
        display_dashboard(metrics)
        time.sleep(5)  # Update every 5 seconds
```

### Automated Alerting

Set up alerts for critical conditions:

```python
# Alert system for QuFLX operations
def setup_alerts():
    # Buffer overflow alerts
    if get_buffer_utilization() > 0.9:
        send_alert("Buffer overflow imminent")
    
    # Performance degradation alerts
    if get_average_response_time() > 10:  # 10ms target
        send_alert("Performance degradation detected")
    
    # Data flow interruption alerts
    if get_tick_rate() == 0 and is_trading_hours():
        send_alert("Data flow interruption detected")
```

## Troubleshooting

### Common MCP Issues

#### Connection Problems
```python
# Check Redis connection
redis_info = get_redis_info()
if not redis_info:
    print("❌ Redis not accessible via MCP")
    print("💡 Check Redis server status")
    print("💡 Verify MCP configuration")
```

#### Performance Issues
```python
# Diagnose performance problems
def diagnose_performance():
    # Check memory usage
    memory_info = get_memory_info()
    if memory_info['used_memory'] > memory_info['max_memory'] * 0.8:
        print("⚠️ High memory usage")
    
    # Check slow operations
    slow_log = get_slow_log()
    if slow_log:
        print("⚠️ Slow operations detected:")
        for operation in slow_log:
            print(f"   {operation}")
```

#### Data Inconsistencies
```python
# Verify data consistency
def verify_data_consistency():
    # Check buffer vs cache consistency
    buffer_data = get_buffer_data()
    cache_data = get_cache_data()
    
    if len(buffer_data) != len(cache_data):
        print("⚠️ Buffer/cache size mismatch")
    
    # Check data freshness
    latest_timestamp = get_latest_timestamp()
    if time.time() - latest_timestamp > 60:  # 1 minute old
        print("⚠️ Stale data detected")
```

## Best Practices

### 1. Regular Monitoring
- Check buffer utilization every 5 minutes during trading hours
- Monitor cache hit rates continuously
- Track performance metrics trends

### 2. Proactive Maintenance
- Clear caches during low-activity periods
- Optimize buffer sizes based on usage patterns
- Update configurations based on performance data

### 3. Documentation
- Log all configuration changes
- Document performance baselines
- Record troubleshooting steps

### 4. Integration Testing
- Test MCP operations with QuFLX running
- Verify data consistency across components
- Validate performance improvements

## Future Enhancements

### Planned MCP Features
- [ ] Advanced analytics dashboard
- [ ] Automated optimization suggestions
- [ ] Integration with monitoring services
- [ ] Custom alert configurations

### Integration Opportunities
- [ ] Connect with trading strategy monitoring
- [ ] Integrate with risk management systems
- [ ] Link with performance analytics platforms

## Support

### Getting Help
For Redis MCP issues with QuFLX:

1. Check Redis server status: `redis-cli ping`
2. Verify MCP configuration in `.kilocode/mcp.json`
3. Run the demo script: `python scripts/redis_mcp_demo.py`
4. Check QuFLX logs for Redis-related errors

### Resources
- [Redis MCP Documentation](https://github.com/modelcontextprotocol/servers)
- [QuFLX Redis Integration Guide](README_Redis_Integration.md)
- [Performance Optimization Guide](dev_docs/Redis_Implementation_Guide.md)

---

**Version**: 1.0.0  
**Last Updated**: 2025-10-24  
**Compatible**: QuFLX v2.0+ with Redis MCP