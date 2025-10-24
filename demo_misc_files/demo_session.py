#!/usr/bin/env python3
"""
Demo script showing how to maintain a CLI session across multiple operations.
This demonstrates the proper way to run multiple CLI operations with shared state.
"""

import sys
from pathlib import Path

# Add capabilities to path
capabilities_dir = Path(__file__).parent / "capabilities"
if str(capabilities_dir) not in sys.path:
    sys.path.insert(0, str(capabilities_dir))

# Import CLI functions directly
from qf import attach_chrome_session
import qf  # Import the module to access globals

def demo_cli_session():
    """Demonstrate maintaining a CLI session across operations."""
    print("🚀 QuantumFlux CLI Session Demo")
    print("=" * 40)

    try:
        # Step 1: Attach to Chrome (maintains global state)
        print("\n1️⃣ Attaching to Chrome session...")
        success, result = attach_chrome_session(port=9222, verbose=True)

        if not success:
            print(f"❌ Failed to attach: {result}")
            return

        print("✅ Successfully attached to Chrome!")

        # Verify globals are set
        print(f"🔗 Driver connected: {qf.driver is not None}")
        print(f"📊 Context created: {qf.ctx is not None}")

        # Step 2: Import and run operations using the shared session
        print("\n2️⃣ Running operations with shared session...")

        # Import capabilities
        from capabilities.data_streaming import RealtimeDataStreaming
        from capabilities.profile_scan import ProfileScan
        from capabilities.session_scan import SessionScan

        # Operation 1: Profile scan
        print("\n👤 Scanning profile...")
        profile_scan = ProfileScan()
        result = profile_scan.run(qf.ctx, {})
        if result.ok:
            data = result.data
            print(f"✅ Profile: {data.get('account')} | Balance: {data.get('balance')}")
        else:
            print(f"❌ Profile scan failed: {result.error}")

        # Operation 2: Session scan
        print("\n📊 Scanning session...")
        session_scan = SessionScan()
        result = session_scan.run(qf.ctx, {})
        if result.ok:
            data = result.data
            print(f"✅ Session: {data.get('account')} | Amount: {data.get('amount')}")
        else:
            print(f"❌ Session scan failed: {result.error}")

        # Operation 3: Data streaming snapshot
        print("\n📈 Running data streaming snapshot...")
        data_streaming = RealtimeDataStreaming()
        data_streaming.PERIOD = 1 * 60  # 1 minute
        data_streaming.CANDLE_ONLY_MODE = True

        result = data_streaming.run(qf.ctx, {"period": 60})
        if result.ok:
            data = result.data
            print("✅ Data streaming completed")
            print(f"📊 Updates collected: {data.get('total_realtime_updates', 0)}")
            print(f"🎯 Current asset: {data.get('current_asset', 'None')}")
        else:
            print(f"❌ Data streaming failed: {result.error}")

        print("\n🎉 All operations completed successfully with shared session!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Cleanup
        try:
            if qf.driver:
                qf.driver.quit()
                print("\n🔌 Chrome session closed")
        except:
            pass

if __name__ == "__main__":
    demo_cli_session()
