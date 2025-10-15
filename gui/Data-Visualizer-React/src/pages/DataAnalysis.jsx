import React, { useState, useEffect, useCallback, useRef } from 'react';
import MultiPaneChart from '../components/charts/MultiPaneChart';
import IndicatorManager from '../components/indicators/IndicatorManager';
import { fetchCurrencyPairs } from '../utils/fileUtils';
import { parseTradingData } from '../utils/tradingData';
import { useWebSocket } from '../hooks/useWebSocket';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

const STREAM_STATES = {
  IDLE: 'idle',
  READY: 'ready',
  DETECTING: 'detecting',
  ASSET_DETECTED: 'asset_detected',
  STREAMING: 'streaming',
  ERROR: 'error'
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
  
  const [streamState, setStreamState] = useState(STREAM_STATES.IDLE);
  const [streamError, setStreamError] = useState(null);
  const [detectedAsset, setDetectedAsset] = useState(null);
  
  const [activeIndicators, setActiveIndicators] = useState({
    'SMA-20': { 
      type: 'sma', 
      params: { period: 20 },
      color: '#22c55e',
      definition: { name: 'Simple Moving Average (SMA)', renderType: 'line' }
    },
    'RSI-14': { 
      type: 'rsi', 
      params: { period: 14 },
      color: '#f59e0b',
      definition: { name: 'Relative Strength Index (RSI)', renderType: 'line' }
    },
    'BB-20': { 
      type: 'bollinger', 
      params: { period: 20, std_dev: 2 },
      color: '#6366f1',
      definition: { name: 'Bollinger Bands', renderType: 'band' }
    }
  });
  
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
    historicalCandles,
    indicatorData,
    indicatorError,
    isCalculatingIndicators,
    startStream, 
    stopStream, 
    changeAsset,
    detectAsset: wsDetectAsset,
    calculateIndicators,
    storeCsvCandles,
    setReconnectionCallback 
  } = useWebSocket();

  const candleBufferRef = useRef([]);
  const processingRef = useRef(false);
  const processTimerRef = useRef(null);
  const MAX_BUFFER_SIZE = 1000;

  const chromeConnected = chromeStatus === 'connected';
  
  const dataSources = [
    { id: 'csv', name: 'CSV' },
    { id: 'platform', name: 'Platform' },
  ];

  const timeframes = ['1m', '5m', '15m', '1h', '4h'];

  const platformAssets = [
    { id: 'EURUSD_OTC', name: 'EUR/USD OTC', file: null },
    { id: 'GBPUSD_OTC', name: 'GBP/USD OTC', file: null },
    { id: 'USDJPY_OTC', name: 'USD/JPY OTC', file: null },
    { id: 'AUDUSD_OTC', name: 'AUD/USD OTC', file: null },
  ];

  const loadAvailableAssets = useCallback(async () => {
    if (dataSource === 'csv') {
      const pairs = await fetchCurrencyPairs(timeframe);
      setAvailableAssets(pairs);
      
      const isValidAsset = pairs.some(p => p.id === selectedAsset);
      if (!isValidAsset && pairs.length > 0) {
        setSelectedAsset(pairs[0].id);
      }
    } else if (dataSource === 'platform') {
      setAvailableAssets([]);
      setSelectedAsset('');
    }
  }, [dataSource, timeframe, selectedAsset]);

  useEffect(() => {
    loadAvailableAssets();
  }, [dataSource, timeframe]);

  useEffect(() => {
    if (dataSource === 'csv' && selectedAsset && timeframe) {
      loadCsvData(selectedAsset, timeframe);
    }
  }, [selectedAsset, timeframe, dataSource]);

  const loadCsvData = async (assetId, tf) => {
    if (!assetId) return;
    
    setLoading(true);
    setLoadingStatus(`Loading ${assetId} (${tf})...`);
    setIsLiveMode(false);
    
    try {
      const response = await fetch(`http://localhost:3001/api/csv/${assetId}?timeframe=${tf}`);
      if (!response.ok) throw new Error('Failed to load CSV data');
      
      const rawData = await response.json();
      const parsedData = parseTradingData(rawData);
      setChartData(parsedData);
      
      const config = Object.entries(activeIndicators).reduce((acc, [id, ind]) => {
        acc[ind.type] = ind.params;
        return acc;
      }, {});
      
      await storeCsvCandles(parsedData, assetId);
      await calculateIndicators(assetId, config);
      
      setLoadingStatus('Data loaded successfully');
      setTimeout(() => setLoadingStatus(''), 2000);
    } catch (err) {
      console.error('[CSV] Load error:', err);
      setLoadingStatus(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (dataSource === 'platform') {
      if (chromeConnected) {
        setStreamState(STREAM_STATES.READY);
        setStreamError(null);
      } else {
        setStreamState(STREAM_STATES.IDLE);
      }
    }
  }, [dataSource, chromeConnected]);

  useEffect(() => {
    if (wsDetectedAsset) {
      setDetectedAsset(wsDetectedAsset);
      setStreamState(STREAM_STATES.ASSET_DETECTED);
    }
  }, [wsDetectedAsset]);

  useEffect(() => {
    if (wsDetectionError) {
      setStreamError(wsDetectionError);
      setStreamState(STREAM_STATES.ERROR);
    }
  }, [wsDetectionError]);

  useEffect(() => {
    if (streamActive && streamAsset) {
      setStreamState(STREAM_STATES.STREAMING);
      setIsLiveMode(true);
    } else if (dataSource === 'platform' && !streamActive) {
      setIsLiveMode(false);
    }
  }, [streamActive, streamAsset, dataSource]);

  useEffect(() => {
    if (lastMessage?.type === 'candle_update' && isLiveMode) {
      const candle = lastMessage.data;
      candleBufferRef.current.push(candle);
      
      if (candleBufferRef.current.length > MAX_BUFFER_SIZE) {
        candleBufferRef.current = candleBufferRef.current.slice(-MAX_BUFFER_SIZE);
      }
      
      if (!processTimerRef.current) {
        processTimerRef.current = setTimeout(processBufferedCandles, 100);
      }
    }
  }, [lastMessage, isLiveMode]);

  const processBufferedCandles = useCallback(() => {
    if (processingRef.current || candleBufferRef.current.length === 0) {
      processTimerRef.current = null;
      return;
    }
    
    processingRef.current = true;
    const candles = [...candleBufferRef.current];
    candleBufferRef.current = [];
    
    setChartData(prevData => {
      const newData = [...prevData];
      candles.forEach(candle => {
        const existingIndex = newData.findIndex(c => c.time === candle.time);
        if (existingIndex >= 0) {
          newData[existingIndex] = candle;
        } else {
          newData.push(candle);
        }
      });
      return newData.sort((a, b) => a.time - b.time);
    });
    
    processingRef.current = false;
    processTimerRef.current = null;
  }, []);

  useEffect(() => {
    return () => {
      if (processTimerRef.current) {
        clearTimeout(processTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    if (historicalCandles && historicalCandles.length > 0) {
      const parsedData = parseTradingData(historicalCandles);
      setChartData(parsedData);
    }
  }, [historicalCandles]);

  const handleDetectAsset = () => {
    setStreamState(STREAM_STATES.DETECTING);
    setStreamError(null);
    setDetectedAsset(null);
    wsDetectAsset();
  };

  const handleStartStream = () => {
    if (detectedAsset) {
      setChartData([]);
      startStream(detectedAsset.asset);
      
      const config = Object.entries(activeIndicators).reduce((acc, [id, ind]) => {
        acc[ind.type] = ind.params;
        return acc;
      }, {});
      
      setTimeout(() => {
        calculateIndicators(detectedAsset.asset, config);
      }, 2000);
    }
  };

  const handleStopStream = () => {
    stopStream();
    setStreamState(STREAM_STATES.READY);
    setDetectedAsset(null);
  };

  const handleIndicatorUpdate = async (indicators) => {
    setActiveIndicators(indicators);
    
    const config = Object.entries(indicators).reduce((acc, [id, ind]) => {
      acc[ind.type] = ind.params;
      return acc;
    }, {});
    
    if (dataSource === 'csv' && selectedAsset) {
      await calculateIndicators(selectedAsset, config);
    } else if (dataSource === 'platform' && streamAsset) {
      await calculateIndicators(streamAsset, config);
    }
  };

  const getLatestPrice = () => {
    if (chartData.length === 0) return null;
    return chartData[chartData.length - 1].close;
  };

  const getPriceChange = () => {
    if (chartData.length < 2) return null;
    const first = chartData[0].close;
    const last = chartData[chartData.length - 1].close;
    return (((last - first) / first) * 100).toFixed(2);
  };

  const getVolume = () => {
    if (chartData.length === 0) return null;
    const totalVolume = chartData.reduce((sum, candle) => sum + (candle.volume || 0), 0);
    return (totalVolume / chartData.length).toFixed(0);
  };

  const getIndicatorReading = (type) => {
    if (!indicatorData || !indicatorData.indicators) return null;
    
    const ind = indicatorData.indicators[type];
    if (!ind) return null;
    
    if (type === 'rsi') {
      return { value: ind.value?.toFixed(0), signal: ind.signal };
    } else if (type === 'macd') {
      return { value: ind.signal, signal: ind.signal };
    } else if (type === 'bollinger') {
      return { value: ind.signal, signal: ind.signal };
    }
    return null;
  };

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
  };

  const getResponsiveColumns = () => {
    if (typeof window === 'undefined') return '20% 65% 15%';
    const width = window.innerWidth;
    if (width >= 1280) return '20% 65% 15%';
    if (width >= 1024) return '22% 60% 18%';
    return '20% 65% 15%';
  };

  const [gridColumns, setGridColumns] = useState(getResponsiveColumns());

  useEffect(() => {
    const handleResize = () => setGridColumns(getResponsiveColumns());
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const containerStyle = {
    display: 'grid',
    gridTemplateColumns: gridColumns,
    gap: spacing.lg,
    padding: spacing.lg,
    minHeight: 'calc(100vh - 120px)',
  };

  return (
    <div style={containerStyle}>
      {/* LEFT COLUMN - Controls */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        {/* Data Source Toggle */}
        <div style={cardStyle}>
          <h3 style={{
            margin: 0,
            marginBottom: spacing.md,
            fontSize: typography.fontSize.lg,
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary
          }}>
            Data Source
          </h3>
          <div style={{ display: 'flex', gap: spacing.sm }}>
            {dataSources.map(source => (
              <button
                key={source.id}
                onClick={() => setDataSource(source.id)}
                style={{
                  flex: 1,
                  padding: `${spacing.sm} ${spacing.md}`,
                  background: dataSource === source.id ? colors.accentGreen : colors.bgSecondary,
                  border: 'none',
                  borderRadius: borderRadius.lg,
                  fontSize: typography.fontSize.sm,
                  fontWeight: typography.fontWeight.semibold,
                  color: dataSource === source.id ? '#000' : colors.textPrimary,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {source.name}
              </button>
            ))}
          </div>
        </div>

        {/* Asset Selector (CSV only) */}
        {dataSource === 'csv' && (
          <div style={cardStyle}>
            <h3 style={{
              margin: 0,
              marginBottom: spacing.md,
              fontSize: typography.fontSize.lg,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>
              Asset Selector
            </h3>
            <select
              value={selectedAsset}
              onChange={(e) => setSelectedAsset(e.target.value)}
              style={{
                width: '100%',
                padding: spacing.md,
                background: colors.bgSecondary,
                border: `1px solid ${colors.cardBorder}`,
                borderRadius: borderRadius.lg,
                fontSize: typography.fontSize.base,
                color: colors.textPrimary,
                cursor: 'pointer'
              }}
            >
              <option value="">Select Asset</option>
              {availableAssets.map(asset => (
                <option key={asset.id} value={asset.id}>{asset.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Platform Mode Controls */}
        {dataSource === 'platform' && (
          <div style={cardStyle}>
            <h3 style={{
              margin: 0,
              marginBottom: spacing.md,
              fontSize: typography.fontSize.lg,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>
              Platform Mode
            </h3>
            
            {streamState === STREAM_STATES.IDLE && (
              <div style={{
                padding: spacing.md,
                background: colors.accentRed,
                borderRadius: borderRadius.lg,
                fontSize: typography.fontSize.sm,
                color: '#000',
                fontWeight: typography.fontWeight.semibold,
                textAlign: 'center'
              }}>
                Chrome not connected
              </div>
            )}
            
            {streamState === STREAM_STATES.READY && (
              <button
                onClick={handleDetectAsset}
                style={{
                  width: '100%',
                  padding: spacing.md,
                  background: colors.accentGreen,
                  border: 'none',
                  borderRadius: borderRadius.lg,
                  fontSize: typography.fontSize.base,
                  fontWeight: typography.fontWeight.bold,
                  color: '#000',
                  cursor: 'pointer'
                }}
              >
                Detect Asset
              </button>
            )}
            
            {streamState === STREAM_STATES.DETECTING && (
              <div style={{
                padding: spacing.md,
                background: colors.accentBlue,
                borderRadius: borderRadius.lg,
                fontSize: typography.fontSize.sm,
                color: '#000',
                fontWeight: typography.fontWeight.semibold,
                textAlign: 'center'
              }}>
                Detecting...
              </div>
            )}
            
            {streamState === STREAM_STATES.ASSET_DETECTED && detectedAsset && (
              <div>
                <div style={{
                  padding: spacing.md,
                  background: colors.bgSecondary,
                  borderRadius: borderRadius.lg,
                  marginBottom: spacing.sm,
                  fontSize: typography.fontSize.sm,
                  color: colors.textPrimary
                }}>
                  Detected: {detectedAsset.asset}
                </div>
                <button
                  onClick={handleStartStream}
                  style={{
                    width: '100%',
                    padding: spacing.md,
                    background: colors.accentGreen,
                    border: 'none',
                    borderRadius: borderRadius.lg,
                    fontSize: typography.fontSize.base,
                    fontWeight: typography.fontWeight.bold,
                    color: '#000',
                    cursor: 'pointer'
                  }}
                >
                  Start Stream
                </button>
              </div>
            )}
            
            {streamState === STREAM_STATES.STREAMING && (
              <button
                onClick={handleStopStream}
                style={{
                  width: '100%',
                  padding: spacing.md,
                  background: colors.accentRed,
                  border: 'none',
                  borderRadius: borderRadius.lg,
                  fontSize: typography.fontSize.base,
                  fontWeight: typography.fontWeight.bold,
                  color: '#000',
                  cursor: 'pointer'
                }}
              >
                Stop Stream
              </button>
            )}
          </div>
        )}

        {/* Timeframe Selector */}
        <div style={cardStyle}>
          <h3 style={{
            margin: 0,
            marginBottom: spacing.md,
            fontSize: typography.fontSize.lg,
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary
          }}>
            Timeframe
          </h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.sm }}>
            {timeframes.map(tf => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                style={{
                  padding: `${spacing.sm} ${spacing.md}`,
                  background: timeframe === tf ? colors.accentGreen : colors.bgSecondary,
                  border: 'none',
                  borderRadius: borderRadius.lg,
                  fontSize: typography.fontSize.sm,
                  fontWeight: typography.fontWeight.semibold,
                  color: timeframe === tf ? '#000' : colors.textPrimary,
                  cursor: 'pointer',
                  transition: 'all 0.2s'
                }}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        {/* Indicator Manager */}
        <div style={cardStyle}>
          <h3 style={{
            margin: 0,
            marginBottom: spacing.md,
            fontSize: typography.fontSize.lg,
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary
          }}>
            Indicators
          </h3>
          
          <IndicatorManager 
            indicators={activeIndicators}
            onChange={handleIndicatorUpdate}
          />
        </div>
      </div>

      {/* CENTER COLUMN - Chart */}
      <div style={{ ...cardStyle, display: 'flex', flexDirection: 'column' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: spacing.lg
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: spacing.md
          }}>
            <div style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: isLiveMode ? colors.accentGreen : colors.textSecondary
            }}></div>
            <h2 style={{
              margin: 0,
              fontSize: typography.fontSize.xl,
              fontWeight: typography.fontWeight.bold,
              color: colors.textPrimary
            }}>
              {streamAsset || selectedAsset || 'Select Asset'}
            </h2>
          </div>
          <div style={{ display: 'flex', gap: spacing.sm }}>
            {['⚙️', '📤', '⭐', '←', '↓', '↑', '→', '⊙', '⊚'].map((icon, idx) => (
              <div key={idx} style={{
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary,
                cursor: 'pointer'
              }}>
                {icon}
              </div>
            ))}
          </div>
        </div>

        <div style={{ flex: 1, minHeight: '500px' }}>
          {chartData.length > 0 ? (
            <MultiPaneChart 
              data={chartData}
              indicators={activeIndicators}
              indicatorData={indicatorData}
              height={500}
            />
          ) : (
            <div style={{
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: colors.bgPrimary,
              borderRadius: borderRadius.lg,
              color: colors.textSecondary,
              fontSize: typography.fontSize.base
            }}>
              {loading ? loadingStatus : 'Select asset to view chart'}
            </div>
          )}
        </div>
      </div>

      {/* RIGHT COLUMN - Stats & Readings */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        {/* Quick Stats */}
        <div style={cardStyle}>
          <h3 style={{
            margin: 0,
            marginBottom: spacing.lg,
            fontSize: typography.fontSize.lg,
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary
          }}>
            Quick Stats
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary
              }}>
                Latest Price
              </span>
              <span style={{
                fontSize: typography.fontSize.base,
                fontWeight: typography.fontWeight.semibold,
                color: colors.textPrimary
              }}>
                {getLatestPrice()?.toFixed(5) || '--'}
              </span>
            </div>
            
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary
              }}>
                Change %
              </span>
              <span style={{
                fontSize: typography.fontSize.base,
                fontWeight: typography.fontWeight.semibold,
                color: getPriceChange() >= 0 ? colors.accentGreen : colors.accentRed
              }}>
                {getPriceChange() !== null ? `${getPriceChange()}%` : '--'}
              </span>
            </div>
            
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <span style={{
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary
              }}>
                Avg Volume
              </span>
              <span style={{
                fontSize: typography.fontSize.base,
                fontWeight: typography.fontWeight.semibold,
                color: colors.textPrimary
              }}>
                {getVolume() || '--'}
              </span>
            </div>
          </div>
        </div>

        {/* Indicator Readings */}
        <div style={cardStyle}>
          <h3 style={{
            margin: 0,
            marginBottom: spacing.lg,
            fontSize: typography.fontSize.lg,
            fontWeight: typography.fontWeight.semibold,
            color: colors.textPrimary
          }}>
            Indicator Readings
          </h3>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
            {['rsi', 'macd', 'bollinger'].map(type => {
              const reading = getIndicatorReading(type);
              const signalColor = reading?.signal === 'BUY' || reading?.signal === 'CALL' ? colors.accentGreen :
                                  reading?.signal === 'SELL' || reading?.signal === 'PUT' ? colors.accentRed :
                                  colors.textSecondary;
              
              return (
                <div key={type} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: spacing.sm
                  }}>
                    <div style={{
                      width: '8px',
                      height: '8px',
                      borderRadius: '50%',
                      background: signalColor
                    }}></div>
                    <span style={{
                      fontSize: typography.fontSize.sm,
                      color: colors.textPrimary
                    }}>
                      {type.toUpperCase()}: {reading?.value || '--'}
                    </span>
                  </div>
                  <span style={{
                    fontSize: typography.fontSize.sm,
                    color: colors.textSecondary
                  }}>
                    {reading?.signal || '--'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataAnalysis;
