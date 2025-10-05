import { io } from 'socket.io-client';

class StrategyService {
  constructor() {
    this.strategies = new Map();
    this.runningStrategies = new Map();
    this.socket = null;
    this.backtestCallbacks = new Map();
    this.signalCallbacks = new Map();
  }

  initializeSocket(url = 'http://localhost:3001') {
    if (this.socket) return this.socket;

    this.socket = io(url, {
      transports: ['websocket', 'polling'],
      reconnection: true
    });

    // Set up event listeners
    this.socket.on('backtest_complete', (data) => {
      const callback = this.backtestCallbacks.get('current');
      if (callback) {
        callback({ success: true, results: data.results });
        this.backtestCallbacks.delete('current');
      }
    });

    this.socket.on('backtest_error', (data) => {
      const callback = this.backtestCallbacks.get('current');
      if (callback) {
        callback({ success: false, error: data.error });
        this.backtestCallbacks.delete('current');
      }
    });

    this.socket.on('signal_generated', (data) => {
      const callback = this.signalCallbacks.get('current');
      if (callback) {
        callback({ success: true, signal: data });
        this.signalCallbacks.delete('current');
      }
    });

    this.socket.on('signal_error', (data) => {
      const callback = this.signalCallbacks.get('current');
      if (callback) {
        callback({ success: false, error: data.error });
        this.signalCallbacks.delete('current');
      }
    });

    this.socket.on('available_data', (data) => {
      const callback = this.backtestCallbacks.get('data_files');
      if (callback) {
        callback({ success: true, files: data.files });
        this.backtestCallbacks.delete('data_files');
      }
    });

    return this.socket;
  }

  registerStrategy(id, strategy) {
    if (!this.validateStrategy(strategy)) {
      throw new Error(`Invalid strategy: ${id}`);
    }
    this.strategies.set(id, {
      ...strategy,
      id,
      createdAt: new Date().toISOString()
    });
    return { success: true, id };
  }

  validateStrategy(strategy) {
    const requiredFields = ['name', 'type'];
    return requiredFields.every(field => strategy.hasOwnProperty(field));
  }

  async loadStrategy(file) {
    try {
      const text = await file.text();
      const extension = file.name.split('.').pop().toLowerCase();

      let strategy;
      
      if (extension === 'json') {
        strategy = JSON.parse(text);
        if (!strategy.name) {
          strategy.name = file.name.replace('.json', '');
        }
        strategy.type = 'json';
        strategy.execute = this.createJSONStrategyExecutor(strategy);
      } else if (extension === 'py') {
        strategy = {
          name: file.name.replace('.py', ''),
          type: 'python',
          code: text,
          execute: this.createPythonStrategyExecutor(text)
        };
      } else {
        throw new Error('Unsupported strategy file type');
      }

      const id = `strategy_${Date.now()}`;
      return this.registerStrategy(id, strategy);
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  createJSONStrategyExecutor(config) {
    return async (candles, indicators) => {
      const signals = [];
      
      if (config.rules) {
        for (const rule of config.rules) {
          const signal = this.evaluateRule(rule, candles, indicators);
          if (signal) {
            signals.push(signal);
          }
        }
      }

      return signals;
    };
  }

  createPythonStrategyExecutor(code) {
    return async (candles, indicators) => {
      if (!this.socket) {
        this.initializeSocket();
      }

      return new Promise((resolve) => {
        this.signalCallbacks.set('current', (result) => {
          if (result.success) {
            resolve([result.signal]);
          } else {
            resolve([]);
          }
        });

        this.socket.emit('generate_signal', {
          candles,
          strategy: 'quantum_flux'
        });
      });
    };
  }

  evaluateRule(rule, candles, indicators) {
    const lastCandle = candles[candles.length - 1];
    
    if (rule.type === 'crossover') {
      const fast = indicators[rule.fastIndicator];
      const slow = indicators[rule.slowIndicator];
      
      if (fast && slow && fast.length > 1 && slow.length > 1) {
        const fastPrev = fast[fast.length - 2];
        const fastCurr = fast[fast.length - 1];
        const slowPrev = slow[slow.length - 2];
        const slowCurr = slow[slow.length - 1];

        if (fastPrev < slowPrev && fastCurr > slowCurr) {
          return {
            type: 'CALL',
            confidence: 0.8,
            reason: `${rule.fastIndicator} crossed above ${rule.slowIndicator}`
          };
        } else if (fastPrev > slowPrev && fastCurr < slowCurr) {
          return {
            type: 'PUT',
            confidence: 0.8,
            reason: `${rule.fastIndicator} crossed below ${rule.slowIndicator}`
          };
        }
      }
    }

    return null;
  }

  async runBacktest(strategyId, filePath, config = {}) {
    if (!this.socket) {
      this.initializeSocket();
    }

    return new Promise((resolve) => {
      this.backtestCallbacks.set('current', resolve);

      this.socket.emit('run_backtest', {
        file_path: filePath,
        strategy: 'quantum_flux',
        ...config
      });
    });
  }

  async getAvailableDataFiles() {
    if (!this.socket) {
      this.initializeSocket();
    }

    // Wait for connection if not connected
    if (!this.socket.connected) {
      await new Promise((resolve) => {
        this.socket.once('connect', resolve);
      });
    }

    return new Promise((resolve) => {
      this.backtestCallbacks.set('data_files', resolve);
      this.socket.emit('get_available_data');
    });
  }

  async generateSignal(candles, strategyType = 'quantum_flux') {
    if (!this.socket) {
      this.initializeSocket();
    }

    return new Promise((resolve) => {
      this.signalCallbacks.set('current', resolve);
      
      this.socket.emit('generate_signal', {
        candles,
        strategy: strategyType
      });
    });
  }

  async executeStrategy(candles, strategyType = 'quantum_flux') {
    if (!this.socket) {
      this.initializeSocket();
    }

    return new Promise((resolve) => {
      const handler = (data) => {
        resolve({ success: true, signal: data.signal });
        this.socket.off('strategy_result', handler);
      };

      this.socket.on('strategy_result', handler);
      
      this.socket.emit('execute_strategy', {
        candles,
        strategy: strategyType
      });
    });
  }

  getStrategy(id) {
    return this.strategies.get(id);
  }

  getAllStrategies() {
    return Array.from(this.strategies.values());
  }

  deleteStrategy(id) {
    return this.strategies.delete(id);
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }
}

export const strategyService = new StrategyService();
