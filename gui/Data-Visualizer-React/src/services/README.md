# Service Layer Architecture

This directory contains the service layer that provides clean interfaces for backend integration.

## Data Provider Service

The `DataProviderService` is a provider-agnostic service that manages different data sources.

### Provider Interface

All providers must implement:

```javascript
{
  connect(): Promise<{success: boolean, ...}>
  disconnect(): Promise<{success: boolean}>
  fetchHistoricalData(asset, timeframe, startDate?, endDate?): Promise<{success: boolean, data: []}>
  subscribe(asset, timeframe, callback): Promise<{success: boolean, subscriptionId: string}>
  unsubscribe(subscriptionId): Promise<{success: boolean}>
  getAssets(): Array<{id, name}>
  supportsLiveStreaming(): boolean
}
```

### Available Providers

1. **CSVProvider** - Local CSV files for historical data
   - No live streaming support
   - Reads from `/public/data` directory

2. **WebSocketProvider** - Real-time data via WebSocket
   - Connects to Socket.IO server (default: port 3001)
   - Supports live tick and candle updates
   - Event types: `price_tick`, `candle_update`

3. **PlatformAPIProvider** - Platform REST API + SSE streaming
   - Requires `baseUrl` and `apiKey` configuration
   - Supports both historical and live data
   - Uses Server-Sent Events for streaming

### Usage Example

```javascript
import { dataProviderService, CSVProvider, WebSocketProvider } from './services';

// Register providers
const csvProvider = new CSVProvider();
const wsProvider = new WebSocketProvider('http://localhost:3001');

dataProviderService.registerProvider('csv', csvProvider);
dataProviderService.registerProvider('websocket', wsProvider);

// Switch provider and connect
await dataProviderService.setProvider('csv');
await dataProviderService.connect();

// Get available assets
const assets = dataProviderService.getAssets();

// Check if live streaming is supported
if (dataProviderService.supportsLiveStreaming()) {
  // Subscribe to live data
  const subscription = await dataProviderService.subscribe('EURUSD', '1m', (data) => {
    console.log('New data:', data);
  });
} else {
  // Fetch historical data
  const result = await dataProviderService.fetchHistoricalData('EURUSD', '1m');
}
```

## Strategy Service

Manages trading strategies in JSON or Python format.

### Strategy Interface

```javascript
{
  id: string
  name: string
  type: 'json' | 'python'
  execute(candles, indicators): Promise<Signal[]>
}
```

### Signal Format

```javascript
{
  type: 'BUY' | 'SELL'
  confidence: number (0-1)
  reason: string
  timestamp?: number
}
```

### Usage Example

```javascript
import { strategyService } from './services';

// Load strategy from file
const result = await strategyService.loadStrategy(file);

// Run backtest
const backtestResult = await strategyService.runBacktest(
  strategyId,
  historicalData,
  {
    initialCapital: 10000,
    positionSize: 0.1,
    commission: 0.001
  }
);
```

## Trading Service

Handles live trading execution and position management.

### API Interface

Your backend should implement these endpoints:

**POST /api/v1/connect**
Request body:
```json
{
  "apiKey": "your-api-key"
}
```
Response: `{success: boolean, message?: string}`

**POST /api/v1/disconnect**
Response: `{success: boolean}`

**GET /api/v1/historical** (for PlatformAPIProvider)
Query parameters: `asset`, `timeframe`, `start?` (timestamp), `end?` (timestamp)
Headers: `Authorization: Bearer {apiKey}`
Response:
```json
{
  "success": true,
  "data": [
    {"time": 1234567890, "open": 1.1234, "high": 1.1250, "low": 1.1220, "close": 1.1240, "volume": 1000}
  ]
}
```

**POST /api/v1/trade**
```json
{
  "asset": "EURUSD",
  "direction": "BUY" | "SELL",
  "amount": 100,
  "duration": 60,
  "stopLoss"?: number,
  "takeProfit"?: number,
  "signalConfidence"?: number
}
```
Response: `{success: boolean, orderId: string, entryPrice: number}`

**POST /api/v1/trade/{orderId}/close**
Response: `{success: boolean, exitPrice: number, pnl: number}`

**GET /api/v1/account**
Response: `{balance: number, equity: number, positions: []}`

**GET /api/v1/stream** (Server-Sent Events)
Query parameters: `asset`, `timeframe`, `token` (auth)
Events: `{type: string, payload: object, asset: string, timestamp: number}`

**POST /api/strategy/execute** (Python strategy execution - must be sandboxed)
Request body:
```json
{
  "code": "strategy python code",
  "candles": [],
  "indicators": {}
}
```
Response: `{signals: [{type: 'BUY'|'SELL', confidence: number, reason: string}]}`

**WebSocket Events** (for WebSocketProvider):
- Emit `start_stream`: `{asset: string, timeframe: string}`
- Emit `stop_stream`: `{asset: string, timeframe: string}`
- Listen `price_tick`: `{asset: string, tick: {price: number, timestamp: number}}`
- Listen `candle_update`: `{asset: string, candle: {open, high, low, close, time}}`

### Usage Example

```javascript
import { tradingService } from './services';

// Connect to platform
await tradingService.connect({
  baseUrl: 'https://api.platform.com',
  apiKey: 'your-api-key'
});

// Execute a signal
const result = await tradingService.executeSignal(signal, {
  defaultAmount: 100,
  duration: 60,
  stopLoss: 0.02,
  takeProfit: 0.05
});

// Close position
await tradingService.closePosition(orderId);
```

## Integration with Your Backend

To integrate your modular backend:

1. **Implement the provider interface** in your backend module
2. **Register it** with the DataProviderService
3. **Implement the API endpoints** for trading (if needed)
4. **Use the services** in your React components

Example backend integration:

```javascript
// In your backend module
export class YourBackendProvider {
  async connect() { /* your implementation */ }
  async fetchHistoricalData(asset, timeframe) { /* your implementation */ }
  async subscribe(asset, timeframe, callback) { /* your implementation */ }
  // ... other methods
}

// In your frontend initialization
import { YourBackendProvider } from './backend/YourBackendProvider';
import { dataProviderService } from './services';

const provider = new YourBackendProvider();
dataProviderService.registerProvider('your-backend', provider);
dataProviderService.setProvider('your-backend');
```

This architecture ensures your backend modules can plug in without modifying the frontend components.
