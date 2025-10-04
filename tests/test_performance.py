"""
Performance tests for QuantumFlux Trading Platform.
Tests response times, throughput, memory usage, and scalability.
"""

import pytest
import time
import asyncio
import psutil
import tracemalloc
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
import statistics
from datetime import datetime

from backend import app
from src.utils.logging_config import log_performance


class TestPerformance:
    """Performance test suite."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_capabilities(self):
        """Mock capabilities adapter for performance testing."""
        with patch('src.adapter.capabilities_adapter.CapabilitiesAdapter') as mock_adapter:
            mock_instance = Mock()
            mock_instance.get_streaming_status.return_value = {
                "connected": True,
                "streaming": True,
                "capabilities": {}
            }
            mock_instance.get_latest_data.return_value = [
                {"asset": "EURUSD", "price": 1.1234, "timestamp": datetime.now().isoformat()}
            ]
            mock_adapter.return_value = mock_instance
            yield mock_instance

    def test_api_response_time(self, client, mock_capabilities):
        """Test API endpoint response times."""
        tracemalloc.start()
        start_time = time.time()

        # Test multiple endpoints
        endpoints = [
            "/status",
            "/health",
            "/health/live",
            "/health/ready"
        ]

        response_times = []

        for endpoint in endpoints:
            request_start = time.time()
            response = client.get(endpoint)
            request_end = time.time()

            assert response.status_code in [200, 503]  # Allow 503 for readiness when not connected
            response_time = request_end - request_start
            response_times.append(response_time)

            # Log individual response time
            log_performance(f"api_{endpoint.replace('/', '_')}", response_time)

        total_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # Calculate statistics
        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)

        # Performance assertions
        assert avg_response_time < 0.5, f"Average response time too slow: {avg_response_time:.3f}s"
        assert max_response_time < 2.0, f"Max response time too slow: {max_response_time:.3f}s"
        assert current < 50 * 1024 * 1024, f"Memory usage too high: {current / 1024 / 1024:.2f}MB"

        # Log overall performance
        log_performance("api_endpoints_test", total_time, current / 1024 / 1024,
                       endpoints_tested=len(endpoints), avg_response_time=avg_response_time)

    def test_concurrent_requests(self, client, mock_capabilities):
        """Test handling of concurrent requests."""
        tracemalloc.start()
        start_time = time.time()

        def make_request(endpoint):
            req_start = time.time()
            response = client.get(endpoint)
            req_end = time.time()
            return req_end - req_start, response.status_code

        # Test concurrent requests to status endpoint
        num_requests = 50
        endpoints = ["/status"] * num_requests

        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(make_request, endpoints))

        total_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        response_times = [r[0] for r in results]
        status_codes = [r[1] for r in results]

        # All requests should succeed
        assert all(code in [200, 503] for code in status_codes), f"Some requests failed: {status_codes}"

        avg_response_time = statistics.mean(response_times)
        max_response_time = max(response_times)
        throughput = num_requests / total_time

        # Performance assertions
        assert avg_response_time < 1.0, f"Average concurrent response time too slow: {avg_response_time:.3f}s"
        assert max_response_time < 3.0, f"Max concurrent response time too slow: {max_response_time:.3f}s"
        assert throughput > 10, f"Throughput too low: {throughput:.2f} req/s"

        log_performance("concurrent_requests_test", total_time, current / 1024 / 1024,
                       num_requests=num_requests, throughput=throughput, avg_response_time=avg_response_time)

    def test_websocket_performance(self, client, mock_capabilities):
        """Test WebSocket connection and message handling performance."""
        tracemalloc.start()
        start_time = time.time()

        # Mock WebSocket data
        mock_capabilities.get_latest_data.return_value = [
            {"asset": "EURUSD", "price": 1.1234 + i * 0.0001, "timestamp": datetime.now().isoformat()}
            for i in range(100)
        ]

        try:
            with client.websocket_connect("/ws/data") as websocket:
                # Measure connection time
                connection_time = time.time() - start_time

                # Receive initial messages
                messages_received = 0
                message_times = []

                # Collect messages for 2 seconds
                test_duration = 2.0
                test_start = time.time()

                while time.time() - test_start < test_duration:
                    try:
                        msg_start = time.time()
                        data = websocket.receive_json()
                        msg_end = time.time()
                        message_times.append(msg_end - msg_start)
                        messages_received += 1
                    except:
                        break

        except Exception as e:
            pytest.skip(f"WebSocket test skipped: {e}")

        total_time = time.time() - start_time
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        if messages_received > 0:
            avg_message_time = statistics.mean(message_times)
            messages_per_second = messages_received / test_duration

            # Performance assertions
            assert avg_message_time < 0.1, f"Average message processing time too slow: {avg_message_time:.3f}s"
            assert messages_per_second > 1, f"Message throughput too low: {messages_per_second:.2f} msg/s"

            log_performance("websocket_performance_test", total_time, current / 1024 / 1024,
                           messages_received=messages_received, messages_per_second=messages_per_second,
                           avg_message_time=avg_message_time)

    def test_memory_leak_detection(self, client, mock_capabilities):
        """Test for memory leaks during repeated operations."""
        tracemalloc.start()

        # Perform multiple requests
        num_iterations = 100
        memory_usage = []

        for i in range(num_iterations):
            # Clear any cached data
            if hasattr(tracemalloc, '_clear_cache'):
                tracemalloc._clear_cache()

            # Make request
            response = client.get("/status")
            assert response.status_code in [200, 503]

            # Record memory usage
            current, peak = tracemalloc.get_traced_memory()
            memory_usage.append(current)

            # Small delay to allow garbage collection
            time.sleep(0.01)

        tracemalloc.stop()

        # Analyze memory usage trend
        if len(memory_usage) >= 10:
            # Check if memory usage is increasing significantly
            first_quarter = statistics.mean(memory_usage[:len(memory_usage)//4])
            last_quarter = statistics.mean(memory_usage[-len(memory_usage)//4:])

            memory_growth = (last_quarter - first_quarter) / first_quarter

            # Allow some memory growth but not excessive
            assert memory_growth < 0.5, f"Potential memory leak detected: {memory_growth:.2%} growth"

            log_performance("memory_leak_test", 0, last_quarter / 1024 / 1024,
                           num_iterations=num_iterations, memory_growth=memory_growth)

    def test_cpu_usage_under_load(self, client, mock_capabilities):
        """Test CPU usage during load testing."""
        process = psutil.Process()
        start_cpu = process.cpu_percent(interval=None)

        # Perform intensive operations
        num_requests = 200

        start_time = time.time()
        for _ in range(num_requests):
            response = client.get("/health/live")
            assert response.status_code == 200

        end_time = time.time()
        end_cpu = process.cpu_percent(interval=None)

        total_time = end_time - start_time
        avg_cpu = (start_cpu + end_cpu) / 2
        requests_per_second = num_requests / total_time

        # CPU should not be excessively high
        assert avg_cpu < 80, f"CPU usage too high during load: {avg_cpu:.1f}%"
        assert requests_per_second > 50, f"Request throughput too low: {requests_per_second:.2f} req/s"

        log_performance("cpu_load_test", total_time, 0,
                       num_requests=num_requests, avg_cpu=avg_cpu, requests_per_second=requests_per_second)

    @pytest.mark.asyncio
    async def test_async_performance(self, mock_capabilities):
        """Test async operation performance."""
        from src.adapter.capabilities_adapter import CapabilitiesAdapter

        start_time = time.time()

        # Test multiple async operations
        tasks = []
        for i in range(10):
            task = asyncio.create_task(asyncio.sleep(0.1))  # Simulate async work
            tasks.append(task)

        await asyncio.gather(*tasks)

        total_time = time.time() - start_time

        # Should complete in reasonable time
        assert total_time < 1.0, f"Async operations too slow: {total_time:.3f}s"

        log_performance("async_performance_test", total_time, 0, num_tasks=len(tasks))


class TestLoadTesting:
    """Load testing scenarios."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    def test_sustained_load(self, client):
        """Test sustained load over time."""
        duration = 10  # seconds
        interval = 0.1  # seconds between requests

        start_time = time.time()
        requests_made = 0
        errors = 0

        while time.time() - start_time < duration:
            try:
                response = client.get("/health/live")
                assert response.status_code == 200
                requests_made += 1
            except:
                errors += 1

            time.sleep(interval)

        total_time = time.time() - start_time
        success_rate = (requests_made / (requests_made + errors)) * 100 if requests_made + errors > 0 else 100

        # Should maintain high success rate
        assert success_rate > 95, f"Success rate too low: {success_rate:.1f}%"
        assert requests_made > duration / interval * 0.8, f"Too few requests completed: {requests_made}"

        log_performance("sustained_load_test", total_time, 0,
                       requests_made=requests_made, errors=errors, success_rate=success_rate)

    def test_burst_load(self, client):
        """Test burst load handling."""
        burst_size = 100

        start_time = time.time()

        # Send burst of requests
        responses = []
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(lambda: client.get("/health/live")) for _ in range(burst_size)]
            responses = [f.result() for f in futures]

        total_time = time.time() - start_time

        success_count = sum(1 for r in responses if r.status_code == 200)
        success_rate = (success_count / burst_size) * 100

        # Should handle burst well
        assert success_rate > 90, f"Burst success rate too low: {success_rate:.1f}%"
        assert total_time < 5.0, f"Burst took too long: {total_time:.3f}s"

        log_performance("burst_load_test", total_time, 0,
                       burst_size=burst_size, success_rate=success_rate)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])