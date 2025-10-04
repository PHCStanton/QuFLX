import React from 'react';
import IndicatorChart from './charts/IndicatorChart';

const IndicatorPanel = ({ data, activeIndicators, onIndicatorToggle }) => {
  const indicators = [
    { id: 'sma', name: 'SMA (20)', color: '#8b5cf6', description: 'Simple Moving Average' },
    { id: 'ema', name: 'EMA (20)', color: '#06d6a0', description: 'Exponential Moving Average' },
    { id: 'rsi', name: 'RSI (14)', color: '#f59e0b', description: 'Relative Strength Index' },
    { id: 'macd', name: 'MACD', color: '#ef4444', description: 'Moving Average Convergence Divergence' }
  ];

  const RSIChart = ({ data }) => (
    <div className="bg-white/5 backdrop-blur-md rounded-lg border border-white/10 p-4 mb-4">
      <h4 className="text-white font-semibold mb-2">RSI Indicator</h4>
      <IndicatorChart
        data={data}
        enabledIndicators={{ rsi: true }}
        theme="dark"
        height={150}
        className="rounded-lg"
      />
    </div>
  );

  const MACDChart = ({ data }) => (
    <div className="bg-white/5 backdrop-blur-md rounded-lg border border-white/10 p-4 mb-4">
      <h4 className="text-white font-semibold mb-2">MACD Indicator</h4>
      <IndicatorChart
        data={data}
        enabledIndicators={{ macd: true }}
        theme="dark"
        height={150}
        className="rounded-lg"
      />
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Indicator Controls */}
      <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-4">
        <h3 className="text-white font-semibold text-lg mb-4">Technical Indicators</h3>
        <div className="grid grid-cols-2 gap-4">
          {indicators.map((indicator) => (
            <div key={indicator.id} className="flex items-center justify-between">
              <div>
                <span className="text-white font-medium">{indicator.name}</span>
                <p className="text-gray-400 text-sm">{indicator.description}</p>
              </div>
              <button
                onClick={() => onIndicatorToggle(indicator.id)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 ${
                  activeIndicators.includes(indicator.id) 
                    ? 'bg-blue-600' 
                    : 'bg-gray-600'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    activeIndicators.includes(indicator.id) 
                      ? 'translate-x-6' 
                      : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* RSI Chart */}
      {activeIndicators.includes('rsi') && data.length > 0 && (
        <RSIChart data={data} />
      )}

      {/* MACD Chart */}
      {activeIndicators.includes('macd') && data.length > 0 && (
        <MACDChart data={data} />
      )}

      {/* Indicator Legend */}
      <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-4">
        <h4 className="text-white font-semibold mb-3">Active Indicators</h4>
        <div className="space-y-2">
          {indicators
            .filter(indicator => activeIndicators.includes(indicator.id))
            .map((indicator) => (
              <div key={indicator.id} className="flex items-center gap-3">
                <div 
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: indicator.color }}
                />
                <span className="text-gray-300">{indicator.name}</span>
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default IndicatorPanel;