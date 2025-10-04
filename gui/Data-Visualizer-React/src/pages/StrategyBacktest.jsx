import React, { useState } from 'react';

const StrategyBacktest = () => {
  const [strategies, setStrategies] = useState([
    { id: '1', name: 'EMA Crossover', type: 'json', status: 'active' },
    { id: '2', name: 'RSI Mean Reversion', type: 'python', status: 'active' },
  ]);
  const [selectedStrategy, setSelectedStrategy] = useState('');
  const [backtestResults, setBacktestResults] = useState(null);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
            <h2 className="text-xl font-bold text-white mb-4">Strategy Manager</h2>
            
            <div className="space-y-3 mb-4">
              {strategies.map(strategy => (
                <div
                  key={strategy.id}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                    selectedStrategy === strategy.id
                      ? 'bg-blue-600/20 border-blue-500'
                      : 'bg-slate-700/50 border-slate-600 hover:border-slate-500'
                  }`}
                  onClick={() => setSelectedStrategy(strategy.id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-white">{strategy.name}</div>
                      <div className="text-xs text-slate-400">.{strategy.type}</div>
                    </div>
                    <span className={`text-xs px-2 py-1 rounded ${
                      strategy.status === 'active' 
                        ? 'bg-green-500/20 text-green-400' 
                        : 'bg-slate-500/20 text-slate-400'
                    }`}>
                      {strategy.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            <button className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors">
              + Upload Strategy
            </button>
          </div>

          <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Backtest Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Initial Capital
                </label>
                <input
                  type="number"
                  defaultValue={10000}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Position Size (%)
                </label>
                <input
                  type="number"
                  defaultValue={10}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                disabled={!selectedStrategy}
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                Run Backtest
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-800/60 rounded-xl border border-slate-700 p-6">
          <h2 className="text-xl font-bold text-white mb-4">Results Dashboard</h2>
          
          {backtestResults ? (
            <div>Results will appear here</div>
          ) : (
            <div className="flex items-center justify-center h-96">
              <div className="text-center text-slate-400">
                <div className="text-4xl mb-4">📊</div>
                <div>Select a strategy and run backtest to see results</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyBacktest;
