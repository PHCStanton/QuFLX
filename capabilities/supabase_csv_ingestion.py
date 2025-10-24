#!/usr/bin/env python3
"""
Supabase CSV Ingestion Module for QuFLX

Handles ingestion of CSV candle data files into Supabase database.
Supports batch processing, error handling, and progress tracking.

Usage:
    from capabilities.supabase_csv_ingestion import SupabaseCSVIngestion

    ingestor = SupabaseCSVIngestion()
    result = ingestor.ingest_csv_file("path/to/file.csv")
"""

import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import logging
import os
import time
from typing import List, Dict, Any, Optional
from config.supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY, BATCH_SIZE, MAX_RETRIES, TIMEOUT_SECONDS


class SupabaseCSVIngestion:
    """
    Handles CSV file ingestion into Supabase database with robust error handling
    and batch processing capabilities.
    """

    def __init__(self, batch_size: int = BATCH_SIZE):
        """
        Initialize the Supabase CSV ingestion client.

        Args:
            batch_size: Number of records to insert in each batch
        """
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        self.batch_size = batch_size
        self.logger = logging.getLogger(__name__)

        # Configure logging
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def parse_filename(self, filepath: str) -> Dict[str, str]:
        """
        Extract asset symbol and timeframe from CSV filename.

        Expected format: {SYMBOL}_otc_{TIMEFRAME}_{DATE}.csv
        Example: EURUSD_otc_1m_2025_10_23_01_23_56.csv

        Args:
            filepath: Path to the CSV file

        Returns:
            Dict containing 'symbol' and 'timeframe'

        Raises:
            ValueError: If filename format is unrecognized
        """
        filename = os.path.basename(filepath).replace('.csv', '')

        try:
            parts = filename.split('_')

            if len(parts) < 4:
                raise ValueError(f"Filename has insufficient parts: {filename}")

            # Find the timeframe in the parts (should be one of: 1m, 5m, 15m, 1H, 4H)
            valid_timeframes = ['1m', '5m', '15m', '1H', '4H']
            timeframe_index = None

            for i, part in enumerate(parts):
                if part in valid_timeframes:
                    timeframe_index = i
                    break

            if timeframe_index is None:
                raise ValueError(f"No valid timeframe found in filename: {filename}")

            # Extract symbol (everything before timeframe)
            symbol_parts = parts[:timeframe_index]
            symbol = '_'.join(symbol_parts)

            # Extract timeframe
            timeframe = parts[timeframe_index]

            return {
                'symbol': symbol,
                'timeframe': timeframe
            }

        except Exception as e:
            raise ValueError(f"Unable to parse filename '{filename}': {str(e)}")

    def get_asset_id(self, symbol: str) -> int:
        """
        Get asset ID by symbol from the database.

        Args:
            symbol: Asset symbol (e.g., 'EURUSD_otc')

        Returns:
            Asset ID

        Raises:
            ValueError: If asset not found
        """
        try:
            result = self.supabase.table('assets').select('id').eq('symbol', symbol).execute()

            if not result.data:
                raise ValueError(f"Asset '{symbol}' not found in database. Please ensure it exists in the assets table.")

            return result.data[0]['id']

        except Exception as e:
            raise ValueError(f"Failed to get asset ID for '{symbol}': {str(e)}")

    def validate_csv_data(self, df: pd.DataFrame, filepath: str) -> List[str]:
        """
        Validate CSV data for required columns and data integrity.

        Args:
            df: DataFrame containing CSV data
            filepath: File path for error reporting

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check required columns
        required_columns = ['timestamp', 'open', 'close', 'high', 'low']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")

        if errors:
            return errors

        # Validate data types and ranges
        try:
            # Check timestamp format
            pd.to_datetime(df['timestamp'], utc=True)
        except Exception as e:
            errors.append(f"Invalid timestamp format: {str(e)}")

        # Check numeric columns
        numeric_columns = ['open', 'close', 'high', 'low']
        for col in numeric_columns:
            try:
                pd.to_numeric(df[col])
                # Check for negative prices (shouldn't happen in forex)
                if (df[col] < 0).any():
                    errors.append(f"Negative values found in column '{col}'")
            except Exception as e:
                errors.append(f"Invalid numeric data in column '{col}': {str(e)}")

        # Check OHLC logic (high >= max(open,close), low <= min(open,close))
        try:
            invalid_high = df['high'] < df[['open', 'close']].max(axis=1)
            invalid_low = df['low'] > df[['open', 'close']].min(axis=1)

            if invalid_high.any():
                errors.append("Some high values are lower than open/close prices")

            if invalid_low.any():
                errors.append("Some low values are higher than open/close prices")

        except Exception as e:
            errors.append(f"Error validating OHLC logic: {str(e)}")

        return errors

    def prepare_records_for_insertion(self, df: pd.DataFrame, asset_id: int, timeframe: str) -> List[Dict[str, Any]]:
        """
        Prepare DataFrame records for Supabase insertion.

        Args:
            df: Validated DataFrame
            asset_id: Asset ID from database
            timeframe: Timeframe string

        Returns:
            List of records ready for insertion
        """
        records = []

        for _, row in df.iterrows():
            record = {
                'asset_id': asset_id,
                'timeframe': timeframe,
                'timestamp': pd.to_datetime(row['timestamp'], utc=True).isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close'])
            }

            # Add volume if present
            if 'volume' in row and pd.notna(row['volume']):
                record['volume'] = int(row['volume'])
            else:
                record['volume'] = 0

            records.append(record)

        return records

    def insert_records_batch(self, records: List[Dict[str, Any]], batch_num: int) -> Dict[str, Any]:
        """
        Insert a batch of records into Supabase with retry logic.

        Args:
            records: List of records to insert
            batch_num: Batch number for logging

        Returns:
            Dict with success status and inserted count
        """
        for attempt in range(MAX_RETRIES):
            try:
                start_time = time.time()
                result = self.supabase.table('candles').insert(records).execute()
                end_time = time.time()

                inserted_count = len(result.data) if result.data else len(records)

                self.logger.info(
                    f"✓ Batch {batch_num}: Inserted {inserted_count}/{len(records)} records "
                    f"in {end_time - start_time:.2f}s"
                )

                return {
                    'success': True,
                    'inserted': inserted_count,
                    'attempts': attempt + 1
                }

            except Exception as e:
                self.logger.warning(
                    f"✗ Batch {batch_num} attempt {attempt + 1}/{MAX_RETRIES} failed: {str(e)}"
                )

                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {
                        'success': False,
                        'error': str(e),
                        'inserted': 0,
                        'attempts': attempt + 1
                    }

    def log_ingestion_result(self, file_info: Dict[str, str], filepath: str,
                           total_records: int, successful_inserts: int,
                           failed_inserts: int, processing_time: float,
                           status: str, error_message: Optional[str] = None):
        """
        Log the ingestion result to the database.

        Args:
            file_info: Dict with symbol and timeframe
            filepath: Full file path
            total_records: Total records in file
            successful_inserts: Number of successful inserts
            failed_inserts: Number of failed inserts
            processing_time: Time taken in seconds
            status: Status string
            error_message: Optional error message
        """
        try:
            log_entry = {
                'asset_symbol': file_info['symbol'],
                'timeframe': file_info['timeframe'],
                'file_path': filepath,
                'records_processed': successful_inserts,
                'records_failed': failed_inserts,
                'status': status,
                'processing_time_seconds': round(processing_time, 2)
            }

            if error_message:
                log_entry['error_message'] = error_message

            self.supabase.table('ingestion_logs').insert(log_entry).execute()

        except Exception as e:
            self.logger.error(f"Failed to log ingestion result: {str(e)}")

    def ingest_csv_file(self, filepath: str) -> Dict[str, Any]:
        """
        Ingest a single CSV file into Supabase.

        Args:
            filepath: Path to the CSV file

        Returns:
            Dict with ingestion results
        """
        start_time = time.time()
        self.logger.info(f"📤 Starting ingestion of: {os.path.basename(filepath)}")

        try:
            # Step 1: Parse filename
            file_info = self.parse_filename(filepath)

            # Step 2: Get asset ID
            asset_id = self.get_asset_id(file_info['symbol'])

            # Step 3: Read and validate CSV
            df = pd.read_csv(filepath)

            validation_errors = self.validate_csv_data(df, filepath)
            if validation_errors:
                error_msg = "; ".join(validation_errors)
                self.logger.error(f"❌ Validation failed: {error_msg}")

                self.log_ingestion_result(
                    file_info, filepath, len(df), 0, len(df),
                    time.time() - start_time, 'failed', error_msg
                )

                return {
                    'success': False,
                    'error': f"Validation failed: {error_msg}",
                    'file': filepath,
                    'records_total': len(df),
                    'records_processed': 0
                }

            # Step 4: Prepare records
            records = self.prepare_records_for_insertion(df, asset_id, file_info['timeframe'])

            # Step 5: Insert in batches
            total_inserted = 0
            total_failed = 0

            for i in range(0, len(records), self.batch_size):
                batch = records[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1

                batch_result = self.insert_records_batch(batch, batch_num)

                if batch_result['success']:
                    total_inserted += batch_result['inserted']
                else:
                    total_failed += len(batch)
                    self.logger.error(f"Failed to insert batch {batch_num}: {batch_result['error']}")

            # Step 6: Determine final status
            processing_time = time.time() - start_time

            if total_failed == 0:
                status = 'completed'
                self.logger.info(f"✅ Successfully ingested {total_inserted} records in {processing_time:.2f}s")
            elif total_inserted > 0:
                status = 'partial'
                self.logger.warning(f"⚠️ Partially ingested: {total_inserted} success, {total_failed} failed")
            else:
                status = 'failed'
                self.logger.error(f"❌ Failed to ingest any records")

            # Step 7: Log result
            self.log_ingestion_result(
                file_info, filepath, len(records),
                total_inserted, total_failed, processing_time, status
            )

            return {
                'success': status in ['completed', 'partial'],
                'status': status,
                'file': filepath,
                'asset': file_info['symbol'],
                'timeframe': file_info['timeframe'],
                'records_total': len(records),
                'records_processed': total_inserted,
                'records_failed': total_failed,
                'processing_time_seconds': round(processing_time, 2)
            }

        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            self.logger.error(f"💥 Unexpected error during ingestion: {error_msg}")

            # Try to log error even if file parsing failed
            try:
                file_info = self.parse_filename(filepath)
                self.log_ingestion_result(
                    file_info, filepath, 0, 0, 0,
                    processing_time, 'failed', error_msg
                )
            except:
                pass

            return {
                'success': False,
                'error': error_msg,
                'file': filepath,
                'records_total': 0,
                'records_processed': 0,
                'processing_time_seconds': round(processing_time, 2)
            }

    def ingest_directory(self, directory: str, pattern: str = "*.csv",
                        recursive: bool = False) -> List[Dict[str, Any]]:
        """
        Ingest all CSV files in a directory.

        Args:
            directory: Directory path to scan
            pattern: File pattern to match (default: "*.csv")
            recursive: Whether to scan subdirectories

        Returns:
            List of ingestion results for each file
        """
        import glob

        if recursive:
            csv_files = glob.glob(os.path.join(directory, "**", pattern), recursive=True)
        else:
            csv_files = glob.glob(os.path.join(directory, pattern))

        self.logger.info(f"🔍 Found {len(csv_files)} CSV files in {directory}")

        results = []
        successful_files = 0
        total_records = 0

        for csv_file in csv_files:
            self.logger.info(f"Processing: {os.path.basename(csv_file)}")
            result = self.ingest_csv_file(csv_file)
            results.append(result)

            if result['success']:
                successful_files += 1
                total_records += result.get('records_processed', 0)

        self.logger.info(f"📊 Directory ingestion complete: {successful_files}/{len(csv_files)} files successful, {total_records} total records")

        return results