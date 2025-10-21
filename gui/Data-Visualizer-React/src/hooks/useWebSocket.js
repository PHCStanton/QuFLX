import { useCallback } from 'react';
import { useConnection } from './useConnection';
import { useStreamControl } from './useStreamControl';
import { useDataStream } from './useDataStream';
import { useIndicators } from './useIndicators';

/**
 * Main WebSocket hook that composes specialized hooks for different concerns
 * Provides a unified interface while maintaining separation of concerns
 */
export const useWebSocket = (url) => {
  // Core WebSocket connection
  const { socket, state: connectionState } = useConnection(url);

  // Stream control and asset detection
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

  // Indicator management
  const {
    indicatorData,
    indicatorError,
    isCalculatingIndicators,
    calculateIndicators
  } = useIndicators({
    asset: stream.asset,
    isConnected: connectionState.isConnected,
    socket
  });

  // Reconnection callback management
  const setReconnectionCallback = useCallback((callback) => {
    if (socket) {
      socket.once('reconnect', () => {
        console.log('[Reconnection] Executing reconnection callback');
        callback();
      });
    }
  }, [socket]);

  return {
    // Connection state
    connection: {
      isConnected: connectionState.isConnected,
      isConnecting: connectionState.isConnecting,
      error: connectionState.error,
      chromeStatus: connectionState.chromeStatus,
    },

    // Stream state
    stream: {
      streamActive: stream.active,
      streamAsset: stream.asset,
      backendReconnected: stream.backendReconnected,
      chromeReconnected: stream.chromeReconnected,
    },

    // Asset detection
    assetDetection: {
      detectedAsset: assetDetection.detectedAsset,
      detectionError: assetDetection.detectionError,
      isDetecting: assetDetection.isDetecting,
    },

    // Data state
    data: {
      lastMessage: streamData.lastMessage,
      historicalCandles: streamData.historicalCandles,
      chartData: streamData.chartData,
      indicatorData,
      indicatorError,
      isCalculatingIndicators,
    },

    // Actions
    actions: {
      ...streamActions,
      ...dataActions,
      calculateIndicators,
      setReconnectionCallback,
    },
  };
};
