"""
Optimized Strategy Classes for Pocket Trader Bot
Enhanced trading strategies with parameter configuration and performance tracking.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import time
import logging
from enum import Enum


class TradeDirection(Enum):
    CALL = "call"
    PUT = "put"
    HOLD = "hold"


@dataclass
class Candle:
    """Enhanced candle data structure"""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    @property
    def body(self) -> float:
        """Candle body size"""
        return abs(self.close - self.open)
    
    @property
    def range(self) -> float:
        """Candle range (high - low)"""
        return self.high - self.low
    
    @property
    def is_bullish(self) -> bool:
        """Check if candle is bullish"""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if candle is bearish"""
        return self.close < self.open


@dataclass
class StrategyConfig:
    """Configuration class for strategy parameters"""
    name: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    risk_level: float = 1.0  # 0.1 to 2.0
    confidence_threshold: float = 0.7  # 0.0 to 1.0
    
    def get_param(self, key: str, default: Any = None) -> Any:
        """Get parameter value with default fallback"""
        return self.parameters.get(key, default)
    
    def set_param(self, key: str, value: Any) -> None:
        """Set parameter value"""
        self.parameters[key] = value


@dataclass
class SignalResult:
    """Strategy signal result"""
    direction: TradeDirection
    confidence: float
    reasoning: str
    indicators: Dict[str, float] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class BaseStrategy(ABC):
    """Base class for all trading strategies"""
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
        self.logger = logging.getLogger(f"Strategy.{self.name}")
        self.performance_metrics = {
            'signals_generated': 0,
            'successful_signals': 0,
            'failed_signals': 0,
            'total_profit': 0.0,
            'win_rate': 0.0,
            'average_confidence': 0.0
        }
    
    @abstractmethod
    def analyze(self, candles: List[Candle]) -> SignalResult:
        """Analyze candles and return trading signal"""
        pass
    
    def calculate_rsi(self, prices: List[float], period: int = 14) -> float:
        """Calculate RSI indicator"""
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
    
    def calculate_sma(self, prices: List[float], period: int) -> float:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        return np.mean(prices[-period:])
    
    def calculate_ema(self, prices: List[float], period: int) -> float:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        weights = np.exp(np.linspace(-1., 0., period))
        weights /= weights.sum()
        ema = np.convolve(prices, weights, mode='full')[:len(prices)]
        ema[:period] = ema[period]
        return ema[-1]
    
    def calculate_bollinger_bands(self, prices: List[float], period: int = 20, std_dev: float = 2) -> Tuple[float, float, float]:
        """Calculate Bollinger Bands (upper, middle, lower)"""
        if len(prices) < period:
            price = prices[-1] if prices else 0.0
            return price, price, price
        
        middle = self.calculate_sma(prices, period)
        std = np.std(prices[-period:])
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return upper, middle, lower
    
    def update_performance(self, signal_result: SignalResult, trade_result: Optional[bool] = None, profit: float = 0.0):
        """Update strategy performance metrics"""
        self.performance_metrics['signals_generated'] += 1
        self.performance_metrics['average_confidence'] = (
            (self.performance_metrics['average_confidence'] * (self.performance_metrics['signals_generated'] - 1) + 
             signal_result.confidence) / self.performance_metrics['signals_generated']
        )
        
        if trade_result is not None:
            if trade_result:
                self.performance_metrics['successful_signals'] += 1
            else:
                self.performance_metrics['failed_signals'] += 1
            
            self.performance_metrics['total_profit'] += profit
            total_trades = self.performance_metrics['successful_signals'] + self.performance_metrics['failed_signals']
            self.performance_metrics['win_rate'] = self.performance_metrics['successful_signals'] / total_trades
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get strategy performance summary"""
        return {
            'name': self.name,
            'signals_generated': self.performance_metrics['signals_generated'],
            'win_rate': self.performance_metrics['win_rate'],
            'total_profit': self.performance_metrics['total_profit'],
            'average_confidence': self.performance_metrics['average_confidence'],
            'config': self.config.parameters
        }


class MomentumBreakoutStrategy(BaseStrategy):
    """Enhanced momentum breakout strategy with configurable parameters"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="Momentum Breakout",
                parameters={
                    'lookback_period': 5,
                    'body_multiplier': 1.2,
                    'volume_threshold': 1.1,
                    'min_candle_body_ratio': 0.6
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        lookback = self.config.get_param('lookback_period', 5)
        body_mult = self.config.get_param('body_multiplier', 1.2)
        vol_thresh = self.config.get_param('volume_threshold', 1.1)
        min_body_ratio = self.config.get_param('min_candle_body_ratio', 0.6)
        
        if len(candles) < lookback:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        current = candles[-1]
        previous = candles[-2]
        
        # Calculate average body size of previous candles
        prev_bodies = [c.body for c in candles[-lookback-1:-1]]
        avg_prev_body = np.mean(prev_bodies)
        
        # Calculate volume analysis
        prev_volumes = [max(c.volume, 1.0) for c in candles[-lookback-1:-1]]
        avg_volume = np.mean(prev_volumes)
        current_volume = max(current.volume, 1.0)
        
        confidence = 0.0
        indicators = {
            'current_body': current.body,
            'avg_prev_body': avg_prev_body,
            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1.0,
            'body_range_ratio': current.body / current.range if current.range > 0 else 0.0
        }
        
        # Bullish breakout conditions
        if (current.is_bullish and 
            current.body > avg_prev_body * body_mult and
            current.close > previous.high and
            current.body > current.range * min_body_ratio and
            current_volume > avg_volume * vol_thresh):
            
            confidence = min(0.9, 0.5 + 
                           (current.body / avg_prev_body - body_mult) * 0.2 +
                           (current_volume / avg_volume - vol_thresh) * 0.1 +
                           (current.body / current.range - min_body_ratio) * 0.2)
            
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Bullish momentum breakout detected",
                indicators
            )
        
        # Bearish breakout conditions
        elif (current.is_bearish and 
              current.body > avg_prev_body * body_mult and
              current.close < previous.low and
              current.body > current.range * min_body_ratio and
              current_volume > avg_volume * vol_thresh):
            
            confidence = min(0.9, 0.5 + 
                           (current.body / avg_prev_body - body_mult) * 0.2 +
                           (current_volume / avg_volume - vol_thresh) * 0.1 +
                           (current.body / current.range - min_body_ratio) * 0.2)
            
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Bearish momentum breakout detected",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, "No momentum breakout detected", indicators)


class OneMinuteReversalStrategy(BaseStrategy):
    """Enhanced one-minute reversal strategy"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="One Minute Reversal",
                parameters={
                    'rsi_period': 7,
                    'rsi_oversold': 25,
                    'rsi_overbought': 75,
                    'confirmation_candles': 2
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        rsi_period = self.config.get_param('rsi_period', 7)
        oversold = self.config.get_param('rsi_oversold', 25)
        overbought = self.config.get_param('rsi_overbought', 75)
        
        if len(candles) < rsi_period + 2:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        prices = [c.close for c in candles]
        rsi = self.calculate_rsi(prices, rsi_period)
        
        current = candles[-1]
        previous = candles[-2]
        
        indicators = {
            'rsi': rsi,
            'current_close': current.close,
            'previous_close': previous.close
        }
        
        # Bullish reversal
        if (rsi < oversold and 
            current.is_bullish and
            current.low < previous.low and
            current.close > previous.close):
            
            confidence = min(0.85, 0.4 + (oversold - rsi) / oversold * 0.3 + 
                           (current.close - current.open) / current.range * 0.15)
            
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Bullish reversal - RSI oversold ({rsi:.1f})",
                indicators
            )
        
        # Bearish reversal
        elif (rsi > overbought and 
              current.is_bearish and
              current.high > previous.high and
              current.close < previous.close):
            
            confidence = min(0.85, 0.4 + (rsi - overbought) / (100 - overbought) * 0.3 + 
                           (current.open - current.close) / current.range * 0.15)
            
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Bearish reversal - RSI overbought ({rsi:.1f})",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, f"No reversal signal - RSI: {rsi:.1f}", indicators)


class RapidMACrossStrategy(BaseStrategy):
    """Enhanced rapid moving average crossover strategy"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="Rapid MA Cross",
                parameters={
                    'fast_period': 5,
                    'slow_period': 13
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        fast_period = self.config.get_param('fast_period', 5)
        slow_period = self.config.get_param('slow_period', 13)
        
        if len(candles) < slow_period + 1:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        closes = [c.close for c in candles]
        
        fast_ema = self.calculate_ema(closes, fast_period)
        slow_ema = self.calculate_ema(closes, slow_period)
        
        prev_closes = closes[:-1]
        prev_fast_ema = self.calculate_ema(prev_closes, fast_period)
        prev_slow_ema = self.calculate_ema(prev_closes, slow_period)
        
        current = candles[-1]
        
        indicators = {
            'fast_ema': fast_ema,
            'slow_ema': slow_ema,
            'prev_fast_ema': prev_fast_ema,
            'prev_slow_ema': prev_slow_ema
        }
        
        # Bullish crossover
        if (prev_fast_ema <= prev_slow_ema and 
            fast_ema > slow_ema and
            current.is_bullish and
            current.close > fast_ema):
            
            cross_strength = abs(fast_ema - slow_ema) / slow_ema if slow_ema > 0 else 0
            confidence = min(0.9, 0.5 + cross_strength * 10 + 
                           (current.close - current.open) / current.range * 0.2)
            
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Bullish MA crossover",
                indicators
            )
        
        # Bearish crossover
        elif (prev_fast_ema >= prev_slow_ema and 
              fast_ema < slow_ema and
              current.is_bearish and
              current.close < fast_ema):
            
            cross_strength = abs(fast_ema - slow_ema) / slow_ema if slow_ema > 0 else 0
            confidence = min(0.9, 0.5 + cross_strength * 10 + 
                           (current.open - current.close) / current.range * 0.2)
            
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Bearish MA crossover",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, "No MA crossover detected", indicators)


class ImpulseSpikeStrategy(BaseStrategy):
    """Enhanced impulse spike detection strategy"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="Impulse Spike",
                parameters={
                    'spike_threshold': 1.5,
                    'volume_multiplier': 1.2,
                    'lookback_candles': 5
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        spike_thresh = self.config.get_param('spike_threshold', 1.5)
        vol_mult = self.config.get_param('volume_multiplier', 1.2)
        lookback = self.config.get_param('lookback_candles', 5)
        
        if len(candles) < lookback + 1:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        current = candles[-1]
        recent_candles = candles[-lookback-1:-1]
        
        avg_body = np.mean([c.body for c in recent_candles])
        avg_volume = np.mean([max(c.volume, 1.0) for c in recent_candles])
        current_volume = max(current.volume, 1.0)
        
        indicators = {
            'current_body': current.body,
            'avg_body': avg_body,
            'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 1
        }
        
        # Bullish impulse spike
        if (current.is_bullish and
            current.body > avg_body * spike_thresh and
            current_volume > avg_volume * vol_mult):
            
            confidence = min(0.85, 0.4 + 
                           (current.body / avg_body - spike_thresh) * 0.2 +
                           (current_volume / avg_volume - vol_mult) * 0.15)
            
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Bullish impulse spike detected",
                indicators
            )
        
        # Bearish impulse spike
        elif (current.is_bearish and
              current.body > avg_body * spike_thresh and
              current_volume > avg_volume * vol_mult):
            
            confidence = min(0.85, 0.4 + 
                           (current.body / avg_body - spike_thresh) * 0.2 +
                           (current_volume / avg_volume - vol_mult) * 0.15)
            
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Bearish impulse spike detected",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, "No impulse spike detected", indicators)


class RSIExtremeStrategy(BaseStrategy):
    """Enhanced RSI extreme levels strategy"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="RSI Extreme",
                parameters={
                    'rsi_period': 14,
                    'extreme_oversold': 20,
                    'extreme_overbought': 80
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        rsi_period = self.config.get_param('rsi_period', 14)
        oversold = self.config.get_param('extreme_oversold', 20)
        overbought = self.config.get_param('extreme_overbought', 80)
        
        if len(candles) < rsi_period + 2:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        prices = [c.close for c in candles]
        rsi = self.calculate_rsi(prices, rsi_period)
        current = candles[-1]
        
        indicators = {'rsi': rsi, 'price': current.close}
        
        # Extreme oversold with bullish confirmation
        if rsi < oversold and current.is_bullish:
            confidence = min(0.8, 0.3 + (oversold - rsi) / oversold * 0.4 +
                           (current.close - current.open) / current.range * 0.1)
            
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Extreme RSI oversold ({rsi:.1f})",
                indicators
            )
        
        # Extreme overbought with bearish confirmation
        elif rsi > overbought and current.is_bearish:
            confidence = min(0.8, 0.3 + (rsi - overbought) / (100 - overbought) * 0.4 +
                           (current.open - current.close) / current.range * 0.1)
            
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Extreme RSI overbought ({rsi:.1f})",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, f"RSI in normal range ({rsi:.1f})", indicators)


class DualEMACrossoverStrategy(BaseStrategy):
    """Enhanced dual EMA crossover strategy"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="Dual EMA Crossover",
                parameters={
                    'fast_ema': 8,
                    'slow_ema': 21,
                    'trend_ema': 50
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        fast_period = self.config.get_param('fast_ema', 8)
        slow_period = self.config.get_param('slow_ema', 21)
        trend_period = self.config.get_param('trend_ema', 50)
        
        if len(candles) < trend_period + 1:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        closes = [c.close for c in candles]
        
        fast_ema = self.calculate_ema(closes, fast_period)
        slow_ema = self.calculate_ema(closes, slow_period)
        trend_ema = self.calculate_ema(closes, trend_period)
        
        prev_closes = closes[:-1]
        prev_fast = self.calculate_ema(prev_closes, fast_period)
        prev_slow = self.calculate_ema(prev_closes, slow_period)
        
        current = candles[-1]
        
        indicators = {
            'fast_ema': fast_ema,
            'slow_ema': slow_ema,
            'trend_ema': trend_ema
        }
        
        # Bullish crossover with trend confirmation
        if (prev_fast <= prev_slow and 
            fast_ema > slow_ema and
            current.close > trend_ema and
            current.is_bullish):
            
            confidence = 0.75
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Bullish EMA crossover with uptrend",
                indicators
            )
        
        # Bearish crossover with trend confirmation
        elif (prev_fast >= prev_slow and 
              fast_ema < slow_ema and
              current.close < trend_ema and
              current.is_bearish):
            
            confidence = 0.75
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Bearish EMA crossover with downtrend",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, "No confirmed EMA crossover", indicators)


class VolumeBreakoutStrategy(BaseStrategy):
    """Enhanced volume-based breakout strategy"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="Volume Breakout",
                parameters={
                    'volume_threshold': 1.5,
                    'breakout_lookback': 5
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        vol_thresh = self.config.get_param('volume_threshold', 1.5)
        lookback = self.config.get_param('breakout_lookback', 5)
        
        if len(candles) < lookback + 1:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        current = candles[-1]
        recent_candles = candles[-lookback-1:-1]
        
        avg_volume = np.mean([max(c.volume, 1.0) for c in recent_candles])
        current_volume = max(current.volume, 1.0)
        
        recent_highs = [c.high for c in recent_candles]
        recent_lows = [c.low for c in recent_candles]
        resistance = max(recent_highs)
        support = min(recent_lows)
        
        indicators = {
            'current_volume': current_volume,
            'avg_volume': avg_volume,
            'resistance': resistance,
            'support': support
        }
        
        # Bullish volume breakout
        if (current_volume > avg_volume * vol_thresh and
            current.close > resistance and
            current.is_bullish):
            
            confidence = min(0.85, 0.5 + (current_volume / avg_volume - vol_thresh) * 0.2)
            
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Bullish volume breakout",
                indicators
            )
        
        # Bearish volume breakdown
        elif (current_volume > avg_volume * vol_thresh and
              current.close < support and
              current.is_bearish):
            
            confidence = min(0.85, 0.5 + (current_volume / avg_volume - vol_thresh) * 0.2)
            
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Bearish volume breakdown",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, "No volume breakout detected", indicators)


class TripleConfirmationStrategy(BaseStrategy):
    """Enhanced triple confirmation strategy combining multiple indicators"""
    
    def __init__(self, config: StrategyConfig = None):
        if config is None:
            config = StrategyConfig(
                name="Triple Confirmation",
                parameters={
                    'rsi_period': 9,
                    'ema_period': 8,
                    'momentum_lookback': 3
                }
            )
        super().__init__(config)
    
    def analyze(self, candles: List[Candle]) -> SignalResult:
        rsi_period = self.config.get_param('rsi_period', 9)
        ema_period = self.config.get_param('ema_period', 8)
        momentum_lookback = self.config.get_param('momentum_lookback', 3)
        
        if len(candles) < max(rsi_period, ema_period, momentum_lookback) + 1:
            return SignalResult(TradeDirection.HOLD, 0.0, "Insufficient data")
        
        closes = [c.close for c in candles]
        rsi = self.calculate_rsi(closes, rsi_period)
        ema = self.calculate_ema(closes, ema_period)
        
        current = candles[-1]
        previous = candles[-2]
        
        # Calculate price momentum
        price_momentum = (current.close - candles[-momentum_lookback-1].close) / candles[-momentum_lookback-1].close * 100
        
        indicators = {
            'rsi': rsi,
            'ema': ema,
            'momentum': price_momentum
        }
        
        # Bullish triple confirmation
        bullish_rsi = 20 < rsi < 60
        bullish_ema = current.close > ema
        bullish_momentum = price_momentum > -0.5
        bullish_candle = current.is_bullish
        
        if (bullish_rsi and bullish_ema and bullish_momentum and 
            bullish_candle and current.close > previous.high):
            
            confidence = 0.8
            return SignalResult(
                TradeDirection.CALL,
                confidence,
                f"Triple bullish confirmation",
                indicators
            )
        
        # Bearish triple confirmation
        bearish_rsi = 40 < rsi < 80
        bearish_ema = current.close < ema
        bearish_momentum = price_momentum < 0.5
        bearish_candle = current.is_bearish
        
        if (bearish_rsi and bearish_ema and bearish_momentum and 
            bearish_candle and current.close < previous.low):
            
            confidence = 0.8
            return SignalResult(
                TradeDirection.PUT,
                confidence,
                f"Triple bearish confirmation",
                indicators
            )
        
        return SignalResult(TradeDirection.HOLD, 0.0, "No triple confirmation", indicators)