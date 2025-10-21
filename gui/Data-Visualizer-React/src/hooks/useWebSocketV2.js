import { useCallback, useMemo } from 'react';
import { useConnection } from './useConnection';
import { useStreamControl } from './useStreamControl';
import { useDataStream } from './useDataStream';
import { useIndicatorCalculations } from './useIndicatorCalculations';

/**
 * Enhanced WebSocket hook with improved state management and reduced complexity
 * Uses composition pattern for better separation of concerns
 */
export const useWebSocket = (url) => {
  // Core connection management
  const { socket, state: connectionState } = useConnection(url);
  const isConnected = connectionState.isConnected;
  const chromeConnected = connectionState.chromeStatus === 'connected';

  // Stream and asset management
  const {
    stream,
    assetDetection,
    actions: streamActions
  } = useStreamControl(socket);

  // Data streaming and processing
  const {
    data: streamData,
    actions: dataActions
  } = useDataStream(socket, {
    maxBufferSize: 1000,
    processInterval: 100
  });

  // Indicator calculations
  const {
    indicatorData,
    indicatorError,
    isCalculatingIndicators,
    calculateIndicators
  } = useIndicatorCalculations(socket);

  // Memoized state objects to prevent unnecessary re-renders
  const connectionInfo = useMemo(() => ({
    isConnected,
    isConnecting: connectionState.isConnecting,
    error: connectionState.error,
    chromeConnected
  }), [isConnected, connectionState.isConnecting, connectionState.error, chromeConnected]);

  const streamInfo = useMemo(() => ({
    isActive: stream.active,
    currentAsset: stream.asset,
    hasReconnected: stream.backendReconnected || stream.chromeReconnected
  }), [stream]);

  const assetInfo = useMemo(() => ({
    detected: assetDetection.detectedAsset,
    error: assetDetection.detectionError,
    isDetecting: assetDetection.isDetecting
  }), [assetDetection]);

  const dataInfo = useMemo(() => ({
    current: streamData.chartData,
    historical: streamData.historicalCandles,
    lastUpdate: streamData.lastMessage,
    indicators: {
      data: indicatorData,
      error: indicatorError,
      isCalculating: isCalculatingIndicators
    }
  }), [streamData, indicatorData, indicatorError, isCalculatingIndicators]);

  // Unified actions object
  const actions = useMemo(() => ({
    stream: {
      start: streamActions.startStream,
      stop: streamActions.stopStream,
      changeAsset: streamActions.changeAsset,
      detectAsset: streamActions.detectAsset
    },
    data: {
      storeCSV: dataActions.storeCsvCandles,
      calculateIndicators
    }
  }), [streamActions, dataActions, calculateIndicators]);

  // Reconnection handler
  const handleReconnect = useCallback((callback) => {
    if (!socket) return;
    socket.once('reconnect', () => {
      console.log('[Reconnection] Executing callback');
      callback();
    });
  }, [socket]);

  return {
    connection: connectionInfo,
    stream: streamInfo,
    asset: assetInfo,
    data: dataInfo,
    actions,
    onReconnect: handleReconnect
  };
};