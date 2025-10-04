import { parseTradingData } from '../../utils/tradingData';

export class CSVProvider {
  constructor() {
    this.connected = false;
    this.availableAssets = [];
  }

  async connect() {
    try {
      const response = await fetch('/data/available_pairs.json');
      this.availableAssets = await response.json();
      this.connected = true;
      return { success: true, assets: this.availableAssets };
    } catch (error) {
      console.error('CSV Provider connection failed:', error);
      return { success: false, error: error.message };
    }
  }

  async disconnect() {
    this.connected = false;
    return { success: true };
  }

  async fetchHistoricalData(asset, timeframe, startDate = null, endDate = null) {
    if (!this.connected) {
      await this.connect();
    }

    try {
      const assetInfo = this.availableAssets.find(a => a.id === asset);
      if (!assetInfo) {
        throw new Error(`Asset not found: ${asset}`);
      }

      const response = await fetch(`/data/${assetInfo.file}`, { cache: 'no-store' });
      const csvText = await response.text();
      const data = parseTradingData(csvText, asset);

      let filteredData = data;
      if (startDate || endDate) {
        filteredData = data.filter(candle => {
          const candleTime = candle.time;
          return (!startDate || candleTime >= startDate) && (!endDate || candleTime <= endDate);
        });
      }

      return {
        success: true,
        data: filteredData,
        asset,
        timeframe,
        provider: 'csv'
      };
    } catch (error) {
      console.error('CSV fetch error:', error);
      return { success: false, error: error.message };
    }
  }

  async subscribe(asset, timeframe, callback) {
    console.warn('CSV Provider does not support live streaming');
    return { success: false, error: 'Live streaming not supported for CSV provider' };
  }

  async unsubscribe(subscriptionId) {
    return { success: true };
  }

  getAssets() {
    return this.availableAssets;
  }

  supportsLiveStreaming() {
    return false;
  }
}
