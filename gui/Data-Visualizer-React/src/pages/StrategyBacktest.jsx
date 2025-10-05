import React, { useState, useEffect } from 'react';
import { strategyService } from '../services/StrategyService';

const StrategyBacktest = () => {
  const [strategies, setStrategies] = useState([]);
  const [selectedStrategy, setSelectedStrategy] = useState('quantum_flux');
  const [dataFiles, setDataFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [backtestResults, setBacktestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [config, setConfig] = useState({
    initialCapital: 10000,
    positionSize: 1
  });

  useEffect(() => {
    // Initialize Socket.IO connection
    strategyService.initializeSocket();
    
    // Load available data files
    loadDataFiles();

    // Add default quantum flux strategy
    setStrategies([
      { id: 'quantum_flux', name: 'Quantum Flux Strategy', type: 'python', status: 'active' }
    ]);
  }, []);

  const loadDataFiles = async () => {
    const result = await strategyService.getAvailableDataFiles();
    if (result.success) {
      setDataFiles(result.files);
      if (result.files.length > 0) {
        setSelectedFile(result.files[0].path);
      }
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const result = await strategyService.loadStrategy(file);
    if (result.success) {
      const newStrategy = strategyService.getStrategy(result.id);
      setStrategies([...strategies, newStrategy]);
      setSelectedStrategy(result.id);
    } else {
      alert(`Failed to load strategy: ${result.error}`);
    }
  };

  const runBacktest = async () => {
    if (!selectedFile || !selectedStrategy) {
      alert('Please select a strategy and data file');
      return;
    }

    setIsRunning(true);
    setBacktestResults(null);

    try {
      const result = await strategyService.runBacktest(selectedStrategy, selectedFile, config);
      
      if (result.success) {
        setBacktestResults(result.results);
      } else {
        alert(`Backtest failed: ${result.error}`);
      }
    } catch (error) {
      alert(`Error: ${error.message}`);
    } finally {
      setIsRunning(false);
    }
  };

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

            <label className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors cursor-pointer block text-center">
              + Upload Strategy
              <input
                type="file"
                accept=".json,.py"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>

          <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Data Selection</h3>
            
            <div className="space-y-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Historical Data File
                </label>
                <select
                  value={selectedFile}
                  onChange={(e) => setSelectedFile(e.target.value)}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {dataFiles.length === 0 ? (
                    <option>Loading files...</option>
                  ) : (
                    dataFiles.map((file, index) => (
                      <option key={file.path || index} value={file.path}>
                        {file.asset} - {file.filename} ({file.timeframe})
                      </option>
                    ))
                  )}
                </select>
                <div className="text-xs text-slate-400 mt-1">{dataFiles.length} files available</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
            <h3 className="text-lg font-semibold text-white mb-4">Backtest Configuration</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Initial Capital ($)
                </label>
                <input
                  type="number"
                  value={config.initialCapital}
                  onChange={(e) => setConfig({ ...config, initialCapital: Number(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Position Size (% per trade)
                </label>
                <input
                  type="number"
                  value={config.positionSize}
                  onChange={(e) => setConfig({ ...config, positionSize: Number(e.target.value) })}
                  className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                onClick={runBacktest}
                disabled={!selectedStrategy || !selectedFile || isRunning}
                className="w-full px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                {isRunning ? 'Running...' : 'Run Backtest'}
              </button>
            </div>
          </div>
        </div>

        <div className="lg:col-span-2 bg-slate-800/60 rounded-xl border border-slate-700 p-6">
          <h2 className="text-xl font-bold text-white mb-4">Results Dashboard</h2>
          
          {backtestResults ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Total Trades</div>
                  <div className="text-2xl font-bold text-white">{backtestResults.statistics.total_trades}</div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Win Rate</div>
                  <div className="text-2xl font-bold text-green-400">
                    {backtestResults.statistics.win_rate.toFixed(1)}%
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Profit/Loss</div>
                  <div className={`text-2xl font-bold ${backtestResults.statistics.total_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    ${backtestResults.statistics.total_profit.toFixed(2)}
                  </div>
                </div>
                <div className="bg-slate-700/50 rounded-lg p-4">
                  <div className="text-sm text-slate-400">Return</div>
                  <div className={`text-2xl font-bold ${backtestResults.statistics.profit_percentage >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {backtestResults.statistics.profit_percentage.toFixed(2)}%
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-white mb-3">Trade History</h3>
                <div className="bg-slate-700/50 rounded-lg p-4 max-h-96 overflow-y-auto">
                  <div className="space-y-2">
                    {backtestResults.trades.slice(0, 20).map((trade, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-slate-800/50 rounded">
                        <div className="flex items-center gap-4">
                          <span className={`px-2 py-1 rounded text-xs ${
                            trade.signal === 'call' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {trade.signal.toUpperCase()}
                          </span>
                          <span className="text-sm text-slate-400">
                            {new Date(trade.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className={`text-sm font-medium ${trade.won ? 'text-green-400' : 'text-red-400'}`}>
                            {trade.won ? '+' : ''}{trade.profit.toFixed(2)}
                          </span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            trade.won ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                          }`}>
                            {trade.won ? 'WIN' : 'LOSS'}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-96">
              <div className="text-center text-slate-400">
                <div className="text-4xl mb-4">📊</div>
                <div>Select a strategy and data file, then run backtest to see results</div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StrategyBacktest;
