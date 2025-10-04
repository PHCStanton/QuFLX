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
    
    def load_asset_data(self, asset: str, timeframe: str = "1m", 
                        date: Optional[str] = None) -> pd.DataFrame:
        """Load asset data from standard naming convention.
        
        Args:
            asset: Asset name (e.g., 'AUDCAD_otc_otc')
            timeframe: Timeframe ('1m' or '5m')
            date: Optional date in format '2025_10_04_18_57_10'
        
        Returns:
            DataFrame with OHLC data
        """
        # Find matching files
        pattern = f"{asset}_{timeframe}_*"
        files = list(self.data_dir.glob(pattern))
        
        if not files:
            raise FileNotFoundError(f"No data files found for {asset} {timeframe}")
        
        # Use most recent file if no date specified
        file_path = files[-1] if date is None else None
        
        if date:
            for f in files:
                if date in f.name:
                    file_path = f
                    break
        
        if not file_path:
            raise FileNotFoundError(f"No file found matching date {date}")
        
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
        for file_path in self.data_dir.glob("*_[15]m_*"):
            parts = file_path.stem.split('_')
            if len(parts) >= 4:
                asset = '_'.join(parts[:-7])  # Everything before timeframe
                timeframe = parts[-7]  # e.g., '1m' or '5m'
                
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
                    
                    if won:
                        profit = trade_amount * payout
                        balance += profit
                        win_count += 1
                    else:
                        balance -= trade_amount
                        loss_count += 1
                    
                    trades.append({
                        'timestamp': entry_candle['timestamp'],
                        'signal': signal,
                        'entry_price': entry_price,
                        'exit_price': exit_price,
                        'won': won,
                        'profit': profit if won else -trade_amount,
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
