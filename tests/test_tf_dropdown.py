#!/usr/bin/env python3
"""
Test script for TF_dropdown_retract capability.
This demonstrates how to use the timeframe dropdown open/close functionality.
"""

import sys
import os
from pathlib import Path

# Add current directory to path for imports
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

# Import the capability
from capabilities.TF_dropdown_retract import TF_Dropdown_Retract

def test_tf_dropdown_capability():
    """Test the TF dropdown capability with mock context."""
    print("🧪 Testing TF Dropdown Retract Capability")
    print("=" * 50)

    # Create capability instance
    tf_dropdown = TF_Dropdown_Retract()

    print(f"✅ Capability created: {tf_dropdown.id}")
    print(f"📋 Available actions: open, close, toggle")
    print(f"🎯 Purpose: Open and retract timeframe dropdown menu")
    print()

    # Show capability info
    print("📖 Capability Information:")
    print(f"   - ID: {tf_dropdown.id}")
    print(f"   - Kind: {tf_dropdown.kind}")
    print("   - Description: Open and retract the timeframe dropdown menu")
    print()

    print("💡 Usage Examples:")
    print("   # Open dropdown")
    print("   result = tf_dropdown.run(ctx, {'action': 'open'})")
    print()
    print("   # Close previously opened dropdown")
    print("   result = tf_dropdown.run(ctx, {'action': 'close'})")
    print()
    print("   # Complete open/close cycle")
    print("   result = tf_dropdown.run(ctx, {'action': 'toggle'})")
    print()

    print("🔧 Integration with existing system:")
    print("   - Added to capabilities/__init__.py")
    print("   - Can be imported: from capabilities import TF_Dropdown_Retract")
    print("   - Factory function available: build() -> TF_Dropdown_Retract")
    print()

    print("✅ TF Dropdown Retract capability is ready for use!")
    print("💡 Use this capability to test dropdown open/close behavior independently")

if __name__ == "__main__":
    test_tf_dropdown_capability()
