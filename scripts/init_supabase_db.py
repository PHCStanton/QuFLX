#!/usr/bin/env python3
"""
Initialize Supabase Database for QuFLX Trading Data

This script sets up the initial database structure and populates
the assets table with known trading pairs from the CSV data.

Usage:
    python scripts/init_supabase_db.py
"""

from supabase import create_client, Client
from config.supabase_config import SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY
import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SupabaseDatabaseInitializer:
    """Handles Supabase database initialization and setup."""

    def __init__(self):
        """Initialize with service role key for admin operations."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
        logger.info("Connected to Supabase with service role key")

    def wait_for_database_ready(self, max_attempts: int = 10) -> bool:
        """Wait for database to be ready after schema creation."""
        for attempt in range(max_attempts):
            try:
                # Test connection by querying assets table
                result = self.supabase.table('assets').select('count').limit(1).execute()
                logger.info("Database connection successful")
                return True
            except Exception as e:
                logger.warning(f"Database not ready (attempt {attempt + 1}/{max_attempts}): {e}")
                time.sleep(2)

        logger.error("Database failed to become ready")
        return False

    def populate_assets_table(self):
        """Populate the assets table with known trading pairs."""
        logger.info("Populating assets table...")

        # Extracted from your CSV data directories
        asset_pairs = [
            # Major forex pairs
            ('EURUSD_otc', 'EUR', 'USD', 'Euro vs US Dollar'),
            ('GBPUSD_otc', 'GBP', 'USD', 'British Pound vs US Dollar'),
            ('AUDUSD_otc', 'AUD', 'USD', 'Australian Dollar vs US Dollar'),
            ('USDJPY_otc', 'USD', 'JPY', 'US Dollar vs Japanese Yen'),
            ('USDCHF_otc', 'USD', 'CHF', 'US Dollar vs Swiss Franc'),

            # Cross pairs
            ('GBPAUD_otc', 'GBP', 'AUD', 'British Pound vs Australian Dollar'),
            ('GBPJPY_otc', 'GBP', 'JPY', 'British Pound vs Japanese Yen'),
            ('CADCHF_otc', 'CAD', 'CHF', 'Canadian Dollar vs Swiss Franc'),
            ('NZDJPY_otc', 'NZD', 'JPY', 'New Zealand Dollar vs Japanese Yen'),

            # Exotic pairs
            ('JODCNY_otc', 'JOD', 'CNY', 'Jordanian Dinar vs Chinese Yuan'),
            ('KESUSD_otc', 'KES', 'USD', 'Kenyan Shilling vs US Dollar'),
            ('OMRCNY_otc', 'OMR', 'CNY', 'Omani Rial vs Chinese Yuan'),
            ('QARCNY_otc', 'QAR', 'CNY', 'Qatari Riyal vs Chinese Yuan'),
            ('TNDUSD_otc', 'TND', 'USD', 'Tunisian Dinar vs US Dollar'),
            ('YERUSD_otc', 'YER', 'USD', 'Yemeni Rial vs US Dollar'),
            ('ZARUSD_otc', 'ZAR', 'USD', 'South African Rand vs US Dollar'),

            # Emerging market pairs
            ('USDARS_otc', 'USD', 'ARS', 'US Dollar vs Argentine Peso'),
            ('USDCLP_otc', 'USD', 'CLP', 'US Dollar vs Chilean Peso'),
            ('USDCNH_otc', 'USD', 'CNH', 'US Dollar vs Chinese Yuan Offshore'),
            ('USDCOP_otc', 'USD', 'COP', 'US Dollar vs Colombian Peso'),
            ('USDINR_otc', 'USD', 'INR', 'US Dollar vs Indian Rupee'),
            ('USDMXN_otc', 'USD', 'MXN', 'US Dollar vs Mexican Peso'),
            ('USDPHP_otc', 'USD', 'PHP', 'US Dollar vs Philippine Peso'),
        ]

        successful_inserts = 0
        failed_inserts = 0

        for symbol, base, quote, display_name in asset_pairs:
            try:
                # Use upsert to handle duplicates
                result = self.supabase.table('assets').upsert({
                    'symbol': symbol,
                    'base_currency': base,
                    'quote_currency': quote,
                    'display_name': display_name,
                    'asset_type': 'forex'
                }).execute()

                successful_inserts += 1
                logger.info(f"✓ Inserted/Updated asset: {symbol}")

            except Exception as e:
                failed_inserts += 1
                logger.error(f"✗ Failed to insert asset {symbol}: {e}")

        logger.info(f"Assets table population completed: {successful_inserts} successful, {failed_inserts} failed")
        return successful_inserts, failed_inserts

    def verify_table_structure(self):
        """Verify that required tables exist and have correct structure."""
        logger.info("Verifying database table structure...")

        tables_to_check = ['assets', 'candles', 'ingestion_logs']
        partitions_to_check = ['candles_1m', 'candles_5m', 'candles_15m', 'candles_1h', 'candles_4h']

        try:
            # Check main tables
            for table in tables_to_check:
                # Simple count query to verify table exists
                result = self.supabase.table(table).select('count', count='exact').limit(1).execute()
                logger.info(f"✓ Table '{table}' exists")

            # Check partitions (they might not be directly queryable via client)
            logger.info("✓ Partition tables should exist (verification via SQL editor recommended)")

            return True

        except Exception as e:
            logger.error(f"✗ Table structure verification failed: {e}")
            return False

    def get_database_stats(self):
        """Get basic statistics about the database."""
        logger.info("Gathering database statistics...")

        try:
            # Count assets
            assets_result = self.supabase.table('assets').select('count', count='exact').execute()
            assets_count = assets_result.count if hasattr(assets_result, 'count') else 0

            # Count candles
            candles_result = self.supabase.table('candles').select('count', count='exact').execute()
            candles_count = candles_result.count if hasattr(candles_result, 'count') else 0

            # Count ingestion logs
            logs_result = self.supabase.table('ingestion_logs').select('count', count='exact').execute()
            logs_count = logs_result.count if hasattr(logs_result, 'count') else 0

            logger.info("Database Statistics:")
            logger.info(f"  - Assets: {assets_count}")
            logger.info(f"  - Candles: {candles_count}")
            logger.info(f"  - Ingestion Logs: {logs_count}")

            return {
                'assets_count': assets_count,
                'candles_count': candles_count,
                'logs_count': logs_count
            }

        except Exception as e:
            logger.error(f"Failed to gather database statistics: {e}")
            return None

    def run_initialization(self):
        """Run the complete database initialization process."""
        logger.info("🚀 Starting Supabase database initialization for QuFLX")
        logger.info("=" * 60)

        # Step 1: Wait for database to be ready
        logger.info("Step 1: Waiting for database to be ready...")
        if not self.wait_for_database_ready():
            logger.error("❌ Database initialization failed - database not ready")
            return False

        # Step 2: Verify table structure
        logger.info("Step 2: Verifying table structure...")
        if not self.verify_table_structure():
            logger.error("❌ Database initialization failed - table structure issues")
            return False

        # Step 3: Populate assets table
        logger.info("Step 3: Populating assets table...")
        successful, failed = self.populate_assets_table()
        if failed > 0:
            logger.warning(f"⚠️  Assets population had {failed} failures")

        # Step 4: Get final statistics
        logger.info("Step 4: Gathering final statistics...")
        stats = self.get_database_stats()

        # Summary
        logger.info("=" * 60)
        if successful > 0:
            logger.info("✅ Database initialization completed successfully!")
            logger.info(f"   - Assets populated: {successful}")
            if stats:
                logger.info(f"   - Total assets in DB: {stats['assets_count']}")
                logger.info(f"   - Total candles: {stats['candles_count']}")
                logger.info(f"   - Ingestion logs: {stats['logs_count']}")
        else:
            logger.error("❌ Database initialization completed with errors")
            return False

        logger.info("=" * 60)
        logger.info("Next steps:")
        logger.info("1. Run the SQL schema file in Supabase SQL Editor (if not already done)")
        logger.info("2. Test CSV ingestion with: python scripts/test_supabase_integration.py")
        logger.info("3. Ingest all CSV data with: python scripts/ingest_all_csv_data.py")

        return True


def main():
    """Main entry point for database initialization."""
    try:
        initializer = SupabaseDatabaseInitializer()
        success = initializer.run_initialization()

        if success:
            logger.info("🎉 Database initialization process completed successfully!")
            return 0
        else:
            logger.error("💥 Database initialization process failed!")
            return 1

    except Exception as e:
        logger.error(f"💥 Unexpected error during database initialization: {e}")
        return 1


if __name__ == "__main__":
    exit(main())