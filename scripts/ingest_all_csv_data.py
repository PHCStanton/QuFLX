#!/usr/bin/env python3
"""
Bulk CSV Data Ingestion for QuFLX

Ingests all CSV files from the data directories into Supabase.
Supports parallel processing and progress tracking.

Usage:
    python scripts/ingest_all_csv_data.py [--timeframes 1m,5m,15m,1H,4H] [--dry-run]
"""

from capabilities.supabase_csv_ingestion import SupabaseCSVIngestion
import os
import logging
import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BulkCSVIngestor:
    """Handles bulk ingestion of CSV files with progress tracking."""

    def __init__(self, max_workers: int = 4):
        """
        Initialize bulk ingestor.

        Args:
            max_workers: Maximum number of parallel workers
        """
        self.ingestor = SupabaseCSVIngestion()
        self.max_workers = max_workers

    def discover_csv_files(self, base_dir: str, timeframes: List[str] = None) -> Dict[str, List[str]]:
        """
        Discover all CSV files organized by timeframe.

        Args:
            base_dir: Base directory containing timeframe subdirectories
            timeframes: List of timeframes to process (optional)

        Returns:
            Dict mapping timeframe to list of file paths
        """
        timeframe_dirs = {
            '1m': '1M_candles',
            '5m': '5M_candles',
            '15m': '15M_candles',
            '1H': '1H_candles',
            '4H': '4H_candles'
        }

        discovered_files = {}

        for tf_short, tf_dir in timeframe_dirs.items():
            if timeframes and tf_short not in timeframes:
                continue

            tf_path = os.path.join(base_dir, tf_dir)
            if not os.path.exists(tf_path):
                logger.warning(f"Timeframe directory not found: {tf_path}")
                continue

            # Find all CSV files in this timeframe directory
            csv_files = []
            for file in os.listdir(tf_path):
                if file.endswith('.csv'):
                    csv_files.append(os.path.join(tf_path, file))

            if csv_files:
                discovered_files[tf_short] = sorted(csv_files)
                logger.info(f"Found {len(csv_files)} {tf_short} files in {tf_path}")

        return discovered_files

    def ingest_single_file(self, filepath: str) -> Dict[str, Any]:
        """
        Ingest a single CSV file (wrapper for thread pool).

        Args:
            filepath: Path to CSV file

        Returns:
            Ingestion result
        """
        try:
            result = self.ingestor.ingest_csv_file(filepath)
            return result
        except Exception as e:
            logger.error(f"Unexpected error ingesting {filepath}: {e}")
            return {
                'success': False,
                'error': str(e),
                'file': filepath
            }

    def ingest_timeframe_batch(self, timeframe: str, files: List[str],
                              dry_run: bool = False) -> Dict[str, Any]:
        """
        Ingest all files for a specific timeframe.

        Args:
            timeframe: Timeframe string (e.g., '1m')
            files: List of file paths
            dry_run: If True, only count files without ingesting

        Returns:
            Batch results summary
        """
        logger.info(f"📊 Processing {timeframe} timeframe: {len(files)} files")

        if dry_run:
            logger.info(f"🔍 DRY RUN: Would process {len(files)} {timeframe} files")
            return {
                'timeframe': timeframe,
                'total_files': len(files),
                'dry_run': True
            }

        start_time = time.time()
        successful_files = 0
        failed_files = 0
        total_records = 0

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for this timeframe
            future_to_file = {
                executor.submit(self.ingest_single_file, filepath): filepath
                for filepath in files
            }

            # Process results as they complete
            for future in as_completed(future_to_file):
                filepath = future_to_file[future]
                try:
                    result = future.result()

                    if result['success']:
                        successful_files += 1
                        total_records += result.get('records_processed', 0)
                        logger.info(f"✅ {os.path.basename(filepath)}: {result.get('records_processed', 0)} records")
                    else:
                        failed_files += 1
                        logger.error(f"❌ {os.path.basename(filepath)}: {result.get('error', 'Unknown error')}")

                except Exception as e:
                    failed_files += 1
                    logger.error(f"💥 {os.path.basename(filepath)}: Exception - {e}")

        processing_time = time.time() - start_time

        summary = {
            'timeframe': timeframe,
            'total_files': len(files),
            'successful_files': successful_files,
            'failed_files': failed_files,
            'total_records': total_records,
            'processing_time_seconds': round(processing_time, 2),
            'records_per_second': round(total_records / processing_time, 2) if processing_time > 0 else 0
        }

        logger.info(f"📈 {timeframe} Summary: {successful_files}/{len(files)} files, {total_records} records in {processing_time:.2f}s")

        return summary

    def run_bulk_ingestion(self, data_dir: str, timeframes: List[str] = None,
                          dry_run: bool = False) -> Dict[str, Any]:
        """
        Run bulk ingestion for all discovered CSV files.

        Args:
            data_dir: Directory containing timeframe subdirectories
            timeframes: List of timeframes to process (optional)
            dry_run: If True, only count files without ingesting

        Returns:
            Complete ingestion results
        """
        logger.info("🚀 Starting bulk CSV ingestion for QuFLX")
        logger.info(f"   Data directory: {data_dir}")
        logger.info(f"   Timeframes: {timeframes or 'all'}")
        logger.info(f"   Dry run: {dry_run}")
        logger.info("=" * 60)

        # Discover files
        discovered_files = self.discover_csv_files(data_dir, timeframes)

        if not discovered_files:
            logger.error("❌ No CSV files found to process")
            return {'error': 'No files found'}

        total_files = sum(len(files) for files in discovered_files.values())
        logger.info(f"📁 Discovered {total_files} CSV files across {len(discovered_files)} timeframes")

        # Process each timeframe sequentially (to avoid overwhelming the database)
        overall_start = time.time()
        timeframe_results = []

        for timeframe, files in discovered_files.items():
            tf_result = self.ingest_timeframe_batch(timeframe, files, dry_run)
            timeframe_results.append(tf_result)

        overall_time = time.time() - overall_start

        # Calculate overall statistics
        overall_stats = {
            'total_files': sum(r['total_files'] for r in timeframe_results),
            'successful_files': sum(r.get('successful_files', 0) for r in timeframe_results),
            'failed_files': sum(r.get('failed_files', 0) for r in timeframe_results),
            'total_records': sum(r.get('total_records', 0) for r in timeframe_results),
            'total_time_seconds': round(overall_time, 2),
            'average_records_per_second': round(
                sum(r.get('total_records', 0) for r in timeframe_results) / overall_time
                if overall_time > 0 else 0, 2
            ),
            'timeframe_results': timeframe_results,
            'dry_run': dry_run
        }

        # Final summary
        logger.info("=" * 60)
        if dry_run:
            logger.info("🔍 DRY RUN COMPLETED")
            logger.info(f"   Would process: {overall_stats['total_files']} files")
        else:
            success_rate = (overall_stats['successful_files'] / overall_stats['total_files'] * 100) if overall_stats['total_files'] > 0 else 0
            logger.info("🎉 BULK INGESTION COMPLETED")
            logger.info(f"   Files processed: {overall_stats['successful_files']}/{overall_stats['total_files']} ({success_rate:.1f}%)")
            logger.info(f"   Total records: {overall_stats['total_records']:,}")
            logger.info(f"   Total time: {overall_stats['total_time_seconds']:.2f}s")
            logger.info(f"   Performance: {overall_stats['average_records_per_second']:.0f} records/sec")

        return overall_stats


def main():
    """Main entry point for bulk ingestion."""
    parser = argparse.ArgumentParser(description='Bulk CSV Data Ingestion for QuFLX')
    parser.add_argument(
        '--timeframes',
        type=str,
        default='1m,5m,15m,1H,4H',
        help='Comma-separated list of timeframes to process (default: 1m,5m,15m,1H,4H)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data/data_output/assets_data/data_collect',
        help='Base directory containing timeframe subdirectories'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Count files without actually ingesting data'
    )
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Maximum number of parallel workers (default: 4)'
    )

    args = parser.parse_args()

    # Parse timeframes
    timeframes = [tf.strip() for tf in args.timeframes.split(',')] if args.timeframes else None

    try:
        ingestor = BulkCSVIngestor(max_workers=args.max_workers)
        results = ingestor.run_bulk_ingestion(args.data_dir, timeframes, args.dry_run)

        if 'error' in results:
            logger.error(f"Ingestion failed: {results['error']}")
            return 1

        # Success
        return 0

    except Exception as e:
        logger.error(f"💥 Unexpected error during bulk ingestion: {e}")
        return 1


if __name__ == "__main__":
    exit(main())