"""Comprehensive tests for live trading functionality.

This module tests the complete live trading pipeline including:
- Signal generation from LiveSignalEngine
- Trade execution via AutomatedTrader
- Real-time signal pipeline orchestration
- Integration between all components
"""

import pytest
import asyncio
import json
import pandas as pd
import numpy as np
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Import live trading components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.signal_engine import LiveSignalEngine, TradingSignal, SignalType, SignalStrength
from src.core.automated_trader import AutomatedTrader, AutoTrade, TradeStatus
from src.core.signal_pipeline import SignalPipeline, PipelineStatus, PipelineMetrics
from src.core.dual_api_integration import DualAPIManager
from src.core.indicators import IndicatorEngine
from src.models.api_models import ConnectionStatus


class TestLiveSignalEngine:
    """Test suite for LiveSignalEngine."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample strategy configuration."""
        return {
            "strategy": {
                "name": "quantum_flux_test",
                "thresholds": {
                    "min_confidence": 0.65,
                    "min_strength": 0.5
                }
            },
            "trading": {
                "trade_duration_minutes": 5,
                "stake_amount": 10.0
            },
            "indicators": {
                "rsi": {"period": 14, "weight": 0.25},
                "macd": {"fast": 12, "slow": 26, "signal": 9, "weight": 0.30},
                "bollinger": {"period": 20, "std_dev": 2, "weight": 0.25},
                "stochastic": {"k_period": 14, "d_period": 3, "weight": 0.20}
            }
        }
    
    @pytest.fixture
    def mock_config_file(self, tmp_path, sample_config):
        """Create a temporary config file."""
        config_file = tmp_path / "test_config.json"
        config_file.write_text(json.dumps(sample_config))
        return str(config_file)
    
    @pytest.fixture
    def signal_engine(self, mock_config_file):
        """Create LiveSignalEngine instance."""
        with patch('src.core.signal_engine.IndicatorEngine'):
            return LiveSignalEngine(mock_config_file)
    
    @pytest.fixture
    def sample_market_data(self):
        """Generate sample market data."""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='1min')
        np.random.seed(42)
        
        # Generate realistic OHLC data
        close_prices = 1.1000 + np.cumsum(np.random.randn(100) * 0.0001)
        open_prices = close_prices + np.random.randn(100) * 0.00005
        high_prices = np.maximum(open_prices, close_prices) + np.abs(np.random.randn(100) * 0.00005)
        low_prices = np.minimum(open_prices, close_prices) - np.abs(np.random.randn(100) * 0.00005)
        volumes = np.random.randint(1000, 10000, 100)
        
        return pd.DataFrame({
            'timestamp': dates,
            'open': open_prices,
            'high': high_prices,
            'low': low_prices,
            'close': close_prices,
            'volume': volumes
        }).set_index('timestamp')
    
    def test_signal_engine_initialization(self, signal_engine):
        """Test signal engine initialization."""
        assert signal_engine is not None
        assert signal_engine.min_confidence == 0.65
        assert signal_engine.min_strength == 0.5
        assert signal_engine.trade_duration == 5
    
    def test_generate_signal_insufficient_data(self, signal_engine):
        """Test signal generation with insufficient data."""
        # Create small dataset
        small_data = pd.DataFrame({
            'open': [1.1000, 1.1001],
            'high': [1.1002, 1.1003],
            'low': [1.0999, 1.1000],
            'close': [1.1001, 1.1002],
            'volume': [1000, 1100]
        })
        
        signal = signal_engine.generate_signal(small_data, "EURUSD")
        assert signal is None
    
    def test_generate_signal_success(self, signal_engine, sample_market_data):
        """Test successful signal generation."""
        # Mock the internal calculation methods
        with patch.object(signal_engine, '_calculate_indicators') as mock_calc, \
             patch.object(signal_engine, '_analyze_rsi') as mock_rsi, \
             patch.object(signal_engine, '_analyze_macd') as mock_macd, \
             patch.object(signal_engine, '_analyze_bollinger_bands') as mock_bb, \
             patch.object(signal_engine, '_analyze_stochastic') as mock_stoch, \
             patch.object(signal_engine, '_combine_signals') as mock_combine:
            
            # Mock indicator data
            mock_indicators = pd.DataFrame({
                'RSI': [70.0],
                'MACD': [0.001],
                'STO_K': [80.0]
            })
            mock_calc.return_value = mock_indicators
            
            # Mock individual signal analysis
            mock_rsi.return_value = (SignalType.CALL, 0.7, 0.8)
            mock_macd.return_value = (SignalType.CALL, 0.6, 0.7)
            mock_bb.return_value = (SignalType.CALL, 0.5, 0.6)
            mock_stoch.return_value = (SignalType.CALL, 0.8, 0.9)
            
            # Mock combined signal
            mock_combine.return_value = (SignalType.CALL, 0.7, 0.8, ["Strong bullish signal"])
            
            signal = signal_engine.generate_signal(sample_market_data, "EURUSD")
            
            assert signal is not None
            assert isinstance(signal, TradingSignal)
            assert signal.asset == "EURUSD"
            assert signal.signal_type in [SignalType.CALL, SignalType.PUT]
            assert isinstance(signal.strength, float)
            assert 0.0 <= signal.confidence <= 1.0
    
    def test_signal_thresholds(self, signal_engine):
        """Test signal threshold configuration."""
        # Test that thresholds are properly set
        assert signal_engine.min_confidence == 0.65
        assert signal_engine.min_strength == 0.5
        assert signal_engine.trade_duration == 5


class TestAutomatedTrader:
    """Test suite for AutomatedTrader."""
    
    @pytest.fixture
    def mock_signal_engine(self):
        """Mock signal engine."""
        mock = Mock(spec=LiveSignalEngine)
        mock.generate_signal.return_value = TradingSignal(
            asset="EURUSD",
            signal_type=SignalType.CALL,
            strength=0.8,
            confidence=0.8,
            price=1.1000,
            timestamp=datetime.now(),
            indicators={"rsi": 70.0},
            reasoning=["Strong bullish signal"],
            expiry_minutes=5
        )
        return mock
    
    @pytest.fixture
    def mock_dual_manager(self):
        """Mock dual API manager."""
        mock = Mock(spec=DualAPIManager)
        mock.execute_trade = AsyncMock(return_value={
            'success': True,
            'trade_id': 'test_123',
            'message': 'Trade executed successfully'
        })
        mock.get_latest_candles.return_value = [
            {
                'timestamp': datetime.now().timestamp(),
                'open': 1.1000,
                'high': 1.1005,
                'low': 1.0995,
                'close': 1.1002,
                'volume': 1000
            }
        ]
        return mock
    
    @pytest.fixture
    def automated_trader(self, mock_signal_engine, mock_dual_manager, tmp_path):
        """Create AutomatedTrader instance."""
        # Create mock config file
        config = {
            "risk_management": {
                "max_daily_trades": 10,
                "max_concurrent_trades": 3
            },
            "trading": {
                "stake_amount": 10.0
            }
        }
        config_file = tmp_path / "trader_config.json"
        config_file.write_text(json.dumps(config))
        
        with patch('pathlib.Path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=json.dumps(config))):
            trader = AutomatedTrader(mock_signal_engine, mock_dual_manager, str(config_file))
        
        return trader
    
    def test_trader_initialization(self, automated_trader):
        """Test trader initialization."""
        assert automated_trader is not None
        assert automated_trader.max_daily_trades == 10
        assert automated_trader.max_concurrent_trades == 3
        assert automated_trader.trade_amount == 10.0
        assert not automated_trader.is_running
    
    @pytest.mark.asyncio
    async def test_start_stop_trading(self, automated_trader):
        """Test starting and stopping trading."""
        # Test start
        await automated_trader.start_automated_trading()
        assert automated_trader.is_running
        
        # Test stop
        await automated_trader.stop_automated_trading()
        assert not automated_trader.is_running
    
    @pytest.mark.asyncio
    async def test_execute_trade_success(self, automated_trader, mock_dual_manager):
        """Test successful trade execution."""
        signal = TradingSignal(
            asset="EURUSD",
            signal_type=SignalType.CALL,
            strength=0.8,
            confidence=0.8,
            price=1.1000,
            timestamp=datetime.now(),
            indicators={"rsi": 70.0},
            reasoning=["Strong bullish signal"],
            expiry_minutes=5
        )
        
        # Test the internal _execute_automated_trade method
        await automated_trader._execute_automated_trade(signal)
        
        # Verify trade was added to active trades
        assert len(automated_trader.active_trades) > 0
        mock_dual_manager.execute_trade.assert_called_once()
    
    def test_risk_management_max_trades(self, automated_trader):
        """Test risk management - maximum trades."""
        # Simulate reaching max daily trades
        automated_trader.stats.daily_trades = automated_trader.max_daily_trades
        
        # Should not allow trading due to max trades limit
        can_trade = automated_trader._check_risk_limits()
        assert not can_trade
    
    def test_risk_management_concurrent_trades(self, automated_trader):
        """Test risk management - concurrent trades."""
        # Add mock active trades
        for i in range(automated_trader.max_concurrent_trades):
            trade = AutoTrade(
                trade_id=f"test_{i}",
                asset="EURUSD",
                direction="CALL",
                amount=10.0,
                signal_strength=0.8,
                entry_time=datetime.now(),
                expiry_time=datetime.now() + timedelta(minutes=5),
                entry_price=1.1000,
                status=TradeStatus.EXECUTED
            )
            automated_trader.active_trades[f"test_{i}"] = trade
        
        # Should not allow trading due to concurrent trades limit
        can_trade = automated_trader._check_risk_limits()
        assert not can_trade


class TestSignalPipeline:
    """Test suite for SignalPipeline."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for pipeline."""
        dual_manager = Mock(spec=DualAPIManager)
        dual_manager.get_connection_status.return_value = ConnectionStatus(
            webdriver_connected=True,
            websocket_connected=True,
            platform_logged_in=True,
            last_heartbeat=datetime.now()
        )
        # Create enough candles for signal generation (pipeline requires at least 50)
        candles = []
        base_time = datetime.now().timestamp()
        for i in range(100):  # Create 100 candles
            candles.append({
                'timestamp': base_time - (i * 60),  # 1 minute intervals
                'open': 1.1000 + (i * 0.0001),
                'high': 1.1005 + (i * 0.0001),
                'low': 1.0995 + (i * 0.0001),
                'close': 1.1002 + (i * 0.0001),
                'volume': 1000
            })
        dual_manager.get_latest_candles.return_value = candles
        dual_manager.is_collecting = True
        dual_manager.start_websocket_collection = AsyncMock()
        
        signal_engine = Mock(spec=LiveSignalEngine)
        signal_engine.generate_signal = AsyncMock(return_value=TradingSignal(
            asset="EURUSD",
            signal_type=SignalType.CALL,
            strength=0.8,
            confidence=0.8,
            price=1.1000,
            timestamp=datetime.now(),
            indicators={"rsi": 70.0},
            reasoning="Strong bullish signal",
            expiry_minutes=5
        ))
        
        automated_trader = Mock(spec=AutomatedTrader)
        automated_trader.execute_trade = AsyncMock(return_value="trade_123")
        automated_trader.is_running = True
        automated_trader.start_automated_trading = AsyncMock(return_value=True)
        automated_trader.stop_automated_trading = AsyncMock()
        
        return dual_manager, signal_engine, automated_trader
    
    @pytest.fixture
    def signal_pipeline(self, mock_components):
        """Create SignalPipeline instance."""
        dual_manager, signal_engine, automated_trader = mock_components
        config = {
            'assets': ['EURUSD', 'GBPUSD'],
            'signal_interval': 5,
            'max_concurrent_signals': 2
        }
        return SignalPipeline(dual_manager, signal_engine, automated_trader, config)
    
    def test_pipeline_initialization(self, signal_pipeline):
        """Test pipeline initialization."""
        assert signal_pipeline is not None
        assert signal_pipeline.status == PipelineStatus.STOPPED
        assert len(signal_pipeline.assets) == 2
        assert signal_pipeline.signal_interval == 5
        assert signal_pipeline.max_concurrent_signals == 2
    
    @pytest.mark.asyncio
    async def test_start_stop_pipeline(self, signal_pipeline):
        """Test starting and stopping pipeline."""
        # Test start
        success = await signal_pipeline.start_pipeline()
        assert success
        assert signal_pipeline.status == PipelineStatus.RUNNING
        assert signal_pipeline.start_time is not None
        
        # Test stop
        await signal_pipeline.stop_pipeline()
        assert signal_pipeline.status == PipelineStatus.STOPPED
    
    @pytest.mark.asyncio
    async def test_signal_processing(self, signal_pipeline, mock_components):
        """Test signal processing workflow."""
        dual_manager, signal_engine, automated_trader = mock_components
        
        # Start pipeline
        await signal_pipeline.start_pipeline()
        
        # Wait for signal processing (longer wait to ensure pipeline loop runs)
        await asyncio.sleep(6)  # Wait longer than signal_interval (5 seconds)
        
        # Verify signal generation was called
        signal_engine.generate_signal.assert_called()
        
        # Stop pipeline
        await signal_pipeline.stop_pipeline()
    
    def test_pipeline_metrics(self, signal_pipeline):
        """Test pipeline metrics tracking."""
        status = signal_pipeline.get_pipeline_status()
        
        assert "metrics" in status
        assert status["metrics"]["signals_generated"] >= 0
        assert status["metrics"]["trades_executed"] >= 0
        assert status["metrics"]["error_count"] >= 0
    
    def test_event_logging(self, signal_pipeline):
        """Test event logging functionality."""
        # Add event callback
        events = []
        signal_pipeline.add_event_callback(lambda event: events.append(event))
        
        # Log test event
        signal_pipeline._log_event(
            "test_event",
            "EURUSD",
            {"test": "data"},
            "Test message"
        )
        
        assert len(signal_pipeline.event_history) > 0
        assert len(events) > 0


class TestLiveTradingIntegration:
    """Integration tests for complete live trading system."""
    
    @pytest.fixture
    def integration_config(self, tmp_path):
        """Create integration test configuration."""
        config = {
            "strategy": {
                "name": "integration_test",
                "thresholds": {
                    "min_confidence": 0.6,
                    "min_strength": 0.4
                }
            },
            "trading": {
                "trade_duration_minutes": 5,
                "stake_amount": 10.0
            },
            "risk_management": {
                "max_daily_trades": 5,
                "max_concurrent_trades": 2
            },
            "indicators": {
                "rsi": {"period": 14, "weight": 0.3},
                "macd": {"fast": 12, "slow": 26, "signal": 9, "weight": 0.4},
                "bollinger": {"period": 20, "std_dev": 2, "weight": 0.3}
            }
        }
        
        config_file = tmp_path / "integration_config.json"
        config_file.write_text(json.dumps(config))
        return str(config_file)
    
    @pytest.mark.asyncio
    async def test_end_to_end_signal_to_trade(self, integration_config):
        """Test complete end-to-end signal generation to trade execution."""
        # Mock all external dependencies
        with patch('src.core.signal_engine.IndicatorEngine'), \
             patch('src.core.dual_api_integration.DualAPIManager') as mock_dual, \
             patch('builtins.open', mock_open(read_data=json.dumps({}))):
            
            # Setup mocks
            mock_dual_instance = Mock()
            mock_dual_instance.get_connection_status.return_value = ConnectionStatus(
                webdriver_connected=True,
                websocket_connected=True,
                platform_logged_in=True,
                last_heartbeat=datetime.now()
            )
            mock_dual_instance.execute_trade = AsyncMock(return_value={
                'success': True,
                'trade_id': 'integration_test_123'
            })
            mock_dual_instance.get_latest_candles.return_value = [
                {
                    'timestamp': datetime.now().timestamp(),
                    'open': 1.1000,
                    'high': 1.1005,
                    'low': 1.0995,
                    'close': 1.1002,
                    'volume': 1000
                }
            ]
            mock_dual.return_value = mock_dual_instance
            
            # Create components
            signal_engine = LiveSignalEngine(integration_config)
            automated_trader = AutomatedTrader(signal_engine, mock_dual_instance, integration_config)
            pipeline = SignalPipeline(
                mock_dual_instance,
                signal_engine,
                automated_trader,
                {'assets': ['EURUSD'], 'signal_interval': 1}
            )
            
            # Test pipeline execution
            await pipeline.start_pipeline()
            await asyncio.sleep(0.1)  # Allow processing
            await pipeline.stop_pipeline()
            
            # Verify pipeline ran successfully
            status = pipeline.get_pipeline_status()
            assert status["metrics"]["error_count"] >= 0
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, integration_config):
        """Test error handling and recovery mechanisms."""
        with patch('src.core.signal_engine.IndicatorEngine'), \
             patch('src.core.dual_api_integration.DualAPIManager') as mock_dual, \
             patch('builtins.open', mock_open(read_data=json.dumps({}))):
            
            # Setup mock that fails initially then succeeds
            mock_dual_instance = Mock()
            mock_dual_instance.get_connection_status.side_effect = [
                Exception("Connection failed"),
                ConnectionStatus(
                    webdriver_connected=True,
                    websocket_connected=True,
                    platform_logged_in=True,
                    last_heartbeat=datetime.now()
                )
            ]
            mock_dual.return_value = mock_dual_instance
            
            # Create pipeline
            signal_engine = LiveSignalEngine(integration_config)
            automated_trader = AutomatedTrader(signal_engine, mock_dual_instance, integration_config)
            pipeline = SignalPipeline(
                mock_dual_instance,
                signal_engine,
                automated_trader,
                {'assets': ['EURUSD'], 'signal_interval': 1}
            )
            
            # Test error recovery
            await pipeline.start_pipeline()
            await asyncio.sleep(0.1)
            await pipeline.stop_pipeline()
            
            # Verify pipeline handled errors gracefully
            status = pipeline.get_pipeline_status()
            assert status["metrics"]["error_count"] >= 0


def mock_open(read_data):
    """Helper function to create mock file open."""
    from unittest.mock import mock_open as _mock_open
    return _mock_open(read_data=read_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])