class StrategyService {
  constructor() {
    this.strategies = new Map();
    this.runningStrategies = new Map();
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
    const requiredFields = ['name', 'type', 'execute'];
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
      const response = await fetch('/api/strategy/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, candles, indicators })
      });

      const result = await response.json();
      return result.signals || [];
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
            type: 'BUY',
            confidence: 0.8,
            reason: `${rule.fastIndicator} crossed above ${rule.slowIndicator}`
          };
        } else if (fastPrev > slowPrev && fastCurr < slowCurr) {
          return {
            type: 'SELL',
            confidence: 0.8,
            reason: `${rule.fastIndicator} crossed below ${rule.slowIndicator}`
          };
        }
      }
    }

    return null;
  }

  async runBacktest(strategyId, data, config = {}) {
    const strategy = this.strategies.get(strategyId);
    if (!strategy) {
      return { success: false, error: 'Strategy not found' };
    }

    const {
      initialCapital = 10000,
      positionSize = 0.1,
      commission = 0.001
    } = config;

    let capital = initialCapital;
    let position = null;
    const trades = [];

    for (let i = 1; i < data.length; i++) {
      const candles = data.slice(0, i + 1);
      const signals = await strategy.execute(candles, {});

      for (const signal of signals) {
        if (signal.type === 'BUY' && !position) {
          const amount = capital * positionSize;
          const price = candles[i].close;
          const shares = amount / price;
          
          position = {
            type: 'LONG',
            entryPrice: price,
            shares,
            entryTime: candles[i].time
          };

          capital -= amount * (1 + commission);
          
        } else if (signal.type === 'SELL' && position) {
          const exitPrice = candles[i].close;
          const pnl = (exitPrice - position.entryPrice) * position.shares;
          
          capital += (position.shares * exitPrice) * (1 - commission);
          
          trades.push({
            ...position,
            exitPrice,
            exitTime: candles[i].time,
            pnl,
            pnlPercent: (pnl / (position.entryPrice * position.shares)) * 100
          });

          position = null;
        }
      }
    }

    const totalPnL = capital - initialCapital;
    const winningTrades = trades.filter(t => t.pnl > 0);
    const losingTrades = trades.filter(t => t.pnl <= 0);

    return {
      success: true,
      results: {
        initialCapital,
        finalCapital: capital,
        totalPnL,
        totalPnLPercent: (totalPnL / initialCapital) * 100,
        totalTrades: trades.length,
        winningTrades: winningTrades.length,
        losingTrades: losingTrades.length,
        winRate: trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0,
        trades
      }
    };
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
}

export const strategyService = new StrategyService();
