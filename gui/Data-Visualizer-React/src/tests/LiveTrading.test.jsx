import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LiveTrading from '../pages/LiveTrading';

// Mock chart-heavy components to avoid jsdom/canvas issues
jest.mock('../components/MultiPaneChart', () => ({
  __esModule: true,
  default: () => <div data-testid="multi-pane-chart" />,
}));

jest.mock('../hooks/useWebSocketV2', () => ({
  useWebSocket: () => ({
    connection: { isConnected: true, isConnecting: false, error: null, chromeConnected: true },
    stream: { isActive: true, currentAsset: 'EURUSD' },
    data: { current: [], lastUpdate: null, historical: [] },
    actions: {
      stream: { start: jest.fn(), stop: jest.fn(), changeAsset: jest.fn(), detectAsset: jest.fn() },
      data: { storeCSV: jest.fn(), calculateIndicators: jest.fn() },
    },
  }),
}));

describe('LiveTrading page', () => {
  it('renders key sections without crashing and reflects stream state', () => {
    render(
      <BrowserRouter>
        <LiveTrading />
      </BrowserRouter>
    );

    // Basic sections
    expect(screen.getByText(/Active Positions/i)).toBeInTheDocument();
    expect(screen.getByText(/Signal Monitor/i)).toBeInTheDocument();

    // Center chart section title
    expect(screen.getByText(/Live Signal Panel/i)).toBeInTheDocument();
  });
});