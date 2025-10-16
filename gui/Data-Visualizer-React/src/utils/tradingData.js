// Trading data utilities and parsers
export const parseTradingData = (input, symbol) => {
  // Handle both string (CSV text) and array (parsed objects) inputs
  let data = [];

  if (typeof input === 'string') {
    // Input is CSV text - parse it
    const lines = input.trim().split('\n');

    // Detect CSV format from header
    let hasIndexColumn = false;

    if (lines.length > 0) {
      const headerParts = lines[0].split(',');

      // Check if first column header is empty or suggests an index
      const firstHeader = headerParts[0].toLowerCase().trim();
      hasIndexColumn = firstHeader === '' || firstHeader === 'index' || firstHeader === 'id' || firstHeader === '#';
    }

    // Skip header and parse data
    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const parts = line.split(',');

      // Handle different CSV formats
      let timestamp, open, close, high, low, volume = null;

      if (parts.length === 5) {
        // Format: timestamp,open,close,high,low (OHLC)
        [timestamp, open, close, high, low] = parts;
      } else if (parts.length === 6) {
        if (hasIndexColumn) {
          // Format: index,timestamp,open,high,low,close
          [, timestamp, open, high, low, close] = parts;
        } else {
          // Format: timestamp,open,close,high,low,volume (OHLCV)
          [timestamp, open, close, high, low, volume] = parts;
        }
      } else if (parts.length === 7) {
        // Format: index,timestamp,open,high,low,close,volume
        [, timestamp, open, high, low, close, volume] = parts;
      } else if (parts.length === 3) {
        // Format: timestamp,asset,price (Tick data)
        const [ts, asset, price] = parts;
        timestamp = ts;
        open = close = high = low = price;
      } else {
        continue;
      }

      if (timestamp && open && close && high && low) {
        // Parse timestamp - handle both Unix timestamp and ISO format
        let timestampSec;
        if (timestamp.includes('-') || timestamp.includes('T') || timestamp.includes(':')) {
          // ISO format or time string
          timestampSec = Math.floor(new Date(timestamp).getTime() / 1000);
        } else {
          // Unix timestamp
          timestampSec = Math.floor(parseFloat(timestamp));
        }

        // Skip invalid timestamps
        if (isNaN(timestampSec)) continue;

        data.push({
          timestamp: timestampSec,
          date: new Date(timestampSec * 1000),
          open: parseFloat(open),
          close: parseFloat(close),
          high: parseFloat(high),
          low: parseFloat(low),
          volume: volume !== null ? parseFloat(volume) || 0 : 0,
          symbol: symbol
        });
      }
    }
  } else if (Array.isArray(input)) {
    // Input is already an array of parsed objects
    for (const item of input) {
      // Map common field names to standard format
      const timestamp = item.timestamp || item.time || item.Date;
      const open = item.open || item.Open;
      const close = item.close || item.Close;
      const high = item.high || item.High;
      const low = item.low || item.Low;
      const volume = item.volume || item.Volume || 0;

      if (timestamp && open && close && high && low) {
        // Parse timestamp - handle both Unix timestamp and ISO format
        let timestampSec;
        if (typeof timestamp === 'string') {
          if (timestamp.includes('-') || timestamp.includes('T') || timestamp.includes(':')) {
            // ISO format or time string
            timestampSec = Math.floor(new Date(timestamp).getTime() / 1000);
          } else {
            // Unix timestamp string
            timestampSec = Math.floor(parseFloat(timestamp));
          }
        } else {
          // Numeric timestamp
          timestampSec = Math.floor(parseFloat(timestamp));
        }

        // Skip invalid timestamps
        if (isNaN(timestampSec)) continue;

        data.push({
          timestamp: timestampSec,
          date: new Date(timestampSec * 1000),
          open: parseFloat(open),
          close: parseFloat(close),
          high: parseFloat(high),
          low: parseFloat(low),
          volume: parseFloat(volume) || 0,
          symbol: symbol
        });
      }
    }
  } else {
    console.error('parseTradingData: Invalid input type. Expected string or array.');
    return [];
  }

  // Sort by timestamp
  const sorted = data.sort((a, b) => a.timestamp - b.timestamp);

  // Remove duplicates by keeping the last entry for each timestamp
  const deduped = [];
  const seen = new Set();

  for (const item of sorted) {
    if (!seen.has(item.timestamp)) {
      seen.add(item.timestamp);
      deduped.push(item);
    }
  }

  return deduped;
};

// Technical indicators calculations
export const calculateSMA = (data, period = 20) => {
  const sma = [];
  for (let i = 0; i < data.length; i++) {
    if (i >= period - 1) {
      const sum = data.slice(i - period + 1, i + 1).reduce((acc, item) => acc + item.close, 0);
      sma.push({
        ...data[i],
        sma: sum / period
      });
    } else {
      sma.push({
        ...data[i],
        sma: null
      });
    }
  }
  return sma;
};

export const calculateEMA = (data, period = 20) => {
  const multiplier = 2 / (period + 1);
  const ema = [];
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      ema.push({
        ...data[i],
        ema: data[i].close
      });
    } else {
      const emaValue = (data[i].close * multiplier) + (ema[i-1].ema * (1 - multiplier));
      ema.push({
        ...data[i],
        ema: emaValue
      });
    }
  }
  return ema;
};

export const calculateRSI = (data, period = 14) => {
  const rsi = [];
  let gains = 0;
  let losses = 0;
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      rsi.push({
        ...data[i],
        rsi: 50
      });
      continue;
    }
    
    const change = data[i].close - data[i-1].close;
    const gain = change > 0 ? change : 0;
    const loss = change < 0 ? Math.abs(change) : 0;
    
    if (i < period) {
      gains += gain;
      losses += loss;
      rsi.push({
        ...data[i],
        rsi: 50
      });
    } else if (i === period) {
      const avgGain = gains / period;
      const avgLoss = losses / period;
      const rs = avgGain / avgLoss;
      const rsiValue = 100 - (100 / (1 + rs));
      rsi.push({
        ...data[i],
        rsi: rsiValue
      });
    } else {
      const prevAvgGain = (rsi[i-1].avgGain * (period - 1) + gain) / period;
      const prevAvgLoss = (rsi[i-1].avgLoss * (period - 1) + loss) / period;
      const rs = prevAvgGain / prevAvgLoss;
      const rsiValue = 100 - (100 / (1 + rs));
      rsi.push({
        ...data[i],
        rsi: rsiValue,
        avgGain: prevAvgGain,
        avgLoss: prevAvgLoss
      });
    }
  }
  return rsi;
};

export const calculateMACD = (data, fastPeriod = 12, slowPeriod = 26, signalPeriod = 9) => {
  const fastEMA = calculateEMA(data, fastPeriod);
  const slowEMA = calculateEMA(data, slowPeriod);
  const macd = [];
  
  for (let i = 0; i < data.length; i++) {
    const macdLine = fastEMA[i].ema - slowEMA[i].ema;
    macd.push({
      ...data[i],
      macd: macdLine,
      fastEMA: fastEMA[i].ema,
      slowEMA: slowEMA[i].ema
    });
  }
  
  const signalLine = calculateEMA(macd.map(item => ({ close: item.macd })), signalPeriod);
  
  return macd.map((item, i) => ({
    ...item,
    signal: signalLine[i].ema,
    histogram: item.macd - signalLine[i].ema
  }));
};

// Backtesting engine
export const backtest = (data, strategy, indicators = {}) => {
  const trades = [];
  let position = null;
  let balance = 10000; // Starting balance
  let totalTrades = 0;
  let winningTrades = 0;
  
  for (let i = 1; i < data.length; i++) {
    const current = data[i];
    const previous = data[i - 1];
    
    // Apply strategy logic
    const signal = strategy(current, previous, indicators);
    
    if (signal === 'BUY' && !position) {
      position = {
        type: 'LONG',
        entryPrice: current.close,
        entryTime: current.timestamp,
        entryIndex: i
      };
    } else if (signal === 'SELL' && !position) {
      position = {
        type: 'SHORT',
        entryPrice: current.close,
        entryTime: current.timestamp,
        entryIndex: i
      };
    } else if (signal === 'CLOSE' && position) {
      const exitPrice = current.close;
      const profit = position.type === 'LONG' 
        ? (exitPrice - position.entryPrice) / position.entryPrice
        : (position.entryPrice - exitPrice) / position.entryPrice;
      
      const tradeProfit = balance * 0.1 * profit; // Risk 10% per trade
      balance += tradeProfit;
      totalTrades++;
      
      if (tradeProfit > 0) winningTrades++;
      
      trades.push({
        ...position,
        exitPrice,
        exitTime: current.timestamp,
        exitIndex: i,
        profit: tradeProfit,
        profitPercent: profit * 100,
        duration: current.timestamp - position.entryTime
      });
      
      position = null;
    }
  }
  
  return {
    trades,
    finalBalance: balance,
    totalReturn: ((balance - 10000) / 10000) * 100,
    totalTrades,
    winningTrades,
    winRate: totalTrades > 0 ? (winningTrades / totalTrades) * 100 : 0,
    profitFactor: trades.length > 0 ? 
      trades.filter(t => t.profit > 0).reduce((sum, t) => sum + t.profit, 0) /
      Math.abs(trades.filter(t => t.profit < 0).reduce((sum, t) => sum + t.profit, 0)) : 0
  };
};

// Sample trading strategies
export const strategies = {
  smaGoldenCross: (current, previous, indicators) => {
    const { sma20, sma50 } = indicators;
    const currentSMA20 = sma20[current.timestamp];
    const currentSMA50 = sma50[current.timestamp];
    const prevSMA20 = sma20[previous.timestamp];
    const prevSMA50 = sma50[previous.timestamp];
    
    if (currentSMA20 && currentSMA50 && prevSMA20 && prevSMA50) {
      if (prevSMA20 <= prevSMA50 && currentSMA20 > currentSMA50) return 'BUY';
      if (prevSMA20 >= prevSMA50 && currentSMA20 < currentSMA50) return 'SELL';
    }
    return 'HOLD';
  },
  
  rsiOversold: (current, previous, indicators) => {
    const { rsi } = indicators;
    const currentRSI = rsi[current.timestamp];
    const prevRSI = rsi[previous.timestamp];
    
    if (currentRSI && prevRSI) {
      if (prevRSI <= 30 && currentRSI > 30) return 'BUY';
      if (prevRSI >= 70 && currentRSI < 70) return 'SELL';
    }
    return 'HOLD';
  },
  
  macdCrossover: (current, previous, indicators) => {
    const { macd } = indicators;
    const currentMACD = macd[current.timestamp];
    const prevMACD = macd[previous.timestamp];
    
    if (currentMACD && prevMACD) {
      if (prevMACD.macd <= prevMACD.signal && currentMACD.macd > currentMACD.signal) return 'BUY';
      if (prevMACD.macd >= prevMACD.signal && currentMACD.macd < currentMACD.signal) return 'SELL';
    }
    return 'HOLD';
  }
};
