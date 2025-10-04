"""
Specialized Data Streaming Session
Streams tick and candle data with CSV export to data/Historical_Data/data_stream/
"""

import sys
import os
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

def data_streaming_session(
    stream_mode="both",  # "candle", "tick", or "both"
    asset_focus=True,   # True = focus on current asset, False = all assets
    csv_output=True,     # Enable CSV saving
    output_dir=None,
    save_candles=True,
    save_ticks=True,
    candle_chunk_size=100,
    tick_chunk_size=1000
):
    """Specialized data streaming session."""

    # Calculate correct output directory if not specified
    if output_dir is None:
        project_root = Path(__file__).parent.parent.parent
        output_dir = str(project_root / "data" / "Historical_Data" / "data_stream")

    print("🎯 QuantumFlux Data Streaming Session")
    print("=" * 50)
    print(f"Mode: {stream_mode}")
    print(f"Asset Focus: {asset_focus}")
    print(f"CSV Output: {csv_output}")
    print(f"Output Directory: {output_dir}")
    
    try:
        # Attach to Chrome
        print("\n🔗 Attaching to Chrome session...")
        success, url = attach_chrome_session(port=9222, verbose=True)
        
        if not success:
            print(f"❌ Failed to attach: {url}")
            return
        
        print("✅ Connected successfully!")
        
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
                if save_ticks and not self.CANDLE_ONLY_MODE:
                    spm.add_tick(asset, timestamp_str, current_value)
            except Exception:
                pass

            # Persist CLOSED candles (if enabled and mode permits)
            try:
                if save_candles and not self.TICK_ONLY_MODE:
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
        print(f"\n🚀 Starting {stream_mode} data streaming...")
        print("💡 Press Ctrl+C to stop")

        inputs = {"period": 60}  # 1 minute candles
        streamer.stream_continuous(qf.ctx, inputs)
        
    except KeyboardInterrupt:
        print("\n⏹️ Streaming stopped by user")
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

    parser = argparse.ArgumentParser(description="Specialized Data Streaming Session")
    parser.add_argument("--mode", choices=["candle", "tick", "both"], default="both",
                       help="Streaming mode (default: both)")
    parser.add_argument("--asset-focus", action="store_true",
                       help="Focus on currently selected asset only (default: enabled)")
    parser.add_argument("--no-csv", action="store_true",
                       help="Disable CSV output")
    parser.add_argument("--output-dir", default="data/Historical_Data/data_stream",
                       help="CSV output directory")
    parser.add_argument("--no-save-candles", action="store_true",
                       help="Disable candle persistence (default: enabled)")
    parser.add_argument("--no-save-ticks", action="store_true",
                       help="Disable tick persistence (default: enabled)")
    parser.add_argument("--candle-chunk-size", type=int, default=100,
                       help="Closed candle rows per CSV file (default: 100)")
    parser.add_argument("--tick-chunk-size", type=int, default=1000,
                       help="Tick rows per CSV file (default: 1000)")

    args = parser.parse_args()

    # Run with defaults if no args provided, or use command line args
    data_streaming_session(
        stream_mode=args.mode,
        asset_focus=True if not args.asset_focus and len(sys.argv) == 1 else args.asset_focus,
        csv_output=not args.no_csv,
        output_dir=args.output_dir,
        save_candles=not args.no_save_candles,
        save_ticks=not args.no_save_ticks,
        candle_chunk_size=args.candle_chunk_size,
        tick_chunk_size=args.tick_chunk_size
    )
