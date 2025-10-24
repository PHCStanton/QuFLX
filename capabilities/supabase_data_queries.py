#!/usr/bin/env python3
"""
Supabase Data Query Module for QuFLX

Provides functions to query and retrieve trading data from Supabase database.
Supports time-series queries, asset filtering, and data aggregation.

Usage:
    from capabilities.supabase_data_queries import SupabaseDataQueries

    querier = SupabaseDataQueries()
    df = querier.get_candles('EURUSD_otc', '1m', limit=1000)
"""

import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from config.supabase_config import SUPABASE_URL, SUPABASE_ANON_KEY
import logging


class SupabaseDataQueries:
    """
    Handles data retrieval and querying from Supabase database.
    Provides convenient methods for accessing trading data.
    """

    def __init__(self):
        """Initialize the Supabase data query client."""
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
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

    def get_asset_id(self, symbol: str) -> Optional[int]:
        """
        Get asset ID by symbol.

        Args:
            symbol: Asset symbol (e.g., 'EURUSD_otc')

        Returns:
            Asset ID or None if not found
        """
        try:
            result = self.supabase.table('assets').select('id').eq('symbol', symbol).execute()
            return result.data[0]['id'] if result.data else None
        except Exception as e:
            self.logger.error(f"Failed to get asset ID for '{symbol}': {e}")
            return None

    def get_candles(self, symbol: str, timeframe: str,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   limit: int = 1000) -> pd.DataFrame:
        """
        Retrieve candle data for a specific asset and timeframe.

        Args:
            symbol: Asset symbol (e.g., 'EURUSD_otc')
            timeframe: Timeframe (e.g., '1m', '5m', '1H')
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            limit: Maximum number of records to return

        Returns:
            DataFrame with candle data
        """
        try:
            asset_id = self.get_asset_id(symbol)
            if not asset_id:
                self.logger.warning(f"Asset '{symbol}' not found")
                return pd.DataFrame()

            # Build query
            query = self.supabase.table('candles')\
                .select('timestamp,open,high,low,close,volume')\
                .eq('asset_id', asset_id)\
                .eq('timeframe', timeframe)\
                .order('timestamp', desc=False)\
                .limit(limit)

            # Add date filters if provided
            if start_date:
                query = query.gte('timestamp', start_date.isoformat())
            if end_date:
                query = query.lte('timestamp', end_date.isoformat())

            result = query.execute()

            if not result.data:
                self.logger.info(f"No data found for {symbol} {timeframe}")
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(result.data)

            # Convert timestamp to datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            # Ensure numeric columns
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            self.logger.info(f"Retrieved {len(df)} candles for {symbol} {timeframe}")
            return df

        except Exception as e:
            self.logger.error(f"Failed to retrieve candles for {symbol} {timeframe}: {e}")
            return pd.DataFrame()

    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict[str, Any]]:
        """
        Get the most recent candle for an asset and timeframe.

        Args:
            symbol: Asset symbol
            timeframe: Timeframe

        Returns:
            Latest candle data or None if not found
        """
        try:
            asset_id = self.get_asset_id(symbol)
            if not asset_id:
                return None

            result = self.supabase.table('candles')\
                .select('timestamp,open,high,low,close,volume')\
                .eq('asset_id', asset_id)\
                .eq('timeframe', timeframe)\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()

            if result.data:
                candle = result.data[0]
                # Convert timestamp to datetime
                candle['timestamp'] = pd.to_datetime(candle['timestamp'], utc=True)
                return candle

            return None

        except Exception as e:
            self.logger.error(f"Failed to get latest candle for {symbol} {timeframe}: {e}")
            return None

    def get_candles_in_range(self, symbol: str, timeframe: str,
                           hours_back: int = 24) -> pd.DataFrame:
        """
        Get candles for the last N hours.

        Args:
            symbol: Asset symbol
            timeframe: Timeframe
            hours_back: Number of hours to look back

        Returns:
            DataFrame with candle data
        """
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(hours=hours_back)

        return self.get_candles(symbol, timeframe, start_date, end_date)

    def get_available_assets(self) -> List[Dict[str, Any]]:
        """
        Get list of all available assets.

        Returns:
            List of asset dictionaries
        """
        try:
            result = self.supabase.table('assets')\
                .select('id,symbol,base_currency,quote_currency,display_name,asset_type')\
                .eq('is_active', True)\
                .order('symbol')\
                .execute()

            return result.data if result.data else []

        except Exception as e:
            self.logger.error(f"Failed to retrieve available assets: {e}")
            return []

    def get_asset_symbols(self) -> List[str]:
        """
        Get list of all available asset symbols.

        Returns:
            List of asset symbols
        """
        assets = self.get_available_assets()
        return [asset['symbol'] for asset in assets]

    def get_timeframes_for_asset(self, symbol: str) -> List[str]:
        """
        Get available timeframes for a specific asset.

        Args:
            symbol: Asset symbol

        Returns:
            List of available timeframes
        """
        try:
            asset_id = self.get_asset_id(symbol)
            if not asset_id:
                return []

            result = self.supabase.table('candles')\
                .select('timeframe')\
                .eq('asset_id', asset_id)\
                .execute()

            if result.data:
                timeframes = list(set(row['timeframe'] for row in result.data))
                return sorted(timeframes)

            return []

        except Exception as e:
            self.logger.error(f"Failed to get timeframes for {symbol}: {e}")
            return []

    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get a summary of data available in the database.

        Returns:
            Dictionary with data summary statistics
        """
        try:
            summary = {}

            # Count total assets
            assets_result = self.supabase.table('assets').select('count', count='exact').execute()
            summary['total_assets'] = assets_result.count if hasattr(assets_result, 'count') else 0

            # Count total candles
            candles_result = self.supabase.table('candles').select('count', count='exact').execute()
            summary['total_candles'] = candles_result.count if hasattr(candles_result, 'count') else 0

            # Get timeframes distribution
            timeframes_result = self.supabase.table('candles')\
                .select('timeframe, count', count='exact')\
                .execute()

            summary['timeframes'] = {}
            if timeframes_result.data:
                for row in timeframes_result.data:
                    summary['timeframes'][row['timeframe']] = row['count']

            # Get date range
            date_result = self.supabase.table('candles')\
                .select('timestamp')\
                .order('timestamp', desc=False)\
                .limit(1)\
                .execute()

            if date_result.data:
                summary['earliest_date'] = date_result.data[0]['timestamp']

            date_result = self.supabase.table('candles')\
                .select('timestamp')\
                .order('timestamp', desc=True)\
                .limit(1)\
                .execute()

            if date_result.data:
                summary['latest_date'] = date_result.data[0]['timestamp']

            # Ingestion stats
            logs_result = self.supabase.table('ingestion_logs')\
                .select('status, count', count='exact')\
                .execute()

            summary['ingestion_stats'] = {}
            if logs_result.data:
                for row in logs_result.data:
                    summary['ingestion_stats'][row['status']] = row['count']

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get data summary: {e}")
            return {}

    def search_candles(self, symbol: Optional[str] = None,
                      timeframe: Optional[str] = None,
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      min_price: Optional[float] = None,
                      max_price: Optional[float] = None,
                      limit: int = 1000) -> pd.DataFrame:
        """
        Advanced search for candles with multiple filters.

        Args:
            symbol: Asset symbol filter
            timeframe: Timeframe filter
            start_date: Start date filter
            end_date: End date filter
            min_price: Minimum close price filter
            max_price: Maximum close price filter
            limit: Maximum results

        Returns:
            Filtered DataFrame
        """
        try:
            query = self.supabase.table('candles')\
                .select('assets(symbol),timestamp,open,high,low,close,volume,timeframe')

            # Apply filters
            if symbol:
                asset_id = self.get_asset_id(symbol)
                if asset_id:
                    query = query.eq('asset_id', asset_id)

            if timeframe:
                query = query.eq('timeframe', timeframe)

            if start_date:
                query = query.gte('timestamp', start_date.isoformat())

            if end_date:
                query = query.lte('timestamp', end_date.isoformat())

            if min_price is not None:
                query = query.gte('close', min_price)

            if max_price is not None:
                query = query.lte('close', max_price)

            result = query.order('timestamp', desc=False).limit(limit).execute()

            if not result.data:
                return pd.DataFrame()

            # Convert to DataFrame
            df = pd.DataFrame(result.data)

            # Flatten asset symbol
            if 'assets' in df.columns:
                df['symbol'] = df['assets'].apply(lambda x: x['symbol'] if isinstance(x, dict) else None)
                df = df.drop('assets', axis=1)

            # Convert timestamp
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)

            return df

        except Exception as e:
            self.logger.error(f"Failed to search candles: {e}")
            return pd.DataFrame()