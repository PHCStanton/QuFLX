class DataProviderService {
  constructor() {
    this.providers = new Map();
    this.currentProvider = null;
    this.currentProviderName = null;
  }

  registerProvider(name, provider) {
    if (!this.validateProvider(provider)) {
      throw new Error(`Invalid provider: ${name}. Provider must implement required interface.`);
    }
    this.providers.set(name, provider);
  }

  validateProvider(provider) {
    const requiredMethods = ['connect', 'disconnect', 'fetchHistoricalData', 'subscribe', 'unsubscribe', 'getAssets', 'supportsLiveStreaming'];
    return requiredMethods.every(method => typeof provider[method] === 'function');
  }

  async setProvider(name) {
    if (!this.providers.has(name)) {
      throw new Error(`Provider not found: ${name}`);
    }
    if (this.currentProvider) {
      await this.currentProvider.disconnect();
    }
    this.currentProvider = this.providers.get(name);
    this.currentProviderName = name;
    return this.currentProvider;
  }

  async connect() {
    if (!this.currentProvider) {
      throw new Error('No provider selected');
    }
    return await this.currentProvider.connect();
  }

  async fetchHistoricalData(asset, timeframe, startDate, endDate) {
    if (!this.currentProvider) {
      throw new Error('No provider selected');
    }
    return await this.currentProvider.fetchHistoricalData(asset, timeframe, startDate, endDate);
  }

  async subscribe(asset, timeframe, callback) {
    if (!this.currentProvider) {
      throw new Error('No provider selected');
    }
    return await this.currentProvider.subscribe(asset, timeframe, callback);
  }

  async unsubscribe(subscriptionId) {
    if (!this.currentProvider) {
      throw new Error('No provider selected');
    }
    return await this.currentProvider.unsubscribe(subscriptionId);
  }

  async disconnect() {
    if (this.currentProvider) {
      await this.currentProvider.disconnect();
      this.currentProvider = null;
      this.currentProviderName = null;
    }
  }

  getAvailableProviders() {
    return Array.from(this.providers.keys());
  }

  getCurrentProvider() {
    return this.currentProvider;
  }

  getCurrentProviderName() {
    return this.currentProviderName;
  }

  getAssets() {
    if (!this.currentProvider) {
      return [];
    }
    return this.currentProvider.getAssets();
  }

  supportsLiveStreaming() {
    if (!this.currentProvider) {
      return false;
    }
    return this.currentProvider.supportsLiveStreaming();
  }
}

export const dataProviderService = new DataProviderService();
