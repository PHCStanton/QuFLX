import os
from pathlib import Path
import time

# Import the module under test
import scripts.custom_sessions.favorites_batch_topdown_collect as mod


def test_normalize_asset_for_payload():
    assert mod.normalize_asset_for_payload("USD/COP OTC") == "USDCOP"
    assert mod.normalize_asset_for_payload("EUR/USD") == "EURUSD"
    assert mod.normalize_asset_for_payload("gbp_jpy_otc") == "GBPJPY"
    assert mod.normalize_asset_for_payload("AUDCAD") == "AUDCAD"


def test_minutes_to_folder_suffix_and_label_to_minutes():
    assert mod.label_to_minutes("H1") == 60
    assert mod.minutes_to_folder_suffix(60)[0] == "1H_candles"
    assert mod.label_to_minutes("M5") == 5
    assert mod.minutes_to_folder_suffix(5)[0] == "5M_candles"
    assert mod.label_to_minutes("M1") == 1
    assert mod.minutes_to_folder_suffix(1)[0] == "1M_candles"


def test_route_csv_to_timeframe_folder(tmp_path):
    # Create a temporary CSV file to simulate output from CollectHistoricalData
    tmp_csv = tmp_path / "temp_history.csv"
    tmp_csv.write_text("timestamp,open,high,low,close,asset,period\n")

    # Route to 15m folder
    dest = mod.route_csv_to_timeframe_folder(str(tmp_csv), "EURUSD OTC", 15)
    assert dest is not None, "Expected destination path to be returned"
    dest_path = Path(dest)
    assert dest_path.is_file(), f"Expected moved file to exist at {dest_path}"
    # Check it landed under project_root/data/data_output/assets_data/data_collect/15M_candles
    assert "data_collect" in dest
    assert "15M_candles" in dest
    assert "EURUSD_OTC_15m_" in dest_path.name


def test_capture_batch_candles_monkeypatched(tmp_path, monkeypatch):
    # Prepare a fake CSV produced by the collector
    produced_csv = tmp_path / "collector_output.csv"
    produced_csv.write_text("timestamp,open,high,low,close,asset,period\n")

    # Fake result object
    class _FakeRes:
        def __init__(self, ok=True, data=None):
            self.ok = ok
            self.data = data or {}
            self.error = None
            self.artifacts = ()

    # Fake CollectHistoricalData that returns our temp CSV path
    class _FakeCollectHistoricalData:
        def run(self, ctx, inputs):
            # Ensure inputs are what we expect
            assert "asset" in inputs
            assert "timeframe" in inputs
            return _FakeRes(ok=True, data={"csv_artifact_path": str(produced_csv)})

    # Monkeypatch the class in the module
    monkeypatch.setattr(mod, "CollectHistoricalData", _FakeCollectHistoricalData)

    # Invoke capture for 5 minutes timeframe
    dest = mod.capture_batch_candles("EUR/USD OTC", 5)
    assert dest is not None, "Expected destination path from capture_batch_candles"
    dest_path = Path(dest)
    assert dest_path.is_file(), f"Expected routed CSV to exist at {dest_path}"
    assert "5M_candles" in str(dest_path.parent)
    assert "EUR_USD_OTC_5m_" in dest_path.name or "EURUSD_OTC_5m_" in dest_path.name
