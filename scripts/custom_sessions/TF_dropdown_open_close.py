"""
TF Dropdown Open/Close Test Session

Behavior:
- Starts data streaming first (background), then tests the TF_dropdown_retract capability with toggle action.
- Persistence (CSV saving) is DISABLED by default in this session to avoid mixing trading/strategy runs with data collection.

Enable persistence explicitly (opt-in):
- Flags:
  --save-candles            Enable candle CSV saving (closed candles only; rotated)
  --save-ticks              Enable tick CSV saving (every tick; rotated)
  --candle-chunk-size N     Closed candle rows per CSV file (default: 100)
  --tick-chunk-size N       Tick rows per CSV file (default: 1000)
- Environment overrides (alternative quick toggle):
  QF_PERSIST=1              Enable both candles and ticks
  QF_PERSIST_CANDLES=1      Enable candles
  QF_PERSIST_TICKS=1        Enable ticks

Destinations (if enabled):
- Candles: data/data_output/assets_data/realtime_stream/1M_candle_data
- Ticks:   data/data_output/assets_data/realtime_stream/1M_tick_data

Notes:
- Only CLOSED candles are written (the currently forming candle is never persisted).
- No changes were made to capabilities/data_streaming.py; patching is local to this session and only installed when persistence is enabled.
"""

import sys
import os
import threading
import time
from pathlib import Path
import types

# Add capabilities to path
capabilities_dir = Path(__file__).parent.parent.parent / "capabilities"
if str(capabilities_dir) not in sys.path:
    sys.path.insert(0, str(capabilities_dir))

from data_streaming import RealtimeDataStreaming
from stream_persistence import StreamPersistenceManager
from qf import attach_chrome_session
import qf

# Import TF_Dropdown_Retract with proper path handling
try:
    from TF_dropdown_retract import TF_Dropdown_Retract
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    this_file = Path(__file__).resolve()
    api_root = this_file.parents[2]  # .../QuFLX
    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))
    from capabilities.TF_dropdown_retract import TF_Dropdown_Retract

def start_data_streaming(stream_mode, asset_focus, csv_output, output_dir, save_candles=False, save_ticks=False, candle_chunk_size=100, tick_chunk_size=1000):
    """Function to run data streaming in background thread."""
    try:
        print(f"📈 [STREAM] Starting {stream_mode} data streaming in background...")

        # Configure data streaming
        streamer = RealtimeDataStreaming()
        streamer.enable_csv_saving = csv_output

        # Set streaming mode
        if stream_mode == "candle":
            streamer.CANDLE_ONLY_MODE = True
            streamer.TICK_ONLY_MODE = False
            streamer.TICK_DATA_MODE = False
        elif stream_mode == "tick":
            streamer.CANDLE_ONLY_MODE = False
            streamer.TICK_ONLY_MODE = True
            streamer.TICK_DATA_MODE = True
        else:  # both
            streamer.CANDLE_ONLY_MODE = False
            streamer.TICK_ONLY_MODE = False
            streamer.TICK_DATA_MODE = False

        streamer.ASSET_FOCUS_MODE = asset_focus

        # Disable core CSV saving; use our persistence layer instead
        streamer.enable_csv_saving = False

        # Check env overrides and prepare persistence only if enabled
        env_persist = os.getenv("QF_PERSIST")
        env_ticks = os.getenv("QF_PERSIST_TICKS")
        env_candles = os.getenv("QF_PERSIST_CANDLES")

        effective_save_candles = bool(save_candles) or bool(env_persist) or bool(env_candles)
        effective_save_ticks = bool(save_ticks) or bool(env_persist) or bool(env_ticks)

        if effective_save_candles or effective_save_ticks:
            # Prepare persistence manager targeting required directories
            project_root = Path(__file__).parent.parent.parent
            candle_dir = project_root / "data" / "data_output" / "assets_data" / "realtime_stream" / "1M_candle_data"
            tick_dir = project_root / "data" / "data_output" / "assets_data" / "realtime_stream" / "1M_tick_data"

            spm = StreamPersistenceManager(
                candle_dir=candle_dir,
                tick_dir=tick_dir,
                candle_chunk_size=candle_chunk_size,
                tick_chunk_size=tick_chunk_size,
            )

            # Track last CLOSED candle index written per asset
            last_closed_written_by_asset: dict[str, int] = {}

            original_output = streamer._output_streaming_data

            def patched_output(self, asset, current_value, timestamp_str, change_indicator):
                # Keep original console behavior
                try:
                    original_output(asset, current_value, timestamp_str, change_indicator)
                except Exception:
                    pass

                # Persist tick data (if enabled and mode permits)
                try:
                    if effective_save_ticks and not self.CANDLE_ONLY_MODE:
                        spm.add_tick(asset, timestamp_str, current_value)
                except Exception:
                    pass

                # Persist CLOSED candles (if enabled and mode permits)
                try:
                    if effective_save_candles and not self.TICK_ONLY_MODE:
                        candles = self.CANDLES.get(asset)
                        if candles and len(candles) >= 2:
                            closed_upto = len(candles) - 2  # last closed index
                            last = last_closed_written_by_asset.get(asset, -1)
                            if closed_upto > last:
                                # Resolve timeframe minutes from stream period (fallback 1)
                                tfm = int(self.PERIOD // 60) if getattr(self, "PERIOD", None) else 1
                                if tfm < 1:
                                    tfm = 1

                                for i in range(last + 1, closed_upto + 1):
                                    c = candles[i]
                                    spm.add_candle(
                                        asset=asset,
                                        timeframe_minutes=tfm,
                                        candle_ts=c[0],
                                        open_price=c[1],
                                        close_price=c[2],
                                        high_price=c[3],
                                        low_price=c[4],
                                    )
                                last_closed_written_by_asset[asset] = closed_upto
                except Exception:
                    pass

            # Bind the patched method
            streamer._output_streaming_data = types.MethodType(patched_output, streamer)

        # Start continuous streaming
        inputs = {"period": 60}  # 1 minute candles
        streamer.stream_continuous(qf.ctx, inputs)

    except Exception as e:
        print(f"❌ [STREAM] Data streaming failed: {e}")
        import traceback
        traceback.print_exc()


def test_tf_dropdown_capability():
    """Test the TF_dropdown_retract capability with toggle action."""
    try:
        print("\n🔄 [TF_TEST] Testing TF Dropdown Retract Capability...")

        # Create TF dropdown capability instance
        tf_dropdown = TF_Dropdown_Retract()

        # Test the toggle action (opens and closes dropdown)
        print("🎯 [TF_TEST] Executing toggle action (open then close dropdown)...")

        result = tf_dropdown.run(qf.ctx, {"action": "toggle"})

        if result.ok:
            data = result.data
            print("✅ [TF_TEST] TF Dropdown toggle completed successfully!")
            print("   📊 Results:")
            print(f"   📂 Opened: {data.get('opened', False)}")
            print(f"   📁 Closed: {data.get('closed', False)}")
            print(f"   🔄 Toggle Success: {data.get('toggle_success', False)}")

            if data.get('selector_used'):
                print(f"   🎯 Selector used: {data.get('selector_used')}")

            return True
        else:
            print(f"❌ [TF_TEST] TF Dropdown toggle failed: {result.error}")

            # Show additional error details if available
            data = result.data
            if data.get('attempts'):
                print("📋 Attempt details:")
                for attempt in data['attempts']:
                    status = "✅" if attempt.get('success') else "❌"
                    print(f"   {status} {attempt.get('selector', 'unknown')}: {attempt.get('success', False)}")

            return False

    except Exception as e:
        print(f"❌ [TF_TEST] TF Dropdown test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def tf_dropdown_test_session(
    stream_mode="both",  # "candle", "tick", or "both"
    asset_focus=True,   # True = focus on current asset, False = all assets
    csv_output=True,     # Enable CSV saving
    output_dir=None,
    test_delay=3,        # Seconds to wait after starting streaming before testing dropdown
    save_candles=False,
    save_ticks=False,
    candle_chunk_size=100,
    tick_chunk_size=1000
):
    """TF Dropdown test session with data streaming."""

    # Calculate correct output directory if not specified
    if output_dir is None:
        project_root = Path(__file__).parent.parent.parent
        output_dir = str(project_root / "data" / "Historical_Data" / "data_stream")

    print("🎯 QuantumFlux TF Dropdown Test Session")
    print("=" * 50)
    print(f"Mode: {stream_mode}")
    print(f"Asset Focus: {asset_focus}")
    print(f"CSV Output: {csv_output}")
    print(f"Output Directory: {output_dir}")
    print(f"Test Delay: {test_delay}s")

    try:
        # Attach to Chrome
        print("\n🔗 Attaching to Chrome session...")
        success, url = attach_chrome_session(port=9222, verbose=True)

        if not success:
            print(f"❌ Failed to attach: {url}")
            return

        print("✅ Connected successfully!")

        # Step 1: Start Data Streaming in Background Thread
        print("\n📈 Step 1: Starting Data Streaming (Background)...")

        streaming_thread = threading.Thread(
            target=start_data_streaming,
            args=(stream_mode, asset_focus, csv_output, output_dir, save_candles, save_ticks, candle_chunk_size, tick_chunk_size),
            daemon=True
        )
        streaming_thread.start()

        # Give streaming a moment to initialize
        time.sleep(2)

        # Step 2: Wait for streaming to stabilize, then test TF dropdown
        print(f"\n⏳ Step 2: Waiting {test_delay} seconds for streaming to stabilize...")
        time.sleep(test_delay)

        print("\n🔄 Step 3: Testing TF Dropdown Retract Capability...")
        test_success = test_tf_dropdown_capability()

        print("\n" + "="*50)
        if test_success:
            print("🎉 Session completed successfully!")
            print("✅ Data streaming is running in background")
            print("✅ TF Dropdown toggle test passed")
        else:
            print("⚠️ Session completed with issues")
            print("✅ Data streaming is running in background")
            print("❌ TF Dropdown toggle test failed")

        print("💡 Press Ctrl+C to stop data streaming")

        # Keep main thread alive while background thread runs
        try:
            while streaming_thread.is_alive():
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️ Received stop signal...")

    except KeyboardInterrupt:
        print("\n⏹️ Session stopped by user")
    except Exception as e:
        print(f"❌ Session failed: {e}")
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
    import argparse

    parser = argparse.ArgumentParser(description="TF Dropdown Open/Close Test Session")
    parser.add_argument("--mode", choices=["candle", "tick", "both"], default="both",
                       help="Streaming mode (default: both)")
    parser.add_argument("--asset-focus", action="store_true",
                       help="Focus on currently selected asset only (default: enabled)")
    parser.add_argument("--no-csv", action="store_true",
                       help="Disable CSV output")
    parser.add_argument("--output-dir", default=None,
                       help="CSV output directory (auto-calculated if not specified)")
    parser.add_argument("--test-delay", type=int, default=3,
                       help="Seconds to wait before testing dropdown (default: 3)")
    parser.add_argument("--save-candles", action="store_true",
                       help="Enable candle persistence (default: disabled)")
    parser.add_argument("--save-ticks", action="store_true",
                       help="Enable tick persistence (default: disabled)")
    parser.add_argument("--candle-chunk-size", type=int, default=100,
                       help="Closed candle rows per CSV file (default: 100)")
    parser.add_argument("--tick-chunk-size", type=int, default=1000,
                       help="Tick rows per CSV file (default: 1000)")

    args = parser.parse_args()

    # Run with defaults if no args provided, or use command line args
    tf_dropdown_test_session(
        stream_mode=args.mode,
        asset_focus=True if not args.asset_focus and len(sys.argv) == 1 else args.asset_focus,
        csv_output=not args.no_csv,
        output_dir=args.output_dir,
        test_delay=args.test_delay,
        save_candles=args.save_candles,
        save_ticks=args.save_ticks,
        candle_chunk_size=args.candle_chunk_size,
        tick_chunk_size=args.tick_chunk_size
    )
