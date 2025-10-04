"""Comprehensive tests for CapabilitiesAdapter integration and new backend endpoints.

This test suite covers:
1. CapabilitiesAdapter functionality
2. New capabilities endpoints (/api/capabilities/*)
3. Realtime proxy endpoints (/api/realtime/*)
4. Optional operations endpoints (/api/operations/*)
5. Rate limiting for new endpoints
6. Error handling and edge cases
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, Any

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import app
from src.adapter.capabilities_adapter import CapabilitiesAdapter


class TestCapabilitiesAdapter:
    """Test suite for CapabilitiesAdapter functionality."""
    
    @pytest.fixture
    def mock_adapter(self):
        """Create a mock CapabilitiesAdapter for testing."""
        adapter = Mock(spec=CapabilitiesAdapter)
        adapter.is_connected = True
        adapter.is_streaming = False
        adapter.current_session_info = {
            "port": 9222,
            "user_data_dir": "/tmp/chrome",
            "session_id": "test_session"
        }
        
        # Mock methods
        adapter.attach_to_existing_session.return_value = True
        adapter.disconnect.return_value = True
        adapter.get_connection_status.return_value = {
            "connected": True,
            "streaming": False,
            "session_info": adapter.current_session_info
        }
        adapter.get_latest_candles.return_value = [
            {
                "timestamp": 1704067200,
                "open": 1.0,
                "high": 1.1,
                "low": 0.9,
                "close": 1.05,
                "volume": 1000,
                "asset": "EURUSD"
            }
        ]
        adapter.get_latest_data.return_value = {
            "assets": ["EURUSD", "GBPUSD"],
            "timestamp": datetime.now().isoformat(),
            "data_count": 2
        }
        adapter.start_streaming.return_value = {"status": "started", "streaming": True}
        adapter.stop_streaming.return_value = {"status": "stopped", "streaming": False}
        
        # Mock optional operations
        adapter.scan_profile.return_value = {
            "account_type": "demo",
            "balance": 10000.0,
            "currency": "USD"
        }
        adapter.scan_favorites.return_value = {
            "eligible": ["EURUSD", "GBPUSD"],
            "selected": "EURUSD"
        }
        adapter.execute_trade_click.return_value = {
            "success": True,
            "trade_id": "trade_123",
            "direction": "call"
        }
        adapter.scan_session.return_value = {
            "capabilities": ["profile_scan", "favorite_select", "trade_click"],
            "status": "active"
        }
        
        return adapter
    
    def test_adapter_initialization(self):
        """Test CapabilitiesAdapter initialization."""
        with patch('src.adapter.capabilities_adapter.RealtimeDataStreaming'), \
             patch('src.adapter.capabilities_adapter.SessionScan'), \
             patch('src.adapter.capabilities_adapter.ProfileScan'), \
             patch('src.adapter.capabilities_adapter.FavoriteSelect'), \
             patch('src.adapter.capabilities_adapter.TradeClick'):
            
            adapter = CapabilitiesAdapter()
            assert adapter is not None
            assert not adapter.is_connected
            assert not adapter.is_streaming
            assert adapter.current_session_info is None
    
    def test_adapter_session_attach(self, mock_adapter):
        """Test session attachment functionality."""
        result = mock_adapter.attach_to_existing_session(port=9222)
        assert result is True
        mock_adapter.attach_to_existing_session.assert_called_once_with(port=9222)
    
    def test_adapter_data_retrieval(self, mock_adapter):
        """Test data retrieval methods."""
        # Test candles
        candles = mock_adapter.get_latest_candles()
        assert len(candles) > 0
        assert "timestamp" in candles[0]
        assert "open" in candles[0]
        
        # Test latest data
        data = mock_adapter.get_latest_data()
        assert "assets" in data
        assert "timestamp" in data
    
    def test_adapter_streaming_control(self, mock_adapter):
        """Test streaming start/stop functionality."""
        # Start streaming
        start_result = mock_adapter.start_streaming()
        assert start_result["status"] == "started"
        
        # Stop streaming
        stop_result = mock_adapter.stop_streaming()
        assert stop_result["status"] == "stopped"


class TestCapabilitiesEndpoints:
    """Test suite for /api/capabilities/* endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_capabilities_adapter(self):
        """Mock the capabilities adapter in backend."""
        mock_adapter = Mock()
        mock_adapter.is_connected = True
        mock_adapter.get_streaming_status.return_value = {
            "connected": True,
            "streaming": False,
            "session_info": {"port": 9222}
        }
        mock_adapter.attach_to_existing_session.return_value = True
        mock_adapter.start_streaming.return_value = {"status": "started"}
        mock_adapter.stop_streaming.return_value = {"status": "stopped"}
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            yield mock_adapter
    
    def test_capabilities_status_endpoint(self, client, mock_capabilities_adapter):
        """Test GET /api/capabilities/status endpoint."""
        response = client.get("/api/capabilities/status")
        assert response.status_code == 200
        data = response.json()
        assert "connected" in data
        assert "streaming" in data
    
    def test_capabilities_status_not_available(self, client):
        """Test status endpoint when adapter is not available."""
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = None
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/capabilities/status")
            assert response.status_code == 200
            data = response.json()
            assert "success" in data
            assert data["success"] is False
    
    def test_capabilities_attach_endpoint(self, client, mock_capabilities_adapter):
        """Test POST /api/capabilities/attach endpoint."""
        payload = {"port": 9222, "user_data_dir": "/tmp/chrome"}
        response = client.post("/api/capabilities/attach", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        mock_capabilities_adapter.attach_to_existing_session.assert_called_once()
    
    def test_capabilities_attach_invalid_port(self, client, mock_capabilities_adapter):
        """Test attach endpoint with invalid port."""
        payload = {"port": "invalid"}
        response = client.post("/api/capabilities/attach", json=payload)
        assert response.status_code == 422  # Validation error
    
    def test_capabilities_streaming_start(self, client, mock_capabilities_adapter):
        """Test POST /api/capabilities/streaming endpoint to start streaming."""
        payload = {"action": "start"}
        response = client.post("/api/capabilities/streaming", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "started"
    
    def test_capabilities_streaming_stop(self, client, mock_capabilities_adapter):
        """Test POST /api/capabilities/streaming endpoint to stop streaming."""
        payload = {"action": "stop"}
        response = client.post("/api/capabilities/streaming", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "stopped"
    
    def test_capabilities_streaming_invalid_action(self, client, mock_capabilities_adapter):
        """Test streaming endpoint with invalid action."""
        payload = {"action": "invalid"}
        response = client.post("/api/capabilities/streaming", json=payload)
        assert response.status_code == 400


class TestRealtimeProxyEndpoints:
    """Test suite for /api/realtime/* endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_capabilities_adapter(self):
        """Mock the capabilities adapter in backend."""
        mock_adapter = Mock()
        mock_adapter.is_connected = True
        mock_adapter.get_streaming_status.return_value = {
            "is_streaming": True,
            "connected": True
        }
        mock_adapter.get_latest_data.return_value = {
            "assets": ["EURUSD", "GBPUSD"],
            "timestamp": datetime.now().isoformat(),
            "data": [
                {"asset": "EURUSD", "price": 1.1234, "timestamp": "2024-01-01T00:00:00"},
                {"asset": "GBPUSD", "price": 1.2345, "timestamp": "2024-01-01T00:00:00"}
            ]
        }
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            yield mock_adapter
    
    def test_realtime_data_endpoint(self, client, mock_capabilities_adapter):
        """Test GET /api/realtime/data endpoint."""
        response = client.get("/api/realtime/data")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
        assert "timestamp" in data
    
    def test_realtime_data_with_filter(self, client, mock_capabilities_adapter):
        """Test realtime data endpoint with asset filter."""
        response = client.get("/api/realtime/data?assets=EURUSD,GBPUSD")
        assert response.status_code == 200
        data = response.json()
        assert "assets" in data
    
    def test_realtime_data_adapter_not_available(self, client):
        """Test realtime data endpoint when adapter is not available."""
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = None
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/realtime/data")
            assert response.status_code == 503
    
    def test_realtime_data_not_connected(self, client):
        """Test realtime data endpoint when adapter is not connected."""
        mock_adapter = Mock()
        mock_adapter.get_streaming_status.return_value = {"is_streaming": False}
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/realtime/data")
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Streaming not active"
    
    def test_realtime_stream_endpoint(self, client, mock_capabilities_adapter):
        """Test GET /api/realtime/stream endpoint."""
        response = client.get("/api/realtime/stream")
        assert response.status_code == 200
        # Note: This is a streaming endpoint, so we just check it starts correctly


class TestOptionalOperationsEndpoints:
    """Test suite for /api/operations/* endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_capabilities_adapter(self):
        """Mock the capabilities adapter in backend."""
        mock_adapter = Mock()
        mock_adapter.is_connected = True
        mock_adapter.scan_profile.return_value = {
            "account_type": "demo",
            "balance": 10000.0,
            "currency": "USD"
        }
        mock_adapter.scan_favorites.return_value = {
            "eligible": ["EURUSD", "GBPUSD"],
            "selected": "EURUSD"
        }
        mock_adapter.execute_trade_click.return_value = {
            "success": True,
            "trade_id": "trade_123",
            "direction": "call"
        }
        mock_adapter.scan_session.return_value = {
            "capabilities": ["profile_scan", "favorite_select", "trade_click"],
            "status": "active"
        }
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            yield mock_adapter
    
    def test_operations_profile_endpoint(self, client, mock_capabilities_adapter):
        """Test GET /api/operations/profile endpoint."""
        response = client.get("/api/operations/profile")
        assert response.status_code == 200
        data = response.json()
        assert "account_type" in data
        assert "balance" in data
    
    def test_operations_favorites_endpoint(self, client, mock_capabilities_adapter):
        """Test GET /api/operations/favorites endpoint."""
        response = client.get("/api/operations/favorites?min_pct=92")
        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
    
    def test_operations_favorites_with_select(self, client, mock_capabilities_adapter):
        """Test favorites endpoint with select parameter."""
        response = client.get("/api/operations/favorites?min_pct=95&select=first")
        assert response.status_code == 200
        data = response.json()
        assert "eligible" in data
    
    def test_operations_trade_endpoint(self, client, mock_capabilities_adapter):
        """Test POST /api/operations/trade endpoint."""
        payload = {"direction": "call", "amount": "100", "duration": "1m"}
        response = client.post("/api/operations/trade", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "trade_id" in data
    
    def test_operations_trade_invalid_direction(self, client, mock_capabilities_adapter):
        """Test trade endpoint with invalid direction."""
        payload = {"direction": "invalid"}
        response = client.post("/api/operations/trade", json=payload)
        assert response.status_code == 400
    
    def test_operations_session_endpoint(self, client, mock_capabilities_adapter):
        """Test GET /api/operations/session endpoint."""
        response = client.get("/api/operations/session")
        assert response.status_code == 200
        data = response.json()
        assert "capabilities" in data
        assert "status" in data
    
    def test_operations_adapter_not_available(self, client):
        """Test operations endpoints when adapter is not available."""
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = None
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/operations/profile")
            assert response.status_code == 503
            
            response = client.get("/api/operations/favorites")
            assert response.status_code == 503
            
            response = client.post("/api/operations/trade", json={"direction": "call"})
            assert response.status_code == 503
            
            response = client.get("/api/operations/session")
            assert response.status_code == 503
    
    def test_operations_not_connected(self, client):
        """Test operations endpoints when adapter is not connected."""
        mock_adapter = Mock()
        mock_adapter.is_connected = False
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/operations/profile")
            assert response.status_code == 503
            
            response = client.get("/api/operations/favorites")
            assert response.status_code == 503
            
            response = client.post("/api/operations/trade", json={"direction": "call"})
            assert response.status_code == 503
            
            response = client.get("/api/operations/session")
            assert response.status_code == 503


class TestRateLimitingNewEndpoints:
    """Test rate limiting for new capabilities endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_capabilities_adapter(self):
        """Mock the capabilities adapter in backend."""
        mock_adapter = Mock()
        mock_adapter.is_connected = True
        mock_adapter.get_streaming_status.return_value = {"connected": True}
        mock_adapter.get_latest_data.return_value = {"data": []}
        mock_adapter.scan_profile.return_value = {"balance": 10000}
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            yield mock_adapter
    
    def test_capabilities_rate_limiting(self, client, mock_capabilities_adapter):
        """Test rate limiting on capabilities endpoints."""
        # Make multiple requests to test rate limiting
        responses = []
        for _ in range(5):
            response = client.get("/api/capabilities/status")
            responses.append(response)
        
        # All should succeed within rate limit
        for response in responses:
            assert response.status_code == 200
    
    def test_realtime_rate_limiting(self, client, mock_capabilities_adapter):
        """Test rate limiting on realtime endpoints."""
        # Make multiple requests to test rate limiting
        responses = []
        for _ in range(5):
            response = client.get("/api/realtime/data")
            responses.append(response)
        
        # All should succeed within rate limit
        for response in responses:
            assert response.status_code == 200
    
    def test_operations_rate_limiting(self, client, mock_capabilities_adapter):
        """Test rate limiting on operations endpoints."""
        # Test profile endpoint rate limiting
        responses = []
        for _ in range(3):
            response = client.get("/api/operations/profile")
            responses.append(response)
        
        # All should succeed within rate limit
        for response in responses:
            assert response.status_code == 200


class TestErrorHandlingNewEndpoints:
    """Test error handling for new capabilities endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_capabilities_adapter_exception(self, client):
        """Test handling of adapter exceptions."""
        mock_adapter = Mock()
        mock_adapter.get_streaming_status.side_effect = Exception("Test error")
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/capabilities/status")
            assert response.status_code == 500
            data = response.json()
            assert "error" in data
    
    def test_realtime_data_exception(self, client):
        """Test handling of realtime data exceptions."""
        mock_adapter = Mock()
        mock_adapter.get_streaming_status.side_effect = Exception("Data error")
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/realtime/data")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
    
    def test_operations_exception(self, client):
        """Test handling of operations exceptions."""
        mock_adapter = Mock()
        mock_adapter.is_connected = True
        mock_adapter.scan_profile.side_effect = Exception("Profile error")
        
        mock_app_state = Mock()
        mock_app_state.capabilities_adapter = mock_adapter
        
        async def async_get_app_state():
            return mock_app_state
        
        with patch('src.core.app_state.get_app_state', side_effect=async_get_app_state):
            response = client.get("/api/operations/profile")
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])