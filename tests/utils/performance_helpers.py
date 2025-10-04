"""Performance Helpers for QuantumFlux Testing.

This module provides performance monitoring and benchmarking utilities:
- Performance metrics collection (response times, memory usage, CPU)
- API endpoint benchmarking
- WebDriver performance monitoring
- Resource usage tracking
- Performance report generation

Migrated from API-test-space for production use.
"""

from __future__ import annotations

import os
import json
import time
import psutil
import threading
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Callable
from contextlib import contextmanager

try:
    import requests
except ImportError:
    requests = None

try:
    from selenium.webdriver.remote.webdriver import WebDriver
except ImportError:
    WebDriver = None


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    response_time_ms: Optional[float]
    page_load_time_ms: Optional[float]
    network_requests: Optional[int]
    javascript_errors: Optional[int]
    dom_elements: Optional[int]
    page_size_kb: Optional[float]


@dataclass
class BenchmarkResult:
    """Benchmark result data structure"""
    test_name: str
    start_time: str
    end_time: str
    duration_seconds: float
    success: bool
    error_message: Optional[str]
    metrics: List[PerformanceMetrics]
    summary_stats: Dict[str, float]
    artifacts_saved: List[str]


class PerformanceMonitor:
    """Performance monitoring utilities"""
    
    def __init__(self, sample_interval: float = 1.0):
        self.sample_interval = sample_interval
        self.monitoring = False
        self.metrics_history: List[PerformanceMetrics] = []
        self.monitor_thread: Optional[threading.Thread] = None
        self.artifacts_dir = self._ensure_artifacts_dir()
    
    def _ensure_artifacts_dir(self) -> str:
        """Ensure artifacts directory exists"""
        artifacts_dir = os.path.join(os.getcwd(), "tests", "test_results", "performance")
        os.makedirs(artifacts_dir, exist_ok=True)
        return artifacts_dir
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect system performance metrics"""
        try:
            # Get current process
            process = psutil.Process()
            
            # CPU and memory metrics
            cpu_percent = process.cpu_percent()
            memory_info = process.memory_info()
            memory_percent = process.memory_percent()
            memory_mb = memory_info.rss / 1024 / 1024  # Convert to MB
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'memory_mb': memory_mb
            }
        except Exception:
            return {
                'cpu_percent': 0.0,
                'memory_percent': 0.0,
                'memory_mb': 0.0
            }
    
    def _collect_browser_metrics(self, driver: WebDriver) -> Dict[str, Any]:
        """Collect browser-specific performance metrics"""
        if not driver:
            return {}
        
        try:
            metrics = {}
            
            # Page load timing
            try:
                timing = driver.execute_script(
                    "return window.performance.timing;"
                )
                if timing:
                    load_time = timing.get('loadEventEnd', 0) - timing.get('navigationStart', 0)
                    metrics['page_load_time_ms'] = load_time
            except Exception:
                pass
            
            # DOM elements count
            try:
                dom_count = driver.execute_script(
                    "return document.getElementsByTagName('*').length;"
                )
                metrics['dom_elements'] = dom_count
            except Exception:
                pass
            
            # JavaScript errors
            try:
                js_errors = driver.execute_script(
                    "return window.jsErrors ? window.jsErrors.length : 0;"
                )
                metrics['javascript_errors'] = js_errors
            except Exception:
                metrics['javascript_errors'] = 0
            
            # Network requests (if available)
            try:
                network_entries = driver.execute_script(
                    "return window.performance.getEntriesByType('navigation').length + window.performance.getEntriesByType('resource').length;"
                )
                metrics['network_requests'] = network_entries
            except Exception:
                pass
            
            # Page size estimation
            try:
                page_size = len(driver.page_source.encode('utf-8')) / 1024  # KB
                metrics['page_size_kb'] = page_size
            except Exception:
                pass
            
            return metrics
            
        except Exception:
            return {}
    
    def _monitoring_loop(self, driver: Optional[WebDriver] = None):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                
                # Collect browser metrics if driver provided
                browser_metrics = self._collect_browser_metrics(driver) if driver else {}
                
                # Create metrics object
                metrics = PerformanceMetrics(
                    timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                    cpu_percent=system_metrics.get('cpu_percent', 0.0),
                    memory_percent=system_metrics.get('memory_percent', 0.0),
                    memory_mb=system_metrics.get('memory_mb', 0.0),
                    response_time_ms=browser_metrics.get('response_time_ms'),
                    page_load_time_ms=browser_metrics.get('page_load_time_ms'),
                    network_requests=browser_metrics.get('network_requests'),
                    javascript_errors=browser_metrics.get('javascript_errors'),
                    dom_elements=browser_metrics.get('dom_elements'),
                    page_size_kb=browser_metrics.get('page_size_kb')
                )
                
                self.metrics_history.append(metrics)
                
                # Limit history size to prevent memory issues
                if len(self.metrics_history) > 1000:
                    self.metrics_history = self.metrics_history[-500:]
                
            except Exception:
                pass  # Continue monitoring even if individual collection fails
            
            time.sleep(self.sample_interval)
    
    def start_monitoring(self, driver: Optional[WebDriver] = None):
        """Start performance monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.metrics_history.clear()
        
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(driver,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> List[PerformanceMetrics]:
        """Stop performance monitoring and return collected metrics"""
        if not self.monitoring:
            return self.metrics_history.copy()
        
        self.monitoring = False
        
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)
        
        return self.metrics_history.copy()
    
    def get_current_metrics(self, driver: Optional[WebDriver] = None) -> PerformanceMetrics:
        """Get current performance metrics snapshot"""
        system_metrics = self._collect_system_metrics()
        browser_metrics = self._collect_browser_metrics(driver) if driver else {}
        
        return PerformanceMetrics(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            cpu_percent=system_metrics.get('cpu_percent', 0.0),
            memory_percent=system_metrics.get('memory_percent', 0.0),
            memory_mb=system_metrics.get('memory_mb', 0.0),
            response_time_ms=browser_metrics.get('response_time_ms'),
            page_load_time_ms=browser_metrics.get('page_load_time_ms'),
            network_requests=browser_metrics.get('network_requests'),
            javascript_errors=browser_metrics.get('javascript_errors'),
            dom_elements=browser_metrics.get('dom_elements'),
            page_size_kb=browser_metrics.get('page_size_kb')
        )
    
    def calculate_summary_stats(self, metrics: List[PerformanceMetrics]) -> Dict[str, float]:
        """Calculate summary statistics from metrics"""
        if not metrics:
            return {}
        
        # Extract numeric values
        cpu_values = [m.cpu_percent for m in metrics]
        memory_values = [m.memory_mb for m in metrics]
        memory_percent_values = [m.memory_percent for m in metrics]
        
        # Page load times (filter out None values)
        page_load_values = [m.page_load_time_ms for m in metrics if m.page_load_time_ms is not None]
        
        stats = {
            'cpu_avg': sum(cpu_values) / len(cpu_values) if cpu_values else 0.0,
            'cpu_max': max(cpu_values) if cpu_values else 0.0,
            'cpu_min': min(cpu_values) if cpu_values else 0.0,
            'memory_avg_mb': sum(memory_values) / len(memory_values) if memory_values else 0.0,
            'memory_max_mb': max(memory_values) if memory_values else 0.0,
            'memory_min_mb': min(memory_values) if memory_values else 0.0,
            'memory_percent_avg': sum(memory_percent_values) / len(memory_percent_values) if memory_percent_values else 0.0,
            'memory_percent_max': max(memory_percent_values) if memory_percent_values else 0.0,
            'sample_count': len(metrics)
        }
        
        if page_load_values:
            stats.update({
                'page_load_avg_ms': sum(page_load_values) / len(page_load_values),
                'page_load_max_ms': max(page_load_values),
                'page_load_min_ms': min(page_load_values)
            })
        
        return stats
    
    def save_metrics_report(self, 
                          metrics: List[PerformanceMetrics], 
                          test_name: str = "performance_test") -> str:
        """Save performance metrics report"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_metrics_{timestamp}.json"
            filepath = os.path.join(self.artifacts_dir, filename)
            
            # Calculate summary stats
            summary_stats = self.calculate_summary_stats(metrics)
            
            report_data = {
                'test_name': test_name,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                'summary_stats': summary_stats,
                'metrics_count': len(metrics),
                'metrics': [asdict(m) for m in metrics]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, default=str)
            
            return filepath
            
        except Exception as e:
            print(f"Failed to save metrics report: {e}")
            return ""


class APIBenchmark:
    """API endpoint benchmarking utilities"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session() if requests else None
        self.artifacts_dir = self._ensure_artifacts_dir()
    
    def _ensure_artifacts_dir(self) -> str:
        """Ensure artifacts directory exists"""
        artifacts_dir = os.path.join(os.getcwd(), "tests", "test_results", "api_benchmark")
        os.makedirs(artifacts_dir, exist_ok=True)
        return artifacts_dir
    
    def benchmark_endpoint(self, 
                         endpoint: str, 
                         method: str = 'GET',
                         data: Optional[Dict] = None,
                         headers: Optional[Dict] = None,
                         iterations: int = 10) -> Dict[str, Any]:
        """Benchmark a single API endpoint"""
        if not self.session:
            return {'error': 'requests library not available'}
        
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        response_times = []
        status_codes = []
        errors = []
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                request_start = time.time()
                
                if method.upper() == 'GET':
                    response = self.session.get(url, headers=headers, timeout=self.timeout)
                elif method.upper() == 'POST':
                    response = self.session.post(url, json=data, headers=headers, timeout=self.timeout)
                elif method.upper() == 'PUT':
                    response = self.session.put(url, json=data, headers=headers, timeout=self.timeout)
                elif method.upper() == 'DELETE':
                    response = self.session.delete(url, headers=headers, timeout=self.timeout)
                else:
                    errors.append(f"Unsupported method: {method}")
                    continue
                
                request_time = (time.time() - request_start) * 1000  # Convert to ms
                response_times.append(request_time)
                status_codes.append(response.status_code)
                
            except Exception as e:
                errors.append(str(e))
        
        total_time = time.time() - start_time
        
        # Calculate statistics
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            
            # Calculate percentiles
            sorted_times = sorted(response_times)
            p50_index = int(len(sorted_times) * 0.5)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            
            p50 = sorted_times[p50_index] if p50_index < len(sorted_times) else sorted_times[-1]
            p95 = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            p99 = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
        else:
            avg_response_time = min_response_time = max_response_time = 0.0
            p50 = p95 = p99 = 0.0
        
        # Success rate
        successful_requests = len([code for code in status_codes if 200 <= code < 300])
        success_rate = (successful_requests / iterations * 100) if iterations > 0 else 0.0
        
        return {
            'endpoint': endpoint,
            'method': method,
            'iterations': iterations,
            'total_time_seconds': total_time,
            'avg_response_time_ms': avg_response_time,
            'min_response_time_ms': min_response_time,
            'max_response_time_ms': max_response_time,
            'p50_response_time_ms': p50,
            'p95_response_time_ms': p95,
            'p99_response_time_ms': p99,
            'success_rate_percent': success_rate,
            'successful_requests': successful_requests,
            'failed_requests': len(errors),
            'status_codes': status_codes,
            'errors': errors,
            'requests_per_second': iterations / total_time if total_time > 0 else 0.0
        }
    
    def benchmark_multiple_endpoints(self, 
                                   endpoints: List[Dict[str, Any]], 
                                   iterations: int = 10) -> Dict[str, Any]:
        """Benchmark multiple API endpoints"""
        results = []
        start_time = time.time()
        
        for endpoint_config in endpoints:
            endpoint = endpoint_config.get('endpoint', '')
            method = endpoint_config.get('method', 'GET')
            data = endpoint_config.get('data')
            headers = endpoint_config.get('headers')
            
            result = self.benchmark_endpoint(
                endpoint=endpoint,
                method=method,
                data=data,
                headers=headers,
                iterations=iterations
            )
            
            results.append(result)
        
        total_time = time.time() - start_time
        
        # Calculate overall statistics
        all_response_times = []
        total_requests = 0
        total_successful = 0
        
        for result in results:
            if 'avg_response_time_ms' in result:
                all_response_times.extend([result['avg_response_time_ms']] * result.get('iterations', 0))
            total_requests += result.get('iterations', 0)
            total_successful += result.get('successful_requests', 0)
        
        overall_stats = {
            'total_endpoints': len(endpoints),
            'total_requests': total_requests,
            'total_successful_requests': total_successful,
            'overall_success_rate_percent': (total_successful / total_requests * 100) if total_requests > 0 else 0.0,
            'total_benchmark_time_seconds': total_time,
            'overall_requests_per_second': total_requests / total_time if total_time > 0 else 0.0
        }
        
        if all_response_times:
            overall_stats.update({
                'overall_avg_response_time_ms': sum(all_response_times) / len(all_response_times),
                'overall_min_response_time_ms': min(all_response_times),
                'overall_max_response_time_ms': max(all_response_times)
            })
        
        return {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'overall_stats': overall_stats,
            'endpoint_results': results
        }
    
    def save_benchmark_report(self, 
                            benchmark_results: Dict[str, Any], 
                            test_name: str = "api_benchmark") -> str:
        """Save benchmark results report"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{test_name}_benchmark_{timestamp}.json"
            filepath = os.path.join(self.artifacts_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(benchmark_results, f, indent=2, default=str)
            
            return filepath
            
        except Exception as e:
            print(f"Failed to save benchmark report: {e}")
            return ""


@contextmanager
def performance_benchmark(test_name: str, 
                        driver: Optional[WebDriver] = None,
                        save_artifacts: bool = True):
    """Context manager for performance benchmarking"""
    monitor = PerformanceMonitor()
    start_time = time.time()
    start_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    
    success = True
    error_message = None
    artifacts_saved = []
    
    try:
        # Start monitoring
        monitor.start_monitoring(driver)
        
        yield monitor
        
    except Exception as e:
        success = False
        error_message = str(e)
        raise
    
    finally:
        # Stop monitoring
        metrics = monitor.stop_monitoring()
        
        end_time = time.time()
        end_timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        duration = end_time - start_time
        
        # Calculate summary stats
        summary_stats = monitor.calculate_summary_stats(metrics)
        
        # Create benchmark result
        result = BenchmarkResult(
            test_name=test_name,
            start_time=start_timestamp,
            end_time=end_timestamp,
            duration_seconds=duration,
            success=success,
            error_message=error_message,
            metrics=metrics,
            summary_stats=summary_stats,
            artifacts_saved=artifacts_saved
        )
        
        # Save artifacts if requested
        if save_artifacts:
            try:
                report_path = monitor.save_metrics_report(metrics, test_name)
                if report_path:
                    artifacts_saved.append(report_path)
                    result.artifacts_saved = artifacts_saved
            except Exception:
                pass
        
        # Store result in monitor for access
        monitor.last_benchmark_result = result


def measure_page_load_time(driver: WebDriver, url: str) -> Dict[str, float]:
    """Measure page load time and related metrics"""
    if not driver:
        return {'error': 'WebDriver not available'}
    
    try:
        start_time = time.time()
        
        # Navigate to page
        driver.get(url)
        
        # Wait for page to load
        driver.execute_script("return document.readyState") == "complete"
        
        load_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Get detailed timing information
        timing = driver.execute_script("return window.performance.timing;")
        
        if timing:
            navigation_start = timing.get('navigationStart', 0)
            dom_loading = timing.get('domLoading', 0)
            dom_interactive = timing.get('domInteractive', 0)
            dom_complete = timing.get('domComplete', 0)
            load_event_end = timing.get('loadEventEnd', 0)
            
            return {
                'total_load_time_ms': load_time,
                'dom_loading_time_ms': dom_loading - navigation_start if dom_loading and navigation_start else 0,
                'dom_interactive_time_ms': dom_interactive - navigation_start if dom_interactive and navigation_start else 0,
                'dom_complete_time_ms': dom_complete - navigation_start if dom_complete and navigation_start else 0,
                'load_event_time_ms': load_event_end - navigation_start if load_event_end and navigation_start else 0
            }
        else:
            return {'total_load_time_ms': load_time}
            
    except Exception as e:
        return {'error': str(e)}


def create_performance_summary(metrics_list: List[PerformanceMetrics]) -> Dict[str, Any]:
    """Create a comprehensive performance summary"""
    if not metrics_list:
        return {'error': 'No metrics provided'}
    
    monitor = PerformanceMonitor()
    summary_stats = monitor.calculate_summary_stats(metrics_list)
    
    # Additional analysis
    cpu_spikes = len([m for m in metrics_list if m.cpu_percent > 80])
    memory_spikes = len([m for m in metrics_list if m.memory_percent > 80])
    
    # Performance grade
    avg_cpu = summary_stats.get('cpu_avg', 0)
    avg_memory = summary_stats.get('memory_percent_avg', 0)
    
    if avg_cpu < 30 and avg_memory < 50:
        performance_grade = 'A'
    elif avg_cpu < 50 and avg_memory < 70:
        performance_grade = 'B'
    elif avg_cpu < 70 and avg_memory < 85:
        performance_grade = 'C'
    else:
        performance_grade = 'D'
    
    return {
        'summary_stats': summary_stats,
        'performance_grade': performance_grade,
        'cpu_spikes_count': cpu_spikes,
        'memory_spikes_count': memory_spikes,
        'total_samples': len(metrics_list),
        'monitoring_duration_minutes': len(metrics_list) * 1.0 / 60,  # Assuming 1-second intervals
        'recommendations': _generate_performance_recommendations(summary_stats, cpu_spikes, memory_spikes)
    }


def _generate_performance_recommendations(stats: Dict[str, float], 
                                        cpu_spikes: int, 
                                        memory_spikes: int) -> List[str]:
    """Generate performance recommendations based on metrics"""
    recommendations = []
    
    avg_cpu = stats.get('cpu_avg', 0)
    avg_memory = stats.get('memory_percent_avg', 0)
    max_memory = stats.get('memory_max_mb', 0)
    
    if avg_cpu > 70:
        recommendations.append("High CPU usage detected. Consider optimizing CPU-intensive operations.")
    
    if avg_memory > 80:
        recommendations.append("High memory usage detected. Consider memory optimization.")
    
    if cpu_spikes > 5:
        recommendations.append(f"Frequent CPU spikes detected ({cpu_spikes} times). Investigate CPU-intensive operations.")
    
    if memory_spikes > 5:
        recommendations.append(f"Frequent memory spikes detected ({memory_spikes} times). Check for memory leaks.")
    
    if max_memory > 1000:  # > 1GB
        recommendations.append("High memory consumption detected. Consider reducing memory footprint.")
    
    if not recommendations:
        recommendations.append("Performance metrics look good. No immediate optimizations needed.")
    
    return recommendations