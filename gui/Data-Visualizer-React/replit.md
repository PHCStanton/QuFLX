# Binary Options Data Analyzer

## Project Overview
A React-based trading data visualization and analysis platform for binary options trading. Features real-time charting with lightweight-charts, technical indicators, backtesting capabilities, and multiple chart types using Recharts.

## Recent Changes (September 30, 2025)
- **Navigation Restructure**: Completely rebuilt app with focused 3-tab layout:
  - Data Analysis: Historical data + live streaming with provider selection
  - Strategy & Backtest: Strategy management and backtesting
  - Live Trading: Signal generation and automated trading
- **Provider Abstraction Layer**: Created modular service architecture for backend integration:
  - DataProviderService: Provider-agnostic data access
  - StrategyService: JSON/Python strategy management
  - TradingService: Live trading execution
  - Multiple providers: CSV (historical), WebSocket (live), Platform API (future)
- **Backend Integration Ready**: Clean interfaces for plugging in modular backend modules
- **Documentation**: Complete API contracts and integration guides in `src/services/README.md`

## Project Architecture

### Tech Stack
- **Frontend Framework**: React 18.3.1
- **Build Tool**: Vite 5.4.1
- **Routing**: React Router DOM 6.30.1
- **Charts**: 
  - lightweight-charts 4.2.0 (candlestick charts)
  - Recharts 2.15.1 (various chart types)
- **Technical Analysis**: technicalindicators 3.1.0
- **Styling**: Tailwind CSS + Material-UI
- **Real-Time**: Socket.IO-client 4.x for WebSocket connections
- **Backend**: Python 3.11, Flask, Flask-SocketIO, Flask-CORS
- **Package Manager**: npm (originally pnpm)

### Project Structure
```
src/
├── pages/               # Main application pages
│   ├── DataAnalysis.jsx        # Historical data + live streaming
│   ├── StrategyBacktest.jsx    # Strategy management + backtesting
│   └── LiveTrading.jsx         # Signal generation + live trading
├── services/            # Service layer (backend integration)
│   ├── DataProviderService.js  # Provider management
│   ├── StrategyService.js      # Strategy execution + backtesting
│   ├── TradingService.js       # Live trading API
│   ├── providers/
│   │   ├── CSVProvider.js      # Local CSV files
│   │   ├── WebSocketProvider.js # Real-time streaming
│   │   └── PlatformAPIProvider.js # Platform REST API
│   └── README.md        # API contracts & integration guide
├── components/
│   ├── charts/          # Chart components
│   └── Header.jsx       # App header
├── hooks/
│   └── useWebSocket.js  # WebSocket hook
├── utils/               # Utilities
└── App.jsx

streaming_server.py      # Demo WebSocket server (port 3001)
public/data/             # CSV trading data files
```

### Key Configuration
- **Frontend Server**: Port 5000, host 0.0.0.0
- **Backend Server**: Port 3001, host 0.0.0.0 (WebSocket streaming)
- **Deployment**: Autoscale deployment with build step
- **Content Security Policy**: Configured for lightweight-charts and unpkg CDN
- **WebSocket**: Socket.IO with polling and WebSocket transports

### Routes
- `/` - Data Analysis (historical data + live streaming)
- `/strategy` - Strategy & Backtest (strategy management + backtesting)
- `/live` - Live Trading (signal generation + automated trading)

### Backend Integration Architecture

The frontend is designed for **modular backend integration** without code changes:

1. **Provider Pattern**: All data sources implement a common interface
   - `connect()`, `disconnect()`, `fetchHistoricalData()`, `subscribe()`, `unsubscribe()`
   - Easy to add new providers (APIs, databases, streaming services)

2. **Service Layer**: Clean separation of concerns
   - **DataProviderService**: Manages data sources (CSV, WebSocket, APIs)
   - **StrategyService**: Loads and executes JSON/Python strategies
   - **TradingService**: Executes trades via platform APIs

3. **API Contracts**: Fully documented in `src/services/README.md`
   - REST endpoints for trading, historical data, account info
   - WebSocket events for real-time streaming
   - Strategy execution interface

4. **Usage Pattern**:
```javascript
import { dataProviderService, YourBackendProvider } from './services';

const provider = new YourBackendProvider(config);
dataProviderService.registerProvider('your-backend', provider);
dataProviderService.setProvider('your-backend');
await dataProviderService.connect();
```

This architecture ensures your backend modules plug in without "train smash" integration issues.

## Development
```bash
npm install
npm run dev
```

## Deployment
- Build command: `npm run build`
- Run command: `npx vite preview --host 0.0.0.0 --port 5000`
- Deployment type: Autoscale (stateless frontend)
