export const mockIndicatorData = {
  indicators: {
    'RSI-14': {
      type: 'RSI',
      value: 65.42,
      signal: 'SELL',
      overbought: 70.00,
      oversold: 30.00
    },
    'MACD-12-26-9': {
      type: 'MACD',
      macd: 0.0012,
      signal: 0.0008,
      histogram: 0.0004,
      signal: 'BUY'
    },
    'BB-20-2': {
      type: 'BB',
      upper: 1.2450,
      middle: 1.2400,
      lower: 1.2350,
      signal: null
    }
  },
  series: {
    'RSI-14': [
      { time: 1635724800, value: 65.42 },
      { time: 1635728400, value: 64.87 }
    ],
    'MACD-12-26-9': {
      macd: [
        { time: 1635724800, value: 0.0012 },
        { time: 1635728400, value: 0.0014 }
      ],
      signal: [
        { time: 1635724800, value: 0.0008 },
        { time: 1635728400, value: 0.0009 }
      ],
      histogram: [
        { time: 1635724800, value: 0.0004 },
        { time: 1635728400, value: 0.0005 }
      ]
    },
    'BB-20-2': {
      upper: [
        { time: 1635724800, value: 1.2450 },
        { time: 1635728400, value: 1.2455 }
      ],
      middle: [
        { time: 1635724800, value: 1.2400 },
        { time: 1635728400, value: 1.2405 }
      ],
      lower: [
        { time: 1635724800, value: 1.2350 },
        { time: 1635728400, value: 1.2355 }
      ]
    }
  }
};

export const mockSocket = {
  on: jest.fn(),
  off: jest.fn(),
  emit: jest.fn(),
  once: jest.fn(),
  removeAllListeners: jest.fn(),
  connected: true,
  io: {
    engine: {
      readyState: 'open'
    }
  }
};

export const mockStreamData = {
  chartData: [
    {
      time: 1635724800,
      open: 1.2400,
      high: 1.2450,
      low: 1.2350,
      close: 1.2425,
      volume: 1000
    },
    {
      time: 1635728400,
      open: 1.2425,
      high: 1.2460,
      low: 1.2420,
      close: 1.2445,
      volume: 1200
    }
  ],
  lastMessage: {
    type: 'candle_update',
    data: {
      time: 1635732000,
      open: 1.2445,
      high: 1.2470,
      low: 1.2440,
      close: 1.2465,
      volume: 1100
    }
  },
  historicalCandles: {
    asset: 'EURUSD',
    count: 2,
    candles: [
      {
        time: 1635717600,
        open: 1.2380,
        high: 1.2420,
        low: 1.2360,
        close: 1.2400,
        volume: 950
      },
      {
        time: 1635721200,
        open: 1.2400,
        high: 1.2430,
        low: 1.2390,
        close: 1.2410,
        volume: 980
      }
    ]
  }
};