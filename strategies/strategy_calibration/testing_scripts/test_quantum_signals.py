#!/usr/bin/env python3
"""
Quantum Flux Strategy Signal Testing
Tests the quantum_flux strategy signal generation with various indicators.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List
import json
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

class QuantumFluxTester:
    """Test the quantum_flux strategy signal generation."""
    
    def __init__(self, config_path: str = "config/strategies/quantum_flux.json"):
        self.strategy_config = self.load_strategy_config(config_path)
        self.indicators_config = self.strategy_config.get('indicators', {})
        self.thresholds = self.strategy_config.get('strategy', {}).get('thresholds', {})
        
    def load_strategy_config(self, config_path: str) -> Dict[str, Any]:
        """Load strategy configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def calculate_simple_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI using simple method."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_simple_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD using simple EMA method."""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(span=signal).mean()
        macd_hist = macd_line - macd_signal
        return macd_line, macd_signal, macd_hist
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0):
        """Calculate Bollinger Bands."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper_band = sma + (std * std_dev)
        lower_band = sma - (std * std_dev)
        return upper_band, sma, lower_band
    
    def calculate_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
        """Calculate Stochastic Oscillator."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Average True Range."""
        high_low = high - low
        high_close = np.abs(high - close.shift())
        low_close = np.abs(low - close.shift())
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        atr = true_range.rolling(window=period).mean()
        return atr
    
    def generate_signal(self, data: pd.DataFrame, min_strength: float = 0.3) -> Dict[str, Any]:
        """Generate trading signal based on quantum_flux strategy."""
        if len(data) < 50:  # Need enough data for indicators
            return {'signal': 'HOLD', 'strength': 0.0, 'confidence': 0.0, 'reasons': []}
        
        # Ensure volume column exists
        if 'volume' not in data.columns:
            data['volume'] = 0
        
        # Calculate indicators
        rsi = self.calculate_simple_rsi(data['close'])
        macd_line, macd_signal, macd_hist = self.calculate_simple_macd(data['close'])
        bb_upper, bb_middle, bb_lower = self.calculate_bollinger_bands(data['close'])
        stoch_k, stoch_d = self.calculate_stochastic(data['high'], data['low'], data['close'])
        atr = self.calculate_atr(data['high'], data['low'], data['close'])
        
        # Get latest values
        latest_idx = len(data) - 1
        current_price = data['close'].iloc[latest_idx]
        current_rsi = rsi.iloc[latest_idx] if not pd.isna(rsi.iloc[latest_idx]) else 50
        current_macd = macd_line.iloc[latest_idx] if not pd.isna(macd_line.iloc[latest_idx]) else 0
        current_macd_signal = macd_signal.iloc[latest_idx] if not pd.isna(macd_signal.iloc[latest_idx]) else 0
        current_bb_upper = bb_upper.iloc[latest_idx] if not pd.isna(bb_upper.iloc[latest_idx]) else current_price
        current_bb_lower = bb_lower.iloc[latest_idx] if not pd.isna(bb_lower.iloc[latest_idx]) else current_price
        current_stoch_k = stoch_k.iloc[latest_idx] if not pd.isna(stoch_k.iloc[latest_idx]) else 50
        current_atr = atr.iloc[latest_idx] if not pd.isna(atr.iloc[latest_idx]) else 0.001
        
        # Signal generation logic
        buy_signals = 0
        sell_signals = 0
        reasons = []
        
        # RSI signals
        if current_rsi < 30:
            buy_signals += 1
            reasons.append("RSI oversold")
        elif current_rsi > 70:
            sell_signals += 1
            reasons.append("RSI overbought")
        
        # MACD signals
        if current_macd > current_macd_signal:
            buy_signals += 1
            reasons.append("MACD bullish")
        else:
            sell_signals += 1
            reasons.append("MACD bearish")
        
        # Bollinger Bands signals
        if current_price <= current_bb_lower:
            buy_signals += 1
            reasons.append("Near BB lower")
        elif current_price >= current_bb_upper:
            sell_signals += 1
            reasons.append("Near BB upper")
        
        # Stochastic signals
        if current_stoch_k < 20:
            buy_signals += 1
            reasons.append("Stoch oversold")
        elif current_stoch_k > 80:
            sell_signals += 1
            reasons.append("Stoch overbought")
        
        # Calculate signal strength
        total_signals = buy_signals + sell_signals
        if total_signals == 0:
            return {'signal': 'HOLD', 'strength': 0.0, 'confidence': 0.0, 'reasons': ['No clear signals']}
        
        strength = max(buy_signals, sell_signals) / 4.0  # Max 4 indicators
        confidence = min(strength * 1.5, 1.0)  # Boost confidence slightly
        
        # Determine signal
        if strength >= min_strength:
            if buy_signals > sell_signals:
                signal = 'BUY'
            elif sell_signals > buy_signals:
                signal = 'SELL'
            else:
                signal = 'HOLD'
        else:
            signal = 'HOLD'
        
        return {
            'signal': signal,
            'strength': strength,
            'confidence': confidence,
            'reasons': reasons,
            'indicators': {
                'rsi': current_rsi,
                'macd': current_macd,
                'macd_signal': current_macd_signal,
                'bb_position': (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower) if current_bb_upper != current_bb_lower else 0.5,
                'stoch_k': current_stoch_k,
                'atr': current_atr
            }
        }
    
    def test_data_files(self, data_dir: str = "../../../../../data/data_5m", max_files: int = 10):
        """Test signal generation on multiple data files."""
        print("🚀 Testing Quantum-Flux Strategy Signal Generation")
        print("=" * 60)
        
        # Display strategy configuration
        print(f"📊 Strategy Configuration:")
        print(f"   Indicators: {list(self.indicators_config.keys()) if self.indicators_config else 'Default set'}")
        print(f"   Thresholds: {self.thresholds if self.thresholds else 'Default values'}")
        print()
        
        if not os.path.exists(data_dir):
            print(f"❌ Data directory not found: {data_dir}")
            return
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            print(f"❌ No CSV files found in {data_dir}")
            return
        
        # Limit files for testing
        test_files = csv_files[:max_files]
        print(f"📁 Found {len(csv_files)} files, testing {len(test_files)} files")
        print()
        
        total_signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        strong_signals = 0
        total_strength = 0
        processed_files = 0
        
        for filename in test_files:
            filepath = os.path.join(data_dir, filename)
            try:
                # Load data
                data = pd.read_csv(filepath)
                
                # Check required columns
                required_cols = ['open', 'high', 'low', 'close']
                missing_cols = [col for col in required_cols if col not in data.columns]
                if missing_cols:
                    print(f"⚠️  {filename}: Missing columns: {missing_cols}")
                    continue
                
                # Generate signal
                signal_result = self.generate_signal(data)
                
                # Update statistics
                total_signals[signal_result['signal']] += 1
                total_strength += signal_result['strength']
                if signal_result['strength'] >= 0.5:
                    strong_signals += 1
                processed_files += 1
                
                # Display result
                signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[signal_result['signal']]
                print(f"{signal_emoji} {filename[:20]:20} | {signal_result['signal']:4} | "
                      f"Strength: {signal_result['strength']:.2f} | "
                      f"Confidence: {signal_result['confidence']:.2f}")
                
                if signal_result['reasons']:
                    print(f"   Reasons: {', '.join(signal_result['reasons'][:3])}")
                
            except Exception as e:
                print(f"❌ Error processing {filename}: {e}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TESTING SUMMARY")
        print(f"   Files processed: {processed_files}")
        print(f"   BUY signals: {total_signals['BUY']}")
        print(f"   SELL signals: {total_signals['SELL']}")
        print(f"   HOLD signals: {total_signals['HOLD']}")
        print(f"   Strong signals (≥0.5): {strong_signals}")
        if processed_files > 0:
            avg_strength = total_strength / processed_files
            print(f"   Average strength: {avg_strength:.3f}")
        print("\n✅ Signal generation test completed!")

def main():
    """Main testing function."""
    tester = QuantumFluxTester()
    tester.test_data_files()

if __name__ == "__main__":
    main()