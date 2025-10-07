import io from 'socket.io-client';

export class WebSocketProvider {
  constructor(url) {
    this.url = url || `${window.location.protocol}//${window.location.hostname}:3001`;
    this.socket = null;
    this.connected = false;
    this.subscriptions = new Map();
    this.subscriptionCounter = 0;
  }

  async connect() {
    return new Promise((resolve) => {
      this.socket = io(this.url, {
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionDelay: 1000,
      });

      this.socket.on('connect', () => {
        console.log('WebSocket Provider connected');
        this.connected = true;
        resolve({ success: true, provider: 'websocket' });
      });

      this.socket.on('disconnect', () => {
        console.log('WebSocket Provider disconnected');
        this.connected = false;
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        resolve({ success: false, error: error.message });
      });
    });
  }

  async disconnect() {
    if (this.socket) {
      this.subscriptions.forEach((sub) => {
        this.socket.emit('stop_stream', {
          asset: sub.asset,
          timeframe: sub.timeframe
        });
      });
      this.subscriptions.clear();
      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
    return { success: true };
  }

  async fetchHistoricalData(asset, timeframe, startDate = null, endDate = null) {
    return new Promise((resolve) => {
      if (!this.connected) {
        resolve({ success: false, error: 'Not connected to WebSocket server' });
        return;
      }

      this.socket.emit('request_historical', {
        asset,
        timeframe,
        startDate,
        endDate
      });

      this.socket.once('historical_data', (response) => {
        resolve({
          success: true,
          data: response.data,
          asset: response.asset,
          timeframe: response.timeframe,
          provider: 'websocket'
        });
      });

      this.socket.once('historical_error', (error) => {
        resolve({ success: false, error: error.message });
      });
    });
  }

  async subscribe(asset, timeframe, callback) {
    if (!this.connected) {
      return { success: false, error: 'Not connected to WebSocket server' };
    }

    const subscriptionId = `sub_${++this.subscriptionCounter}`;

    this.socket.emit('start_stream', { asset, timeframe });

    const tickHandler = (data) => {
      if (data.asset === asset) {
        callback({
          type: 'tick',
          data: data.tick,
          asset: data.asset,
          timestamp: data.timestamp
        });
      }
    };

    const candleHandler = (data) => {
      if (data.asset === asset) {
        callback({
          type: 'candle',
          data: data.candle,
          asset: data.asset,
          timestamp: data.timestamp
        });
      }
    };

    this.socket.on('price_tick', tickHandler);
    this.socket.on('candle_update', candleHandler);

    this.subscriptions.set(subscriptionId, {
      asset,
      timeframe,
      tickHandler,
      candleHandler
    });

    return {
      success: true,
      subscriptionId,
      asset,
      timeframe
    };
  }

  async unsubscribe(subscriptionId) {
    const subscription = this.subscriptions.get(subscriptionId);
    if (!subscription) {
      return { success: false, error: 'Subscription not found' };
    }

    this.socket.emit('stop_stream', {
      asset: subscription.asset,
      timeframe: subscription.timeframe
    });
    this.socket.off('price_tick', subscription.tickHandler);
    this.socket.off('candle_update', subscription.candleHandler);
    this.subscriptions.delete(subscriptionId);

    return { success: true };
  }

  getAssets() {
    return [
      { id: 'EURUSD_OTC', name: 'EUR/USD OTC' },
      { id: 'GBPUSD_OTC', name: 'GBP/USD OTC' },
      { id: 'USDJPY_OTC', name: 'USD/JPY OTC' },
      { id: 'AUDUSD_OTC', name: 'AUD/USD OTC' },
    ];
  }

  supportsLiveStreaming() {
    return true;
  }
}
