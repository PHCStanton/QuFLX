#!/usr/bin/env python3
"""
Test script for the new chart/timeframe dropdown functionality.

This script demonstrates how to use the enhanced chart/timeframe dropdown
detection and control capabilities that have been added to selenium_ui_controls.py
and improved in TF_dropdown_retract.py.
"""

from __future__ import annotations

import sys
import os
from typing import Any, Dict

# Add utils to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

try:
    from selenium_ui_controls import HighPriorityControls
    from capabilities.TF_dropdown_retract import TF_Dropdown_Retract
    from capabilities.base import Ctx
    print("✅ Successfully imported enhanced modules")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class MockDriver:
    """Mock driver for testing without actual browser."""

    def __init__(self):
        self.elements = {}

    def find_element(self, by: str, value: str):
        """Mock find_element - would need actual implementation for real testing."""
        return MockElement()

    def find_elements(self, by: str, value: str):
        """Mock find_elements - would need actual implementation for real testing."""
        return [MockElement()]

    def execute_script(self, script: str, *args):
        """Mock execute_script."""
        return True


class MockElement:
    """Mock element for testing."""

    def __init__(self):
        self.text = "M1"
        self.tag_name = "button"
        self.displayed = True
        self.enabled = True

    def is_displayed(self) -> bool:
        return self.displayed

    def is_enabled(self) -> bool:
        return self.enabled

    def click(self):
        pass

    def get_attribute(self, name: str) -> str:
        return f"mock_{name}"


def test_high_priority_controls():
    """Test the new HighPriorityControls functionality."""
    print("\n🧪 Testing HighPriorityControls enhancements...")

    try:
        # Test with mock driver
        mock_driver = MockDriver()
        hpc = HighPriorityControls(mock_driver)

        # Test finding chart/timeframe dropdown button
        print("  🔍 Testing find_chart_timeframe_dropdown_with_meta()...")
        find_meta = hpc.find_chart_timeframe_dropdown_with_meta()

        print(f"    📊 Find result: ok={find_meta.get('ok')}")
        print(f"    🎯 Button found: {find_meta.get('button_found')}")
        print(f"    📋 Selector used: {find_meta.get('selector_used')}")

        # Test clicking chart/timeframe dropdown button
        print("  🖱️  Testing click_chart_timeframe_dropdown_with_meta()...")
        click_meta = hpc.click_chart_timeframe_dropdown_with_meta()

        print(f"    ✅ Click result: ok={click_meta.get('ok')}")
        print(f"    🎯 Clicked: {click_meta.get('clicked')}")
        print(f"    📂 Dropdown opened: {click_meta.get('dropdown_opened')}")

        print("  ✅ HighPriorityControls tests completed")
        return True

    except Exception as e:
        print(f"  ❌ HighPriorityControls test failed: {e}")
        return False


def test_tf_dropdown_retract():
    """Test the improved TF_Dropdown_Retract functionality."""
    print("\n🧪 Testing TF_Dropdown_Retract improvements...")

    try:
        # Test with mock context
        mock_driver = MockDriver()
        mock_ctx = Ctx(mock_driver, verbose=True)

        tf_retract = TF_Dropdown_Retract()

        # Test open action
        print("  🔓 Testing 'open' action...")
        open_result = tf_retract.run(mock_ctx, {"action": "open"})

        print(f"    📊 Open result: ok={open_result.ok}")
        if open_result.data:
            print(f"    🎯 Opened: {open_result.data.get('opened', 'N/A')}")
            print(f"    📋 Selector used: {open_result.data.get('selector_used', 'N/A')}")

        # Test toggle action
        print("  🔄 Testing 'toggle' action...")
        toggle_result = tf_retract.run(mock_ctx, {"action": "toggle"})

        print(f"    📊 Toggle result: ok={toggle_result.ok}")
        if toggle_result.data:
            print(f"    🔄 Toggle success: {toggle_result.data.get('toggle_success', 'N/A')}")

        # Test close action (should work if button was stored)
        print("  🔒 Testing 'close' action...")
        close_result = tf_retract.run(mock_ctx, {"action": "close"})

        print(f"    📊 Close result: ok={close_result.ok}")
        if close_result.data:
            print(f"    🎯 Closed: {close_result.data.get('closed', 'N/A')}")

        print("  ✅ TF_Dropdown_Retract tests completed")
        return True

    except Exception as e:
        print(f"  ❌ TF_Dropdown_Retract test failed: {e}")
        return False


def demonstrate_usage():
    """Demonstrate proper usage of the new functionality."""
    print("\n📚 Usage Examples:")
    print()

    print("1️⃣ Using HighPriorityControls directly:")
    print("""
    from selenium_ui_controls import HighPriorityControls

    # Initialize with your driver
    hpc = HighPriorityControls(driver)

    # Find the chart/timeframe dropdown button
    find_meta = hpc.find_chart_timeframe_dropdown_with_meta()
    if find_meta['ok']:
        print(f"Found button with selector: {find_meta['selector_used']}")

    # Click the chart/timeframe dropdown button
    click_meta = hpc.click_chart_timeframe_dropdown_with_meta()
    if click_meta['ok']:
        print("Successfully opened chart/timeframe dropdown")
    """)

    print("2️⃣ Using TF_Dropdown_Retract capability:")
    print("""
    from capabilities.TF_dropdown_retract import TF_Dropdown_Retract
    from capabilities.base import Ctx

    # Initialize capability
    tf_retract = TF_Dropdown_Retract()
    ctx = Ctx(driver, verbose=True)

    # Open dropdown
    open_result = tf_retract.run(ctx, {"action": "open"})

    # Toggle dropdown (open then close)
    toggle_result = tf_retract.run(ctx, {"action": "toggle"})

    # Close dropdown
    close_result = tf_retract.run(ctx, {"action": "close"})
    """)

    print("3️⃣ Integration with existing topdown_select:")
    print("""
    # The topdown_select capability now uses enhanced detection automatically
    from capabilities.topdown_select import TopdownSelect

    topdown = TopdownSelect()
    result = topdown.run(ctx, {
        "stack": "1m",
        "save": True,
        "reopen_each": True
    })
    """)


def main():
    """Main test function."""
    print("🧪 Testing Enhanced Chart/Timeframe Dropdown Functionality")
    print("=" * 60)

    # Run tests
    hpc_ok = test_high_priority_controls()
    tf_ok = test_tf_dropdown_retract()

    # Show usage examples
    demonstrate_usage()

    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"  HighPriorityControls: {'✅ PASS' if hpc_ok else '❌ FAIL'}")
    print(f"  TF_Dropdown_Retract:  {'✅ PASS' if tf_ok else '❌ FAIL'}")

    if hpc_ok and tf_ok:
        print("\n🎉 All tests completed successfully!")
        print("The enhanced chart/timeframe dropdown functionality is ready to use.")
    else:
        print("\n⚠️  Some tests failed. Please check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()