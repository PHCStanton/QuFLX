# QuantumFlux React Trading Dashboard

A modern React-based trading dashboard for binary options with real-time data streaming, historical backtesting, and strategy execution capabilities.

## Features

### ✅ Completed & Operational
- **Real-time Data Streaming**: Live tick and candle updates via Socket.IO
- **Historical Backtesting**: Test strategies on 100+ historical CSV files
- **Strategy Execution**: Quantum Flux strategy with RSI, MACD, Bollinger Bands, EMAs
- **Interactive Charts**: Real-time visualization with Recharts
- **File Discovery**: Smart detection of multiple CSV formats (OTC & HLOC)
- **Signal Generation**: Trading signals with confidence scores
- **Socket.IO Integration**: Unified communication protocol for all backend operations

## Quick Start

### Prerequisites
- Node.js 16+ with npm/pnpm
- Python 3.11+ (for backend)
- uv (Python package installer)

### Installation

```bash
# Install dependencies
npm install
# or
pnpm install
```

### Running the Application

**Start Backend** (Terminal 1):
```bash
cd gui/Data-Visualizer-React
uv run python streaming_server.py
```

**Start Frontend** (Terminal 2):
```bash
cd gui/Data-Visualizer-React
npm run dev
```

**Access Dashboard**:
- Frontend: http://localhost:5000
- Backend API: http://localhost:3001

## Project Structure

```
gui/Data-Visualizer-React/
├── src/
│   ├── pages/
│   │   ├── DataAnalysis.jsx       # Historical data analysis
│   │   ├── LiveTrading.jsx        # Real-time trading interface
│   │   └── StrategyBacktest.jsx   # Backtesting interface ✨
│   ├── services/
│   │   ├── StrategyService.js     # Strategy management (Socket.IO)
│   │   ├── DataProviderService.js # Data provider abstraction
│   │   └── providers/
│   │       ├── CSVProvider.js     # CSV data loading
│   │       └── WebSocketProvider.js # Real-time data streaming
│   ├── components/
│   │   ├── charts/
│   │   │   └── LightweightChart.jsx # Chart components
│   │   ├── TradingChart.jsx
│   │   └── RealTimeChart.jsx
│   └── hooks/
│       └── useWebSocket.js        # WebSocket connection hook
├── data_loader.py                 # CSV loading & backtest engine ✨
├── streaming_server.py            # Flask-SocketIO backend ✨
└── data_history/pocket_option/    # Historical CSV files
```

## Backend API (Socket.IO)

### Events

**Client → Server:**
- `run_backtest` - Execute strategy backtest
  ```json
  { "file_path": "path/to/data.csv", "strategy": "quantum_flux" }
  ```
- `get_available_data` - List available CSV files
- `generate_signal` - Generate trading signal
  ```json
  { "candles": [...], "strategy": "quantum_flux" }
  ```
- `execute_strategy` - Execute strategy on live data
  ```json
  { "candles": [...], "strategy": "quantum_flux" }
  ```

**Server → Client:**
- `backtest_complete` - Backtest results
- `backtest_error` - Backtest error
- `available_data` - List of CSV files
- `signal_generated` - Generated trading signal
- `strategy_result` - Strategy execution result

### Real-time Streaming Events
- `start_stream` - Start price streaming
- `stop_stream` - Stop price streaming
- `tick_update` - Real-time price tick
- `candle_update` - New candle formed

## Data Format

### CSV Structure
```csv
timestamp,open,close,high,low
2025-10-04 12:00:00,1.0856,1.0858,1.0860,1.0855
```

### Candle Object
```typescript
{
  timestamp: string,  // ISO format
  open: number,
  high: number,
  low: number,
  close: number,
  volume: number      // Default: 1000.0
}
```

## Strategy Backtesting

Navigate to the **Strategy Backtest** page in the dashboard:

1. **Select Data File**: Choose from 100+ historical CSV files
2. **Select Strategy**: Quantum Flux (more strategies coming soon)
3. **Configure**:
   - Initial Capital: $10,000 (default)
   - Position Size: 1% per trade
4. **Run Backtest**: Click "Run Backtest" button
5. **View Results**:
   - Total trades, wins, losses
   - Win rate percentage
   - Profit/loss
   - Individual trade history

## Available Strategies

### Quantum Flux Strategy
- **Indicators**: RSI (14), MACD (12,26,9), Bollinger Bands (20,2), EMA (12,26)
- **Signal Types**: CALL, PUT, NEUTRAL
- **Confidence Scoring**: 0-100%
- **Minimum Candles**: 50

## Development

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

### Backend Development
```bash
# With auto-reload
uv run python streaming_server.py --reload
```

## Troubleshooting

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:3001/health

# Verify data files are accessible
ls data_history/pocket_option/
```

### Frontend Issues
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install

# Check browser console for errors
# Open DevTools (F12) → Console tab
```

### Connection Issues
- Ensure backend is running on port 3001
- Check firewall settings
- Verify Socket.IO connection in browser console

## Tech Stack

- **Frontend**: React 18, Vite 5, Recharts, Socket.IO Client, TailwindCSS
- **Backend**: Flask-SocketIO, Python 3.11
- **Data**: Pandas, NumPy (technical indicators)
- **Strategy**: Quantum Flux (RSI, MACD, Bollinger Bands, EMAs)

## Contributing

This is a trading platform for PocketOption automation. Follow existing code patterns and maintain type safety where possible.

## License

Proprietary - QuantumFlux Trading Platform
