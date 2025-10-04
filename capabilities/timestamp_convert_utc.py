from __future__ import annotations

from typing import Any, Dict, Optional, List, Tuple
import os
import csv
import glob
from datetime import datetime, timedelta
from dataclasses import dataclass

from .base import Ctx, CapResult, Capability, add_utils_to_syspath, save_json, timestamp, join_artifact, ensure_dir


@dataclass
class ConversionResult:
    """Result of timestamp conversion for a single file."""
    original_file: str
    converted_file: str
    original_timezone: str
    target_timezone: str
    rows_converted: int
    conversion_errors: int
    start_timestamp: str
    end_timestamp: str


class TimestampConvertUTC(Capability):
    """
    Capability: Convert timestamps from UTC+2 to UTC+0 in CSV files.

    Interface:
      run(ctx, {
        "source_directory": str,           # Directory containing CSV files with UTC+2 timestamps
        "target_directory": str,           # Directory to save converted UTC+0 files
        "file_pattern": str = "*.csv",     # Pattern to match CSV files
        "timestamp_column": str = "timestamp",  # Name of timestamp column
        "source_timezone": str = "UTC+2",  # Source timezone
        "target_timezone": str = "UTC+0",  # Target timezone
        "backup_original": bool = True,    # Whether to keep original files
      })

    Behavior:
      - Scans source directory for CSV files matching pattern
      - Converts timestamps from source timezone to target timezone
      - Saves converted files with "_utc_converted" suffix
      - Handles various timestamp formats
      - Provides detailed conversion statistics

    Example timestamp conversion:
      "2025-09-28 21:22:00" (UTC+2) → "2025-09-28 19:22:00" (UTC+0)

    Kind: "control-read"
    """
    id = "timestamp_convert_utc"
    kind = "control-read"

    def run(self, ctx: Ctx, inputs: Dict[str, Any]) -> CapResult:
        source_dir = inputs.get("source_directory", "")
        target_dir = inputs.get("target_directory", "")
        file_pattern = inputs.get("file_pattern", "*.csv")
        timestamp_column = inputs.get("timestamp_column", "timestamp")
        source_timezone = inputs.get("source_timezone", "UTC+2")
        target_timezone = inputs.get("target_timezone", "UTC+0")
        backup_original = inputs.get("backup_original", True)

        # Validate required inputs
        if not source_dir:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error="source_directory is required",
                artifacts=()
            )

        if not target_dir:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error="target_directory is required",
                artifacts=()
            )

        # Convert timezone strings to timedelta objects
        source_offset = self._parse_timezone_offset(source_timezone)
        target_offset = self._parse_timezone_offset(target_timezone)

        if source_offset is None or target_offset is None:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error=f"Invalid timezone format. Use formats like 'UTC+2', 'UTC-5', or 'UTC+0'",
                artifacts=()
            )

        # Ensure target directory exists
        try:
            ensure_dir(target_dir)
        except Exception as e:
            return CapResult(
                ok=False,
                data={"inputs": inputs},
                error=f"Failed to create target directory: {str(e)}",
                artifacts=()
            )

        # Find all CSV files in source directory
        search_pattern = os.path.join(source_dir, file_pattern)
        csv_files = glob.glob(search_pattern)

        if not csv_files:
            return CapResult(
                ok=False,
                data={"inputs": inputs, "search_pattern": search_pattern},
                error=f"No CSV files found matching pattern: {search_pattern}",
                artifacts=()
            )

        conversion_results: List[ConversionResult] = []
        total_files_processed = 0
        total_rows_converted = 0
        total_conversion_errors = 0

        # Process each CSV file
        for csv_file in csv_files:
            try:
                result = self._convert_csv_file(
                    csv_file,
                    target_dir,
                    timestamp_column,
                    source_offset,
                    target_offset,
                    backup_original,
                    ctx.verbose
                )

                if result:
                    conversion_results.append(result)
                    total_files_processed += 1
                    total_rows_converted += result.rows_converted
                    total_conversion_errors += result.conversion_errors

            except Exception as e:
                if ctx.verbose:
                    print(f"❌ Error processing file {csv_file}: {str(e)}")
                total_conversion_errors += 1

        # Save conversion summary
        artifacts = []
        if ctx.debug and conversion_results:
            summary_data = {
                "timestamp": timestamp(),
                "conversion_summary": {
                    "total_files_processed": total_files_processed,
                    "total_rows_converted": total_rows_converted,
                    "total_conversion_errors": total_conversion_errors,
                    "source_timezone": source_timezone,
                    "target_timezone": target_timezone,
                    "file_pattern": file_pattern
                },
                "conversion_results": [
                    {
                        "original_file": r.original_file,
                        "converted_file": r.converted_file,
                        "rows_converted": r.rows_converted,
                        "conversion_errors": r.conversion_errors,
                        "start_timestamp": r.start_timestamp,
                        "end_timestamp": r.end_timestamp
                    }
                    for r in conversion_results
                ]
            }

            summary_file = f"timestamp_conversion_summary_{timestamp()}.json"
            artifact_path = save_json(ctx, summary_file, summary_data, subfolder="timestamp_conversion")
            artifacts.append(artifact_path)

        # Determine overall success
        success = total_files_processed > 0 and total_conversion_errors == 0

        return CapResult(
            ok=success,
            data={
                "total_files_processed": total_files_processed,
                "total_rows_converted": total_rows_converted,
                "total_conversion_errors": total_conversion_errors,
                "source_timezone": source_timezone,
                "target_timezone": target_timezone,
                "conversion_results": [
                    {
                        "original_file": os.path.basename(r.original_file),
                        "converted_file": os.path.basename(r.converted_file),
                        "rows_converted": r.rows_converted,
                        "conversion_errors": r.conversion_errors
                    }
                    for r in conversion_results
                ]
            },
            error=None if success else f"Processed {total_files_processed} files with {total_conversion_errors} errors",
            artifacts=tuple(artifacts)
        )

    def _parse_timezone_offset(self, timezone_str: str) -> Optional[timedelta]:
        """Parse timezone string like 'UTC+2' or 'UTC-5' to timedelta object."""
        try:
            if not timezone_str.upper().startswith('UTC'):
                return None

            offset_str = timezone_str.upper().replace('UTC', '')
            if not offset_str:
                return timedelta(hours=0)

            sign = 1 if offset_str.startswith('+') else -1
            hours = int(offset_str[1:])

            return timedelta(hours=sign * hours)
        except Exception:
            return None

    def _convert_csv_file(
        self,
        csv_file: str,
        target_dir: str,
        timestamp_column: str,
        source_offset: timedelta,
        target_offset: timedelta,
        backup_original: bool,
        verbose: bool = False
    ) -> Optional[ConversionResult]:
        """Convert timestamps in a single CSV file."""

        # Generate output filename
        filename = os.path.basename(csv_file)
        name_without_ext = filename.rsplit('.', 1)[0]
        converted_filename = f"{name_without_ext}_utc_converted.csv"
        converted_file = os.path.join(target_dir, converted_filename)

        rows_converted = 0
        conversion_errors = 0
        start_timestamp = None
        end_timestamp = None

        try:
            with open(csv_file, 'r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)

                # Validate that timestamp column exists
                if timestamp_column not in reader.fieldnames:
                    if verbose:
                        print(f"⚠️ Timestamp column '{timestamp_column}' not found in {filename}")
                    return None

                with open(converted_file, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
                    writer.writeheader()

                    for row_num, row in enumerate(reader, start=2):  # Start at 2 to account for header
                        try:
                            original_timestamp = row[timestamp_column]

                            # Parse the timestamp
                            # Handle format: "2025-09-28 21:22:00"
                            dt = datetime.strptime(original_timestamp, "%Y-%m-%d %H:%M:%S")

                            # Apply source timezone offset (convert to UTC)
                            utc_dt = dt - source_offset

                            # Apply target timezone offset (convert to target timezone)
                            target_dt = utc_dt + target_offset

                            # Update the timestamp in the row
                            row[timestamp_column] = target_dt.strftime("%Y-%m-%d %H:%M:%S")

                            # Track timestamp range
                            if start_timestamp is None:
                                start_timestamp = original_timestamp
                            end_timestamp = original_timestamp

                            writer.writerow(row)
                            rows_converted += 1

                        except ValueError as e:
                            if verbose:
                                print(f"⚠️ Error converting row {row_num} in {filename}: {str(e)}")
                            conversion_errors += 1
                            # Write original row if conversion fails
                            writer.writerow(row)
                        except Exception as e:
                            if verbose:
                                print(f"⚠️ Unexpected error in row {row_num} in {filename}: {str(e)}")
                            conversion_errors += 1
                            # Write original row if conversion fails
                            writer.writerow(row)

            if verbose:
                print(f"✅ Converted {filename}: {rows_converted} rows ({conversion_errors} errors)")

            return ConversionResult(
                original_file=csv_file,
                converted_file=converted_file,
                original_timezone=f"UTC{source_offset.total_seconds() / 3600:+.0f}",
                target_timezone=f"UTC{target_offset.total_seconds() / 3600:+.0f}",
                rows_converted=rows_converted,
                conversion_errors=conversion_errors,
                start_timestamp=start_timestamp or "",
                end_timestamp=end_timestamp or ""
            )

        except Exception as e:
            if verbose:
                print(f"❌ Error processing file {csv_file}: {str(e)}")
            return None

    def _detect_timestamp_format(self, sample_timestamps: List[str]) -> Optional[str]:
        """Detect the timestamp format from sample data."""
        common_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%dT%H:%M:%S.%f",
            "%m/%d/%Y %H:%M:%S",
            "%d/%m/%Y %H:%M:%S",
        ]

        for timestamp_str in sample_timestamps:
            for fmt in common_formats:
                try:
                    datetime.strptime(timestamp_str, fmt)
                    return fmt
                except ValueError:
                    continue

        return None


# Factory for orchestrator
def build() -> Capability:
    return TimestampConvertUTC()


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Convert CSV timestamps from UTC+2 to UTC+0")
    parser.add_argument("--source-dir", required=True, help="Source directory containing CSV files")
    parser.add_argument("--target-dir", required=True, help="Target directory for converted files")
    parser.add_argument("--pattern", default="*.csv", help="File pattern to match (default: *.csv)")
    parser.add_argument("--timestamp-column", default="timestamp", help="Name of timestamp column (default: timestamp)")
    parser.add_argument("--source-tz", default="UTC+2", help="Source timezone (default: UTC+2)")
    parser.add_argument("--target-tz", default="UTC+0", help="Target timezone (default: UTC+0)")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Create a mock context for standalone usage
    class MockCtx:
        def __init__(self, verbose=False):
            self.verbose = verbose
            self.debug = False
            self.dry_run = False

    ctx = MockCtx(verbose=args.verbose)

    # Run the conversion
    converter = TimestampConvertUTC()
    result = converter.run(ctx, {
        "source_directory": args.source_dir,
        "target_directory": args.target_dir,
        "file_pattern": args.pattern,
        "timestamp_column": args.timestamp_column,
        "source_timezone": args.source_tz,
        "target_timezone": args.target_tz,
        "backup_original": True
    })

    # Print results
    print("\n📊 Conversion Results:")
    print(f"  Files processed: {result.data.get('total_files_processed', 0)}")
    print(f"  Rows converted: {result.data.get('total_rows_converted', 0)}")
    print(f"  Errors: {result.data.get('total_conversion_errors', 0)}")

    if result.data.get('conversion_results'):
        print("\n📁 File Details:")
        for file_result in result.data['conversion_results']:
            print(f"  {os.path.basename(file_result['original_file'])} → {os.path.basename(file_result['converted_file'])}")
            print(f"    Rows: {file_result['rows_converted']}, Errors: {file_result['conversion_errors']}")

    if not result.ok:
        print(f"\n❌ Conversion failed: {result.error}")
        sys.exit(1)
    else:
        print("\n✅ Conversion completed successfully!")
        sys.exit(0)