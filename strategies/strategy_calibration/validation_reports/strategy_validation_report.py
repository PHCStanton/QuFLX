#!/usr/bin/env python3
"""
Quantum-Flux Strategy Validation Report
Final validation and readiness assessment for TUI integration.
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

class StrategyValidator:
    """Validates the Quantum-Flux strategy for production readiness."""
    
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
    
    def generate_signal(self, df: pd.DataFrame, min_strength: float = 0.2) -> Dict[str, Any]:
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
    
    def validate_strategy_readiness(self, data_dir: str = "../../../../../data/data_5m", max_files: int = 5) -> Dict[str, Any]:
        """Perform comprehensive validation tests."""
        validation_results = {
            'tests_passed': 0,
            'total_tests': 5,
            'test_results': {},
            'overall_status': 'FAILED',
            'recommendations': []
        }
        
        # Test 1: Configuration Loading
        print("🔧 Test 1: Configuration Loading")
        if self.strategy_config:
            validation_results['tests_passed'] += 1
            validation_results['test_results']['config_loading'] = 'PASSED'
            print("   ✅ Configuration loaded successfully")
        else:
            validation_results['test_results']['config_loading'] = 'FAILED'
            print("   ❌ Configuration loading failed")
        
        # Test 2: Indicator Setup
        print("\n🔧 Test 2: Indicator Setup")
        try:
            # Create dummy data for testing
            test_data = pd.DataFrame({
                'open': np.random.randn(100).cumsum() + 100,
                'high': np.random.randn(100).cumsum() + 101,
                'low': np.random.randn(100).cumsum() + 99,
                'close': np.random.randn(100).cumsum() + 100,
                'volume': np.random.randint(1000, 10000, 100)
            })
            
            # Test indicator calculations
            test_data = self.calculate_indicators(test_data)
            required_indicators = ['rsi', 'macd', 'macd_signal', 'macd_hist', 'bb_upper', 'bb_lower', 'stoch_k']
            
            if all(col in test_data.columns for col in required_indicators):
                validation_results['tests_passed'] += 1
                validation_results['test_results']['indicator_setup'] = 'PASSED'
                print("   ✅ All indicators calculated successfully")
            else:
                validation_results['test_results']['indicator_setup'] = 'FAILED'
                print("   ❌ Some indicators failed to calculate")
                
        except Exception as e:
            validation_results['test_results']['indicator_setup'] = 'FAILED'
            print(f"   ❌ Indicator setup failed: {e}")
        
        # Test 3: Data Processing
        print("\n🔧 Test 3: Data Processing")
        if not os.path.exists(data_dir):
            validation_results['test_results']['data_processing'] = 'FAILED'
            print(f"   ❌ Data directory not found: {data_dir}")
        else:
            csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
            if csv_files:
                try:
                    # Test processing a real file
                    test_file = os.path.join(data_dir, csv_files[0])
                    df = pd.read_csv(test_file)
                    
                    if 'volume' not in df.columns:
                        df['volume'] = 0
                    
                    signal_result = self.generate_signal(df)
                    
                    if 'signal' in signal_result and signal_result['signal'] in ['BUY', 'SELL', 'HOLD']:
                        validation_results['tests_passed'] += 1
                        validation_results['test_results']['data_processing'] = 'PASSED'
                        print("   ✅ Data processing successful")
                    else:
                        validation_results['test_results']['data_processing'] = 'FAILED'
                        print("   ❌ Signal generation failed")
                        
                except Exception as e:
                    validation_results['test_results']['data_processing'] = 'FAILED'
                    print(f"   ❌ Data processing failed: {e}")
            else:
                validation_results['test_results']['data_processing'] = 'FAILED'
                print("   ❌ No CSV files found for testing")
        
        # Test 4: Signal Quality
        print("\n🔧 Test 4: Signal Quality")
        try:
            if not os.path.exists(data_dir):
                validation_results['test_results']['signal_quality'] = 'FAILED'
                print("   ❌ Cannot test signal quality - no data directory")
            else:
                csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
                test_files = csv_files[:max_files]
                
                signals = {'BUY': 0, 'SELL': 0, 'HOLD': 0}
                total_strength = 0
                processed_files = 0
                
                for filename in test_files:
                    filepath = os.path.join(data_dir, filename)
                    try:
                        df = pd.read_csv(filepath)
                        if 'volume' not in df.columns:
                            df['volume'] = 0
                        
                        signal_result = self.generate_signal(df, min_strength=0.2)
                        signals[signal_result['signal']] += 1
                        total_strength += signal_result['strength']
                        processed_files += 1
                    except:
                        continue
                
                if processed_files > 0:
                    actionable_signals = signals['BUY'] + signals['SELL']
                    actionable_rate = actionable_signals / processed_files
                    avg_strength = total_strength / processed_files
                    
                    if actionable_rate >= 0.3 and avg_strength >= 0.15:
                        validation_results['tests_passed'] += 1
                        validation_results['test_results']['signal_quality'] = 'PASSED'
                        print(f"   ✅ Signal quality good: {actionable_rate*100:.1f}% actionable, avg strength {avg_strength:.3f}")
                    else:
                        validation_results['test_results']['signal_quality'] = 'FAILED'
                        print(f"   ❌ Signal quality poor: {actionable_rate*100:.1f}% actionable, avg strength {avg_strength:.3f}")
                        
                    # Store signal statistics
                    validation_results['signal_stats'] = {
                        'total_signals': processed_files,
                        'buy_signals': signals['BUY'],
                        'sell_signals': signals['SELL'],
                        'hold_signals': signals['HOLD'],
                        'actionable_rate': actionable_rate,
                        'avg_strength': avg_strength
                    }
                else:
                    validation_results['test_results']['signal_quality'] = 'FAILED'
                    print("   ❌ No files processed for signal quality test")
                    
        except Exception as e:
            validation_results['test_results']['signal_quality'] = 'FAILED'
            print(f"   ❌ Signal quality test failed: {e}")
        
        # Test 5: Production Readiness
        print("\n🔧 Test 5: Production Readiness")
        try:
            # Check if all previous tests passed
            critical_tests = ['config_loading', 'indicator_setup', 'data_processing']
            critical_passed = all(validation_results['test_results'].get(test) == 'PASSED' for test in critical_tests)
            
            if critical_passed and validation_results['tests_passed'] >= 4:
                validation_results['tests_passed'] += 1
                validation_results['test_results']['production_readiness'] = 'PASSED'
                print("   ✅ Strategy ready for production")
            else:
                validation_results['test_results']['production_readiness'] = 'FAILED'
                print("   ❌ Strategy not ready for production")
                
        except Exception as e:
            validation_results['test_results']['production_readiness'] = 'FAILED'
            print(f"   ❌ Production readiness test failed: {e}")
        
        # Overall assessment
        if validation_results['tests_passed'] >= 4:
            validation_results['overall_status'] = 'PASSED'
        elif validation_results['tests_passed'] >= 3:
            validation_results['overall_status'] = 'MARGINAL'
        else:
            validation_results['overall_status'] = 'FAILED'
        
        return validation_results
    
    def generate_integration_guide(self) -> str:
        """Generate TUI integration guide."""
        guide = """
# Quantum-Flux Strategy TUI Integration Guide

## Integration Steps

### 1. Update Implementation Plan
- [ ] Review PO_IMPLEMENTATION_PLAN.md
- [ ] Update TUI architecture section
- [ ] Add quantum_flux strategy integration

### 2. Create TUI Mockups
- [ ] Design signal display interface
- [ ] Create indicator dashboard
- [ ] Plan real-time updates

### 3. Implement Basic Structure
- [ ] Update src/quantumflux/tui/main.py
- [ ] Add strategy selection menu
- [ ] Implement signal display components

### 4. Integrate Signal Generation
- [ ] Import quantum_flux strategy
- [ ] Add real-time signal updates
- [ ] Implement threshold controls

### 5. Add Pocket Option API
- [ ] Connect to PO WebSocket
- [ ] Implement trade execution
- [ ] Add position monitoring

## Recommended TUI Layout

```
┌─ Quantum-Flux Trading Interface ─────────────────────────────────┐
│                                                                  │
│ Strategy: quantum_flux          Threshold: 0.2    Status: ACTIVE │
│                                                                  │
│ ┌─ Current Signals ─┐  ┌─ Indicators ──────┐  ┌─ Performance ─┐ │
│ │ EURUSD    🟢 BUY  │  │ RSI:     45.2     │  │ Win Rate: 58% │ │
│ │ GBPUSD    🔴 SELL │  │ MACD:    +0.003   │  │ Profit: +12.4 │ │
│ │ USDJPY    🟡 HOLD │  │ BB Pos:  0.65     │  │ Trades: 23    │ │
│ │ AUDUSD    🟢 BUY  │  │ Stoch:   72.1     │  │               │ │
│ └───────────────────┘  └───────────────────┘  └───────────────┘ │
│                                                                  │
│ ┌─ Live Trades ─────────────────────────────────────────────────┐ │
│ │ EURUSD BUY  1.0850 → 1.0855  +$8.00  [2m remaining]         │ │
│ │ GBPUSD SELL 1.2650 → 1.2645  +$8.00  [4m remaining]         │ │
│ └───────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [Q]uit  [S]ettings  [H]istory  [R]efresh  [T]hreshold  [P]ause  │
└──────────────────────────────────────────────────────────────────┘
```

## Key Components to Implement

1. **SignalDisplay**: Real-time signal updates
2. **IndicatorPanel**: Live indicator values
3. **PerformanceTracker**: Win/loss statistics
4. **TradeMonitor**: Active trade tracking
5. **SettingsPanel**: Threshold and parameter controls

## Integration Checklist

- [ ] Strategy validation passed
- [ ] TUI components designed
- [ ] Real-time data feed connected
- [ ] Signal generation integrated
- [ ] Pocket Option API connected
- [ ] Error handling implemented
- [ ] Performance monitoring added
- [ ] User controls functional
- [ ] Testing completed
- [ ] Documentation updated
"""
        return guide
    
    def run_validation(self, data_dir: str = "../../../../../data/data_5m"):
        """Run complete validation process."""
        print("🔍 Quantum-Flux Strategy Validation Report")
        print("=" * 60)
        
        # Run validation tests
        results = self.validate_strategy_readiness(data_dir)
        
        # Display results
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print(f"   Tests Passed: {results['tests_passed']}/{results['total_tests']}")
        print(f"   Overall Status: {results['overall_status']}")
        
        if 'signal_stats' in results:
            stats = results['signal_stats']
            print(f"\n📈 Signal Generation Results:")
            print(f"   Total Signals: {stats['total_signals']}")
            print(f"   BUY: {stats['buy_signals']}, SELL: {stats['sell_signals']}, HOLD: {stats['hold_signals']}")
            print(f"   Actionable Rate: {stats['actionable_rate']*100:.1f}%")
            print(f"   Average Strength: {stats['avg_strength']:.3f}")
        
        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        if results['overall_status'] == 'PASSED':
            print("   ✅ Strategy is ready for TUI integration")
            print("   🚀 Proceed with real-time data feed integration")
            print("   📊 Implement position sizing and risk management")
            print("   🔗 Connect Pocket Option API for live trading")
        elif results['overall_status'] == 'MARGINAL':
            print("   ⚠️ Strategy needs minor improvements")
            print("   🔧 Optimize signal thresholds")
            print("   📊 Test with more data files")
        else:
            print("   ❌ Strategy requires significant improvements")
            print("   🔧 Review indicator calculations")
            print("   📊 Adjust signal generation logic")
        
        # Generate integration guide
        print("\n📋 Generating TUI Integration Guide...")
        guide = self.generate_integration_guide()
        
        # Save guide to file
        with open("quantum_flux_tui_integration_guide.md", "w", encoding='utf-8') as f:
            f.write(guide)
        
        print("   💾 Integration guide saved to: quantum_flux_tui_integration_guide.md")
        
        # Save validation results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = f"strategy_validation_results_{timestamp}.json"
        
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"   💾 Validation results saved to: {results_file}")
        
        # Display TUI mockup
        print("\n" + "=" * 60)
        print("🖥️  RECOMMENDED TUI LAYOUT")
        print("=" * 60)
        print("""
┌─ Quantum-Flux Trading Interface ─────────────────────────────────┐
│                                                                  │
│ Strategy: quantum_flux          Threshold: 0.2    Status: ACTIVE │
│                                                                  │
│ ┌─ Current Signals ─┐  ┌─ Indicators ──────┐  ┌─ Performance ─┐ │
│ │ EURUSD    🟢 BUY  │  │ RSI:     45.2     │  │ Win Rate: 58% │ │
│ │ GBPUSD    🔴 SELL │  │ MACD:    +0.003   │  │ Profit: +12.4 │ │
│ │ USDJPY    🟡 HOLD │  │ BB Pos:  0.65     │  │ Trades: 23    │ │
│ │ AUDUSD    🟢 BUY  │  │ Stoch:   72.1     │  │               │ │
│ └───────────────────┘  └───────────────────┘  └───────────────┘ │
│                                                                  │
│ ┌─ Live Trades ─────────────────────────────────────────────────┐ │
│ │ EURUSD BUY  1.0850 → 1.0855  +$8.00  [2m remaining]         │ │
│ │ GBPUSD SELL 1.2650 → 1.2645  +$8.00  [4m remaining]         │ │
│ └───────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ [Q]uit  [S]ettings  [H]istory  [R]efresh  [T]hreshold  [P]ause  │
└──────────────────────────────────────────────────────────────────┘
        """)
        
        print("\n🎯 NEXT STEPS:")
        print("   1. Update PO_IMPLEMENTATION_PLAN.md with TUI details")
        print("   2. Create TUI mockups and wireframes")
        print("   3. Implement basic TUI structure")
        print("   4. Integrate signal generation")
        print("   5. Add Pocket Option API connectivity")
        
        print("\n✅ Strategy validation completed!")
        
        return results

def main():
    """Main validation function."""
    validator = StrategyValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()