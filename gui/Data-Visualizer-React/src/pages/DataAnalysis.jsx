import React, { useState, useEffect, useCallback } from 'react';
import LightweightChart from '../components/charts/LightweightChart';
import { fetchCurrencyPairs } from '../utils/fileUtils';
import { parseTradingData } from '../utils/tradingData';
import { useWebSocket } from '../hooks/useWebSocket';

const DataAnalysis = () => {
  const [dataSource, setDataSource] = useState('csv');
  const [timeframe, setTimeframe] = useState('1m');
  const [selectedAsset, setSelectedAsset] = useState('');
  const [availableAssets, setAvailableAssets] = useState([]);
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingStatus, setLoadingStatus] = useState('');
  const [isLiveMode, setIsLiveMode] = useState(false);
  const [statistics, setStatistics] = useState(null);
  
  // WebSocket connection for live streaming
  const { isConnected, lastMessage, socketRef } = useWebSocket('/socket.io');

  const dataSources = [
    { id: 'csv', name: 'CSV Files (Historical)' },
    { id: 'platform', name: 'Platform WebSocket', disabled: true },
    { id: 'binance', name: 'Binance API', disabled: true },
  ];

  const timeframes = ['1m', '5m', '15m', '1h', '4h'];

  const loadAvailableAssets = useCallback(async () => {
    if (dataSource === 'csv') {
      const pairs = await fetchCurrencyPairs(timeframe);
      setAvailableAssets(pairs);
      if (pairs.length > 0) {
        setSelectedAsset(pairs[0].id);
      }
    }
  }, [dataSource, timeframe]);

  const loadHistoricalData = useCallback(async () => {
    setLoading(true);
    setLoadingStatus('Fetching CSV file...');
    setStatistics(null);
    
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
        
        setLoadingStatus('Parsing CSV data...');
        const csvText = await response.text();
        const data = parseTradingData(csvText, selectedAsset);
        
        setLoadingStatus('Rendering chart...');
        setChartData(data);
        
        // Calculate statistics
        if (data.length > 0) {
          const latest = data[data.length - 1];
          const first = data[0];
          const priceChange = latest.close - first.close;
          const priceChangePercent = ((priceChange / first.close) * 100).toFixed(2);
          
          setStatistics({
            latestPrice: latest.close.toFixed(5),
            open: latest.open.toFixed(5),
            high: latest.high.toFixed(5),
            low: latest.low.toFixed(5),
            priceChange: priceChange.toFixed(5),
            priceChangePercent: priceChangePercent,
            dataPoints: data.length,
            timeRange: `${first.date.toLocaleString()} - ${latest.date.toLocaleString()}`
          });
        }
        
        console.log(`Loaded ${data.length} data points for ${selectedAsset}`);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      alert(`Failed to load data: ${error.message || 'Unknown error'}`);
      setStatistics(null);
    }
    setLoading(false);
    setLoadingStatus('');
  }, [availableAssets, selectedAsset, dataSource, timeframe]);

  useEffect(() => {
    loadAvailableAssets();
  }, [loadAvailableAssets]);

  useEffect(() => {
    if (selectedAsset && !isLiveMode) {
      loadHistoricalData();
    }
  }, [selectedAsset, timeframe, isLiveMode, loadHistoricalData]);

  // Handle streaming data updates
  useEffect(() => {
    if (isLiveMode && lastMessage) {
      // Add new tick to chart data
      const newDataPoint = {
        timestamp: Math.floor(lastMessage.timestamp / 1000),
        date: new Date(lastMessage.timestamp),
        open: lastMessage.price,
        close: lastMessage.price,
        high: lastMessage.price,
        low: lastMessage.price,
        volume: lastMessage.volume || 0,
        symbol: lastMessage.asset
      };
      
      setChartData(prevData => {
        const newData = [...prevData, newDataPoint];
        // Keep last 500 data points for performance
        return newData.slice(-500);
      });
    }
  }, [isLiveMode, lastMessage]);

  const toggleLiveMode = () => {
    const newLiveMode = !isLiveMode;
    setIsLiveMode(newLiveMode);
    
    if (newLiveMode && socketRef.current && isConnected) {
      // Start streaming when enabling live mode
      socketRef.current.emit('start_stream', {
        asset: selectedAsset || 'EURUSD_OTC'
      });
      console.log('Started live stream for', selectedAsset);
    } else if (!newLiveMode && socketRef.current) {
      // Stop streaming when disabling live mode
      socketRef.current.emit('stop_stream');
      console.log('Stopped live stream');
      // Reload historical data
      if (selectedAsset) {
        loadHistoricalData();
      }
    }
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
                disabled={!isConnected}
                className="rounded"
              />
              <span className="text-sm text-slate-300">
                Live Stream Mode {!isConnected && '(Connecting...)'}
              </span>
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

      {statistics && (
        <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
          <h3 className="text-xl font-semibold text-white mb-4">Statistics</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Current Price</div>
              <div className="text-white text-lg font-semibold">{statistics.latestPrice}</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Change</div>
              <div className={`text-lg font-semibold ${parseFloat(statistics.priceChangePercent) >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                {statistics.priceChange} ({statistics.priceChangePercent}%)
              </div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">High / Low</div>
              <div className="text-white text-lg font-semibold">{statistics.high} / {statistics.low}</div>
            </div>
            <div className="bg-slate-700/50 rounded-lg p-4">
              <div className="text-slate-400 text-sm mb-1">Data Points</div>
              <div className="text-white text-lg font-semibold">{statistics.dataPoints}</div>
            </div>
          </div>
        </div>
      )}

      <div className="bg-slate-800/60 rounded-xl border border-slate-700 p-6">
        <h3 className="text-xl font-semibold text-white mb-4">Chart</h3>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div className="text-slate-300 mb-2">{loadingStatus}</div>
              <div className="w-12 h-12 border-4 border-slate-600 border-t-blue-500 rounded-full animate-spin mx-auto"></div>
            </div>
          </div>
        ) : (
          <LightweightChart data={chartData} height={500} />
        )}
      </div>
    </div>
  );
};

export default DataAnalysis;
