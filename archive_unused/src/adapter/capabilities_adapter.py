"""CapabilitiesAdapter - Integration layer between API-test-space capabilities and backend.

This adapter provides a clean interface to the proven capabilities while maintaining
compatibility with the existing backend architecture.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Add capabilities directory to path for capability imports
capabilities_dir = Path(__file__).parent.parent.parent / "capabilities"
if str(capabilities_dir) not in sys.path:
    sys.path.insert(0, str(capabilities_dir))

try:
    from capabilities.data_streaming import RealtimeDataStreaming
    from capabilities.base import Ctx, CapResult
    from capabilities.session_scan import SessionScan
    from capabilities.profile_scan import ProfileScan
    from capabilities.favorite_select import FavoriteSelect
    from capabilities.trade_click_cap import TradeClick
    from capabilities.signal_generation import SignalGeneration
    from capabilities.automated_trading import AutomatedTrading
    from capabilities.strategy_management import StrategyManagement
    from capabilities.ab_testing import ABTesting
except ImportError as e:
    print(f"Warning: Could not import capabilities: {e}")
    # Fallback imports or graceful degradation
    RealtimeDataStreaming = None
    Ctx = None


class CapabilitiesAdapter:
    """Adapter that wraps API-test-space capabilities for backend integration.
    
    This class provides:
    - Session attachment to existing Chrome instances
    - Real-time data streaming with multiple modes
    - Candle data access for backend endpoints
    - Optional trading operations
    """
    
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.ctx: Optional[Ctx] = None
        self.data_streaming: Optional[RealtimeDataStreaming] = None
        self.session_scan: Optional[Any] = None
        self.profile_scan: Optional[Any] = None
        self.favorite_select: Optional[Any] = None
        self.trade_click: Optional[Any] = None
        self.signal_generation: Optional[Any] = None
        self.automated_trading: Optional[Any] = None
        self.strategy_management: Optional[Any] = None
        self.ab_testing: Optional[Any] = None
        
        # State tracking
        self.is_connected = False
        self.is_streaming = False
        self.current_session_info: Optional[Dict[str, Any]] = None
        
        # Configuration
        self.artifacts_root = str(Path(__file__).parent.parent.parent / "Historical_Data" / "adapter_artifacts")
        self.debug = False
        self.verbose = True

        # Use workspace Chrome profile directory
        self.workspace_chrome_profile = Path(__file__).parent.parent.parent / "Chrome_profile"
        
        # Initialize capability classes if available
        self._initialize_capabilities()
    
    def _initialize_capabilities(self):
        """Initialize capability classes if they are available."""
        try:
            if RealtimeDataStreaming:
                self.data_streaming = RealtimeDataStreaming()
            if SessionScan:
                self.session_scan = SessionScan()
            if ProfileScan:
                self.profile_scan = ProfileScan()
            if FavoriteSelect:
                self.favorite_select = FavoriteSelect()
            if TradeClick:
                self.trade_click = TradeClick()
            if SignalGeneration:
                self.signal_generation = SignalGeneration()
            if AutomatedTrading:
                self.automated_trading = AutomatedTrading()
            if StrategyManagement:
                self.strategy_management = StrategyManagement()
            if ABTesting:
                self.ab_testing = ABTesting()

            if self.verbose:
                print("✅ Capabilities initialized successfully")
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Warning: Could not initialize some capabilities: {e}")
        
    def attach_to_existing_session(self, port: int = 9222, user_data_dir: Optional[str] = None) -> bool:
        """Attach to an existing Chrome session.

        Args:
            port: Chrome debugger port (default: 9222 for hybrid sessions)
            user_data_dir: Chrome user data directory path (defaults to workspace Chrome_profile)

        Returns:
            bool: True if attachment successful, False otherwise
        """
        try:
            if self.driver:
                self.disconnect()

            # Use workspace Chrome profile if not specified
            if user_data_dir is None:
                user_data_dir = str(self.workspace_chrome_profile)

            # Configure Chrome options for attachment to existing session
            chrome_options = Options()
            chrome_options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
            chrome_options.add_argument(f"--user-data-dir={user_data_dir}")

            # Enable performance logging for WebSocket interception
            # Note: When attaching to existing sessions, we use minimal options to avoid conflicts
            chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

            # Create driver instance
            self.driver = webdriver.Chrome(options=chrome_options)

            # Create context for capabilities
            self.ctx = Ctx(
                driver=self.driver,
                artifacts_root=self.artifacts_root,
                debug=self.debug,
                dry_run=False,
                verbose=self.verbose
            )

            # Initialize capabilities
            if RealtimeDataStreaming:
                self.data_streaming = RealtimeDataStreaming()

            # Test connection
            current_url = self.driver.current_url
            if "pocketoption" in current_url.lower():
                self.is_connected = True
                self.current_session_info = {
                    "port": port,
                    "user_data_dir": user_data_dir,
                    "url": current_url,
                    "attached_at": datetime.now().isoformat()
                }

                if self.verbose:
                    print(f"✅ Successfully attached to Chrome session at port {port}")
                    print(f"📍 Current URL: {current_url}")
                    print(f"📁 Using profile: {user_data_dir}")

                return True
            else:
                if self.verbose:
                    print(f"⚠️ Attached to Chrome but not on PocketOption (URL: {current_url})")
                    print(f"📁 Using profile: {user_data_dir}")
                return False

        except Exception as e:
            if self.verbose:
                print(f"❌ Failed to attach to Chrome session: {e}")
            self.is_connected = False
            return False
    
    def start_realtime_streaming(self, period: int = 1, stream_mode: str = "candle", 
                               asset_focus: bool = False) -> bool:
        """Start real-time data streaming.
        
        Args:
            period: Timeframe period in minutes
            stream_mode: Streaming mode ('candle', 'tick', 'both')
            asset_focus: Focus on currently selected asset only
            
        Returns:
            bool: True if streaming started successfully
        """
        if not self.is_connected or not self.data_streaming:
            if self.verbose:
                print("❌ Cannot start streaming: not connected or data_streaming not available")
            return False
            
        try:
            # Configure streaming mode
            self.data_streaming.PERIOD = period
            self.data_streaming.CANDLE_ONLY_MODE = stream_mode in ["candle", "both"]
            self.data_streaming.TICK_ONLY_MODE = stream_mode == "tick"
            self.data_streaming.ASSET_FOCUS_MODE = asset_focus
            self.data_streaming.TICK_DATA_MODE = stream_mode in ["tick", "both"]
            
            # Start streaming in background
            inputs = {"period": period}
            
            # Run initial setup
            result = self.data_streaming.run(self.ctx, inputs)
            
            if result.ok:
                self.is_streaming = True
                if self.verbose:
                    print(f"🚀 Started real-time streaming (mode: {stream_mode}, period: {period}m)")
                return True
            else:
                if self.verbose:
                    print(f"❌ Failed to start streaming: {result.error}")
                return False
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error starting streaming: {e}")
            return False
    
    def stop_realtime_streaming(self) -> bool:
        """Stop real-time data streaming.
        
        Returns:
            bool: True if stopped successfully
        """
        try:
            if self.data_streaming and self.is_streaming:
                # Save current data to CSV before stopping
                if hasattr(self.data_streaming, 'CANDLES'):
                    for asset in self.data_streaming.CANDLES:
                        if self.data_streaming.CANDLES[asset]:
                            self.data_streaming.save_to_csv(asset, self.ctx)
                            
                self.is_streaming = False
                if self.verbose:
                    print("⏹️ Stopped real-time streaming")
                return True
            return False
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error stopping streaming: {e}")
            return False
    
    def get_latest_candles(self, asset: str, count: int = 500) -> List[Dict[str, Any]]:
        """Get latest candle data for an asset.
        
        Args:
            asset: Asset symbol (e.g., 'EURUSD')
            count: Number of candles to return
            
        Returns:
            List of candle dictionaries with keys: timestamp, open, high, low, close
        """
        if not self.data_streaming or not hasattr(self.data_streaming, 'CANDLES'):
            return []
            
        try:
            candles_data = self.data_streaming.CANDLES.get(asset, [])
            
            # Convert to standardized format
            formatted_candles = []
            for candle in candles_data[-count:]:
                if len(candle) >= 5:
                    formatted_candles.append({
                        "timestamp": candle[0],
                        "open": candle[1],
                        "close": candle[2], 
                        "high": candle[3],
                        "low": candle[4],
                        "volume": candle[5] if len(candle) > 5 else 0
                    })
                    
            return formatted_candles
            
        except Exception as e:
            if self.verbose:
                print(f"❌ Error getting candles for {asset}: {e}")
            return []
    
    def get_available_assets(self) -> List[str]:
        """Get list of assets with available data.
        
        Returns:
            List of asset symbols
        """
        if not self.data_streaming or not hasattr(self.data_streaming, 'CANDLES'):
            return []
            
        return list(self.data_streaming.CANDLES.keys())
    
    def get_streaming_status(self) -> Dict[str, Any]:
        """Get current streaming status and statistics.
        
        Returns:
            Dictionary with status information
        """
        status = {
            "connected": self.is_connected,
            "streaming": self.is_streaming,
            "session_info": self.current_session_info,
            "available_assets": self.get_available_assets(),
            "capabilities": {
                "data_streaming": self.data_streaming is not None,
                "session_scan": self.session_scan is not None,
                "profile_scan": self.profile_scan is not None,
                "favorite_select": self.favorite_select is not None,
                "trade_click": self.trade_click is not None,
                "signal_generation": self.signal_generation is not None,
                "automated_trading": self.automated_trading is not None,
                "strategy_management": self.strategy_management is not None,
                "ab_testing": self.ab_testing is not None
            }
        }
        
        if self.data_streaming:
            status["streaming_config"] = {
                "period": getattr(self.data_streaming, 'PERIOD', None),
                "candle_only_mode": getattr(self.data_streaming, 'CANDLE_ONLY_MODE', False),
                "tick_only_mode": getattr(self.data_streaming, 'TICK_ONLY_MODE', False),
                "asset_focus_mode": getattr(self.data_streaming, 'ASSET_FOCUS_MODE', False)
            }
            
            # Add data statistics
            if hasattr(self.data_streaming, 'CANDLES'):
                asset_stats = {}
                for asset, candles in self.data_streaming.CANDLES.items():
                    asset_stats[asset] = {
                        "candle_count": len(candles),
                        "latest_timestamp": candles[-1][0] if candles else None
                    }
                status["asset_statistics"] = asset_stats
        
        return status
    
    def get_latest_data(self) -> Optional[List[Dict[str, Any]]]:
        """Get the latest real-time data from the streaming capability.
        
        Returns:
            List of latest data points or None if no data available
        """
        if not self.is_streaming or not self.data_streaming:
            return None
            
        try:
            # Get latest real-time updates
            latest_data = []
            
            # Get current asset prices if available
            if hasattr(self.data_streaming, 'current_asset_prices'):
                for asset, price_data in self.data_streaming.current_asset_prices.items():
                    if isinstance(price_data, dict):
                        data_point = {
                            "asset": asset,
                            "price": price_data.get('price'),
                            "timestamp": price_data.get('timestamp'),
                            "type": "price_update"
                        }
                        latest_data.append(data_point)
            
            # Get latest real-time asset data
            if hasattr(self.data_streaming, 'realtime_asset_data') and self.data_streaming.realtime_asset_data:
                # Get the last few updates (limit to avoid overwhelming)
                recent_updates = self.data_streaming.realtime_asset_data[-10:]
                for update in recent_updates:
                    if isinstance(update, dict):
                        update["type"] = "realtime_update"
                        latest_data.append(update)
            
            # Get latest candle data for current asset
            if hasattr(self.data_streaming, 'CANDLES') and hasattr(self.data_streaming, 'CURRENT_ASSET'):
                current_asset = self.data_streaming.CURRENT_ASSET
                if current_asset and current_asset in self.data_streaming.CANDLES:
                    candles = self.data_streaming.CANDLES[current_asset]
                    if candles:
                        # Get the latest candle
                        latest_candle = candles[-1]
                        candle_data = {
                            "asset": current_asset,
                            "timestamp": latest_candle[0],
                            "open": latest_candle[1],
                            "high": latest_candle[2], 
                            "low": latest_candle[3],
                            "close": latest_candle[4],
                            "type": "candle_update"
                        }
                        latest_data.append(candle_data)
            
            return latest_data if latest_data else None
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error getting latest data: {e}")
            return None
    
    def disconnect(self) -> None:
        """Disconnect from Chrome session and cleanup resources."""
        try:
            if self.is_streaming:
                self.stop_realtime_streaming()
                
            if self.driver:
                self.driver.quit()
                self.driver = None
                
            self.ctx = None
            self.data_streaming = None
            self.is_connected = False
            self.current_session_info = None
            
            if self.verbose:
                print("🔌 Disconnected from Chrome session")
                
        except Exception as e:
            if self.verbose:
                print(f"⚠️ Error during disconnect: {e}")
    
    def scan_profile(self) -> Dict[str, Any]:
        """Scan user profile and account information.
        
        Returns:
            Dict containing profile data including account type, balance, etc.
        """
        try:
            if not self.is_connected or not self.ctx:
                if self.verbose:
                    print("❌ Cannot scan profile: not connected")
                return {"error": "Not connected to Chrome session"}
            
            if not self.profile_scan:
                return {"error": "ProfileScan capability not available"}
            
            # Run profile scan
            result = self.profile_scan.run(self.ctx, {})
            
            if result.ok:
                if self.verbose:
                    print("✅ Profile scan completed successfully")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ Profile scan failed: {result.error}")
                return {"error": result.error}
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error scanning profile: {e}")
            return {"error": str(e)}
    
    def scan_favorites(self, min_pct: int = 92, select: Optional[str] = None) -> Dict[str, Any]:
        """Scan favorites bar for eligible assets.
        
        Args:
            min_pct: Minimum payout percentage (default 92)
            select: Optional selection preference ("first", "last", or None)
            
        Returns:
            Dict containing eligible assets and selection result
        """
        try:
            if not self.is_connected or not self.ctx:
                if self.verbose:
                    print("❌ Cannot scan favorites: not connected")
                return {"error": "Not connected to Chrome session"}
            
            if not self.favorite_select:
                return {"error": "FavoriteSelect capability not available"}
            
            # Run favorite select
            inputs = {"min_pct": min_pct}
            if select:
                inputs["select"] = select
                
            result = self.favorite_select.run(self.ctx, inputs)
            
            if result.ok:
                eligible_count = len(result.data.get('eligible', []))
                if self.verbose:
                    print(f"✅ Favorite scan completed: found {eligible_count} eligible assets")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ Favorite scan failed: {result.error}")
                return {"error": result.error}
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error scanning favorites: {e}")
            return {"error": str(e)}
    
    def execute_trade_click(self, side: str, timeout: int = 5, 
                           root: str = "#put-call-buttons-chart-1") -> Dict[str, Any]:
        """Execute a trade click (BUY/SELL).
        
        Args:
            side: Trade direction ("buy" or "sell")
            timeout: Click timeout in seconds (default 5)
            root: Root selector for trade buttons (default "#put-call-buttons-chart-1")
            
        Returns:
            Dict containing trade execution result and diagnostics
        """
        try:
            if not self.is_connected or not self.ctx:
                if self.verbose:
                    print("❌ Cannot execute trade: not connected")
                return {"error": "Not connected to Chrome session"}
            
            if not self.trade_click:
                return {"error": "TradeClick capability not available"}
            
            # Validate side parameter
            if side.lower() not in ["buy", "sell"]:
                return {"error": "Invalid side parameter. Must be 'buy' or 'sell'"}
            
            # Run trade click
            inputs = {
                "side": side.lower(),
                "timeout": timeout,
                "root": root
            }
            
            result = self.trade_click.run(self.ctx, inputs)
            
            if result.ok:
                if self.verbose:
                    print(f"✅ Trade click executed successfully: {side.upper()}")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ Trade click failed: {result.error}")
                return {"error": result.error}
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error executing trade click: {e}")
            return {"error": str(e)}
    
    def scan_session(self) -> Dict[str, Any]:
        """Scan current session for active trades and account status.
        
        Returns:
            Dict containing session data including active trades, balance, etc.
        """
        try:
            if not self.is_connected or not self.ctx:
                if self.verbose:
                    print("❌ Cannot scan session: not connected")
                return {"error": "Not connected to Chrome session"}
            
            if not self.session_scan:
                return {"error": "SessionScan capability not available"}
            
            # Run session scan
            result = self.session_scan.run(self.ctx, {})
            
            if result.ok:
                if self.verbose:
                    print("✅ Session scan completed successfully")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ Session scan failed: {result.error}")
                return {"error": result.error}
                
        except Exception as e:
            if self.verbose:
                print(f"❌ Error scanning session: {e}")
            return {"error": str(e)}
    
    def generate_signal(self, asset: str, min_candles: int = 30, signal_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Generate trading signal for an asset using real candle data."""
        try:
            if not self.is_connected or not self.ctx:
                if self.verbose:
                    print("❌ Cannot generate signal: not connected")
                return {"error": "Not connected to Chrome session"}

            if not self.signal_generation:
                return {"error": "SignalGeneration capability not available"}

            # Get real candle data from data streaming
            candles = self.get_latest_candles(asset, min_candles)

            if candles and len(candles) >= min_candles:
                # Convert candles to the format expected by signal generation
                candle_data = []
                for candle in candles:
                    # Convert from dict format to list format [timestamp, open, close, high, low]
                    candle_data.append([
                        candle.get("timestamp", 0),
                        candle.get("open", 0),
                        candle.get("close", 0),
                        candle.get("high", 0),
                        candle.get("low", 0)
                    ])

                # Run signal generation with real data
                inputs = {"asset": asset, "min_candles": min_candles, "real_candles": candle_data}
                if signal_types:
                    inputs["signal_types"] = signal_types

                result = self.signal_generation.run(self.ctx, inputs)

                if result.ok:
                    # Update the result to indicate real data was used
                    result.data["data_source"] = "real_time_data"
                    result.data["candles_analyzed"] = len(candle_data)
                    if self.verbose:
                        print(f"✅ Signal generated for {asset} using real candle data ({len(candle_data)} candles)")
                    return result.data
                else:
                    if self.verbose:
                        print(f"❌ Signal generation failed: {result.error}")
                    return {"error": result.error}
            else:
                # Fall back to mock signals if no real data available
                if self.verbose:
                    print(f"⚠️ No real candle data available for {asset}, using mock signals")

                inputs = {"asset": asset, "min_candles": min_candles}
                if signal_types:
                    inputs["signal_types"] = signal_types

                result = self.signal_generation.run(self.ctx, inputs)

                if result.ok:
                    if self.verbose:
                        print(f"✅ Mock signal generated for {asset}")
                    return result.data
                else:
                    if self.verbose:
                        print(f"❌ Signal generation failed: {result.error}")
                    return {"error": result.error}

        except Exception as e:
            if self.verbose:
                print(f"❌ Error generating signal for {asset}: {e}")
            return {"error": str(e)}

    def manage_automated_trading(self, action: str, strategy_id: Optional[str] = None,
                                assets: Optional[List[str]] = None,
                                risk_settings: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage automated trading operations."""
        try:
            if not self.is_connected or not self.ctx:
                if self.verbose:
                    print("❌ Cannot manage automated trading: not connected")
                return {"error": "Not connected to Chrome session"}

            if not self.automated_trading:
                return {"error": "AutomatedTrading capability not available"}

            # Run automated trading management
            inputs = {"action": action}
            if strategy_id:
                inputs["strategy_id"] = strategy_id
            if assets:
                inputs["assets"] = assets
            if risk_settings:
                inputs["risk_settings"] = risk_settings

            result = self.automated_trading.run(self.ctx, inputs)

            if result.ok:
                if self.verbose:
                    print(f"✅ Automated trading {action} completed")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ Automated trading {action} failed: {result.error}")
                return {"error": result.error}

        except Exception as e:
            if self.verbose:
                print(f"❌ Error managing automated trading: {e}")
            return {"error": str(e)}

    def manage_strategy(self, action: str, strategy_id: Optional[str] = None,
                         strategy_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage trading strategies."""
        try:
            if not self.strategy_management:
                return {"error": "StrategyManagement capability not available"}

            # Create a default context if none exists (for read-only operations)
            ctx = self.ctx
            if not ctx:
                # Create minimal context for read-only operations
                ctx = Ctx(
                    driver=None,
                    artifacts_root=self.artifacts_root,
                    debug=self.debug,
                    dry_run=False,
                    verbose=self.verbose
                )

            # Run strategy management
            inputs = {"action": action}
            if strategy_id:
                inputs["strategy_id"] = strategy_id
            if strategy_data:
                inputs["strategy_data"] = strategy_data

            result = self.strategy_management.run(ctx, inputs)

            if result.ok:
                if self.verbose:
                    print(f"✅ Strategy {action} completed")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ Strategy {action} failed: {result.error}")
                return {"error": result.error}

        except Exception as e:
            if self.verbose:
                print(f"❌ Error managing strategy: {e}")
            return {"error": str(e)}

    def manage_ab_testing(self, action: str, test_name: Optional[str] = None,
                         test_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Manage A/B testing operations."""
        try:
            if not self.ab_testing:
                return {"error": "ABTesting capability not available"}

            # Run A/B testing management
            inputs = {"action": action}
            if test_name:
                inputs["test_name"] = test_name
            if test_config:
                inputs.update(test_config)

            result = self.ab_testing.run(self.ctx, inputs)

            if result.ok:
                if self.verbose:
                    print(f"✅ A/B testing {action} completed")
                return result.data
            else:
                if self.verbose:
                    print(f"❌ A/B testing {action} failed: {result.error}")
                return {"error": result.error}

        except Exception as e:
            if self.verbose:
                print(f"❌ Error managing A/B testing: {e}")
            return {"error": str(e)}

    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status (alias for get_streaming_status for compatibility)."""
        streaming_status = self.get_streaming_status()
        return {
            "webdriver_connected": streaming_status.get("connected", False),
            "websocket_connected": streaming_status.get("streaming", False),
            "platform_logged_in": streaming_status.get("connected", False),
            "last_heartbeat": datetime.now()
        }

    def is_market_open(self) -> bool:
        """Check if market is open (simplified - always True for crypto)."""
        # For PocketOption, markets are typically always open for crypto
        # This could be enhanced to check actual market hours
        return True

    def execute_trade(self, direction: str, amount: float, asset: str, duration: int = 60) -> Dict[str, Any]:
        """Execute a trade (wrapper around execute_trade_click for compatibility)."""
        return self.execute_trade_click(
            side=direction.lower(),
            timeout=5,
            root="#put-call-buttons-chart-1"
        )

    def __del__(self):
        """Cleanup on object destruction."""
        try:
            self.disconnect()
        except:
            pass