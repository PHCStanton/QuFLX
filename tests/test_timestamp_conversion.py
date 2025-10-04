#!/usr/bin/env python3
"""
Test script for the timestamp conversion capability.

This script demonstrates how to use the new timestamp_convert_utc capability
to convert CSV files with UTC+2 timestamps to UTC+0.
"""

from __future__ import annotations

import os
import tempfile
import csv
from datetime import datetime

# Import the new capability
try:
    from capabilities.timestamp_convert_utc import TimestampConvertUTC
    from capabilities.base import Ctx
    print("✅ Successfully imported TimestampConvertUTC capability")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)


def create_sample_csv_with_utc2_timestamps(filename: str):
    """Create a sample CSV file with UTC+2 timestamps for testing."""
    # Sample data similar to the provided CSV files
    sample_data = [
        ["timestamp", "open", "close", "high", "low"],
        ["2025-09-28 21:22:00", "18.839", "18.84072", "18.84072", "18.83872"],
        ["2025-09-28 21:23:00", "18.8406", "18.84042", "18.84143", "18.84029"],
        ["2025-09-28 21:24:00", "18.84042", "18.84092", "18.84147", "18.84041"],
        ["2025-09-28 21:25:00", "18.84092", "18.84238", "18.84249", "18.84092"],
    ]

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(sample_data)

    print(f"📄 Created sample CSV: {filename}")
    return filename


def test_timestamp_conversion():
    """Test the timestamp conversion functionality."""
    print("\n🧪 Testing Timestamp Conversion Capability")
    print("-" * 45)

    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = os.path.join(temp_dir, "source")
        target_dir = os.path.join(temp_dir, "target")

        os.makedirs(source_dir)
        os.makedirs(target_dir)

        # Create sample CSV files
        sample_file1 = create_sample_csv_with_utc2_timestamps(
            os.path.join(source_dir, "test_data_1m.csv")
        )
        sample_file2 = create_sample_csv_with_utc2_timestamps(
            os.path.join(source_dir, "test_data_15m.csv")
        )

        # Create mock context
        class MockCtx:
            def __init__(self):
                self.verbose = True
                self.debug = True
                self.artifacts_root = temp_dir

        ctx = MockCtx()

        # Test the conversion
        converter = TimestampConvertUTC()
        result = converter.run(ctx, {
            "source_directory": source_dir,
            "target_directory": target_dir,
            "file_pattern": "*.csv",
            "timestamp_column": "timestamp",
            "source_timezone": "UTC+2",
            "target_timezone": "UTC+0",
            "backup_original": True
        })

        # Display results
        print("\n📊 Conversion Results:")
        print(f"  ✅ Success: {result.ok}")
        print(f"  📁 Files processed: {result.data.get('total_files_processed', 0)}")
        print(f"  📊 Rows converted: {result.data.get('total_rows_converted', 0)}")
        print(f"  ❌ Errors: {result.data.get('total_conversion_errors', 0)}")

        if result.data.get('conversion_results'):
            print("\n📋 Detailed Results:")
            for file_result in result.data['conversion_results']:
                print(f"  Original: {os.path.basename(file_result['original_file'])}")
                print(f"  Converted: {os.path.basename(file_result['converted_file'])}")
                print(f"  Rows: {file_result['rows_converted']}, Errors: {file_result['conversion_errors']}")

        # Verify conversion by reading one of the converted files
        if result.ok and result.data.get('conversion_results'):
            first_result = result.data['conversion_results'][0]
            converted_file = os.path.join(target_dir, os.path.basename(first_result['converted_file']))

            if os.path.exists(converted_file):
                print(f"\n🔍 Verifying conversion in: {os.path.basename(converted_file)}")
                with open(converted_file, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    rows = list(reader)

                    print("  First few converted timestamps:")
                    for i, row in enumerate(rows[1:4]):  # Skip header, show first 3 data rows
                        original_time = ["2025-09-28 21:22:00", "2025-09-28 21:23:00", "2025-09-28 21:24:00"][i]
                        converted_time = row[0]
                        print(f"    {original_time} (UTC+2) → {converted_time} (UTC+0)")

        return result.ok


def demonstrate_usage():
    """Show how to use the timestamp conversion capability."""
    print("\n📚 Usage Examples:")
    print()

    print("1️⃣ Basic conversion from command line:")
    print("""
    python capabilities/timestamp_convert_utc.py \\
        --source-dir "data/data_output/assets_data/data_collect/1M_candles" \\
        --target-dir "data/data_output/assets_data/data_collect/1M_candles_utc" \\
        --pattern "*.csv" \\
        --source-tz "UTC+2" \\
        --target-tz "UTC+0" \\
        --verbose
    """)

    print("2️⃣ Using as a capability in automation:")
    print("""
    from capabilities.timestamp_convert_utc import TimestampConvertUTC
    from capabilities.base import Ctx

    # Initialize
    converter = TimestampConvertUTC()
    ctx = Ctx(driver, artifacts_root="data_output", debug=True, verbose=True)

    # Convert timestamps
    result = converter.run(ctx, {
        "source_directory": "data/data_output/assets_data/data_collect/1M_candles",
        "target_directory": "data/data_output/assets_data/data_collect/1M_candles_utc",
        "file_pattern": "BHDCNY_otc_1m_*.csv",
        "timestamp_column": "timestamp",
        "source_timezone": "UTC+2",
        "target_timezone": "UTC+0"
    })

    if result.ok:
        print(f"✅ Converted {result.data['total_files_processed']} files")
    """)

    print("3️⃣ Converting 15-minute candles:")
    print("""
    result = converter.run(ctx, {
        "source_directory": "data/data_output/assets_data/data_collect/15M_candles",
        "target_directory": "data/data_output/assets_data/data_collect/15M_candles_utc",
        "file_pattern": "BHDCNY_otc_15m_*.csv",
        "timestamp_column": "timestamp",
        "source_timezone": "UTC+2",
        "target_timezone": "UTC+0"
    })
    """)


def show_conversion_examples():
    """Show examples of timestamp conversions."""
    print("\n🔄 Timestamp Conversion Examples:")
    print("-" * 35)

    examples = [
        ("2025-09-28 21:22:00", "2025-09-28 19:22:00"),
        ("2025-09-28 21:23:00", "2025-09-28 19:23:00"),
        ("2025-09-28 22:00:00", "2025-09-28 20:00:00"),
        ("2025-09-28 23:59:59", "2025-09-28 21:59:59"),
    ]

    print("UTC+2 (Original)    →    UTC+0 (Converted)")
    print("-" * 45)
    for original, converted in examples:
        print(f"{original}    →    {converted}")


def main():
    """Main test function."""
    print("🧪 Testing Timestamp Conversion Capability")
    print("=" * 50)

    # Show conversion examples
    show_conversion_examples()

    # Test the conversion functionality
    success = test_timestamp_conversion()

    # Show usage examples
    demonstrate_usage()

    # Summary
    print("\n" + "=" * 50)
    if success:
        print("🎉 Timestamp conversion test completed successfully!")
        print("The capability is ready to convert your CSV files from UTC+2 to UTC+0.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        exit(1)

    print("\n💡 Next Steps:")
    print("  1. Use the command-line interface to convert your existing CSV files")
    print("  2. Integrate the capability into your data processing pipelines")
    print("  3. Convert both 1M and 15M candle data to UTC+0 for consistency")


if __name__ == "__main__":
    main()