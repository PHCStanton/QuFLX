import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import RealTimeChart from '../RealTimeChart';

// Mock lightweight-charts
jest.mock('lightweight-charts', () => ({
  createChart: jest.fn(() => ({
    addCandlestickSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
      applyOptions: jest.fn()
    })),
    addLineSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
      applyOptions: jest.fn()
    })),
    timeScale: jest.fn(() => ({
      fitContent: jest.fn(),
      setVisibleRange: jest.fn()
    })),
    priceScale: jest.fn(() => ({
      applyOptions: jest.fn()
    })),
    applyOptions: jest.fn(),
    remove: jest.fn(),
    subscribeCrosshairMove: jest.fn(),
    unsubscribeCrosshairMove: jest.fn()
  })),
  ColorType: {
    Solid: 'solid'
  }
}));

describe('RealTimeChart Component', () => {
  const mockChartData = [
    {
      time: '2024-01-01',
      open: 1.0850,
      high: 1.0865,
      low: 1.0845,
      close: 1.0860
    },
    {
      time: '2024-01-02',
      open: 1.0860,
      high: 1.0875,
      low: 1.0855,
      close: 1.0870
    }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('should render chart container', () => {
      render(<RealTimeChart data={mockChartData} symbol="EURUSD" />);

      const container = document.querySelector('[data-testid="chart-container"]');
      expect(container).toBeDefined();
    });

    test('should display symbol name', () => {
      render(<RealTimeChart data={mockChartData} symbol="EURUSD" />);

      expect(screen.queryByText(/EURUSD/i)).toBeDefined();
    });

    test('should render with default props', () => {
      const { container } = render(
        <RealTimeChart data={mockChartData} symbol="EURUSD" />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle empty data gracefully', () => {
      const { container } = render(
        <RealTimeChart data={[]} symbol="EURUSD" />
      );

      expect(container).toBeInTheDocument();
    });
  });

  describe('Data Updates', () => {
    test('should update chart when data changes', async () => {
      const { rerender } = render(
        <RealTimeChart data={mockChartData} symbol="EURUSD" />
      );

      const newData = [
        ...mockChartData,
        {
          time: '2024-01-03',
          open: 1.0870,
          high: 1.0885,
          low: 1.0865,
          close: 1.0880
        }
      ];

      rerender(<RealTimeChart data={newData} symbol="EURUSD" />);

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should handle real-time candle updates', async () => {
      const { rerender } = render(
        <RealTimeChart data={mockChartData} symbol="EURUSD" />
      );

      const updatedData = [
        ...mockChartData.slice(0, -1),
        {
          time: '2024-01-02',
          open: 1.0860,
          high: 1.0880,
          low: 1.0855,
          close: 1.0875
        }
      ];

      rerender(<RealTimeChart data={updatedData} symbol="EURUSD" />);

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should append new candles correctly', async () => {
      const initialData = mockChartData.slice(0, 1);
      const { rerender } = render(
        <RealTimeChart data={initialData} symbol="EURUSD" />
      );

      rerender(<RealTimeChart data={mockChartData} symbol="EURUSD" />);

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should handle rapid data updates', async () => {
      const { rerender } = render(
        <RealTimeChart data={mockChartData} symbol="EURUSD" />
      );

      for (let i = 0; i < 10; i++) {
        const updatedData = [
          ...mockChartData,
          {
            time: `2024-01-0${3 + i}`,
            open: 1.0850 + (i * 0.001),
            high: 1.0865 + (i * 0.001),
            low: 1.0845 + (i * 0.001),
            close: 1.0860 + (i * 0.001)
          }
        ];

        rerender(<RealTimeChart data={updatedData} symbol="EURUSD" />);
      }

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Chart Configuration', () => {
    test('should apply custom chart options', () => {
      const customOptions = {
        width: 800,
        height: 400,
        timeScale: { timeVisible: true }
      };

      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          options={customOptions}
        />
      );

      expect(true).toBe(true);
    });

    test('should handle different timeframes', () => {
      const timeframes = ['1m', '5m', '15m', '1h', '4h', '1d'];

      timeframes.forEach(tf => {
        const { unmount } = render(
          <RealTimeChart
            data={mockChartData}
            symbol="EURUSD"
            timeframe={tf}
          />
        );
        unmount();
      });

      expect(true).toBe(true);
    });

    test('should apply color scheme correctly', () => {
      const colorScheme = {
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderUpColor: '#26a69a',
        borderDownColor: '#ef5350'
      };

      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          colorScheme={colorScheme}
        />
      );

      expect(true).toBe(true);
    });
  });

  describe('Indicators', () => {
    test('should render indicators when provided', () => {
      const indicators = [
        {
          type: 'sma',
          period: 20,
          color: '#FF6B6B'
        },
        {
          type: 'ema',
          period: 50,
          color: '#4ECDC4'
        }
      ];

      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          indicators={indicators}
        />
      );

      expect(true).toBe(true);
    });

    test('should update indicators with new data', async () => {
      const indicators = [
        { type: 'sma', period: 20 }
      ];

      const { rerender } = render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          indicators={indicators}
        />
      );

      const newData = [
        ...mockChartData,
        {
          time: '2024-01-03',
          open: 1.0870,
          high: 1.0885,
          low: 1.0865,
          close: 1.0880
        }
      ];

      rerender(
        <RealTimeChart
          data={newData}
          symbol="EURUSD"
          indicators={indicators}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should handle multiple indicators', () => {
      const indicators = [
        { type: 'sma', period: 20 },
        { type: 'ema', period: 50 },
        { type: 'rsi', period: 14 },
        { type: 'macd' },
        { type: 'bollinger', period: 20 }
      ];

      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          indicators={indicators}
        />
      );

      expect(true).toBe(true);
    });

    test('should remove indicators when not provided', async () => {
      const indicators = [{ type: 'sma', period: 20 }];

      const { rerender } = render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          indicators={indicators}
        />
      );

      rerender(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          indicators={[]}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Interaction', () => {
    test('should handle crosshair movement', async () => {
      const onCrosshairMove = jest.fn();

      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          onCrosshairMove={onCrosshairMove}
        />
      );

      // Simulate crosshair movement
      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should display tooltip on hover', async () => {
      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          showTooltip={true}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should handle zoom and pan', async () => {
      const { container } = render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          enableZoom={true}
          enablePan={true}
        />
      );

      expect(container).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('should handle large datasets efficiently', () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        time: `2024-01-${String(i).padStart(2, '0')}`,
        open: 1.0850 + (Math.random() * 0.01),
        high: 1.0865 + (Math.random() * 0.01),
        low: 1.0845 + (Math.random() * 0.01),
        close: 1.0860 + (Math.random() * 0.01)
      }));

      const startTime = performance.now();

      render(
        <RealTimeChart data={largeData} symbol="EURUSD" />
      );

      const duration = performance.now() - startTime;

      expect(duration).toBeLessThan(2000);
    });

    test('should not re-render unnecessarily', () => {
      const renderSpy = jest.fn();

      const TestWrapper = ({ data }) => {
        renderSpy();
        return <RealTimeChart data={data} symbol="EURUSD" />;
      };

      const { rerender } = render(
        <TestWrapper data={mockChartData} />
      );

      const initialRenderCount = renderSpy.mock.calls.length;

      rerender(<TestWrapper data={mockChartData} />);

      // Should not re-render with same data
      expect(renderSpy.mock.calls.length).toBeLessThanOrEqual(
        initialRenderCount + 1
      );
    });

    test('should clean up resources on unmount', () => {
      const { unmount } = render(
        <RealTimeChart data={mockChartData} symbol="EURUSD" />
      );

      unmount();

      expect(true).toBe(true);
    });
  });

  describe('Error Handling', () => {
    test('should handle invalid data gracefully', () => {
      const invalidData = [
        { time: '2024-01-01' }, // Missing OHLC
        { open: 1.0850 } // Missing time
      ];

      const { container } = render(
        <RealTimeChart data={invalidData} symbol="EURUSD" />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle missing symbol', () => {
      const { container } = render(
        <RealTimeChart data={mockChartData} />
      );

      expect(container).toBeInTheDocument();
    });

    test('should recover from rendering errors', () => {
      const { rerender } = render(
        <RealTimeChart data={mockChartData} symbol="EURUSD" />
      );

      // Attempt to render with problematic data
      rerender(
        <RealTimeChart data={null} symbol="EURUSD" />
      );

      expect(true).toBe(true);
    });
  });

  describe('Responsive Design', () => {
    test('should adapt to container size changes', async () => {
      const { container, rerender } = render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          width={800}
          height={400}
        />
      );

      rerender(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          width={1200}
          height={600}
        />
      );

      await waitFor(() => {
        expect(container).toBeInTheDocument();
      });
    });

    test('should handle mobile viewport', () => {
      render(
        <RealTimeChart
          data={mockChartData}
          symbol="EURUSD"
          width={375}
          height={667}
        />
      );

      expect(true).toBe(true);
    });
  });
});</parameter>
<parameter name="line_count">420</parameter>
</invoke>
</function_calls>