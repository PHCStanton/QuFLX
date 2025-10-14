import React, { useEffect, useRef, useCallback, useState } from 'react';
import { useWebSocket } from '../../hooks/useWebSocket';

// Import components
import DataSourceSelector from './components/DataSourceSelector';
import CSVModeController from './components/CSVModeController';
import PlatformModeController from './components/PlatformModeController';
import ConnectionStatus from './components/ConnectionStatus';
import StatisticsPanel from './components/StatisticsPanel';
import IndicatorsPanel from './components/IndicatorsPanel';
import OptimizedTradingChart from './components/OptimizedTradingChart';

// Import hooks
import { useStreamingState } from './hooks/useStreamingState';
import { useCSVData } from './hooks/useCSVData';
import { usePlatformStreaming } from './hooks/usePlatformStreaming';

const DataAnalysisContainer = () => {
  // WebSocket connection (MUST be first - provides chromeStatus)
  const {
    isConnected,
    isConnecting,
    lastMessage,
    chromeStatus,
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
    detectAsset: wsDetectAsset,
    calculateIndicators,
    storeCsvCandles,
    setReconnectionCallback
  } = useWebSocket();

  // State management
  const {
    streamingState,
    chartConfig,
    uiState,
    setMode,
    setAsset,
    setStatus,
    setTimeframe,
    setLiveMode,
    setLoading,
    setStatistics
  } = useStreamingState();

  // CSV data management
  const {
    availableAssets,
    selectedAsset,
    setSelectedAsset,
    loadAvailableAssets,
    loadCSVData
  } = useCSVData();

  // Platform streaming management (depends on chromeStatus from useWebSocket)
  const {
    streamState,
    detectedAsset,
    streamError,
    isDetecting,
    handleDetectAsset,
    handleAssetDetected,
    handleDetectionError,
    handleStartStream,
    handleStopStream,
    reset: resetPlatformState
  } = usePlatformStreaming(chromeStatus === 'connected');

  // Chart reference for direct updates
  const chartRef = useRef(null);
  
  // Store current chart data (for initial load and updates)
  const [currentChartData, setCurrentChartData] = useState([]);

  // Handle data source changes
  const handleDataSourceChange = useCallback((newDataSource) => {
    setMode(newDataSource);
    setCurrentChartData([]); // Clear chart data
  }, [setMode]);

  // Handle timeframe changes
  const handleTimeframeChange = useCallback((newTimeframe) => {
    setTimeframe(newTimeframe);
    if (streamingState.mode === 'csv') {
      loadAvailableAssets(newTimeframe);
    }
  }, [setTimeframe, streamingState.mode, loadAvailableAssets]);

  // Load CSV data
  const handleLoadCSVData = useCallback(async () => {
    if (!selectedAsset) return;

    setLoading(true, 'Fetching CSV file...');
    try {
      const data = await loadCSVData(selectedAsset, chartConfig.timeframe);
      console.log('[DataAnalysisContainer] Loaded CSV data:', data?.length, 'points');
      
      if (data && data.length > 0) {
        // Store CSV candles in backend for indicators
        storeCsvCandles(selectedAsset, data);
        
        // Update chart data state (will trigger re-render)
        console.log('[DataAnalysisContainer] Setting chart data to state');
        setCurrentChartData(data);
        setLiveMode(false);

        // Calculate statistics
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
    } catch (error) {
      console.error('[DataAnalysisContainer] Error loading CSV data:', error);
      alert(`Failed to load data: ${error.message || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  }, [selectedAsset, chartConfig.timeframe, loadCSVData, setLoading, setLiveMode, setStatistics, storeCsvCandles]);

  // Handle indicator calculation
  const handleCalculateIndicators = useCallback(() => {
    const asset = streamingState.mode === 'platform' ? detectedAsset : selectedAsset;
    if (asset) {
      console.log('[Indicators] Requesting indicators for:', asset);
      calculateIndicators(asset);
    } else {
      alert('No asset selected. Please select an asset or start streaming first.');
    }
  }, [streamingState.mode, selectedAsset, detectedAsset, calculateIndicators]);

  // Handle platform streaming events
  const handlePlatformDetectAsset = useCallback(() => {
    handleDetectAsset();
    wsDetectAsset();
  }, [handleDetectAsset, wsDetectAsset]);

  const handlePlatformStartStream = useCallback(() => {
    handleStartStream();
    startStream(detectedAsset);
    setLiveMode(true);
    setCurrentChartData([]); // Clear chart for streaming
  }, [handleStartStream, startStream, detectedAsset, setLiveMode]);

  const handlePlatformStopStream = useCallback(() => {
    handleStopStream();
    stopStream();
    setLiveMode(false);
  }, [handleStopStream, stopStream, setLiveMode]);

  // Setup reconnection callback
  useEffect(() => {
    const handleReconnection = () => {
      console.log('[Reconnection] Clearing chart data and resetting state...');

      // Clear chart data
      setCurrentChartData([]);

      // Reset states
      setLiveMode(false);
      resetPlatformState();
      setStatistics(null);
    };

    setReconnectionCallback(handleReconnection);
  }, [setReconnectionCallback, setLiveMode, resetPlatformState, setStatistics]);

  // Load available assets when timeframe changes
  useEffect(() => {
    if (streamingState.mode === 'csv') {
      loadAvailableAssets(chartConfig.timeframe);
    }
  }, [streamingState.mode, chartConfig.timeframe, loadAvailableAssets]);

  // Auto-load CSV data when asset changes
  useEffect(() => {
    if (streamingState.mode === 'csv' && selectedAsset) {
      handleLoadCSVData();
    }
  }, [streamingState.mode, selectedAsset, handleLoadCSVData]);

  // Handle WebSocket detection events
  useEffect(() => {
    if (wsDetectedAsset && streamState === 'detecting') {
      handleAssetDetected(wsDetectedAsset);
    } else if (wsDetectionError && streamState === 'detecting') {
      handleDetectionError(wsDetectionError);
    }
  }, [wsDetectedAsset, wsDetectionError, streamState, handleAssetDetected, handleDetectionError]);

  // Handle historical candles (for seeding chart)
  useEffect(() => {
    if (historicalCandles?.candles) {
      console.log(`[HistoricalData] Seeding chart with ${historicalCandles.count} candles`);
      const formattedCandles = historicalCandles.candles.map(candle => ({
        timestamp: candle.timestamp,
        date: new Date(candle.date || candle.timestamp * 1000),
        open: candle.open,
        high: candle.high,
        low: candle.low,
        close: candle.close,
        volume: candle.volume || 0,
        symbol: candle.asset
      }));

      setCurrentChartData(formattedCandles);
      setLiveMode(true);
    }
  }, [historicalCandles, setLiveMode]);

  // Handle real-time candle updates
  useEffect(() => {
    if (chartConfig.isLiveMode && lastMessage && chartRef.current?.updateCandle) {
      chartRef.current.updateCandle(lastMessage);
    }
  }, [chartConfig.isLiveMode, lastMessage]);


  return (
    <div className="space-y-6">
      {/* Data Source Configuration */}
      <div
        className="glass rounded-xl p-6"
        style={{ borderColor: 'var(--card-border)' }}
      >
        <h2
          className="text-2xl font-bold mb-6"
          style={{ color: 'var(--text-primary)' }}
        >
          Data Source Configuration
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <DataSourceSelector
            dataSource={streamingState.mode}
            setDataSource={handleDataSourceChange}
            timeframe={chartConfig.timeframe}
            setTimeframe={handleTimeframeChange}
            isLiveMode={chartConfig.isLiveMode}
          />

          {streamingState.mode === 'csv' && (
            <CSVModeController
              selectedAsset={selectedAsset}
              setSelectedAsset={setSelectedAsset}
              availableAssets={availableAssets}
              loading={uiState.loading}
              loadHistoricalData={handleLoadCSVData}
            />
          )}

          {streamingState.mode === 'platform' && (
            <PlatformModeController
              streamState={streamState}
              streamError={streamError}
              detectedAsset={detectedAsset}
              chromeConnected={chromeStatus === 'connected'}
              handleDetectAsset={handlePlatformDetectAsset}
              handleStartStream={handlePlatformStartStream}
              handleStopStream={handlePlatformStopStream}
              isDetecting={isDetecting}
            />
          )}
        </div>

        <div className="mt-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Additional controls can go here */}
          </div>

          <ConnectionStatus
            isConnected={isConnected}
            isConnecting={isConnecting}
            chromeConnected={chromeStatus === 'connected'}
            backendReconnected={backendReconnected}
            chromeReconnected={chromeReconnected}
          />

          <div className="flex items-center gap-2">
            <div
              className={`w-3 h-3 rounded-full ${chartConfig.isLiveMode ? 'animate-pulse' : ''}`}
              style={{
                backgroundColor: chartConfig.isLiveMode ? 'var(--accent-green)' : 'var(--card-border)'
              }}
            />
            <span
              className="text-sm"
              style={{ color: 'var(--text-secondary)' }}
            >
              {chartConfig.isLiveMode ? 'Live' : 'Historical'}
            </span>
          </div>
        </div>
      </div>

      {/* Statistics Panel - CSV Mode Only */}
      {uiState.statistics && streamingState.mode === 'csv' && (
        <StatisticsPanel statistics={uiState.statistics} />
      )}

      {/* Technical Indicators Panel */}
      <IndicatorsPanel
        indicatorData={indicatorData}
        indicatorError={indicatorError}
        isCalculatingIndicators={isCalculatingIndicators}
        handleCalculateIndicators={handleCalculateIndicators}
        selectedAsset={selectedAsset}
        streamAsset={detectedAsset}
        detectedAsset={detectedAsset}
        dataSource={streamingState.mode}
      />

      {/* Optimized Trading Chart */}
      <OptimizedTradingChart
        ref={chartRef}
        data={currentChartData}
        isLiveMode={chartConfig.isLiveMode}
        height={500}
        backendIndicators={indicatorData}
      />
    </div>
  );
};

export default DataAnalysisContainer;