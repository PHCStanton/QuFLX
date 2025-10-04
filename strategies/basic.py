# bot/strategies/basic.py
"""
Basic Trading Strategies - Tier 3 strategies from gunna_v2.py and others
Simple and reliable strategies for consistent performance.
"""

from typing import List, Optional
import numpy as np
from .base import BaseStrategy


class BasicStrategies:
    """Basic trading strategies from multiple sources - simple implementations."""
    
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
    def momentum_breakout(candles) -> Optional[str]:
        """
        Momentum Breakout - Basic momentum and volume breakout strategy.
        Simple but effective for trending markets.
        """
        if len(candles) < 7:
            return None
        
        last = candles[-1]
        prev_5_highs = [c.high for c in candles[-6:-1]]
        prev_5_lows = [c.low for c in candles[-6:-1]]
        prices = [c.close for c in candles]
        rsi = BasicStrategies.calculate_rsi(prices)
        volumes = [c.volume for c in candles]
        avg_vol = np.mean(volumes[-6:-1])
        
        # Bullish momentum breakout
        if (last.close > max(prev_5_highs) and rsi > 55 and 
            last.volume > avg_vol * 1.1 and last.close > last.open):
            return "call"
        
        # Bearish momentum breakout
        if (last.close < min(prev_5_lows) and rsi < 45 and 
            last.volume > avg_vol * 1.1 and last.close < last.open):
            return "put"
        
        return None

    @staticmethod
    def one_minute_reversal(candles) -> Optional[str]:
        """
        1-Minute Reversal - Quick reversal pattern detection.
        Identifies short-term reversal opportunities.
        """
        if len(candles) < 4:
            return None
        
        c2, c1, c0 = candles[-3], candles[-2], candles[-1]
        
        # Bullish reversal
        if (c2.close < c2.open and c1.close < c1.open and c0.close > c0.open and
            c0.open < c1.close and c0.close > c1.open and
            c0.close - c0.open > (c1.open - c1.close) * 1.2):
            return "call"
        
        # Bearish reversal
        if (c2.close > c2.open and c1.close > c1.open and c0.close < c0.open and
            c0.open > c1.close and c0.close < c1.open and
            c0.open - c0.close > (c1.close - c1.open) * 1.2):
            return "put"
        
        return None

    @staticmethod
    def rapid_ma_cross(candles) -> Optional[str]:
        """
        Rapid MA Cross - Fast moving average crossover strategy.
        Uses short-period EMAs for quick signals.
        """
        if len(candles) < 25:
            return None
        
        prices = [c.close for c in candles]
        ema_5_prev = BasicStrategies.calculate_ema(prices[:-1], 5)
        ema_21_prev = BasicStrategies.calculate_ema(prices[:-1], 21)
        ema_5_now = BasicStrategies.calculate_ema(prices, 5)
        ema_21_now = BasicStrategies.calculate_ema(prices, 21)
        
        # Bullish crossover
        if ema_5_prev < ema_21_prev and ema_5_now > ema_21_now:
            return "call"
        
        # Bearish crossover
        if ema_5_prev > ema_21_prev and ema_5_now < ema_21_now:
            return "put"
        
        return None

    @staticmethod
    def impulse_spike(candles) -> Optional[str]:
        """
        Impulse Spike - Detects strong impulse movements.
        Identifies unusually large candle bodies indicating strong momentum.
        """
        if len(candles) < 8:
            return None
        
        last = candles[-1]
        prev_bodies = [abs(c.close - c.open) for c in candles[-7:-1]]
        avg_body = np.mean(prev_bodies)
        
        # Bullish impulse
        if (last.close > last.open and 
            (last.close - last.open) > avg_body * 2.2):
            return "call"
        
        # Bearish impulse
        if (last.close < last.open and 
            (last.open - last.close) > avg_body * 2.2):
            return "put"
        
        return None