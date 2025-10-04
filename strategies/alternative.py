# bot/strategies/alternative.py
"""
Alternative Trading Strategies - Tier 2 strategies from gunna.py
Unique strategies with different approaches and methodologies.
"""

from typing import List, Optional
import numpy as np
from .base import BaseStrategy


class AlternativeStrategies:
    """Alternative trading strategies from gunna.py - unique implementations."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator."""
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

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

    @staticmethod
    def rsi_volume_strategy(candles) -> Optional[str]:
        """
        RSI + Volume Strategy - Combines RSI with volume analysis.
        Uses volume confirmation for RSI-based signals.
        """
        if len(candles) < 15:
            return None
        
        prices = [c.close for c in candles]
        volumes = [c.volume for c in candles]
        rsi = AlternativeStrategies.calculate_rsi(prices)
        avg_volume = np.mean(volumes[-10:])
        current_volume = candles[-1].volume
        
        # Oversold with volume spike
        if rsi < 30 and current_volume > avg_volume * 1.2:
            return "call"
        # Overbought with volume spike
        elif rsi > 70 and current_volume > avg_volume * 1.2:
            return "put"
        
        return None

    @staticmethod
    def smart_martingale(candles) -> Optional[str]:
        """
        Smart Martingale Strategy - Trend-based martingale approach.
        Uses trend analysis to determine martingale direction.
        """
        if len(candles) < 10:
            return None
        
        prices = [c.close for c in candles]
        trend = np.polyfit(range(len(prices[-5:])), prices[-5:], 1)[0]
        
        # Follow trend direction
        if trend > 0.0001:
            return "call"
        elif trend < -0.0001:
            return "put"
        
        return None

    @staticmethod
    def two_candle_breakout(candles) -> Optional[str]:
        """
        Two Candle Breakout Strategy - Simple breakout detection.
        Identifies breakouts from recent price ranges.
        """
        if len(candles) < 7:
            return None
        
        last = candles[-1]
        prev_5_highs = [c.high for c in candles[-6:-1]]
        prev_5_lows = [c.low for c in candles[-6:-1]]
        
        # Bullish breakout
        if last.close > max(prev_5_highs) and last.close > last.open:
            return "call"
        # Bearish breakout
        elif last.close < min(prev_5_lows) and last.close < last.open:
            return "put"
        
        return None

    @staticmethod
    def triple_confluence(candles) -> Optional[str]:
        """
        Triple Confluence Strategy - Multi-signal confirmation.
        Requires multiple indicators to align for signal generation.
        """
        if len(candles) < 25:
            return None
        
        prices = [c.close for c in candles]
        rsi = AlternativeStrategies.calculate_rsi(prices)
        ema_5 = AlternativeStrategies.calculate_ema(prices, 5)
        ema_21 = AlternativeStrategies.calculate_ema(prices, 21)
        
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI signals
        if rsi < 35:
            bullish_signals += 1
        elif rsi > 65:
            bearish_signals += 1
        
        # EMA signals
        if ema_5 > ema_21:
            bullish_signals += 1
        elif ema_5 < ema_21:
            bearish_signals += 1
        
        # Price momentum signals
        if prices[-1] > prices[-2]:
            bullish_signals += 1
        elif prices[-1] < prices[-2]:
            bearish_signals += 1
        
        # Require at least 2 confirmations
        if bullish_signals >= 2:
            return "call"
        elif bearish_signals >= 2:
            return "put"
        
        return None

    @staticmethod
    def reversal_candle_trap(candles) -> Optional[str]:
        """
        Reversal Candle Trap Strategy - Pattern-based reversal detection.
        Identifies specific candlestick reversal patterns.
        """
        if len(candles) < 4:
            return None
        
        c2, c1, c0 = candles[-3], candles[-2], candles[-1]
        
        # Bullish reversal pattern
        if (c2.close < c2.open and c1.close < c1.open and 
            c0.close > c0.open and c0.close > c1.high):
            return "call"
        
        # Bearish reversal pattern
        if (c2.close > c2.open and c1.close > c1.open and 
            c0.close < c0.open and c0.close < c1.low):
            return "put"
        
        return None