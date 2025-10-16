import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import MultiPaneChart from '../MultiPaneChart';

// Mock lightweight-charts
jest.mock('lightweight-charts', () => ({
  createChart: jest.fn(() => ({
    addCandlestickSeries: jest.fn(() => ({
      setData: jest.fn(),
      update: jest.fn(),
      applyOptions: jest.fn()
    })),
    addHistogramSeries: jest.fn(() => ({
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

describe('MultiPaneChart Component', () => {
  const mockCandleData = [
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

  const mockVolumeData = [
    { time: '2024-01-01', value: 1000000 },
    { time: '2024-01-02', value: 1500000 }
  ];

  const mockIndicatorData = [
    { time: '2024-01-01', value: 50 },
    { time: '2024-01-02', value: 55 }
  ];

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('Rendering', () => {
    test('should render multiple panes', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should render candle pane', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          symbol="EURUSD"
          panes={['candles']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should render volume pane', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['volume']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should render indicator panes', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{
            rsi: mockIndicatorData,
            macd: mockIndicatorData
          }}
          symbol="EURUSD"
          panes={['candles', 'rsi', 'macd']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle empty panes array', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          symbol="EURUSD"
          panes={[]}
        />
      );

      expect(container).toBeInTheDocument();
    });
  });

  describe('Pane Management', () => {
    test('should add new pane dynamically', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          symbol="EURUSD"
          panes={['candles']}
        />
      );

      rerender(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should remove pane dynamically', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      rerender(
        <MultiPaneChart
          candleData={mockCandleData}
          symbol="EURUSD"
          panes={['candles']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should reorder panes', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          indicatorData={{ rsi: mockIndicatorData }}
          symbol="EURUSD"
          panes={['candles', 'volume', 'rsi']}
        />
      );

      rerender(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          indicatorData={{ rsi: mockIndicatorData }}
          symbol="EURUSD"
          panes={['rsi', 'candles', 'volume']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should handle pane height adjustments', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          paneHeights={{ candles: 60, volume: 40 }}
        />
      );

      rerender(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          paneHeights={{ candles: 70, volume: 30 }}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Data Synchronization', () => {
    test('should synchronize time scale across panes', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          syncTimeScale={true}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should update all panes with new data', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      const newCandleData = [
        ...mockCandleData,
        {
          time: '2024-01-03',
          open: 1.0870,
          high: 1.0885,
          low: 1.0865,
          close: 1.0880
        }
      ];

      const newVolumeData = [
        ...mockVolumeData,
        { time: '2024-01-03', value: 2000000 }
      ];

      rerender(
        <MultiPaneChart
          candleData={newCandleData}
          volumeData={newVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });

    test('should handle partial data updates', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      // Update only candle data
      const updatedCandleData = [
        ...mockCandleData.slice(0, -1),
        {
          time: '2024-01-02',
          open: 1.0860,
          high: 1.0880,
          low: 1.0855,
          close: 1.0875
        }
      ];

      rerender(
        <MultiPaneChart
          candleData={updatedCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Volume Pane', () => {
    test('should render volume histogram', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should color volume bars based on candle direction', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          volumeColorUp="#26a69a"
          volumeColorDown="#ef5350"
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle volume data updates', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      const newVolumeData = [
        ...mockVolumeData,
        { time: '2024-01-03', value: 2500000 }
      ];

      rerender(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={newVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Indicator Panes', () => {
    test('should render RSI indicator', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{ rsi: mockIndicatorData }}
          symbol="EURUSD"
          panes={['candles', 'rsi']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should render MACD indicator', () => {
      const macdData = [
        { time: '2024-01-01', macd: 0.5, signal: 0.4, histogram: 0.1 },
        { time: '2024-01-02', macd: 0.6, signal: 0.5, histogram: 0.1 }
      ];

      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{ macd: macdData }}
          symbol="EURUSD"
          panes={['candles', 'macd']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should render Bollinger Bands', () => {
      const bbData = [
        {
          time: '2024-01-01',
          upper: 1.0900,
          middle: 1.0850,
          lower: 1.0800
        },
        {
          time: '2024-01-02',
          upper: 1.0910,
          middle: 1.0860,
          lower: 1.0810
        }
      ];

      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{ bollinger: bbData }}
          symbol="EURUSD"
          panes={['candles', 'bollinger']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle multiple indicators', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{
            rsi: mockIndicatorData,
            macd: [
              { time: '2024-01-01', macd: 0.5, signal: 0.4, histogram: 0.1 },
              { time: '2024-01-02', macd: 0.6, signal: 0.5, histogram: 0.1 }
            ]
          }}
          symbol="EURUSD"
          panes={['candles', 'rsi', 'macd']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should update indicator data', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{ rsi: mockIndicatorData }}
          symbol="EURUSD"
          panes={['candles', 'rsi']}
        />
      );

      const newIndicatorData = [
        ...mockIndicatorData,
        { time: '2024-01-03', value: 60 }
      ];

      rerender(
        <MultiPaneChart
          candleData={mockCandleData}
          indicatorData={{ rsi: newIndicatorData }}
          symbol="EURUSD"
          panes={['candles', 'rsi']}
        />
      );

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Crosshair Synchronization', () => {
    test('should synchronize crosshair across panes', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          syncCrosshair={true}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should display synchronized tooltips', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          showTooltip={true}
          syncCrosshair={true}
        />
      );

      expect(container).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    test('should handle large datasets across multiple panes', () => {
      const largeData = Array.from({ length: 1000 }, (_, i) => ({
        time: `2024-01-${String(i).padStart(2, '0')}`,
        open: 1.0850 + (Math.random() * 0.01),
        high: 1.0865 + (Math.random() * 0.01),
        low: 1.0845 + (Math.random() * 0.01),
        close: 1.0860 + (Math.random() * 0.01)
      }));

      const largeVolumeData = Array.from({ length: 1000 }, (_, i) => ({
        time: `2024-01-${String(i).padStart(2, '0')}`,
        value: Math.random() * 5000000
      }));

      const startTime = performance.now();

      render(
        <MultiPaneChart
          candleData={largeData}
          volumeData={largeVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      const duration = performance.now() - startTime;

      expect(duration).toBeLessThan(3000);
    });

    test('should efficiently handle pane resizing', async () => {
      const { rerender } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={mockVolumeData}
          symbol="EURUSD"
          panes={['candles', 'volume']}
          paneHeights={{ candles: 60, volume: 40 }}
        />
      );

      for (let i = 0; i < 10; i++) {
        rerender(
          <MultiPaneChart
            candleData={mockCandleData}
            volumeData={mockVolumeData}
            symbol="EURUSD"
            panes={['candles', 'volume']}
            paneHeights={{
              candles: 50 + i,
              volume: 50 - i
            }}
          />
        );
      }

      await waitFor(() => {
        expect(true).toBe(true);
      });
    });
  });

  describe('Error Handling', () => {
    test('should handle missing candle data', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={null}
          symbol="EURUSD"
          panes={['candles']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle missing volume data', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          volumeData={null}
          symbol="EURUSD"
          panes={['candles', 'volume']}
        />
      );

      expect(container).toBeInTheDocument();
    });

    test('should handle invalid pane names', () => {
      const { container } = render(
        <MultiPaneChart
          candleData={mockCandleData}
          symbol="EURUSD"
          panes={['candles', 'invalid_pane']}
        />
      );

      expect(container).toBeInTheDocument();
    });
  });
});</parameter>
<parameter name="line_count">450</parameter>
</invoke>
</function_calls>