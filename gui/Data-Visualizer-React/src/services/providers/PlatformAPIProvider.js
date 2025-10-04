export class PlatformAPIProvider {
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || '';
    this.apiKey = config.apiKey || '';
    this.connected = false;
    this.subscriptions = new Map();
  }

  async connect() {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          apiKey: this.apiKey
        })
      });

      const result = await response.json();
      
      if (result.success) {
        this.connected = true;
        return { success: true, provider: 'platform-api' };
      }
      
      return { success: false, error: result.message };
    } catch (error) {
      console.error('Platform API connection failed:', error);
      return { success: false, error: error.message };
    }
  }

  async disconnect() {
    if (this.connected) {
      this.subscriptions.forEach((subscription) => {
        subscription.eventSource.close();
      });
      this.subscriptions.clear();

      await fetch(`${this.baseUrl}/api/v1/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });
      this.connected = false;
    }
    return { success: true };
  }

  async fetchHistoricalData(asset, timeframe, startDate = null, endDate = null) {
    if (!this.connected) {
      return { success: false, error: 'Not connected to Platform API' };
    }

    try {
      const params = new URLSearchParams({
        asset,
        timeframe,
        ...(startDate && { start: startDate }),
        ...(endDate && { end: endDate })
      });

      const response = await fetch(`${this.baseUrl}/api/v1/historical?${params}`, {
        headers: {
          'Authorization': `Bearer ${this.apiKey}`
        }
      });

      const result = await response.json();
      
      return {
        success: true,
        data: result.data,
        asset,
        timeframe,
        provider: 'platform-api'
      };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async subscribe(asset, timeframe, callback) {
    if (!this.connected) {
      return { success: false, error: 'Not connected to Platform API' };
    }

    const subscriptionId = `platform_${Date.now()}`;
    const url = `${this.baseUrl}/api/v1/stream?asset=${asset}&timeframe=${timeframe}&token=${this.apiKey}`;
    
    const eventSource = new EventSource(url);

    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      callback({
        type: data.type,
        data: data.payload,
        asset: data.asset,
        timestamp: data.timestamp
      });
    };

    eventSource.onerror = (error) => {
      console.error('Stream error:', error);
      this.subscriptions.delete(subscriptionId);
      eventSource.close();
    };

    this.subscriptions.set(subscriptionId, {
      eventSource,
      asset,
      timeframe
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

    subscription.eventSource.close();
    this.subscriptions.delete(subscriptionId);
    return { success: true };
  }

  getAssets() {
    return [
      { id: 'EURUSD', name: 'EUR/USD' },
      { id: 'GBPUSD', name: 'GBP/USD' },
      { id: 'USDJPY', name: 'USD/JPY' },
      { id: 'AUDUSD', name: 'AUD/USD' },
    ];
  }

  supportsLiveStreaming() {
    return true;
  }
}
