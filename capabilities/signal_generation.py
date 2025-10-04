from __future__ import annotations

from typing import Any, Dict, Optional, Tuple, List
import json

from .base import Ctx, CapResult, Capability, timestamp, save_json


class SignalGeneration(Capability):
    """
    Capability for generating trading signals for specific assets.

    Interface inputs:
      - asset: str (required) - Asset symbol (e.g., 'EURUSD')
      - min_candles: int = 30 - Minimum candles required for analysis
      - signal_types: List[str] = ["SMA", "RSI", "MACD"] - Types of signals to generate

    Behavior:
      - Analyzes recent candle data for the specified asset
      - Generates technical analysis signals
      - Returns signal data with confidence scores
    Kind: "read"
    """
    id = "signal_generation"
    kind = "read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        asset = inputs.get("asset", "").strip().upper()
        min_candles = int(inputs.get("min_candles", 30))
        signal_types = inputs.get("signal_types", ["SMA", "RSI", "MACD"])

        if not asset:
            return CapResult(ok=False, data={"inputs": inputs}, error="asset is required", artifacts=())

        try:
            # Check if real candle data was provided directly (from adapter)
            real_candles = inputs.get("real_candles")
            if real_candles and len(real_candles) >= min_candles:
                # Use provided real candle data
                signals = self._generate_signals(real_candles, signal_types)
                candles_analyzed = len(real_candles)
                data_source = "real_time_data"
            else:
                # Try to get real candle data from data streaming capability
                candles = self._get_candle_data(ctx, asset, min_candles)

                if candles and len(candles) >= min_candles:
                    # Generate signals from real candle data
                    signals = self._generate_signals(candles, signal_types)
                    candles_analyzed = len(candles)
                    data_source = "real_time_data"
                else:
                    # Fallback to mock signals if no real data available
                    signals = self._generate_mock_signals(asset, signal_types)
                    candles_analyzed = 0
                    data_source = "mock_data_fallback"

            # Save signal data if debug is enabled
            artifacts = []
            if ctx.debug:
                signal_data = {
                    "asset": asset,
                    "timestamp": timestamp(),
                    "signals": signals,
                    "signal_types": signal_types,
                    "candles_analyzed": candles_analyzed,
                    "data_source": data_source
                }
                artifacts.append(save_json(ctx, f"signal_generation_{asset}_{timestamp()}.json", signal_data, "signals"))

            return CapResult(
                ok=True,
                data={
                    "asset": asset,
                    "signals": signals,
                    "candles_analyzed": candles_analyzed,
                    "signal_types": signal_types,
                    "data_source": data_source
                },
                artifacts=tuple(artifacts)
            )

        except Exception as e:
            return CapResult(ok=False, data={"asset": asset, "inputs": inputs}, error=f"Signal generation failed: {str(e)}", artifacts=())

    def _generate_signals(self, candles: List[List], signal_types: List[str]) -> Dict[str, Any]:
        """Generate trading signals from candle data."""
        signals = {}

        try:
            # Simple signal generation logic (can be enhanced with real technical analysis)
            if "SMA" in signal_types:
                signals["SMA"] = self._calculate_sma_signal(candles)

            if "RSI" in signal_types:
                signals["RSI"] = self._calculate_rsi_signal(candles)

            if "MACD" in signal_types:
                signals["MACD"] = self._calculate_macd_signal(candles)

        except Exception as e:
            signals["error"] = f"Signal calculation failed: {str(e)}"

        return signals

    def _calculate_sma_signal(self, candles: List[List]) -> Dict[str, Any]:
        """Calculate Simple Moving Average signal."""
        if len(candles) < 20:
            return {"signal": "insufficient_data", "confidence": 0.0}

        # Simple SMA crossover logic
        closes = [candle[4] if len(candle) > 4 else 0 for candle in candles[-20:]]

        if len(closes) < 20:
            return {"signal": "insufficient_data", "confidence": 0.0}

        sma_10 = sum(closes[-10:]) / 10
        sma_20 = sum(closes) / 20

        if sma_10 > sma_20:
            return {"signal": "bullish", "confidence": 0.6, "sma_10": sma_10, "sma_20": sma_20}
        elif sma_10 < sma_20:
            return {"signal": "bearish", "confidence": 0.6, "sma_10": sma_10, "sma_20": sma_20}
        else:
            return {"signal": "neutral", "confidence": 0.3, "sma_10": sma_10, "sma_20": sma_20}

    def _calculate_rsi_signal(self, candles: List[List]) -> Dict[str, Any]:
        """Calculate RSI signal."""
        if len(candles) < 14:
            return {"signal": "insufficient_data", "confidence": 0.0}

        # Simplified RSI calculation
        closes = [candle[4] if len(candle) > 4 else 0 for candle in candles[-14:]]

        if len(closes) < 14:
            return {"signal": "insufficient_data", "confidence": 0.0}

        gains = []
        losses = []

        for i in range(1, len(closes)):
            change = closes[i] - closes[i-1]
            if change > 0:
                gains.append(change)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(change))

        avg_gain = sum(gains) / 14
        avg_loss = sum(losses) / 14

        if avg_loss == 0:
            rsi = 100
        else:
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

        if rsi > 70:
            return {"signal": "overbought", "confidence": 0.7, "rsi": rsi}
        elif rsi < 30:
            return {"signal": "oversold", "confidence": 0.7, "rsi": rsi}
        else:
            return {"signal": "neutral", "confidence": 0.4, "rsi": rsi}

    def _calculate_macd_signal(self, candles: List[List]) -> Dict[str, Any]:
        """Calculate MACD signal."""
        if len(candles) < 26:
            return {"signal": "insufficient_data", "confidence": 0.0}

        closes = [candle[4] if len(candle) > 4 else 0 for candle in candles[-26:]]

        if len(closes) < 26:
            return {"signal": "insufficient_data", "confidence": 0.0}

        # Simplified MACD calculation
        ema_12 = self._calculate_ema(closes, 12)
        ema_26 = self._calculate_ema(closes, 26)

        if ema_12 is None or ema_26 is None:
            return {"signal": "insufficient_data", "confidence": 0.0}

        macd = ema_12 - ema_26

        if macd > 0:
            return {"signal": "bullish", "confidence": 0.5, "macd": macd}
        elif macd < 0:
            return {"signal": "bearish", "confidence": 0.5, "macd": macd}
        else:
            return {"signal": "neutral", "confidence": 0.3, "macd": macd}

    def _calculate_ema(self, prices: List[float], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(prices) < period:
            return None

        multiplier = 2 / (period + 1)
        ema = prices[0]

        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))

        return ema

    def _get_candle_data(self, ctx: Ctx, asset: str, min_candles: int) -> Optional[List[List]]:
        """Get candle data for the specified asset from data streaming capability."""
        try:
            # Import data streaming capability
            from .data_streaming import RealtimeDataStreaming

            # Create data streaming instance and get candle data
            data_streaming = RealtimeDataStreaming()

            # Try to get candle data - this assumes the data streaming has been run previously
            # In a real implementation, we might need to run data collection first
            if hasattr(data_streaming, 'CANDLES') and asset in data_streaming.CANDLES:
                candles = data_streaming.CANDLES[asset]
                if len(candles) >= min_candles:
                    return candles[-min_candles:]  # Return the most recent candles

            # If no data available, try to run data collection
            # This is a simplified approach - in production, data streaming should be running continuously
            result = data_streaming.run(ctx, {"period": 60})  # 1 minute period
            if result.ok and hasattr(data_streaming, 'CANDLES') and asset in data_streaming.CANDLES:
                candles = data_streaming.CANDLES[asset]
                if len(candles) >= min_candles:
                    return candles[-min_candles:]

            return None

        except Exception as e:
            if ctx.verbose:
                print(f"Warning: Could not get real candle data for {asset}: {e}")
            return None

    def _generate_mock_signals(self, asset: str, signal_types: List[str]) -> Dict[str, Any]:
        """Generate mock signals for demonstration purposes."""
        import random
        signals = {}

        # Generate mock signals based on asset and signal types
        for signal_type in signal_types:
            if signal_type == "SMA":
                # Random bullish/bearish/neutral
                signal_options = ["bullish", "bearish", "neutral"]
                signal = random.choice(signal_options)
                confidence = random.uniform(0.3, 0.8)
                signals["SMA"] = {
                    "signal": signal,
                    "confidence": round(confidence, 2),
                    "sma_10": round(random.uniform(1.05, 1.15), 4),
                    "sma_20": round(random.uniform(1.04, 1.14), 4)
                }
            elif signal_type == "RSI":
                rsi_value = random.uniform(20, 80)
                if rsi_value > 70:
                    signal = "overbought"
                    confidence = random.uniform(0.6, 0.8)
                elif rsi_value < 30:
                    signal = "oversold"
                    confidence = random.uniform(0.6, 0.8)
                else:
                    signal = "neutral"
                    confidence = random.uniform(0.3, 0.5)
                signals["RSI"] = {
                    "signal": signal,
                    "confidence": round(confidence, 2),
                    "rsi": round(rsi_value, 2)
                }
            elif signal_type == "MACD":
                macd_value = random.uniform(-0.01, 0.01)
                if macd_value > 0:
                    signal = "bullish"
                    confidence = random.uniform(0.4, 0.7)
                elif macd_value < 0:
                    signal = "bearish"
                    confidence = random.uniform(0.4, 0.7)
                else:
                    signal = "neutral"
                    confidence = random.uniform(0.2, 0.4)
                signals["MACD"] = {
                    "signal": signal,
                    "confidence": round(confidence, 2),
                    "macd": round(macd_value, 4)
                }

        return signals


# Factory for orchestrator
def build() -> Capability:
    return SignalGeneration()