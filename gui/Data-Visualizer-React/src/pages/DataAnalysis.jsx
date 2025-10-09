import React, { useState, useEffect, useCallback, useRef } from 'react';
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
  
  // WebSocket connection for live streaming (dynamic backend URL detection)
  const { isConnected, isConnecting, lastMessage, chromeStatus, streamActive, streamAsset, startStream, stopStream, changeAsset } = useWebSocket();
  // Buffer for candle updates with backpressure handling
  const candleBufferRef = useRef([]);
  const processingRef = useRef(false);
  const processTimerRef = useRef(null);
  const MAX_BUFFER_SIZE = 1000;

  // Platform WebSocket is only enabled when Chrome is connected
  const chromeConnected = chromeStatus === 'connected';
  
  const dataSources = [
    { id: 'csv', name: 'CSV Files (Historical Data)' },
    { id: 'platform', name: 'Platform WebSocket (Live Streaming)' },
    { id: 'binance', name: 'Binance API', disabled: true },
  ];

  const timeframes = ['1m', '5m', '15m', '1h', '4h'];

  // Platform assets (hardcoded - available via WebSocket streaming)
  const platformAssets = [
    { id: 'EURUSD_OTC', name: 'EUR/USD OTC', file: null },
    { id: 'GBPUSD_OTC', name: 'GBP/USD OTC', file: null },
    { id: 'USDJPY_OTC', name: 'USD/JPY OTC', file: null },
    { id: 'AUDUSD_OTC', name: 'AUD/USD OTC', file: null },
  ];

  const loadAvailableAssets = useCallback(async () => {
    if (dataSource === 'csv') {
      // Load CSV files from backend (filtered by timeframe)
      const pairs = await fetchCurrencyPairs(timeframe);
      setAvailableAssets(pairs);
      
      // Validate current asset is in the new list, reset if not
      const isValidAsset = pairs.some(p => p.id === selectedAsset);
      if (!isValidAsset && pairs.length > 0) {
        setSelectedAsset(pairs[0].id);
        console.log(`Asset reset to ${pairs[0].id} (previous asset not in CSV list)`);
      }
    } else if (dataSource === 'platform') {
      // Use platform assets (WebSocket streaming)
      setAvailableAssets(platformAssets);
      
      // Validate current asset is in the new list, reset if not
      const isValidAsset = platformAssets.some(p => p.id === selectedAsset);
      if (!isValidAsset && platformAssets.length > 0) {
        setSelectedAsset(platformAssets[0].id);
        console.log(`Asset reset to ${platformAssets[0].id} (previous asset not in platform list)`);
      }
    }
  }, [dataSource, timeframe, selectedAsset]);

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
    if (selectedAsset && !isLiveMode && dataSource === 'csv') {
      loadHistoricalData();
    }
  }, [selectedAsset, timeframe, isLiveMode, loadHistoricalData, dataSource]);

  // When switching to platform mode, automatically enable live mode if Chrome is connected
  useEffect(() => {
    if (dataSource === 'platform' && isConnected && chromeConnected && selectedAsset) {
      // Validate asset exists in platform list before streaming (prevent race condition)
      const isValidPlatformAsset = platformAssets.some(p => p.id === selectedAsset);
      if (isValidPlatformAsset) {
        if (!isLiveMode) {
          // First time enabling live mode - use startStream
          setIsLiveMode(true);
          startStream(selectedAsset);
        } else {
          // Already in live mode, just change asset - use changeAsset
          changeAsset(selectedAsset);
        }
      } else {
        console.warn(`Cannot start stream: ${selectedAsset} not in platform asset list`);
      }
    } else if (dataSource === 'platform' && (!isConnected || !chromeConnected)) {
      // Chrome/backend disconnected while in platform mode - disable live mode
      setIsLiveMode(false);
      stopStream();
    } else if (dataSource === 'csv') {
      setIsLiveMode(false);
      stopStream();
    }
  }, [dataSource, isConnected, chromeConnected, selectedAsset, isLiveMode, startStream, changeAsset, stopStream]);

  // Push candles into buffer with asset gating and backpressure handling
  useEffect(() => {
    if (!isLiveMode || !lastMessage) return;
    const gateAsset = dataSource === 'platform' ? (streamAsset || selectedAsset) : selectedAsset;
    if (lastMessage.asset === gateAsset) {
      // Backpressure: limit buffer size
      if (candleBufferRef.current.length > MAX_BUFFER_SIZE) {
        candleBufferRef.current = candleBufferRef.current.slice(-MAX_BUFFER_SIZE / 2);
      }
      candleBufferRef.current.push(lastMessage);
    }
  }, [isLiveMode, lastMessage, selectedAsset, dataSource, streamAsset]);

  // Simplified candle processing loop (~10 fps)
  useEffect(() => {
    if (!isLiveMode) {
      // Clear buffer and stop processing when not live
      candleBufferRef.current = [];
      if (processTimerRef.current) {
        clearInterval(processTimerRef.current);
        processTimerRef.current = null;
      }
      return;
    }

    if (!processTimerRef.current) {
      processTimerRef.current = setInterval(() => {
        if (processingRef.current) return;
        processingRef.current = true;

        const buffer = candleBufferRef.current;
        if (buffer.length === 0) {
          processingRef.current = false;
          return;
        }

        // Take a snapshot of current buffer and clear it
        candleBufferRef.current = [];

        // Update chart with pre-formed candles from backend
        setChartData(prevData => {
          let data = prevData.slice();
          
          for (const candle of buffer) {
            const timestamp = candle.timestamp;
            
            if (data.length > 0) {
              const last = data[data.length - 1];
              
              // Update existing candle if same timestamp
              if (last.timestamp === timestamp) {
                data[data.length - 1] = {
                  timestamp: timestamp,
                  date: new Date(candle.date || timestamp * 1000),
                  open: candle.open,
                  high: candle.high,
                  low: candle.low,
                  close: candle.close,
                  volume: candle.volume || 0,
                  symbol: candle.asset
                };
                continue;
              }
              
              // Skip out-of-order candles
              if (timestamp < last.timestamp) {
                continue;
              }
            }

            // Append new candle
            data.push({
              timestamp: timestamp,
              date: new Date(candle.date || timestamp * 1000),
              open: candle.open,
              high: candle.high,
              low: candle.low,
              close: candle.close,
              volume: candle.volume || 0,
              symbol: candle.asset
            });
          }
          
          // Cap data length to prevent memory issues
          return data.slice(-500);
        });

        processingRef.current = false;
      }, 100); // ~10 fps
    }

    return () => {
      if (processTimerRef.current) {
        clearInterval(processTimerRef.current);
        processTimerRef.current = null;
      }
    };
  }, [isLiveMode]);

  const toggleLiveMode = () => {
    // Only applicable for Platform mode (CSV doesn't support live streaming)
    if (dataSource !== 'platform') return;
    
    const newLiveMode = !isLiveMode;
    
    // Only allow enabling live mode if both Chrome and backend are connected
    if (newLiveMode && (!isConnected || !chromeConnected)) {
      console.warn('Cannot enable live mode: Chrome or backend not connected');
      return;
    }
    
    setIsLiveMode(newLiveMode);
    
    if (newLiveMode) {
      // Start streaming when enabling live mode (already verified connections above)
      startStream(selectedAsset || 'EURUSD_OTC');
      console.log('Started live stream for', selectedAsset);
    } else {
      // Stop streaming when disabling live mode
      stopStream();
      console.log('Stopped live stream');
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

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              {dataSource === 'csv' ? 'CSV File' : 'Asset / Pair'}
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
            {dataSource === 'csv' && (
              <button
                onClick={loadHistoricalData}
                disabled={loading}
                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
              >
                {loading ? 'Loading...' : 'Load CSV Data'}
              </button>
            )}
            
            {dataSource === 'platform' && (
              <div className="flex items-center gap-2">
                {chromeConnected ? (
                  <>
                    <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse"></div>
                    <span className="text-sm text-green-400 font-medium">
                      Live Streaming {isLiveMode ? `(${selectedAsset})` : ''}
                    </span>
                  </>
                ) : (
                  <>
                    <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                    <span className="text-sm text-yellow-400 font-medium">
                      Waiting for Chrome connection...
                    </span>
                  </>
                )}
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : isConnecting ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
              <span className="text-xs text-slate-400">Backend: {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${chromeConnected ? 'bg-green-500' : 'bg-yellow-500'}`}></div>
              <span className="text-xs text-slate-400">Chrome: {chromeConnected ? 'Connected' : 'Not Connected'}</span>
            </div>
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
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-xl font-semibold text-white">Chart</h3>
          <span className={`text-xs px-2 py-1 rounded-full border ${isLiveMode ? 'bg-green-900/30 text-green-300 border-green-700' : 'bg-slate-700/50 text-slate-300 border-slate-600'}`}>
            {isLiveMode 
              ? `Streaming • ${dataSource === 'platform' ? (streamAsset || selectedAsset || '') : (selectedAsset || '')}` 
              : `Historical • ${selectedAsset || ''}`}
          </span>
        </div>
        {loading && !isLiveMode ? (
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
