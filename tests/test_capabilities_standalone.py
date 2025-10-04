"""
Standalone test for capabilities-first architecture.
Tests direct capability integration without conftest.py dependencies.
"""

import sys
import os
from unittest.mock import Mock

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def test_capabilities_direct_import():
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
        print("✓ All capabilities imported successfully")

    except ImportError as e:
        print(f"✗ Failed to import capabilities directly: {e}")
        return False
    return True

def test_data_streaming_initialization():
    """Test that RealtimeDataStreaming initializes correctly."""
    try:
        from capabilities.data_streaming import RealtimeDataStreaming

        rds = RealtimeDataStreaming()

        # Check default attributes
        assert rds.PERIOD == 60  # Default period in seconds
        assert rds.CURRENT_ASSET is None
        assert rds.SESSION_AUTHENTICATED is False
        assert rds.SESSION_TIMEFRAME_DETECTED is False
        assert rds.enable_csv_saving is True
        print("✓ RealtimeDataStreaming initialized correctly")

    except Exception as e:
        print(f"✗ RealtimeDataStreaming initialization failed: {e}")
        return False
    return True

def test_backend_imports_capabilities():
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
        print("✓ Backend capability imports work")

    except Exception as e:
        print(f"✗ Backend capability imports failed: {e}")
        return False
    return True

def test_cli_imports_work():
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
        print("✓ CLI capability imports work")

    except Exception as e:
        print(f"✗ CLI capability imports failed: {e}")
        return False
    return True

def test_no_circular_dependencies():
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
        print("✓ No circular import issues")

    except ImportError as e:
        print(f"✗ Circular import detected: {e}")
        return False
    return True

def test_data_streaming_run_without_logs():
    """Test data streaming run with no WebSocket logs."""
    try:
        from capabilities.data_streaming import RealtimeDataStreaming
        from capabilities.base import Ctx

        # Mock driver
        mock_driver = Mock()
        mock_driver.get_log.return_value = []

        # Mock context
        ctx = Ctx(
            driver=mock_driver,
            artifacts_root="test_artifacts",
            debug=False,
            dry_run=False,
            verbose=True
        )

        rds = RealtimeDataStreaming()
        result = rds.run(ctx, {"period": 60})

        # Should return successful result even with no data
        assert result.ok is True
        assert "total_realtime_updates" in result.data
        assert "latest_asset_prices" in result.data
        assert result.data["total_realtime_updates"] == 0
        print("✓ Data streaming run without logs works")

    except Exception as e:
        print(f"✗ Data streaming run failed: {e}")
        return False
    return True

def test_smoke_test_integration():
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
        print("✓ Smoke test integration works")

    except Exception as e:
        print(f"✗ Smoke test integration failed: {e}")
        return False
    return True

def main():
    """Run all tests."""
    print("Testing Capabilities-First Architecture")
    print("=" * 50)

    tests = [
        test_capabilities_direct_import,
        test_data_streaming_initialization,
        test_backend_imports_capabilities,
        test_cli_imports_work,
        test_no_circular_dependencies,
        test_data_streaming_run_without_logs,
        test_smoke_test_integration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ {test.__name__} failed with exception: {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Capabilities-first architecture is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
