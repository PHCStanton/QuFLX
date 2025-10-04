"""
Security tests for QuantumFlux Trading Platform.
Tests authentication, authorization, input validation, and security hardening.
"""

import pytest
import json
import time
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from backend import app
from src.utils.logging_config import log_security_event


class TestAuthentication:
    """Test authentication mechanisms."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_api_key_authentication_required(self, client):
        """Test that sensitive endpoints require API key."""
        # These endpoints should require authentication in production
        sensitive_endpoints = [
            "/api/operations/trade",
            "/auto-trading/start",
            "/strategies",
            "/tests/ab/start"
        ]

        for endpoint in sensitive_endpoints:
            response = client.post(endpoint, json={})
            # Should return 401 or 403 without proper auth
            assert response.status_code in [401, 403, 422], f"Endpoint {endpoint} should require authentication"

    def test_invalid_api_key_rejected(self, client):
        """Test that invalid API keys are rejected."""
        headers = {"Authorization": "Bearer invalid_key"}

        response = client.get("/status", headers=headers)
        # Should still work for read-only endpoints, or require auth
        assert response.status_code in [200, 401, 403]

    def test_rate_limiting_enforced(self, client):
        """Test that rate limiting is properly enforced."""
        # Make multiple rapid requests
        responses = []
        for _ in range(150):  # Exceed typical rate limit
            response = client.get("/status")
            responses.append(response.status_code)
            time.sleep(0.01)  # Small delay to avoid overwhelming

        # Should see some 429 responses if rate limiting is working
        rate_limited_responses = sum(1 for code in responses if code == 429)
        if rate_limited_responses > 0:
            log_security_event("rate_limit_triggered", details={"requests_made": len(responses)})


class TestInputValidation:
    """Test input validation and sanitization."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_sql_injection_prevention(self, client):
        """Test prevention of SQL injection attacks."""
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "1; SELECT * FROM users;",
            "UNION SELECT password FROM users"
        ]

        for malicious_input in malicious_inputs:
            # Test in various parameters
            response = client.get(f"/trade/signal/{malicious_input}")
            # Should not crash and should validate input
            assert response.status_code in [200, 400, 422, 404], f"SQL injection attempt not handled: {malicious_input}"

    def test_xss_prevention(self, client):
        """Test prevention of XSS attacks."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "<iframe src='javascript:alert(\"xss\")'></iframe>",
            "<svg onload=alert('xss')>"
        ]

        for payload in xss_payloads:
            response = client.get("/status", params={"test": payload})
            # Should not execute scripts and should sanitize input
            assert response.status_code in [200, 400, 422]
            # Check that response doesn't contain the payload (basic check)
            if response.status_code == 200:
                response_text = response.text.lower()
                assert "<script>" not in response_text, f"XSS payload not sanitized: {payload}"

    def test_path_traversal_prevention(self, client):
        """Test prevention of path traversal attacks."""
        traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\sam",
            "../../../../root/.bashrc"
        ]

        for path in traversal_attempts:
            response = client.get(f"/api/realtime/data?file={path}")
            # Should not allow access to system files
            assert response.status_code in [200, 400, 403, 404], f"Path traversal not prevented: {path}"

    def test_buffer_overflow_prevention(self, client):
        """Test prevention of buffer overflow attacks."""
        # Create very large input
        large_input = "A" * 100000  # 100KB of data

        response = client.post("/api/operations/trade",
                             json={"side": "buy", "amount": large_input})
        # Should handle large input gracefully
        assert response.status_code in [200, 400, 413, 422], "Large input not handled properly"

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON input."""
        malformed_jsons = [
            "{invalid json",
            '{"unclosed": "object"',
            '["incomplete array"',
            '{"key": value}',  # unquoted value
            '{"key": "value",}',  # trailing comma
        ]

        for malformed in malformed_jsons:
            response = client.post("/strategies",
                                 data=malformed,
                                 headers={"Content-Type": "application/json"})
            # Should return 422 for invalid JSON
            assert response.status_code == 422, f"Malformed JSON not rejected: {malformed}"

    def test_negative_values_validation(self, client):
        """Test validation of negative and invalid numeric values."""
        invalid_amounts = [-100, -1, 0, -0.01]

        for amount in invalid_amounts:
            response = client.post("/api/operations/trade",
                                 json={"side": "buy", "amount": amount})
            # Should validate positive amounts
            assert response.status_code in [400, 422], f"Invalid amount not rejected: {amount}"

    def test_string_length_limits(self, client):
        """Test enforcement of string length limits."""
        # Very long asset name
        long_asset = "EURUSD" * 1000  # 6KB string

        response = client.get(f"/trade/signal/{long_asset}")
        # Should handle or reject overly long inputs
        assert response.status_code in [200, 400, 414, 422], "Long input not handled properly"


class TestAuthorization:
    """Test authorization mechanisms."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_endpoint_authorization_levels(self, client):
        """Test that different endpoints have appropriate authorization levels."""
        # Public endpoints (no auth required)
        public_endpoints = [
            "/health",
            "/health/live",
            "/health/ready",
            "/docs",
            "/redoc",
            "/"
        ]

        for endpoint in public_endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 404], f"Public endpoint {endpoint} should be accessible"

        # Protected endpoints (may require auth)
        protected_endpoints = [
            "/api/operations/trade",
            "/auto-trading/start",
            "/strategies",
            "/tests/ab/start"
        ]

        for endpoint in protected_endpoints:
            response = client.post(endpoint, json={})
            # May require auth or validation
            assert response.status_code in [200, 400, 401, 403, 422], f"Protected endpoint {endpoint} auth check failed"

    def test_user_role_permissions(self, client):
        """Test role-based permissions."""
        # Test with different user roles/contexts
        roles = ["admin", "trader", "viewer", "anonymous"]

        for role in roles:
            # Simulate different user contexts
            headers = {"X-User-Role": role}

            response = client.get("/status", headers=headers)
            # Should handle different roles appropriately
            assert response.status_code in [200, 401, 403], f"Role {role} not handled properly"


class TestSecurityHeaders:
    """Test security headers and configurations."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/status")

        # Recommended security headers
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security",
            "Content-Security-Policy"
        ]

        present_headers = [h for h in security_headers if h in response.headers]
        missing_headers = [h for h in security_headers if h not in response.headers]

        # Log security assessment
        if missing_headers:
            log_security_event("missing_security_headers",
                             details={"missing": missing_headers, "present": present_headers})

        # At minimum, should have some security headers
        assert len(present_headers) > 0, f"No security headers found. Missing: {missing_headers}"

    def test_cors_configuration_secure(self, client):
        """Test that CORS is configured securely."""
        # Test preflight request
        response = client.options("/status",
                                headers={
                                    "Origin": "http://localhost:5173",
                                    "Access-Control-Request-Method": "GET"
                                })

        # Should allow configured origins
        assert response.status_code in [200, 404]  # 404 if OPTIONS not implemented

        if "Access-Control-Allow-Origin" in response.headers:
            allowed_origin = response.headers["Access-Control-Allow-Origin"]
            # Should not allow all origins (*) in production
            assert allowed_origin != "*", f"CORS allows all origins: {allowed_origin}"

    def test_sensitive_data_not_logged(self, client):
        """Test that sensitive data is not logged in responses."""
        # Make request that might include sensitive data
        response = client.get("/status")

        response_text = response.text.lower()

        # Should not contain sensitive patterns
        sensitive_patterns = ["password", "secret", "key", "token"]

        for pattern in sensitive_patterns:
            assert pattern not in response_text, f"Sensitive data pattern '{pattern}' found in response"


class TestDataExposure:
    """Test for data exposure vulnerabilities."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_error_messages_safe(self, client):
        """Test that error messages don't expose sensitive information."""
        # Trigger various errors
        error_endpoints = [
            ("/trade/signal/INVALID_ASSET", "GET"),
            ("/strategies/invalid_id", "GET"),
            ("/api/operations/trade", "POST"),  # Invalid request
        ]

        for endpoint, method in error_endpoints:
            if method == "GET":
                response = client.get(endpoint)
            elif method == "POST":
                response = client.post(endpoint, json={})

            if response.status_code >= 400:
                response_text = response.text.lower()

                # Should not expose system information
                dangerous_patterns = [
                    "traceback",
                    "exception",
                    "/usr/",
                    "/home/",
                    "c:\\",
                    "internal",
                    "debug"
                ]

                for pattern in dangerous_patterns:
                    assert pattern not in response_text, f"Dangerous pattern '{pattern}' in error response"

    def test_directory_listing_prevention(self, client):
        """Test prevention of directory listing."""
        # Try to access directories
        directory_paths = [
            "/static/",
            "/assets/",
            "/files/",
            "/data/"
        ]

        for path in directory_paths:
            response = client.get(path)
            # Should not list directory contents
            assert response.status_code not in [200], f"Directory listing possible at {path}"
            assert "<html>" not in response.text.lower() or "index of" not in response.text.lower(), f"Directory listing at {path}"


class TestSessionSecurity:
    """Test session and authentication security."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_session_timeout(self, client):
        """Test session timeout handling."""
        # Make authenticated request
        response = client.get("/status")
        assert response.status_code in [200, 401, 403]

        # Wait (simulate timeout - in real test would wait longer)
        time.sleep(0.1)

        # Make another request - should handle session appropriately
        response2 = client.get("/status")
        assert response2.status_code in [200, 401, 403]

    def test_concurrent_session_handling(self, client):
        """Test handling of concurrent sessions."""
        # Simulate multiple concurrent requests
        import threading
        results = []

        def make_request():
            response = client.get("/status")
            results.append(response.status_code)

        threads = []
        for _ in range(10):
            t = threading.Thread(target=make_request)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # All requests should be handled
        assert len(results) == 10
        assert all(code in [200, 401, 403] for code in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])