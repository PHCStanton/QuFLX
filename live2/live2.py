import logging
import atexit
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading
import time
import datetime
from typing import List, Optional
from dataclasses import dataclass
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import numpy as np
import sys
import os
import json
import hashlib
import math
import random

# Import PocketOption API Client and Data Streaming
from pocket_option_api_client import PocketOptionAPIClient, create_pocket_option_client_from_config, TradeResult
from data_streaming import RealtimeDataStreaming

# --- Configure urllib3 warning suppression ---
import warnings
import urllib3
from urllib3.exceptions import InsecureRequestWarning, NotOpenSSLWarning, DependencyWarning

# Suppress urllib3 warnings
warnings.filterwarnings("ignore", category=UserWarning, module="urllib3")
warnings.filterwarnings("ignore", category=DeprecationWarning, module="urllib3")
warnings.filterwarnings("ignore", category=InsecureRequestWarning)
warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
warnings.filterwarnings("ignore", category=DependencyWarning)
warnings.filterwarnings("ignore", message=".*connection pool.*")
warnings.filterwarnings("ignore", message=".*Connection pool is full.*")

urllib3.disable_warnings()
urllib3_logger = logging.getLogger("urllib3")
urllib3_logger.setLevel(logging.ERROR)

# ---- CONFIGURATION CONSTANTS ----
MAX_TRADES_LIMIT = 20  # Reduced to 20 for client testing
SESSION_FILE = "beast_session.dat"

# ---- SELECTOR CONSTANTS ----
BALANCE_SELECTORS = [
    "js-balance-demo",
    "js-balance",
    "balance-value",
]

CSS_BALANCE_SELECTORS = [
    ".balance__value",
    ".js-balance-demo",
    ".js-balance",
    "[data-qa='balance']",
    ".balance-value"
]

TRADE_BUTTON_SELECTORS = {
    'call': [
        ".btn-call",
        ".call-btn",
        "[data-test='call-button']",
        ".higher-btn",
        ".up-btn"
    ],
    'put': [
        ".btn-put",
        ".put-btn",
        "[data-test='put-button']",
        ".lower-btn",
        ".down-btn"
    ]
}

STAKE_INPUT_SELECTORS = [
    'div.value__val > input[type="text"]',
    'input[data-test="amount-input"]',
    '.amount-input',
    'input.amount',
    '.stake-input'
]

TRADE_HISTORY_SELECTORS = [
    "div.deals-list__item-first",
    ".deals-list .deal-item:first-child",
    ".trade-history .trade-item:first-child",
    ".history-item:first-child",
    "[data-qa='trade-item']:first-child"
]

PROFIT_SELECTORS = [
    ".//div[contains(@class,'profit')]",
    ".//span[contains(@class,'profit')]",
    ".//div[contains(@class,'pnl')]",
    ".//span[contains(@class,'pnl')]",
    ".//div[contains(text(),'$')]",
    ".//span[contains(text(),'$')]"
]

LOGIN_PAGE_INDICATORS = [
    "input[type='email']",
    "input[type='password']",
    ".login-form",
    ".auth-form",
    "[data-test='login-button']",
    ".login-button",
    "button[type='submit']"
]

TRADING_PAGE_INDICATORS = [
    ".btn-call",
    ".btn-put",
    ".call-btn",
    ".put-btn",
    "[data-test='call-button']",
    "[data-test='put-button']",
    ".trading-interface",
    ".chart-container"
]

POPUP_SELECTORS = [
    "//div[contains(@class,'trade-closed')]",
    "//div[contains(@class,'trade-result')]",
    "//div[contains(@class,'deal-result')]",
    "//div[contains(@class,'popup')]//div[contains(text(),'Profit') or contains(text(),'Loss')]",
    "//div[contains(@class,'modal')]//div[contains(text(),'Trade')]"
]

PROFIT_INDICATORS = [
    ".//span[contains(@class,'profit')]",
    ".//div[contains(@class,'profit')]",
    ".//span[contains(text(),'$')]",
    ".//div[contains(text(),'$')]"
]

@dataclass
class Candle:
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

class SecurityManager:
    def __init__(self):
        self.session_file = SESSION_FILE
        self.max_trades = MAX_TRADES_LIMIT
        
    def get_machine_id(self):
        """Generate unique machine identifier"""
        try:
            import platform
            machine_info = f"{platform.node()}-{platform.machine()}-{platform.processor()}"
            return hashlib.md5(machine_info.encode()).hexdigest()[:16]
        except:
            return "default_machine"
    
    def load_session_data(self):
        """Load existing session data"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    machine_id = self.get_machine_id()
                    if data.get('machine_id') == machine_id:
                        return data
                    else:
                        logging.warning("🔒 Session file from different machine detected")
                        return self.create_new_session()
            else:
                return self.create_new_session()
        except Exception as e:
            logging.error(f"🔒 Error loading session: {e}")
            return self.create_new_session()
    
    def create_new_session(self):
        """Create new session data"""
        session_data = {
            'machine_id': self.get_machine_id(),
            'trades_used': 0,
            'session_active': True,
            'created_date': datetime.datetime.now().isoformat(),
            'last_access': datetime.datetime.now().isoformat()
        }
        self.save_session_data(session_data)
        return session_data
    
    def save_session_data(self, data):
        """Save session data to file"""
        try:
            data['last_access'] = datetime.datetime.now().isoformat()
            with open(self.session_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logging.error(f"🔒 Error saving session: {e}")
    
    def reset_with_license_key(self, key: str) -> bool:
        """Reset session with license key"""
        if key == "4444":  # Your secret reset key
            session_data = self.create_new_session()
            self.save_session_data(session_data)
            logging.info("🔒 Session reset with valid license key")
            return True
        return False
    
    def increment_trade_count(self, session_data):
        """Increment trade count and check limits"""
        session_data['trades_used'] += 1
        self.save_session_data(session_data)
        
        remaining = self.max_trades - session_data['trades_used']
        logging.info(f"🔒 Trade #{session_data['trades_used']}/{self.max_trades} executed. Remaining: {remaining}")
        
        if session_data['trades_used'] >= self.max_trades:
            session_data['session_active'] = False
            self.save_session_data(session_data)
            return False
        return True
    
    def is_session_valid(self, session_data):
        """Check if session is still valid"""
        return session_data.get('session_active', False) and session_data['trades_used'] < self.max_trades
    
    def get_remaining_trades(self, session_data):
        """Get remaining trades count"""
        return max(0, self.max_trades - session_data['trades_used'])

class NeuralBeastQuantumFusion:
    """🌟 NEURAL BEAST QUANTUM FUSION - Ultimate Blended Strategy 🌟"""
    
    def __init__(self):
        self.fusion_mode = "ultimate"
        self.fusion_power = 85
        self.neural_signals = 0
        self.beast_signals = 0
        self.quantum_signals = 0
        self.fusion_signals = 0
        self.confidence = 0.0
        
    @staticmethod
    def calculate_rsi(prices: List[float], period: int = 14) -> float:
        """Enhanced RSI calculation with quantum enhancement"""
        if len(prices) < period + 1:
            return 50.0
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[:period]) if len(gains) >= period else 0
        avg_loss = np.mean(losses[:period]) if len(losses) >= period else 0
        
        for i in range(period, len(gains)):
            avg_gain = (avg_gain * (period - 1) + gains[i]) / period
            avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def calculate_bollinger_bands(prices: List[float], period: int = 20, multiplier: float = 2.0):
        """Calculate Bollinger Bands with neural enhancement"""
        if len(prices) < period:
            return prices[-1], prices[-1], prices[-1]
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper_band = sma + (multiplier * std)
        lower_band = sma - (multiplier * std)
        
        return upper_band, sma, lower_band

    @staticmethod
    def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
        """Calculate MACD with beast enhancement"""
        if len(prices) < slow:
            return 0, 0, 0
        
        ema_fast = NeuralBeastQuantumFusion.calculate_ema(prices, fast)
        ema_slow = NeuralBeastQuantumFusion.calculate_ema(prices, slow)
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line * 0.9
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram

    @staticmethod
    def calculate_ema(prices: List[float], period: int) -> float:
        """Enhanced EMA calculation"""
        if len(prices) < period:
            return prices[-1] if prices else 0.0
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema

    @staticmethod
    def calculate_stochastic(candles: List[Candle], k_period: int = 14, d_period: int = 3):
        """Calculate Stochastic Oscillator"""
        if len(candles) < k_period:
            return 50.0, 50.0
        
        recent_candles = candles[-k_period:]
        highest_high = max(c.high for c in recent_candles)
        lowest_low = min(c.low for c in recent_candles)
        current_close = candles[-1].close
        
        if highest_high == lowest_low:
            k_percent = 50.0
        else:
            k_percent = ((current_close - lowest_low) / (highest_high - lowest_low)) * 100
        
        # Simplified D% calculation
        d_percent = k_percent * 0.9
        
        return k_percent, d_percent

    @staticmethod
    def calculate_atr(candles: List[Candle], period: int = 14) -> float:
        """Calculate Average True Range with quantum enhancement"""
        if len(candles) < period:
            return 0.001
        
        true_ranges = []
        for i in range(1, len(candles)):
            tr1 = candles[i].high - candles[i].low
            tr2 = abs(candles[i].high - candles[i-1].close)
            tr3 = abs(candles[i].low - candles[i-1].close)
            true_ranges.append(max(tr1, tr2, tr3))
        
        return np.mean(true_ranges[-period:]) if true_ranges else 0.001

    @staticmethod
    def analyze_volume(candles: List[Candle]) -> dict:
        """Neural volume analysis"""
        if len(candles) < 10:
            return {'current': 1.0, 'average': 1.0, 'spike': False, 'strength': 0.0}
        
        volumes = [c.volume for c in candles[-10:]]
        avg_volume = np.mean(volumes[:-1])
        current_volume = volumes[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            'current': current_volume,
            'average': avg_volume,
            'spike': volume_ratio > 1.8,
            'strength': min(volume_ratio, 3.0)
        }

    @staticmethod
    def calculate_momentum(candles: List[Candle], period: int = 5) -> float:
        """Quantum momentum calculation"""
        if len(candles) < period:
            return 0.0
        
        first_price = candles[-period].close
        last_price = candles[-1].close
        
        return (last_price - first_price) / first_price

    @staticmethod
    def detect_market_regime(candles: List[Candle]) -> str:
        """Beast market regime detection"""
        if len(candles) < 20:
            return 'unknown'
        
        prices = [c.close for c in candles[-20:]]
        first_price = prices[0]
        last_price = prices[-1]
        
        total_move = abs(last_price - first_price)
        price_range = max(prices) - min(prices)
        
        returns = []
        for i in range(1, len(prices)):
            returns.append((prices[i] - prices[i-1]) / prices[i-1])
        
        volatility = np.std(returns) if returns else 0
        
        if total_move / first_price > 0.003 and volatility > 0.002:
            return 'strong_trending'
        elif total_move / first_price > 0.001 and volatility > 0.001:
            return 'trending'
        elif volatility < 0.0005:
            return 'ranging'
        else:
            return 'choppy'

    @staticmethod
    def detect_neural_patterns(candles: List[Candle]) -> List[dict]:
        """Advanced neural pattern recognition"""
        patterns = []
        if len(candles) < 5:
            return patterns
        
        recent = candles[-5:]
        
        # Neural Hammer Detection
        current = recent[-1]
        body_size = abs(current.close - current.open)
        total_range = current.high - current.low
        lower_shadow = min(current.open, current.close) - current.low
        upper_shadow = current.high - max(current.open, current.close)
        
        if total_range > 0 and lower_shadow > body_size * 2.5 and upper_shadow < body_size * 0.5:
            patterns.append({
                'name': 'Neural Hammer',
                'type': 'bullish',
                'strength': 0.85,
                'confidence': 0.78
            })
        
        # Neural Shooting Star Detection
        if total_range > 0 and upper_shadow > body_size * 2.5 and lower_shadow < body_size * 0.5:
            patterns.append({
                'name': 'Neural Shooting Star',
                'type': 'bearish',
                'strength': 0.85,
                'confidence': 0.78
            })
        
        # Neural Engulfing Pattern
        if len(recent) >= 2:
            prev = recent[-2]
            curr = recent[-1]
            
            prev_body = abs(prev.close - prev.open)
            curr_body = abs(curr.close - curr.open)
            
            # Bullish Engulfing
            if (prev.close < prev.open and curr.close > curr.open and 
                curr.open < prev.close and curr.close > prev.open and
                curr_body > prev_body * 1.2):
                patterns.append({
                    'name': 'Neural Bullish Engulfing',
                    'type': 'bullish',
                    'strength': 0.90,
                    'confidence': 0.82
                })
            
            # Bearish Engulfing
            if (prev.close > prev.open and curr.close < curr.open and 
                curr.open > prev.close and curr.close < prev.open and
                curr_body > prev_body * 1.2):
                patterns.append({
                    'name': 'Neural Bearish Engulfing',
                    'type': 'bearish',
                    'strength': 0.90,
                    'confidence': 0.82
                })
        
        return patterns

    @staticmethod
    def calculate_fibonacci_levels(candles: List[Candle]) -> dict:
        """Quantum Fibonacci analysis"""
        if len(candles) < 20:
            return {}
        
        highs = [c.high for c in candles[-20:]]
        lows = [c.low for c in candles[-20:]]
        
        high = max(highs)
        low = min(lows)
        diff = high - low
        
        return {
            'level_236': high - diff * 0.236,
            'level_382': high - diff * 0.382,
            'level_500': high - diff * 0.500,
            'level_618': high - diff * 0.618,
            'level_786': high - diff * 0.786
        }

    @staticmethod
    def calculate_ultimate_confluence(candles: List[Candle]) -> dict:
        """Beast ultimate confluence calculation"""
        bullish = 0
        bearish = 0
        
        if len(candles) < 20:
            return {'bullish': 0, 'bearish': 0, 'strength': 0.0}
        
        closes = [c.close for c in candles]
        current = candles[-1]
        
        # RSI Confluence
        rsi = NeuralBeastQuantumFusion.calculate_rsi(closes, 14)
        if rsi < 30:
            bullish += 2
        elif rsi < 40:
            bullish += 1
        if rsi > 70:
            bearish += 2
        elif rsi > 60:
            bearish += 1
        
        # MACD Confluence
        macd, signal, histogram = NeuralBeastQuantumFusion.calculate_macd(closes)
        if macd > signal:
            bullish += 1
        if macd < signal:
            bearish += 1
        
        # Bollinger Bands Confluence
        upper_bb, middle_bb, lower_bb = NeuralBeastQuantumFusion.calculate_bollinger_bands(closes)
        if current.close < lower_bb:
            bullish += 2
        if current.close > upper_bb:
            bearish += 2
        
        # Stochastic Confluence
        stoch_k, stoch_d = NeuralBeastQuantumFusion.calculate_stochastic(candles)
        if stoch_k < 20:
            bullish += 1
        if stoch_k > 80:
            bearish += 1
        
        # Volume Confluence
        volume_data = NeuralBeastQuantumFusion.analyze_volume(candles)
        if volume_data['spike']:
            momentum = NeuralBeastQuantumFusion.calculate_momentum(candles)
            if momentum > 0:
                bullish += 1
            if momentum < 0:
                bearish += 1
        
        # EMA Confluence
        ema9 = NeuralBeastQuantumFusion.calculate_ema(closes, 9)
        ema21 = NeuralBeastQuantumFusion.calculate_ema(closes, 21)
        if current.close > ema9 > ema21:
            bullish += 1
        if current.close < ema9 < ema21:
            bearish += 1
        
        total_signals = bullish + bearish
        strength = max(bullish, bearish) / max(total_signals, 1)
        
        return {'bullish': bullish, 'bearish': bearish, 'strength': strength}

    @staticmethod
    def neural_beast_quantum_fusion_strategy(candles: List[Candle]) -> Optional[str]:
        """🌟 NEURAL BEAST QUANTUM FUSION - Ultimate Blended Strategy 🌟"""
        if len(candles) < 50:
            return None
        
        closes = [c.close for c in candles]
        current = candles[-1]
        
        # PHASE 1: Neural Quantum Engine Analysis
        neural_signals = []
        
        # Neural Pattern Recognition
        patterns = NeuralBeastQuantumFusion.detect_neural_patterns(candles)
        for pattern in patterns:
            if pattern['confidence'] > 0.75:
                neural_signals.append({
                    'type': 'call' if pattern['type'] == 'bullish' else 'put',
                    'strength': pattern['strength'],
                    'reason': f"Neural Pattern: {pattern['name']}"
                })
        
        # Quantum RSI Analysis
        rsi = NeuralBeastQuantumFusion.calculate_rsi(closes, 14)
        stoch_k, stoch_d = NeuralBeastQuantumFusion.calculate_stochastic(candles)
        volume_data = NeuralBeastQuantumFusion.analyze_volume(candles)
        
        if rsi < 25 and stoch_k < 20 and volume_data['spike']:
            neural_signals.append({
                'type': 'call',
                'strength': 0.92,
                'reason': 'Quantum Extreme Oversold + Neural Volume Spike'
            })
        
        if rsi > 75 and stoch_k > 80 and volume_data['spike']:
            neural_signals.append({
                'type': 'put',
                'strength': 0.92,
                'reason': 'Quantum Extreme Overbought + Neural Volume Spike'
            })
        
        # PHASE 2: Beast Hybrid Core Analysis
        beast_signals = []
        
        # Ultimate Confluence Analysis
        confluence = NeuralBeastQuantumFusion.calculate_ultimate_confluence(candles)
        regime = NeuralBeastQuantumFusion.detect_market_regime(candles)
        
        if confluence['bullish'] >= 6 and confluence['strength'] > 0.7 and regime in ['trending', 'strong_trending']:
            beast_signals.append({
                'type': 'call',
                'strength': 0.95,
                'reason': f'Beast Ultimate Confluence: {confluence["bullish"]} bullish signals'
            })
        
        if confluence['bearish'] >= 6 and confluence['strength'] > 0.7 and regime in ['trending', 'strong_trending']:
            beast_signals.append({
                'type': 'put',
                'strength': 0.95,
                'reason': f'Beast Ultimate Confluence: {confluence["bearish"]} bearish signals'
            })
        
        # PHASE 3: Quantum Momentum Matrix Analysis
        quantum_signals = []
        
        # Multi-timeframe momentum
        momentum_short = NeuralBeastQuantumFusion.calculate_momentum(candles, 3)
        momentum_medium = NeuralBeastQuantumFusion.calculate_momentum(candles, 7)
        momentum_long = NeuralBeastQuantumFusion.calculate_momentum(candles, 15)
        
        # Fibonacci Confluence
        fibonacci = NeuralBeastQuantumFusion.calculate_fibonacci_levels(candles)
        
        # Quantum Momentum Alignment
        if (momentum_short > 0.001 and momentum_medium > 0.0005 and momentum_long > 0.0002):
            quantum_signals.append({
                'type': 'call',
                'strength': 0.88,
                'reason': 'Quantum Multi-Momentum Alignment Bullish'
            })
        
        if (momentum_short < -0.001 and momentum_medium < -0.0005 and momentum_long < -0.0002):
            quantum_signals.append({
                'type': 'put',
                'strength': 0.88,
                'reason': 'Quantum Multi-Momentum Alignment Bearish'
            })
        
        # Fibonacci Quantum Bounce
        for level_name, level_value in fibonacci.items():
            if abs(current.close - level_value) < 0.0001:
                if level_name in ['level_618', 'level_786']:
                    if momentum_short > 0:
                        quantum_signals.append({
                            'type': 'call',
                            'strength': 0.85,
                            'reason': f'Quantum Fibonacci {level_name} Bullish Bounce'
                        })
                    elif momentum_short < 0:
                        quantum_signals.append({
                            'type': 'put',
                            'strength': 0.85,
                            'reason': f'Quantum Fibonacci {level_name} Bearish Bounce'
                        })
        
        # PHASE 4: ULTIMATE FUSION ANALYSIS
        all_signals = neural_signals + beast_signals + quantum_signals
        
        if not all_signals:
            return None
        
        # Count signal types
        call_signals = [s for s in all_signals if s['type'] == 'call']
        put_signals = [s for s in all_signals if s['type'] == 'put']
        
        # Calculate fusion strength
        call_strength = sum(s['strength'] for s in call_signals) / len(call_signals) if call_signals else 0
        put_strength = sum(s['strength'] for s in put_signals) / len(put_signals) if put_signals else 0
        
        # Fusion decision logic
        min_signals_required = 2
        min_strength_required = 0.80
        
        if len(call_signals) >= min_signals_required and call_strength >= min_strength_required:
            if len(put_signals) == 0 or call_strength > put_strength + 0.1:
                reasons = [s['reason'] for s in call_signals[:2]]
                logging.info(f"🌟 NEURAL BEAST QUANTUM FUSION: CALL Signal")
                logging.info(f"   Fusion Strength: {call_strength:.2f}")
                logging.info(f"   Neural Signals: {len(neural_signals)}")
                logging.info(f"   Beast Signals: {len(beast_signals)}")
                logging.info(f"   Quantum Signals: {len(quantum_signals)}")
                logging.info(f"   Reasons: {', '.join(reasons)}")
                return "call"
        
        if len(put_signals) >= min_signals_required and put_strength >= min_strength_required:
            if len(call_signals) == 0 or put_strength > call_strength + 0.1:
                reasons = [s['reason'] for s in put_signals[:2]]
                logging.info(f"🌟 NEURAL BEAST QUANTUM FUSION: PUT Signal")
                logging.info(f"   Fusion Strength: {put_strength:.2f}")
                logging.info(f"   Neural Signals: {len(neural_signals)}")
                logging.info(f"   Beast Signals: {len(beast_signals)}")
                logging.info(f"   Quantum Signals: {len(quantum_signals)}")
                logging.info(f"   Reasons: {', '.join(reasons)}")
                return "put"
        
        return None

# NEURAL BEAST QUANTUM FUSION STRATEGY MAP
FUSION_STRATEGY_MAP = {
    "Neural Beast Quantum Fusion": NeuralBeastQuantumFusion.neural_beast_quantum_fusion_strategy,
}

class AdvancedRiskManager:
    """Enhanced risk management system for Neural Beast Quantum Fusion"""
    
    def __init__(self):
        self.max_consecutive_losses = 3
        self.daily_loss_limit = 100.0
        self.position_sizing_method = "adaptive"
        self.risk_per_trade = 0.02
    
    def calculate_position_size(self, balance: float, confidence: float) -> float:
        """Calculate optimal position size based on confidence and balance"""
        base_size = balance * self.risk_per_trade
        confidence_multiplier = 0.5 + (confidence * 0.5)
        return base_size * confidence_multiplier
    
    def should_trade(self, consecutive_losses: int, daily_pnl: float, 
                    market_volatility: float) -> bool:
        """Determine if conditions are suitable for trading"""
        if consecutive_losses >= self.max_consecutive_losses:
            return False
        if daily_pnl <= -self.daily_loss_limit:
            return False
        if market_volatility > 3.0:
            return np.random.random() < 0.3
        return True

def detect_trade_closed_popup(driver, poll_time=5.0, poll_interval=0.3):
    import time as pytime
    end_time = pytime.time() + poll_time
    while pytime.time() < end_time:
        try:
            for selector in POPUP_SELECTORS:
                try:
                    popup = driver.find_element(By.XPATH, selector)

                    for indicator in PROFIT_INDICATORS:
                        try:
                            profit_elem = popup.find_element(By.XPATH, indicator)
                            profit_text = profit_elem.text.replace('$','').replace(',','').replace('+','').strip()

                            import re
                            numbers = re.findall(r'-?\d+\.?\d*', profit_text)
                            if numbers:
                                profit = float(numbers[0])
                                win = profit > 0
                                logging.info(f"✅ Trade result from popup: Win={win}, Profit=${profit}")
                                return win, profit, abs(profit) + 10.0
                        except:
                            continue

                    if "win" in popup.text.lower() or "profit" in popup.text.lower():
                        logging.info("✅ Trade result from popup text: WIN detected")
                        return True, 15.0, 25.0
                    elif "loss" in popup.text.lower() or "lose" in popup.text.lower():
                        logging.info("❌ Trade result from popup text: LOSS detected")
                        return False, -10.0, 0.0

                except NoSuchElementException:
                    continue

        except Exception as e:
            logging.debug(f"Popup detection attempt: {e}")

        pytime.sleep(poll_interval)

    logging.warning("⚠️ No popup detected, checking trade history...")
    return None, 0, 0

def get_last_trade_result(driver, timeout=15):
    try:
        last_trade = None
        for selector in TRADE_HISTORY_SELECTORS:
            try:
                WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                trades = driver.find_elements(By.CSS_SELECTOR, selector)
                if trades:
                    last_trade = trades[0]
                    break
            except:
                continue

        if not last_trade:
            logging.warning("⚠️ Could not find trade history element")
            return None, 0, 0

        for selector in PROFIT_SELECTORS:
            try:
                profit_elem = last_trade.find_element(By.XPATH, selector)
                profit_text = profit_elem.text.replace('$','').replace(',', '').replace('+','').strip()

                import re
                numbers = re.findall(r'-?\d+\.?\d*', profit_text)
                if numbers:
                    profit = float(numbers[0])
                    win = profit > 0
                    payout = abs(profit) + 10.0 if win else 0.0
                    logging.info(f"✅ Trade result from history: Win={win}, Profit=${profit}")
                    return win, profit, payout
            except:
                continue

        try:
            trade_html = last_trade.get_attribute('outerHTML').lower()
            if any(word in trade_html for word in ['win', 'profit', 'success', 'green']):
                logging.info("✅ Trade result from visual indicators: WIN detected")
                return True, 15.0, 25.0
            elif any(word in trade_html for word in ['loss', 'lose', 'fail', 'red']):
                logging.info("❌ Trade result from visual indicators: LOSS detected")
                return False, -10.0, 0.0
        except:
            pass

        logging.warning("⚠️ Could not determine trade result from history")
        return None, 0, 0

    except Exception as e:
        logging.error(f"❌ Error detecting trade result: {e}")
        return None, 0, 0

class BeastTradingBot:
    """
    Main class for the Neural Beast Quantum Fusion trading bot.

    This class handles the main logic for the trading bot, including:
    - GUI integration
    - WebDriver setup and management
    - API client and data streaming initialization
    - Trade execution and result handling
    - Real-time data processing and strategy application
    - Risk management and session control

    The bot is designed to work with both the PocketOption API and browser automation,
    with a preference for the API when available.
    """
    def __init__(self, gui=None, args=None):
        self.gui = gui
        self.args = args
        self.driver = None
        self.bot_running = False
        self.loss_streak = 0
        self.profit_today = 0.0
        self.balance = 10000.0
        self.logs = []
        self.candles = []
        self.fusion_strategy = NeuralBeastQuantumFusion()
        self.selected_strategy = "Neural Beast Quantum Fusion"
        self.stake = 100.0
        self.win_count = 0
        self.loss_count = 0
        self.total_trades = 0
        self.strategy_map = FUSION_STRATEGY_MAP
        self.take_profit = 500.0
        self.stop_loss = 250.0
        self.trade_hold_time = 8
        self.max_trades = MAX_TRADES_LIMIT
        self.session_start_time = 0
        self.risk_manager = AdvancedRiskManager()

        # CSV data upload attributes
        self.csv_data_loaded = False
        self.csv_data_type = None  # 'tick' or 'candle'
        self.csv_asset_name = None
        self.csv_data_count = 0
        self.csv_time_range = None

        # Initialize security manager
        self.security = SecurityManager()
        self.session_data = self.security.load_session_data()

        # Check if session is valid
        if not self.security.is_session_valid(self.session_data):
            self.show_session_ended()
            return

        # Load existing trade count
        self.total_trades = self.session_data['trades_used']
        logging.info(f"🔒 Session loaded: {self.total_trades}/{MAX_TRADES_LIMIT} trades used")

        # Initialize PocketOption API Client
        self.api_client = None
        self._initialize_api_client()

        # Initialize Real-time Data Streaming
        self.data_streaming = RealtimeDataStreaming()
        
        # Configure data_streaming based on args
        if self.args:
            if self.args.asset_focus:
                self.data_streaming.set_asset_focus(self.args.asset_focus)
            else:
                self.data_streaming.release_asset_focus()

            if self.args.stream_mode == "tick":
                self.data_streaming.TICK_ONLY_MODE = True
            elif self.args.stream_mode == "candle":
                self.data_streaming.CANDLE_ONLY_MODE = True
        else:
            self.data_streaming.release_asset_focus()

        self.data_streaming.set_timeframe(1, lock=False)

        # Register callback for asset changes
        self.data_streaming.add_asset_change_callback(
            self._on_asset_changed
        )

        # Fallback to browser automation if API client fails
        if not self.api_client:
            logging.warning("⚠️ API client initialization failed - falling back to browser automation")
            self.setup_driver()
            if self.driver:
                self.navigate_to_trading_page()

    def _initialize_api_client(self):
        """Initialize PocketOption API client from config"""
        try:
            self.api_client = create_pocket_option_client_from_config()
            if self.api_client:
                # Connect to API
                if self.api_client.connect():
                    logging.info("✅ PocketOption API client initialized and connected")
                    # Set up trade result callback
                    self.api_client.add_trade_result_callback(self._on_trade_result)
                    # Update balance from API
                    self.balance = self.api_client.get_balance()
                    logging.info(f"💰 API Balance: ${self.balance:.2f}")
                else:
                    logging.error("❌ Failed to connect PocketOption API client")
                    self.api_client = None
            else:
                logging.error("❌ Failed to create PocketOption API client from config")
        except Exception as e:
            logging.error(f"❌ Error initializing API client: {e}")
            self.api_client = None

    def _on_trade_result(self, result: TradeResult):
        """Handle trade result from API client"""
        try:
            win = result.win
            profit = result.profit
            payout_percentage = result.payout_percentage

            logging.info(f"📊 API Trade Result: {result.trade_id} - {'WIN' if win else 'LOSS'} - Profit: ${profit:.2f} - Payout: {payout_percentage:.1f}%")

            # Log the trade with payout percentage
            self.log_trade(self.selected_strategy, "call" if win else "put", profit, win, payout_percentage)

        except Exception as e:
            logging.error(f"Error handling trade result: {e}")

    def _on_asset_changed(self, old_asset: str, new_asset: str) -> None:
        """
        Handle asset change notification from data streaming.

        Called when user selects different asset in PocketOption UI.
        """
        logging.info(f"🎯 Asset changed: {old_asset} → {new_asset}")
        # Reset loss streak on asset change (optional)
        # self.loss_streak = 0
        # Update GUI if available
        if self.gui:
            self.gui.update_asset_display(new_asset)

    def detect_and_update_asset(self):
        """
        Detect asset changes from the UI and update the data streaming focus.

        This method leverages the asset detection capabilities of data_streaming.py
        to keep the bot synchronized with the user's UI actions.
        """
        if not self.driver:
            return

        try:
            # Use data_streaming.py's built-in asset detection
            detected_asset = self.data_streaming.detect_asset_from_ui(self.driver)
            if detected_asset:
                current_asset = self.data_streaming.get_current_asset()
                if detected_asset != current_asset:
                    logging.info(f"🎯 Asset changed detected: {current_asset} -> {detected_asset}")
                    # Update data streaming to focus on new asset
                    self.data_streaming.set_asset_focus(detected_asset)
                    # Update bot's current asset tracking
                    self.current_asset = detected_asset
                    logging.info(f"✅ Asset focus updated to: {detected_asset}")
        except Exception as e:
            logging.debug(f"Asset detection error: {e}")

    def _run_data_streaming(self, ctx):
        """Run data streaming in background thread with asset change detection"""
        try:
            logging.info("📊 Starting continuous data streaming...")

            # Use continuous streaming mode
            self.data_streaming.stream_continuous(ctx, {"period": 60})

            logging.info("📊 Data streaming completed")
        except Exception as e:
            logging.error(f"❌ Data streaming error: {e}")

    def show_session_ended(self):
        """Show enhanced session ended popup with reset option"""
        # Create custom dialog
        dialog = tk.Toplevel()
        dialog.title("SESSION ENDED")
        dialog.geometry("400x200")
        dialog.configure(bg='#1a1a1a')
        dialog.resizable(False, False)
        dialog.grab_set()  # Make it modal
        
        # Center the dialog
        dialog.transient(self.gui.root if self.gui else None)
        
        # Main message
        message_label = tk.Label(dialog,
                               text="SESSION ENDED\n\nCONTACT OWNER OR ENTER RESET LICENSE KEY:",
                               bg='#1a1a1a',
                               fg='#FF4444',
                               font=('Courier', 12, 'bold'),
                               justify='center')
        message_label.pack(pady=20)
        
        # Entry for license key
        key_frame = tk.Frame(dialog, bg='#1a1a1a')
        key_frame.pack(pady=10)
        
        tk.Label(key_frame,
                text="License Key:",
                bg='#1a1a1a',
                fg='#FFFFFF',
                font=('Courier', 10)).pack(side='left', padx=5)
        
        key_entry = tk.Entry(key_frame,
                           bg='#333333',
                           fg='#00FFFF',
                           font=('Courier', 10),
                           width=15,
                           show='*')
        key_entry.pack(side='left', padx=5)
        
        # Buttons frame
        button_frame = tk.Frame(dialog, bg='#1a1a1a')
        button_frame.pack(pady=20)
        
        def try_reset():
            key = key_entry.get().strip()
            if key:
                if self.reset_session_with_key(key):
                    messagebox.showinfo("Success", "Session reset successfully!")
                    dialog.destroy()
                    # Update GUI if available
                    if self.gui:
                        self.gui.trades = {'total': 0, 'wins': 0, 'losses': 0}
                        self.gui.balance = 10000
                    return
                else:
                    messagebox.showerror("Error", "Invalid license key!")
            else:
                messagebox.showwarning("Warning", "Please enter a license key!")
        
        def use_gui_reset():
            dialog.destroy()
            if self.gui:
                self.gui.reset_session()
        
        def close_app():
            dialog.destroy()
            if self.gui:
                self.gui.on_closing()
            else:
                sys.exit(0)
        
        tk.Button(button_frame,
                 text="Reset Here",
                 bg='#22C55E',
                 fg='white',
                 font=('Courier', 9, 'bold'),
                 command=try_reset).pack(side='left', padx=5)
        
        tk.Button(button_frame,
                 text="Use GUI Reset",
                 bg='#8855FF',
                 fg='white',
                 font=('Courier', 9, 'bold'),
                 command=use_gui_reset).pack(side='left', padx=5)
        
        tk.Button(button_frame,
                 text="Exit",
                 bg='#DC2626',
                 fg='white',
                 font=('Courier', 9, 'bold'),
                 command=close_app).pack(side='left', padx=5)
        
        # Focus on entry
        key_entry.focus_set()
        
        # Bind Enter key to reset
        key_entry.bind('<Return>', lambda e: try_reset())
        
        logging.error("🔒 SESSION ENDED - Trade limit reached")

    def setup_driver(self) -> bool:
        """Setup driver to attach to existing Chrome session instead of creating new one"""
        try:
            # Import selenium webdriver
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            # Configure options for attaching to existing session
            options = Options()
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

            # Compatibility flags (non-invasive)
            options.add_argument("--ignore-ssl-errors")
            options.add_argument("--ignore-certificate-errors")
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--no-first-run")
            options.add_argument("--no-default-browser-check")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-popup-blocking")

            # Create driver that attaches to existing Chrome session
            self.driver = webdriver.Chrome(options=options)

            # Verify connection
            try:
                current_url = self.driver.current_url
                logging.info(f"✅ Successfully attached to Chrome session at: {current_url}")
            except Exception:
                logging.info("✅ Successfully attached to Chrome session")

            return True

        except Exception as e:
            logging.error(f"❌ Failed to attach to Chrome session: {e}")
            logging.error("💡 Make sure Chrome is running with --remote-debugging-port=9222")
            logging.error("💡 Run 'python start_hybrid_session.py' first")
            return False

    def navigate_to_trading_page(self):
        """Check if we're already on the trading page (since we attach to existing session)"""
        try:
            logging.info("🔍 Checking current page in attached Chrome session...")

            # Check current URL
            current_url = self.driver.current_url
            logging.info(f"Current URL: {current_url}")

            # Check if we're already on a Pocket Option trading page
            if "pocketoption.com" in current_url:
                if self.is_trading_page_loaded():
                    logging.info("✅ Already on Pocket Option trading page")
                    return
                elif self.is_login_page_loaded():
                    logging.info("📋 On Pocket Option login page - please login manually")
                    return
                else:
                    logging.info("📄 On Pocket Option site but not trading page")
                    # Try to navigate to trading page
                    try:
                        self.driver.get("https://pocketoption.com/en/cabinet/demo-quick-high-low")
                        time.sleep(3)
                        if self.is_trading_page_loaded():
                            logging.info("✅ Successfully navigated to trading page")
                            return
                    except Exception as e:
                        logging.warning(f"Could not navigate to trading page: {e}")

            logging.info("ℹ️ Please ensure you're logged into Pocket Option demo trading page")

        except Exception as e:
            logging.error(f"❌ Error checking current page: {e}")

    def is_login_page_loaded(self) -> bool:
        """Check if we're on a login page"""
        try:
            for indicator in LOGIN_PAGE_INDICATORS:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements:
                        logging.info(f"✅ Login page detected with element: {indicator}")
                        return True
                except:
                    continue

            return False

        except Exception as e:
            logging.error(f"Error checking if login page loaded: {e}")
            return False

    def is_trading_page_loaded(self) -> bool:
        """Check if we're on a valid trading page"""
        try:
            for indicator in TRADING_PAGE_INDICATORS:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, indicator)
                    if elements:
                        logging.info(f"✅ Trading page detected with element: {indicator}")
                        return True
                except:
                    continue

            return False

        except Exception as e:
            logging.error(f"Error checking if trading page loaded: {e}")
            return False

    def get_balance(self) -> float:
        # Try API client first
        if self.api_client and self.api_client.is_connected():
            try:
                api_balance = self.api_client.get_balance()
                if api_balance > 0:
                    self.balance = api_balance
                    return self.balance
            except Exception as e:
                logging.debug(f"API balance retrieval failed: {e}")

        # Fallback to browser scraping
        if not self.driver:
            return self.balance

        try:
            ready_state = self.driver.execute_script("return document.readyState")
            if ready_state != "complete":
                return self.balance
        except Exception:
            return self.balance

        for selector in BALANCE_SELECTORS:
            try:
                element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.CLASS_NAME, selector))
                )
                text = element.text.replace('$', '').replace(',', '').strip()
                balance = float(text.replace(' ', '').replace('\u202f', '').replace('\xa0', ''))
                if balance > 0:
                    return balance
            except:
                continue

        for css in CSS_BALANCE_SELECTORS:
            try:
                element = WebDriverWait(self.driver, 1).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, css))
                )
                text = element.text.replace('$', '').replace(',', '').strip()
                balance = float(text.replace(' ', '').replace('\u202f', '').replace('\xa0', ''))
                if balance > 0:
                    return balance
            except Exception:
                continue

        return self.balance

    def get_candle_data(self) -> List[Candle]:
        # Priority 1: CSV data if loaded
        if self.csv_data_loaded and self.csv_data_type == 'candle':
            return self.candles[-50:] if self.candles else self.generate_mock_candles()

        # Priority 2: Real-time WebSocket data from data_streaming
        current_asset = self._get_current_asset()
        latest_candle = self._get_latest_candle_from_streaming(current_asset)
        if latest_candle:
            return self._convert_streaming_data_to_candles(current_asset, latest_candle)

        # Priority 3: Browser JavaScript extraction (fallback)
        if self.driver:
            candles = self._extract_candles_from_browser()
            if candles:
                return candles[-50:]

        # Priority 4: Mock data (last resort)
        logging.warning("⚠️ Using mock candle data - no real-time data available")
        return self.generate_mock_candles()

    def _get_current_asset(self) -> str:
        """Get current asset with fallback"""
        try:
            current_asset = self.data_streaming.get_current_asset()
            return current_asset or "EURUSD_otc"
        except Exception:
            return "EURUSD_otc"

    def _get_latest_candle_from_streaming(self, asset: str):
        """Get latest candle from streaming with retries"""
        try:
            for attempt in range(3):
                latest_candle = self.data_streaming.get_latest_candle(asset)
                if latest_candle:
                    logging.info(f"📊 Using real-time data from data_streaming.py for {asset}")
                    return latest_candle
                if attempt < 2:
                    time.sleep(0.5)
            logging.warning(f"⚠️ No real-time data available from data_streaming.py for {asset}, falling back to browser data")
        except Exception as e:
            logging.debug(f"WebSocket data unavailable: {e}")
        return None

    def _convert_streaming_data_to_candles(self, asset: str, latest_candle) -> List[Candle]:
        """Convert streaming data to Candle objects"""
        # Get more candles if available
        all_candles = self.data_streaming.get_all_candles(asset)
        if all_candles and len(all_candles) > 1:
            return [Candle(timestamp=c[0], open=c[1], close=c[2], high=c[3], low=c[4], volume=1.0)
                   for c in all_candles[-50:]]

        # Return single latest candle
        return [Candle(timestamp=latest_candle[0], open=latest_candle[1], close=latest_candle[2],
                      high=latest_candle[3], low=latest_candle[4], volume=1.0)]

    def _extract_candles_from_browser(self) -> List[Candle]:
        """Extract candle data from browser JavaScript"""
        try:
            script = """
            if (typeof window.chartData !== 'undefined') return window.chartData.slice(-50);
            if (typeof window.candleData !== 'undefined') return window.candleData.slice(-50);
            if (typeof window.tradingData !== 'undefined') return window.tradingData.slice(-50);
            return [];
            """
            data = self.driver.execute_script(script)
            if not data:
                return []

            candles = []
            for item in data:
                if isinstance(item, dict) and all(k in item for k in ['open', 'high', 'low', 'close']):
                    candles.append(Candle(
                        timestamp=item.get('timestamp', time.time()),
                        open=float(item['open']),
                        high=float(item['high']),
                        low=float(item['low']),
                        close=float(item['close']),
                        volume=float(item.get('volume', 1.0))
                    ))
            return candles
        except Exception as e:
            logging.debug(f"Browser data extraction failed: {e}")
            return []

    def generate_mock_candles(self) -> List[Candle]:
        candles = []
        base_price = 1.0 + np.random.uniform(-0.1, 0.1)
        for i in range(50):
            change = np.random.randn() * 0.002
            base_price += change
            high = base_price + abs(np.random.randn() * 0.001)
            low = base_price - abs(np.random.randn() * 0.001)
            close = base_price + np.random.randn() * 0.0005
            candle = Candle(
                timestamp=time.time() - (50 - i) * 60,
                open=base_price,
                high=high,
                low=low,
                close=close,
                volume=np.random.uniform(0.5, 2.0)
            )
            candles.append(candle)
            base_price = close
        return candles

    def set_stake(self, amount: float) -> bool:
        try:
            for selector in STAKE_INPUT_SELECTORS:
                try:
                    input_box = WebDriverWait(self.driver, 2).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    input_box.clear()
                    self.driver.execute_script("arguments[0].value = '';", input_box)
                    time.sleep(0.1)
                    input_box.send_keys(str(amount))
                    self.driver.execute_script("arguments[0].value = arguments[1];", input_box, str(amount))
                    logging.info(f"💰 Stake set to ${amount}")
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue

            logging.warning("⚠️ Could not find stake input field")
            return False
        except Exception as e:
            logging.error(f"❌ Failed to set stake: {e}")
            return False

    def execute_trade(self, decision: str) -> bool:
        # Try API client first (primary method)
        if self.api_client and self.api_client.is_connected():
            try:
                # ✅ Dynamic asset with proper fallback
                asset = self.data_streaming.get_current_asset()
                if not asset:
                    logging.warning("⚠️ Asset detection failed, using fallback")
                    asset = "EURUSD_otc"

                logging.info(f"🎯 Trading asset: {asset}")
                expiry = 60  # 1 minute expiry

                trade_id = self.api_client.execute_trade(
                    asset=asset,
                    direction=decision,
                    amount=self.stake,
                    expiry=expiry
                )

                if trade_id:
                    logging.info(f"🚀 API Trade executed: {decision.upper()} ${self.stake} on {asset}")
                    return True
                else:
                    logging.warning("⚠️ API trade execution failed")
                    return False

            except Exception as e:
                logging.error(f"❌ API trade execution error: {e}")
                return False

        # Fallback to browser automation
        if not self.driver:
            return False

        if not self.set_stake(self.stake):
            logging.warning("⚠️ Could not set stake. Proceeding with trade anyway.")

        for selector in TRADE_BUTTON_SELECTORS[decision]:
            try:
                button = WebDriverWait(self.driver, 2).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                )
                button.click()
                logging.info(f"🚀 Browser Trade executed: {decision.upper()} (Stake: ${self.stake})")
                return True
            except (TimeoutException, NoSuchElementException):
                continue
            except Exception as e:
                logging.error(f"❌ Error clicking {decision} button with selector {selector}: {e}")
                continue

        logging.warning(f"⚠️ Could not find {decision} button")
        return False

    def log_trade(self, strategy: str, decision: str, profit: float, win: bool, payout_percentage: float = 0.0):
        """FIXED: Enhanced trade logging to properly record both wins and losses with payout percentage"""
        # Check trade limit before logging
        if not self.security.increment_trade_count(self.session_data):
            logging.error("🔒 TRADE LIMIT REACHED - Bot terminating")
            self.bot_running = False
            self.show_session_ended()
            return

        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        result = "WIN" if win else "LOSS"
        remaining = self.security.get_remaining_trades(self.session_data)
        entry = f"{timestamp} | {strategy} | {decision.upper()} | {result} | P/L: ${profit:.2f} | Payout: {payout_percentage:.1f}% | Remaining: {remaining}"
        self.logs.append(entry)
        
        # FIXED: Ensure both wins and losses are properly tracked
        self.total_trades = self.session_data['trades_used']
        if win:
            self.win_count += 1
            self.loss_streak = 0
            logging.info(f"✅ WIN TRADE: {entry}")
        else:
            self.loss_count += 1  # FIXED: This was working but adding extra logging
            self.loss_streak += 1
            logging.info(f"❌ LOSS TRADE: {entry}")
        
        self.profit_today += profit
        
        # Enhanced logging for debugging
        winrate = self.get_winrate()
        logging.info(f"📊 UPDATED STATS: Trades={self.total_trades}/{MAX_TRADES_LIMIT}, Wins={self.win_count}, Losses={self.loss_count}, WR={winrate:.1f}%, P/L=${self.profit_today:.2f}")
        
        # Update GUI if available
        if self.gui:
            self.gui.trades = {'total': self.total_trades, 'wins': self.win_count, 'losses': self.loss_count}
            self.gui.balance = self.balance
        
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]

    def get_winrate(self) -> float:
        if self.total_trades == 0:
            return 0.0
        winrate = (self.win_count / self.total_trades) * 100
        return winrate

    def reset_session_with_key(self, key: str) -> bool:
        """Reset session with license key"""
        if self.security.reset_with_license_key(key):
            self._reset_session_stats()
            logging.info("🔒 Session reset via bot")
            return True
        return False

    def _reset_session_stats(self):
        """Reset all session statistics"""
        self.session_data = self.security.load_session_data()
        self.total_trades = self.session_data['trades_used']
        self.win_count = 0
        self.loss_count = 0
        self.profit_today = 0.0
        self.loss_streak = 0

    def load_csv_tick_data(self, file_path: str) -> bool:
        """Load tick data from CSV file and convert to candles"""
        try:
            logging.info(f"📊 Loading tick data from: {file_path}")

            # Read CSV file
            import pandas as pd
            df = pd.read_csv(file_path)

            # Validate CSV format
            if 'timestamp' not in df.columns or 'asset' not in df.columns or 'price' not in df.columns:
                raise ValueError("CSV must contain 'timestamp', 'asset', and 'price' columns")

            # Skip header row if it contains column names as data
            if df['timestamp'].iloc[0] == 'timestamp':
                df = df.iloc[1:].reset_index(drop=True)

            # Extract asset name from first row
            asset_name = df['asset'].iloc[0]
            logging.info(f"🎯 Detected asset: {asset_name}")

            # Convert timestamps - handle the time-only format (HH:MM:SSZ)
            def parse_timestamp(ts):
                if isinstance(ts, str) and ts.endswith('Z'):
                    # Convert time-only format to full datetime
                    # Assume today's date for the timestamp
                    today = datetime.datetime.now().date()
                    time_str = ts[:-1]  # Remove 'Z'
                    try:
                        time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
                        return datetime.datetime.combine(today, time_obj)
                    except ValueError:
                        # Try with different format
                        time_obj = datetime.datetime.strptime(time_str, '%H:%M:%S').time()
                        return datetime.datetime.combine(today, time_obj)
                else:
                    return pd.to_datetime(ts, utc=True)

            df['timestamp'] = df['timestamp'].apply(parse_timestamp)
            df = df.sort_values('timestamp')

            # Convert to Candle objects (aggregate ticks into 1-minute candles)
            candles = []
            current_minute = None
            minute_data = []

            for _, row in df.iterrows():
                timestamp = row['timestamp']
                price = float(row['price'])

                # Get minute boundary
                minute_boundary = timestamp.replace(second=0, microsecond=0)

                if current_minute != minute_boundary:
                    # Process previous minute's data
                    if minute_data:
                        self._process_minute_ticks(minute_data, candles, current_minute)

                    # Start new minute
                    current_minute = minute_boundary
                    minute_data = []

                minute_data.append(price)

            # Process final minute
            if minute_data:
                self._process_minute_ticks(minute_data, candles, current_minute)

            # Store data
            self.candles = candles
            self.csv_data_loaded = True
            self.csv_data_type = 'tick'
            self.csv_asset_name = asset_name
            self.csv_data_count = len(candles)

            # Calculate time range
            if candles:
                start_time = datetime.datetime.fromtimestamp(candles[0].timestamp)
                end_time = datetime.datetime.fromtimestamp(candles[-1].timestamp)
                self.csv_time_range = f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"

            logging.info(f"✅ Loaded {len(candles)} candles from tick data for {asset_name}")
            return True

        except Exception as e:
            logging.error(f"❌ Error loading tick CSV: {e}")
            return False

    def load_csv_candle_data(self, file_path: str) -> bool:
        """Load candle data directly from CSV file"""
        try:
            logging.info(f"📊 Loading candle data from: {file_path}")

            # Read CSV file
            import pandas as pd
            df = pd.read_csv(file_path)

            # Validate CSV format
            required_cols = ['timestamp', 'open', 'close', 'high', 'low']
            if not all(col in df.columns for col in required_cols):
                raise ValueError(f"CSV must contain columns: {required_cols}")

            # Extract asset name from filename
            from pathlib import Path
            filename = Path(file_path).name
            asset_match = filename.split('_otc_')[0] if '_otc_' in filename else filename.split('_')[0]
            asset_name = asset_match.upper()

            logging.info(f"🎯 Detected asset: {asset_name}")

            # Convert timestamps and sort
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            df = df.sort_values('timestamp')

            # Convert to Candle objects
            candles = []
            for _, row in df.iterrows():
                candle = Candle(
                    timestamp=row['timestamp'].timestamp(),
                    open=float(row['open']),
                    high=float(row['high']),
                    low=float(row['low']),
                    close=float(row['close']),
                    volume=1.0  # Default volume
                )
                candles.append(candle)

            # Store data
            self.candles = candles
            self.csv_data_loaded = True
            self.csv_data_type = 'candle'
            self.csv_asset_name = asset_name
            self.csv_data_count = len(candles)

            # Calculate time range
            if candles:
                start_time = datetime.datetime.fromtimestamp(candles[0].timestamp)
                end_time = datetime.datetime.fromtimestamp(candles[-1].timestamp)
                self.csv_time_range = f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}"

            logging.info(f"✅ Loaded {len(candles)} candles from candle data for {asset_name}")
            return True

        except Exception as e:
            logging.error(f"❌ Error loading candle CSV: {e}")
            return False

    def _process_minute_ticks(self, minute_data: List[float], candles: List[Candle], minute_timestamp: datetime.datetime) -> None:
        """Process tick data for a single minute into a candle"""
        if not minute_data:
            return

        open_price = minute_data[0]
        close_price = minute_data[-1]
        high_price = max(minute_data)
        low_price = min(minute_data)

        candle = Candle(
            timestamp=minute_timestamp.timestamp(),
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=len(minute_data)  # Use tick count as volume
        )
        candles.append(candle)

    def load_csv_data(self, file_path: str) -> bool:
        """Main method to load CSV data - auto-detects format and calls appropriate loader"""
        try:
            from pathlib import Path
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Read first few lines to detect format
            with open(file_path, 'r', encoding='utf-8') as f:
                first_line = f.readline().strip()
                second_line = f.readline().strip() if f.readline() else ""

            # Detect format based on headers
            if 'timestamp,asset,price' in first_line.lower():
                logging.info("🎯 Detected tick data format")
                return self.load_csv_tick_data(file_path)
            elif 'timestamp,open,close,high,low' in first_line.lower():
                logging.info("🎯 Detected candle data format")
                return self.load_csv_candle_data(file_path)
            else:
                # Try to infer from filename
                filename = Path(file_path).name.lower()
                if 'tick' in filename:
                    logging.info("🎯 Inferred tick data format from filename")
                    return self.load_csv_tick_data(file_path)
                elif 'candle' in filename:
                    logging.info("🎯 Inferred candle data format from filename")
                    return self.load_csv_candle_data(file_path)
                else:
                    raise ValueError("Could not determine CSV format from headers or filename")

        except Exception as e:
            logging.error(f"❌ Error loading CSV data: {e}")
            return False

    def clear_csv_data(self) -> None:
        """Clear loaded CSV data and reset to browser data"""
        self.csv_data_loaded = False
        self.csv_data_type = None
        self.csv_asset_name = None
        self.csv_data_count = 0
        self.csv_time_range = None
        self.candles = []
        logging.info("🗑️ CSV data cleared - using browser data")

    def run_trading_session(self):
        # Check session validity before starting
        if not self.security.is_session_valid(self.session_data):
            self.show_session_ended()
            return

        self._initialize_session()
        self._setup_trading_environment()

        session_time_limit = 2 * 60 * 60
        last_trade_time = 0
        streaming_thread = self._start_data_streaming()

        while self.bot_running:
            try:
                if self._should_stop_trading(session_time_limit):
                    break

                if not self.risk_manager.should_trade(self.loss_streak, self.profit_today, 1.0):
                    logging.info("🛡️ Risk management: Skipping trade due to risk conditions")
                    time.sleep(5)
                    continue

                self._update_balance()
                self.detect_and_update_asset()

                decision = self._get_trading_decision()
                if decision and self._can_execute_trade(last_trade_time):
                    self._execute_and_log_trade(decision)
                    last_trade_time = time.time()

            except Exception as e:
                logging.error(f"❌ Error in trading loop: {e}")
                time.sleep(5)

        self.bot_running = False
        logging.info("🏁 Exiting Neural Beast Quantum Fusion session...")

    def _initialize_session(self):
        """Initialize session parameters"""
        if self.args and self.args.stream:
            self.bot_running = True
            self.loss_streak = 0
            self.session_start_time = time.time()
            logging.info(f"🔒 NEURAL BEAST QUANTUM FUSION session started in stream mode - {self.security.get_remaining_trades(self.session_data)} trades remaining")
        else:
            messagebox.showinfo("Login Required", "Please login to Pocket Option in the opened browser, then press OK to start trading.")

        self.bot_running = True
        self.loss_streak = 0
        self.session_start_time = time.time()
        logging.info(f"🔒 NEURAL BEAST QUANTUM FUSION session started - {self.security.get_remaining_trades(self.session_data)} trades remaining")

    def _setup_trading_environment(self):
        """Setup trading environment after login"""
        try:
            logging.info("⚡ Quick setup after login...")

            # Wait for trading page
            for attempt in range(10):
                if self.is_trading_page_loaded():
                    logging.info("✅ Trading page ready")
                    break
                time.sleep(2)

            # Balance check
            logging.info("💰 Quick balance check...")
            for attempt in range(3):
                try:
                    balance = self.get_balance()
                    if balance > 0:
                        self.balance = balance
                        logging.info(f"✅ Balance: ${self.balance}")
                        break
                    time.sleep(1)
                except Exception as e:
                    logging.warning(f"Balance attempt {attempt + 1} failed: {e}")
                    time.sleep(1)
            else:
                logging.warning("⚠️ Using default balance")
                self.balance = 10000.0

        except Exception as e:
            logging.error(f"❌ Error during setup: {e}")
            self.balance = 10000.0

    def _start_data_streaming(self):
        """Start data streaming thread if driver available"""
        if not self.driver:
            return None

        try:
            class SimpleCtx:
                def __init__(self, driver):
                    self.driver = driver
                    self.verbose = False
                    self.debug = False

            ctx = SimpleCtx(self.driver)
            streaming_thread = threading.Thread(
                target=self._run_data_streaming,
                args=(ctx,),
                daemon=True
            )
            streaming_thread.start()
            logging.info("📊 Real-time data streaming started")
            return streaming_thread
        except Exception as e:
            logging.warning(f"⚠️ Could not start data streaming: {e}")
            return None

    def _should_stop_trading(self, session_time_limit: float) -> bool:
        """Check if trading should stop"""
        if not self.security.is_session_valid(self.session_data):
            logging.error("🔒 Session invalid - terminating")
            self.show_session_ended()
            return True

        elapsed_time = time.time() - self.session_start_time
        if elapsed_time >= session_time_limit:
            self.bot_running = False
            messagebox.showinfo("Session Complete", "2-hour trading session complete. Bot is stopping.")
            logging.info("⏰ 2-hour time limit reached - trading session stopped.")
            return True

        if self.total_trades >= self.max_trades:
            self.bot_running = False
            self.show_session_ended()
            return True

        if self.profit_today >= self.take_profit:
            self.bot_running = False
            messagebox.showinfo("Take Profit Hit", f"Take profit of ${self.take_profit} reached. Bot is stopping.")
            logging.info(f"🎯 Take profit of ${self.take_profit} reached - trading session stopped.")
            return True

        if self.profit_today <= -self.stop_loss:
            self.bot_running = False
            messagebox.showinfo("Stop Loss Hit", f"Stop loss of ${self.stop_loss} reached. Bot is stopping.")
            logging.info(f"🛡️ Stop loss of ${self.stop_loss} reached - trading session stopped.")
            return True

        return False

    def _update_balance(self):
        """Update balance from API or browser"""
        try:
            if self.api_client and self.api_client.is_connected():
                new_balance = self.api_client.get_balance()
                if new_balance > 0:
                    self.balance = new_balance
            elif self.driver:
                new_balance = self.get_balance()
                if new_balance > 0:
                    self.balance = new_balance
        except Exception:
            pass

    def _get_trading_decision(self) -> Optional[str]:
        """Get trading decision from strategy"""
        self.candles = self.get_candle_data()
        strategy_func = self.strategy_map.get(self.selected_strategy)
        return strategy_func(self.candles) if strategy_func else None

    def _can_execute_trade(self, last_trade_time: float) -> bool:
        """Check if enough time has passed since last trade"""
        return (time.time() - last_trade_time) >= 8

    def _execute_and_log_trade(self, decision: str):
        """Execute trade and handle result logging"""
        if self.execute_trade(decision):
            time.sleep(self.trade_hold_time)

            # Handle trade result detection
            if not self.api_client or not self.api_client.is_connected():
                win, profit, payout = detect_trade_closed_popup(self.driver, poll_time=5.0)

                if win is None:
                    logging.info("🔍 Checking trade history...")
                    time.sleep(2)
                    win, profit, payout = get_last_trade_result(self.driver, timeout=10)

                if win is None:
                    logging.warning("⚠️ Could not detect trade result - skipping trade logging")
                    return

                logging.info(f"📊 Browser trade result: Win={win}, P/L=${profit:.2f}")
                self.log_trade(self.selected_strategy, decision, profit, win)
        else:
            time.sleep(3)

class NeuralBeastGUI:
    def __init__(self, root, args=None):
        self.root = root
        self.args = args
        self.root.title("🌟 NEURAL BEAST QUANTUM FUSION 🌟")
        self.root.geometry("800x700")
        self.root.configure(bg='#000000')
        self.root.resizable(True, True)
        self.root.minsize(740, 620)  # Minimum size to prevent too small window
        
        # State variables
        self.is_active = False
        self.fusion_power = 97  # FIXED: Set to 97% as requested
        self.neural_energy = 0
        self.beast_mode = 0
        self.quantum_strength = 0
        self.balance = 10000
        self.trades = {'total': 0, 'wins': 0, 'losses': 0}
        self.settings = {'stake': 100, 'take_profit': 500, 'stop_loss': 250}
        self.feed_messages = []
        self.glow_intensity = 0
        
        # Animation variables
        self.animation_running = False
        self.particle_positions = []
        
        # Initialize bot
        self.bot = BeastTradingBot(gui=self, args=self.args)
        
        self.setup_styles()
        self.create_widgets()
        self.start_animations()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure custom styles
        style.configure('Title.TLabel', 
                       background='#111111', 
                       foreground='#FF8800', 
                       font=('Courier', 12, 'bold'))
        
        style.configure('Status.TLabel', 
                       background='#1a1a1a', 
                       foreground='#00FFFF', 
                       font=('Courier', 8))
        
        style.configure('Energy.TLabel', 
                       background='#1a1a1a', 
                       foreground='#FFFFFF', 
                       font=('Courier', 8, 'bold'))
        
        style.configure('Active.TButton',
                       background='#22C55E',
                       foreground='white',
                       font=('Courier', 10, 'bold'))
        
        style.configure('Inactive.TButton',
                       background='#F97316',
                       foreground='white',
                       font=('Courier', 10, 'bold'))
    
    def create_widgets(self):
        # Main container with padding
        main_frame = tk.Frame(self.root, bg='#000000')
        main_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Header section
        self.create_header(main_frame)
        
        # Fusion power matrix
        self.create_fusion_matrix(main_frame)
        
        # Main content area (2 columns now)
        content_frame = tk.Frame(main_frame, bg='#000000')
        content_frame.pack(fill='both', expand=True, pady=5)

        # Configure grid weights for responsive layout
        content_frame.grid_columnconfigure(0, weight=1)  # Control panel
        content_frame.grid_columnconfigure(1, weight=1)  # Stats panel
        
        # Left column - Control Panel
        self.create_control_panel(content_frame)
        
        # Right column - Statistics with Live Feed
        self.create_statistics_panel(content_frame)
    
    def create_header(self, parent):
        header_frame = tk.Frame(parent, bg='#1a1a1a', relief='ridge', bd=2)
        header_frame.pack(fill='x', pady=(0, 5))
        
        # Animated background effect
        self.header_canvas = tk.Canvas(header_frame, height=60, bg='#1a1a1a', highlightthickness=0)
        self.header_canvas.pack(fill='x', padx=5, pady=5)
        
        # Title
        title_label = tk.Label(header_frame, 
                              text="🌟 NEURAL BEAST QUANTUM FUSION 🌟",
                              bg='#1a1a1a', 
                              fg='#FF8800',
                              font=('Courier', 14, 'bold'))
        title_label.place(relx=0.5, rely=0.3, anchor='center')
        
        subtitle_label = tk.Label(header_frame,
                                 text="🔥 ULTIMATE AI STRATEGY 🔥",
                                 bg='#1a1a1a',
                                 fg='#00FFFF',
                                 font=('Courier', 10))
        subtitle_label.place(relx=0.5, rely=0.7, anchor='center')
        
        # Status bar
        self.status_frame = tk.Frame(header_frame, bg='#1a1a1a')
        self.status_frame.pack(side='bottom', fill='x', padx=5, pady=2)
        
        self.status_left = tk.Label(self.status_frame,
                                   text="⚪ STANDBY",
                                   bg='#1a1a1a',
                                   fg='#888888',
                                   font=('Courier', 8, 'bold'))
        self.status_left.pack(side='left')
        
        self.status_right = tk.Label(self.status_frame,
                                    text=f"Balance: ${self.balance:,} | Trades: {self.trades['total']}/20 | Win Rate: 0%",
                                    bg='#1a1a1a',
                                    fg='#CCCCCC',
                                    font=('Courier', 8))
        self.status_right.pack(side='right')
    
    def create_fusion_matrix(self, parent):
        matrix_frame = tk.Frame(parent, bg='#1a1a1a', relief='ridge', bd=2)
        matrix_frame.pack(fill='x', pady=(0, 5))
        
        title = tk.Label(matrix_frame,
                        text="⚡ FUSION POWER MATRIX ⚡",
                        bg='#1a1a1a',
                        fg='#FF8800',
                        font=('Courier', 10, 'bold'))
        title.pack(pady=5)
        
        # Energy bars container
        bars_frame = tk.Frame(matrix_frame, bg='#1a1a1a')
        bars_frame.pack(fill='x', padx=10, pady=5)
        
        # Individual energy bars
        self.energy_bars = {}
        self.energy_labels = {}
        
        energy_types = [
            ('NEURAL', '#00FFFF', '🧠'),
            ('BEAST', '#FF4444', '💪'),
            ('QUANTUM', '#8855FF', '⚛️')
        ]
        
        for i, (name, color, icon) in enumerate(energy_types):
            bar_frame = tk.Frame(bars_frame, bg='#1a1a1a')
            bar_frame.grid(row=0, column=i, padx=5, sticky='ew')
            bars_frame.grid_columnconfigure(i, weight=1)
            
            # Label
            label = tk.Label(bar_frame,
                           text=f"{icon} {name}: 0%",
                           bg='#1a1a1a',
                           fg=color,
                           font=('Courier', 8, 'bold'))
            label.pack()
            
            # Progress bar
            canvas = tk.Canvas(bar_frame, height=15, bg='#333333', highlightthickness=1,
                             highlightbackground='#666666')
            canvas.pack(fill='x', pady=2)
            
            self.energy_bars[name] = canvas
            self.energy_labels[name] = label
        
        # Master fusion bar
        master_frame = tk.Frame(matrix_frame, bg='#1a1a1a')
        master_frame.pack(fill='x', padx=10, pady=10)
        
        master_label = tk.Label(master_frame,
                               text="MASTER FUSION LEVEL",
                               bg='#1a1a1a',
                               fg='#FF8800',
                               font=('Courier', 10, 'bold'))
        master_label.pack()
        
        self.master_fusion_canvas = tk.Canvas(master_frame, height=25, bg='#333333',
                                            highlightthickness=2, highlightbackground='#FF8800')
        self.master_fusion_canvas.pack(fill='x', pady=5)
    
    def create_control_panel(self, parent):
        control_frame = tk.Frame(parent, bg='#1a1a1a', relief='ridge', bd=2)
        control_frame.pack(side='left', fill='both', expand=True, padx=(0, 2))

        title = tk.Label(control_frame,
                        text="⚙️ FUSION CONTROL",
                        bg='#1a1a1a',
                        fg='#FF8800',
                        font=('Courier', 9, 'bold'))
        title.pack(pady=5)

        # CSV Data Upload Section
        csv_frame = tk.Frame(control_frame, bg='#1a1a1a')
        csv_frame.pack(fill='x', padx=5, pady=5)

        csv_title = tk.Label(csv_frame,
                            text="📊 CSV DATA UPLOAD",
                            bg='#1a1a1a',
                            fg='#00FFFF',
                            font=('Courier', 7, 'bold'))
        csv_title.pack(anchor='w')

        # Upload buttons
        upload_buttons_frame = tk.Frame(csv_frame, bg='#1a1a1a')
        upload_buttons_frame.pack(fill='x', pady=2)

        self.upload_tick_btn = tk.Button(upload_buttons_frame,
                                        text="📈 UPLOAD TICK DATA",
                                        bg='#22C55E',
                                        fg='white',
                                        font=('Courier', 6, 'bold'),
                                        command=self.upload_tick_csv)
        self.upload_tick_btn.pack(side='left', fill='x', expand=True, padx=(0, 1))

        self.upload_candle_btn = tk.Button(upload_buttons_frame,
                                          text="🕯️ UPLOAD CANDLE DATA",
                                          bg='#3B82F6',
                                          fg='white',
                                          font=('Courier', 6, 'bold'),
                                          command=self.upload_candle_csv)
        self.upload_candle_btn.pack(side='left', fill='x', expand=True, padx=(1, 0))

        # Clear data button
        self.clear_csv_btn = tk.Button(csv_frame,
                                      text="🗑️ CLEAR CSV DATA",
                                      bg='#DC2626',
                                      fg='white',
                                      font=('Courier', 6, 'bold'),
                                      command=self.clear_csv_data_gui,
                                      state='disabled')
        self.clear_csv_btn.pack(fill='x', pady=2)

        # CSV data status
        self.csv_status_frame = tk.Frame(csv_frame, bg='#333333', relief='solid', bd=1)
        self.csv_status_frame.pack(fill='x', pady=2)

        self.csv_status_label = tk.Label(self.csv_status_frame,
                                        text="No CSV data loaded",
                                        bg='#333333',
                                        fg='#888888',
                                        font=('Courier', 5))
        self.csv_status_label.pack(anchor='w', padx=2, pady=1)

        # Settings with confirmation
        settings_frame = tk.Frame(control_frame, bg='#1a1a1a')
        settings_frame.pack(fill='x', padx=5, pady=5)

        self.setting_vars = {}
        for setting, value in self.settings.items():
            label = tk.Label(settings_frame,
                            text=f"{setting.replace('_', ' ').upper()} ($):",
                            bg='#1a1a1a',
                            fg='#CCCCCC',
                            font=('Courier', 7))
            label.pack(anchor='w')

            var = tk.StringVar(value=str(value))
            entry = tk.Entry(settings_frame,
                            textvariable=var,
                            bg='#333333',
                            fg='#00FFFF',
                            font=('Courier', 8),
                            width=15)
            entry.pack(fill='x', pady=2)

            # Bind validation with confirmation
            entry.bind('<FocusOut>', lambda e, s=setting, v=var: self.validate_setting_change(s, v))
            entry.bind('<Return>', lambda e, s=setting, v=var: self.validate_setting_change(s, v))

            self.setting_vars[setting] = var

        # Control buttons
        button_frame = tk.Frame(control_frame, bg='#1a1a1a')
        button_frame.pack(fill='x', padx=5, pady=10)

        self.activate_btn = tk.Button(button_frame,
                                     text="🚀 ACTIVATE FUSION 🚀",
                                     bg='#F97316',
                                     fg='white',
                                     font=('Courier', 8, 'bold'),
                                     command=self.toggle_fusion)
        self.activate_btn.pack(fill='x', pady=2)

        self.stop_btn = tk.Button(button_frame,
                                 text="🛑 STOP FUSION",
                                 bg='#DC2626',
                                 fg='white',
                                 font=('Courier', 8, 'bold'),
                                 command=self.stop_fusion,
                                 state='disabled')
        self.stop_btn.pack(fill='x', pady=2)

        # Reset session button
        self.reset_btn = tk.Button(button_frame,
                                  text="🔑 RESET SESSION",
                                  bg='#8855FF',
                                  fg='white',
                                  font=('Courier', 8, 'bold'),
                                  command=self.reset_session)
        self.reset_btn.pack(fill='x', pady=2)

        # Strategy components - Made scrollable to show all content
        strategy_frame = tk.Frame(control_frame, bg='#1a1a1a')
        strategy_frame.pack(fill='both', expand=True, padx=5, pady=5)

        strategy_title = tk.Label(strategy_frame,
                                 text="🔒 CLASSIFIED ALGORITHMS 🔒",
                                 bg='#1a1a1a',
                                 fg='#FF4444',
                                 font=('Courier', 7, 'bold'))
        strategy_title.pack()

        # Create a canvas and scrollbar for the algorithms
        canvas_frame = tk.Frame(strategy_frame, bg='#1a1a1a')
        canvas_frame.pack(fill='both', expand=True, pady=5)

        algorithms_canvas = tk.Canvas(canvas_frame, bg='#1a1a1a', highlightthickness=0, height=150)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=algorithms_canvas.yview)
        scrollable_frame = tk.Frame(algorithms_canvas, bg='#1a1a1a')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: algorithms_canvas.configure(scrollregion=algorithms_canvas.bbox("all"))
        )

        algorithms_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        algorithms_canvas.configure(yscrollcommand=scrollbar.set)

        algorithms = [
            ("NEURAL ENGINE", "#00FFFF"),
            ("BEAST CORE", "#FF4444"),
            ("QUANTUM MATRIX", "#8855FF"),
            ("FUSION ALGORITHM", "#FF8800"),
            ("RISK MANAGER", "#44FF44"),
            ("SESSION CONTROL", "#8855FF")
        ]

        for name, color in algorithms:
            algo_frame = tk.Frame(scrollable_frame, bg='#333333', relief='solid', bd=1)
            algo_frame.pack(fill='x', pady=2, padx=2)

            algo_label = tk.Label(algo_frame,
                                  text=name,
                                  bg='#333333',
                                  fg=color,
                                  font=('Courier', 7, 'bold'))
            algo_label.pack(anchor='w', padx=3, pady=1)

            status_label = tk.Label(algo_frame,
                                    text="[ACTIVE]",
                                    bg='#333333',
                                    fg='#888888',
                                    font=('Courier', 6))
            status_label.pack(anchor='w', padx=3, pady=1)

        algorithms_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def validate_setting_change(self, setting, var):
        """Validate and confirm setting changes"""
        try:
            new_value = float(var.get())
            old_value = self.settings[setting]
            
            if new_value != old_value:
                # Show confirmation dialog
                confirm = messagebox.askyesno(
                    "Confirm Change",
                    f"Change {setting.replace('_', ' ').title()} from ${old_value} to ${new_value}?\n\nThis will affect your trading parameters.",
                    icon='question'
                )
                
                if confirm:
                    self.settings[setting] = new_value
                    # Update bot settings
                    if self.bot:
                        if setting == 'stake':
                            self.bot.stake = new_value
                        elif setting == 'take_profit':
                            self.bot.take_profit = new_value
                        elif setting == 'stop_loss':
                            self.bot.stop_loss = new_value
                    
                    messagebox.showinfo("Success", f"{setting.replace('_', ' ').title()} updated to ${new_value}")
                else:
                    # Revert to old value
                    var.set(str(old_value))
        except ValueError:
            messagebox.showerror("Invalid Input", f"Please enter a valid number for {setting.replace('_', ' ').title()}")
            var.set(str(self.settings[setting]))  # Revert to old value
    
    def create_statistics_panel(self, parent):
        stats_frame = tk.Frame(parent, bg='#1a1a1a', relief='ridge', bd=2)
        stats_frame.pack(side='left', fill='both', expand=True, padx=2)
        
        title = tk.Label(stats_frame,
                        text="📊 SESSION STATS",
                        bg='#1a1a1a',
                        fg='#00FFFF',
                        font=('Courier', 9, 'bold'))
        title.pack(pady=5)
        
        # Stats grid
        self.stats_frame = tk.Frame(stats_frame, bg='#1a1a1a')
        self.stats_frame.pack(fill='x', padx=5, pady=5)
        
        self.stat_labels = {}
        stats = [
            ("TRADES", f"{self.trades['total']}/20", "#00FFFF"),
            ("WINS", str(self.trades['wins']), "#44FF44"),
            ("LOSSES", str(self.trades['losses']), "#FF4444"),
            ("WIN RATE", "0%", "#FFAA00"),
            ("P/L TODAY", "$0.00", "#44FF44"),
            ("REMAINING", "20", "#8855FF")
        ]
        
        for i, (label, value, color) in enumerate(stats):
            row, col = i // 2, i % 2
            
            stat_container = tk.Frame(self.stats_frame, bg='#333333', relief='solid', bd=1)
            stat_container.grid(row=row, column=col, padx=2, pady=2, sticky='ew')
            self.stats_frame.grid_columnconfigure(col, weight=1)
            
            label_widget = tk.Label(stat_container,
                                   text=label,
                                   bg='#333333',
                                   fg='#888888',
                                   font=('Courier', 6))
            label_widget.pack()
            
            value_widget = tk.Label(stat_container,
                                   text=value,
                                   bg='#333333',
                                   fg=color,
                                   font=('Courier', 8, 'bold'))
            value_widget.pack()
            
            self.stat_labels[label] = value_widget
        
        # Live Feed (moved from separate panel to here)
        feed_frame = tk.Frame(stats_frame, bg='#1a1a1a')
        feed_frame.pack(fill='both', expand=True, padx=5, pady=10)
        
        feed_title = tk.Label(feed_frame,
                             text="📡 FUSION FEED",
                             bg='#1a1a1a',
                             fg='#FF8800',
                             font=('Courier', 8, 'bold'))
        feed_title.pack()
        
        # Scrollable text area
        feed_container = tk.Frame(feed_frame, bg='#1a1a1a')
        feed_container.pack(fill='both', expand=True, pady=5)
        
        self.feed_text = tk.Text(feed_container,
                                bg='#000000',
                                fg='#00FF00',
                                font=('Courier', 6),
                                height=15,
                                width=50,
                                wrap='word',
                                state='disabled')
        
        scrollbar = tk.Scrollbar(feed_container, command=self.feed_text.yview)
        self.feed_text.config(yscrollcommand=scrollbar.set)
        
        self.feed_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def toggle_fusion(self):
        if not self.is_active:
            self.is_active = True
            self.activate_btn.config(text="🔥 FUSION ACTIVE 🔥", bg='#22C55E', state='disabled')
            self.stop_btn.config(state='normal')
            self.status_left.config(text="🌟 FUSION ACTIVE", fg='#44FF44')
            
            # Update settings with confirmation already handled
            for key, var in self.setting_vars.items():
                try:
                    self.settings[key] = float(var.get())
                    # Update bot settings
                    if key == 'stake':
                        self.bot.stake = self.settings[key]
                    elif key == 'take_profit':
                        self.bot.take_profit = self.settings[key]
                    elif key == 'stop_loss':
                        self.bot.stop_loss = self.settings[key]
                except ValueError:
                    pass
            
            # Start trading in separate thread
            trading_thread = threading.Thread(target=self.bot.run_trading_session, daemon=True)
            trading_thread.start()
    
    def stop_fusion(self):
        self.is_active = False
        self.bot.bot_running = False
        self.activate_btn.config(text="🚀 ACTIVATE FUSION 🚀", bg='#F97316', state='normal')
        self.stop_btn.config(state='disabled')
        self.status_left.config(text="⚪ STANDBY", fg='#888888')
    
    def reset_session(self):
        """Reset session with license key"""
        key = simpledialog.askstring("License Key", "Enter license key to reset session:", show='*')
        if key and self.bot.reset_session_with_key(key):
            self._reset_gui_stats()
            messagebox.showinfo("Success", "Session reset successfully!")
            logging.info("🔒 Session reset via GUI")
        else:
            messagebox.showerror("Error", "Invalid license key!")

    def _reset_gui_stats(self):
        """Reset GUI statistics"""
        self.trades = {'total': 0, 'wins': 0, 'losses': 0}
        self.balance = 10000

    def upload_tick_csv(self):
        """Upload tick data CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Tick Data CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="data/tick_data"
        )

        if file_path:
            try:
                if self.bot.load_csv_data(file_path):
                    self.update_csv_status()
                    messagebox.showinfo("Success", f"Tick data loaded successfully!\n\nAsset: {self.bot.csv_asset_name}\nData points: {self.bot.csv_data_count}")
                    logging.info("✅ Tick CSV uploaded via GUI")
                else:
                    messagebox.showerror("Error", "Failed to load tick data. Check the file format and try again.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file: {str(e)}")

    def upload_candle_csv(self):
        """Upload candle data CSV file"""
        file_path = filedialog.askopenfilename(
            title="Select Candle Data CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir="data/candle_data"
        )

        if file_path:
            try:
                if self.bot.load_csv_data(file_path):
                    self.update_csv_status()
                    messagebox.showinfo("Success", f"Candle data loaded successfully!\n\nAsset: {self.bot.csv_asset_name}\nData points: {self.bot.csv_data_count}")
                    logging.info("✅ Candle CSV uploaded via GUI")
                else:
                    messagebox.showerror("Error", "Failed to load candle data. Check the file format and try again.")
            except Exception as e:
                messagebox.showerror("Error", f"Error loading file: {str(e)}")

    def clear_csv_data_gui(self):
        """Clear CSV data via GUI"""
        if messagebox.askyesno("Confirm", "Clear all loaded CSV data and return to browser data?"):
            self.bot.clear_csv_data()
            self.update_csv_status()
            messagebox.showinfo("Success", "CSV data cleared. Using browser data.")
            logging.info("🗑️ CSV data cleared via GUI")

    def update_csv_status(self):
        """Update CSV data status display"""
        if self.bot.csv_data_loaded:
            status_text = f"✅ {self.bot.csv_data_type.upper()} DATA LOADED\n"
            status_text += f"Asset: {self.bot.csv_asset_name}\n"
            status_text += f"Points: {self.bot.csv_data_count:,}\n"
            status_text += f"Range: {self.bot.csv_time_range}"

            self.csv_status_label.config(text=status_text, fg='#44FF44')
            self.clear_csv_btn.config(state='normal')
        else:
            self.csv_status_label.config(text="No CSV data loaded", fg='#888888')
            self.clear_csv_btn.config(state='disabled')
    
    def update_energy_bars(self):
        if self.is_active:
            current_time = time.time()
            self.neural_energy = 75 + math.sin(current_time) * 20
            self.beast_mode = 80 + math.cos(current_time * 0.8) * 15
            self.quantum_strength = 85 + math.sin(current_time * 1.2) * 12
            # FIXED: Master fusion level fixed at 97%
            self.fusion_power = 97
        else:
            self.neural_energy = max(0, self.neural_energy - 2)
            self.beast_mode = max(0, self.beast_mode - 2)
            self.quantum_strength = max(0, self.quantum_strength - 2)
            self.fusion_power = 0  # FIXED: Set to 0 when inactive
        
        # Update energy bar displays
        energies = {
            'NEURAL': (self.neural_energy, '#00FFFF', '🧠'),
            'BEAST': (self.beast_mode, '#FF4444', '💪'),
            'QUANTUM': (self.quantum_strength, '#8855FF', '⚛️')
        }
        
        for name, (value, color, icon) in energies.items():
            if name in self.energy_bars:
                canvas = self.energy_bars[name]
                label = self.energy_labels[name]
                
                canvas.delete("all")
                width = canvas.winfo_width()
                height = canvas.winfo_height()
                
                if width > 1:  # Ensure canvas is initialized
                    fill_width = (value / 100) * width
                    canvas.create_rectangle(0, 0, fill_width, height, fill=color, outline="")
                    label.config(text=f"{icon} {name}: {int(value)}%")
        
        # FIXED: Update master fusion bar to show 97% when active, 0% when inactive
        if hasattr(self, 'master_fusion_canvas'):
            canvas = self.master_fusion_canvas
            canvas.delete("all")
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            
            if width > 1:
                fill_width = (self.fusion_power / 100) * width
                canvas.create_rectangle(0, 0, fill_width, height, fill='#FF8800', outline="")
                canvas.create_text(width//2, height//2, text=f"{int(self.fusion_power)}%", 
                                 fill='white', font=('Courier', 10, 'bold'))
    
    def add_feed_message(self):
        if not self.is_active:
            return
            
        messages = [
            ("NEURAL", f"Neural patterns detected: {random.randint(3, 8)} signals", "#00FFFF"),
            ("BEAST", f"Beast confluence: {random.randint(4, 6)} indicators aligned", "#FF4444"),
            ("QUANTUM", f"Quantum momentum: {random.choice(['Bullish', 'Bearish', 'Neutral'])} bias", "#8855FF"),
            ("FUSION", f"Fusion analysis: {random.choice(['High', 'Medium', 'Ultra'])} confidence", "#FF8800"),
            ("SYSTEM", f"Win rate optimization: {85 + random.random() * 10:.1f}% efficiency", "#44FF44")
        ]
        
        msg_type, content, color = random.choice(messages)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        self.feed_text.config(state='normal')
        
        # Add timestamp
        self.feed_text.insert('end', f"[{timestamp}] ", 'timestamp')
        self.feed_text.tag_config('timestamp', foreground='#888888')
        
        # Add message type
        self.feed_text.insert('end', f"{msg_type}: ", 'msgtype')
        self.feed_text.tag_config('msgtype', foreground=color, font=('Courier', 6, 'bold'))
        
        # Add content
        self.feed_text.insert('end', f"{content}\n", 'content')
        self.feed_text.tag_config('content', foreground='#CCCCCC')
        
        self.feed_text.see('end')
        self.feed_text.config(state='disabled')
        
        # Keep only last 50 lines
        lines = self.feed_text.get('1.0', 'end').split('\n')
        if len(lines) > 50:
            self.feed_text.config(state='normal')
            self.feed_text.delete('1.0', '2.0')
            self.feed_text.config(state='disabled')
    
    def update_statistics(self):
        # Update from bot data
        if self.bot:
            self.trades = {'total': self.bot.total_trades, 'wins': self.bot.win_count, 'losses': self.bot.loss_count}
            self.balance = self.bot.balance
        
        # Update win rate
        win_rate = (self.trades['wins'] / self.trades['total']) * 100 if self.trades['total'] > 0 else 0
        remaining = self.bot.security.get_remaining_trades(self.bot.session_data) if self.bot else 20
        
        # Update status bar
        self.status_right.config(
            text=f"Balance: ${self.balance:,} | Trades: {self.trades['total']}/20 | Win Rate: {win_rate:.1f}%"
        )
        
        # Update stat labels
        stats_update = {
            "TRADES": f"{self.trades['total']}/20",
            "WINS": str(self.trades['wins']),
            "LOSSES": str(self.trades['losses']),
            "WIN RATE": f"{win_rate:.1f}%",
            "P/L TODAY": f"${self.bot.profit_today:.2f}" if self.bot else "$0.00",
            "REMAINING": str(remaining)
        }
        
        for label, value in stats_update.items():
            if label in self.stat_labels:
                self.stat_labels[label].config(text=value)
    
    def animation_loop(self):
        while self.animation_running:
            try:
                self.update_energy_bars()
                
                if self.is_active and random.random() < 0.3:  # 30% chance per cycle
                    self.add_feed_message()
                
                self.update_statistics()
                
                time.sleep(0.1)
            except Exception as e:
                print(f"Animation error: {e}")
                break
    
    def start_animations(self):
        self.animation_running = True
        self.animation_thread = threading.Thread(target=self.animation_loop, daemon=True)
        self.animation_thread.start()
    
    def on_closing(self):
        self.animation_running = False
        if self.bot:
            self.bot.bot_running = False
            if self.bot.api_client:
                self.bot.api_client.disconnect()
            if self.bot.driver:
                self.bot.driver.quit()
        self.root.destroy()

def main():
    # Setup logging with proper encoding for Windows
    import sys
    import argparse
    
    # Configure logging with UTF-8 encoding support
    class SafeStreamHandler(logging.StreamHandler):
        def emit(self, record):
            try:
                super().emit(record)
            except UnicodeEncodeError:
                # Fallback: remove emojis and special characters
                record.msg = str(record.msg).encode('ascii', 'ignore').decode('ascii')
                super().emit(record)
    
    # Setup file handler with UTF-8 encoding
    file_handler = logging.FileHandler('neural_beast_quantum_fusion.log', encoding='utf-8')
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Setup console handler with safe encoding
    console_handler = SafeStreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        handlers=[file_handler, console_handler]
    )
    
    # Suppress urllib3 logger
    logging.getLogger("urllib3").setLevel(logging.ERROR)
    logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Neural Beast Quantum Fusion Trading Bot")
    parser.add_argument("--stream", action="store_true", help="Enable continuous streaming mode")
    parser.add_argument("--stream_mode", type=str, choices=["candle", "tick", "both"], default="both", help="Streaming mode")
    parser.add_argument("--asset_focus", type=str, help="Focus streaming on a specific asset")
    args = parser.parse_args()
    
    try:
        # Initialize Neural Beast Quantum Fusion GUI
        root = tk.Tk()
        app = NeuralBeastGUI(root, args)  # Pass args to GUI
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        # Setup cleanup
        def cleanup():
            if app.bot:
                if app.bot.api_client:
                    app.bot.api_client.disconnect()
                if app.bot.driver:
                    app.bot.driver.quit()

        atexit.register(cleanup)
        
        # Run the Neural Beast Quantum Fusion application
        root.mainloop()
        
    except Exception as e:
        logging.error(f"Neural Beast Quantum Fusion Application error: {e}")
        messagebox.showerror("Error", f"Neural Beast Quantum Fusion failed to start: {str(e)}")

if __name__ == "__main__":
    # Check for stream mode
    import sys
    if "--stream" in sys.argv:
        run_stream_mode()
    else:
        main()

def run_stream_mode():
    """Run the bot in headless streaming mode"""
    # Minimal setup for headless operation
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Neural Beast Quantum Fusion Trading Bot")
    parser.add_argument("--stream", action="store_true", help="Enable continuous streaming mode")
    parser.add_argument("--stream_mode", type=str, choices=["candle", "tick", "both"], default="both", help="Streaming mode")
    parser.add_argument("--asset_focus", type=str, help="Focus streaming on a specific asset")
    args = parser.parse_args()

    bot = BeastTradingBot(args=args)

    # Ensure driver is setup for streaming
    if not bot.driver:
        if not bot.setup_driver():
            logging.error("Failed to setup WebDriver. Exiting.")
            sys.exit(1)

    # Start the trading session in a separate thread
    trading_thread = threading.Thread(target=bot.run_trading_session, daemon=True)
    trading_thread.start()

    # Keep the main thread alive
    try:
        while trading_thread.is_alive():
            trading_thread.join(timeout=1.0)
    except KeyboardInterrupt:
        logging.info("Shutting down stream mode...")
        bot.bot_running = False
        # Wait for thread to finish
        trading_thread.join()
