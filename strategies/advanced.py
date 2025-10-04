# bot/strategies/advanced.py
"""
Advanced Trading Strategies - Tier 1 strategies from gtrr46.py
These are the most sophisticated strategies with proven performance.
"""

from typing import List, Optional
import numpy as np
from .base import BaseStrategy


class AdvancedStrategies:
    """Advanced trading strategies from gtrr46.py - most comprehensive implementation."""
    
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator with enhanced accuracy."""
        if len(prices) < period + 1:
            return 50.0
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = (np.mean(gains[-period:])
                    if np.any(gains[-period:]) else 0)
        avg_loss = (np.mean(losses[-period:])
                    if np.any(losses[-period:]) else 0)
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
        """Calculate Exponential Moving Average with enhanced precision."""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        a = np.convolve(prices, weights, mode='full')[:len(prices)]
        a[:period] = a[period]
        return a[-1]

    @staticmethod
    def aggressive_momentum_scalper(candles) -> Optional[str]:
        """
        Aggressive Momentum Scalper - Advanced body size and momentum analysis.
        Focuses on strong momentum candles with significant body size.
        """
        if len(candles) < 5:
            return None
        
        c0 = candles[-1]
        c1 = candles[-2]
        body_size = abs(c0.close - c0.open)
        candle_range = c0.high - c0.low
        prev_bodies = [abs(c.close - c.open) for c in candles[-4:-1]]
        avg_prev_body = np.mean(prev_bodies)
        
        # Bullish momentum
        if (c0.close > c0.open and
                body_size > avg_prev_body * 1.2 and
                c0.close > c1.high and
                body_size > candle_range * 0.6):
            return "call"
        
        # Bearish momentum
        if (c0.close < c0.open and
                body_size > avg_prev_body * 1.2 and
                c0.close < c1.low and
                body_size > candle_range * 0.6):
            return "put"
        
        return None

    @staticmethod
    def rapid_rsi_extremes(candles) -> Optional[str]:
        """
        Rapid RSI Extremes - Fast RSI with reversal detection.
        Uses shorter RSI period for quicker signals with confirmation.
        """
        if len(candles) < 8:
            return None
        
        prices = [c.close for c in candles]
        rsi = AdvancedStrategies.calculate_rsi(prices, 7)
        c0 = candles[-1]
        c1 = candles[-2]
        
        # Oversold reversal
        if (rsi < 25 and
                c0.close > c0.open and
                c0.low < c1.low and
                c0.close > c1.close):
            return "call"
        
        # Overbought reversal
        if (rsi > 75 and
                c0.close < c0.open and
                c0.high > c1.high and
                c0.close < c1.close):
            return "put"
        
        return None

    @staticmethod
    def dual_ema_crossover_aggressive(candles) -> Optional[str]:
        """
        Dual EMA Crossover Aggressive - Aggressive crossover with confirmation.
        Uses fast EMA crossover with price action confirmation.
        """
        if len(candles) < 15:
            return None
        
        closes = [c.close for c in candles]
        ema5 = AdvancedStrategies.calculate_ema(closes, 5)
        ema13 = AdvancedStrategies.calculate_ema(closes, 13)
        prev_closes = closes[:-1]
        prev_ema5 = AdvancedStrategies.calculate_ema(prev_closes, 5)
        prev_ema13 = AdvancedStrategies.calculate_ema(prev_closes, 13)
        c0 = candles[-1]
        
        # Bullish crossover
        if (prev_ema5 <= prev_ema13 and
                ema5 > ema13 and
                c0.close > c0.open and
                c0.close > ema5):
            return "call"
        
        # Bearish crossover
        if (prev_ema5 >= prev_ema13 and
                ema5 < ema13 and
                c0.close < c0.open and
                c0.close < ema5):
            return "put"
        
        return None

    @staticmethod
    def volume_price_breakout(candles) -> Optional[str]:
        """
        Volume Price Breakout - Volume-weighted breakout detection.
        Combines price breakouts with volume confirmation.
        """
        if len(candles) < 8:
            return None
        
        c0 = candles[-1]
        volumes = [max(c.volume, 1.0) for c in candles[-7:-1]]
        avg_volume = np.mean(volumes)
        current_volume = max(c0.volume, 1.0)
        recent_highs = [c.high for c in candles[-5:-1]]
        recent_lows = [c.low for c in candles[-5:-1]]
        resistance = max(recent_highs)
        support = min(recent_lows)
        
        # Bullish breakout
        if (c0.close > resistance and
                c0.close > c0.open and
                current_volume > avg_volume * 1.1 and
                c0.high == max([c.high for c in candles[-5:]])):
            return "call"
        
        # Bearish breakout
        if (c0.close < support and
                c0.close < c0.open and
                current_volume > avg_volume * 1.1 and
                c0.low == min([c.low for c in candles[-5:]])):
            return "put"
        
        return None

    @staticmethod
    def triple_confirmation_scalper(candles) -> Optional[str]:
        """
        Triple Confirmation Scalper - Multi-indicator confluence.
        Requires multiple confirmations for signal generation.
        """
        if len(candles) < 10:
            return None
        
        closes = [c.close for c in candles]
        rsi = AdvancedStrategies.calculate_rsi(closes, 9)
        ema8 = AdvancedStrategies.calculate_ema(closes, 8)
        c0 = candles[-1]
        c1 = candles[-2]
        price_momentum = (c0.close - candles[-3].close) / candles[-3].close * 100
        
        # Bullish confluence
        bullish_rsi = 20 < rsi < 60
        bullish_ema = c0.close > ema8
        bullish_momentum = price_momentum > -0.5
        bullish_candle = c0.close > c0.open
        
        if (bullish_rsi and bullish_ema and bullish_momentum and bullish_candle and
                c0.close > c1.high):
            return "call"
        
        # Bearish confluence
        bearish_rsi = 40 < rsi < 80
        bearish_ema = c0.close < ema8
        bearish_momentum = price_momentum < 0.5
        bearish_candle = c0.close < c0.open
        
        if (bearish_rsi and bearish_ema and bearish_momentum and bearish_candle and
                c0.close < c1.low):
            return "put"
        
        return None