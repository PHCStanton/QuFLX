"""
Test suite for the new capabilities-first architecture.
Tests the direct integration of capabilities without complex adapters.
"""

import pytest
from unittest.mock import Mock, patch
from capabilities.data_streaming import RealtimeDataStreaming
from capabilities.base import Ctx, CapResult


class TestCapabilitiesFirst:
    """Test the capabilities-first architecture."""

    @pytest.fixture
    def mock_driver(self):
        """Mock selenium webdriver."""
        driver = Mock()
        driver.get_log.return_value = []
        return driver

    @pytest.fixture
    def mock_ctx(self, mock_driver):
        """Mock context object."""
        return Ctx(
            driver=mock_driver,
            artifacts_root="test_artifacts",
            debug=False,
            dry_run=False,
            verbose=True
        )

    def test_data_streaming_initialization(self):
        """Test that RealtimeDataStreaming initializes correctly."""
        rds = RealtimeDataStreaming()

        # Check default attributes
        assert rds.PERIOD == 60  # Default period in seconds
        assert rds.CURRENT_ASSET is None
        assert rds.SESSION_AUTHENTICATED is False
        assert rds.SESSION_TIMEFRAME_DETECTED is False
        assert rds.enable_csv_saving is True

    def test_data_streaming_run_without_logs(self, mock_ctx):
        """Test data streaming run with no WebSocket logs."""
        rds = RealtimeDataStreaming()
        result = rds.run(mock_ctx, {"period": 60})

        # Should return successful result even with no data
        assert result.ok is True
        assert "total_realtime_updates" in result.data
        assert "latest_asset_prices" in result.data
        assert result.data["total_realtime_updates"] == 0

    def test_data_streaming_with_custom_period(self, mock_ctx):
        """Test data streaming with custom period."""
        rds = RealtimeDataStreaming()
        result = rds.run(mock_ctx, {"period": 120})  # 2 minutes

        assert result.ok is True
        assert result.data["period_minutes"] == 120

    def test_capabilities_direct_import(self):
        """Test that capabilities can be imported directly."""
        try:
            from capabilities.data_streaming import RealtimeDataStreaming
            from capabilities.profile_scan import ProfileScan
            from capabilities.session_scan import SessionScan
            from capabilities.favorite_select import FavoriteSelect
            from capabilities.trade_click_cap import TradeClick

            # All imports should succeed
            assert RealtimeDataStreaming is not None
            assert ProfileScan is not None
            assert SessionScan is not None
            assert FavoriteSelect is not None
            assert TradeClick is not None

        except ImportError as e:
            pytest.fail(f"Failed to import capabilities directly: {e}")

    def test_backend_imports_capabilities(self):
        """Test that backend can import capabilities directly."""
        try:
            # This simulates what backend.py does
            from capabilities.data_streaming import RealtimeDataStreaming
            from capabilities.profile_scan import ProfileScan
            from capabilities.session_scan import SessionScan

            # Create instances
            rds = RealtimeDataStreaming()
            ps = ProfileScan()
            ss = SessionScan()

            assert rds is not None
            assert ps is not None
            assert ss is not None

        except Exception as e:
            pytest.fail(f"Backend capability imports failed: {e}")

    def test_cli_imports_work(self):
        """Test that CLI can import capabilities."""
        try:
            from capabilities.data_streaming import RealtimeDataStreaming
            from capabilities.profile_scan import ProfileScan
            from capabilities.session_scan import SessionScan
            from capabilities.favorite_select import FavoriteSelect

            # Test that CLI can create capability instances
            capabilities = {
                "data_streaming": RealtimeDataStreaming(),
                "profile_scan": ProfileScan(),
                "session_scan": SessionScan(),
                "favorite_select": FavoriteSelect()
            }

            assert len(capabilities) == 4
            for name, cap in capabilities.items():
                assert cap is not None

        except Exception as e:
            pytest.fail(f"CLI capability imports failed: {e}")

    @patch('capabilities.data_streaming.RealtimeDataStreaming._get_performance_logs')
    def test_data_streaming_with_mock_logs(self, mock_get_logs, mock_ctx):
        """Test data streaming with mock WebSocket logs."""
        # Mock some basic WebSocket logs
        mock_logs = [
            {
                "message": {
                    "method": "Network.webSocketFrameReceived",
                    "params": {
                        "response": {
                            "payloadData": "test_payload"
                        }
                    }
                }
            }
        ]
        mock_get_logs.return_value = mock_logs

        rds = RealtimeDataStreaming()
        result = rds.run(mock_ctx, {"period": 60})

        assert result.ok is True
        # Should have processed the mock log
        assert result.data["total_realtime_updates"] == 0  # No valid data in mock

    def test_smoke_test_integration(self):
        """Test that smoke test can import and use capabilities."""
        try:
            from capabilities.data_streaming import RealtimeDataStreaming
            from capabilities.profile_scan import ProfileScan
            from capabilities.session_scan import SessionScan

            # This mirrors what test_smoke.py does
            rds = RealtimeDataStreaming()
            ps = ProfileScan()
            ss = SessionScan()

            assert hasattr(rds, 'run')
            assert hasattr(ps, 'run')
            assert hasattr(ss, 'run')

        except Exception as e:
            pytest.fail(f"Smoke test integration failed: {e}")


class TestArchitectureSimplification:
    """Test that the architecture is simplified compared to old approach."""

    def test_no_complex_adapters_needed(self):
        """Test that we don't need complex adapter layers."""
        try:
            # Direct capability usage - this should work without adapters
            from capabilities.data_streaming import RealtimeDataStreaming
            from capabilities.profile_scan import ProfileScan

            rds = RealtimeDataStreaming()
            ps = ProfileScan()

            # Should be able to call methods directly
            assert hasattr(rds, 'run')
            assert hasattr(ps, 'run')

        except Exception as e:
            pytest.fail(f"Direct capability usage failed: {e}")

    def test_backend_direct_integration(self):
        """Test that backend integrates directly with capabilities."""
        try:
            # Simulate backend.py imports
            from capabilities.data_streaming import RealtimeDataStreaming
            from capabilities.profile_scan import ProfileScan
            from capabilities.session_scan import SessionScan
            from capabilities.favorite_select import FavoriteSelect
            from capabilities.trade_click_cap import TradeClick

            # Backend should be able to create instances directly
            capabilities = {
                "data_streaming": RealtimeDataStreaming(),
                "profile_scan": ProfileScan(),
                "session_scan": SessionScan(),
                "favorites": FavoriteSelect(),
                "trade": TradeClick()
            }

            assert len(capabilities) == 5

        except Exception as e:
            pytest.fail(f"Backend direct integration failed: {e}")

    def test_no_circular_dependencies(self):
        """Test that there are no circular import issues."""
        try:
            # Import all capabilities at once - should not cause circular imports
            from capabilities import (
                data_streaming,
                profile_scan,
                session_scan,
                favorite_select,
                trade_click_cap
            )

            assert data_streaming.RealtimeDataStreaming is not None
            assert profile_scan.ProfileScan is not None
            assert session_scan.SessionScan is not None
            assert favorite_select.FavoriteSelect is not None
            assert trade_click_cap.TradeClick is not None

        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
