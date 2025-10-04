"""
Favorites-based Batch Topdown Data Collector

Behavior:
- Optionally starts realtime data streaming in background when --start-stream is used (default OFF to avoid performance log contention), asset-focused.
- Refreshes favorites to only >= min_pct (default 92%) using FavoriteStarSelect.
- Scans favorites bar via FavoriteSelect and iterates each favorite asset.
- For each favorite:
  - For each timeframe label in the chosen stack (default 1m stack: H1 -> M15 -> M5 -> M1):
    - Select timeframe (no screenshots).
    - Immediately capture ONLY the batch historical candles triggered by the timeframe selection
      via capabilities/collect_historical_data.py, and save CSV.
- Screenshots are DISABLED in this session (ctx.debug=False and TopdownSelect save=False).
- Streaming persistence (tick/candle CSV) is OFF by default; opt-in via --save-candles/--save-ticks
  or environment overrides (QF_PERSIST, QF_PERSIST_CANDLES, QF_PERSIST_TICKS), injected locally
  using the same pattern as other sessions.

CSV routing for batch candles (per previous task):
- data/data_output/assets_data/data_collect/1H_candles
- data/data_output/assets_data/data_collect/15M_candles
- data/data_output/assets_data/data_collect/5M_candles
- data/data_output/assets_data/data_collect/1M_candles
Filenames: {ASSET}_{tf}_{YYYY_MM_DD_HH_MM_SS}.csv (e.g., AUDCHF_otc_15m_2025_09_28_20_23_23.csv)

Usage (PowerShell):
  # Default (asset-focused; 1m stack; no streaming persistence)
  python scripts\\custom_sessions\\favorites_batch_topdown_collect.py

  # Custom threshold and explicit labels
  python scripts\\custom_sessions\\favorites_batch_topdown_collect.py --min-pct 95 --labels H4 H1 M15 M5

  # Enable streaming and persist streaming data (opt-in)
  python scripts\\custom_sessions\\favorites_batch_topdown_collect.py --start-stream --save-candles --save-ticks --candle-chunk-size 200
"""

from __future__ import annotations

import os
import re
import sys
import time
import shutil
from pathlib import Path
from datetime import datetime
import types
from typing import List, Optional, Tuple

# Ensure project root (C:\QuFLX) is on sys.path so 'capabilities' package imports work
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Also ensure this script directory is on sys.path (for local imports like stream_persistence)
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Capabilities imports
from capabilities.data_streaming import RealtimeDataStreaming  # type: ignore
from capabilities.favorite_star_select import FavoriteStarSelect  # type: ignore
from capabilities.favorite_select import FavoriteSelect  # type: ignore
from capabilities.topdown_select import TopdownSelect  # type: ignore
from capabilities.collect_historical_data import CollectHistoricalData  # type: ignore

# Persistence injector
from stream_persistence import StreamPersistenceManager  # type: ignore

# Project attach helpers
from qf import attach_chrome_session
import qf  # qf.ctx and qf.driver are used


# Global timeframe hint (used by streaming persistence injection)
CURRENT_TIMEFRAME_MINUTES = 1


def set_current_timeframe_by_label(label: str):
    """Map timeframe label (e.g., H1, M15, M5, M1) to minutes for filename tagging and persistence alignment."""
    global CURRENT_TIMEFRAME_MINUTES
    m = {
        "H4": 240,
        "H1": 60,
        "M30": 30,
        "M15": 15,
        "M10": 10,
        "M5": 5,
        "M3": 3,
        "M2": 2,
        "M1": 1,
        "S30": 0.5,  # keep as 0.5 if ever used, but persistence uses int minutes >= 1
        "S15": 0.25,
        "S5": 0.0833,
    }
    key = (label or "").upper().strip()
    val = m.get(key)
    try:
        if val and val >= 1:
            CURRENT_TIMEFRAME_MINUTES = int(val)
    except Exception:
        pass


def label_to_minutes(label: str) -> Optional[int]:
    m = {
        "D1": 1440,
        "H4": 240,
        "H1": 60,
        "M30": 30,
        "M15": 15,
        "M10": 10,
        "M5": 5,
        "M3": 3,
        "M2": 2,
        "M1": 1,
        "S30": 0,  # ignore sub-1m for CSV routing here
        "S15": 0,
        "S5": 0,
    }
    return m.get((label or "").upper().strip())


def minutes_to_folder_suffix(minutes: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Map minutes to (folder_name, tf_suffix) for filenames.
    60 -> ("1H_candles", "1h")
    15 -> ("15M_candles", "15m")
    5  -> ("5M_candles",  "5m")
    1  -> ("1M_candles",  "1m")
    """
    table = {
        60: ("1H_candles", "1h"),
        30: ("30M_candles", "30m"),
        15: ("15M_candles", "15m"),
        10: ("10M_candles", "10m"),
        5: ("5M_candles", "5m"),
        3: ("3M_candles", "3m"),
        2: ("2M_candles", "2m"),
        1: ("1M_candles", "1m"),
    }
    return table.get(int(minutes), (None, None))


def sanitize_asset(name: str) -> str:
    return re.sub(r"[^\w\-_]", "_", str(name or "unknown"))


def normalize_asset_for_payload(label: str) -> str:
    """
    Normalize UI asset label to payload-friendly base symbol (e.g., 'USD/COP OTC' -> 'USDCOP').
    - Strip common OTC tokens before removing non-letters
    - Uppercase result
    """
    try:
        s = str(label or "")
        s = s.upper()
        # Remove common OTC tokens and underscores before cleaning
        for tok in [" OTC", "_OTC", "OTC"]:
            s = s.replace(tok, "")
        # Remove all non A-Z letters, collapse pairs like "EUR/USD" -> "EURUSD"
        s = re.sub(r"[^A-Z]", "", s)
        return s
    except Exception:
        return str(label or "").upper()


def start_data_streaming(
    stream_mode: str,
    asset_focus: bool,
    csv_output: bool,
    save_candles: bool = False,
    save_ticks: bool = False,
    candle_chunk_size: int = 100,
    tick_chunk_size: int = 1000,
):
    """Background streaming with optional persistence injection (disabled by default) and asset-focus mode."""
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

        # Do not use core CSV saving; use our persistence layer only if explicitly requested
        streamer.enable_csv_saving = False

        # Env overrides for quick toggles
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
                                # Resolve timeframe minutes (prefer CURRENT_TIMEFRAME_MINUTES)
                                try:
                                    tfm = int(CURRENT_TIMEFRAME_MINUTES)
                                except Exception:
                                    tfm = None
                                if not tfm or tfm < 1:
                                    tfm = int(self.PERIOD // 60) if getattr(self, "PERIOD", None) else 1

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

        # Start continuous streaming @ 1-minute period base
        inputs = {"period": 60}  # seconds
        streamer.stream_continuous(qf.ctx, inputs)

    except Exception as e:
        print(f"❌ [STREAM] Data streaming failed: {e}")
        import traceback
        traceback.print_exc()


def refresh_favorites(min_pct: int) -> None:
    """Use FavoriteStarSelect to ensure favorites bar has only >= min_pct assets."""
    try:
        cap = FavoriteStarSelect()
        res = cap.run(qf.ctx, {
            "min_pct": int(min_pct),
            "sweep_all": True,
            "unstar_below": True,
            "close_after": True,
            "dry_run": False,
        })
        if res.ok:
            counts = (res.data or {}).get("processed", {}).get("counts", {})
            print(f"⭐ [FAV] Refreshed favorites >= {min_pct}% (eligible={counts.get('eligible')}, starred={counts.get('star_clicked')})")
        else:
            print(f"⚠️ [FAV] FavoriteStarSelect failed: {res.error}")
    except Exception as e:
        print(f"❌ [FAV] Error refreshing favorites: {e}")


def get_favorite_labels(min_pct: int) -> List[str]:
    """Scan favorites bar and return eligible labels (>= min_pct)."""
    try:
        fav = FavoriteSelect()
        res = fav.run(qf.ctx, {"min_pct": int(min_pct), "select": None})
        if res.ok:
            labels = (res.data or {}).get("eligible", []) or []
            print(f"⭐ [FAV] Found {len(labels)} eligible favorites >= {min_pct}%")
            return labels
        else:
            print(f"⚠️ [FAV] FavoriteSelect failed: {res.error}")
            return []
    except Exception as e:
        print(f"❌ [FAV] Error scanning favorites: {e}")
        return []


def click_favorite_by_label(label: str) -> bool:
    """Click a favorite asset by label via FavoriteSelect helper."""
    try:
        fav = FavoriteSelect()
        ok = fav._click_favorite_by_label(qf.ctx, label)
        print(f"🎯 [FAV] Select '{label}': {'ok' if ok else 'not found'}")
        return bool(ok)
    except Exception as e:
        print(f"❌ [FAV] Error selecting favorite {label}: {e}")
        return False


def route_csv_to_timeframe_folder(csv_path: Optional[str], asset_label: str, tf_minutes: int) -> Optional[str]:
    """
    Move/rename the produced CSV into the timeframe-specific data_collect folder with our filename convention.
    Returns new absolute path if moved, else None.
    """
    if not csv_path or not os.path.isfile(csv_path):
        return None

    folder, tf_suffix = minutes_to_folder_suffix(tf_minutes)
    if not folder or not tf_suffix:
        return None

    # Prepare destination
    project_root = Path(__file__).parent.parent.parent
    dest_dir = project_root / "data" / "data_output" / "assets_data" / "data_collect" / folder
    dest_dir.mkdir(parents=True, exist_ok=True)

    # Build filename: {ASSET}_{tf}_{YYYY_MM_DD_HH_MM_SS}.csv
    asset_s = sanitize_asset(asset_label)
    ts = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    dest_name = f"{asset_s}_{tf_suffix}_{ts}.csv"
    dest_path = dest_dir / dest_name

    try:
        shutil.move(csv_path, str(dest_path))
        print(f"💾 [CSV] Moved -> {dest_path}")
        return str(dest_path)
    except Exception as e:
        print(f"⚠️ [CSV] Move failed ({e}); copying instead")
        try:
            shutil.copy2(csv_path, str(dest_path))
            print(f"💾 [CSV] Copied -> {dest_path}")
            return str(dest_path)
        except Exception as e2:
            print(f"❌ [CSV] Copy failed: {e2}")
            return None


def capture_batch_candles(asset_label: str, tf_minutes: int) -> Optional[str]:
    """
    Invoke CollectHistoricalData for the given asset/timeframe to capture only the batch 'history' payload
    generated at timeframe selection. Returns routed CSV path or None.
    """
    try:
        collector = CollectHistoricalData()
        # Normalize to payload-compatible symbol, e.g., 'USD/COP OTC' -> 'USDCOP'
        asset_for_payload = normalize_asset_for_payload(asset_label)
        res = collector.run(qf.ctx, {
            "asset": asset_for_payload,
            "timeframe": int(tf_minutes),
        })

        if not res.ok:
            print(f"⚠️ [BATCH] CollectHistoricalData failed for {asset_label} {tf_minutes}m: {res.error}")
            return None

        # The capability writes CSV under ./historical_data_output; fetch from result
        csv_path = (res.data or {}).get("csv_artifact_path") or ""
        if not csv_path or not os.path.isfile(csv_path):
            # Try to discover most recent CSV in the default folder as fallback
            fallback_dir = Path.cwd() / "historical_data_output"
            if fallback_dir.exists():
                try:
                    latest = max(
                        (p for p in fallback_dir.glob("*.csv") if p.is_file()),
                        key=lambda p: p.stat().st_mtime,
                        default=None
                    )
                    csv_path = str(latest) if latest else ""
                except Exception:
                    csv_path = ""

        return route_csv_to_timeframe_folder(csv_path, asset_label, tf_minutes)

    except Exception as e:
        print(f"❌ [BATCH] Error capturing batch candles for {asset_label} {tf_minutes}m: {e}")
        return None


def run_topdown_for_asset(asset_label: str, stack: str, labels_override: Optional[List[str]], delay_ms: int = 300, tf_wait_s: float = 5.0) -> None:
    """
    For the selected favorite asset, iterate the timeframe labels:
     - open timeframe dropdown once, click label, close dropdown
     - set CURRENT_TIMEFRAME_MINUTES
     - capture only the batch history via CollectHistoricalData
     - route CSV to timeframe folder
    """
    try:
        td = TopdownSelect()
        sequences = {
            "1m": ["H1", "M15", "M5", "M1"],
            "5m": ["H4", "H1", "M15", "M5"],
        }
        labels = labels_override or sequences.get(stack, ["H1", "M15", "M5", "M1"])

        # Open dropdown once initially
        open_meta = td._open_timeframe_menu(qf.ctx, None)
        opening_button = open_meta.get("opening_button")
        if not open_meta.get("opened"):
            print("⚠️ [TOPDOWN] Could not open timeframe dropdown initially; proceeding with click attempts")

        for i, lab in enumerate(labels):
            print(f"\n🔄 [TOPDOWN] {asset_label}: {lab}")
            clicked, strategy, sel = td._click_timeframe(qf.ctx, lab)
            if not clicked:
                print(f"❌ [TOPDOWN] Click failed for label {lab} (strategy={strategy} sel={sel})")
                continue

            # Update CURRENT_TIMEFRAME_MINUTES so persistence (if enabled) tags properly
            set_current_timeframe_by_label(lab)

            # Close dropdown after selection
            try:
                ok_close = td._toggle_close_dropdown(qf.ctx, opening_button)
                if not ok_close:
                    print("⚠️ [TOPDOWN] Dropdown close not confirmed; continuing")
            except Exception as e:
                print(f"⚠️ [TOPDOWN] Close error: {e}")

            # Allow UI to settle minimally
            time.sleep(max(0.0, tf_wait_s))

            # Map to minutes and capture batch candles
            tf_min = label_to_minutes(lab)
            if tf_min and tf_min >= 1:
                _ = capture_batch_candles(asset_label, tf_min)

            # Small pacing between labels
            if i < len(labels) - 1:
                time.sleep(max(0, delay_ms) / 1000.0)

            # Re-open dropdown for next label if needed
            if i < len(labels) - 1:
                open_meta = td._open_timeframe_menu(qf.ctx, None)
                opening_button = open_meta.get("opening_button")

        print(f"\n✅ [TOPDOWN] Completed for asset {asset_label}")

    except Exception as e:
        print(f"❌ [TOPDOWN] Asset flow failed for {asset_label}: {e}")


def run_session(
    min_pct: int = 92,
    stream_mode: str = "both",
    asset_focus: bool = True,
    save_candles: bool = False,
    save_ticks: bool = False,
    candle_chunk_size: int = 100,
    tick_chunk_size: int = 1000,
    start_stream: bool = False,
    stack: str = "1m",
    labels_override: Optional[List[str]] = None,
    delay_ms: int = 300,
    tf_wait_s: float = 1.0,
):
    """
    Main session flow:
      - Attach Chrome
      - Start background streaming (asset-focused)
      - Refresh favorites to >= min_pct and enumerate
      - Iterate each favorite: click it, perform topdown labels, capture batch candles
    """
    # Attach to Chrome (persistent debugging port 9222)
    print("🔗 Attaching to Chrome (9222)...")
    ok, info = attach_chrome_session(port=9222, verbose=True)
    if not ok:
        print(f"❌ Attach failed: {info}")
        return
    print("✅ Attached")

    # Start streaming in background (daemon), optional to avoid performance log contention during batch capture
    if start_stream:
        import threading
        streaming_thread = threading.Thread(
            target=start_data_streaming,
            args=(stream_mode, asset_focus, False, save_candles, save_ticks, candle_chunk_size, tick_chunk_size),
            daemon=True
        )
        streaming_thread.start()
        time.sleep(2)  # brief warm-up

    # Refresh and get favorites
    refresh_favorites(min_pct=min_pct)
    labels = get_favorite_labels(min_pct=min_pct)
    if not labels:
        print("⚠️ No eligible favorites found; exiting.")
        return

    # Iterate each favorite
    for fav_label in labels:
        print(f"\n==============================")
        print(f"🎯 Processing favorite: {fav_label}")
        if not click_favorite_by_label(fav_label):
            print(f"⚠️ Skipping {fav_label} (click failed)")
            continue
        run_topdown_for_asset(fav_label, stack, labels_override, delay_ms, tf_wait_s)

    print("\n🎉 Session completed. Background streaming will terminate with the process.")
    # We do not join the streaming thread (daemon); exiting main ends it.


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Favorites-based Batch Topdown Data Collector")
    parser.add_argument("--min-pct", type=int, default=92, help="Minimum payout percentage for favorites (default 92)")
    parser.add_argument("--mode", choices=["candle", "tick", "both"], default="both", help="Streaming mode (default both)")
    parser.add_argument("--asset-focus", action="store_true", help="Asset focus mode for stream (default True)")
    parser.add_argument("--no-asset-focus", action="store_true", help="Disable asset focus (default: enabled)")
    parser.add_argument("--save-candles", action="store_true", help="Enable stream persistence: closed candles (opt-in)")
    parser.add_argument("--save-ticks", action="store_true", help="Enable stream persistence: ticks (opt-in)")
    parser.add_argument("--candle-chunk-size", type=int, default=100, help="Closed candle rows per CSV (default 100)")
    parser.add_argument("--tick-chunk-size", type=int, default=1000, help="Tick rows per CSV (default 1000)")
    parser.add_argument("--stack", choices=["1m", "5m"], default="1m", help="Topdown stack (default 1m)")
    parser.add_argument("--labels", nargs="+", help="Explicit timeframe labels, e.g. H4 H1 M15 M5")
    parser.add_argument("--delay-ms", type=int, default=300, help="Delay between timeframe selections (ms)")
    parser.add_argument("--tf-wait-s", type=float, default=5.0, help="Wait after timeframe select before capture (s)")
    parser.add_argument("--start-stream", action="store_true", help="Start background realtime streaming (may compete for performance logs)")

    args = parser.parse_args()

    # Default behavior: asset focus enabled. Allow explicit disable with --no-asset-focus.
    asset_focus_flag = not getattr(args, "no_asset_focus", False)

    run_session(
        min_pct=args.min_pct,
        stream_mode=args.mode,
        asset_focus=asset_focus_flag,
        save_candles=args.save_candles,
        save_ticks=args.save_ticks,
        candle_chunk_size=args.candle_chunk_size,
        tick_chunk_size=args.tick_chunk_size,
        stack=args.stack,
        labels_override=args.labels,
        delay_ms=args.delay_ms,
        tf_wait_s=args.tf_wait_s,
        start_stream=args.start_stream,
    )
