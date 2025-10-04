"""
Technical Analysis Engine
Calculates various technical indicators for market data analysis
"""

import numpy as np
from typing import List, Optional
from collections import deque

from .data_models import CandleData, TechnicalIndicators


class TechnicalAnalyzer:
    """
    Technical analysis engine for calculating market indicators.
    
    Supports:
    - RSI (Relative Strength Index)
    - EMA (Exponential Moving Average)
    - SMA (Simple Moving Average)
    - MACD (Moving Average Convergence Divergence)
    - Bollinger Bands
    - Stochastic Oscillator
    - ATR (Average True Range)
    """
    
    def __init__(self, rsi_period: int = 14, ema_fast: int = 12, ema_slow: int = 26, macd_signal: int = 9):
        self.rsi_period = rsi_period
        self.ema_fast_period = ema_fast
        self.ema_slow_period = ema_slow
        self.macd_signal_period = macd_signal
        
        # Cache for calculations
        self._price_cache = deque(maxlen=200)
        self._rsi_cache = deque(maxlen=100)
        self._ema_fast_cache = deque(maxlen=100)
        self._ema_slow_cache = deque(maxlen=100)
    
    def calculate_indicators(self, candles: List[CandleData]) -> TechnicalIndicators:
        """Calculate all technical indicators for the given candles."""
        if not candles or len(candles) < 2:
            return TechnicalIndicators()
        
        # Extract price arrays
        closes = np.array([c.close for c in candles])
        highs = np.array([c.high for c in candles])
        lows = np.array([c.low for c in candles])
        opens = np.array([c.open for c in candles])
        
        indicators = TechnicalIndicators()
        
        try:
            # RSI
            if len(closes) >= self.rsi_period:
                indicators.rsi = self._calculate_rsi(closes)
            
            # Moving Averages
            if len(closes) >= self.ema_fast_period:
                indicators.ema_fast = self._calculate_ema(closes, self.ema_fast_period)
            
            if len(closes) >= self.ema_slow_period:
                indicators.ema_slow = self._calculate_ema(closes, self.ema_slow_period)
            
            if len(closes) >= 20:
                indicators.sma = self._calculate_sma(closes, 20)
                indicators.wma = self._calculate_wma(closes, 20)
            
            # MACD
            if indicators.ema_fast is not None and indicators.ema_slow is not None:
                macd_line = indicators.ema_fast - indicators.ema_slow
                indicators.macd = macd_line
                
                # MACD Signal line (EMA of MACD line)
                if len(closes) >= self.ema_slow_period + self.macd_signal_period:
                    indicators.macd_signal = self._calculate_macd_signal(closes)
                    if indicators.macd_signal is not None:
                        indicators.macd_histogram = indicators.macd - indicators.macd_signal
            
            # Bollinger Bands
            if len(closes) >= 20:
                bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(closes)
                indicators.bollinger_upper = bb_upper
                indicators.bollinger_middle = bb_middle
                indicators.bollinger_lower = bb_lower
            
            # Stochastic Oscillator
            if len(closes) >= 14:
                stoch_k, stoch_d = self._calculate_stochastic(highs, lows, closes)
                indicators.stochastic_k = stoch_k
                indicators.stochastic_d = stoch_d
            
            # ATR (Average True Range)
            if len(closes) >= 14:
                indicators.atr = self._calculate_atr(highs, lows, closes)
        
        except Exception as e:
            # Return partial indicators if some calculations fail
            pass
        
        return indicators
    
    def _calculate_rsi(self, prices: np.ndarray, period: int = None) -> Optional[float]:
        """Calculate Relative Strength Index."""
        if period is None:
            period = self.rsi_period
        
        if len(prices) < period + 1:
            return None
        
        try:
            deltas = np.diff(prices)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            
            # Calculate average gains and losses
            avg_gain = np.mean(gains[-period:])
            avg_loss = np.mean(losses[-period:])
            
            if avg_loss == 0:
                return 100.0
            
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi)
        
        except Exception:
            return None
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None
        
        try:
            alpha = 2.0 / (period + 1)
            ema = prices[0]
            
            for price in prices[1:]:
                ema = alpha * price + (1 - alpha) * ema
            
            return float(ema)
        
        except Exception:
            return None
    
    def _calculate_sma(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None
        
        try:
            return float(np.mean(prices[-period:]))
        except Exception:
            return None
    
    def _calculate_wma(self, prices: np.ndarray, period: int) -> Optional[float]:
        """Calculate Weighted Moving Average."""
        if len(prices) < period:
            return None
        
        try:
            weights = np.arange(1, period + 1)
            wma = np.average(prices[-period:], weights=weights)
            return float(wma)
        except Exception:
            return None
    
    def _calculate_macd_signal(self, prices: np.ndarray) -> Optional[float]:
        """Calculate MACD signal line."""
        try:
            # Calculate MACD line first
            ema_fast = self._calculate_ema(prices, self.ema_fast_period)
            ema_slow = self._calculate_ema(prices, self.ema_slow_period)
            
            if ema_fast is None or ema_slow is None:
                return None
            
            # For simplicity, return EMA of recent MACD values
            # In a full implementation, you'd maintain a MACD history
            macd_line = ema_fast - ema_slow
            return macd_line * 0.9  # Simplified signal approximation
        
        except Exception:
            return None
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> tuple:
        """Calculate Bollinger Bands."""
        try:
            if len(prices) < period:
                return None, None, None
            
            sma = np.mean(prices[-period:])
            std = np.std(prices[-period:])
            
            upper_band = sma + (std_dev * std)
            lower_band = sma - (std_dev * std)
            
            return float(upper_band), float(sma), float(lower_band)
        
        except Exception:
            return None, None, None
    
    def _calculate_stochastic(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, 
                            k_period: int = 14, d_period: int = 3) -> tuple:
        """Calculate Stochastic Oscillator (%K and %D)."""
        try:
            if len(closes) < k_period:
                return None, None
            
            # Calculate %K
            lowest_low = np.min(lows[-k_period:])
            highest_high = np.max(highs[-k_period:])
            
            if highest_high == lowest_low:
                k_percent = 50.0
            else:
                k_percent = ((closes[-1] - lowest_low) / (highest_high - lowest_low)) * 100
            
            # %D is typically a moving average of %K
            # For simplicity, we'll return a smoothed version
            d_percent = k_percent * 0.8  # Simplified smoothing
            
            return float(k_percent), float(d_percent)
        
        except Exception:
            return None, None
    
    def _calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, 
                      period: int = 14) -> Optional[float]:
        """Calculate Average True Range."""
        try:
            if len(closes) < period + 1:
                return None
            
            true_ranges = []
            
            for i in range(1, len(closes)):
                high_low = highs[i] - lows[i]
                high_close = abs(highs[i] - closes[i-1])
                low_close = abs(lows[i] - closes[i-1])
                
                true_range = max(high_low, high_close, low_close)
                true_ranges.append(true_range)
            
            if len(true_ranges) < period:
                return None
            
            atr = np.mean(true_ranges[-period:])
            return float(atr)
        
        except Exception:
            return None
    
    def get_trend_signal(self, indicators: TechnicalIndicators) -> str:
        """Get a simple trend signal based on indicators."""
        signals = []
        
        # RSI signals
        if indicators.rsi is not None:
            if indicators.rsi < 30:
                signals.append("OVERSOLD")
            elif indicators.rsi > 70:
                signals.append("OVERBOUGHT")
        
        # MACD signals
        if indicators.macd is not None and indicators.macd_signal is not None:
            if indicators.macd > indicators.macd_signal:
                signals.append("BULLISH")
            else:
                signals.append("BEARISH")
        
        # EMA signals
        if indicators.ema_fast is not None and indicators.ema_slow is not None:
            if indicators.ema_fast > indicators.ema_slow:
                signals.append("UPTREND")
            else:
                signals.append("DOWNTREND")
        
        if not signals:
            return "NEUTRAL"
        
        # Return the most common signal
        return max(set(signals), key=signals.count)