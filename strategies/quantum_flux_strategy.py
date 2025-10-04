"""Quantum Flux Strategy Engine for Binary Options Trading.

This module implements the core Quantum Flux strategy with:
- Multi-timeframe signal analysis
- Confidence scoring system
- Binary options specific signal generation
- Quantum momentum indicators
- Flux divergence detection
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import talib
from scipy import stats
from sklearn.preprocessing import StandardScaler

from .base import BaseStrategy
from ..core.indicators import TechnicalIndicators
from ..utils.logger import get_logger
from ..utils.exceptions import QuantumFluxError


class SignalDirection(Enum):
    """Signal direction enumeration."""
    CALL = "call"  # Buy/Up signal
    PUT = "put"    # Sell/Down signal
    NEUTRAL = "neutral"  # No signal


class TimeFrame(Enum):
    """Timeframe enumeration."""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    M30 = "30m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"


class QuantumFluxError(QuantumFluxError):
    """Quantum Flux strategy specific error."""
    pass


@dataclass
class QuantumSignal:
    """Quantum Flux signal container."""
    direction: SignalDirection
    confidence: float  # 0.0 to 1.0
    strength: float    # 0.0 to 1.0
    timeframe: TimeFrame
    entry_price: float
    timestamp: datetime
    expiry_minutes: int = 5  # Binary option expiry
    
    # Signal components
    momentum_score: float = 0.0
    flux_score: float = 0.0
    divergence_score: float = 0.0
    volume_score: float = 0.0
    
    # Metadata
    indicators: Dict[str, float] = field(default_factory=dict)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    strategy_name: str = "quantum_flux"  # Strategy identifier
    
    # Configuration thresholds (set by strategy)
    min_confidence_threshold: float = field(default=0.3)
    min_strength_threshold: float = field(default=0.2)
    
    @property
    def is_valid(self) -> bool:
        """Check if signal is valid for trading using configurable thresholds."""
        return (
            self.direction != SignalDirection.NEUTRAL and
            self.confidence >= self.min_confidence_threshold and
            self.strength >= self.min_strength_threshold
        )
    
    def set_validation_thresholds(self, min_confidence: float, min_strength: float) -> None:
        """Set validation thresholds for this signal."""
        self.min_confidence_threshold = min_confidence
        self.min_strength_threshold = min_strength
    
    @property
    def risk_level(self) -> str:
        """Get risk level based on confidence."""
        if self.confidence >= 0.8:
            return "low"
        elif self.confidence >= 0.6:
            return "medium"
        else:
            return "high"


@dataclass
class UnifiedSignalConfig:
    """Unified configuration for signal generation and strategies."""
    # Core signal thresholds - configurable, no hardcoded fallbacks
    min_confidence: float = 0.3
    min_strength: float = 0.2
    signal_threshold: float = 0.2  # Threshold for signal generation (adjusted from 0.4)
    signal_threshold_negative: float = -0.2  # Negative threshold for PUT signals (adjusted from -0.4)
    
    # Strategy selection and consensus
    primary_strategy: str = "quantum_flux"
    enabled_strategies: List[str] = field(default_factory=lambda: ["quantum_flux"])
    enable_multi_strategy_consensus: bool = True
    consensus_threshold: float = 0.7
    
    # Rate limiting
    max_signals_per_hour: int = 12
    cooldown_minutes: int = 3
    
    # Market data requirements
    min_data_points: int = 50
    required_timeframes: List[str] = field(default_factory=lambda: ["1m", "5m", "15m"])
    
    # Binary options specific
    default_expiry_minutes: int = 5
    supported_expiries: List[int] = field(default_factory=lambda: [1, 3, 5, 10, 15, 30])
    
    # Timeframe weights
    timeframe_weights: Dict[TimeFrame, float] = field(default_factory=lambda: {
        TimeFrame.M1: 0.1,
        TimeFrame.M5: 0.2,
        TimeFrame.M15: 0.3,
        TimeFrame.M30: 0.2,
        TimeFrame.H1: 0.15,
        TimeFrame.H4: 0.05
    })
    
    # Indicator parameters
    rsi_period: int = 14
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    bb_period: int = 20
    bb_std: float = 2.0
    
    # Quantum parameters
    quantum_momentum_period: int = 21
    flux_sensitivity: float = 0.7
    divergence_lookback: int = 10
    
    # Performance tracking
    track_signal_performance: bool = True
    performance_window_hours: int = 24


# Backward compatibility alias
QuantumFluxConfig = UnifiedSignalConfig


class QuantumFluxStrategy(BaseStrategy):
    """Quantum Flux strategy for binary options trading."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Quantum Flux Strategy.
        
        Args:
            config: Strategy configuration dictionary
        """
        super().__init__(config)
        self.logger = get_logger(__name__)
        
        # Initialize Quantum Flux specific config
        self.qf_config = UnifiedSignalConfig()
        self._update_config_from_dict(config.get('quantum_flux', {}))
        
        # Initialize technical indicators
        self.indicators = TechnicalIndicators()
        
        # Data storage for multi-timeframe analysis
        self.price_data: Dict[TimeFrame, pd.DataFrame] = {}
        self.signal_history: List[QuantumSignal] = []
        
        # Signal tracking
        self.last_signal_time: Optional[datetime] = None
        self.signals_this_hour = 0
        self.hour_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        
        self.logger.info("Quantum Flux Strategy initialized")
    
    def should_trade(self, indicators: Dict[str, float]) -> bool:
        """
        Determine if a trade should be executed based on indicators.
        
        Args:
            indicators: Dictionary of indicator names and values
            
        Returns:
            True if a trade should be executed
        """
        # Check if we have minimum required indicators
        if not self.validate_indicators(indicators):
            return False
        
        # Calculate signal strength
        strength = self.get_signal_strength(indicators)
        
        # Check if strength meets minimum threshold
        return strength >= self.qf_config.min_strength
    
    def get_signal_strength(self, indicators: Dict[str, float]) -> float:
        """
        Calculate signal strength (0.0 to 1.0).
        
        Args:
            indicators: Dictionary of indicator names and values
            
        Returns:
            Signal strength as a float between 0.0 and 1.0
        """
        try:
            # Calculate individual component scores
            momentum_score = self._calculate_momentum_score(indicators)
            flux_score = self._calculate_flux_score(indicators)
            divergence_score = self._calculate_divergence_score(indicators)
            volume_score = self._calculate_volume_score(indicators)
            
            # Weighted average of all scores
            weights = {
                'momentum': 0.3,
                'flux': 0.3,
                'divergence': 0.2,
                'volume': 0.2
            }
            
            total_strength = (
                momentum_score * weights['momentum'] +
                flux_score * weights['flux'] +
                divergence_score * weights['divergence'] +
                volume_score * weights['volume']
            )
            
            return min(max(total_strength, 0.0), 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating signal strength: {e}")
            return 0.0
    
    def _calculate_momentum_score(self, indicators: Dict[str, float]) -> float:
        """
        Calculate momentum score based on RSI and MACD.
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            Momentum score between 0.0 and 1.0
        """
        try:
            rsi = indicators.get('rsi', 50)
            macd = indicators.get('macd', 0)
            macd_signal = indicators.get('macd_signal', 0)
            
            # RSI momentum (0.3 weight)
            if rsi > 70:
                rsi_score = 0.8  # Overbought - potential reversal
            elif rsi < 30:
                rsi_score = 0.8  # Oversold - potential reversal
            elif 40 <= rsi <= 60:
                rsi_score = 0.3  # Neutral zone
            else:
                rsi_score = 0.6  # Moderate momentum
            
            # MACD momentum (0.7 weight)
            macd_diff = macd - macd_signal
            if abs(macd_diff) > 0.001:
                macd_score = min(abs(macd_diff) * 100, 1.0)
            else:
                macd_score = 0.1
            
            return (rsi_score * 0.3) + (macd_score * 0.7)
            
        except Exception as e:
            self.logger.error(f"Error calculating momentum score: {e}")
            return 0.0
     
    def _calculate_flux_score(self, indicators: Dict[str, float]) -> float:
        """
        Calculate quantum flux score based on price position relative to Bollinger Bands.
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            Flux score between 0.0 and 1.0
        """
        try:
            close = indicators.get('close', 0)
            bb_upper = indicators.get('bb_upper', close)
            bb_lower = indicators.get('bb_lower', close)
            bb_middle = indicators.get('bb_middle', close)
            
            if bb_upper == bb_lower:
                return 0.1  # No volatility
            
            # Calculate position within bands
            bb_range = bb_upper - bb_lower
            position_from_middle = abs(close - bb_middle)
            
            # Higher score when price is near bands (potential reversal)
            if close >= bb_upper or close <= bb_lower:
                return 0.9  # At or beyond bands
            else:
                # Score based on distance from middle
                flux_score = (position_from_middle / (bb_range / 2))
                return min(flux_score, 1.0)
            
        except Exception as e:
            self.logger.error(f"Error calculating flux score: {e}")
            return 0.0
     
    def _calculate_divergence_score(self, indicators: Dict[str, float]) -> float:
        """
        Calculate divergence score based on EMA crossovers.
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            Divergence score between 0.0 and 1.0
        """
        try:
            ema_12 = indicators.get('ema_12', 0)
            ema_26 = indicators.get('ema_26', 0)
            close = indicators.get('close', 0)
            
            if ema_12 == 0 or ema_26 == 0:
                return 0.1
            
            # EMA divergence
            ema_diff = abs(ema_12 - ema_26)
            ema_avg = (ema_12 + ema_26) / 2
            
            if ema_avg > 0:
                ema_divergence = ema_diff / ema_avg
            else:
                ema_divergence = 0
            
            # Price vs EMA divergence
            price_ema_diff = abs(close - ema_12) / close if close > 0 else 0
            
            # Combine scores
            divergence_score = (ema_divergence * 0.6) + (price_ema_diff * 0.4)
            
            return min(divergence_score * 10, 1.0)  # Scale up
            
        except Exception as e:
            self.logger.error(f"Error calculating divergence score: {e}")
            return 0.0
    
    def _calculate_volume_score(self, indicators: Dict[str, float]) -> float:
        """
        Calculate volume score (simplified for binary options).
        
        Args:
            indicators: Dictionary of indicator values
            
        Returns:
            Volume score between 0.0 and 1.0
        """
        try:
            volume = indicators.get('volume', 1)
            
            # For binary options, we use a simplified volume score
            # In real implementation, this would compare to average volume
            if volume > 0:
                # Normalize volume (this is a placeholder)
                volume_score = min(volume / 1000000, 1.0)
                return max(volume_score, 0.1)  # Minimum score
            else:
                return 0.1
            
        except Exception as e:
            self.logger.error(f"Error calculating volume score: {e}")
            return 0.1
     
    def get_required_indicators(self) -> List[str]:
        """
        Return list of required indicator names.
        
        Returns:
            List of required indicator names
        """
        return [
            'rsi',
            'macd',
            'macd_signal',
            'macd_histogram',
            'bb_upper',
            'bb_middle',
            'bb_lower',
            'sma_20',
            'ema_12',
            'ema_26',
            'volume',
            'close',
            'high',
            'low'
        ]
    
    def _update_config_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary."""
        for key, value in config_dict.items():
            if hasattr(self.qf_config, key):
                setattr(self.qf_config, key, value)
    
    def should_trade(self, indicators: Dict[str, float]) -> bool:
        """Determine if a trade should be executed."""
        signal = self.generate_signal(indicators)
        return signal.is_valid if signal else False
    
    def get_signal_strength(self, indicators: Dict[str, float]) -> float:
        """Calculate signal strength."""
        signal = self.generate_signal(indicators)
        return signal.strength if signal else 0.0
    
    def generate_signal(self, 
                       market_data: Dict[str, Any],
                       timeframe: TimeFrame = TimeFrame.M5) -> Optional[QuantumSignal]:
        """
        Generate Quantum Flux signal for binary options.
        
        Args:
            market_data: Market data including OHLCV
            timeframe: Primary timeframe for signal generation
            
        Returns:
            QuantumSignal or None if no valid signal
        """
        try:
            # Check signal rate limits
            if not self._can_generate_signal():
                return None
            
            # Extract price data
            if 'ohlcv' not in market_data:
                self.logger.warning("No OHLCV data provided")
                return None
            
            df = market_data['ohlcv']
            if len(df) < 50:  # Need sufficient data
                self.logger.warning("Insufficient data for signal generation")
                return None
            
            current_price = df['close'].iloc[-1]
            
            # Calculate quantum indicators
            quantum_indicators = self._calculate_quantum_indicators(df)
            
            # Multi-timeframe analysis
            mtf_signals = self._multi_timeframe_analysis(market_data)
            
            # Generate primary signal
            primary_signal = self._generate_primary_signal(
                df, quantum_indicators, timeframe, current_price
            )
            
            if not primary_signal:
                return None
            
            # Enhance with multi-timeframe confluence
            enhanced_signal = self._enhance_with_mtf_confluence(
                primary_signal, mtf_signals
            )
            
            # Apply final filters
            if self._apply_signal_filters(enhanced_signal, market_data):
                self._update_signal_tracking(enhanced_signal)
                self.signal_history.append(enhanced_signal)
                return enhanced_signal
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error generating signal: {e}")
            return None
    
    def _calculate_quantum_indicators(self, df: pd.DataFrame) -> Dict[str, np.ndarray]:
        """
        Calculate Quantum Flux specific indicators.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dictionary of quantum indicators
        """
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values if 'volume' in df.columns else np.ones_like(close)
        
        indicators = {}
        
        # Quantum Momentum Oscillator
        indicators['qmo'] = self._quantum_momentum_oscillator(close)
        
        # Flux Divergence Index
        indicators['fdi'] = self._flux_divergence_index(close, volume)
        
        # Quantum Wave Indicator
        indicators['qwi'] = self._quantum_wave_indicator(high, low, close)
        
        # Flux Volatility Ratio
        indicators['fvr'] = self._flux_volatility_ratio(close)
        
        # Quantum Support/Resistance
        indicators['qsr'] = self._quantum_support_resistance(high, low, close)
        
        return indicators
    
    def _quantum_momentum_oscillator(self, close: np.ndarray) -> np.ndarray:
        """
        Calculate Quantum Momentum Oscillator.
        
        Args:
            close: Close prices
            
        Returns:
            QMO values
        """
        period = self.qf_config.quantum_momentum_period
        
        # Calculate momentum components
        roc = np.zeros_like(close)
        roc[period:] = ((close[period:] - close[:-period]) / close[:-period]) * 100
        
        # Apply quantum transformation (non-linear scaling) with increased sensitivity
        qmo = np.tanh(roc / 15) * 100  # Increased divisor from 10 to 15 for better sensitivity
        
        # Smooth with adaptive filter
        alpha = 2 / (period + 1)
        qmo_smooth = np.zeros_like(qmo)
        qmo_smooth[0] = qmo[0]
        
        for i in range(1, len(qmo)):
            qmo_smooth[i] = alpha * qmo[i] + (1 - alpha) * qmo_smooth[i-1]
        
        return qmo_smooth
    
    def _flux_divergence_index(self, close: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """
        Calculate Flux Divergence Index.
        
        Args:
            close: Close prices
            volume: Volume data
            
        Returns:
            FDI values
        """
        # Price momentum
        price_momentum = np.gradient(close)
        
        # Volume momentum
        volume_momentum = np.gradient(volume)
        
        # Simple normalization to preserve signal strength
        # Normalize by standard deviation instead of StandardScaler
        price_std = np.std(price_momentum) if np.std(price_momentum) > 0 else 1
        volume_std = np.std(volume_momentum) if np.std(volume_momentum) > 0 else 1
        
        price_norm = price_momentum / price_std
        volume_norm = volume_momentum / volume_std
        
        # Calculate divergence
        divergence = price_norm - volume_norm
        
        # Apply flux transformation with increased sensitivity
        fdi = np.tanh(divergence * self.qf_config.flux_sensitivity * 1.5) * 100
        
        return fdi
    
    def _quantum_wave_indicator(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """
        Calculate Quantum Wave Indicator.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            
        Returns:
            QWI values
        """
        # Calculate typical price
        typical_price = (high + low + close) / 3
        
        # Calculate wave components
        period = 14
        wave_1 = np.sin(2 * np.pi * np.arange(len(close)) / period)
        wave_2 = np.cos(2 * np.pi * np.arange(len(close)) / (period * 2))
        
        # Price-adjusted waves
        price_change = np.gradient(typical_price)
        qwi = (wave_1 + wave_2) * np.tanh(price_change * 10) * 50
        
        return qwi
    
    def _flux_volatility_ratio(self, close: np.ndarray) -> np.ndarray:
        """
        Calculate Flux Volatility Ratio.
        
        Args:
            close: Close prices
            
        Returns:
            FVR values
        """
        # Short-term volatility (5 periods)
        short_vol = pd.Series(close).rolling(5).std().values
        
        # Long-term volatility (20 periods)
        long_vol = pd.Series(close).rolling(20).std().values
        
        # Volatility ratio
        fvr = np.zeros_like(close)
        mask = long_vol != 0
        fvr[mask] = short_vol[mask] / long_vol[mask]
        
        # Normalize to -100 to 100
        fvr = (fvr - 1) * 100
        
        return fvr
    
    def _quantum_support_resistance(self, high: np.ndarray, low: np.ndarray, close: np.ndarray) -> np.ndarray:
        """
        Calculate Quantum Support/Resistance levels.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            
        Returns:
            QSR values (-100 to 100, negative = support, positive = resistance)
        """
        qsr = np.zeros_like(close)
        lookback = 20
        
        for i in range(lookback, len(close)):
            recent_high = np.max(high[i-lookback:i])
            recent_low = np.min(low[i-lookback:i])
            current_price = close[i]
            
            # Calculate position within range
            if recent_high != recent_low:
                position = (current_price - recent_low) / (recent_high - recent_low)
                # Convert to -100 to 100 scale
                qsr[i] = (position - 0.5) * 200
            
        return qsr
    
    def _generate_primary_signal(self, 
                               df: pd.DataFrame,
                               quantum_indicators: Dict[str, np.ndarray],
                               timeframe: TimeFrame,
                               current_price: float) -> Optional[QuantumSignal]:
        """
        Generate primary signal based on quantum indicators.
        
        Args:
            df: OHLCV DataFrame
            quantum_indicators: Calculated quantum indicators
            timeframe: Signal timeframe
            current_price: Current market price
            
        Returns:
            Primary QuantumSignal or None
        """
        # Get latest indicator values
        qmo = quantum_indicators['qmo'][-1]
        fdi = quantum_indicators['fdi'][-1]
        qwi = quantum_indicators['qwi'][-1]
        fvr = quantum_indicators['fvr'][-1]
        qsr = quantum_indicators['qsr'][-1]
        
        # Calculate component scores
        momentum_score = self._calculate_momentum_score(qmo, fdi)
        flux_score = self._calculate_flux_score(qwi, fvr)
        divergence_score = self._calculate_divergence_score(quantum_indicators)
        volume_score = self._calculate_volume_score(df)
        
        # Determine signal direction
        total_score = (momentum_score + flux_score + divergence_score + volume_score) / 4
        
        self.logger.debug(f"Signal generation scores - Momentum: {momentum_score:.3f}, Flux: {flux_score:.3f}, Divergence: {divergence_score:.3f}, Volume: {volume_score:.3f}, Total: {total_score:.3f}")
        self.logger.debug(f"Signal thresholds - Positive: {self.qf_config.signal_threshold}, Negative: {self.qf_config.signal_threshold_negative}")
        
        if total_score > self.qf_config.signal_threshold:
            direction = SignalDirection.CALL
            self.logger.debug(f"Generated CALL signal with score {total_score:.3f} > {self.qf_config.signal_threshold}")
        elif total_score < self.qf_config.signal_threshold_negative:
            direction = SignalDirection.PUT
            self.logger.debug(f"Generated PUT signal with score {total_score:.3f} < {self.qf_config.signal_threshold_negative}")
        else:
            direction = SignalDirection.NEUTRAL
            self.logger.debug(f"No signal generated - score {total_score:.3f} within neutral range [{self.qf_config.signal_threshold_negative}, {self.qf_config.signal_threshold}]")
        
        if direction == SignalDirection.NEUTRAL:
            return None
        
        # Calculate confidence and strength
        confidence = min(abs(total_score), 1.0)
        strength = self._calculate_signal_strength(quantum_indicators)
        
        self.logger.debug(f"Signal metrics - Confidence: {confidence:.3f}, Strength: {strength:.3f}")
        self.logger.debug(f"Validation thresholds - Min confidence: {self.qf_config.min_confidence}, Min strength: {self.qf_config.min_strength}")
        
        # Create signal
        signal = QuantumSignal(
            direction=direction,
            confidence=confidence,
            strength=strength,
            timeframe=timeframe,
            entry_price=current_price,
            timestamp=datetime.now(),
            expiry_minutes=self.qf_config.default_expiry_minutes,
            momentum_score=momentum_score,
            flux_score=flux_score,
            divergence_score=divergence_score,
            volume_score=volume_score,
            indicators={
                'qmo': qmo,
                'fdi': fdi,
                'qwi': qwi,
                'fvr': fvr,
                'qsr': qsr
            },
            min_confidence_threshold=self.qf_config.min_confidence,
            min_strength_threshold=self.qf_config.min_strength
        )
        
        return signal
    
    def _calculate_momentum_score(self, qmo: float, fdi: float) -> float:
        """
        Calculate momentum component score.
        
        Args:
            qmo: Quantum Momentum Oscillator value
            fdi: Flux Divergence Index value
            
        Returns:
            Momentum score (-1 to 1)
        """
        # Normalize QMO (-100 to 100) to (-1 to 1)
        qmo_norm = qmo / 100
        
        # Normalize FDI (-100 to 100) to (-1 to 1)
        fdi_norm = fdi / 100
        
        # Combine with weights
        momentum_score = 0.7 * qmo_norm + 0.3 * fdi_norm
        
        return np.clip(momentum_score, -1, 1)
    
    def _calculate_flux_score(self, qwi: float, fvr: float) -> float:
        """
        Calculate flux component score.
        
        Args:
            qwi: Quantum Wave Indicator value
            qwi: Flux Volatility Ratio value
            
        Returns:
            Flux score (-1 to 1)
        """
        # Normalize QWI to (-1 to 1) with increased sensitivity
        qwi_norm = np.tanh(qwi / 35)  # Reduced from 50 to 35 for better sensitivity
        
        # Normalize FVR with increased sensitivity
        fvr_norm = np.tanh(fvr / 35)  # Reduced from 50 to 35 for better sensitivity
        
        # Combine
        flux_score = 0.6 * qwi_norm + 0.4 * fvr_norm
        
        return np.clip(flux_score, -1, 1)
    
    def _calculate_divergence_score(self, quantum_indicators: Dict[str, np.ndarray]) -> float:
        """
        Calculate divergence component score.
        
        Args:
            quantum_indicators: All quantum indicators
            
        Returns:
            Divergence score (-1 to 1)
        """
        lookback = self.qf_config.divergence_lookback
        
        # Get recent values
        qmo_recent = quantum_indicators['qmo'][-lookback:]
        fdi_recent = quantum_indicators['fdi'][-lookback:]
        
        # Calculate trends
        qmo_trend = np.polyfit(range(len(qmo_recent)), qmo_recent, 1)[0]
        fdi_trend = np.polyfit(range(len(fdi_recent)), fdi_recent, 1)[0]
        
        # Divergence occurs when trends are opposite
        if qmo_trend * fdi_trend < 0:  # Opposite signs
            divergence_score = abs(qmo_trend - fdi_trend) / 10
        else:
            divergence_score = 0
        
        return np.clip(divergence_score, -1, 1)
    
    def _calculate_volume_score(self, df: pd.DataFrame) -> float:
        """
        Calculate volume component score.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Volume score (-1 to 1)
        """
        if 'volume' not in df.columns:
            return 0.0
        
        volume = df['volume'].values
        if len(volume) < 20:
            return 0.0
        
        # Compare recent volume to average
        recent_volume = np.mean(volume[-5:])
        avg_volume = np.mean(volume[-20:])
        
        if avg_volume == 0:
            return 0.0
        
        volume_ratio = recent_volume / avg_volume
        
        # Convert to score
        if volume_ratio > 1.5:
            volume_score = 0.5
        elif volume_ratio > 1.2:
            volume_score = 0.3
        elif volume_ratio < 0.8:
            volume_score = -0.3
        else:
            volume_score = 0.0
        
        return volume_score
    
    def _calculate_signal_strength(self, quantum_indicators: Dict[str, np.ndarray]) -> float:
        """
        Calculate overall signal strength.
        
        Args:
            quantum_indicators: All quantum indicators
            
        Returns:
            Signal strength (0 to 1)
        """
        # Get latest values
        qmo = abs(quantum_indicators['qmo'][-1])
        fdi = abs(quantum_indicators['fdi'][-1])
        qwi = abs(quantum_indicators['qwi'][-1])
        fvr = abs(quantum_indicators['fvr'][-1])
        
        # Normalize and combine
        strength_components = [
            qmo / 100,
            fdi / 100,
            qwi / 50,
            fvr / 50
        ]
        
        strength = np.mean(strength_components)
        return np.clip(strength, 0, 1)
    
    def _multi_timeframe_analysis(self, market_data: Dict[str, Any]) -> Dict[TimeFrame, float]:
        """
        Perform multi-timeframe analysis.
        
        Args:
            market_data: Market data for different timeframes
            
        Returns:
            Dictionary of timeframe -> signal score
        """
        mtf_signals = {}
        
        # For now, simulate MTF analysis
        # In production, this would analyze multiple timeframe data
        for tf in [TimeFrame.M1, TimeFrame.M5, TimeFrame.M15, TimeFrame.M30]:
            # Simplified MTF score calculation
            if 'ohlcv' in market_data:
                df = market_data['ohlcv']
                if len(df) >= 20:
                    # Calculate simple trend score for this timeframe
                    close = df['close'].values
                    sma_short = np.mean(close[-5:])
                    sma_long = np.mean(close[-20:])
                    
                    if sma_long != 0:
                        trend_score = (sma_short - sma_long) / sma_long
                        mtf_signals[tf] = np.clip(trend_score * 10, -1, 1)
                    else:
                        mtf_signals[tf] = 0.0
                else:
                    mtf_signals[tf] = 0.0
            else:
                mtf_signals[tf] = 0.0
        
        return mtf_signals
    
    def _enhance_with_mtf_confluence(self, 
                                   primary_signal: QuantumSignal,
                                   mtf_signals: Dict[TimeFrame, float]) -> QuantumSignal:
        """
        Enhance signal with multi-timeframe confluence.
        
        Args:
            primary_signal: Primary signal
            mtf_signals: Multi-timeframe signals
            
        Returns:
            Enhanced signal
        """
        # Calculate weighted MTF score
        mtf_score = 0.0
        total_weight = 0.0
        
        for tf, score in mtf_signals.items():
            weight = self.qf_config.timeframe_weights.get(tf, 0.1)
            mtf_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            mtf_score /= total_weight
        
        # Adjust confidence based on MTF confluence
        direction_multiplier = 1 if primary_signal.direction == SignalDirection.CALL else -1
        confluence = mtf_score * direction_multiplier
        
        if confluence > 0:  # MTF agrees with primary signal
            primary_signal.confidence = min(primary_signal.confidence * (1 + confluence * 0.3), 1.0)
        else:  # MTF disagrees
            primary_signal.confidence = max(primary_signal.confidence * (1 + confluence * 0.5), 0.0)
        
        # Store MTF data in metadata
        primary_signal.market_conditions['mtf_signals'] = mtf_signals
        primary_signal.market_conditions['mtf_confluence'] = confluence
        
        return primary_signal
    
    def _apply_signal_filters(self, signal: QuantumSignal, market_data: Dict[str, Any]) -> bool:
        """
        Apply market condition adjustments to the signal.
        This is the ONLY validation layer in the strategy - simplified from multiple layers.
        
        Args:
            signal: Generated signal
            market_data: Market data
            
        Returns:
            True if signal passes final validation
        """
        # Market hours adjustment (not a filter, just adjustment)
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # Outside major trading hours
            signal.confidence *= 0.8  # Reduce confidence
        
        # Volatility adjustment (not a filter, just adjustment)
        if 'ohlcv' in market_data:
            df = market_data['ohlcv']
            if len(df) >= 20:
                recent_volatility = df['close'].pct_change().rolling(20).std().iloc[-1]
                if recent_volatility > 0.05:  # High volatility
                    signal.confidence *= 0.9
        
        # Final validation using the signal's own thresholds (set from config)
        is_valid = signal.is_valid
        self.logger.debug(f"Signal validation result: {is_valid} (confidence: {signal.confidence:.3f} >= {signal.min_confidence_threshold}, strength: {signal.strength:.3f} >= {signal.min_strength_threshold})")
        return is_valid
    
    def _can_generate_signal(self) -> bool:
        """
        Check if we can generate a new signal based on rate limits.
        
        Returns:
            True if signal can be generated
        """
        now = datetime.now()
        
        # Reset hourly counter
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        if current_hour > self.hour_reset_time:
            self.signals_this_hour = 0
            self.hour_reset_time = current_hour
        
        self.logger.debug(f"Rate limiting check - Hourly signals: {self.signals_this_hour}/{self.qf_config.max_signals_per_hour}")
        
        # Check hourly limit
        if self.signals_this_hour >= self.qf_config.max_signals_per_hour:
            self.logger.debug(f"Signal generation blocked - hourly limit reached ({self.signals_this_hour}/{self.qf_config.max_signals_per_hour})")
            return False
        
        # Check cooldown period
        if self.last_signal_time:
            time_since_last = (now - self.last_signal_time).total_seconds() / 60
            self.logger.debug(f"Cooldown check - Time since last signal: {time_since_last:.1f} minutes (required: {self.qf_config.cooldown_minutes})")
            if time_since_last < self.qf_config.cooldown_minutes:
                self.logger.debug(f"Signal generation blocked - cooldown period active ({time_since_last:.1f} < {self.qf_config.cooldown_minutes} minutes)")
                return False
        
        self.logger.debug("Rate limiting check passed - signal generation allowed")
        return True
    
    def _update_signal_tracking(self, signal: QuantumSignal) -> None:
        """
        Update signal tracking variables.
        
        Args:
            signal: Generated signal
        """
        self.last_signal_time = signal.timestamp
        self.signals_this_hour += 1
    
    def get_strategy_status(self) -> Dict[str, Any]:
        """
        Get current strategy status.
        
        Returns:
            Strategy status dictionary
        """
        return {
            'name': 'Quantum Flux Strategy',
            'version': '1.0.0',
            'signals_generated': len(self.signal_history),
            'signals_this_hour': self.signals_this_hour,
            'last_signal_time': self.last_signal_time.isoformat() if self.last_signal_time else None,
            'can_generate_signal': self._can_generate_signal(),
            'config': {
                'min_confidence': self.qf_config.min_confidence,
                'min_strength': self.qf_config.min_strength,
                'default_expiry': self.qf_config.default_expiry_minutes,
                'max_signals_per_hour': self.qf_config.max_signals_per_hour,
                'cooldown_minutes': self.qf_config.cooldown_minutes
            }
        }
    
    def get_recent_signals(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent signals.
        
        Args:
            limit: Maximum number of signals to return
            
        Returns:
            List of recent signals
        """
        recent_signals = self.signal_history[-limit:] if self.signal_history else []
        
        return [{
            'direction': signal.direction.value,
            'confidence': signal.confidence,
            'strength': signal.strength,
            'timeframe': signal.timeframe.value,
            'entry_price': signal.entry_price,
            'timestamp': signal.timestamp.isoformat(),
            'expiry_minutes': signal.expiry_minutes,
            'risk_level': signal.risk_level,
            'is_valid': signal.is_valid,
            'scores': {
                'momentum': signal.momentum_score,
                'flux': signal.flux_score,
                'divergence': signal.divergence_score,
                'volume': signal.volume_score
            }
        } for signal in recent_signals]
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Update strategy configuration.
        
        Args:
            new_config: New configuration parameters
        """
        self._update_config_from_dict(new_config)
        self.logger.info("Quantum Flux strategy configuration updated")
    
    def reset_signal_history(self) -> None:
        """
        Reset signal history (useful for backtesting).
        """
        self.signal_history.clear()
        self.last_signal_time = None
        self.signals_this_hour = 0
        self.hour_reset_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        self.logger.info("Signal history reset")