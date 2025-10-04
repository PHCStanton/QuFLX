#!/usr/bin/env python3
"""
Practical script to convert your actual CSV files from UTC+2 to UTC+0.

This script demonstrates how to use the timestamp_convert_utc capability
to convert your specific CSV files mentioned in the request.
"""

from __future__ import annotations

import os
import sys

# Import the timestamp conversion capability
try:
    from capabilities.timestamp_convert_utc import TimestampConvertUTC
    from capabilities.base import Ctx
    print("✅ Successfully imported TimestampConvertUTC capability")
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


def convert_1m_candles():
    """Convert 1-minute candle CSV files from UTC+2 to UTC+0."""
    print("\n🔄 Converting 1M candle files from UTC+2 to UTC+0")
    print("-" * 50)

    source_dir = "data/data_output/assets_data/data_collect/1M_candles"
    target_dir = "data/data_output/assets_data/data_collect/1M_candles_utc"

    # Create mock context (in real usage, you'd use actual driver context)
    class MockCtx:
        def __init__(self):
            self.verbose = True
            self.debug = True
            self.artifacts_root = "data_output"

    ctx = MockCtx()

    # Initialize converter
    converter = TimestampConvertUTC()

    # Convert the files
    result = converter.run(ctx, {
        "source_directory": source_dir,
        "target_directory": target_dir,
        "file_pattern": "BHDCNY_otc_1m_*.csv",  # Your specific file pattern
        "timestamp_column": "timestamp",
        "source_timezone": "UTC+2",
        "target_timezone": "UTC+0",
        "backup_original": True
    })

    # Display results
    if result.ok:
        print("✅ 1M candles conversion completed successfully!")
        print(f"  📁 Files processed: {result.data.get('total_files_processed', 0)}")
        print(f"  📊 Rows converted: {result.data.get('total_rows_converted', 0)}")
        print(f"  ❌ Errors: {result.data.get('total_conversion_errors', 0)}")

        if result.data.get('conversion_results'):
            print("\n📋 Conversion Details:")
            for file_result in result.data['conversion_results']:
                print(f"  {os.path.basename(file_result['original_file'])}")
                print(f"    → {os.path.basename(file_result['converted_file'])}")
                print(f"    Rows: {file_result['rows_converted']}, Errors: {file_result['conversion_errors']}")
    else:
        print(f"❌ Conversion failed: {result.error}")

    return result.ok


def convert_15m_candles():
    """Convert 15-minute candle CSV files from UTC+2 to UTC+0."""
    print("\n🔄 Converting 15M candle files from UTC+2 to UTC+0")
    print("-" * 51)

    source_dir = "data/data_output/assets_data/data_collect/15M_candles"
    target_dir = "data/data_output/assets_data/data_collect/15M_candles_utc"

    # Create mock context
    class MockCtx:
        def __init__(self):
            self.verbose = True
            self.debug = True
            self.artifacts_root = "data_output"

    ctx = MockCtx()

    # Initialize converter
    converter = TimestampConvertUTC()

    # Convert the files
    result = converter.run(ctx, {
        "source_directory": source_dir,
        "target_directory": target_dir,
        "file_pattern": "BHDCNY_otc_15m_*.csv",  # Your specific file pattern
        "timestamp_column": "timestamp",
        "source_timezone": "UTC+2",
        "target_timezone": "UTC+0",
        "backup_original": True
    })

    # Display results
    if result.ok:
        print("✅ 15M candles conversion completed successfully!")
        print(f"  📁 Files processed: {result.data.get('total_files_processed', 0)}")
        print(f"  📊 Rows converted: {result.data.get('total_rows_converted', 0)}")
        print(f"  ❌ Errors: {result.data.get('total_conversion_errors', 0)}")

        if result.data.get('conversion_results'):
            print("\n📋 Conversion Details:")
            for file_result in result.data['conversion_results']:
                print(f"  {os.path.basename(file_result['original_file'])}")
                print(f"    → {os.path.basename(file_result['converted_file'])}")
                print(f"    Rows: {file_result['rows_converted']}, Errors: {file_result['conversion_errors']}")
    else:
        print(f"❌ Conversion failed: {result.error}")

    return result.ok


def show_sample_conversion():
    """Show what the conversion will look like with your actual data."""
    print("\n📊 Sample Conversion Preview:")
    print("-" * 30)

    print("Your original CSV files have timestamps like:")
    print("  timestamp,open,close,high,low")
    print("  2025-09-28 21:22:00,18.839,18.84072,18.84072,18.83872")
    print("  2025-09-28 21:23:00,18.8406,18.84042,18.84143,18.84029")
    print()

    print("After conversion to UTC+0, they will be:")
    print("  timestamp,open,close,high,low")
    print("  2025-09-28 19:22:00,18.839,18.84072,18.84072,18.83872")
    print("  2025-09-28 19:23:00,18.8406,18.84042,18.84143,18.84029")
    print()

    print("💡 This converts your UTC+2 timestamps to standard UTC+0")
    print("   for consistency with other trading systems.")


def main():
    """Main conversion function."""
    print("🕐 CSV Timestamp Conversion: UTC+2 to UTC+0")
    print("=" * 45)

    # Show what we're going to do
    show_sample_conversion()

    # Ask user if they want to proceed
    print("\n⚠️  Ready to convert your actual CSV files?")
    print("   This will create new files with '_utc_converted' suffix")
    print("   Original files will be preserved.")

    try:
        proceed = input("\nProceed with conversion? (y/N): ").strip().lower()
        if proceed != 'y':
            print("Conversion cancelled.")
            return
    except KeyboardInterrupt:
        print("\nConversion cancelled.")
        return

    # Perform the conversions
    print("\n🚀 Starting conversions...")

    success_1m = convert_1m_candles()
    success_15m = convert_15m_candles()

    # Summary
    print("\n" + "=" * 45)
    if success_1m and success_15m:
        print("🎉 All conversions completed successfully!")

        print("\n📁 Converted Files Created:")
        print("  📂 data/data_output/assets_data/data_collect/1M_candles_utc/")
        print("  📂 data/data_output/assets_data/data_collect/15M_candles_utc/")

        print("\n💡 Next Steps:")
        print("  1. Verify the converted files look correct")
        print("  2. Update your data processing pipelines to use the UTC+0 files")
        print("  3. Consider archiving or removing the original UTC+2 files")

    else:
        print("⚠️ Some conversions failed. Please check the error messages above.")
        sys.exit(1)


if __name__ == "__main__":
    main()