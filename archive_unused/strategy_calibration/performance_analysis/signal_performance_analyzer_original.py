#!/usr/bin/env python3
"""
Signal Performance Analyzer
Analyzes win/loss rates and profitability of quantum_flux strategy signals.
"""

import os
import sys
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import json
from datetime import datetime, timedelta
import argparse

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class SignalPerformanceAnalyzer:
    """Analyzes the performance of trading signals by simulating trades."""
    
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
        
        # RSI enhanced signals
        rsi_oversold = rsi_config.get('oversold', 30)
        rsi_overbought = rsi_config.get('overbought', 70)
        bullish_floor = rsi_config.get('trend_zones', {}).get('bullish_floor', 40)
        bearish_ceiling = rsi_config.get('trend_zones', {}).get('bearish_ceiling', 60)
        
        # RSI crossover signals
        df['rsi_buy_signal'] = (df['rsi'].shift(1) < rsi_oversold) & (df['rsi'] >= rsi_oversold)
        df['rsi_sell_signal'] = (df['rsi'].shift(1) > rsi_overbought) & (df['rsi'] <= rsi_overbought)
        
        # RSI trend strength signals
        df['rsi_bullish_trend'] = df['rsi'] > bullish_floor
        df['rsi_bearish_trend'] = df['rsi'] < bearish_ceiling
        
        # MACD
        macd_config = self.indicators_config.get('macd', {})
        fast = macd_config.get('fast', 12)
        slow = macd_config.get('slow', 26)
        signal = macd_config.get('signal', 9)
        min_separation = macd_config.get('min_separation', 0.0001)
        
        macd_line, macd_signal, macd_hist = self.calculate_simple_macd(
            df['close'], fast=fast, slow=slow, signal=signal
        )
        df['macd'] = macd_line
        df['macd_signal'] = macd_signal
        df['macd_hist'] = macd_hist
        
        # MACD enhanced signals
        # Golden cross: MACD line crosses above signal line
        df['macd_golden_cross'] = (df['macd'].shift(1) <= df['macd_signal'].shift(1)) & \
                                  (df['macd'] > df['macd_signal']) & \
                                  (abs(df['macd'] - df['macd_signal']) > min_separation)
        
        # Death cross: MACD line crosses below signal line
        df['macd_death_cross'] = (df['macd'].shift(1) >= df['macd_signal'].shift(1)) & \
                                 (df['macd'] < df['macd_signal']) & \
                                 (abs(df['macd'] - df['macd_signal']) > min_separation)
        
        # Zero line crossovers
        df['macd_zero_cross_up'] = (df['macd'].shift(1) <= 0) & (df['macd'] > 0)
        df['macd_zero_cross_down'] = (df['macd'].shift(1) >= 0) & (df['macd'] < 0)
        
        # Histogram momentum
        df['macd_hist_momentum_up'] = (df['macd_hist'].shift(1) < 0) & (df['macd_hist'] >= 0)
        df['macd_hist_momentum_down'] = (df['macd_hist'].shift(1) > 0) & (df['macd_hist'] <= 0)
        
        # Bollinger Bands
        bb_config = self.indicators_config.get('bollinger', {})
        bb_period = bb_config.get('period', 20)
        bb_std = bb_config.get('std_dev', 2.0)
        reversion_threshold = bb_config.get('reversion_threshold', 0.05)
        breakout_threshold = bb_config.get('breakout_threshold', 0.1)
        
        bb_upper, bb_middle, bb_lower = self.calculate_simple_bollinger(
            df['close'], period=bb_period, std_dev=bb_std
        )
        df['bb_upper'] = bb_upper
        df['bb_middle'] = bb_middle
        df['bb_lower'] = bb_lower
        
        # Bollinger Band enhanced signals
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_middle']
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # Band touch and reversion signals
        df['bb_lower_touch'] = df['close'] <= df['bb_lower']
        df['bb_upper_touch'] = df['close'] >= df['bb_upper']
        
        # Reversion signals (bounce back from bands)
        df['bb_buy_reversion'] = (df['bb_lower_touch'].shift(1)) & \
                                 (df['close'] > df['bb_lower']) & \
                                 ((df['close'] - df['bb_lower']) / df['bb_lower'] > reversion_threshold)
        
        df['bb_sell_reversion'] = (df['bb_upper_touch'].shift(1)) & \
                                  (df['close'] < df['bb_upper']) & \
                                  ((df['bb_upper'] - df['close']) / df['bb_upper'] > reversion_threshold)
        
        # Volatility breakout signals
        df['bb_breakout_up'] = (df['close'] > df['bb_upper']) & \
                               ((df['close'] - df['bb_upper']) / df['bb_upper'] > breakout_threshold)
        
        df['bb_breakout_down'] = (df['close'] < df['bb_lower']) & \
                                 ((df['bb_lower'] - df['close']) / df['bb_lower'] > breakout_threshold)
        
        # Band squeeze detection (low volatility)
        df['bb_squeeze'] = df['bb_width'] < df['bb_width'].rolling(window=20).quantile(0.2)
        
        # Stochastic
        stoch_config = self.indicators_config.get('stochastic', {})
        k_period = stoch_config.get('k_period', 14)
        d_period = stoch_config.get('d_period', 3)
        
        stoch_k, stoch_d = self.calculate_simple_stochastic(
            df['high'], df['low'], df['close'], k_period=k_period, d_period=d_period
        )
        df['stoch_k'] = stoch_k
        df['stoch_d'] = stoch_d

        # Stochastic crossover signals
        stoch_oversold = stoch_config.get('oversold', 20)
        stoch_overbought = stoch_config.get('overbought', 80)
        
        # BUY signal: %K crosses back above oversold level
        df['stoch_buy_signal'] = (df['stoch_k'].shift(1) < stoch_oversold) & (df['stoch_k'] >= stoch_oversold)
        
        # SELL signal: %K crosses back below overbought level
        df['stoch_sell_signal'] = (df['stoch_k'].shift(1) > stoch_overbought) & (df['stoch_k'] <= stoch_overbought)
        
        return df
    
    def generate_signal(self, row: pd.Series, min_strength: float = 0.2) -> Dict[str, Any]:
        """Generate trading signal based on indicator values."""
        signal_data = {
            'signal': 'HOLD',
            'strength': 0.0,
            'confidence': 0.0,
            'reasons': [],
            'entry_price': row['close'],
            'timestamp': row.name if hasattr(row, 'name') else None
        }
        
        # Get indicator values
        rsi = row.get('rsi', 50)
        macd_hist = row.get('macd_hist', 0)
        bb_position = (row['close'] - row['bb_lower']) / (row['bb_upper'] - row['bb_lower']) if (row['bb_upper'] - row['bb_lower']) != 0 else 0.5
        stoch_k = row.get('stoch_k', 50)
        
        # RSI signals
        rsi_oversold = self.indicators_config.get('rsi', {}).get('oversold', 25)
        rsi_overbought = self.indicators_config.get('rsi', {}).get('overbought', 75)
        
        signal_strength = 0.0
        confidence_factors = []
        reasons = []
        
        # Enhanced RSI Analysis
        if row.get('rsi_buy_signal'):
            signal_strength += 0.35
            confidence_factors.append(0.8)
            reasons.append(f"RSI BUY crossover ({rsi:.1f})")
        elif row.get('rsi_sell_signal'):
            signal_strength -= 0.35
            confidence_factors.append(0.8)
            reasons.append(f"RSI SELL crossover ({rsi:.1f})")
        
        # RSI trend strength confirmation
        if row.get('rsi_bullish_trend') and signal_strength > 0:
            signal_strength += 0.1
            confidence_factors.append(0.6)
            reasons.append("RSI bullish trend")
        elif row.get('rsi_bearish_trend') and signal_strength < 0:
            signal_strength -= 0.1
            confidence_factors.append(0.6)
            reasons.append("RSI bearish trend")
        
        # Enhanced MACD Analysis
        if row.get('macd_golden_cross'):
            signal_strength += 0.4
            confidence_factors.append(0.85)
            reasons.append("MACD golden cross")
        elif row.get('macd_death_cross'):
            signal_strength -= 0.4
            confidence_factors.append(0.85)
            reasons.append("MACD death cross")
        
        # MACD zero line confirmation
        if row.get('macd_zero_cross_up'):
            signal_strength += 0.2
            confidence_factors.append(0.7)
            reasons.append("MACD bullish trend")
        elif row.get('macd_zero_cross_down'):
            signal_strength -= 0.2
            confidence_factors.append(0.7)
            reasons.append("MACD bearish trend")
        
        # MACD histogram momentum
        if row.get('macd_hist_momentum_up'):
            signal_strength += 0.15
            confidence_factors.append(0.6)
            reasons.append("MACD momentum up")
        elif row.get('macd_hist_momentum_down'):
            signal_strength -= 0.15
            confidence_factors.append(0.6)
            reasons.append("MACD momentum down")
        
        # Enhanced Bollinger Bands Analysis
        if row.get('bb_buy_reversion'):
            signal_strength += 0.3
            confidence_factors.append(0.8)
            reasons.append("BB reversion BUY")
        elif row.get('bb_sell_reversion'):
            signal_strength -= 0.3
            confidence_factors.append(0.8)
            reasons.append("BB reversion SELL")
        
        # Volatility breakout signals
        if row.get('bb_breakout_up'):
            signal_strength += 0.25
            confidence_factors.append(0.75)
            reasons.append("BB breakout up")
        elif row.get('bb_breakout_down'):
            signal_strength -= 0.25
            confidence_factors.append(0.75)
            reasons.append("BB breakout down")
        
        # Band squeeze breakout preparation
        if row.get('bb_squeeze'):
            # Reduce confidence during squeeze periods
            if confidence_factors:
                confidence_factors = [c * 0.8 for c in confidence_factors]
            reasons.append("BB squeeze (low volatility)")
        
        # Stochastic Crossover Analysis
        if row.get('stoch_buy_signal'):
            signal_strength += 0.25
            confidence_factors.append(0.7)
            reasons.append("Stoch BUY crossover")
        elif row.get('stoch_sell_signal'):
            signal_strength -= 0.25
            confidence_factors.append(0.7)
            reasons.append("Stoch SELL crossover")
        
        # Calculate confidence
        confidence = np.mean(confidence_factors) if confidence_factors else 0.0
        
        # Determine signal type
        if signal_strength > min_strength:
            signal_data['signal'] = 'BUY'
        elif signal_strength < -min_strength:
            signal_data['signal'] = 'SELL'
        
        signal_data['strength'] = abs(signal_strength)
        signal_data['confidence'] = confidence
        signal_data['reasons'] = reasons
        
        return signal_data
    
    def simulate_trade_outcome(self, signal: Dict[str, Any], future_prices: pd.Series, 
                             trade_duration_minutes: int = 5, payout_rate: float = 0.8) -> Dict[str, Any]:
        """Simulate the outcome of a binary options trade based on a signal."""
        if signal['signal'] == 'HOLD':
            return {'outcome': 'NO_TRADE', 'profit': 0, 'entry_price': 0, 'exit_price': 0}
        
        entry_price = signal['entry_price']
        
        # Find exit price after trade duration
        if len(future_prices) < trade_duration_minutes:
            return {'outcome': 'INSUFFICIENT_DATA', 'profit': 0, 'entry_price': entry_price, 'exit_price': entry_price}
        
        exit_price = future_prices.iloc[trade_duration_minutes - 1]
        
        # Determine trade outcome
        if signal['signal'] == 'BUY':
            # For BUY signal, we win if price goes up
            if exit_price > entry_price:
                outcome = 'WIN'
                profit = payout_rate  # 80% profit on winning trade
            else:
                outcome = 'LOSS'
                profit = -1.0  # Lose entire investment
        else:  # SELL signal
            # For SELL signal, we win if price goes down
            if exit_price < entry_price:
                outcome = 'WIN'
                profit = payout_rate  # 80% profit on winning trade
            else:
                outcome = 'LOSS'
                profit = -1.0  # Lose entire investment
        
        return {
            'outcome': outcome,
            'profit': profit,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'price_change': exit_price - entry_price,
            'price_change_pct': ((exit_price - entry_price) / entry_price) * 100 if entry_price != 0 else 0
        }
    
    def analyze_signal_performance(self, file_path: str, min_strength: float = 0.2, 
                                 trade_duration_minutes: int = 5, payout_rate: float = 0.8) -> Dict[str, Any]:
        """Analyze the performance of signals on a single asset."""
        try:
            # Load data
            df = pd.read_csv(file_path)
            
            # Ensure required columns
            required_cols = ['open', 'high', 'low', 'close']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                return {'error': f"Missing columns: {missing_cols}"}
            
            # Add volume column if missing
            if 'volume' not in df.columns:
                df['volume'] = 0
            
            # Calculate indicators
            df = self.calculate_indicators(df)
            
            # Generate signals and simulate trades
            trades = []
            total_signals = 0
            actionable_signals = 0
            
            # Use data from index 50 onwards to ensure indicators are stable
            start_idx = max(50, len(df) - 200)  # Use last 200 points or from index 50
            
            for i in range(start_idx, len(df) - trade_duration_minutes):
                row = df.iloc[i]
                
                # Skip if indicators are not available
                if pd.isna(row['rsi']) or pd.isna(row['macd_hist']):
                    continue
                
                # Generate signal
                signal = self.generate_signal(row, min_strength=min_strength)
                total_signals += 1
                
                if signal['signal'] != 'HOLD':
                    actionable_signals += 1
                    
                    # Get future prices for trade simulation
                    future_prices = df['close'].iloc[i+1:i+1+trade_duration_minutes]
                    
                    # Simulate trade outcome
                    trade_result = self.simulate_trade_outcome(signal, future_prices, 
                                                             trade_duration_minutes, payout_rate)
                    
                    # Combine signal and trade result
                    trade_data = {
                        'timestamp': i,
                        'signal_type': signal['signal'],
                        'signal_strength': signal['strength'],
                        'signal_confidence': signal['confidence'],
                        'reasons': signal['reasons'],
                        **trade_result
                    }
                    
                    trades.append(trade_data)
            
            # Calculate performance metrics
            if not trades:
                return {
                    'asset': os.path.basename(file_path).replace('.csv', ''),
                    'total_signals': total_signals,
                    'actionable_signals': actionable_signals,
                    'trades': 0,
                    'win_rate': 0,
                    'total_profit': 0,
                    'avg_profit_per_trade': 0,
                    'performance': 'NO_TRADES'
                }
            
            # Filter successful trades (exclude insufficient data)
            successful_trades = [t for t in trades if t['outcome'] in ['WIN', 'LOSS']]
            
            if not successful_trades:
                return {
                    'asset': os.path.basename(file_path).replace('.csv', ''),
                    'total_signals': total_signals,
                    'actionable_signals': actionable_signals,
                    'trades': len(trades),
                    'win_rate': 0,
                    'total_profit': 0,
                    'avg_profit_per_trade': 0,
                    'performance': 'INSUFFICIENT_DATA'
                }
            
            wins = len([t for t in successful_trades if t['outcome'] == 'WIN'])
            losses = len([t for t in successful_trades if t['outcome'] == 'LOSS'])
            win_rate = wins / len(successful_trades) if successful_trades else 0
            
            total_profit = sum([t['profit'] for t in successful_trades])
            avg_profit_per_trade = total_profit / len(successful_trades) if successful_trades else 0
            
            # Performance classification
            if win_rate >= 0.6:
                performance = 'EXCELLENT'
            elif win_rate >= 0.55:
                performance = 'GOOD'
            elif win_rate >= 0.5:
                performance = 'AVERAGE'
            else:
                performance = 'POOR'
            
            return {
                'asset': os.path.basename(file_path).replace('.csv', ''),
                'total_signals': total_signals,
                'actionable_signals': actionable_signals,
                'trades': len(successful_trades),
                'wins': wins,
                'losses': losses,
                'win_rate': win_rate,
                'total_profit': total_profit,
                'avg_profit_per_trade': avg_profit_per_trade,
                'performance': performance,
                'sample_trades': successful_trades[:5]  # First 5 trades for analysis
            }
            
        except Exception as e:
            return {'error': str(e), 'asset': os.path.basename(file_path)}
    
    def run_performance_analysis(self, data_dir: str = "data/data_1m", max_files: int = 10):
        """Run comprehensive performance analysis across multiple assets."""
        print("📊 QUANTUM-FLUX SIGNAL PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        if not os.path.exists(data_dir):
            print(f"❌ Data directory not found: {data_dir}")
            return
        
        # Get CSV files
        csv_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')][:max_files]
        
        if not csv_files:
            print(f"❌ No CSV files found in {data_dir}")
            return
        
        print(f"\n🔍 Analyzing signal performance on {len(csv_files)} assets...")
        print(f"📋 Trade Parameters: 1-minute binary options, 80% payout rate")
        
        results = []
        successful_analyses = 0
        total_trades = 0
        total_wins = 0
        total_profit = 0
        
        for file_name in csv_files:
            file_path = os.path.join(data_dir, file_name)
            # Use configured min_strength instead of hardcoded value
            min_strength = self.thresholds.get('min_strength', 0.2) if self.thresholds else 0.2
            result = self.analyze_signal_performance(file_path, min_strength=min_strength)
            results.append(result)
            
            if 'error' not in result and result['trades'] > 0:
                successful_analyses += 1
                asset = result['asset']
                
                # Display individual asset results
                performance_emoji = {
                    'EXCELLENT': '🟢',
                    'GOOD': '🟡', 
                    'AVERAGE': '🟠',
                    'POOR': '🔴'
                }.get(result['performance'], '⚪')
                
                print(f"\n{performance_emoji} {asset}:")
                print(f"   📈 Trades: {result['trades']} | Win Rate: {result['win_rate']:.1%} | Profit: {result['total_profit']:+.2f}")
                print(f"   📊 Signals: {result['actionable_signals']}/{result['total_signals']} actionable")
                
                if result['sample_trades']:
                    print(f"   🎯 Sample: {result['sample_trades'][0]['signal_type']} → {result['sample_trades'][0]['outcome']} ({result['sample_trades'][0]['profit']:+.2f})")
                
                # Accumulate totals
                total_trades += result['trades']
                total_wins += result['wins']
                total_profit += result['total_profit']
                
            elif 'error' in result:
                print(f"❌ {result.get('asset', file_name)}: {result['error']}")
            else:
                print(f"⚪ {result['asset']}: No trades generated")
        
        # Overall performance summary
        print(f"\n" + "=" * 80)
        print(f"📊 OVERALL PERFORMANCE SUMMARY")
        
        if total_trades > 0:
            overall_win_rate = total_wins / total_trades
            avg_profit_per_trade = total_profit / total_trades
            
            print(f"\n🎯 Trading Performance:")
            print(f"   📈 Total Trades: {total_trades}")
            print(f"   🏆 Total Wins: {total_wins}")
            print(f"   📉 Total Losses: {total_trades - total_wins}")
            print(f"   🎯 Overall Win Rate: {overall_win_rate:.1%}")
            print(f"   💰 Total Profit: {total_profit:+.2f} units")
            print(f"   📊 Avg Profit/Trade: {avg_profit_per_trade:+.3f} units")
            
            # Performance assessment
            if overall_win_rate >= 0.6:
                assessment = "🟢 EXCELLENT - Strategy is highly profitable"
            elif overall_win_rate >= 0.55:
                assessment = "🟡 GOOD - Strategy shows positive performance"
            elif overall_win_rate >= 0.5:
                assessment = "🟠 AVERAGE - Strategy breaks even"
            else:
                assessment = "🔴 POOR - Strategy needs improvement"
            
            print(f"\n🏆 Performance Assessment: {assessment}")
            
            # Recommendations
            print(f"\n💡 RECOMMENDATIONS:")
            if overall_win_rate >= 0.55:
                print(f"   ✅ Strategy is ready for live trading")
                # Updated recommendation to reflect configured threshold
                configured_min_strength = self.thresholds.get('min_strength', 0.2) if self.thresholds else 0.2
                print(f"   🎯 Consider using threshold {configured_min_strength} for optimal signal generation")
                print(f"   💰 Expected profit: {avg_profit_per_trade:+.1%} per trade")
            else:
                print(f"   ⚠️ Strategy requires optimization")
                print(f"   🔧 Consider adjusting signal thresholds")
                print(f"   📊 Test different trade durations")
                print(f"   🎯 Focus on higher confidence signals")
        else:
            print(f"❌ No trades were generated across all assets")
            print(f"💡 Consider lowering signal thresholds or checking data quality")
        
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"signal_performance_analysis_{timestamp}.json"
        
        # Use configured min_strength in trade_parameters
        configured_min_strength = self.thresholds.get('min_strength', 0.2) if self.thresholds else 0.2
        analysis_data = {
            'timestamp': datetime.now().isoformat(),
            'strategy': self.strategy_config.get('bot_name', 'Unknown'),
            'trade_parameters': {
                'duration_minutes': 5,
                'payout_rate': 0.8,
                'min_strength': configured_min_strength  # Updated to use configured value
            },
            'summary': {
                'total_assets': len(csv_files),
                'successful_analyses': successful_analyses,
                'total_trades': total_trades,
                'total_wins': total_wins,
                'overall_win_rate': total_wins / total_trades if total_trades > 0 else 0,
                'total_profit': total_profit,
                'avg_profit_per_trade': total_profit / total_trades if total_trades > 0 else 0
            },
            'detailed_results': results
        }
        
        with open(output_file, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"\n💾 Detailed analysis saved to: {output_file}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Signal Performance Analyzer")
    parser.add_argument("--data-dir", type=str, default="data/data_1m", help="Directory containing the data files")
    args = parser.parse_args()
    
    analyzer = SignalPerformanceAnalyzer()
    analyzer.run_performance_analysis(data_dir=args.data_dir, max_files=10)

if __name__ == "__main__":
    main()