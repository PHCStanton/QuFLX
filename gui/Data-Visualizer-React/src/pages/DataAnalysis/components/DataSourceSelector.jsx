import React from 'react';

const DataSourceSelector = ({
  dataSource,
  setDataSource,
  timeframe,
  setTimeframe,
  isLiveMode
}) => {
  const dataSources = [
    { id: 'csv', name: 'CSV Files (Historical Data)' },
    { id: 'platform', name: 'Platform WebSocket (Live Streaming)' },
    { id: 'binance', name: 'Binance API', disabled: true },
  ];

  const timeframes = ['1m', '5m', '15m', '1h', '4h'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div>
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--text-secondary)' }}
        >
          Data Provider
        </label>
        <select
          value={dataSource}
          onChange={(e) => setDataSource(e.target.value)}
          className="w-full glass border rounded-lg px-4 py-2 focus:outline-none focus:ring-2"
          style={{
            backgroundColor: 'var(--card-bg)',
            borderColor: 'var(--card-border)',
            color: 'var(--text-primary)'
          }}
        >
          {dataSources.map(source => (
            <option key={source.id} value={source.id} disabled={source.disabled}>
              {source.name} {source.disabled ? '(Coming Soon)' : ''}
            </option>
          ))}
        </select>
      </div>

      <div>
        <label
          className="block text-sm font-medium mb-2"
          style={{ color: 'var(--text-secondary)' }}
        >
          Timeframe
        </label>
        <select
          value={timeframe}
          onChange={(e) => setTimeframe(e.target.value)}
          className="w-full glass border rounded-lg px-4 py-2 focus:outline-none focus:ring-2"
          style={{
            backgroundColor: 'var(--card-bg)',
            borderColor: 'var(--card-border)',
            color: 'var(--text-primary)'
          }}
          disabled={dataSource === 'platform' || isLiveMode}
        >
          {timeframes.map(tf => (
            <option key={tf} value={tf}>{tf}</option>
          ))}
        </select>
        {dataSource === 'platform' && (
          <p className="text-xs text-slate-400 mt-1">Platform uses 1M timeframe</p>
        )}
      </div>
    </div>
  );
};

export default DataSourceSelector;