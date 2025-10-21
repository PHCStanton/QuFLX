import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../hooks/useWebSocketV2';

// Mock composed hooks used by useWebSocketV2
jest.mock('../hooks/useConnection', () => ({
  useConnection: () => ({
    socket: {
      once: (event, cb) => {
        // Immediately invoke reconnect handlers to simulate a successful reconnection
        if (event === 'reconnect' && typeof cb === 'function') cb();
      },
    },
    state: {
      isConnected: true,
      isConnecting: false,
      error: null,
      chromeStatus: 'connected',
    },
  }),
}));

jest.mock('../hooks/useStreamControl', () => ({
  useStreamControl: () => ({
    stream: {
      active: false,
      asset: 'EURUSD',
      backendReconnected: false,
      chromeReconnected: false,
    },
    assetDetection: {
      detectedAsset: 'EURUSD',
      detectionError: null,
      isDetecting: false,
    },
    actions: {
      startStream: jest.fn(),
      stopStream: jest.fn(),
      changeAsset: jest.fn(),
      detectAsset: jest.fn(),
    },
  }),
}));jest.mock('../hooks/useDataStream', () => ({
  useDataStream: () => ({
    data: {
      chartData: [
        { time: 1635724800, open: 1.24, high: 1.245, low: 1.235, close: 1.2425, volume: 1000 },
        { time: 1635728400, open: 1.2425, high: 1.246, low: 1.242, close: 1.2445, volume: 1200 },
      ],
      historicalCandles: [],
      lastMessage: {
        type: 'candle_update',
        data: { time: 1635732000, open: 1.2445, high: 1.247, low: 1.244, close: 1.2465, volume: 1100 },
      },
    },
    actions: {
      storeCsvCandles: jest.fn(),
    },
  }),
}));

jest.mock('../hooks/useIndicatorCalculations', () => ({
  useIndicatorCalculations: () => ({
    indicatorData: {
      indicators: {
        'SMA-10': { type: 'SMA', value: 1.2345 },
        'RSI-14': { type: 'RSI', value: 65.42 },
      },
    },
    indicatorError: null,
    isCalculatingIndicators: false,
    calculateIndicators: jest.fn(),
  }),
}));

describe('useWebSocketV2 (composed hook) basics', () => {
  it('exposes connection, stream, asset, data objects with expected shapes', () => {
    const { result } = renderHook(() => useWebSocket());
    expect(result.current.connection.isConnected).toBe(true);
    expect(result.current.connection.error).toBeNull();

    expect(result.current.stream.currentAsset).toBe('EURUSD');
    expect(result.current.stream.isActive).toBe(false);

    expect(result.current.asset.detected).toBe('EURUSD');
    expect(result.current.asset.error).toBeNull();

    expect(Array.isArray(result.current.data.current)).toBe(true);
    expect(result.current.data.lastUpdate?.type).toBe('candle_update');

    expect(result.current.data.indicators).toHaveProperty('data');
    expect(result.current.data.indicators).toHaveProperty('error');
    expect(result.current.data.indicators).toHaveProperty('isCalculating');
  });
});describe('useWebSocketV2 actions and reconnection', () => {
  it('exposes unified actions that are callable', () => {
    const { result } = renderHook(() => useWebSocket());

    expect(typeof result.current.actions.stream.start).toBe('function');
    expect(typeof result.current.actions.stream.stop).toBe('function');
    expect(typeof result.current.actions.stream.changeAsset).toBe('function');
    expect(typeof result.current.actions.stream.detectAsset).toBe('function');

    expect(typeof result.current.actions.data.storeCSV).toBe('function');
    expect(typeof result.current.actions.data.calculateIndicators).toBe('function');

    // These calls should not throw and should be synchronous in this mock
    act(() => {
      result.current.actions.stream.start();
      result.current.actions.stream.stop();
      result.current.actions.stream.changeAsset('GBPUSD');
      result.current.actions.stream.detectAsset();
      result.current.actions.data.storeCSV({ candles: [] });
      result.current.actions.data.calculateIndicators();
    });
  });

  it('onReconnect triggers the provided callback when socket reconnects', () => {
    const { result } = renderHook(() => useWebSocket());
    const callback = jest.fn();

    act(() => {
      // Our mocked useConnection socket immediately invokes the callback
      result.current.onReconnect(callback);
    });

    expect(callback).toHaveBeenCalledTimes(1);
  });
});