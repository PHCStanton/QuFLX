#!/usr/bin/env python3
"""
Quantum-Flux Strategy Performance Summary
Tests the strategy across multiple currency pairs and provides performance overview.
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

class QuantumFluxSummary:
    """Summary analysis of Quantum-Flux strategy across multiple assets."""
    
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
        
        return df
    
    def generate_signal(self, df: pd.DataFrame, min_strength: float = 0.3) -> Dict[str, Any]:
        """Generate trading signal based on latest data."""
        if len(df) < 50:  # Need enough data for indicators
            return {'signal': 'HOLD', 'strength': 0.0, 'confidence': 0.0, 'reasons': []}
        
        # Calculate indicators
        df = self.calculate_indicators(df)
        
        # Get latest values
        latest_idx = len(df) - 1
        current_price = df['close'].iloc[latest_idx]
        current_rsi = df['rsi'].iloc[latest_idx] if not pd.isna(df['rsi'].iloc[latest_idx]) else 50
        current_macd_hist = df['macd_hist'].iloc[latest_idx] if not pd.isna(df['macd_hist'].iloc[latest_idx]) else 0
        current_bb_upper = df['bb_upper'].iloc[latest_idx] if not pd.isna(df['bb_upper'].iloc[latest_idx]) else current_price
        current_bb_lower = df['bb_lower'].iloc[latest_idx] if not pd.isna(df['bb_lower'].iloc[latest_idx]) else current_price
        current_stoch_k = df['stoch_k'].iloc[latest_idx] if not pd.isna(df['stoch_k'].iloc[latest_idx]) else 50
        
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
        if current_macd_hist > 0:
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
        confidence = min(strength * 1.5, 1.0)
        
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
                'macd_hist': current_macd_hist,
                'bb_position': (current_price - current_bb_lower) / (current_bb_upper - current_bb_lower) if current_bb_upper != current_bb_lower else 0.5,
                'stoch_k': current_stoch_k
            }
        }
    
    def analyze_asset(self, filepath: str, min_strength: float = 0.3) -> Dict[str, Any]:
        """Analyze a single asset file."""
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
            
            # Generate signal
            signal_result = self.generate_signal(df, min_strength)
            
            return {
                'asset': os.path.basename(filepath).replace('.csv', ''),
                'signal': signal_result['signal'],
                'strength': signal_result['strength'],
                'confidence': signal_result['confidence'],
                'reasons': signal_result['reasons'],
                'indicators': signal_result['indicators'],
                'data_points': len(df)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def test_threshold_optimization(self, data_dir: str = "../../../../../data/data_5m", max_files: int = 10) -> Dict[str, Any]:
        """Test different threshold values to find optimal settings."""
        if not os.path.exists(data_dir):
            return {'error': f"Data directory not found: {data_dir}"}
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            return {'error': f"No CSV files found in {data_dir}"}
        
        test_files = csv_files[:max_files]
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        
        threshold_results = {}
        
        for threshold in thresholds:
            signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
            total_strength = 0
            processed_files = 0
            
            for filename in test_files:
                filepath = os.path.join(data_dir, filename)
                result = self.analyze_asset(filepath, threshold)
                
                if 'error' not in result:
                    signals[result['signal']] += 1
                    total_strength += result['strength']
                    processed_files += 1
            
            actionable_signals = signals['BUY'] + signals['SELL']
            total_signals = sum(signals.values())
            actionable_rate = actionable_signals / total_signals if total_signals > 0 else 0
            avg_strength = total_strength / processed_files if processed_files > 0 else 0
            
            threshold_results[threshold] = {
                'signals': signals,
                'actionable_rate': actionable_rate,
                'avg_strength': avg_strength,
                'processed_files': processed_files
            }
        
        return threshold_results
    
    def run_summary_analysis(self, data_dir: str = "../../../../../data/data_5m", max_files: int = 10, min_strength: float = 0.3):
        """Run comprehensive summary analysis."""
        print("🚀 Quantum-Flux Strategy Performance Summary")
        print("=" * 60)
        
        if not os.path.exists(data_dir):
            print(f"❌ Data directory not found: {data_dir}")
            return
        
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
        if not csv_files:
            print(f"❌ No CSV files found in {data_dir}")
            return
        
        test_files = csv_files[:max_files]
        print(f"📁 Testing {len(test_files)} out of {len(csv_files)} assets")
        print(f"⚙️  Signal threshold: {min_strength}")
        print()
        
        # Analyze each asset
        results = []
        signals_summary = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
        total_strength = 0
        processed_files = 0
        
        for filename in test_files:
            filepath = os.path.join(data_dir, filename)
            result = self.analyze_asset(filepath, min_strength)
            
            if 'error' in result:
                print(f"❌ {filename}: {result['error']}")
                continue
            
            results.append(result)
            signals_summary[result['signal']] += 1
            total_strength += result['strength']
            processed_files += 1
            
            # Display result
            signal_emoji = {'BUY': '🟢', 'SELL': '🔴', 'HOLD': '🟡'}[result['signal']]
            asset_name = result['asset'].replace('_', ' ')[:25]
            print(f"{signal_emoji} {asset_name:25} | {result['signal']:4} | "
                  f"Strength: {result['strength']:.2f} | "
                  f"Confidence: {result['confidence']:.2f}")
        
        print("\n" + "=" * 60)
        print("📊 CURRENT MARKET SIGNALS")
        print(f"   🟢 BUY: {signals_summary['BUY']}")
        print(f"   🔴 SELL: {signals_summary['SELL']}")
        print(f"   🟡 HOLD: {signals_summary['HOLD']}")
        
        if processed_files > 0:
            avg_strength = total_strength / processed_files
            actionable_signals = signals_summary['BUY'] + signals_summary['SELL']
            actionable_rate = actionable_signals / processed_files
            
            print(f"   📊 Average strength: {avg_strength:.3f}")
            print(f"   🎯 Actionable rate: {actionable_rate*100:.1f}%")
        
        # Test threshold optimization
        print("\n🔧 THRESHOLD OPTIMIZATION")
        print("-" * 40)
        threshold_results = self.test_threshold_optimization(data_dir, max_files)
        
        if 'error' not in threshold_results:
            best_threshold = None
            best_score = 0
            
            for threshold, data in threshold_results.items():
                actionable_rate = data['actionable_rate']
                avg_strength = data['avg_strength']
                score = actionable_rate * avg_strength  # Combined score
                
                print(f"   Threshold {threshold}: {data['actionable_rate']*100:.1f}% actionable, "
                      f"avg strength {data['avg_strength']:.3f}, score {score:.3f}")
                
                if score > best_score:
                    best_score = score
                    best_threshold = threshold
            
            if best_threshold:
                print(f"\n🎯 Recommended threshold: {best_threshold}")
                best_data = threshold_results[best_threshold]
                total_signals = sum(best_data['signals'].values())
                print(f"   📊 Would generate {total_signals} total signals")
                print(f"   🎯 {best_data['actionable_rate']*100:.1f}% actionable signals")
        
        # Strategy readiness assessment
        print("\n🏆 STRATEGY READINESS")
        print("-" * 30)
        
        if processed_files >= 5:
            if actionable_rate >= 0.3 and avg_strength >= 0.25:
                status = "✅ FUNCTIONAL - Ready for live testing"
            elif actionable_rate >= 0.2:
                status = "⚠️ MARGINAL - Needs optimization"
            else:
                status = "❌ POOR - Requires major adjustments"
        else:
            status = "❓ INSUFFICIENT DATA - Need more test files"
        
        print(f"   {status}")
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_data = {
            'timestamp': datetime.now().isoformat(),
            'strategy': 'Quantum-Flux',
            'test_parameters': {
                'files_tested': processed_files,
                'min_strength': min_strength
            },
            'current_signals': signals_summary,
            'performance_metrics': {
                'avg_strength': avg_strength if processed_files > 0 else 0,
                'actionable_rate': actionable_rate if processed_files > 0 else 0
            },
            'threshold_optimization': threshold_results,
            'recommended_threshold': best_threshold,
            'readiness_status': status,
            'detailed_results': results
        }
        
        filename = f"quantum_strategy_summary_{timestamp}.json"
        with open(filename, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        print(f"\n💾 Summary saved to: {filename}")
        print("\n✅ Strategy summary analysis completed!")

def main():
    """Main summary function."""
    summary = QuantumFluxSummary()
    summary.run_summary_analysis()

if __name__ == "__main__":
    main()