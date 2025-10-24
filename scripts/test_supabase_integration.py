#!/usr/bin/env python3
"""
Test Supabase Integration for QuFLX

Tests the complete Supabase integration including:
- Database connection
- CSV ingestion
- Data querying
- Error handling

Usage:
    python scripts/test_supabase_integration.py
"""

from capabilities.supabase_csv_ingestion import SupabaseCSVIngestion
from capabilities.supabase_data_queries import SupabaseDataQueries
from supabase import create_client, Client
from config.supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY
import logging
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_database_connection():
    """Test basic database connection."""
    print("🔗 Testing database connection...")
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

        # Test connection by querying assets table
        result = supabase.table('assets').select('count', count='exact').limit(1).execute()
        print("✅ Database connection successful")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def test_csv_ingestion():
    """Test CSV file ingestion."""
    print("\n📤 Testing CSV ingestion...")

    ingestor = SupabaseCSVIngestion()

    # Use a test file from your data
    test_file = "data/data_output/assets_data/data_collect/1M_candles/EURUSD_otc_1m_2025_10_23_01_23_56.csv"

    if not os.path.exists(test_file):
        print(f"⚠️ Test file not found: {test_file}")
        print("   Please ensure you have CSV data files in the expected location")
        return False

    try:
        result = ingestor.ingest_csv_file(test_file)

        if result['success']:
            print("✅ CSV ingestion successful!")
            print(f"   - Asset: {result.get('asset', 'N/A')}")
            print(f"   - Timeframe: {result.get('timeframe', 'N/A')}")
            print(f"   - Records processed: {result.get('records_processed', 0)}")
            print(f"   - Processing time: {result.get('processing_time_seconds', 0):.2f}s")
        else:
            print(f"❌ CSV ingestion failed: {result.get('error', 'Unknown error')}")
            return False

        return True

    except Exception as e:
        print(f"❌ CSV ingestion test failed: {e}")
        return False


def test_data_queries():
    """Test data querying functionality."""
    print("\n📥 Testing data queries...")

    querier = SupabaseDataQueries()

    try:
        # Test getting available assets
        assets = querier.get_asset_symbols()
        print(f"✅ Found {len(assets)} available assets")
        if assets:
            print(f"   Sample assets: {assets[:5]}")

        # Test getting candles for EURUSD
        df = querier.get_candles('EURUSD_otc', '1m', limit=5)
        if not df.empty:
            print(f"✅ Retrieved {len(df)} EURUSD 1m candles")
            print("   Sample data:")
            print(df.head(3).to_string(index=False))
        else:
            print("⚠️ No EURUSD 1m data found (this is expected if no data was ingested yet)")

        # Test getting latest candle
        latest = querier.get_latest_candle('EURUSD_otc', '1m')
        if latest:
            print("✅ Retrieved latest EURUSD 1m candle")
            print(f"   Timestamp: {latest['timestamp']}")
            print(f"   Close: {latest['close']}")
        else:
            print("⚠️ No latest candle found")

        # Test data summary
        summary = querier.get_data_summary()
        if summary:
            print("✅ Data summary retrieved:")
            print(f"   - Total assets: {summary.get('total_assets', 0)}")
            print(f"   - Total candles: {summary.get('total_candles', 0)}")
            if 'timeframes' in summary:
                print(f"   - Timeframes: {summary['timeframes']}")

        return True

    except Exception as e:
        print(f"❌ Data queries test failed: {e}")
        return False


def test_error_handling():
    """Test error handling scenarios."""
    print("\n🛡️ Testing error handling...")

    ingestor = SupabaseCSVIngestion()
    querier = SupabaseDataQueries()

    try:
        # Test with non-existent file
        result = ingestor.ingest_csv_file("non_existent_file.csv")
        if not result['success']:
            print("✅ Correctly handled non-existent file")
        else:
            print("❌ Should have failed for non-existent file")

        # Test querying non-existent asset
        df = querier.get_candles('NONEXISTENT_otc', '1m')
        if df.empty:
            print("✅ Correctly handled non-existent asset query")
        else:
            print("❌ Should have returned empty DataFrame for non-existent asset")

        return True

    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False


def run_full_test_suite():
    """Run the complete test suite."""
    print("🧪 QuFLX Supabase Integration Test Suite")
    print("=" * 50)

    tests = [
        ("Database Connection", test_database_connection),
        ("CSV Ingestion", test_csv_ingestion),
        ("Data Queries", test_data_queries),
        ("Error Handling", test_error_handling),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: CRASHED - {e}")

    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! Supabase integration is working correctly.")
        print("\nNext steps:")
        print("1. Run the database schema SQL in Supabase SQL Editor")
        print("2. Run: python scripts/init_supabase_db.py")
        print("3. Run: python scripts/ingest_all_csv_data.py")
    else:
        print("⚠️ Some tests failed. Please check the errors above and fix issues before proceeding.")

    return passed == total


if __name__ == "__main__":
    success = run_full_test_suite()
    exit(0 if success else 1)