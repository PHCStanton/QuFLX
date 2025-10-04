"""Data loader for historical CSV data and live streaming data."""

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DataLoader:
    """Load historical CSV data for backtesting."""
    
    def __init__(self, data_dir: str = "data_history/pocket_option"):
        self.data_dir = Path(data_dir)
    
    def load_csv(self, file_path: str) -> pd.DataFrame:
        """Load CSV file and return DataFrame."""
        try:
            df = pd.read_csv(file_path)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Add volume column if missing (default to 1000)
            if 'volume' not in df.columns:
                df['volume'] = 1000.0
            
            return df
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
            raise
    
    def load_asset_data(self, asset: str, timeframe: str = "1m") -> pd.DataFrame:
        """Load asset data from standard naming convention or direct path.
        
        Args:
            asset: Asset name (e.g., 'AUDCAD_otc_otc') or full file path
            timeframe: Timeframe ('1m' or '5m') - ignored if asset is a file path
        
        Returns:
            DataFrame with OHLC data
        """
        # Check if asset is actually a file path
        asset_path = Path(asset)
        if asset_path.exists() and asset_path.is_file():
            logger.info(f"Loading data from direct path: {asset}")
            return self.load_csv(str(asset_path))
        
        # Otherwise, search by asset name and timeframe
        # Get all available files and filter by asset and timeframe
        all_files = self.get_available_files()
        
        # Try exact match first (case-insensitive)
        exact_matches = [
            f for f in all_files 
            if f['asset'].lower() == asset.lower() and f['timeframe'] == timeframe
        ]
        
        # Fallback to partial match if no exact match
        if not exact_matches:
            exact_matches = [
                f for f in all_files 
                if asset.lower() in f['asset'].lower() and f['timeframe'] == timeframe
            ]
        
        if not exact_matches:
            raise FileNotFoundError(f"No data files found for {asset} {timeframe}")
        
        # Sort by filename (most recent timestamp last) and use the last one
        matching_files = sorted(exact_matches, key=lambda x: x['filename'])
        file_info = matching_files[-1]
        file_path = file_info['path']
        
        logger.info(f"Loading data from {file_path}")
        return self.load_csv(file_path)
    
    def df_to_candles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert DataFrame to list of candle dictionaries."""
        candles = []
        for _, row in df.iterrows():
            candles.append({
                'timestamp': row['timestamp'].isoformat(),
                'open': float(row['open']),
                'high': float(row['high']),
                'low': float(row['low']),
                'close': float(row['close']),
                'volume': float(row.get('volume', 1000.0))
            })
        return candles
    
    def get_available_files(self) -> List[Dict[str, str]]:
        """Get list of available data files."""
        files = []
        # Search for all CSV files recursively
        for file_path in self.data_dir.rglob("*.csv"):
            if file_path.is_file():
                # Try to extract timeframe from filename first
                parts = file_path.stem.split('_')
                timeframe = None
                asset = None
                
                # Method 1: Look for timeframe in filename (e.g., ASSET_1m_date)
                for i, part in enumerate(parts):
                    if part in ['1m', '5m', '15m', '1h', '4h', '1d']:
                        timeframe = part
                        asset = '_'.join(parts[:i])
                        break
                
                # Method 2: Infer from parent directory name (e.g., data_1m, data_5m)
                if not timeframe:
                    parent_dir = file_path.parent.name
                    if 'data_1m' in parent_dir or '1m' in parent_dir.lower():
                        timeframe = '1m'
                    elif 'data_5m' in parent_dir or '5m' in parent_dir.lower():
                        timeframe = '5m'
                    elif '15m' in parent_dir.lower():
                        timeframe = '15m'
                    
                    # Extract asset from filename
                    asset = parts[0] if parts else 'Unknown'
                
                # Method 3: Default fallback
                if not timeframe:
                    timeframe = 'unknown'
                if not asset:
                    asset = file_path.stem
                
                files.append({
                    'filename': file_path.name,
                    'asset': asset,
                    'timeframe': timeframe,
                    'path': str(file_path)
                })
        
        return files


class BacktestEngine:
    """Execute strategy backtesting on historical data."""
    
    def __init__(self, strategy):
        self.strategy = strategy
    
    def run_backtest(self, candles: List[Dict[str, Any]], 
                     window_size: int = 50) -> Dict[str, Any]:
        """Run backtest on candle data.
        
        Args:
            candles: List of candle dictionaries
            window_size: Number of candles to use for each signal
        
        Returns:
            Backtest results with trades and statistics
        """
        trades = []
        equity_curve = []
        balance = 10000.0  # Starting balance
        win_count = 0
        loss_count = 0
        
        for i in range(window_size, len(candles)):
            # Get window of candles for strategy
            window = candles[i-window_size:i]
            
            # Generate signal
            signal = self.strategy.execute(window)
            
            if signal in ['call', 'put']:
                entry_candle = candles[i]
                entry_price = entry_candle['close']
                
                # Simulate next candle outcome (simplified)
                if i + 1 < len(candles):
                    exit_candle = candles[i + 1]
                    exit_price = exit_candle['close']
                    
                    # Determine win/loss
                    if signal == 'call':
                        won = exit_price > entry_price
                    else:  # put
                        won = exit_price < entry_price
                    
                    trade_amount = balance * 0.01  # 1% per trade
                    payout = 0.8  # 80% payout
                    
                    # Calculate profit/loss
                    if won:
                        profit = trade_amount * payout
                        balance += profit
                        win_count += 1
                    else:
                        profit = -trade_amount
                        balance -= trade_amount
                        loss_count += 1
                    
                    trades.append({
                        'timestamp': entry_candle['timestamp'],
                        'signal': signal,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'won': won,
                        'profit': profit,
                        'balance': balance
                    })
                    
                    equity_curve.append({
                        'timestamp': entry_candle['timestamp'],
                        'balance': balance
                    })
        
        total_trades = win_count + loss_count
        win_rate = (win_count / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'trades': trades,
            'equity_curve': equity_curve,
            'statistics': {
                'total_trades': total_trades,
                'wins': win_count,
                'losses': loss_count,
                'win_rate': win_rate,
                'starting_balance': 10000.0,
                'ending_balance': balance,
                'total_profit': balance - 10000.0,
                'profit_percentage': ((balance - 10000.0) / 10000.0) * 100
            }
        }
