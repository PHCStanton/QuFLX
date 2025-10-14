import React from 'react';

const StatisticsPanel = ({ statistics }) => {
  if (!statistics) return null;

  return (
    <div
      className="glass rounded-xl p-6"
      style={{ borderColor: 'var(--card-border)' }}
    >
      <h3
        className="text-xl font-semibold mb-4"
        style={{ color: 'var(--text-primary)' }}
      >Statistics</h3>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div
          className="glass rounded-lg p-4"
          style={{ borderColor: 'var(--card-border)' }}
        >
          <div
            className="text-sm mb-1"
            style={{ color: 'var(--text-muted)' }}
          >Current Price</div>
          <div
            className="text-lg font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >{statistics.latestPrice}</div>
        </div>
        <div
          className="glass rounded-lg p-4"
          style={{ borderColor: 'var(--card-border)' }}
        >
          <div
            className="text-sm mb-1"
            style={{ color: 'var(--text-muted)' }}
          >Change</div>
          <div
            className="text-lg font-semibold"
            style={{
              color: parseFloat(statistics.priceChangePercent) >= 0 ? 'var(--accent-green)' : 'var(--accent-red)'
            }}
          >
            {statistics.priceChange} ({statistics.priceChangePercent}%)
          </div>
        </div>
        <div
          className="glass rounded-lg p-4"
          style={{ borderColor: 'var(--card-border)' }}
        >
          <div
            className="text-sm mb-1"
            style={{ color: 'var(--text-muted)' }}
          >High / Low</div>
          <div
            className="text-lg font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >{statistics.high} / {statistics.low}</div>
        </div>
        <div
          className="glass rounded-lg p-4"
          style={{ borderColor: 'var(--card-border)' }}
        >
          <div
            className="text-sm mb-1"
            style={{ color: 'var(--text-muted)' }}
          >Data Points</div>
          <div
            className="text-lg font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >{statistics.dataPoints}</div>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPanel;