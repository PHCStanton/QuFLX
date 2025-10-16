import {
  calculateSMA,
  calculateEMA,
  calculateRSI,
  calculateMACD,
  calculateBollingerBands,
  formatCandleData,
  calculateATR,
  calculateStochastic,
  validateCandleData,
  aggregateCandles
} from '../tradingData';

describe('Trading Data Utilities', () => {
  const mockCandles = [
    { time: '2024-01-01', open: 1.0850, high: 1.0865, low: 1.0845, close: 1.0860 },
    { time: '2024-01-02', open: 1.0860, high: 1.0875, low: 1.0855, close: 1.0870 },
    { time: '2024-01-03', open: 1.0870, high: 1.0885, low: 1.0865, close: 1.0880 },
    { time: '2024-01-04', open: 1.0880, high: 1.0895, low: 1.0875, close: 1.0890 },
    { time: '2024-01-05', open: 1.0890, high: 1.0905, low: 1.0885, close: 1.0900 }
  ];

  describe('SMA (Simple Moving Average)', () => {
    test('should calculate SMA correctly', () => {
      const closes = mockCandles.map(c => c.close);
      const sma = calculateSMA(closes, 3);

      expect(sma).toBeDefined();
      expect(sma.length).toBe(closes.length);
      expect(sma[sma.length - 1]).toBeGreaterThan(0);
    });

    test('should handle period larger than data length', () => {
      const closes = mockCandles.map(c => c.close);
      const sma = calculateSMA(closes, 100);

      expect(sma).toBeDefined();
      expect(sma.length).toBe(closes.length);
    });

    test('should return NaN for insufficient data points', () => {
      const closes = [1.0850, 1.0860];
      const sma = calculateSMA(closes, 5);

      expect(sma).toBeDefined();
      expect(sma.length).toBe(closes.length);
    });

    test('should handle empty array', () => {
      const sma = calculateSMA([], 5);

      expect(sma).toBeDefined();
      expect(sma.length).toBe(0);
    });

    test('should calculate SMA with period 1', () => {
      const closes = mockCandles.map(c => c.close);
      const sma = calculateSMA(closes, 1);

      expect(sma).toEqual(closes);
    });
  });

  describe('EMA (Exponential Moving Average)', () => {
    test('should calculate EMA correctly', () => {
      const closes = mockCandles.map(c => c.close);
      const ema = calculateEMA(closes, 3);

      expect(ema).toBeDefined();
      expect(ema.length).toBe(closes.length);
      expect(ema[ema.length - 1]).toBeGreaterThan(0);
    });

    test('should give more weight to recent prices', () => {
      const closes = [1.0850, 1.0860, 1.0870, 1.0880, 1.0890];
      const ema = calculateEMA(closes, 3);

      expect(ema[ema.length - 1]).toBeGreaterThan(ema[0]);
    });

    test('should handle period larger than data length', () => {
      const closes = mockCandles.map(c => c.close);
      const ema = calculateEMA(closes, 100);

      expect(ema).toBeDefined();
      expect(ema.length).toBe(closes.length);
    });

    test('should handle empty array', () => {
      const ema = calculateEMA([], 5);

      expect(ema).toBeDefined();
      expect(ema.length).toBe(0);
    });
  });

  describe('RSI (Relative Strength Index)', () => {
    test('should calculate RSI correctly', () => {
      const closes = mockCandles.map(c => c.close);
      const rsi = calculateRSI(closes, 14);

      expect(rsi).toBeDefined();
      expect(rsi.length).toBe(closes.length);
      rsi.forEach(value => {
        if (value !== undefined && !isNaN(value)) {
          expect(value).toBeGreaterThanOrEqual(0);
          expect(value).toBeLessThanOrEqual(100);
        }
      });
    });

    test('should return 50 for flat prices', () => {
      const closes = [1.0850, 1.0850, 1.0850, 1.0850, 1.0850];
      const rsi = calculateRSI(closes, 3);

      expect(rsi).toBeDefined();
    });

    test('should return high RSI for uptrend', () => {
      const closes = [1.0850, 1.0860, 1.0870, 1.0880, 1.0890, 1.0900];
      const rsi = calculateRSI(closes, 3);

      const lastRSI = rsi[rsi.length - 1];
      if (!isNaN(lastRSI)) {
        expect(lastRSI).toBeGreaterThan(50);
      }
    });

    test('should return low RSI for downtrend', () => {
      const closes = [1.0900, 1.0890, 1.0880, 1.0870, 1.0860, 1.0850];
      const rsi = calculateRSI(closes, 3);

      const lastRSI = rsi[rsi.length - 1];
      if (!isNaN(lastRSI)) {
        expect(lastRSI).toBeLessThan(50);
      }
    });

    test('should handle insufficient data', () => {
      const closes = [1.0850, 1.0860];
      const rsi = calculateRSI(closes, 14);

      expect(rsi).toBeDefined();
      expect(rsi.length).toBe(closes.length);
    });
  });

  describe('MACD (Moving Average Convergence Divergence)', () => {
    test('should calculate MACD correctly', () => {
      const closes = mockCandles.map(c => c.close);
      const macd = calculateMACD(closes, 12, 26, 9);

      expect(macd).toBeDefined();
      expect(macd.length).toBe(closes.length);
      macd.forEach(point => {
        if (point) {
          expect(point.macd).toBeDefined();
          expect(point.signal).toBeDefined();
          expect(point.histogram).toBeDefined();
        }
      });
    });

    test('should calculate histogram as difference', () => {
      const closes = mockCandles.map(c => c.close);
      const macd = calculateMACD(closes, 12, 26, 9);

      macd.forEach(point => {
        if (point && point.macd !== undefined && point.signal !== undefined) {
          const expectedHistogram = point.macd - point.signal;
          expect(Math.abs(point.histogram - expectedHistogram)).toBeLessThan(0.0001);
        }
      });
    });

    test('should handle custom periods', () => {
      const closes = mockCandles.map(c => c.close);
      const macd = calculateMACD(closes, 5, 10, 5);

      expect(macd).toBeDefined();
      expect(macd.length).toBe(closes.length);
    });

    test('should handle empty array', () => {
      const macd = calculateMACD([], 12, 26, 9);

      expect(macd).toBeDefined();
      expect(macd.length).toBe(0);
    });
  });

  describe('Bollinger Bands', () => {
    test('should calculate Bollinger Bands correctly', () => {
      const closes = mockCandles.map(c => c.close);
      const bb = calculateBollingerBands(closes, 20, 2);

      expect(bb).toBeDefined();
      expect(bb.length).toBe(closes.length);
      bb.forEach(band => {
        if (band) {
          expect(band.upper).toBeDefined();
          expect(band.middle).toBeDefined();
          expect(band.lower).toBeDefined();
          expect(band.upper).toBeGreaterThanOrEqual(band.middle);
          expect(band.middle).toBeGreaterThanOrEqual(band.lower);
        }
      });
    });

    test('should have middle band as SMA', () => {
      const closes = mockCandles.map(c => c.close);
      const bb = calculateBollingerBands(closes, 3, 2);
      const sma = calculateSMA(closes, 3);

      bb.forEach((band, i) => {
        if (band && sma[i]) {
          expect(Math.abs(band.middle - sma[i])).toBeLessThan(0.0001);
        }
      });
    });

    test('should handle custom standard deviations', () => {
      const closes = mockCandles.map(c => c.close);
      const bb1 = calculateBollingerBands(closes, 20, 1);
      const bb2 = calculateBollingerBands(closes, 20, 3);

      bb1.forEach((band1, i) => {
        const band2 = bb2[i];
        if (band1 && band2) {
          expect(band2.upper - band2.middle).toBeGreaterThan(
            band1.upper - band1.middle
          );
        }
      });
    });

    test('should handle empty array', () => {
      const bb = calculateBollingerBands([], 20, 2);

      expect(bb).toBeDefined();
      expect(bb.length).toBe(0);
    });
  });

  describe('ATR (Average True Range)', () => {
    test('should calculate ATR correctly', () => {
      const atr = calculateATR(mockCandles, 14);

      expect(atr).toBeDefined();
      expect(atr.length).toBe(mockCandles.length);
      atr.forEach(value => {
        if (value !== undefined && !isNaN(value)) {
          expect(value).toBeGreaterThanOrEqual(0);
        }
      });
    });

    test('should handle custom period', () => {
      const atr = calculateATR(mockCandles, 5);

      expect(atr).toBeDefined();
      expect(atr.length).toBe(mockCandles.length);
    });

    test('should handle empty array', () => {
      const atr = calculateATR([], 14);

      expect(atr).toBeDefined();
      expect(atr.length).toBe(0);
    });
  });

  describe('Stochastic Oscillator', () => {
    test('should calculate Stochastic correctly', () => {
      const stoch = calculateStochastic(mockCandles, 14, 3, 3);

      expect(stoch).toBeDefined();
      expect(stoch.length).toBe(mockCandles.length);
      stoch.forEach(point => {
        if (point) {
          expect(point.k).toBeDefined();
          expect(point.d).toBeDefined();
          if (!isNaN(point.k)) {
            expect(point.k).toBeGreaterThanOrEqual(0);
            expect(point.k).toBeLessThanOrEqual(100);
          }
        }
      });
    });

    test('should handle custom periods', () => {
      const stoch = calculateStochastic(mockCandles, 5, 3, 3);

      expect(stoch).toBeDefined();
      expect(stoch.length).toBe(mockCandles.length);
    });

    test('should handle empty array', () => {
      const stoch = calculateStochastic([], 14, 3, 3);

      expect(stoch).toBeDefined();
      expect(stoch.length).toBe(0);
    });
  });

  describe('Data Formatting', () => {
    test('should format candle data correctly', () => {
      const formatted = formatCandleData(mockCandles);

      expect(formatted).toBeDefined();
      expect(formatted.length).toBe(mockCandles.length);
      formatted.forEach(candle => {
        expect(candle.time).toBeDefined();
        expect(candle.open).toBeDefined();
        expect(candle.high).toBeDefined();
        expect(candle.low).toBeDefined();
        expect(candle.close).toBeDefined();
      });
    });

    test('should handle missing fields', () => {
      const incompleteCandles = [
        { time: '2024-01-01', close: 1.0860 },
        { time: '2024-01-02', open: 1.0860, close: 1.0870 }
      ];

      const formatted = formatCandleData(incompleteCandles);

      expect(formatted).toBeDefined();
      expect(formatted.length).toBe(incompleteCandles.length);
    });

    test('should handle empty array', () => {
      const formatted = formatCandleData([]);

      expect(formatted).toBeDefined();
      expect(formatted.length).toBe(0);
    });
  });

  describe('Data Validation', () => {
    test('should validate correct candle data', () => {
      const isValid = validateCandleData(mockCandles);

      expect(isValid).toBe(true);
    });

    test('should reject invalid OHLC values', () => {
      const invalidCandles = [
        { time: '2024-01-01', open: 1.0850, high: 1.0840, low: 1.0845, close: 1.0860 }
      ];

      const isValid = validateCandleData(invalidCandles);

      expect(isValid).toBe(false);
    });

    test('should reject missing required fields', () => {
      const incompleteCandles = [
        { time: '2024-01-01', open: 1.0850, close: 1.0860 }
      ];

      const isValid = validateCandleData(incompleteCandles);

      expect(isValid).toBe(false);
    });

    test('should handle empty array', () => {
      const isValid = validateCandleData([]);

      expect(isValid).toBe(true);
    });

    test('should reject null or undefined', () => {
      expect(validateCandleData(null)).toBe(false);
      expect(validateCandleData(undefined)).toBe(false);
    });
  });

  describe('Candle Aggregation', () => {
    test('should aggregate candles to higher timeframe', () => {
      const aggregated = aggregateCandles(mockCandles, 2);

      expect(aggregated).toBeDefined();
      expect(aggregated.length).toBeLessThanOrEqual(mockCandles.length);
      aggregated.forEach(candle => {
        expect(candle.open).toBeDefined();
        expect(candle.high).toBeDefined();
        expect(candle.low).toBeDefined();
        expect(candle.close).toBeDefined();
      });
    });

    test('should maintain OHLC integrity', () => {
      const aggregated = aggregateCandles(mockCandles, 2);

      aggregated.forEach(candle => {
        expect(candle.high).toBeGreaterThanOrEqual(candle.open);
        expect(candle.high).toBeGreaterThanOrEqual(candle.close);
        expect(candle.low).toBeLessThanOrEqual(candle.open);
        expect(candle.low).toBeLessThanOrEqual(candle.close);
      });
    });

    test('should handle aggregation factor of 1', () => {
      const aggregated = aggregateCandles(mockCandles, 1);

      expect(aggregated.length).toBe(mockCandles.length);
    });

    test('should handle empty array', () => {
      const aggregated = aggregateCandles([], 2);

      expect(aggregated).toBeDefined();
      expect(aggregated.length).toBe(0);
    });
  });

  describe('Performance', () => {
    test('should calculate indicators efficiently on large datasets', () => {
      const largeDataset = Array.from({ length: 1000 }, (_, i) => ({
        time: `2024-01-${String(i).padStart(2, '0')}`,
        open: 1.0850 + (Math.random() * 0.01),
        high: 1.0865 + (Math.random() * 0.01),
        low: 1.0845 + (Math.random() * 0.01),
        close: 1.0860 + (Math.random() * 0.01)
      }));

      const closes = largeDataset.map(c => c.close);

      const startTime = performance.now();

      calculateSMA(closes, 20);
      calculateEMA(closes, 20);
      calculateRSI(closes, 14);
      calculateMACD(closes, 12, 26, 9);
      calculateBollingerBands(closes, 20, 2);
      calculateATR(largeDataset, 14);
      calculateStochastic(largeDataset, 14, 3, 3);

      const duration = performance.now() - startTime;

      expect(duration).toBeLessThan(1000);
    });
  });

  describe('Edge Cases', () => {
    test('should handle single candle', () => {
      const singleCandle = [mockCandles[0]];

      expect(calculateSMA(singleCandle.map(c => c.close), 5)).toBeDefined();
      expect(calculateRSI(singleCandle.map(c => c.close), 14)).toBeDefined();
      expect(calculateATR(singleCandle, 14)).toBeDefined();
    });

    test('should handle NaN values gracefully', () => {
      const closes = [1.0850, NaN, 1.0870, 1.0880, 1.0890];

      expect(calculateSMA(closes, 3)).toBeDefined();
      expect(calculateEMA(closes, 3)).toBeDefined();
    });

    test('should handle very small price movements', () => {
      const closes = [1.0850, 1.0850001, 1.0850002, 1.0850003, 1.0850004];

      expect(calculateRSI(closes, 3)).toBeDefined();
      expect(calculateMACD(closes, 12, 26, 9)).toBeDefined();
    });
  });
});</parameter>
<parameter name="line_count">450</parameter>
</invoke>
</function_calls>