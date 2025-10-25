# Redis MCP Setup Guide

## Issue Resolution

The Redis MCP server shows "No tools available" which indicates either:
1. The MCP server isn't properly installed
2. The Redis connection isn't working
3. The MCP server needs to be restarted

## Quick Fix Steps

### 1. Install Redis MCP Server

```bash
pip install mcp-server-redis
```

### 2. Verify Redis is Running

```bash
redis-cli ping
# Should return: PONG
```

If Redis isn't running:
```bash
# Windows
redis-server --daemonize yes --port 6379

# Linux/Mac
redis-server
```

### 3. Test MCP Server Directly

```bash
python -m mcp_server_redis --url redis://localhost:6379
```

### 4. Restart IDE/MCP Client

After fixing the connection, restart your IDE or MCP client to reload the configuration.

## Alternative: Use Our Demo Script

Since the MCP server might have issues, use our comprehensive demo script:

```bash
python scripts/redis_mcp_demo.py
```

This provides the same functionality without requiring MCP tools:
- ✅ Real-time Redis monitoring
- ✅ Buffer operations demonstration
- ✅ Cache management
- ✅ Performance analysis
- ✅ Pub/sub testing

## Manual Redis Operations

If MCP continues to have issues, you can manually interact with Redis:

### Check Redis Status
```python
import redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)
print(r.info())
```

### Monitor QuFLX Buffers
```python
# Check buffer sizes
assets = ['EURUSD_otc', 'GBPUSD_otc', 'USDJPY_otc']
for asset in assets:
    buffer_key = f"ticks:{asset}"
    size = r.llen(buffer_key)
    print(f"{asset}: {size} ticks")
```

### Check Cache Contents
```python
# Check historical data cache
cache_key = "historical:EURUSD_otc:1M"
cached_data = r.get(cache_key)
if cached_data:
    import json
    candles = json.loads(cached_data)
    print(f"Cached {len(candles)} candles")
```

## Configuration Verification

Your `.kilocode/mcp.json` should now look like:

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
        "-m",
        "mcp_server_redis",
        "--url",
        "redis://localhost:6379"
      ]
    }
  }
}
```

## Next Steps

1. **Install MCP Server**: `pip install mcp-server-redis`
2. **Start Redis**: `redis-server`
3. **Test Connection**: `redis-cli ping`
4. **Run Demo**: `python scripts/redis_mcp_demo.py`
5. **Restart IDE**: Reload MCP configuration

The demo script provides full Redis integration functionality even if MCP tools aren't available immediately.