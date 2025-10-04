import React, { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { backtest, strategies } from '../utils/tradingData';

const BacktestPanel = ({ data, indicators }) => {
  const [selectedStrategy, setSelectedStrategy] = useState('smaGoldenCross');
  const [backtestResults, setBacktestResults] = useState(null);
  const [isRunning, setIsRunning] = useState(false);

  const strategyOptions = [
    { id: 'smaGoldenCross', name: 'SMA Golden Cross', description: 'Buy when SMA20 crosses above SMA50' },
    { id: 'rsiOversold', name: 'RSI Oversold/Overbought', description: 'Buy at RSI < 30, Sell at RSI > 70' },
    { id: 'macdCrossover', name: 'MACD Crossover', description: 'Buy when MACD crosses above signal line' }
  ];

  const runBacktest = async () => {
    if (!data || data.length < 50) return;
    
    setIsRunning(true);
    
    // Simulate processing delay
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    try {
      const strategy = strategies[selectedStrategy];
      const results = backtest(data, strategy, indicators);
      setBacktestResults(results);
    } catch (error) {
      console.error('Backtesting error:', error);
    }
    
    setIsRunning(false);
  };

  const MetricCard = ({ title, value, subtitle, color = 'blue' }) => (
    <div className="bg-white/5 backdrop-blur-md rounded-lg border border-white/10 p-4">
      <h4 className="text-gray-400 text-sm font-medium">{title}</h4>
      <p className={`text-2xl font-bold text-${color}-400 mt-1`}>{value}</p>
      {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
    </div>
  );

  const TradesList = ({ trades }) => (
    <div className="bg-white/5 backdrop-blur-md rounded-lg border border-white/10 p-4">
      <h4 className="text-white font-semibold mb-4">Recent Trades</h4>
      <div className="max-h-64 overflow-y-auto">
        {trades.slice(-10).map((trade, index) => (
          <div key={index} className="flex justify-between items-center py-2 border-b border-white/10 last:border-b-0">
            <div>
              <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                trade.type === 'LONG' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                {trade.type}
              </span>
              <span className="text-gray-400 text-sm ml-2">
                {new Date(trade.entryTime).toLocaleDateString()}
              </span>
            </div>
            <div className="text-right">
              <p className={`font-medium ${trade.profit > 0 ? 'text-green-400' : 'text-red-400'}`}>
                {trade.profit > 0 ? '+' : ''}${trade.profit.toFixed(2)}
              </p>
              <p className="text-gray-500 text-sm">{trade.profitPercent.toFixed(2)}%</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const ProfitChart = ({ trades }) => {
    const chartData = trades.map((trade, index) => ({
      trade: index + 1,
      profit: trade.profit,
      cumulative: trades.slice(0, index + 1).reduce((sum, t) => sum + t.profit, 0)
    }));

    return (
      <div className="bg-white/5 backdrop-blur-md rounded-lg border border-white/10 p-4">
        <h4 className="text-white font-semibold mb-4">Profit/Loss Distribution</h4>
        <ResponsiveContainer width="100%" height={200}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
            <XAxis 
              tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 10 }}
              stroke="rgba(255,255,255,0.3)"
            />
            <YAxis 
              tick={{ fill: 'rgba(255,255,255,0.7)', fontSize: 10 }}
              stroke="rgba(255,255,255,0.3)"
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255,255,255,0.1)', 
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                backdropFilter: 'blur(10px)'
              }}
            />
            <Bar dataKey="profit" fill={(entry) => entry.profit > 0 ? '#10b981' : '#ef4444'} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  };

  const WinRateChart = () => {
    if (!backtestResults) return null;
    
    const data = [
      { name: 'Winning Trades', value: backtestResults.winningTrades, color: '#10b981' },
      { name: 'Losing Trades', value: backtestResults.totalTrades - backtestResults.winningTrades, color: '#ef4444' }
    ];

    return (
      <div className="bg-white/5 backdrop-blur-md rounded-lg border border-white/10 p-4">
        <h4 className="text-white font-semibold mb-4">Win Rate Analysis</h4>
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={40}
              outerRadius={80}
              paddingAngle={5}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(255,255,255,0.1)', 
                border: '1px solid rgba(255,255,255,0.2)',
                borderRadius: '8px',
                backdropFilter: 'blur(10px)'
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Strategy Selection */}
      <div className="bg-white/5 backdrop-blur-md rounded-xl border border-white/10 p-4">
        <h3 className="text-white font-semibold text-lg mb-4">Backtest Configuration</h3>
        
        <div className="mb-4">
          <label className="block text-gray-300 text-sm font-medium mb-2">
            Select Trading Strategy
          </label>
          <select
            value={selectedStrategy}
            onChange={(e) => setSelectedStrategy(e.target.value)}
            className="w-full bg-white/10 border border-white/20 rounded-lg px-3 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {strategyOptions.map((strategy) => (
              <option key={strategy.id} value={strategy.id} className="bg-gray-800">
                {strategy.name}
              </option>
            ))}
          </select>
          <p className="text-gray-400 text-sm mt-1">
            {strategyOptions.find(s => s.id === selectedStrategy)?.description}
          </p>
        </div>

        <button
          onClick={runBacktest}
          disabled={isRunning || !data || data.length < 50}
          className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 disabled:from-gray-600 disabled:to-gray-700 text-white font-medium py-2 px-4 rounded-lg transition-all duration-200 disabled:cursor-not-allowed"
        >
          {isRunning ? (
            <div className="flex items-center justify-center">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Running Backtest...
            </div>
          ) : (
            'Run Backtest'
          )}
        </button>
      </div>

      {/* Results */}
      {backtestResults && (
        <>
          {/* Performance Metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <MetricCard
              title="Total Return"
              value={`${backtestResults.totalReturn.toFixed(2)}%`}
              subtitle="Overall performance"
              color={backtestResults.totalReturn > 0 ? 'green' : 'red'}
            />
            <MetricCard
              title="Win Rate"
              value={`${backtestResults.winRate.toFixed(1)}%`}
              subtitle={`${backtestResults.winningTrades}/${backtestResults.totalTrades} trades`}
              color="blue"
            />
            <MetricCard
              title="Final Balance"
              value={`$${backtestResults.finalBalance.toFixed(2)}`}
              subtitle="Starting: $10,000"
              color={backtestResults.finalBalance > 10000 ? 'green' : 'red'}
            />
            <MetricCard
              title="Profit Factor"
              value={backtestResults.profitFactor.toFixed(2)}
              subtitle="Profit/Loss ratio"
              color={backtestResults.profitFactor > 1 ? 'green' : 'red'}
            />
          </div>

          {/* Charts and Analysis */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {backtestResults.trades.length > 0 && <ProfitChart trades={backtestResults.trades} />}
            <WinRateChart />
          </div>

          {/* Trades List */}
          {backtestResults.trades.length > 0 && <TradesList trades={backtestResults.trades} />}
        </>
      )}
    </div>
  );
};

export default BacktestPanel;