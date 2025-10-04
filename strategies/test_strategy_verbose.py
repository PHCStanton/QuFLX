#!/usr/bin/env python3
"""
Verbose Neural Beast Strategy Test
This will show exactly what's happening in the strategy analysis
"""

import sys
import os
import logging
import time
import numpy as np
from dataclasses import dataclass
from typing import List

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simplified_neural_beast_bot import NeuralBeastQuantumFusion, Candle, SimplifiedBeastTradingBot

def create_extreme_candles_for_signals():
    """Create candles that should definitely generate signals"""
    candles = []
    base_price = 1.0
    
    # Create 45 normal candles
    for i in range(45):
        change = np.random.randn() * 0.001
        base_price += change
        high = base_price + abs(np.random.randn() * 0.0005)
        low = base_price - abs(np.random.randn() * 0.0005)
        close = base_price + np.random.randn() * 0.0002
        
        candle = Candle(
            timestamp=time.time() - (50 - i) * 60,
            open=base_price,
            high=high,
            low=low,
            close=close,
            volume=1.0
        )
        candles.append(candle)
        base_price = close
    
    # Create 5 extreme candles to trigger RSI oversold (should generate CALL signal)
    for i in range(5):
        # Force big drops to create oversold condition
        base_price -= 0.01  # Big drop
        high = base_price + 0.0001
        low = base_price - 0.001
        close = base_price - 0.005  # Even bigger drop
        
        candle = Candle(
            timestamp=time.time() - (5 - i) * 60,
            open=base_price,
            high=high,
            low=low,
            close=close,
            volume=1.0
        )
        candles.append(candle)
        base_price = close
    
    return candles

def test_with_extreme_candles():
    """Test strategy with extreme candles that should generate signals"""
    print("🔥 TESTING WITH EXTREME CANDLES (SHOULD GENERATE SIGNALS)")
    print("=" * 60)
    
    # Setup detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(message)s',
        handlers=[logging.StreamHandler()],
        force=True  # Force reconfigure logging
    )
    
    # Create extreme candles
    candles = create_extreme_candles_for_signals()
    print(f"📊 Created {len(candles)} extreme candles")
    
    # Show price movement
    closes = [c.close for c in candles]
    print(f"   Price movement: {closes[0]:.5f} → {closes[-1]:.5f}")
    print(f"   Total change: {((closes[-1] - closes[0]) / closes[0] * 100):.2f}%")
    
    # Test strategy with detailed logging
    print("\n🧠 Running strategy analysis...")
    decision = NeuralBeastQuantumFusion.neural_beast_quantum_fusion_strategy(candles)
    
    if decision:
        print(f"\n🚀 SUCCESS: Signal generated = {decision.upper()}")
    else:
        print(f"\n❌ FAILED: No signal generated even with extreme conditions")
    
    return decision is not None

def test_strategy_requirements():
    """Test if strategy requirements are too strict"""
    print("\n🔍 TESTING STRATEGY REQUIREMENTS")
    print("=" * 40)
    
    # Create a bot and generate normal candles
    bot = SimplifiedBeastTradingBot(gui=None, auto_setup_integration=False)
    candles = bot.generate_mock_candles()
    
    # Manually calculate indicators to see values
    closes = [c.close for c in candles]
    current = candles[-1]
    
    # Calculate all indicators
    rsi = NeuralBeastQuantumFusion.calculate_rsi(closes, 14)
    upper_bb, middle_bb, lower_bb = NeuralBeastQuantumFusion.calculate_bollinger_bands(closes)
    ema9 = NeuralBeastQuantumFusion.calculate_ema(closes, 9)
    ema21 = NeuralBeastQuantumFusion.calculate_ema(closes, 21)
    
    print(f"📊 INDICATOR VALUES:")
    print(f"   RSI: {rsi:.1f} (need <25 or >75 for signal)")
    print(f"   Price: {current.close:.5f}")
    print(f"   BB Upper: {upper_bb:.5f}")
    print(f"   BB Lower: {lower_bb:.5f}")
    print(f"   EMA9: {ema9:.5f}")
    print(f"   EMA21: {ema21:.5f}")
    
    # Check signal conditions
    signals = []
    
    # RSI signals
    if rsi < 25:
        signals.append(('call', 0.85, 'RSI Oversold'))
        print(f"   ✅ RSI Signal: OVERSOLD")
    elif rsi > 75:
        signals.append(('put', 0.85, 'RSI Overbought'))
        print(f"   ✅ RSI Signal: OVERBOUGHT")
    else:
        print(f"   ❌ RSI: No signal (neutral zone)")
    
    # Bollinger Bands signals
    if current.close < lower_bb:
        signals.append(('call', 0.80, 'BB Lower Band'))
        print(f"   ✅ BB Signal: Below lower band")
    elif current.close > upper_bb:
        signals.append(('put', 0.80, 'BB Upper Band'))
        print(f"   ✅ BB Signal: Above upper band")
    else:
        print(f"   ❌ BB: No signal (within bands)")
    
    # EMA signals
    if current.close > ema9 > ema21:
        signals.append(('call', 0.75, 'EMA Bullish'))
        print(f"   ✅ EMA Signal: Bullish trend")
    elif current.close < ema9 < ema21:
        signals.append(('put', 0.75, 'EMA Bearish'))
        print(f"   ✅ EMA Signal: Bearish trend")
    else:
        print(f"   ❌ EMA: No clear trend")
    
    print(f"\n📋 TOTAL SIGNALS: {len(signals)}")
    print(f"   Requirement: Need 2+ signals with 0.75+ average strength")
    
    if len(signals) >= 2:
        print(f"   ✅ Signal count requirement met")
    else:
        print(f"   ❌ Signal count requirement NOT met (need 2, have {len(signals)})")
    
    return len(signals)

if __name__ == "__main__":
    print("🔍 VERBOSE NEURAL BEAST STRATEGY DIAGNOSTIC")
    print("This will show exactly what's happening in the strategy")
    print("=" * 60)
    
    # Test normal strategy requirements
    signal_count = test_strategy_requirements()
    
    # Test with extreme candles
    extreme_success = test_with_extreme_candles()
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC SUMMARY:")
    print(f"   Normal candles: {signal_count} signals generated")
    print(f"   Extreme candles: {'SUCCESS' if extreme_success else 'FAILED'}")
    
    if signal_count == 0 and not extreme_success:
        print("\n🚨 ISSUE IDENTIFIED:")
        print("   Strategy requirements are too strict!")
        print("   Even extreme conditions don't generate signals.")
        print("   Need to lower requirements or fix strategy logic.")
    elif signal_count > 0:
        print("\n✅ Strategy requirements are working!")
        print("   Normal conditions can generate signals.")
    else:
        print("\n⚠️ Mixed results - needs investigation.")
