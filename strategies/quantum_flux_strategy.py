"""Quantum Flux Strategy Engine for Binary Options Trading.

Simplified version for GUI integration with core functionality.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from strategies.base import BaseStrategy


class SignalDirection(Enum):
    """Signal direction enumeration."""
    CALL = "call"
    PUT = "put"
    NEUTRAL = "neutral"


@dataclass
class QuantumSignal:
    """Quantum Flux signal container."""
    direction: SignalDirection
    confidence: float
    strength: float
    entry_price: float
    timestamp: datetime
    indicators: Dict[str, float]
    
    @property
    def is_valid(self) -> bool:
        """Check if signal is valid for trading."""
        return (
            self.direction != SignalDirection.NEUTRAL and
            self.confidence >= 0.6 and
            self.strength >= 0.5
        )


class QuantumFluxStrategy(BaseStrategy):
    """Quantum Flux strategy for binary options trading."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Quantum Flux Strategy."""
        super().__init__(config)
        self.min_candles = 50
        self.rsi_period = 14
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.bb_period = 20
        self.bb_std = 2.0
        
    def execute(self, candles: List[Dict[str, Any]]) -> Optional[str]:
        """Execute strategy on candle data."""
        signal = self.generate_signal(candles)
        if signal and signal.is_valid:
            return signal.direction.value
        return None
    
    def generate_signal(self, candles: List[Dict[str, Any]]) -> Optional[QuantumSignal]:
        """Generate trading signal from candle data."""
        if len(candles) < self.min_candles:
            return None
        
        # Convert to DataFrame
        df = pd.DataFrame(candles)
        if 'close' not in df.columns:
            return None
            
        close_prices = df['close'].values
        
        # Calculate indicators
        indicators = self._calculate_indicators(df)
        
        # Generate signal
        signal_score = self._calculate_signal_score(indicators)
        
        if abs(signal_score) < 0.2:
            direction = SignalDirection.NEUTRAL
        elif signal_score > 0:
            direction = SignalDirection.CALL
        else:
            direction = SignalDirection.PUT
        
        confidence = min(abs(signal_score), 1.0)
        strength = confidence
        
        return QuantumSignal(
            direction=direction,
            confidence=confidence,
            strength=strength,
            entry_price=float(close_prices[-1]),
            timestamp=datetime.now(),
            indicators=indicators
        )
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict[str, float]:
        """Calculate technical indicators."""
        close = df['close'].values
        
        # RSI
        rsi = self._calculate_rsi(close, self.rsi_period)
        
        # MACD
        macd, macd_signal, macd_hist = self._calculate_macd(
            close, self.macd_fast, self.macd_slow, self.macd_signal
        )
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = self._calculate_bollinger_bands(
            close, self.bb_period, self.bb_std
        )
        
        # EMAs
        ema_12 = self._calculate_ema(close, 12)
        ema_26 = self._calculate_ema(close, 26)
        
        return {
            'rsi': float(rsi),
            'macd': float(macd),
            'macd_signal': float(macd_signal),
            'macd_histogram': float(macd_hist),
            'bb_upper': float(bb_upper),
            'bb_middle': float(bb_middle),
            'bb_lower': float(bb_lower),
            'ema_12': float(ema_12),
            'ema_26': float(ema_26),
            'close': float(close[-1])
        }
    
    def _calculate_signal_score(self, indicators: Dict[str, float]) -> float:
        """Calculate overall signal score."""
        score = 0.0
        
        # RSI component
        rsi = indicators['rsi']
        if rsi < 30:
            score += 0.4  # Oversold, bullish
        elif rsi > 70:
            score -= 0.4  # Overbought, bearish
        
        # MACD component
        macd_hist = indicators['macd_histogram']
        if macd_hist > 0:
            score += 0.3
        else:
            score -= 0.3
        
        # Bollinger Bands component
        close = indicators['close']
        bb_upper = indicators['bb_upper']
        bb_lower = indicators['bb_lower']
        bb_middle = indicators['bb_middle']
        
        if close < bb_lower:
            score += 0.3  # Below lower band, bullish
        elif close > bb_upper:
            score -= 0.3  # Above upper band, bearish
        
        # EMA trend
        if indicators['ema_12'] > indicators['ema_26']:
            score += 0.2
        else:
            score -= 0.2
        
        return np.clip(score, -1.0, 1.0)
    
    def _calculate_rsi(self, prices: np.ndarray, period: int) -> float:
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
    
    def _calculate_macd(self, prices: np.ndarray, fast: int, slow: int, signal: int):
        """Calculate MACD indicator."""
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd_line = ema_fast - ema_slow
        
        # Simplified signal calculation
        macd_signal = macd_line * 0.9
        macd_hist = macd_line - macd_signal
        
        return macd_line, macd_signal, macd_hist
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """Calculate EMA."""
        if len(prices) < period:
            return float(prices[-1]) if len(prices) > 0 else 0.0
        
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        ema = np.convolve(prices, weights, mode='valid')
        return float(ema[-1]) if len(ema) > 0 else float(prices[-1])
    
    def _calculate_bollinger_bands(self, prices: np.ndarray, period: int, std_dev: float):
        """Calculate Bollinger Bands."""
        if len(prices) < period:
            current = float(prices[-1]) if len(prices) > 0 else 0.0
            return current, current, current
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        
        return upper, sma, lower
