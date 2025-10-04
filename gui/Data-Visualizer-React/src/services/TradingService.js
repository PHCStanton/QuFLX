class TradingService {
  constructor() {
    this.positions = new Map();
    this.orders = [];
    this.platformAPI = null;
    this.isConnected = false;
  }

  async connect(apiConfig) {
    try {
      const response = await fetch(`${apiConfig.baseUrl}/api/v1/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          apiKey: apiConfig.apiKey
        })
      });

      const result = await response.json();
      
      if (result.success) {
        this.platformAPI = apiConfig;
        this.isConnected = true;
        return { success: true };
      }

      return { success: false, error: result.message };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async disconnect() {
    if (this.isConnected && this.platformAPI) {
      await fetch(`${this.platformAPI.baseUrl}/api/v1/disconnect`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.platformAPI.apiKey}`
        }
      });
      this.isConnected = false;
      this.platformAPI = null;
    }
    return { success: true };
  }

  async executeSignal(signal, config = {}) {
    if (!this.isConnected) {
      return { success: false, error: 'Not connected to trading platform' };
    }

    const {
      asset = signal.asset,
      direction = signal.type,
      amount = config.defaultAmount || 100,
      duration = config.duration || 60,
      stopLoss = config.stopLoss,
      takeProfit = config.takeProfit
    } = config;

    try {
      const response = await fetch(`${this.platformAPI.baseUrl}/api/v1/trade`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.platformAPI.apiKey}`
        },
        body: JSON.stringify({
          asset,
          direction: direction.toUpperCase(),
          amount,
          duration,
          stopLoss,
          takeProfit,
          signalConfidence: signal.confidence
        })
      });

      const result = await response.json();
      
      if (result.success) {
        const order = {
          id: result.orderId,
          asset,
          direction,
          amount,
          entryPrice: result.entryPrice,
          timestamp: new Date().toISOString(),
          signal,
          status: 'open'
        };

        this.orders.push(order);
        this.positions.set(result.orderId, order);

        return {
          success: true,
          order
        };
      }

      return { success: false, error: result.message };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async closePosition(orderId) {
    if (!this.isConnected) {
      return { success: false, error: 'Not connected to trading platform' };
    }

    try {
      const response = await fetch(`${this.platformAPI.baseUrl}/api/v1/trade/${orderId}/close`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.platformAPI.apiKey}`
        }
      });

      const result = await response.json();
      
      if (result.success) {
        const position = this.positions.get(orderId);
        if (position) {
          position.status = 'closed';
          position.exitPrice = result.exitPrice;
          position.pnl = result.pnl;
          position.closedAt = new Date().toISOString();
        }

        this.positions.delete(orderId);

        return {
          success: true,
          result
        };
      }

      return { success: false, error: result.message };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  getPositions() {
    return Array.from(this.positions.values());
  }

  getOrders() {
    return this.orders;
  }

  getPosition(orderId) {
    return this.positions.get(orderId);
  }

  async getAccountInfo() {
    if (!this.isConnected) {
      return { success: false, error: 'Not connected to trading platform' };
    }

    try {
      const response = await fetch(`${this.platformAPI.baseUrl}/api/v1/account`, {
        headers: {
          'Authorization': `Bearer ${this.platformAPI.apiKey}`
        }
      });

      const result = await response.json();
      return { success: true, account: result };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

export const tradingService = new TradingService();
