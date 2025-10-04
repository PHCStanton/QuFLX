"""
Chunked CSV persistence for realtime streaming (ticks and candles), without modifying core capability.

- Tick files: rotate every N (default 1000) rows
- Candle files: write CLOSED candles only, rotate every N (default 100) rows
- Destination directories (per user requirement):
  - Candles: data/data_output/assets_data/realtime_stream/1M_candle_data
  - Ticks:   data/data_output/assets_data/realtime_stream/1M_tick_data
"""

from __future__ import annotations

import csv
import os
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple, List, Optional


def sanitize_asset(name: str) -> str:
    """Sanitize asset string for safe filenames."""
    return re.sub(r"[^\w\-_]", "_", str(name or "unknown"))


class RotatingCSVWriter:
    """
    Simple rotating CSV writer:
    - Writes header once per part file
    - Appends rows and rotates to next part after chunk_size rows
    - Opens/closes the file on every write to be crash-safe
    """

    def __init__(self, dir_path: Path, file_prefix: str, header: List[str], chunk_size: int) -> None:
        self.dir_path = Path(dir_path)
        self.file_prefix = file_prefix
        self.header = header
        self.chunk_size = max(1, int(chunk_size))
        self.part_index = 1
        self.rows_in_current = 0
        self._lock = threading.Lock()

        self.dir_path.mkdir(parents=True, exist_ok=True)

    @property
    def _current_file(self) -> Path:
        return self.dir_path / f"{self.file_prefix}_part{self.part_index:03d}.csv"

    def write_row(self, row: List[object]) -> None:
        with self._lock:
            # Rotate if current part is full
            if self.rows_in_current >= self.chunk_size:
                self.part_index += 1
                self.rows_in_current = 0

            file_path = self._current_file
            is_new_file = not file_path.exists() or file_path.stat().st_size == 0

            # Open, write header if needed, then append row
            with open(file_path, mode="a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                if is_new_file:
                    writer.writerow(self.header)
                writer.writerow(row)
                self.rows_in_current += 1


class StreamPersistenceManager:
    """
    Manages rotating CSV writers for ticks and candles.
    - Candle writers keyed by (asset, timeframe_minutes)
    - Tick writers keyed by asset
    """

    def __init__(
        self,
        candle_dir: Path | str,
        tick_dir: Path | str,
        candle_chunk_size: int = 100,
        tick_chunk_size: int = 1000,
        session_ts: Optional[str] = None,
    ) -> None:
        self.candle_dir = Path(candle_dir)
        self.tick_dir = Path(tick_dir)
        self.candle_chunk_size = max(1, int(candle_chunk_size))
        self.tick_chunk_size = max(1, int(tick_chunk_size))
        self.session_ts = session_ts or datetime.utcnow().strftime("%Y_%m_%d_%H_%M_%S")

        # Writers
        self._tick_writers: Dict[str, RotatingCSVWriter] = {}
        self._candle_writers: Dict[Tuple[str, int], RotatingCSVWriter] = {}

        # Ensure directories exist
        self.candle_dir.mkdir(parents=True, exist_ok=True)
        self.tick_dir.mkdir(parents=True, exist_ok=True)

        # Locks for writer creation
        self._tick_lock = threading.Lock()
        self._candle_lock = threading.Lock()

    # ---- Tick persistence ----
    def _get_tick_writer(self, asset: str) -> RotatingCSVWriter:
        key = asset
        if key in self._tick_writers:
            return self._tick_writers[key]

        with self._tick_lock:
            if key in self._tick_writers:
                return self._tick_writers[key]

            asset_s = sanitize_asset(asset)
            prefix = f"{asset_s}_ticks_{self.session_ts}"
            writer = RotatingCSVWriter(
                dir_path=self.tick_dir,
                file_prefix=prefix,
                header=["timestamp", "asset", "price"],
                chunk_size=self.tick_chunk_size,
            )
            self._tick_writers[key] = writer
            return writer

    def add_tick(self, asset: str, timestamp_str: str, price: object) -> None:
        writer = self._get_tick_writer(asset)
        writer.write_row([timestamp_str, asset, price])

    # ---- Candle persistence (closed candles only) ----
    def _get_candle_writer(self, asset: str, timeframe_minutes: int) -> RotatingCSVWriter:
        tf = max(1, int(timeframe_minutes or 1))
        key = (asset, tf)
        if key in self._candle_writers:
            return self._candle_writers[key]

        with self._candle_lock:
            if key in self._candle_writers:
                return self._candle_writers[key]

            asset_s = sanitize_asset(asset)
            prefix = f"{asset_s}_{tf}m_{self.session_ts}"
            writer = RotatingCSVWriter(
                dir_path=self.candle_dir,
                file_prefix=prefix,
                header=["timestamp", "open", "close", "high", "low"],
                chunk_size=self.candle_chunk_size,
            )
            self._candle_writers[key] = writer
            return writer

    @staticmethod
    def _fmt_utc(ts: object) -> str:
        try:
            if isinstance(ts, (int, float)):
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            elif isinstance(ts, str) and ts.isdigit():
                dt = datetime.fromtimestamp(float(ts), tz=timezone.utc)
            else:
                # Fallback: try parsing as ISO, else use now()
                try:
                    dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                except Exception:
                    dt = datetime.now(tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M:%SZ")
        except Exception:
            return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")

    def add_candle(
        self,
        asset: str,
        timeframe_minutes: int,
        candle_ts: object,
        open_price: object,
        close_price: object,
        high_price: object,
        low_price: object,
    ) -> None:
        writer = self._get_candle_writer(asset, timeframe_minutes)
        ts_str = self._fmt_utc(candle_ts)
        writer.write_row([ts_str, open_price, close_price, high_price, low_price])
