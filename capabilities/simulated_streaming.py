"""
Simulated Data Streaming for Indicator Testing
===============================================

Generates realistic OHLC candlestick data for testing technical indicators
and visualizations WITHOUT connecting to real market data.

This module is ONLY used when explicitly enabled via configuration.
NO automatic fallback - must be intentionally selected.
"""

import random
import time
from datetime import datetime
from typing import List, Dict, Optional
import numpy as np


class SimulatedDataGenerator:
    """
    Generates realistic simulated OHLC candlestick data for testing.
    
    Features:
    - Configurable base price and volatility
    - Realistic price movements with trends
    - Random walk with momentum
    - Proper OHLC relationships (high >= open,close; low <= open,close)
    """
    
    def __init__(
        self, 
        base_price: float = 1.1000,
        volatility: float = 0.0005,  # 0.05% default volatility
        trend_strength: float = 0.3
    ):
        """
        Initialize simulated data generator.
        
        Args:
            base_price: Starting price for the asset
            volatility: Price volatility (standard deviation of returns)
            trend_strength: Strength of trending behavior (0-1)
        """
        self.base_price = base_price
        self.current_price = base_price
        self.volatility = volatility
        self.trend_strength = trend_strength
        self.trend_direction = random.choice([-1, 1])
        self.bars_in_trend = 0
        self.max_trend_length = random.randint(20, 50)
        
    def generate_candle(self, period_seconds: int = 60) -> List:
        """
        Generate a single OHLC candle.
        
        Args:
            period_seconds: Candle period in seconds
            
        Returns:
            [timestamp, open, close, high, low]
        """
        timestamp = int(time.time() * 1000)
        open_price = self.current_price
        
        # Generate price movement with trend
        if self.bars_in_trend >= self.max_trend_length:
            # Reverse trend
            self.trend_direction *= -1
            self.bars_in_trend = 0
            self.max_trend_length = random.randint(20, 50)
        
        # Calculate price change with trend and randomness
        trend_component = self.trend_direction * self.volatility * self.trend_strength
        random_component = random.gauss(0, self.volatility) * (1 - self.trend_strength)
        price_change = (trend_component + random_component) * open_price
        
        close_price = open_price + price_change
        
        # Generate high and low with realistic relationships
        intra_bar_range = abs(price_change) * random.uniform(1.5, 3.0)
        high_price = max(open_price, close_price) + intra_bar_range * random.random()
        low_price = min(open_price, close_price) - intra_bar_range * random.random()
        
        # Ensure OHLC relationships are valid
        high_price = max(high_price, open_price, close_price)
        low_price = min(low_price, open_price, close_price)
        
        # Update current price
        self.current_price = close_price
        self.bars_in_trend += 1
        
        return [timestamp, open_price, close_price, high_price, low_price]
    
    def generate_historical_candles(self, count: int = 200, period_seconds: int = 60) -> List[List]:
        """
        Generate historical candles for backtesting/initialization.
        
        Args:
            count: Number of historical candles to generate
            period_seconds: Period of each candle in seconds
            
        Returns:
            List of [timestamp, open, close, high, low] candles
        """
        candles = []
        current_time = int(time.time() * 1000) - (count * period_seconds * 1000)
        
        for i in range(count):
            timestamp = current_time + (i * period_seconds * 1000)
            open_price = self.current_price
            
            # Generate price movement
            if self.bars_in_trend >= self.max_trend_length:
                self.trend_direction *= -1
                self.bars_in_trend = 0
                self.max_trend_length = random.randint(20, 50)
            
            trend_component = self.trend_direction * self.volatility * self.trend_strength
            random_component = random.gauss(0, self.volatility) * (1 - self.trend_strength)
            price_change = (trend_component + random_component) * open_price
            
            close_price = open_price + price_change
            
            # Generate high and low
            intra_bar_range = abs(price_change) * random.uniform(1.5, 3.0)
            high_price = max(open_price, close_price) + intra_bar_range * random.random()
            low_price = min(open_price, close_price) - intra_bar_range * random.random()
            
            # Ensure valid OHLC
            high_price = max(high_price, open_price, close_price)
            low_price = min(low_price, open_price, close_price)
            
            candles.append([timestamp, open_price, close_price, high_price, low_price])
            
            self.current_price = close_price
            self.bars_in_trend += 1
        
        return candles


class SimulatedStreamingCapability:
    """
    Simulated streaming capability that mimics real data streaming behavior.
    
    This is used ONLY when explicitly enabled - NO automatic fallback.
    """
    
    def __init__(self, period_seconds: int = 60):
        """
        Initialize simulated streaming capability.
        
        Args:
            period_seconds: Candle period in seconds (default: 60 for 1-minute)
        """
        self.PERIOD = period_seconds
        self.generators: Dict[str, SimulatedDataGenerator] = {}
        self.active_assets: List[str] = []
        
        # Predefined asset configurations
        self.asset_configs = {
            'EURUSD_OTC': {'base_price': 1.1000, 'volatility': 0.0005},
            'GBPUSD_OTC': {'base_price': 1.2700, 'volatility': 0.0006},
            'USDJPY_OTC': {'base_price': 110.50, 'volatility': 0.08},
            'AUDUSD_OTC': {'base_price': 0.7300, 'volatility': 0.0005},
            'BTCUSD_OTC': {'base_price': 45000.00, 'volatility': 200.0},
            'ETHUSD_OTC': {'base_price': 3000.00, 'volatility': 30.0},
        }
    
    def start_streaming(self, assets: List[str]):
        """
        Start simulated streaming for specified assets.
        
        Args:
            assets: List of asset symbols to stream
        """
        print(f"[SIMULATED MODE] Starting simulated streaming for assets: {assets}")
        self.active_assets = assets
        
        for asset in assets:
            if asset not in self.generators:
                config = self.asset_configs.get(asset, {'base_price': 1.0, 'volatility': 0.001})
                self.generators[asset] = SimulatedDataGenerator(
                    base_price=config['base_price'],
                    volatility=config['volatility']
                )
    
    def stop_streaming(self, asset: str):
        """Stop simulated streaming for an asset."""
        print(f"[SIMULATED MODE] Stopping simulated streaming for {asset}")
        if asset in self.active_assets:
            self.active_assets.remove(asset)
    
    def get_current_candle(self, asset: str) -> Optional[List]:
        """
        Get current candle for an asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            [timestamp, open, close, high, low] or None
        """
        if asset not in self.generators:
            return None
        
        return self.generators[asset].generate_candle(self.PERIOD)
    
    def get_historical_candles(self, asset: str, count: int = 200) -> List[List]:
        """
        Get historical candles for an asset.
        
        Args:
            asset: Asset symbol
            count: Number of historical candles
            
        Returns:
            List of [timestamp, open, close, high, low] candles
        """
        if asset not in self.generators:
            config = self.asset_configs.get(asset, {'base_price': 1.0, 'volatility': 0.001})
            self.generators[asset] = SimulatedDataGenerator(
                base_price=config['base_price'],
                volatility=config['volatility']
            )
        
        return self.generators[asset].generate_historical_candles(count, self.PERIOD)
    
    def get_candle_history(self, asset: str, limit: int = 200) -> List[List]:
        """
        Get candle history for an asset (alias for compatibility).
        
        Args:
            asset: Asset symbol
            limit: Number of candles
            
        Returns:
            List of [timestamp, open, close, high, low] candles
        """
        return self.get_historical_candles(asset, limit)
    
    def get_latest_candle(self, asset: str) -> Optional[List]:
        """
        Get the latest candle for an asset.
        
        Args:
            asset: Asset symbol
            
        Returns:
            [timestamp, open, close, high, low] or None
        """
        if asset not in self.generators:
            return None
        
        return self.generators[asset].generate_candle(self.PERIOD)
    
    def get_all_candles(self, asset: str) -> List[List]:
        """
        Get all candles for an asset (returns historical for simulated mode).
        
        Args:
            asset: Asset symbol
            
        Returns:
            List of [timestamp, open, close, high, low] candles
        """
        return self.get_historical_candles(asset, count=200)
    
    def _reset_stream_state(self, inputs: Optional[Dict] = None):
        """
        Reset streaming state (compatibility method for real-mode interface).
        In simulated mode, this reinitializes generators.
        
        Args:
            inputs: Configuration dict (optional)
        """
        print("[SIMULATED MODE] Resetting stream state")
        # Reinitialize generators
        for asset in list(self.generators.keys()):
            config = self.asset_configs.get(asset, {'base_price': 1.0, 'volatility': 0.001})
            self.generators[asset] = SimulatedDataGenerator(
                base_price=config['base_price'],
                volatility=config['volatility']
            )
    
    def get_current_asset(self) -> Optional[str]:
        """
        Get the currently focused asset.
        
        Returns:
            Asset symbol or None
        """
        return self.active_assets[0] if self.active_assets else None
    
    def set_asset_focus(self, asset: str):
        """Set the focused asset for streaming (compatibility method)."""
        if asset not in self.active_assets:
            self.active_assets.append(asset)
    
    def release_asset_focus(self):
        """Release asset focus (compatibility method)."""
        self.active_assets.clear()
    
    def set_timeframe(self, minutes: int = 1, lock: bool = False):
        """Set the timeframe for candles (compatibility method)."""
        self.PERIOD = minutes * 60
    
    def unlock_timeframe(self):
        """Unlock the timeframe (compatibility method)."""
        pass  # No-op for simulated mode
