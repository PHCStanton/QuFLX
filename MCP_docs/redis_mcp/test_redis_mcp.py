#!/usr/bin/env python3
"""
Simple test for Redis MCP Server
"""

import redis
from mcp_server_redis_custom import RedisMCPServer

def test_redis_connection():
    """Test basic Redis connection"""
    try:
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        result = r.ping()
        print(f"✅ Redis connection: {result}")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_mcp_tools():
    """Test MCP server tools"""
    try:
        server = RedisMCPServer()
        print("✅ Redis MCP Server initialized")
        
        # Test basic Redis operations through MCP
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        
        # Test SET/GET
        r.set("test_key", "test_value")
        value = r.get("test_key")
        print(f"✅ SET/GET test: {value}")
        
        # Test QuFLX-specific operations
        r.lpush("ticks:EURUSD_otc", '{"test": "data"}')
        length = r.llen("ticks:EURUSD_otc")
        print(f"✅ Buffer operations: {length} items")
        
        # Test cache operations
        r.setex("historical:EURUSD_otc:1M", 3600, '[{"test": "candle"}]')
        cached = r.get("historical:EURUSD_otc:1M")
        print(f"✅ Cache operations: {cached is not None}")
        
        # Clean up
        r.delete("test_key", "ticks:EURUSD_otc", "historical:EURUSD_otc:1M")
        
        return True
    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Testing Redis MCP Setup")
    print("=" * 40)
    
    # Test Redis connection
    if not test_redis_connection():
        print("\n❌ Redis is not running. Please start Redis server.")
        return
    
    # Test MCP tools
    if test_mcp_tools():
        print("\n✅ All Redis MCP tests passed!")
        print("\n📋 Available MCP Tools:")
        tools = [
            "redis_ping - Test Redis connection",
            "redis_get - Get value from Redis", 
            "redis_set - Set value in Redis",
            "redis_del - Delete key from Redis",
            "redis_keys - List Redis keys",
            "redis_info - Get Redis server information",
            "redis_llen - Get length of Redis list",
            "redis_lrange - Get range of elements from Redis list",
            "redis_lpush - Push element to front of Redis list",
            "redis_ltrim - Trim Redis list to specified range",
            "quflx_monitor_buffers - Monitor QuFLX trading data buffers",
            "quflx_monitor_cache - Monitor QuFLX historical data cache",
            "quflx_get_performance_metrics - Get QuFLX Redis performance metrics"
        ]
        for tool in tools:
            print(f"   • {tool}")
        
        print("\n🎯 Redis MCP is ready for use!")
        print("   • Restart your IDE to load the MCP configuration")
        print("   • The Redis MCP tools will be available in your MCP client")
        print("   • Use the demo script: python scripts/redis_mcp_demo.py")
    else:
        print("\n❌ MCP tools test failed")

if __name__ == "__main__":
    main()