"""Pytest configuration and fixtures for QuantumFlux API tests."""

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import after path setup
from src.models.api_models import ConnectionStatus


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_dual_manager():
    """Mock dual API manager for testing."""
    mock = Mock()
    mock.get_connection_status.return_value = ConnectionStatus(
        webdriver_connected=True,
        websocket_connected=True,
        platform_logged_in=True,
        last_heartbeat=datetime.now()
    )
    mock.get_candles.return_value = [
        {
            "timestamp": "2024-01-01T00:00:00",
            "open": 1.0,
            "high": 1.1,
            "low": 0.9,
            "close": 1.05,
            "volume": 1000
        }
    ]
    mock.get_latest_data.return_value = {
        "EURUSD": {
            "price": 1.1234,
            "timestamp": "2024-01-01T00:00:00",
            "bid": 1.1233,
            "ask": 1.1235
        }
    }
    # Add the method that WebSocket endpoint actually calls
    mock.get_websocket_data.return_value = [
        {
            "price": 1.1234,
            "timestamp": "2024-01-01T00:00:00",
            "symbol": "EURUSD",
            "bid": 1.1233,
            "ask": 1.1235
        }
    ]
    mock.initialize = AsyncMock()
    mock.cleanup = AsyncMock()
    return mock


@pytest.fixture
def mock_strategy_tester():
    """Mock strategy tester for testing."""
    mock = Mock()
    mock.strategies = {}
    mock.add_strategy.return_value = "strategy_123"
    mock.start_ab_test.return_value = "test_456"
    mock.get_test_status.return_value = {
        "test_id": "test_456",
        "status": "running",
        "progress": 50.0,
        "results": None,
        "strategy_a_performance": {
            "total_trades": 10,
            "winning_trades": 6,
            "total_profit": 150.0,
            "win_rate": 0.6
        },
        "strategy_b_performance": {
            "total_trades": 10,
            "winning_trades": 7,
            "total_profit": 200.0,
            "win_rate": 0.7
        }
    }
    return mock


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    # Import here to avoid circular imports
    from backend import app
    return TestClient(app)


@pytest.fixture
def sample_strategy_config():
    """Sample strategy configuration for testing."""
    return {
        "strategy_type": "trend_following",
        "parameters": {
            "period": 14,
            "threshold": 0.5,
            "signal_strength": 0.7
        },
        "risk_management": {
            "max_risk_per_trade": 0.02,
            "stop_loss": 0.05,
            "take_profit": 0.10,
            "max_daily_trades": 10
        },
        "timeframe": "1m",
        "assets": ["EURUSD", "GBPUSD"]
    }


@pytest.fixture
def sample_ab_test_config():
    """Sample A/B test configuration for testing."""
    return {
        "name": "Trend vs Mean Reversion Test",
        "description": "Comparing trend following vs mean reversion strategies",
        "strategy_a_id": "strategy_trend",
        "strategy_b_id": "strategy_mean_reversion",
        "test_duration_hours": 24,
        "initial_balance": 1000.0,
        "max_trades_per_strategy": 50
    }


@pytest.fixture
def mock_logging():
    """Mock logging to prevent log file creation during tests."""
    with patch('src.utils.logging_config.setup_logging') as mock_setup:
        mock_loggers = {
            'app': Mock(),
            'api': Mock(),
            'performance': Mock(),
            'security': Mock(),
            'errors': Mock()
        }
        mock_setup.return_value = mock_loggers
        yield mock_loggers


@pytest.fixture(autouse=True)
def mock_dependencies():
    """Auto-use fixture to mock external dependencies."""
    with patch('src.core.app_state.get_app_state') as mock_get_app_state, \
         patch('backend.setup_logging') as mock_logging:
        
        # Create mock app_state instance
        mock_app_state = Mock()
        
        # Setup dual manager mock with all required methods
        mock_dual = Mock()
        mock_dual.get_connection_status.return_value = ConnectionStatus(
            webdriver_connected=True,
            websocket_connected=True,
            platform_logged_in=True,
            last_heartbeat=datetime.now()
        )
        mock_dual.initialize = AsyncMock()
        mock_dual.cleanup = AsyncMock()
        mock_dual.get_latest_candles = AsyncMock(return_value=[])
        mock_dual.get_websocket_data = AsyncMock(return_value=[])
        mock_dual.execute_trade = AsyncMock()
        mock_dual.is_collecting = True
        mock_dual.start_websocket_collection = AsyncMock()
        mock_dual.setup_websocket_interception = AsyncMock()
        
        # Setup strategy tester mock
        mock_tester = Mock()
        mock_tester.strategies = {}
        mock_tester.add_strategy.return_value = "strategy_123"
        mock_tester.start_ab_test.return_value = "test_456"
        
        # Setup capabilities adapter mock
        mock_capabilities_adapter = Mock()
        mock_capabilities_adapter.get_streaming_status.return_value = {
            "connected": True,
            "streaming": False,
            "capabilities": {}
        }
        mock_capabilities_adapter.attach_to_existing_session = AsyncMock(return_value=True)
        mock_capabilities_adapter.get_latest_candles = AsyncMock(return_value=[])
        mock_capabilities_adapter.get_latest_data = AsyncMock(return_value={})
        
        # Attach all components to mock app_state
        mock_app_state.dual_manager = mock_dual
        mock_app_state.tester = mock_tester
        mock_app_state.capabilities_adapter = mock_capabilities_adapter
        mock_app_state.initialized = True
        
        # Make get_app_state return the mock app_state
        mock_get_app_state.return_value = mock_app_state
        
        # Setup logging mock
        mock_logging.return_value = {
            'app': Mock(),
            'api': Mock(),
            'performance': Mock(),
            'security': Mock(),
            'errors': Mock()
        }
        
        yield {
            'app_state': mock_app_state,
            'dual_manager': mock_dual,
            'tester': mock_tester,
            'capabilities_adapter': mock_capabilities_adapter,
            'logging': mock_logging
        }


@pytest.fixture
def disable_rate_limiting():
    """Disable rate limiting for tests."""
    with patch('src.middleware.rate_limiter.RateLimiter.is_allowed') as mock_allowed:
        mock_allowed.return_value = (True, {
            "limit": 100,
            "remaining": 99,
            "reset": 3600,
            "retry_after": 0
        })
        yield


@pytest.fixture
def mock_websocket_data():
    """Mock WebSocket data for testing."""
    return {
        "EURUSD": {
            "price": 1.1234,
            "timestamp": "2024-01-01T12:00:00",
            "bid": 1.1233,
            "ask": 1.1235,
            "volume": 1500,
            "change": 0.0012,
            "change_percent": 0.11
        },
        "GBPUSD": {
            "price": 1.2567,
            "timestamp": "2024-01-01T12:00:00",
            "bid": 1.2566,
            "ask": 1.2568,
            "volume": 1200,
            "change": -0.0023,
            "change_percent": -0.18
        }
    }


# Test data generators
def generate_candle_data(count=10, asset="EURUSD"):
    """Generate sample candle data for testing."""
    candles = []
    base_price = 1.1000
    
    for i in range(count):
        timestamp = f"2024-01-01T{i:02d}:00:00"
        open_price = base_price + (i * 0.001)
        high_price = open_price + 0.002
        low_price = open_price - 0.001
        close_price = open_price + 0.0005
        
        candles.append({
            "timestamp": timestamp,
            "open": round(open_price, 5),
            "high": round(high_price, 5),
            "low": round(low_price, 5),
            "close": round(close_price, 5),
            "volume": 1000 + (i * 100)
        })
    
    return candles


def generate_strategy_performance(trades=20, win_rate=0.6):
    """Generate sample strategy performance data."""
    winning_trades = int(trades * win_rate)
    losing_trades = trades - winning_trades
    
    return {
        "total_trades": trades,
        "winning_trades": winning_trades,
        "losing_trades": losing_trades,
        "win_rate": win_rate,
        "total_profit": round((winning_trades * 50) - (losing_trades * 30), 2),
        "average_profit_per_trade": round(((winning_trades * 50) - (losing_trades * 30)) / trades, 2),
        "max_drawdown": round(losing_trades * 30 * 0.3, 2),
        "sharpe_ratio": round(1.2 + (win_rate * 0.5), 2)
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "websocket: mark test as websocket test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test names."""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        
        # Add slow marker to tests that might be slow
        if any(keyword in item.name.lower() for keyword in ["websocket", "rate_limit", "performance"]):
            item.add_marker(pytest.mark.slow)
        
        # Add websocket marker to websocket tests
        if "websocket" in item.name.lower():
            item.add_marker(pytest.mark.websocket)