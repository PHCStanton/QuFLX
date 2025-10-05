import React, { useState, useEffect, useCallback } from 'react';
import LightweightChart from '../components/charts/LightweightChart';
import { fetchCurrencyPairs } from '../utils/fileUtils';
import { parseTradingData } from '../utils/tradingData';

const DataAnalysis = () => {
  const [dataSource, setDataSource] = useState('csv');
  const [timeframe, setTimeframe] = useState('1m');
  const [selectedAsset, setSelectedAsset] = useState('');
  const [availableAssets, setAvailableAssets] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isLiveMode, setIsLiveMode] = useState(false);

  const dataSources = [
    { id: 'csv', name: 'CSV Files (Historical)' },
    { id: 'platform', name: 'Platform WebSocket', disabled: true },
    { id: 'binance', name: 'Binance API', disabled: true },
  ];

  const timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d'];

  const loadAvailableAssets = useCallback(async () => {
    if (dataSource === 'csv') {
      const pairs = await fetchCurrencyPairs();
      setAvailableAssets(pairs);
      if (pairs.length > 0) {
        setSelectedAsset(pairs[0].id);
      }
    }
  }, [dataSource]);

  const loadHistoricalData = useCallback(async () => {
    setLoading(true);
    try {
      const assetInfo = availableAssets.find(a => a.id === selectedAsset);
      if (assetInfo && dataSource === 'csv') {
        // Use the new API endpoint to fetch CSV data (using Vite proxy)
        const response = await fetch(`/api/csv-data/${assetInfo.file}`, { 
          cache: 'no-store' 
        });
        
        if (!response.ok) {
          throw new Error(`Failed to load data: ${response.statusText}`);
        }
        
        const csvText = await response.text();
        const data = parseTradingData(csvText, selectedAsset);
        setChartData(data);
        console.log(`Loaded ${data.length} data points for ${selectedAsset}`);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      alert(`Failed to load data: ${error.message}`);
    }
    setLoading(false);
  }, [availableAssets, selectedAsset, dataSource, timeframe]);

  useEffect(() => {
    loadAvailableAssets();
  }, [loadAvailableAssets]);

  useEffect(() => {
    if (selectedAsset && !isLiveMode) {
      loadHistoricalData();
    }
  }, [selectedAsset, timeframe, isLiveMode, loadHistoricalData]);

  const toggleLiveMode = () => {
    setIsLiveMode(!isLiveMode);
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
        <h2 className="text-2xl font-bold text-white mb-6">Data Source Configuration</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Data Provider
            </label>
            <select
              value={dataSource}
              onChange={(e) => setDataSource(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {dataSources.map(source => (
                <option key={source.id} value={source.id} disabled={source.disabled}>
                  {source.name} {source.disabled ? '(Coming Soon)' : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Timeframe
            </label>
            <select
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLiveMode}
            >
              {timeframes.map(tf => (
                <option key={tf} value={tf}>{tf}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Asset / Pair
            </label>
            <select
              value={selectedAsset}
              onChange={(e) => setSelectedAsset(e.target.value)}
              className="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {availableAssets.map(asset => (
                <option key={asset.id} value={asset.id}>{asset.name}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={loadHistoricalData}
              disabled={isLiveMode || loading}
              className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
            >
              {loading ? 'Loading...' : 'Load Data'}
            </button>
            
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={isLiveMode}
                onChange={toggleLiveMode}
                disabled={dataSource === 'csv'}
                className="rounded"
              />
              <span className="text-sm text-slate-300">Live Stream Mode</span>
            </label>
          </div>

          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${isLiveMode ? 'bg-green-500 animate-pulse' : 'bg-slate-500'}`} />
            <span className="text-sm text-slate-300">
              {isLiveMode ? 'Live' : 'Historical'}
            </span>
          </div>
        </div>
      </div>

      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Chart</h3>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-slate-300">Loading chart data...</div>
          </div>
        ) : (
          <LightweightChart data={chartData} height={500} />
        )}
      </div>
    </div>
  );
};

export default DataAnalysis;
