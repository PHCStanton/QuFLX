#!/usr/bin/env python3
"""
Custom Redis MCP Server for QuFLX
Compatible with Python 3.11+
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence
import redis
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    LoggingLevel
)

# Redis configuration
REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0

class RedisMCPServer:
    """Custom Redis MCP Server for QuFLX Integration"""
    
    def __init__(self):
        self.server = Server("redis-quflx")
        self.redis_client = None
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> List[Tool]:
            """List available Redis tools"""
            return [
                Tool(
                    name="redis_ping",
                    description="Test Redis connection",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="redis_get",
                    description="Get value from Redis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "Redis key"
                            }
                        },
                        "required": ["key"]
                    }
                ),
                Tool(
                    name="redis_set",
                    description="Set value in Redis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "Redis key"
                            },
                            "value": {
                                "type": "string",
                                "description": "Redis value"
                            },
                            "ttl": {
                                "type": "integer",
                                "description": "Time to live in seconds (optional)"
                            }
                        },
                        "required": ["key", "value"]
                    }
                ),
                Tool(
                    name="redis_del",
                    description="Delete key from Redis",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "Redis key"
                            }
                        },
                        "required": ["key"]
                    }
                ),
                Tool(
                    name="redis_keys",
                    description="List Redis keys matching pattern",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "pattern": {
                                "type": "string",
                                "description": "Key pattern (default: *)",
                                "default": "*"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="redis_info",
                    description="Get Redis server information",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "section": {
                                "type": "string",
                                "description": "Specific info section (optional)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="redis_llen",
                    description="Get length of Redis list",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "List key"
                            }
                        },
                        "required": ["key"]
                    }
                ),
                Tool(
                    name="redis_lrange",
                    description="Get range of elements from Redis list",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "List key"
                            },
                            "start": {
                                "type": "integer",
                                "description": "Start index (default: 0)",
                                "default": 0
                            },
                            "stop": {
                                "type": "integer",
                                "description": "Stop index (default: -1)",
                                "default": -1
                            }
                        },
                        "required": ["key"]
                    }
                ),
                Tool(
                    name="redis_lpush",
                    description="Push element to front of Redis list",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "List key"
                            },
                            "value": {
                                "type": "string",
                                "description": "Value to push"
                            }
                        },
                        "required": ["key", "value"]
                    }
                ),
                Tool(
                    name="redis_ltrim",
                    description="Trim Redis list to specified range",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "description": "List key"
                            },
                            "start": {
                                "type": "integer",
                                "description": "Start index"
                            },
                            "stop": {
                                "type": "integer",
                                "description": "Stop index"
                            }
                        },
                        "required": ["key", "start", "stop"]
                    }
                ),
                Tool(
                    name="quflx_monitor_buffers",
                    description="Monitor QuFLX trading data buffers",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "assets": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of assets to monitor (default: common assets)",
                                "default": ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="quflx_monitor_cache",
                    description="Monitor QuFLX historical data cache",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "asset": {
                                "type": "string",
                                "description": "Asset to monitor (optional)"
                            },
                            "timeframe": {
                                "type": "string",
                                "description": "Timeframe to monitor (optional)"
                            }
                        },
                        "required": []
                    }
                ),
                Tool(
                    name="quflx_get_performance_metrics",
                    description="Get QuFLX Redis performance metrics",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
            """Handle tool calls"""
            try:
                if not self.redis_client:
                    self.redis_client = redis.Redis(
                        host=REDIS_HOST, 
                        port=REDIS_PORT, 
                        db=REDIS_DB,
                        decode_responses=True
                    )
                
                if name == "redis_ping":
                    result = self.redis_client.ping()
                    return [TextContent(type="text", text=f"PONG: {result}")]
                
                elif name == "redis_get":
                    key = arguments["key"]
                    value = self.redis_client.get(key)
                    return [TextContent(type="text", text=f"GET {key}: {value}")]
                
                elif name == "redis_set":
                    key = arguments["key"]
                    value = arguments["value"]
                    ttl = arguments.get("ttl")
                    
                    if ttl:
                        result = self.redis_client.setex(key, ttl, value)
                    else:
                        result = self.redis_client.set(key, value)
                    
                    return [TextContent(type="text", text=f"SET {key}: {result}")]
                
                elif name == "redis_del":
                    key = arguments["key"]
                    result = self.redis_client.delete(key)
                    return [TextContent(type="text", text=f"DEL {key}: {result} keys deleted")]
                
                elif name == "redis_keys":
                    pattern = arguments.get("pattern", "*")
                    keys = self.redis_client.keys(pattern)
                    return [TextContent(type="text", text=f"KEYS {pattern}: {keys}")]
                
                elif name == "redis_info":
                    section = arguments.get("section")
                    info = self.redis_client.info(section)
                    return [TextContent(type="text", text=f"INFO{f' {section}' if section else ''}:\n{json.dumps(info, indent=2)}")]
                
                elif name == "redis_llen":
                    key = arguments["key"]
                    length = self.redis_client.llen(key)
                    return [TextContent(type="text", text=f"LLEN {key}: {length} elements")]
                
                elif name == "redis_lrange":
                    key = arguments["key"]
                    start = arguments.get("start", 0)
                    stop = arguments.get("stop", -1)
                    elements = self.redis_client.lrange(key, start, stop)
                    return [TextContent(type="text", text=f"LRANGE {key} {start} {stop}:\n{json.dumps(elements, indent=2)}")]
                
                elif name == "redis_lpush":
                    key = arguments["key"]
                    value = arguments["value"]
                    result = self.redis_client.lpush(key, value)
                    return [TextContent(type="text", text=f"LPUSH {key} {value}: {result} elements in list")]
                
                elif name == "redis_ltrim":
                    key = arguments["key"]
                    start = arguments["start"]
                    stop = arguments["stop"]
                    result = self.redis_client.ltrim(key, start, stop)
                    return [TextContent(type="text", text=f"LTRIM {key} {start} {stop}: {result}")]
                
                elif name == "quflx_monitor_buffers":
                    assets = arguments.get("assets", ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"])
                    buffer_info = {}
                    
                    for asset in assets:
                        buffer_key = f"ticks:{asset}"
                        size = self.redis_client.llen(buffer_key)
                        buffer_info[asset] = {
                            "buffer_key": buffer_key,
                            "size": size,
                            "status": "active" if size > 0 else "empty"
                        }
                    
                    return [TextContent(type="text", text=f"QuFLX Buffer Monitor:\n{json.dumps(buffer_info, indent=2)}")]
                
                elif name == "quflx_monitor_cache":
                    asset = arguments.get("asset")
                    timeframe = arguments.get("timeframe")
                    
                    # Find cache keys
                    cache_pattern = "historical:*"
                    if asset:
                        cache_pattern = f"historical:{asset}"
                    if timeframe:
                        cache_pattern += f":{timeframe}"
                    
                    cache_keys = self.redis_client.keys(cache_pattern)
                    cache_info = {}
                    
                    for key in cache_keys:
                        ttl = self.redis_client.ttl(key)
                        cache_info[key] = {
                            "ttl": ttl,
                            "status": "fresh" if ttl > 300 else "expiring" if ttl > 0 else "expired"
                        }
                    
                    return [TextContent(type="text", text=f"QuFLX Cache Monitor:\n{json.dumps(cache_info, indent=2)}")]
                
                elif name == "quflx_get_performance_metrics":
                    info = self.redis_client.info()
                    
                    # Calculate QuFLX-specific metrics
                    tick_keys = self.redis_client.keys("ticks:*")
                    cache_keys = self.redis_client.keys("historical:*")
                    
                    metrics = {
                        "redis_memory": info.get("used_memory_human"),
                        "redis_connected_clients": info.get("connected_clients"),
                        "redis_commands_processed": info.get("total_commands_processed"),
                        "quflx_active_buffers": len(tick_keys),
                        "quflx_cached_datasets": len(cache_keys),
                        "quflx_total_buffered_ticks": sum(self.redis_client.llen(key) for key in tick_keys)
                    }
                    
                    return [TextContent(type="text", text=f"QuFLX Performance Metrics:\n{json.dumps(metrics, indent=2)}")]
                
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
                    
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]
    
    async def run(self):
        """Run the MCP server"""
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="redis-quflx",
                    server_version="1.0.0",
                    capabilities=self.server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )

async def main():
    """Main entry point"""
    server = RedisMCPServer()
    await server.run()

if __name__ == "__main__":
    asyncio.run(main())