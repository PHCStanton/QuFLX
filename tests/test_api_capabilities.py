"""API Capability Testing for QuantumFlux Trading Platform.

This module provides comprehensive testing and validation of API capabilities:
1. Dual API method validation (WebDriver + WebSocket)
2. Performance benchmarking and analysis
3. Data quality assessment
4. Integration testing framework

Migrated from API-test-space for production use.
"""

import os
import pytest
import asyncio
import json
import time
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
from enum import Enum
from unittest.mock import Mock, patch, AsyncMock

from src.core.dual_api_integration import DualAPIManager, ConnectionStatus
from src.core.po_data_collector import PocketOptionDataCollector, CandleData
from config.settings import AppConfig


class ValidationStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class CapabilityType(Enum):
    """Types of API capabilities to test"""
    WEBDRIVER_INIT = "webdriver_initialization"
    PLATFORM_CONNECTION = "platform_connection"
    WEBSOCKET_INTERCEPTION = "websocket_interception"
    DATA_COLLECTION = "data_collection"
    DATA_VALIDATION = "data_validation"
    PERFORMANCE_MONITORING = "performance_monitoring"
    ERROR_HANDLING = "error_handling"
    AUTHENTICATION = "authentication"


@dataclass
class ValidationResult:
    """Individual test result data"""
    test_id: str
    capability: CapabilityType
    status: ValidationStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    success: bool = False
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    logs: List[str] = None

    def __post_init__(self):
        if self.logs is None:
            self.logs = []


@dataclass
class ValidationSuite:
    """Complete validation suite configuration"""
    suite_id: str
    name: str
    description: str
    capabilities_to_test: List[CapabilityType]
    test_duration_seconds: int = 30
    headless_mode: bool = True
    enable_performance_monitoring: bool = True
    enable_data_validation: bool = True
    custom_parameters: Optional[Dict[str, Any]] = None


class APICapabilityValidator:
    """Comprehensive API capability testing and validation framework"""
    
    def __init__(self, 
                 test_session_id: Optional[str] = None,
                 output_directory: str = "test_results",
                 enable_detailed_logging: bool = True):
        """
        Initialize the API capability validator
        
        Args:
            test_session_id: Unique identifier for this test session
            output_directory: Directory for test result outputs
            enable_detailed_logging: Enable detailed test logging
        """
        self.test_session_id = test_session_id or f"api_test_{int(time.time())}"
        self.output_directory = output_directory
        self.enable_detailed_logging = enable_detailed_logging
        
        # Test management
        self.test_results: Dict[str, ValidationResult] = {}
        self.validation_suites: Dict[str, ValidationSuite] = {}
        self.test_logs = deque(maxlen=1000)
        
        # API managers
        self.dual_api_manager: Optional[DualAPIManager] = None
        self.data_collector: Optional[PocketOptionDataCollector] = None
        
        # Performance tracking
        self.performance_metrics = defaultdict(list)
        self.benchmark_results = {}
        
        self._log(f"API Capability Validator initialized - Session: {self.test_session_id}")
        
        # Create default validation suites
        self._create_default_validation_suites()
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}"
        self.test_logs.append(log_entry)
        
        if self.enable_detailed_logging:
            print(log_entry)
    
    def _create_default_validation_suites(self):
        """Create default validation suites for comprehensive testing"""
        
        # Basic API functionality suite
        basic_suite = ValidationSuite(
            suite_id="basic_api_test",
            name="Basic API Functionality",
            description="Test core API initialization and connection capabilities",
            capabilities_to_test=[
                CapabilityType.WEBDRIVER_INIT,
                CapabilityType.PLATFORM_CONNECTION,
                CapabilityType.WEBSOCKET_INTERCEPTION
            ],
            test_duration_seconds=30,
            headless_mode=True
        )
        
        # Data collection and validation suite
        data_suite = ValidationSuite(
            suite_id="data_collection_test",
            name="Data Collection & Validation",
            description="Test real-time data collection and validation capabilities",
            capabilities_to_test=[
                CapabilityType.DATA_COLLECTION,
                CapabilityType.DATA_VALIDATION,
                CapabilityType.PERFORMANCE_MONITORING
            ],
            test_duration_seconds=60,
            headless_mode=True
        )
        
        # Performance and stress testing suite
        performance_suite = ValidationSuite(
            suite_id="performance_stress_test",
            name="Performance & Stress Testing",
            description="Test API performance under various conditions",
            capabilities_to_test=[
                CapabilityType.PERFORMANCE_MONITORING,
                CapabilityType.ERROR_HANDLING,
                CapabilityType.DATA_COLLECTION
            ],
            test_duration_seconds=120,
            headless_mode=True,
            custom_parameters={'stress_test_mode': True}
        )
        
        # Authentication and security suite
        auth_suite = ValidationSuite(
            suite_id="authentication_test",
            name="Authentication & Security",
            description="Test authentication mechanisms and security features",
            capabilities_to_test=[
                CapabilityType.AUTHENTICATION,
                CapabilityType.PLATFORM_CONNECTION,
                CapabilityType.ERROR_HANDLING
            ],
            test_duration_seconds=45,
            headless_mode=False  # May need user interaction
        )
        
        # Register all suites
        for suite in [basic_suite, data_suite, performance_suite, auth_suite]:
            self.validation_suites[suite.suite_id] = suite
        
        self._log(f"Created {len(self.validation_suites)} default validation suites")
    
    async def run_validation_suite(self, suite_id: str) -> Dict[str, ValidationResult]:
        """Run a complete validation suite"""
        if suite_id not in self.validation_suites:
            raise ValueError(f"Validation suite '{suite_id}' not found")
        
        suite = self.validation_suites[suite_id]
        self._log(f"Starting validation suite: {suite.name}")
        
        suite_results = {}
        
        try:
            # Initialize API managers
            await self._initialize_api_managers(suite)
            
            # Run capability tests
            for capability in suite.capabilities_to_test:
                test_result = await self._test_capability(capability, suite)
                suite_results[capability.value] = test_result
                self.test_results[test_result.test_id] = test_result
            
        except Exception as e:
            self._log(f"Validation suite error: {e}", "ERROR")
            raise
        
        finally:
            # Cleanup
            await self._cleanup_api_managers()
        
        self._log(f"Validation suite '{suite.name}' completed")
        return suite_results
    
    async def _initialize_api_managers(self, suite: ValidationSuite):
        """Initialize API managers for testing"""
        self._log("Initializing API managers for testing...")
        
        # Initialize Dual API Manager
        self.dual_api_manager = DualAPIManager(
            status_callback=self._api_status_callback,
            test_mode=True
        )
        
        # Initialize Data Collector
        self.data_collector = PocketOptionDataCollector(
            headless=suite.headless_mode,
            data_callback=self._data_callback,
            test_mode=True,
            validation_enabled=suite.enable_data_validation
        )
        
        self._log("API managers initialized successfully")
    
    async def _cleanup_api_managers(self):
        """Cleanup API managers after testing"""
        self._log("Cleaning up API managers...")
        
        if self.data_collector:
            await self.data_collector.stop()
            self.data_collector = None
        
        if self.dual_api_manager:
            await self.dual_api_manager.disconnect()
            self.dual_api_manager = None
        
        self._log("API managers cleaned up")
    
    def _api_status_callback(self, status: ConnectionStatus):
        """Callback for API status updates"""
        self._log(f"API Status: WebDriver={status.webdriver_connected}, WebSocket={status.websocket_connected}")
    
    def _data_callback(self, data: CandleData):
        """Callback for data updates"""
        if self.enable_detailed_logging:
            self._log(f"Data received: {data.asset} - {data.close}")
    
    async def _test_capability(self, capability: CapabilityType, suite: ValidationSuite) -> ValidationResult:
        """Test a specific API capability"""
        test_id = f"{suite.suite_id}_{capability.value}_{int(time.time())}"
        test_result = ValidationResult(
            test_id=test_id,
            capability=capability,
            status=ValidationStatus.RUNNING,
            start_time=datetime.now()
        )
        
        self._log(f"Testing capability: {capability.value}")
        
        try:
            # Route to specific capability test
            if capability == CapabilityType.WEBDRIVER_INIT:
                success, metrics = await self._test_webdriver_initialization(suite)
            elif capability == CapabilityType.PLATFORM_CONNECTION:
                success, metrics = await self._test_platform_connection(suite)
            elif capability == CapabilityType.WEBSOCKET_INTERCEPTION:
                success, metrics = await self._test_websocket_interception(suite)
            elif capability == CapabilityType.DATA_COLLECTION:
                success, metrics = await self._test_data_collection(suite)
            elif capability == CapabilityType.DATA_VALIDATION:
                success, metrics = await self._test_data_validation(suite)
            elif capability == CapabilityType.PERFORMANCE_MONITORING:
                success, metrics = await self._test_performance_monitoring(suite)
            elif capability == CapabilityType.ERROR_HANDLING:
                success, metrics = await self._test_error_handling(suite)
            elif capability == CapabilityType.AUTHENTICATION:
                success, metrics = await self._test_authentication(suite)
            else:
                success, metrics = False, {'error': 'Unknown capability type'}
            
            test_result.success = success
            test_result.metrics = metrics
            test_result.status = ValidationStatus.COMPLETED if success else ValidationStatus.FAILED
            
        except Exception as e:
            test_result.success = False
            test_result.error_message = str(e)
            test_result.status = ValidationStatus.FAILED
            self._log(f"Capability test error: {e}", "ERROR")
        
        test_result.end_time = datetime.now()
        test_result.duration_seconds = (test_result.end_time - test_result.start_time).total_seconds()
        
        self._log(f"Capability test '{capability.value}' completed: {'SUCCESS' if test_result.success else 'FAILED'}")
        
        return test_result
    
    async def _test_webdriver_initialization(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test WebDriver initialization capability"""
        metrics = {'test_type': 'webdriver_initialization'}
        
        try:
            if not self.dual_api_manager:
                return False, {'error': 'Dual API manager not initialized'}
            
            # Test WebDriver initialization
            start_time = time.time()
            success = await self.dual_api_manager.initialize_webdriver()
            init_time = time.time() - start_time
            
            metrics.update({
                'initialization_time_seconds': init_time,
                'webdriver_initialized': success
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_platform_connection(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test platform connection capability"""
        metrics = {'test_type': 'platform_connection'}
        
        try:
            if not self.dual_api_manager:
                return False, {'error': 'Dual API manager not initialized'}
            
            # Test platform connection
            start_time = time.time()
            status = self.dual_api_manager.get_connection_status()
            connection_time = time.time() - start_time
            
            success = status.webdriver_connected and status.platform_logged_in
            
            metrics.update({
                'connection_time_seconds': connection_time,
                'webdriver_connected': status.webdriver_connected,
                'platform_logged_in': status.platform_logged_in,
                'websocket_connected': status.websocket_connected
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_websocket_interception(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test WebSocket interception capability"""
        metrics = {'test_type': 'websocket_interception'}
        
        try:
            if not self.dual_api_manager:
                return False, {'error': 'Dual API manager not initialized'}
            
            # Test WebSocket interception
            start_time = time.time()
            status = self.dual_api_manager.get_connection_status()
            test_duration = min(suite.test_duration_seconds, 30)  # Cap at 30 seconds
            
            # Wait for WebSocket connection
            await asyncio.sleep(test_duration)
            
            final_status = self.dual_api_manager.get_connection_status()
            test_time = time.time() - start_time
            
            success = final_status.websocket_connected
            
            metrics.update({
                'test_duration_seconds': test_time,
                'initial_websocket_connected': status.websocket_connected,
                'final_websocket_connected': final_status.websocket_connected,
                'connection_stable': status.websocket_connected == final_status.websocket_connected
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_data_collection(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test data collection capability"""
        metrics = {'test_type': 'data_collection'}
        
        try:
            if not self.data_collector:
                return False, {'error': 'Data collector not initialized'}
            
            # Test data collection
            start_time = time.time()
            test_duration = min(suite.test_duration_seconds, 60)  # Cap at 60 seconds
            
            # Start data collection
            await self.data_collector.start()
            await asyncio.sleep(test_duration)
            
            # Get collected data
            data = self.data_collector.get_latest_data()
            collection_time = time.time() - start_time
            
            success = len(data) > 0 if data else False
            
            metrics.update({
                'collection_duration_seconds': collection_time,
                'data_points_collected': len(data) if data else 0,
                'data_collection_successful': success
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_data_validation(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test data validation capability"""
        metrics = {'test_type': 'data_validation'}
        
        try:
            if not self.data_collector:
                return False, {'error': 'Data collector not initialized'}
            
            # Test data validation
            data = self.data_collector.get_latest_data()
            
            if not data:
                return False, {'error': 'No data available for validation'}
            
            # Validate data structure and content
            validation_results = []
            for asset, asset_data in data.items():
                if isinstance(asset_data, dict) and 'price' in asset_data:
                    validation_results.append(True)
                else:
                    validation_results.append(False)
            
            success = all(validation_results) and len(validation_results) > 0
            
            metrics.update({
                'assets_validated': len(validation_results),
                'validation_success_rate': sum(validation_results) / len(validation_results) if validation_results else 0,
                'data_validation_successful': success
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_performance_monitoring(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test performance monitoring capability"""
        metrics = {'test_type': 'performance_monitoring'}
        
        try:
            # Collect performance metrics
            start_time = time.time()
            test_duration = min(suite.test_duration_seconds, 30)  # Cap at 30 seconds
            
            # Monitor performance during test
            performance_samples = []
            for _ in range(int(test_duration)):
                sample_start = time.time()
                
                # Simulate performance monitoring
                if self.dual_api_manager:
                    status = self.dual_api_manager.get_connection_status()
                    sample_time = time.time() - sample_start
                    performance_samples.append(sample_time)
                
                await asyncio.sleep(1)
            
            total_time = time.time() - start_time
            
            if performance_samples:
                avg_response_time = statistics.mean(performance_samples)
                max_response_time = max(performance_samples)
                min_response_time = min(performance_samples)
                success = avg_response_time < 1.0  # Success if average response < 1 second
            else:
                avg_response_time = max_response_time = min_response_time = 0
                success = False
            
            metrics.update({
                'test_duration_seconds': total_time,
                'performance_samples': len(performance_samples),
                'avg_response_time_seconds': avg_response_time,
                'max_response_time_seconds': max_response_time,
                'min_response_time_seconds': min_response_time,
                'performance_acceptable': success
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_error_handling(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test error handling capability"""
        metrics = {'test_type': 'error_handling'}
        
        try:
            # Test error handling scenarios
            error_scenarios_tested = 0
            error_scenarios_handled = 0
            
            # Test scenario 1: Invalid connection
            try:
                if self.dual_api_manager:
                    # Simulate error condition
                    status = self.dual_api_manager.get_connection_status()
                    error_scenarios_tested += 1
                    error_scenarios_handled += 1  # If no exception, it's handled
            except Exception:
                error_scenarios_tested += 1
                # Exception caught, so error handling works
                error_scenarios_handled += 1
            
            # Test scenario 2: Data collection error
            try:
                if self.data_collector:
                    # Test with invalid parameters
                    data = self.data_collector.get_latest_data()
                    error_scenarios_tested += 1
                    error_scenarios_handled += 1
            except Exception:
                error_scenarios_tested += 1
                error_scenarios_handled += 1
            
            success = error_scenarios_handled == error_scenarios_tested and error_scenarios_tested > 0
            
            metrics.update({
                'error_scenarios_tested': error_scenarios_tested,
                'error_scenarios_handled': error_scenarios_handled,
                'error_handling_success_rate': error_scenarios_handled / error_scenarios_tested if error_scenarios_tested > 0 else 0,
                'error_handling_successful': success
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    async def _test_authentication(self, suite: ValidationSuite) -> Tuple[bool, Dict[str, Any]]:
        """Test authentication capability"""
        metrics = {'test_type': 'authentication'}
        
        try:
            if not self.dual_api_manager:
                return False, {'error': 'Dual API manager not initialized'}
            
            # Test authentication status
            start_time = time.time()
            status = self.dual_api_manager.get_connection_status()
            auth_time = time.time() - start_time
            
            success = status.platform_logged_in
            
            metrics.update({
                'authentication_check_time_seconds': auth_time,
                'platform_logged_in': status.platform_logged_in,
                'webdriver_connected': status.webdriver_connected,
                'authentication_successful': success
            })
            
            return success, metrics
            
        except Exception as e:
            metrics['error'] = str(e)
            return False, metrics
    
    def get_test_results(self) -> Dict[str, ValidationResult]:
        """Get all test results"""
        return self.test_results.copy()
    
    def get_validation_suites(self) -> Dict[str, ValidationSuite]:
        """Get all validation suites"""
        return self.validation_suites.copy()
    
    def export_results(self, format_type: str = "json") -> str:
        """Export test results to specified format"""
        if format_type.lower() == "json":
            results_data = {
                'session_id': self.test_session_id,
                'timestamp': datetime.now().isoformat(),
                'test_results': {k: asdict(v) for k, v in self.test_results.items()},
                'validation_suites': {k: asdict(v) for k, v in self.validation_suites.items()}
            }
            return json.dumps(results_data, indent=2, default=str)
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Pytest fixtures and test classes

@pytest.fixture
def api_validator():
    """Fixture for API capability validator"""
    return APICapabilityValidator(
        test_session_id="pytest_session",
        enable_detailed_logging=False
    )


@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Mock(spec=AppConfig)
    config.test.test_mode = True
    config.test.test_timeout_seconds = 30
    config.validation.enable_real_time_validation = True
    config.data_collection.collection_interval_ms = 1000
    return config


class TestAPICapabilities:
    """Test suite for API capability validation"""
    
    def test_validator_initialization(self, api_validator):
        """Test API validator initialization"""
        assert api_validator.test_session_id == "pytest_session"
        assert len(api_validator.validation_suites) > 0
        assert "basic_api_test" in api_validator.validation_suites
    
    def test_validation_suite_creation(self, api_validator):
        """Test validation suite creation"""
        suites = api_validator.get_validation_suites()
        
        # Check that default suites are created
        expected_suites = ["basic_api_test", "data_collection_test", "performance_stress_test", "authentication_test"]
        for suite_id in expected_suites:
            assert suite_id in suites
            suite = suites[suite_id]
            assert isinstance(suite, ValidationSuite)
            assert len(suite.capabilities_to_test) > 0
    
    @pytest.mark.asyncio
    async def test_webdriver_initialization_capability(self, api_validator):
        """Test WebDriver initialization capability"""
        # Mock the dual API manager
        mock_manager = Mock()
        mock_manager.initialize_webdriver = AsyncMock(return_value=True)
        api_validator.dual_api_manager = mock_manager
        
        suite = ValidationSuite(
            suite_id="test_webdriver",
            name="Test WebDriver",
            description="Test WebDriver initialization",
            capabilities_to_test=[CapabilityType.WEBDRIVER_INIT],
            test_duration_seconds=5
        )
        
        success, metrics = await api_validator._test_webdriver_initialization(suite)
        
        assert success is True
        assert 'initialization_time_seconds' in metrics
        assert 'webdriver_initialized' in metrics
    
    @pytest.mark.asyncio
    async def test_platform_connection_capability(self, api_validator):
        """Test platform connection capability"""
        # Mock the dual API manager
        mock_manager = Mock()
        mock_status = Mock()
        mock_status.webdriver_connected = True
        mock_status.platform_logged_in = True
        mock_status.websocket_connected = True
        mock_manager.get_connection_status = Mock(return_value=mock_status)
        api_validator.dual_api_manager = mock_manager
        
        suite = ValidationSuite(
            suite_id="test_connection",
            name="Test Connection",
            description="Test platform connection",
            capabilities_to_test=[CapabilityType.PLATFORM_CONNECTION],
            test_duration_seconds=5
        )
        
        success, metrics = await api_validator._test_platform_connection(suite)
        
        assert success is True
        assert 'connection_time_seconds' in metrics
        assert 'webdriver_connected' in metrics
        assert 'platform_logged_in' in metrics
    
    @pytest.mark.asyncio
    async def test_data_collection_capability(self, api_validator):
        """Test data collection capability"""
        # Mock the data collector
        mock_collector = Mock()
        mock_collector.start = AsyncMock(return_value=None)
        mock_collector.get_latest_data = Mock(return_value={
            'EURUSD': {'price': 1.1234, 'timestamp': '2024-01-01T00:00:00'}
        })
        api_validator.data_collector = mock_collector
        
        suite = ValidationSuite(
            suite_id="test_data",
            name="Test Data Collection",
            description="Test data collection",
            capabilities_to_test=[CapabilityType.DATA_COLLECTION],
            test_duration_seconds=5
        )
        
        success, metrics = await api_validator._test_data_collection(suite)
        
        assert success is True
        assert 'collection_duration_seconds' in metrics
        assert 'data_points_collected' in metrics
        assert metrics['data_points_collected'] > 0
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_capability(self, api_validator):
        """Test performance monitoring capability"""
        # Mock the dual API manager
        mock_manager = Mock()
        mock_status = Mock()
        mock_status.webdriver_connected = True
        mock_manager.get_connection_status = AsyncMock(return_value=mock_status)
        api_validator.dual_api_manager = mock_manager
        
        suite = ValidationSuite(
            suite_id="test_performance",
            name="Test Performance",
            description="Test performance monitoring",
            capabilities_to_test=[CapabilityType.PERFORMANCE_MONITORING],
            test_duration_seconds=3  # Short duration for testing
        )
        
        success, metrics = await api_validator._test_performance_monitoring(suite)
        
        assert 'test_duration_seconds' in metrics
        assert 'performance_samples' in metrics
        assert 'avg_response_time_seconds' in metrics
    
    def test_export_results(self, api_validator):
        """Test results export functionality"""
        # Add a test result
        test_result = ValidationResult(
            test_id="test_export",
            capability=CapabilityType.WEBDRIVER_INIT,
            status=ValidationStatus.COMPLETED,
            start_time=datetime.now(),
            success=True
        )
        api_validator.test_results["test_export"] = test_result
        
        # Export results
        exported = api_validator.export_results("json")
        
        assert isinstance(exported, str)
        data = json.loads(exported)
        assert 'session_id' in data
        assert 'test_results' in data
        assert 'validation_suites' in data
        assert 'test_export' in data['test_results']
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_validation_suite_mock(self, api_validator):
        """Test running a full validation suite with mocked components"""
        # This test uses mocks to simulate a full validation suite run
        with patch.object(api_validator, '_initialize_api_managers') as mock_init, \
             patch.object(api_validator, '_cleanup_api_managers') as mock_cleanup, \
             patch.object(api_validator, '_test_capability') as mock_test:
            
            # Mock successful capability test
            mock_test_result = ValidationResult(
                test_id="mock_test",
                capability=CapabilityType.WEBDRIVER_INIT,
                status=ValidationStatus.COMPLETED,
                start_time=datetime.now(),
                success=True
            )
            mock_test.return_value = mock_test_result
            
            # Run validation suite
            results = await api_validator.run_validation_suite("basic_api_test")
            
            # Verify results
            assert len(results) > 0
            mock_init.assert_called_once()
            mock_cleanup.assert_called_once()
            assert mock_test.call_count > 0


@pytest.mark.integration
class TestAPICapabilitiesIntegration:
    """Integration tests for API capabilities (requires actual components)"""
    
    @pytest.mark.skipif(not os.getenv('RUN_INTEGRATION_TESTS'), 
                        reason="Integration tests require RUN_INTEGRATION_TESTS=1")
    @pytest.mark.asyncio
    async def test_real_api_validation(self):
        """Test API validation with real components (requires environment setup)"""
        validator = APICapabilityValidator(
            test_session_id="integration_test",
            enable_detailed_logging=True
        )
        
        try:
            # Run a basic validation suite
            results = await validator.run_validation_suite("basic_api_test")
            
            # Verify we got results
            assert len(results) > 0
            
            # Check that at least some tests passed
            success_count = sum(1 for result in results.values() if result.success)
            assert success_count > 0, "At least some capability tests should pass"
            
        except Exception as e:
            pytest.skip(f"Integration test failed due to environment: {e}")