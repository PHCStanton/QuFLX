#!/usr/bin/env python3
"""
Quantum-Flux Strategy Signal Testing
Tests pure indicator-based signal generation without AI models.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from quantumflux.utils.config import ConfigManager
from quantumflux.core.indicators import IndicatorEngine

class QuantumFluxSignalTester:
    """Test Quantum-Flux strategy signal generation."""
    
    def __init__(self, config_path: str = "config/strategies/quantum_flux.json"):
        self.config_manager = ConfigManager()
        self.strategy_config = self.load_strategy_config(config_path)
        self.indicators_config = self.strategy_config.get('indicators', {})
        self.thresholds = self.strategy_config.get('strategy', {}).get('thresholds', {})
        self.indicator_engine = IndicatorEngine(self.strategy_config)
        
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
    
    def calculate_simple_bollinger(self, prices: pd.Series, period: int = 20, std_dev: float = 2.0):
        """Calculate Bollinger Bands using simple method."""
        sma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)
        return upper, sma, lower
    
    def calculate_simple_stochastic(self, high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3):
        """Calculate Stochastic oscillator using simple method."""
        lowest_low = low.rolling(window=k_period).min()
        highest_high = high.rolling(window=k_period).max()
        k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        d_percent = k_percent.rolling(window=d_period).mean()
        return k_percent, d_percent
    
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate all technical indicators for the strategy."""
        print("\n📊 Calculating Technical Indicators...")
        
        # RSI
        rsi_config = self.indicators_config.get('rsi', {})
        rsi_period = rsi_config.get('period', 14)
        df['rsi'] = self.calculate_simple_rsi(df['close'], period=rsi_period)
        
        # MACD
        macd_config = self.indicators_config.get('macd', {})
        fast = macd_config.get('fast', 12)
        slow = macd_config.get('slow', 26)
        signal = macd_config.get('signal', 9)
        
        macd_line, macd_signal, macd_hist = self.calculate_simple_macd(
            df['close'], fast=fast, slow=slow, signal=signal
        )
        df['macd'] = macd_line
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # Bollinger Bands
        bb_config = self.indicators_config.get('bollinger', {})
        bb_period = bb_config.get('period', 20)
        bb_std = bb_config.get('std_dev', 2.0)
        
        bb_upper, bb_middle, bb_lower = self.calculate_simple_bollinger(
            df['close'], period=bb_period, std_dev=bb_std
        )
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        # Stochastic
        stoch_config = self.indicators_config.get('stochastic', {})
        k_period = stoch_config.get('k_period', 14)
        d_period = stoch_config.get('d_period', 3)
        
        stoch_k, stoch_d = self.calculate_simple_stochastic(
            df['high'], df['low'], df['close'], k_period=k_period, d_period=d_period
        )
        df['stoch_k'] = stoch_k
        df['stoch_d'] = stoch_d
        
        # ATR (simple version)
        atr_config = self.indicators_config.get('atr', {})
        atr_period = atr_config.get('period', 14)
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = true_range.rolling(window=atr_period).mean()
        
        return df
    
    def generate_signal(self, row: pd.Series) -> Dict[str, Any]:
        """Generate trading signal based on indicator values."""
        signal_data = {
            'timestamp': row.name,
            'price': row['close'],
            'signal': 'HOLD',
            'strength': 0.0,
            'confidence': 0.0,
            'reasons': []
        }
        
        # Get indicator values
        rsi = row.get('rsi', 50)
        macd_hist = row.get('macd_hist', 0)
        bb_position = (row['close'] - row['bb_lower']) / (row['bb_upper'] - row['bb_lower'])
        stoch_k = row.get('stoch_k', 50)
        
        # RSI signals
        rsi_oversold = self.indicators_config.get('rsi', {}).get('oversold', 25)
        rsi_overbought = self.indicators_config.get('rsi', {}).get('overbought', 75)
        
        signal_strength = 0.0
        reasons = []
        
        # RSI Analysis
        if rsi < rsi_oversold:
            signal_strength += 0.3
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > rsi_overbought:
            signal_strength -= 0.3
            reasons.append(f"RSI overbought ({rsi:.1f})")
        
        # MACD Analysis
        if macd_hist > 0:
            signal_strength += 0.2
            reasons.append("MACD bullish")
        elif macd_hist < 0:
            signal_strength -= 0.2
            reasons.append("MACD bearish")
        
        # Bollinger Bands Analysis
        if bb_position < 0.2:  # Near lower band
            signal_strength += 0.2
            reasons.append("Near BB lower band")
        elif bb_position > 0.8:  # Near upper band
            signal_strength -= 0.2
            reasons.append("Near BB upper band")
        
        # Stochastic Analysis
        if stoch_k < 20:
            signal_strength += 0.1
            reasons.append("Stochastic oversold")
        elif stoch_k > 80:
            signal_strength -= 0.1
            reasons.append("Stochastic overbought")
        
        # Determine signal type
        min_strength = self.thresholds.get('min_strength', 0.8)
        min_confidence = self.thresholds.get('min_confidence', 0.75)
        
        if signal_strength > min_strength:
            signal_data['signal'] = 'BUY'
        elif signal_strength < -min_strength:
            signal_data['signal'] = 'SELL'
        
        signal_data['strength'] = abs(signal_strength)
        signal_data['confidence'] = min(1.0, abs(signal_strength) / min_strength)
        signal_data['reasons'] = reasons
        
        return signal_data
    
    def test_data_file(self, file_path: str) -> Dict[str, Any]:
        """Test signal generation on a data file."""
        print(f"\n🔍 Testing: {file_path}")
        
        try:
            # Load data
            df = pd.read_csv(file_path)
            print(f"📈 Loaded {len(df)} rows of data")
            
            # Ensure required columns (volume is optional)
            required_cols = ['open', 'high', 'low', 'close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {'error': f"Missing columns: {missing_cols}"}
            
            # Add volume column if missing (set to 0)
            if 'volume' not in df.columns:
                df['volume'] = 0
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Generate signals for last 100 rows (to avoid NaN from indicators)
            test_rows = df.iloc[-100:].copy()
            signals = []
            
            for idx, row in test_rows.iterrows():
                if pd.notna(row['rsi']) and pd.notna(row['macd_hist']):
                    signal = self.generate_signal(row)
                    signals.append(signal)
            
            # Analyze results
            buy_signals = [s for s in signals if s['signal'] == 'BUY']
            sell_signals = [s for s in signals if s['signal'] == 'SELL']
            
            result = {
                'file': file_path,
                'total_signals': len(signals),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'hold_signals': len(signals) - len(buy_signals) - len(sell_signals),
                'avg_strength': np.mean([s['strength'] for s in signals]) if signals else 0,
                'strong_signals': len([s for s in signals if s['strength'] > 0.8]),
                'sample_signals': signals[-5:] if len(signals) >= 5 else signals
            }
            
            return result
            
        except Exception as e:
            return {'error': str(e)}
    
    def run_tests(self, data_dir: str = "data/data_1m") -> None:
        """Run signal tests on all data files."""
        print("🚀 Quantum-Flux Strategy Signal Testing")
        print("=" * 50)
        
        # Display strategy configuration
        print(f"\n📋 Strategy: {self.strategy_config.get('bot_name', 'Unknown')}")
        print(f"🎯 Min Confidence: {self.thresholds.get('min_confidence', 0.75)}")
        print(f"💪 Min Strength: {self.thresholds.get('min_strength', 0.8)}")
        
        print("\n📊 Configured Indicators:")
        for indicator, config in self.indicators_config.items():
            print(f"  • {indicator.upper()}: {config}")
        
        # Test files
        if not os.path.exists(data_dir):
            print(f"❌ Data directory not found: {data_dir}")
            return
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            print(f"❌ No CSV files found in {data_dir}")
            return
        
        print(f"\n🔍 Testing {len(csv_files)} data files...")
        
        results = []
        for file_name in csv_files[:3]:  # Test first 3 files
            file_path = os.path.join(data_dir, file_name)
            result = self.test_data_file(file_path)
            results.append(result)
            
            if 'error' in result:
                print(f"❌ {file_name}: {result['error']}")
            else:
                print(f"✅ {file_name}:")
                print(f"   📊 Total signals: {result['total_signals']}")
                print(f"   📈 Buy: {result['buy_signals']}, 📉 Sell: {result['sell_signals']}")
                print(f"   💪 Strong signals: {result['strong_signals']}")
                print(f"   🎯 Avg strength: {result['avg_strength']:.3f}")
                
                # Show sample signals
                if result['sample_signals']:
                    print("   🔍 Recent signals:")
                    for signal in result['sample_signals']:
                        print(f"     {signal['signal']} @ {signal['price']:.5f} (strength: {signal['strength']:.2f})")
        
        print("\n" + "=" * 50)
        print("✅ Signal testing completed!")

def main():
    """Main function."""
    tester = QuantumFluxSignalTester()
    tester.run_tests()

if __name__ == "__main__":
    main()