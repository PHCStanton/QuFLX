import { render, act, screen, waitFor } from '@testing-library/react';
import { renderHook } from '@testing-library/react-hooks';
import { useWebSocket } from '../hooks/useWebSocketV2';
import { useIndicators } from '../hooks/useIndicators';
import DataAnalysis from '../pages/DataAnalysis';
import { mockSocket, mockIndicatorData, mockStreamData } from './mocks/websocketMock';

// Mock the socket.io-client
jest.mock('socket.io-client', () => {
  return jest.fn(() => mockSocket);
});

describe('Indicator Pipeline Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('Full indicator pipeline flow works correctly', async () => {
    // Setup WebSocket hook
    const { result: wsResult } = renderHook(() => useWebSocket());
    
    // Simulate WebSocket connection
    act(() => {
      mockSocket.emit('connect');
      mockSocket.emit('connection_status', { chrome: 'connected' });
    });

    // Verify WebSocket connection
    expect(wsResult.current.connection.isConnected).toBe(true);
    expect(wsResult.current.connection.chromeConnected).toBe(true);

    // Render DataAnalysis component
    render(<DataAnalysis />);

    // Simulate receiving indicator data
    act(() => {
      mockSocket.emit('indicators_calculated', mockIndicatorData);
    });

    // Wait for indicator panel to update
    await waitFor(() => {
      expect(screen.getByText('RSI-14')).toBeInTheDocument();
      expect(screen.getByText('65.42')).toBeInTheDocument();
    });

    // Verify indicator display
    expect(screen.getByText('SELL')).toHaveStyle({ color: expect.stringContaining('error') });
    expect(screen.getByText('Overbought: 70.00')).toBeInTheDocument();
  });

  test('Indicator pipeline handles multiple data sources correctly', async () => {
    const { result: wsResult } = renderHook(() => useWebSocket());
    const { result: indResult } = renderHook(() => useIndicators({
      asset: 'EURUSD',
      isConnected: true,
      calculateIndicators: jest.fn(),
      indicatorData: mockIndicatorData,
      indicatorError: null
    }));

    // Add multiple indicators
    act(() => {
      indResult.current.addIndicator({
        instanceName: 'RSI-14',
        type: 'RSI',
        params: { period: 14 }
      });
      indResult.current.addIndicator({
        instanceName: 'MACD-12-26-9',
        type: 'MACD',
        params: { fast: 12, slow: 26, signal: 9 }
      });
    });

    // Verify indicators are tracked correctly
    expect(Object.keys(indResult.current.activeIndicators)).toHaveLength(2);

    // Simulate streaming data
    act(() => {
      mockSocket.emit('candle_update', mockStreamData.lastMessage);
    });

    // Verify data processing
    expect(wsResult.current.data.current).toHaveLength(1);
    expect(wsResult.current.data.indicators.data).toEqual(mockIndicatorData.indicators);
  });

  test('Indicator pipeline handles errors gracefully', async () => {
    render(<DataAnalysis />);

    // Simulate indicator calculation error
    act(() => {
      mockSocket.emit('indicators_error', {
        error: 'Failed to calculate indicators',
        details: 'Invalid parameter values'
      });
    });

    // Verify error display
    await waitFor(() => {
      expect(screen.getByText('Failed to calculate indicators')).toBeInTheDocument();
    });

    // Verify recovery after error
    act(() => {
      mockSocket.emit('indicators_calculated', mockIndicatorData);
    });

    await waitFor(() => {
      expect(screen.getByText('RSI-14')).toBeInTheDocument();
      expect(screen.queryByText('Failed to calculate indicators')).not.toBeInTheDocument();
    });
  });

  test('Indicator pipeline maintains state consistency', async () => {
    const { result: wsResult } = renderHook(() => useWebSocket());
    
    // Simulate connection loss and reconnection
    act(() => {
      mockSocket.emit('disconnect');
    });

    expect(wsResult.current.connection.isConnected).toBe(false);

    act(() => {
      mockSocket.emit('connect');
      mockSocket.emit('connection_status', { chrome: 'connected' });
    });

    expect(wsResult.current.connection.isConnected).toBe(true);

    // Verify indicator state is preserved
    expect(wsResult.current.data.indicators.data).toEqual(mockIndicatorData.indicators);
  });
});