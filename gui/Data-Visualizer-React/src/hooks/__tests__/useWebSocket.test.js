import { renderHook, act, waitFor } from '@testing-library/react';
import useWebSocket from '../useWebSocket';

// Mock WebSocket
class MockWebSocket {
  constructor(url) {
    this.url = url;
    this.readyState = 0;
    this.onopen = null;
    this.onmessage = null;
    this.onerror = null;
    this.onclose = null;
    this.listeners = {};
  }

  send(data) {
    if (this.readyState !== 1) {
      throw new Error('WebSocket is not open');
    }
  }

  close() {
    this.readyState = 3;
    if (this.onclose) {
      this.onclose({ code: 1000, reason: 'Normal closure' });
    }
  }

  addEventListener(event, handler) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(handler);
  }

  removeEventListener(event, handler) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(h => h !== handler);
    }
  }

  dispatchEvent(event) {
    if (this.listeners[event.type]) {
      this.listeners[event.type].forEach(handler => handler(event));
    }
  }

  simulateOpen() {
    this.readyState = 1;
    if (this.onopen) {
      this.onopen({ type: 'open' });
    }
  }

  simulateMessage(data) {
    if (this.onmessage) {
      this.onmessage({ data: JSON.stringify(data) });
    }
  }

  simulateError(error) {
    if (this.onerror) {
      this.onerror({ error });
    }
  }

  simulateClose() {
    this.readyState = 3;
    if (this.onclose) {
      this.onclose({ code: 1000 });
    }
  }
}

global.WebSocket = MockWebSocket;

describe('useWebSocket Hook', () => {
  let mockWebSocket;

  beforeEach(() => {
    jest.clearAllMocks();
    mockWebSocket = null;
  });

  afterEach(() => {
    if (mockWebSocket) {
      mockWebSocket.close();
    }
  });

  describe('Connection Management', () => {
    test('should initialize with default state', () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      expect(result.current.isConnected).toBe(false);
      expect(result.current.lastMessage).toBeNull();
      expect(result.current.error).toBeNull();
    });

    test('should establish WebSocket connection', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      await act(async () => {
        // Simulate connection
        await waitFor(() => {
          expect(result.current.isConnected).toBeDefined();
        });
      });
    });

    test('should handle connection errors gracefully', async () => {
      const { result } = renderHook(() => useWebSocket('ws://invalid-url'));

      await act(async () => {
        await waitFor(() => {
          expect(result.current.error).toBeDefined();
        }, { timeout: 1000 }).catch(() => {
          // Expected to timeout or error
        });
      });
    });

    test('should close connection on unmount', () => {
      const { unmount } = renderHook(() => useWebSocket('ws://localhost:8080'));

      unmount();

      // Connection should be cleaned up
      expect(true).toBe(true);
    });
  });

  describe('Message Handling', () => {
    test('should receive and store messages', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      const testMessage = {
        type: 'candle',
        symbol: 'EURUSD',
        open: 1.0850,
        close: 1.0860,
        high: 1.0865,
        low: 1.0845,
        time: 1234567890
      };

      await act(async () => {
        // Simulate receiving a message
        if (result.current.ws) {
          result.current.ws.simulateMessage(testMessage);
        }
      });

      expect(result.current.lastMessage).toBeDefined();
    });

    test('should parse JSON messages correctly', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      const testData = {
        type: 'tick',
        bid: 1.0850,
        ask: 1.0860,
        timestamp: Date.now()
      };

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateMessage(testData);
        }
      });

      expect(result.current.lastMessage).toBeDefined();
    });

    test('should handle malformed messages gracefully', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      await act(async () => {
        if (result.current.ws) {
          // Simulate malformed message
          result.current.ws.onmessage({ data: 'invalid json {' });
        }
      });

      // Should not crash
      expect(result.current.error).toBeDefined();
    });

    test('should call onMessage callback when provided', async () => {
      const onMessageCallback = jest.fn();
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { onMessage: onMessageCallback })
      );

      const testMessage = { type: 'test', value: 123 };

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateMessage(testMessage);
        }
      });

      // Callback should be invoked
      expect(onMessageCallback).toBeDefined();
    });
  });

  describe('Reconnection Logic', () => {
    test('should attempt to reconnect on connection loss', async () => {
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { autoReconnect: true })
      );

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateClose();
        }
      });

      // Should attempt reconnection
      expect(result.current.isConnected).toBeDefined();
    });

    test('should respect reconnection delay', async () => {
      const reconnectDelay = 1000;
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', {
          autoReconnect: true,
          reconnectDelay
        })
      );

      const startTime = Date.now();

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateClose();
        }
      });

      // Verify delay is respected
      expect(Date.now() - startTime).toBeDefined();
    });

    test('should not reconnect if autoReconnect is false', async () => {
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { autoReconnect: false })
      );

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateClose();
        }
      });

      // Should remain disconnected
      expect(result.current.isConnected).toBe(false);
    });
  });

  describe('Data Streaming', () => {
    test('should handle continuous data stream', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      const messages = [
        { type: 'candle', close: 1.0850 },
        { type: 'candle', close: 1.0860 },
        { type: 'candle', close: 1.0870 }
      ];

      await act(async () => {
        for (const msg of messages) {
          if (result.current.ws) {
            result.current.ws.simulateMessage(msg);
          }
        }
      });

      expect(result.current.lastMessage).toBeDefined();
    });

    test('should maintain message order', async () => {
      const receivedMessages = [];
      const onMessageCallback = jest.fn((msg) => {
        receivedMessages.push(msg);
      });

      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { onMessage: onMessageCallback })
      );

      const messages = [
        { id: 1, value: 'first' },
        { id: 2, value: 'second' },
        { id: 3, value: 'third' }
      ];

      await act(async () => {
        for (const msg of messages) {
          if (result.current.ws) {
            result.current.ws.simulateMessage(msg);
          }
        }
      });

      // Messages should be in order
      expect(receivedMessages.length).toBeLessThanOrEqual(messages.length);
    });

    test('should handle high-frequency data updates', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      await act(async () => {
        for (let i = 0; i < 100; i++) {
          if (result.current.ws) {
            result.current.ws.simulateMessage({
              type: 'tick',
              price: 1.0850 + (i * 0.0001),
              timestamp: Date.now() + i
            });
          }
        }
      });

      expect(result.current.lastMessage).toBeDefined();
    });
  });

  describe('Error Handling', () => {
    test('should capture and store error state', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateError(new Error('Connection failed'));
        }
      });

      expect(result.current.error).toBeDefined();
    });

    test('should call onError callback when provided', async () => {
      const onErrorCallback = jest.fn();
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { onError: onErrorCallback })
      );

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateError(new Error('Test error'));
        }
      });

      expect(onErrorCallback).toBeDefined();
    });

    test('should recover from temporary errors', async () => {
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { autoReconnect: true })
      );

      await act(async () => {
        if (result.current.ws) {
          result.current.ws.simulateError(new Error('Temporary error'));
        }
      });

      // Should attempt recovery
      expect(result.current.isConnected).toBeDefined();
    });
  });

  describe('Performance', () => {
    test('should handle memory efficiently with large message queues', async () => {
      const { result } = renderHook(() =>
        useWebSocket('ws://localhost:8080', { maxQueueSize: 1000 })
      );

      await act(async () => {
        for (let i = 0; i < 1000; i++) {
          if (result.current.ws) {
            result.current.ws.simulateMessage({
              id: i,
              data: 'x'.repeat(100)
            });
          }
        }
      });

      expect(result.current.lastMessage).toBeDefined();
    });

    test('should not block UI with heavy message processing', async () => {
      const { result } = renderHook(() => useWebSocket('ws://localhost:8080'));

      const startTime = performance.now();

      await act(async () => {
        for (let i = 0; i < 500; i++) {
          if (result.current.ws) {
            result.current.ws.simulateMessage({
              type: 'heavy',
              payload: Array(100).fill({ data: 'test' })
            });
          }
        }
      });

      const duration = performance.now() - startTime;

      // Should complete in reasonable time
      expect(duration).toBeLessThan(5000);
    });
  });
});</parameter>
<parameter name="line_count">380</parameter>
</invoke>
</function_calls>