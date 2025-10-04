import React, { useState } from 'react';

const LiveTrading = () => {
  const [mode, setMode] = useState('signals');
  const [isRunning, setIsRunning] = useState(false);
  const [signals, setSignals] = useState([]);

  return (
    <div className="space-y-6">
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-white">Live Trading Control</h2>
          
          <div className="flex items-center gap-4">
            <div className="flex bg-slate-700 rounded-lg p-1">
              <button
                onClick={() => setMode('signals')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  mode === 'signals'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Signal Generation
              </button>
              <button
                onClick={() => setMode('trading')}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  mode === 'trading'
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                Live Trading
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Strategy
            </label>
            <select className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option>EMA Crossover</option>
              <option>RSI Mean Reversion</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Data Source
            </label>
            <select className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
              <option>Platform WebSocket</option>
              <option disabled>Binance (Coming Soon)</option>
            </select>
          </div>

          {mode === 'trading' && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Platform API
              </label>
              <select className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option>Platform API v1</option>
              </select>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Action
            </label>
            <button
              onClick={() => setIsRunning(!isRunning)}
              className={`w-full px-4 py-2 rounded-lg font-medium transition-colors ${
                isRunning
                  ? 'bg-red-600 hover:bg-red-700'
                  : 'bg-green-600 hover:bg-green-700'
              } text-white`}
            >
              {isRunning ? 'Stop' : 'Start'} {mode === 'signals' ? 'Detection' : 'Trading'}
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-slate-800/60 rounded-xl border border-slate-700 p-6">
          <h3 className="text-xl font-semibold text-white mb-4">
            {mode === 'signals' ? 'Signal Log' : 'Active Positions'}
          </h3>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Time</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Asset</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Direction</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                    {mode === 'signals' ? 'Confidence' : 'Size'}
                  </th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                    {mode === 'signals' ? 'Outcome' : 'P&L'}
                  </th>
                </tr>
              </thead>
              <tbody>
                {signals.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="text-center py-8 text-slate-400">
                      {isRunning ? 'Waiting for signals...' : 'Start detection to see signals'}
                    </td>
                  </tr>
                ) : (
                  signals.map((signal, idx) => (
                    <tr key={idx} className="border-b border-slate-700/50">
                      <td className="py-3 px-4 text-sm text-slate-300">{signal.time}</td>
                      <td className="py-3 px-4 text-sm text-slate-300">{signal.asset}</td>
                      <td className="py-3 px-4 text-sm">
                        <span className={signal.direction === 'BUY' ? 'text-green-400' : 'text-red-400'}>
                          {signal.direction}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-slate-300">{signal.value}</td>
                      <td className="py-3 px-4 text-sm text-slate-300">{signal.result}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Performance Metrics</h3>
          
          <div className="space-y-4">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-400 mb-1">
                {mode === 'signals' ? 'Signal Accuracy' : 'Total P&L'}
              </div>
              <div className="text-2xl font-bold text-white">
                {mode === 'signals' ? '0%' : '$0.00'}
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-400 mb-1">
                {mode === 'signals' ? 'Total Signals' : 'Win Rate'}
              </div>
              <div className="text-2xl font-bold text-white">
                {mode === 'signals' ? '0' : '0%'}
              </div>
            </div>

            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-sm text-slate-400 mb-1">
                {mode === 'signals' ? 'Profitable' : 'Active Trades'}
              </div>
              <div className="text-2xl font-bold text-green-400">
                {mode === 'signals' ? '0' : '0'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveTrading;
