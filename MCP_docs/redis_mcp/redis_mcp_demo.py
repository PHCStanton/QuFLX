#!/usr/bin/env python3
"""
Redis MCP Demo for QuFLX Integration
Demonstrates how to use Redis MCP with our trading platform
"""

import json
import time
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, List

# Import our Redis integration
import sys
from pathlib import Path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from capabilities.redis_integration import RedisIntegration
from config.redis_config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    TICK_LIST_PATTERN, PUBSUB_CHANNEL_PATTERN, HISTORICAL_CACHE_PATTERN
)

class RedisMCPDemo:
    """Demonstrates Redis MCP usage with QuFLX"""
    
    def __init__(self):
        self.redis_integration = None
        try:
            self.redis_integration = RedisIntegration()
            print("✅ Redis integration initialized for MCP demo")
        except Exception as e:
            print(f"❌ Failed to initialize Redis: {e}")
    
    def simulate_trading_data(self, asset: str, duration_seconds: int = 60):
        """Simulate real-time trading data for demonstration"""
        print(f"\n🔄 Simulating {duration_seconds}s of {asset} trading data...")
        
        start_time = time.time()
        tick_count = 0
        
        while time.time() - start_time < duration_seconds:
            # Generate realistic tick data
            current_time = int(time.time())
            base_price = 1.0823 if "EURUSD" in asset else 1.2745
            price_variation = (hash(f"{asset}_{current_time}") % 100) / 10000
            price = base_price + price_variation
            
            tick_data = {
                'asset': asset,
                'timestamp': current_time,
                'open': price,
                'high': price + 0.0002,
                'low': price - 0.0002,
                'close': price,
                'volume': 100 + tick_count % 50
            }
            
            # Add to Redis buffer (includes pub/sub publishing)
            if self.redis_integration:
                self.redis_integration.add_tick_to_buffer(asset, tick_data)
            
            tick_count += 1
            time.sleep(0.1)  # 10 ticks per second
        
        print(f"✅ Generated {tick_count} ticks for {asset}")
        return tick_count
    
    def demonstrate_buffer_operations(self, asset: str):
        """Demonstrate Redis buffer operations"""
        print(f"\n📊 Demonstrating buffer operations for {asset}...")
        
        # Check buffer size
        buffer_size = self.redis_integration.get_buffer_size(asset)
        print(f"   Current buffer size: {buffer_size}")
        
        # Get ticks from buffer
        ticks = self.redis_integration.get_ticks_from_buffer(asset)
        print(f"   Retrieved {len(ticks)} ticks from buffer")
        
        # Clear buffer using existing method
        tick_key = f"ticks:{asset}"
        self.redis_integration.redis_client.delete(tick_key)
        print(f"   Buffer cleared")
        
        return ticks
    
    def demonstrate_caching(self, asset: str, timeframe: str = "1M"):
        """Demonstrate historical data caching"""
        print(f"\n💾 Demonstrating caching for {asset} {timeframe}...")
        
        # Generate sample historical data
        candles_data = []
        base_timestamp = int(time.time()) - 3600  # 1 hour ago
        
        for i in range(50):
            timestamp = base_timestamp + i * 60  # 1 minute intervals
            base_price = 1.0823 if "EURUSD" in asset else 1.2745
            price_variation = (hash(f"{asset}_{timestamp}") % 100) / 10000
            price = base_price + price_variation
            
            candles_data.append({
                'timestamp': timestamp,
                'open': price,
                'high': price + 0.0005,
                'low': price - 0.0005,
                'close': price + (price_variation * 0.1),
                'volume': 100 + i % 200
            })
        
        # Cache data
        success = self.redis_integration.cache_historical_candles(asset, timeframe, candles_data)
        print(f"   Cached {len(candles_data)} candles: {'✅' if success else '❌'}")
        
        # Retrieve cached data
        cached_data = self.redis_integration.get_cached_historical_candles(asset, timeframe)
        print(f"   Retrieved {len(cached_data) if cached_data else 0} candles from cache")
        
        return candles_data
    
    def demonstrate_pub_sub(self, asset: str):
        """Demonstrate pub/sub functionality"""
        print(f"\n📡 Demonstrating pub/sub for {asset}...")
        
        received_messages = []
        
        def message_callback(message):
            data = json.loads(message['data'])
            received_messages.append(data)
            print(f"   📨 Received: {data['asset']} @ {data['close']}")
        
        # Subscribe to asset updates
        success = self.redis_integration.subscribe_to_asset_updates(asset, message_callback)
        print(f"   Subscribed to {asset} updates: {'✅' if success else '❌'}")
        
        # Publish some test messages
        for i in range(5):
            test_message = {
                'asset': asset,
                'timestamp': int(time.time()),
                'open': 1.0823 + i * 0.0001,
                'high': 1.0825 + i * 0.0001,
                'low': 1.0821 + i * 0.0001,
                'close': 1.0824 + i * 0.0001,
                'volume': 100 + i * 10
            }
            
            # Add tick to buffer (includes publishing)
            self.redis_integration.add_tick_to_buffer(asset, test_message)
            time.sleep(0.5)
        
        print(f"   Published 5 test messages, received {len(received_messages)}")
        return received_messages
    
    def demonstrate_performance_monitoring(self):
        """Demonstrate Redis performance monitoring"""
        print(f"\n📈 Demonstrating performance monitoring...")
        
        # Get Redis info
        redis_info = self.redis_integration.get_redis_info()
        print(f"   Redis version: {redis_info.get('redis_version', 'Unknown')}")
        print(f"   Memory usage: {redis_info.get('used_memory_human', 'Unknown')}")
        print(f"   Connected clients: {redis_info.get('connected_clients', 'Unknown')}")
        print(f"   Commands processed: {redis_info.get('total_commands_processed', 'Unknown')}")
        
        # Get buffer statistics (manual calculation)
        tick_keys = self.redis_integration.redis_client.keys("ticks:*")
        buffer_stats = {}
        for key in tick_keys:
            asset = key.replace("ticks:", "")
            buffer_stats[asset] = self.redis_integration.get_buffer_size(asset)
        print(f"   Buffer statistics: {buffer_stats}")
        
        return redis_info
    
    def demonstrate_batch_processing(self, asset: str):
        """Demonstrate batch processing to Supabase"""
        print(f"\n⚙️ Demonstrating batch processing for {asset}...")
        
        # Import batch processor
        from capabilities.redis_batch_processor import RedisBatchProcessor
        
        batch_processor = RedisBatchProcessor(self.redis_integration)
        
        # Register asset
        batch_processor.register_asset(asset)
        print(f"   Registered {asset} for batch processing")
        
        # Get processing status
        status = batch_processor.get_processing_status()
        print(f"   Processing status: {status}")
        
        # Process ticks manually
        batch_processor._process_asset_ticks(asset)
        print(f"   Processed ticks for {asset}")
        
        # Unregister asset
        batch_processor.unregister_asset(asset)
        print(f"   Unregistered {asset}")
        
        return status
    
    def run_complete_demo(self):
        """Run complete demonstration of Redis MCP capabilities"""
        print("🚀 Starting Redis MCP Demo for QuFLX Integration")
        print("=" * 60)
        
        assets = ["EURUSD_otc", "GBPUSD_otc", "USDJPY_otc"]
        
        for asset in assets:
            print(f"\n📍 Demonstrating {asset} operations...")
            
            # 1. Simulate trading data
            self.simulate_trading_data(asset, duration_seconds=10)
            
            # 2. Demonstrate buffer operations
            self.demonstrate_buffer_operations(asset)
            
            # 3. Demonstrate caching
            self.demonstrate_caching(asset)
            
            # 4. Demonstrate pub/sub
            self.demonstrate_pub_sub(asset)
            
            # 5. Demonstrate batch processing
            self.demonstrate_batch_processing(asset)
            
            time.sleep(2)  # Brief pause between assets
        
        # 6. Performance monitoring
        self.demonstrate_performance_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ Redis MCP Demo Complete!")
        print("\n💡 Key Takeaways:")
        print("   • Redis provides <1ms operations for real-time data")
        print("   • Pub/sub enables efficient data distribution")
        print("   • Caching reduces database load")
        print("   • Batch processing ensures data persistence")
        print("   • Performance monitoring enables optimization")
        print("\n🔗 Integration with QuFLX:")
        print("   • Use Redis MCP for real-time monitoring")
        print("   • Cache historical data for faster access")
        print("   • Monitor buffer sizes and performance")
        print("   • Debug data flow issues")

def main():
    """Main demonstration function"""
    demo = RedisMCPDemo()
    
    if demo.redis_integration:
        demo.run_complete_demo()
    else:
        print("❌ Cannot run demo - Redis not available")
        print("\n💡 To fix:")
        print("   1. Install Redis server")
        print("   2. Start Redis: redis-server")
        print("   3. Run this script again")

if __name__ == "__main__":
    main()