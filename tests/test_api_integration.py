"""Integration tests for QuantumFlux Trading Platform API.

This module provides HTTP-based integration testing using requests library
to test the actual running server, complementing the existing unit tests.
"""

import pytest
import requests
import json
import time
from typing import Dict, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds


class TestAPIIntegration:
    """Integration test suite for QuantumFlux Trading Platform API."""
    
    @classmethod
    def setup_class(cls):
        """Setup class method run once before all tests."""
        cls.base_url = BASE_URL
        cls.headers = {"Content-Type": "application/json"}
        
        # Test server connectivity
        try:
            response = requests.get(f"{cls.base_url}/status", timeout=5)
            if response.status_code != 200:
                pytest.skip("Server is not running or not accessible")
        except requests.exceptions.RequestException:
            pytest.skip("Server is not running or not accessible")
    
    def test_01_server_health_check(self):
        """Test basic server connectivity and health."""
        response = requests.get(f"{self.base_url}/status", timeout=TIMEOUT)
        
        assert response.status_code == 200, f"Server health check failed: {response.status_code}"
        
        data = response.json()
        assert "success" in data, "Response missing 'success' field"
        assert "timestamp" in data, "Response missing 'timestamp' field"
        assert "connection_status" in data, "Response missing 'connection_status' field"
        
        print(f"✓ Server is healthy. Status: {data.get('success')}")
    
    def test_02_status_endpoint_structure(self):
        """Test status endpoint response structure and data types."""
        response = requests.get(f"{self.base_url}/status", timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate main structure
        assert isinstance(data["success"], bool)
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["connection_status"], dict)
        
        # Validate connection status structure
        conn_status = data["connection_status"]
        required_fields = ["webdriver_connected", "websocket_connected", "platform_logged_in"]
        
        for field in required_fields:
            assert field in conn_status, f"Missing field: {field}"
            assert isinstance(conn_status[field], bool), f"Field {field} should be boolean"
        
        print(f"✓ Status endpoint structure validated")
        print(f"  - WebDriver: {conn_status.get('webdriver_connected')}")
        print(f"  - WebSocket: {conn_status.get('websocket_connected')}")
        print(f"  - Platform: {conn_status.get('platform_logged_in')}")
    
    def test_03_health_endpoint(self):
        """Test health check endpoint."""
        response = requests.get(f"{self.base_url}/health", timeout=TIMEOUT)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "success" in data
        assert "timestamp" in data
        assert "status" in data
        assert "checks" in data
        
        # Validate health checks
        checks = data["checks"]
        assert "api" in checks
        assert "database" in checks
        assert "webdriver" in checks
        
        print(f"✓ Health endpoint validated. Overall status: {data.get('status')}")
        
        # Print detailed health information
        for check_name, check_data in checks.items():
            if isinstance(check_data, dict) and "status" in check_data:
                print(f"  - {check_name}: {check_data['status']}")
    
    def test_04_candles_endpoint_validation(self):
        """Test candles endpoint parameter validation."""
        # Test with missing parameters
        response = requests.get(f"{self.base_url}/candles/EURUSD", timeout=TIMEOUT)
        
        # Should return some response (may be error due to missing params or platform not connected)
        assert response.status_code in [200, 400, 422, 500]
        
        data = response.json()
        assert "success" in data
        assert "timestamp" in data
        
        print(f"✓ Candles endpoint accessible. Success: {data.get('success')}")
        if not data.get('success'):
            print(f"  - Expected error (platform not connected): {data.get('message', 'No message')}")
    
    def test_05_candles_endpoint_with_params(self):
        """Test candles endpoint with query parameters."""
        params = {
            "timeframe": "M1",
            "count": 10
        }
        
        response = requests.get(
            f"{self.base_url}/candles/EURUSD",
            params=params,
            timeout=TIMEOUT
        )
        
        # Should return response (may be error due to platform not connected)
        assert response.status_code in [200, 400, 500]
        
        data = response.json()
        assert "success" in data
        assert "timestamp" in data
        
        print(f"✓ Candles endpoint with params tested. Success: {data.get('success')}")
    
    def test_06_trade_execute_validation_errors(self):
        """Test trade execution endpoint validation."""
        # Test with empty payload
        response = requests.post(
            f"{self.base_url}/trade/execute",
            headers=self.headers,
            json={},
            timeout=TIMEOUT
        )
        
        assert response.status_code == 422  # Validation error
        data = response.json()
        
        # Should have validation error details
        assert "detail" in data or "validation_errors" in data
        
        print("✓ Trade execution validation working correctly")
    
    def test_07_trade_execute_missing_fields(self):
        """Test trade execution with missing required fields."""
        incomplete_payload = {
            "asset": "EURUSD",
            "direction": "CALL"
            # Missing amount and expiry_time
        }
        
        response = requests.post(
            f"{self.base_url}/trade/execute",
            headers=self.headers,
            json=incomplete_payload,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 422  # Validation error
        print("✓ Missing fields validation working correctly")
    
    def test_08_trade_execute_invalid_direction(self):
        """Test trade execution with invalid direction."""
        invalid_payload = {
            "asset": "EURUSD",
            "direction": "INVALID_DIRECTION",
            "amount": 1.0,
            "expiry_time": 60
        }
        
        response = requests.post(
            f"{self.base_url}/trade/execute",
            headers=self.headers,
            json=invalid_payload,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 422  # Validation error
        print("✓ Invalid direction validation working correctly")
    
    def test_09_trade_execute_valid_request(self):
        """Test trade execution with valid request format."""
        valid_payload = {
            "asset": "EURUSD",
            "direction": "CALL",
            "amount": 1.0,
            "expiry_time": 60
        }
        
        response = requests.post(
            f"{self.base_url}/trade/execute",
            headers=self.headers,
            json=valid_payload,
            timeout=TIMEOUT
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Validate response structure
        assert "success" in data
        assert "timestamp" in data
        assert "message" in data
        assert "trade_result" in data
        
        # Validate trade result structure
        trade_result = data["trade_result"]
        required_fields = ["trade_id", "asset", "direction", "amount", "status"]
        
        for field in required_fields:
            assert field in trade_result, f"Missing field in trade_result: {field}"
        
        print(f"✓ Trade execution endpoint structure validated")
        print(f"  - Success: {data.get('success')}")
        print(f"  - Trade ID: {trade_result.get('trade_id')}")
        print(f"  - Status: {trade_result.get('status')}")
        
        # Expected to fail due to platform not connected
        if not data.get('success'):
            print(f"  - Expected failure: {data.get('message')}")
    
    def test_10_rate_limiting_headers(self):
        """Test that rate limiting headers are present."""
        response = requests.get(f"{self.base_url}/status", timeout=TIMEOUT)
        
        assert response.status_code == 200
        
        # Check for rate limiting headers
        headers = response.headers
        rate_limit_headers = ["x-ratelimit-limit", "x-ratelimit-remaining", "x-ratelimit-reset"]
        
        for header in rate_limit_headers:
            assert header in headers, f"Missing rate limit header: {header}"
        
        print("✓ Rate limiting headers present")
        print(f"  - Limit: {headers.get('x-ratelimit-limit')}")
        print(f"  - Remaining: {headers.get('x-ratelimit-remaining')}")
        print(f"  - Reset: {headers.get('x-ratelimit-reset')}")
    
    def test_11_request_tracing_headers(self):
        """Test that request tracing headers are present."""
        response = requests.get(f"{self.base_url}/status", timeout=TIMEOUT)
        
        assert response.status_code == 200
        assert "x-request-id" in response.headers
        
        request_id = response.headers["x-request-id"]
        
        # Basic UUID format validation
        assert len(request_id) >= 32, "Request ID too short"
        assert "-" in request_id, "Request ID should contain hyphens"
        
        print(f"✓ Request tracing header present: {request_id}")
    
    def test_12_response_time_performance(self):
        """Test API response times are within acceptable limits."""
        endpoints = [
            ("/status", 2.0),  # 2 second limit
            ("/health", 3.0),  # 3 second limit
        ]
        
        for endpoint, time_limit in endpoints:
            start_time = time.time()
            response = requests.get(f"{self.base_url}{endpoint}", timeout=TIMEOUT)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            assert response.status_code == 200
            assert response_time < time_limit, f"{endpoint} too slow: {response_time:.2f}s > {time_limit}s"
            
            print(f"✓ {endpoint} response time: {response_time:.3f}s (limit: {time_limit}s)")
    
    def test_13_error_handling_nonexistent_endpoint(self):
        """Test error handling for nonexistent endpoints."""
        response = requests.get(f"{self.base_url}/nonexistent-endpoint", timeout=TIMEOUT)
        
        assert response.status_code == 404
        print("✓ 404 error handling working correctly")
    
    def test_14_error_handling_invalid_json(self):
        """Test error handling for invalid JSON payloads."""
        response = requests.post(
            f"{self.base_url}/trade/execute",
            headers=self.headers,
            data="{invalid json syntax}",
            timeout=TIMEOUT
        )
        
        assert response.status_code in [400, 422]
        print("✓ Invalid JSON error handling working correctly")
    
    def test_15_cors_and_options_handling(self):
        """Test CORS and OPTIONS request handling."""
        response = requests.options(f"{self.base_url}/status", timeout=TIMEOUT)
        
        # Should handle OPTIONS requests gracefully
        assert response.status_code in [200, 204, 405]
        print(f"✓ OPTIONS request handled: {response.status_code}")


class TestAPILoadTesting:
    """Basic load testing for API endpoints."""
    
    def test_concurrent_status_requests(self):
        """Test handling of multiple concurrent requests."""
        import concurrent.futures
        import threading
        
        def make_request():
            try:
                response = requests.get(f"{BASE_URL}/status", timeout=5)
                return response.status_code == 200
            except:
                return False
        
        # Make 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        success_count = sum(results)
        total_requests = len(results)
        
        # At least 80% should succeed
        success_rate = success_count / total_requests
        assert success_rate >= 0.8, f"Success rate too low: {success_rate:.2%}"
        
        print(f"✓ Concurrent requests test: {success_count}/{total_requests} succeeded ({success_rate:.1%})")


def run_integration_tests():
    """Run integration tests with detailed output."""
    print("\n" + "="*60)
    print("QuantumFlux Trading Platform - API Integration Tests")
    print("="*60)
    
    # Run tests with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "-s",  # Don't capture output
        "--tb=short",  # Short traceback format
        "--color=yes"  # Colored output
    ])
    
    print("\n" + "="*60)
    if exit_code == 0:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed.")
    print("="*60)
    
    return exit_code


if __name__ == "__main__":
    run_integration_tests()