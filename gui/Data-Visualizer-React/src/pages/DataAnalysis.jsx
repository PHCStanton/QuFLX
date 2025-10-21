import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import DataSourceSelector from '../components/DataSourceSelector';
import AssetSelector from '../components/AssetSelector';
import PlatformModeControls from '../components/PlatformModeControls';
import TimeframeSelector from '../components/TimeframeSelector';
import ChartContainer from '../components/ChartContainer';
import IndicatorPanel from '../components/IndicatorPanel';
import StatsPanel from '../components/StatsPanel';
import { fetchCurrencyPairs } from '../utils/fileUtils';
import { parseTradingData } from '../utils/tradingData';
import { useWebSocket } from '../hooks/useWebSocketV2';
import { useResponsiveGrid } from '../hooks/useResponsiveGrid';
import { useIndicators } from '../hooks/useIndicators';
import { useLiveMode } from '../hooks/useLiveMode';
import { useCsvData } from '../hooks/useCsvData';
import { getCurrentAsset } from '../utils/indicatorUtils';
import { Link } from 'react-router-dom';
import { colors, spacing, typography, borderRadius } from '../styles/designTokens';

const DataAnalysis = () => {
  // Data source state
  const [dataSource, setDataSource] = useState('csv');
  const [timeframe, setTimeframe] = useState('1m');
  const [selectedAsset, setSelectedAsset] = useState('');
  const [selectedAssetFile, setSelectedAssetFile] = useState('');
  const [availableAssets, setAvailableAssets] = useState([]);
  const [chartData, setChartData] = useState([]);
  
  // Stream state
  const [detectedAsset, setDetectedAsset] = useState(null);

  // WebSocket state and actions with improved structure
  const {
    connection,
    stream,
    asset,
    data,
    actions,
    onReconnect
  } = useWebSocket();

  const {
    isConnected,
    chromeConnected
  } = connection;

  const {
    isActive: streamActive,
    currentAsset: streamAsset
  } = stream;

  const {
    detected: wsDetectedAsset
  } = asset;

  const {
    current: wsChartData,
    historical: historicalCandles,
    lastUpdate: lastMessage
  } = data;

  // Safe indicator props (flattened with guards)
  const indData = useMemo(() => data?.indicators?.data ?? null, [data]);
  const indError = useMemo(() => data?.indicators?.error ?? null, [data]);
  const isCalc = useMemo(() => data?.indicators?.isCalculating ?? false, [data]);

  if (process.env.NODE_ENV === 'development' && !indData) {
    console.warn('[DataAnalysis] Indicator data missing');
  }

  // Update chart data when WebSocket data changes
  useEffect(() => {
    if (dataSource === 'platform' && wsChartData?.length > 0) {
      setChartData(wsChartData);
    }
  }, [dataSource, wsChartData]);

  // Indicator management
  // Get indicator calculation and storage functions from the unified actions (avoid calling hooks twice)
  const calculateIndicators = actions?.data?.calculateIndicators ?? null;
  const storeCsvCandles = actions?.data?.storeCSV ?? null;

  // Indicator management with calculation support
  const {
    activeIndicators,
    addIndicator,
    removeIndicator,
    formatIndicatorReading
  } = useIndicators({
    asset: getCurrentAsset(dataSource, selectedAsset, streamAsset),
    isConnected,
    calculateIndicators,
    indicatorData: indData,
    indicatorError: indError,
    isCalculatingIndicators: isCalc
  });


  const gridColumns = useResponsiveGrid();

  // Load available assets
  const loadAvailableAssets = useCallback(async () => {
    if (dataSource === 'csv') {
      const pairs = await fetchCurrencyPairs(timeframe);
      setAvailableAssets(pairs);
      
      const isValidAsset = pairs.some(p => p.id === selectedAsset);
      if (!isValidAsset && pairs.length > 0) {
        setSelectedAsset(pairs[0].id);
        setSelectedAssetFile(pairs[0].file);
      }
    } else if (dataSource === 'platform') {
      setAvailableAssets([]);
      setSelectedAsset('');
    }
  }, [dataSource, timeframe, selectedAsset]);

  useEffect(() => {
    loadAvailableAssets();
  }, [loadAvailableAssets]);

  // CSV data loading
  const {
    data: csvData,
    isLoading: csvLoading,
    error: csvError
  } = useCsvData({
    dataSource,
    selectedAsset,
    selectedAssetFile,
    timeframe,
    isConnected,
    storeCsvCandles
  });

  // Update chart data when CSV data changes
  useEffect(() => {
    if (dataSource === 'csv' && csvData.length > 0) {
      setChartData(csvData);
    }
  }, [dataSource, csvData]);

  // Live mode state management
  const { isLiveMode, canEnterLiveMode, isStreamReady, isStreaming } = useLiveMode({
    dataSource,
    chromeConnected,
    streamActive,
    streamAsset
  });

  // Handle detected asset updates
  useEffect(() => {
    if (wsDetectedAsset) {
      setDetectedAsset(wsDetectedAsset);
    }
  }, [wsDetectedAsset]);





  // Platform mode controls
  // Platform mode controls
  // Platform mode controls with improved action handling
  const handleDetectAsset = useCallback(() => {
    setDetectedAsset(null);
    actions.stream.detectAsset();
  }, [actions.stream]);

  const handleStartStream = useCallback(() => {
    if (detectedAsset) {
      setChartData([]);
      actions.stream.start(detectedAsset.asset);
    }
  }, [detectedAsset, actions.stream]);

  const handleStopStream = useCallback(() => {
    actions.stream.stop();
    setDetectedAsset(null);
  }, [actions.stream]);

  // Stats calculations
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

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: gridColumns,
      gap: spacing.md,
      padding: `${spacing.md} ${spacing.lg}`,
      minHeight: 'calc(100vh - 120px)',
    }}>
      {/* LEFT COLUMN - Controls */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        <DataSourceSelector
          dataSource={dataSource}
          onDataSourceChange={setDataSource}
        />

        {dataSource === 'csv' && (
          <AssetSelector
            selectedAsset={selectedAsset}
            selectedAssetFile={selectedAssetFile}
            availableAssets={availableAssets}
            onAssetChange={(asset, file) => {
              setSelectedAsset(asset);
              setSelectedAssetFile(file);
            }}
          />
        )}

        {dataSource === 'platform' && (
          <PlatformModeControls
            canEnterLiveMode={canEnterLiveMode}
            isStreamReady={isStreamReady}
            isStreaming={isStreaming}
            detectedAsset={detectedAsset}
            onDetectAsset={handleDetectAsset}
            onStartStream={handleStartStream}
            onStopStream={handleStopStream}
          />
        )}

        <TimeframeSelector
          timeframe={timeframe}
          onTimeframeChange={setTimeframe}
        />
      </div>

      {/* CENTER COLUMN - Chart */}
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        {/* Status + Navigation */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: spacing.sm
        }}>
          <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>
            {isConnected ? 'WS Connected' : 'WS Disconnected'} · Chrome: {chromeConnected ? 'Connected' : 'Not Connected'} · Stream: {streamActive ? 'Active' : 'Idle'}{streamAsset ? ` · Asset: ${streamAsset}` : ''}
          </div>
          {streamActive && (
            <Link to="/live" style={{
              padding: `${spacing.xs} ${spacing.sm}`,
              background: colors.accentGreen,
              borderRadius: borderRadius.md,
              color: '#000',
              textDecoration: 'none',
              fontWeight: typography.fontWeight.semibold
            }}>
              Open Live Tab →
            </Link>
          )}
        </div>

        <ChartContainer
          data={chartData}
          indicators={activeIndicators}
          backendIndicators={indData}
          height={600}
          streamActive={streamActive}
          streamAsset={streamAsset}
          selectedAsset={selectedAsset}
        />

        <IndicatorPanel
          indicators={activeIndicators}
          onChange={(indicators) => {
            Object.entries(indicators).forEach(([name, config]) => {
              if (!activeIndicators[name]) {
                addIndicator({ instanceName: name, ...config });
              }
            });
            Object.keys(activeIndicators).forEach(name => {
              if (!indicators[name]) {
                removeIndicator(name);
              }
            });
          }}
        />
      </div>

      {/* RIGHT COLUMN - Stats & Readings */}
      <StatsPanel
        chartData={chartData}
        indicatorData={indData}
        indicatorError={indError}
        getLatestPrice={getLatestPrice}
        getPriceChange={getPriceChange}
        getVolume={getVolume}
        getIndicatorReading={formatIndicatorReading}
      />
    </div>
  );
};

export default DataAnalysis;
