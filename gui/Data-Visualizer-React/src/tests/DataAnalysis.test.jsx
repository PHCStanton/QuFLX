import React from 'react';
import { render, screen } from '@testing-library/react';
import DataAnalysis from '../pages/DataAnalysis';

// Mock chart-heavy components to avoid jsdom/canvas issues
jest.mock('../components/ChartContainer', () => ({
  __esModule: true,
  default: () => <div data-testid="chart-container" />,
}));

jest.mock('../components/IndicatorPanel', () => ({
  __esModule: true,
  default: () => <div data-testid="indicator-panel" />,
}));

jest.mock('../components/StatsPanel', () => ({
  __esModule: true,
  default: () => <div data-testid="stats-panel" />,
}));

jest.mock('../hooks/useWebSocketV2', () => ({
  useWebSocket: () => ({
    connection: { isConnected: true, chromeConnected: true },
    stream: { isActive: true, currentAsset: 'EURUSD' },
    asset: { detected: { asset: 'EURUSD', source: 'chrome' }, error: null },
    data: {
      current: [],
      historical: [],
      lastUpdate: Date.now(),
      indicators: { data: {}, error: null, isCalculating: false },
    },
    actions: {
      stream: { start: jest.fn(), stop: jest.fn(), detectAsset: jest.fn(), changeAsset: jest.fn() },
      data: { storeCSV: jest.fn(), calculateIndicators: jest.fn() },
    },
  }),
}));

describe('DataAnalysis page', () => {
  it('renders status bar with connection and stream info', () => {
    render(<DataAnalysis />);
    expect(screen.getByText(/WS Connected/i)).toBeInTheDocument();
    expect(screen.getByText(/Chrome: Connected/i)).toBeInTheDocument();
    expect(screen.getByText(/Stream: Active/i)).toBeInTheDocument();
    expect(screen.getByText(/Asset: EURUSD/i)).toBeInTheDocument();
  });
});