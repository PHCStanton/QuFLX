#!/usr/bin/env python3
"""
Detailed Quantum-Flux Strategy Analysis
Analyzes indicator values and signal generation with adjustable thresholds.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import json

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', '..'))

class QuantumFluxAnalyzer:
    """Detailed analysis of Quantum-Flux strategy signals."""
    
    def __init__(self, config_path: str = "../../../../../config/strategies/quantum_flux.json"):
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
    
    def analyze_signal_strength(self, row: pd.Series, custom_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """Analyze signal strength with detailed breakdown."""
        if custom_thresholds is None:
            custom_thresholds = {'min_strength': 0.4, 'min_confidence': 0.5}
        
        signal_data = {
            'timestamp': row.name,
            'price': row['close'],
            'signal': 'HOLD',
            'strength': 0.0,
            'confidence': 0.0,
            'reasons': [],
            'indicator_values': {},
            'signal_components': {}
        }
        
        # Get indicator values
        rsi = row.get('rsi', 50)
        macd_hist = row.get('macd_hist', 0)
        bb_position = (row['close'] - row['bb_lower']) / (row['bb_upper'] - row['bb_lower']) if (row['bb_upper'] - row['bb_lower']) != 0 else 0.5
        stoch_k = row.get('stoch_k', 50)
        
        # Store indicator values
        signal_data['indicator_values'] = {
            'rsi': rsi,
            'macd_hist': macd_hist,
            'bb_position': bb_position,
            'stoch_k': stoch_k,
            'price': row['close'],
            'bb_upper': row['bb_upper'],
            'bb_lower': row['bb_lower']
        }
        
        # RSI signals
        rsi_oversold = self.indicators_config.get('rsi', {}).get('oversold', 25)
        rsi_overbought = self.indicators_config.get('rsi', {}).get('overbought', 75)
        
        signal_strength = 0.0
        reasons = []
        components = {}
        
        # RSI Analysis
        rsi_component = 0.0
        if rsi < rsi_oversold:
            rsi_component = 0.3
            reasons.append(f"RSI oversold ({rsi:.1f})")
        elif rsi > rsi_overbought:
            rsi_component = -0.3
            reasons.append(f"RSI overbought ({rsi:.1f})")
        elif rsi < 40:
            rsi_component = 0.1
            reasons.append(f"RSI low ({rsi:.1f})")
        elif rsi > 60:
            rsi_component = -0.1
            reasons.append(f"RSI high ({rsi:.1f})")
        
        components['rsi'] = rsi_component
        signal_strength += rsi_component
        
        # MACD Analysis
        macd_component = 0.0
        if macd_hist > 0.0001:
            macd_component = 0.2
            reasons.append("MACD bullish")
        elif macd_hist < -0.0001:
            macd_component = -0.2
            reasons.append("MACD bearish")
        
        components['macd'] = macd_component
        signal_strength += macd_component
        
        # Bollinger Bands Analysis
        bb_component = 0.0
        if bb_position < 0.2:  # Near lower band
            bb_component = 0.2
            reasons.append("Near BB lower band")
        elif bb_position > 0.8:  # Near upper band
            bb_component = -0.2
            reasons.append("Near BB upper band")
        
        components['bollinger'] = bb_component
        signal_strength += bb_component
        
        # Stochastic Analysis
        stoch_component = 0.0
        if stoch_k < 20:
            stoch_component = 0.2
            reasons.append(f"Stoch oversold ({stoch_k:.1f})")
        elif stoch_k > 80:
            stoch_component = -0.2
            reasons.append(f"Stoch overbought ({stoch_k:.1f})")
        
        components['stochastic'] = stoch_component
        signal_strength += stoch_component
        
        # Determine signal direction and strength
        signal_data['signal_components'] = components
        signal_data['strength'] = abs(signal_strength)
        signal_data['confidence'] = min(abs(signal_strength) * 1.2, 1.0)
        signal_data['reasons'] = reasons
        
        # Determine signal type
        min_strength = custom_thresholds.get('min_strength', 0.4)
        if abs(signal_strength) >= min_strength:
            if signal_strength > 0:
                signal_data['signal'] = 'BUY'
            elif signal_strength < 0:
                signal_data['signal'] = 'SELL'
        
        return signal_data
    
    def analyze_file(self, filepath: str, custom_thresholds: Dict[str, float] = None) -> Dict[str, Any]:
        """Analyze a single data file with detailed signal breakdown."""
        try:
            # Load data
            df = pd.read_csv(filepath)
            
            # Check required columns
            required_cols = ['open', 'high', 'low', 'close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {'error': f"Missing columns: {missing_cols}"}
            
            # Add volume if missing
            if 'volume' not in df.columns:
                df['volume'] = 0
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Analyze signals for all rows with sufficient data
            signals = []
            for idx in range(50, len(df)):  # Skip first 50 rows for indicator warmup
                row = df.iloc[idx]
                signal_analysis = self.analyze_signal_strength(row, custom_thresholds)
                signals.append(signal_analysis)
            
            # Generate summary
            buy_signals = [s for s in signals if s['signal'] == 'BUY']
            sell_signals = [s for s in signals if s['signal'] == 'SELL']
            hold_signals = [s for s in signals if s['signal'] == 'HOLD']
            
            avg_strength = np.mean([s['strength'] for s in signals]) if signals else 0
            
            # Get latest signal for display
            latest_signal = signals[-1] if signals else None
            
            return {
                'filename': os.path.basename(filepath),
                'total_signals': len(signals),
                'buy_signals': len(buy_signals),
                'sell_signals': len(sell_signals),
                'hold_signals': len(hold_signals),
                'avg_strength': avg_strength,
                'latest_signal': latest_signal,
                'all_signals': signals
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def run_analysis(self, data_file: str = None, data_dir: str = "../../../../../data/data_5m"):
        """Run detailed analysis on specified file or directory."""
        print("🔍 Quantum-Flux Strategy Detailed Analysis")
        print("=" * 60)
        
        # Test different threshold configurations
        threshold_configs = {
            'Conservative': {'min_strength': 0.6, 'min_confidence': 0.7},
            'Moderate': {'min_strength': 0.4, 'min_confidence': 0.5},
            'Aggressive': {'min_strength': 0.2, 'min_confidence': 0.3}
        }
        
        # Determine file to analyze
        if data_file:
            test_file = data_file
        else:
            # Find a suitable test file
            if os.path.exists(data_dir):
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                if csv_files:
                    test_file = os.path.join(data_dir, csv_files[0])
                else:
                    print(f"❌ No CSV files found in {data_dir}")
                    return
            else:
                print(f"❌ Data directory not found: {data_dir}")
                return
        
        print(f"📁 Analyzing: {os.path.basename(test_file)}")
        print()
        
        # Run analysis with different thresholds
        for config_name, thresholds in threshold_configs.items():
            print(f"🎯 {config_name} Thresholds (min_strength: {thresholds['min_strength']})")
            print("-" * 40)
            
            result = self.analyze_file(test_file, thresholds)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            # Display results
            print(f"   📊 Total signals: {result['total_signals']}")
            print(f"   🟢 BUY signals: {result['buy_signals']}")
            print(f"   🔴 SELL signals: {result['sell_signals']}")
            print(f"   🟡 HOLD signals: {result['hold_signals']}")
            print(f"   💪 Average strength: {result['avg_strength']:.3f}")
            
            # Show latest signal details
            if result['latest_signal']:
                latest = result['latest_signal']
                print(f"   🎯 Latest signal: {latest['signal']} (strength: {latest['strength']:.2f})")
                if latest['reasons']:
                    print(f"      Reasons: {', '.join(latest['reasons'][:2])}")
            
            print()
        
        # Show detailed indicator values for latest signal
        moderate_result = self.analyze_file(test_file, threshold_configs['Moderate'])
        if 'error' not in moderate_result and moderate_result['latest_signal']:
            latest = moderate_result['latest_signal']
            indicators = latest['indicator_values']
            
            print("📈 Latest Indicator Values:")
            print("-" * 30)
            print(f"   RSI: {indicators['rsi']:.1f}")
            print(f"   MACD Histogram: {indicators['macd_hist']:.4f}")
            print(f"   BB Position: {indicators['bb_position']:.2f} (0=lower, 1=upper)")
            print(f"   Stochastic K: {indicators['stoch_k']:.1f}")
            print(f"   Price: {indicators['price']:.5f}")
            print()
        
        print("💡 Recommendations:")
        print("   • Conservative: Use for live trading with high confidence")
        print("   • Moderate: Balanced approach for most situations")
        print("   • Aggressive: More signals but higher risk")
        print("\n✅ Detailed analysis completed!")

def main():
    """Main analysis function."""
    analyzer = QuantumFluxAnalyzer()
    
    # You can specify a particular file or let it auto-select
    # analyzer.run_analysis(data_file="../../../../../data/data_5m/EURUSD_2024_2_5_11.csv")
    analyzer.run_analysis()

if __name__ == "__main__":
    main()