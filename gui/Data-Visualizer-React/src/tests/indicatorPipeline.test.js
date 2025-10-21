import { renderHook, act } from '@testing-library/react-hooks';
import { useIndicators } from '../hooks/useIndicators';
import { useWebSocket } from '../hooks/useWebSocketV2';
import { mockSocket, mockIndicatorData } from './mocks/websocketMock';

describe('Indicator Pipeline Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('useIndicators hook handles generic indicator data correctly', () => {
    const { result } = renderHook(() => useIndicators({
      asset: 'EURUSD',
      isConnected: true,
      calculateIndicators: jest.fn(),
      indicatorData: mockIndicatorData,
      indicatorError: null
    }));

    // Verify indicator reading formatting
    const reading = result.current.formatIndicatorReading('RSI-14');
    expect(reading).toEqual({
      value: '65.42',
      signal: 'SELL',
      type: 'RSI',
      additionalValues: {
        overbought: '70.00',
        oversold: '30.00'
      }
    });
  });

  test('useWebSocket hook provides correct indicator data structure', () => {
    const { result } = renderHook(() => useWebSocket());

    // Verify indicator data structure
    expect(result.current.data.indicators).toHaveProperty('data');
    expect(result.current.data.indicators).toHaveProperty('error');

    // Verify actions structure
    expect(result.current.actions.data).toHaveProperty('calculateIndicators');
  });

  test('Indicator pipeline handles multiple indicator instances', () => {
    const { result } = renderHook(() => useIndicators({
      asset: 'EURUSD',
      isConnected: true,
      calculateIndicators: jest.fn(),
      indicatorData: {
        indicators: {
          'SMA-10': { type: 'SMA', value: 1.2345 },
          'SMA-20': { type: 'SMA', value: 1.2355 },
          'RSI-14': { type: 'RSI', value: 65.42 }
        }
      },
      indicatorError: null
    }));

    // Add multiple indicators
    act(() => {
      result.current.addIndicator({
        instanceName: 'SMA-10',
        type: 'SMA',
        params: { period: 10 }
      });
      result.current.addIndicator({
        instanceName: 'SMA-20',
        type: 'SMA',
        params: { period: 20 }
      });
    });

    // Verify both instances are managed correctly
    expect(Object.keys(result.current.activeIndicators)).toHaveLength(2);
  });

  test('Indicator pipeline handles errors gracefully', () => {
    const { result } = renderHook(() => useIndicators({
      asset: 'EURUSD',
      isConnected: true,
      calculateIndicators: jest.fn(),
      indicatorData: null,
      indicatorError: 'Failed to calculate indicators'
    }));

    // Verify error handling
    const reading = result.current.formatIndicatorReading('RSI-14');
    expect(reading).toBeNull();
  });
});