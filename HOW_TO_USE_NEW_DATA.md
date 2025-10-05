# How to Use Your New Historical Data for Strategy Testing

## ✅ Setup Complete!

Your data from `data/data_output/assets_data/data_collect/` is now integrated and ready for backtesting!

## 📊 Data Summary

**Format**: `timestamp,open,close,high,low` (UTC timestamps with 'Z' suffix)

**Files by Timeframe:**
- 1M (1-minute) candles: **44 CSV files**
- 5M (5-minute) candles: **23 CSV files**  
- 15M (15-minute) candles: **23 CSV files**
- 1H (1-hour) candles: **4 CSV files**

**Total**: ~**95 fresh CSV files** from October 2025!

## 🚀 How to Use for Backtesting

### Method 1: Via GUI (Easiest)

1. **Start the backends**:
   ```bash
   cd gui/Data-Visualizer-React
   uv run python streaming_server.py
   ```

2. **Start the frontend** (new terminal):
   ```bash
   cd gui/Data-Visualizer-React
   npm run dev
   ```

3. **Open browser**: http://localhost:5000

4. **Run backtest**:
   - Click "Strategy Backtest" page
   - Select file from dropdown (new files will appear automatically!)
   - Choose strategy (Quantum Flux)
   - Click "Run Backtest"
   - View results!

### Method 2: Via Python (Programmatic)

```python
from gui.Data_Visualizer_React.data_loader import DataLoader

# Initialize loader
loader = DataLoader()

# Load data for any asset/timeframe
df = loader.load_asset_data('AUDCAD', '1m')  # Automatically finds latest AUDCAD 1m file
print(f"Loaded {len(df)} candles")

# Or load specific file
df = loader.load_csv('data/data_output/assets_data/data_collect/1M_candles/EURUSD_otc_otc_1m_2025_10_04_18_56_34.csv')
```

### Method 3: Direct File Access

All files are now searchable! The data loader searches both:
- `gui/Data-Visualizer-React/data_history/pocket_option/` (old location)
- `data/data_output/assets_data/data_collect/` (new location)

## 📁 Available Assets

Based on your new data, you can backtest:
- **AUDCAD** (1m, 5m, 15m)
- **EURUSD** (1m, 5m, 15m)
- **AUDCHF** (5m, 15m)
- **AUDNZD** (5m, 15m)
- **AUDUSD** (5m, 15m)
- **CADJPY** (5m, 15m)
- **EURCHF** (5m, 15m)
- **EURJPY** (5m, 15m)
- And many more OTC pairs!

## ⚡ Quick Test

Try backtesting AUDCAD on fresh October data:

```python
from gui.Data_Visualizer_React.data_loader import DataLoader, BacktestEngine
from strategies.quantum_flux_strategy import QuantumFluxStrategy

# Load data
loader = DataLoader()
df = loader.load_asset_data('AUDCAD', '1m')  # Gets latest AUDCAD 1m file
candles = loader.df_to_candles(df)

# Run backtest
strategy = QuantumFluxStrategy()
engine = BacktestEngine(strategy)
results = engine.run_backtest(candles)

print(f"Win Rate: {results['win_rate']:.1f}%")
print(f"Total Profit: ${results['total_profit']:.2f}")
print(f"Total Trades: {results['total_trades']}")
```

## 🔍 Sample Data

**AUDCAD 1M** (101 candles):
- Date: October 4, 2025
- Time range: 19:16 - 20:56 UTC
- First price: 0.97756
- Format: Properly timestamped UTC

## 🎯 Next Steps

1. **Test multiple timeframes**: Compare 1m vs 5m vs 15m strategies
2. **Test multiple assets**: See which pairs work best with Quantum Flux
3. **Optimize parameters**: Use backtesting to tune strategy settings
4. **Compare results**: Track which timeframe/asset combinations perform best

## ✨ Benefits

- **Fresh October 2025 data**: Most recent market conditions
- **Multiple timeframes**: Test across different trading speeds
- **95+ files**: Comprehensive testing across many assets
- **Auto-discovery**: Just select from dropdown - it's all there!

Your backtesting system now has access to all this data automatically! 🚀
