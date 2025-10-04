"""Standalone tests for Phase 3: Strategy Engine & Automation - Direct testing without conftest."""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_capabilities():
    """Mock the capabilities adapter for direct testing."""
    with patch('backend.capabilities') as mock_capabilities:
        # Create a mock adapter
        mock_adapter = Mock()

        # Mock connection status
        mock_adapter.is_connected = True
        mock_adapter.get_streaming_status.return_value = {
            "connected": True,
            "streaming": True,
            "capabilities": {
                "signal_generation": True,
                "automated_trading": True,
                "strategy_management": True,
                "ab_testing": True
            }
        }

        # Mock signal generation
        mock_adapter.generate_signal.return_value = {
            "asset": "EURUSD",
            "signals": {
                "SMA": {"signal": "bullish", "confidence": 0.7, "sma_10": 1.085, "sma_20": 1.082},
                "RSI": {"signal": "neutral", "confidence": 0.5, "rsi": 55.2},
                "MACD": {"signal": "bullish", "confidence": 0.6, "macd": 0.002}
            },
            "candles_analyzed": 30,
            "signal_types": ["SMA", "RSI", "MACD"],
            "data_source": "real_time_data"
        }

        # Mock automated trading
        mock_adapter.manage_automated_trading.return_value = {
            "status": "started",
            "strategy_id": "quantum_flux_1min",
            "assets": ["EURUSD", "GBPUSD"],
            "trading_stats": {
                "is_running": True,
                "start_time": datetime.now().isoformat(),
                "trades_executed": 0,
                "total_pnl": 0.0,
                "active_positions": 0
            }
        }

        # Mock strategy management
        mock_adapter.manage_strategy.return_value = {
            "strategies": [
                {
                    "id": "quantum_flux_1min",
                    "name": "Quantum Flux 1-Minute Strategy",
                    "description": "Advanced 1-minute timeframe strategy"
                },
                {
                    "id": "conservative_sma",
                    "name": "Conservative SMA Strategy",
                    "description": "Simple moving average strategy"
                }
            ],
            "count": 2
        }

        # Mock A/B testing
        mock_adapter.manage_ab_testing.return_value = {
            "test_name": "strategy_comparison_test",
            "status": "started",
            "strategy_a": "quantum_flux_1min",
            "strategy_b": "conservative_sma",
            "duration_minutes": 60,
            "sample_size": 100
        }

        # Assign mock to capabilities
        mock_capabilities.return_value = mock_adapter

        yield mock_adapter


class TestPhase3Endpoints:
    """Direct tests for Phase 3 endpoints."""

    def test_signal_generation_endpoint(self, client, mock_capabilities):
        """Test signal generation endpoint directly."""
        response = client.get("/trade/signal/EURUSD")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["asset"] == "EURUSD"
        assert "signals" in data
        assert "SMA" in data["signals"]
        assert "RSI" in data["signals"]
        assert "MACD" in data["signals"]
        assert data["candles_analyzed"] == 30
        assert data["data_source"] == "real_time_data"

    def test_automated_trading_start_endpoint(self, client, mock_capabilities):
        """Test automated trading start endpoint."""
        response = client.post("/auto-trading/start?strategy_id=quantum_flux_1min&assets=EURUSD,GBPUSD")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Automated trading started"
        assert data["strategy_id"] == "quantum_flux_1min"
        assert "EURUSD" in data["assets"]
        assert "GBPUSD" in data["assets"]

    def test_automated_trading_status_endpoint(self, client, mock_capabilities):
        """Test automated trading status endpoint."""
        response = client.get("/auto-trading/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["is_running"] is True
        assert "trading_stats" in data

    def test_automated_trading_stop_endpoint(self, client, mock_capabilities):
        """Test automated trading stop endpoint."""
        mock_capabilities.manage_automated_trading.return_value = {
            "status": "stopped",
            "final_stats": {
                "is_running": False,
                "trades_executed": 5,
                "total_pnl": 12.5
            },
            "active_trades": []
        }

        response = client.post("/auto-trading/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "Automated trading stopped"
        assert data["final_stats"]["trades_executed"] == 5

    def test_strategies_list_endpoint(self, client, mock_capabilities):
        """Test strategies list endpoint."""
        response = client.get("/strategies")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["count"] == 2
        assert len(data["strategies"]) == 2
        assert data["strategies"][0]["id"] == "quantum_flux_1min"
        assert data["strategies"][1]["id"] == "conservative_sma"

    def test_strategy_get_endpoint(self, client, mock_capabilities):
        """Test strategy get endpoint."""
        mock_capabilities.manage_strategy.return_value = {
            "strategy": {
                "strategy_id": "quantum_flux_1min",
                "name": "Quantum Flux 1-Minute Strategy",
                "description": "Advanced 1-minute timeframe strategy",
                "parameters": {"timeframe": "1m", "indicators": ["SMA", "RSI", "MACD"]},
                "risk_settings": {"max_position_size": 0.01, "min_confidence": 0.65}
            }
        }

        response = client.get("/strategies/quantum_flux_1min")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["strategy"]["strategy_id"] == "quantum_flux_1min"
        assert data["strategy"]["name"] == "Quantum Flux 1-Minute Strategy"

    def test_strategy_performance_endpoint(self, client, mock_capabilities):
        """Test strategy performance endpoint."""
        mock_capabilities.manage_strategy.return_value = {
            "strategy_id": "quantum_flux_1min",
            "performance": {
                "total_trades": 150,
                "win_rate": 0.68,
                "total_pnl": 245.75,
                "avg_profit": 1.64,
                "max_drawdown": 15.2,
                "sharpe_ratio": 1.23
            }
        }

        response = client.get("/strategies/quantum_flux_1min/performance")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["strategy_id"] == "quantum_flux_1min"
        assert data["performance"]["win_rate"] == 0.68

    def test_ab_test_start_endpoint(self, client, mock_capabilities):
        """Test A/B test start endpoint."""
        test_data = {
            "test_name": "strategy_comparison_test",
            "strategy_a": "quantum_flux_1min",
            "strategy_b": "conservative_sma",
            "duration_minutes": 60,
            "sample_size": 100
        }

        response = client.post("/tests/ab/start", json=test_data)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "A/B test started"
        assert data["test_name"] == "strategy_comparison_test"

    def test_ab_test_status_endpoint(self, client, mock_capabilities):
        """Test A/B test status endpoint."""
        mock_capabilities.manage_ab_testing.return_value = {
            "active_tests": ["test_1", "test_2"],
            "completed_tests": ["test_3"]
        }

        response = client.get("/tests/ab/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "test_1" in data["data"]["active_tests"]
        assert "test_3" in data["data"]["completed_tests"]

    def test_ab_test_results_endpoint(self, client, mock_capabilities):
        """Test A/B test results endpoint."""
        mock_capabilities.manage_ab_testing.return_value = {
            "test_name": "completed_test",
            "results": {
                "winner": "A",
                "confidence_level": "95%",
                "significant": True,
                "pnl_difference": 25.5,
                "recommendation": "Use strategy quantum_flux_1min (A)"
            },
            "groups": {
                "A": {"strategy": "quantum_flux_1min", "metrics": {"win_rate": 0.72, "total_pnl": 185.5}},
                "B": {"strategy": "conservative_sma", "metrics": {"win_rate": 0.65, "total_pnl": 160.0}}
            }
        }

        response = client.get("/tests/ab/results?test_name=completed_test")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["test_name"] == "completed_test"
        assert data["results"]["winner"] == "A"
        assert data["results"]["significant"] is True

    def test_capabilities_status_includes_phase3(self, client, mock_capabilities):
        """Test that capabilities status includes Phase 3 features."""
        response = client.get("/api/capabilities/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "status" in data
        capabilities = data["status"]["capabilities"]
        assert capabilities["signal_generation"] is True
        assert capabilities["automated_trading"] is True
        assert capabilities["strategy_management"] is True
        assert capabilities["ab_testing"] is True

    def test_not_connected_error_handling(self, client, mock_capabilities):
        """Test error handling when not connected."""
        mock_capabilities.is_connected = False
        mock_capabilities.generate_signal.return_value = {"error": "Not connected to Chrome session"}

        response = client.get("/trade/signal/EURUSD")

        assert response.status_code == 400
        data = response.json()
        assert "Not connected to Chrome session" in data["detail"]

    def test_full_phase3_workflow_simulation(self, client, mock_capabilities):
        """Test a simulated full Phase 3 workflow."""
        # 1. Check capabilities status
        response = client.get("/api/capabilities/status")
        assert response.status_code == 200

        # 2. Generate signal
        signal_response = client.get("/trade/signal/EURUSD")
        assert signal_response.status_code == 200
        signal_data = signal_response.json()
        assert signal_data["data_source"] == "real_time_data"

        # 3. Start automated trading
        trading_response = client.post("/auto-trading/start?strategy_id=quantum_flux_1min&assets=EURUSD")
        assert trading_response.status_code == 200
        trading_data = trading_response.json()
        assert trading_data["strategy_id"] == "quantum_flux_1min"

        # 4. Check trading status
        status_response = client.get("/auto-trading/status")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["is_running"] is True

        # 5. List strategies
        strategies_response = client.get("/strategies")
        assert strategies_response.status_code == 200
        strategies_data = strategies_response.json()
        assert strategies_data["count"] >= 1

        # 6. Stop trading
        stop_response = client.post("/auto-trading/stop")
        assert stop_response.status_code == 200
        stop_data = stop_response.json()
        assert stop_data["message"] == "Automated trading stopped"

        print("✅ Full Phase 3 workflow test completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])