# bot/strategies/base.py
"""
Base Strategy Class - Common interface for all trading strategies.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
import numpy as np

from ..utils.logging import get_logger

logger = get_logger(__name__)

class BaseStrategy(ABC):
    """Base class for all trading strategies."""
    
    def __init__(self):
        self.name = self.__class__.__name__
    
    @abstractmethod
    def execute(self, candles) -> Optional[str]:
        """
        Execute the strategy on given candle data.
        
        Args:
            candles: List of Candle objects
            
        Returns:
            Optional[str]: 'call', 'put', or None
        """
        pass
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:]) if np.any(gains[-period:]) else 0
        avg_loss = np.mean(losses[-period:]) if np.any(losses[-period:]) else 0
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def calculate_sma(prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return np.mean(prices[-period:])
    
    @staticmethod  
    def calculate_ema(prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        a = np.convolve(prices, weights, mode='full')[:len(prices)]
        a[:period] = a[period]
        return a[-1]
    
    def validate_candles(self, candles, min_length: int) -> bool:
        """Validate candle data meets minimum requirements."""
        if not candles or len(candles) < min_length:
            logger.debug(f"Strategy {self.name}: Insufficient candle data ({len(candles) if candles else 0} < {min_length})")
            return False
        return True
    
    def log_signal(self, signal: str, details: str = ""):
        """Log strategy signal generation."""
        logger.info(f"Strategy {self.name} generated {signal} signal. {details}")