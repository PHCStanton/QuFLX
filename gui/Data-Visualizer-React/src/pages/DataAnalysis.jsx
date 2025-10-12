import React, { useState, useEffect, useCallback, useRef } from 'react';
import LightweightChart from '../components/charts/LightweightChart';
import { fetchCurrencyPairs } from '../utils/fileUtils';
import { parseTradingData } from '../utils/tradingData';
import { useWebSocket } from '../hooks/useWebSocket';

// Stream lifecycle states for Platform mode
const STREAM_STATES = {
  IDLE: 'idle',                    // Chrome not connected
  READY: 'ready',                  // Chrome connected, ready to detect
  DETECTING: 'detecting',          // Detecting asset from PocketOption
  ASSET_DETECTED: 'asset_detected', // Asset detected, ready to stream
  STREAMING: 'streaming',          // Active stream
  ERROR: 'error'                   // Detection or streaming error
};

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
  
  // State machine for Platform streaming lifecycle
  const [streamState, setStreamState] = useState(STREAM_STATES.IDLE);
  const [streamError, setStreamError] = useState(null);
  const [detectedAsset, setDetectedAsset] = useState(null);
  
  // WebSocket connection for live streaming (dynamic backend URL detection)
  const { 
    isConnected, 
    isConnecting, 
    lastMessage, 
    chromeStatus, 
    streamActive, 
    streamAsset, 
    backendReconnected,
    chromeReconnected,
    detectedAsset: wsDetectedAsset,
    detectionError: wsDetectionError,
    isDetecting: wsIsDetecting,
    startStream, 
    stopStream, 
    changeAsset,
    detectAsset: wsDetectAsset,
    setReconnectionCallback 
  } = useWebSocket();
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
      // Platform mode: No asset dropdown, detection-based only
      // Clear any previous selectedAsset to prevent conflicts
      setAvailableAssets([]);
      setSelectedAsset('');
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

  // State machine: Manage Platform mode stream state transitions
  useEffect(() => {
    if (dataSource !== 'platform') {
      // Reset stream state when not in platform mode
      setStreamState(STREAM_STATES.IDLE);
      setDetectedAsset(null);
      setStreamError(null);
      return;
    }

    // Platform mode state transitions based on Chrome connection
    if (!chromeConnected) {
      setStreamState(STREAM_STATES.IDLE);
      setDetectedAsset(null);
    } else if (chromeConnected && streamState === STREAM_STATES.IDLE) {
      setStreamState(STREAM_STATES.READY);
      setStreamError(null);
    }
  }, [dataSource, chromeConnected, streamState]);

  // Sync WebSocket detection state with local state machine
  useEffect(() => {
    if (wsDetectedAsset && streamState === STREAM_STATES.DETECTING) {
      setDetectedAsset(wsDetectedAsset);
      setStreamState(STREAM_STATES.ASSET_DETECTED);
      setStreamError(null);
    } else if (wsDetectionError && streamState === STREAM_STATES.DETECTING) {
      setStreamError(wsDetectionError);
      setStreamState(STREAM_STATES.ERROR);
      setDetectedAsset(null);
    }
  }, [wsDetectedAsset, wsDetectionError, streamState]);

  // Handler: Detect asset from PocketOption
  const handleDetectAsset = useCallback(() => {
    if (!isConnected) {
      setStreamError('Backend not connected');
      setStreamState(STREAM_STATES.ERROR);
      return;
    }

    setStreamState(STREAM_STATES.DETECTING);
    setStreamError(null);
    wsDetectAsset(); // Use real WebSocket detection
  }, [isConnected, wsDetectAsset]);

  // Handler: Start streaming with detected asset
  const handleStartStream = useCallback(() => {
    if (!detectedAsset) {
      setStreamError('No asset detected');
      setStreamState(STREAM_STATES.ERROR);
      return;
    }

    console.log(`[StartStream] Starting stream for ${detectedAsset}...`);
    
    // Clear previous chart data
    setChartData([]);
    candleBufferRef.current = [];
    setStatistics(null);
    
    // Start streaming
    setIsLiveMode(true);
    startStream(detectedAsset);
    setStreamState(STREAM_STATES.STREAMING);
  }, [detectedAsset, startStream]);

  // Handler: Stop streaming
  const handleStopStream = useCallback(() => {
    console.log('[StopStream] Stopping stream...');
    setIsLiveMode(false);
    stopStream();
    setStreamState(STREAM_STATES.READY);
    setDetectedAsset(null);
  }, [stopStream]);

  useEffect(() => {
    loadAvailableAssets();
  }, [loadAvailableAssets]);

  // Setup reconnection callback to clear state and reload data
  useEffect(() => {
    const handleReconnection = () => {
      console.log('[Reconnection] Clearing chart data and reloading...');
      
      // Clear chart data and buffers
      setChartData([]);
      candleBufferRef.current = [];
      setStatistics(null);
      
      // Stop current stream if active
      if (isLiveMode) {
        stopStream();
        setIsLiveMode(false);
      }
      
      // Reset state machine for Platform mode
      if (dataSource === 'platform') {
        setStreamState(chromeConnected ? STREAM_STATES.READY : STREAM_STATES.IDLE);
        setDetectedAsset(null);
        setStreamError(null);
      }
      
      // Reload data based on current source
      if (dataSource === 'csv' && selectedAsset) {
        setTimeout(() => {
          loadHistoricalData();
        }, 500); // Short delay to ensure state is cleared
      }
      // Platform mode: State machine controls streaming, no auto-start
    };
    
    setReconnectionCallback(handleReconnection);
  }, [dataSource, selectedAsset, chromeConnected, isLiveMode, loadHistoricalData, stopStream, setReconnectionCallback]);

  // Auto-load CSV data when asset or timeframe changes
  useEffect(() => {
    if (selectedAsset && dataSource === 'csv') {
      loadHistoricalData();
    }
  }, [selectedAsset, timeframe, loadHistoricalData, dataSource]);

  // Clear chart when switching to Platform mode
  useEffect(() => {
    if (dataSource === 'platform') {
      // Clear everything when entering platform mode
      setChartData([]);
      setStatistics(null);
      candleBufferRef.current = [];
      setIsLiveMode(false);
      stopStream();
      setSelectedAsset(''); // Clear asset - will be detected
    }
  }, [dataSource, stopStream]);

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

  // Legacy toggleLiveMode removed - use state machine handlers instead (handleDetectAsset, handleStartStream, handleStopStream)

  return (
    <div className="space-y-6">
      <div
        className="glass rounded-xl p-6"
        style={{ borderColor: 'var(--card-border)' }}
      >
        <h2
          className="text-2xl font-bold mb-6"
          style={{ color: 'var(--text-primary)' }}
        >Data Source Configuration</h2>
        
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

          {/* CSV Mode: Show Asset Dropdown */}
          {dataSource === 'csv' && (
            <div>
              <label
                className="block text-sm font-medium mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                CSV File
              </label>
              <select
                value={selectedAsset}
                onChange={(e) => setSelectedAsset(e.target.value)}
                className="w-full glass border rounded-lg px-4 py-2 focus:outline-none focus:ring-2"
                style={{
                  backgroundColor: 'var(--card-bg)',
                  borderColor: 'var(--card-border)',
                  color: 'var(--text-primary)'
                }}
              >
                {availableAssets.map(asset => (
                  <option key={asset.id} value={asset.id}>{asset.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Platform Mode: Show Stream Control Panel */}
          {dataSource === 'platform' && (
            <div>
              <label
                className="block text-sm font-medium mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >
                Stream Controls
              </label>
              <div
                className="glass border rounded-lg p-4 space-y-3"
                style={{ borderColor: 'var(--card-border)' }}
              >
                {/* Stream State Display */}
                {streamState === STREAM_STATES.IDLE && (
                  <div className="flex items-center gap-2 text-yellow-400">
                    <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                    <span className="text-sm">Waiting for Chrome connection...</span>
                  </div>
                )}

                {streamState === STREAM_STATES.READY && (
                  <button
                    onClick={handleDetectAsset}
                    className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
                    style={{
                      backgroundColor: 'var(--accent-purple)',
                      color: 'var(--text-primary)'
                    }}
                    onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-blue)'}
                    onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-purple)'}
                  >
                    Detect Asset from PocketOption
                  </button>
                )}

                {streamState === STREAM_STATES.DETECTING && (
                  <div className="flex items-center justify-center gap-2 text-blue-400">
                    <div className="w-4 h-4 border-2 border-blue-400 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm">Detecting asset...</span>
                  </div>
                )}

                {streamState === STREAM_STATES.ASSET_DETECTED && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-green-400">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path>
                      </svg>
                      <span className="text-sm font-medium">Detected: {detectedAsset}</span>
                    </div>
                    <button
                      onClick={handleStartStream}
                      className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
                      style={{
                        backgroundColor: 'var(--accent-green)',
                        color: 'var(--text-primary)'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-blue)'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-green)'}
                    >
                      Start Stream
                    </button>
                  </div>
                )}

                {streamState === STREAM_STATES.STREAMING && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-green-400">
                      <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                      <span className="text-sm font-medium">Streaming: {detectedAsset}</span>
                    </div>
                    <button
                      onClick={handleStopStream}
                      className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
                      style={{
                        backgroundColor: 'var(--accent-red)',
                        color: 'var(--text-primary)'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-purple)'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-red)'}
                    >
                      Stop Stream
                    </button>
                  </div>
                )}

                {streamState === STREAM_STATES.ERROR && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-red-400">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"></path>
                      </svg>
                      <span className="text-sm">{streamError}</span>
                    </div>
                    <button
                      onClick={handleDetectAsset}
                      className="w-full px-4 py-2 rounded-lg font-medium transition-colors"
                      style={{
                        backgroundColor: 'var(--accent-purple)',
                        color: 'var(--text-primary)'
                      }}
                      onMouseEnter={(e) => e.target.style.backgroundColor = 'var(--accent-blue)'}
                      onMouseLeave={(e) => e.target.style.backgroundColor = 'var(--accent-purple)'}
                    >
                      Retry Detection
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {dataSource === 'csv' && (
              <button
                onClick={loadHistoricalData}
                disabled={loading}
                className="px-6 py-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
                style={{
                  backgroundColor: loading ? 'var(--card-border)' : 'var(--accent-blue)',
                  color: 'var(--text-primary)'
                }}
                onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = 'var(--accent-purple)')}
                onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = 'var(--accent-blue)')}
              >
                {loading ? 'Loading...' : 'Load CSV Data'}
              </button>
            )}
          </div>
          
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: isConnected ? 'var(--accent-green)' : isConnecting ? 'var(--accent-orange)' : 'var(--accent-red)'
                }}
              ></div>
              <span
                className="text-xs"
                style={{ color: 'var(--text-muted)' }}
              >Backend: {isConnected ? 'Connected' : isConnecting ? 'Connecting...' : 'Disconnected'}</span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-2 h-2 rounded-full"
                style={{
                  backgroundColor: chromeConnected ? 'var(--accent-green)' : 'var(--accent-orange)'
                }}
              ></div>
              <span
                className="text-xs"
                style={{ color: 'var(--text-muted)' }}
              >Chrome: {chromeConnected ? 'Connected' : 'Not Connected'}</span>
            </div>
            {backendReconnected && (
              <div className="flex items-center gap-1 px-2 py-1 bg-blue-500/20 border border-blue-500/50 rounded-md">
                <svg className="w-3 h-3 text-blue-400 animate-spin" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span className="text-xs text-blue-400 font-medium">Backend Reconnected</span>
              </div>
            )}
            {chromeReconnected && (
              <div className="flex items-center gap-1 px-2 py-1 bg-green-500/20 border border-green-500/50 rounded-md">
                <svg className="w-3 h-3 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"></path>
                </svg>
                <span className="text-xs text-green-400 font-medium">Chrome Reconnected</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${isLiveMode ? 'animate-pulse' : ''}`}
              style={{
                backgroundColor: isLiveMode ? 'var(--accent-green)' : 'var(--card-border)'
              }}
            />
            <span
              className="text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              {isLiveMode ? 'Live' : 'Historical'}
            </span>
          </div>
        </div>
      </div>

      {/* Statistics Panel - CSV Mode Only */}
      {statistics && dataSource === 'csv' && (
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
      )}

      <div
        className="glass rounded-xl p-6"
        style={{ borderColor: 'var(--card-border)' }}
      >
        <div className="flex items-center justify-between mb-4">
          <h3
            className="text-xl font-semibold"
            style={{ color: 'var(--text-primary)' }}
          >Chart</h3>
          <span
            className="text-xs px-2 py-1 rounded-full border"
            style={{
              backgroundColor: isLiveMode ? 'var(--accent-green)' : 'var(--card-bg)',
              color: isLiveMode ? 'var(--text-primary)' : 'var(--text-secondary)',
              borderColor: isLiveMode ? 'var(--accent-green)' : 'var(--card-border)'
            }}
          >
            {isLiveMode
              ? `Streaming • ${dataSource === 'platform' ? (streamAsset || selectedAsset || '') : (selectedAsset || '')}`
              : `Historical • ${selectedAsset || ''}`}
          </span>
        </div>
        {loading && !isLiveMode ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-center">
              <div
                className="mb-2"
                style={{ color: 'var(--text-secondary)' }}
              >{loadingStatus}</div>
              <div
                className="w-12 h-12 border-4 rounded-full animate-spin mx-auto"
                style={{
                  borderColor: 'var(--card-border)',
                  borderTopColor: 'var(--accent-blue)'
                }}
              ></div>
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
