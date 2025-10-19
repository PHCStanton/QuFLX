import { useEffect, useState, useCallback, useRef } from 'react';
import io from 'socket.io-client';
import { detectSocketUrl } from '../utils/urlHelper';

const useWebSocketState = () => {
  const [connectionState, setConnectionState] = useState({
    isConnected: false,
    isConnecting: false,
    error: null,
    chromeStatus: 'not connected'
  });

  const [streamState, setStreamState] = useState({
    active: false,
    asset: null,
    backendReconnected: false,
    chromeReconnected: false
  });

  const [assetState, setAssetState] = useState({
    detectedAsset: null,
    detectionError: null,
    isDetecting: false
  });

  const [dataState, setDataState] = useState({
    lastMessage: null,
    historicalCandles: null,
    indicatorData: null,
    indicatorError: null,
    isCalculatingIndicators: false
  });

  return {
    connectionState,
    setConnectionState,
    streamState,
    setStreamState,
    assetState,
    setAssetState,
    dataState,
    setDataState
  };
};

export const useWebSocket = (url) => {
  const {
    connectionState,
    setConnectionState,
    streamState,
    setStreamState,
    assetState,
    setAssetState,
    dataState,
    setDataState
  } = useWebSocketState();

  const socketRef = useRef(null);
  const reconnectionCallbackRef = useRef(null);

  useEffect(() => {
    // Create socket connection with polling first to avoid initial errors
    const connectUrl = url || detectSocketUrl();
    setConnectionState(prev => ({ ...prev, isConnecting: true }));
    const socket = io(connectUrl, {
      // Prefer WebSocket, but allow polling fallback for Windows/threading backend
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      forceNew: true, // Force a new connection instead of reusing old sessions
      timeout: 10000
    });

    socketRef.current = socket;

    socket.on('connect', () => {
      console.log('WebSocket connected with session:', socket.id);
      setConnectionState(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        error: null
      }));
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setConnectionState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false
      }));
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setConnectionState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: err.message
      }));
    });
    
    socket.on('reconnect_error', (err) => {
      console.error('WebSocket reconnection error:', err);
    });
    
    socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed after all attempts');
      setConnectionState(prev => ({
        ...prev,
        error: 'Failed to reconnect to server',
        isConnecting: false
      }));
    });

    socket.on('reconnect_attempt', () => {
      console.log('Attempting to reconnect...');
      setConnectionState(prev => ({ ...prev, isConnecting: true }));
    });

    socket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected successfully after ${attemptNumber} attempt(s)`);
      setConnectionState(prev => ({ ...prev, isConnecting: false }));
      
      // Trigger reconnection callback if provided
      if (reconnectionCallbackRef.current) {
        console.log('[Reconnection] Executing reconnection callback to clear state and reload data');
        reconnectionCallbackRef.current();
      }
    });

    socket.on('candle_update', (data) => {
      setDataState(prev => ({ ...prev, lastMessage: data }));
    });

    socket.on('stream_started', (data) => {
      console.log('Stream started:', data);
      setStreamState(prev => ({
        ...prev,
        active: true,
        asset: data?.asset || prev.asset
      }));
    });

    socket.on('stream_stopped', (data) => {
      console.log('Stream stopped:', data);
      setStreamState(prev => ({ ...prev, active: false }));
    });

    socket.on('asset_changed', (data) => {
      console.log('Asset changed:', data);
      setStreamState(prev => ({ ...prev, asset: data?.asset || prev.asset }));
    });

    socket.on('connection_status', (data) => {
      console.log('Connection status:', data);
      setConnectionState(prev => ({ ...prev, chromeStatus: data.chrome || 'not connected' }));
    });

    socket.on('backend_reconnected', (data) => {
      console.log('[Reconnection] Backend reconnected:', data);
      setStreamState(prev => ({ ...prev, backendReconnected: true }));

      // Trigger reconnection callback to clear state
      if (reconnectionCallbackRef.current) {
        console.log('[Reconnection] Backend reconnected - clearing state and reloading data');
        reconnectionCallbackRef.current();
      }

      // Reset flag after a short delay
      setTimeout(() => setStreamState(prev => ({ ...prev, backendReconnected: false })), 3000);
    });

    socket.on('chrome_reconnected', (data) => {
      console.log('[Reconnection] Chrome reconnected:', data);
      setStreamState(prev => ({ ...prev, chromeReconnected: true }));

      // Reset flag after a short delay
      setTimeout(() => setStreamState(prev => ({ ...prev, chromeReconnected: false })), 3000);
    });

    socket.on('asset_detected', (data) => {
      console.log('[AssetDetection] Asset detected:', data);
      setAssetState(prev => ({
        ...prev,
        detectedAsset: data.asset,
        detectionError: null,
        isDetecting: false
      }));
    });

    socket.on('asset_detection_failed', (data) => {
      console.error('[AssetDetection] Detection failed:', data);
      setAssetState(prev => ({
        ...prev,
        detectionError: data.error,
        detectedAsset: null,
        isDetecting: false
      }));
    });

    // Stage 1: Listen for historical candles loaded event
    socket.on('historical_candles_loaded', (data) => {
      console.log(`[HistoricalData] Received ${data.count} historical candles for ${data.asset}`);
      setDataState(prev => ({ ...prev, historicalCandles: data }));
    });

    // Stage 2: Listen for indicator calculation results
    socket.on('indicators_calculated', (data) => {
      console.log(`[Indicators] Received full data for ${data.asset}:`, data);
      console.log(`[Indicators] Has series data:`, !!data.series, data.series ? Object.keys(data.series) : 'none');
      setDataState(prev => ({
        ...prev,
        indicatorData: data,
        indicatorError: null,
        isCalculatingIndicators: false
      }));
    });

    socket.on('indicators_error', (data) => {
      console.error('[Indicators] Calculation error:', data.error);
      setDataState(prev => ({
        ...prev,
        indicatorError: data.error,
        indicatorData: null,
        isCalculatingIndicators: false
      }));
    });

    socket.on('csv_storage_success', (data) => {
      console.log(`[CSV Storage] Successfully stored ${data.candle_count} candles for ${data.asset}`);
    });

    socket.on('csv_storage_error', (data) => {
      console.error('[CSV Storage] Storage error:', data.error);
    });

    return () => {
      console.log('Cleaning up WebSocket connection');
      
      // Only cleanup if socket is in a valid state
      if (socket) {
        socket.removeAllListeners();
        
        // Handle cleanup based on connection state to prevent warnings and memory leaks
        const engineState = socket.io?.engine?.readyState;
        
        if (socket.connected || engineState === 'open') {
          // Socket is established - normal disconnect
          socket.disconnect();
        } else if (engineState === 'opening') {
          // Socket is still connecting - abort to prevent zombie connection
          socket.io.engine?.close?.();
        }
      }
    };
  }, [url]);

  const startStream = useCallback((asset) => {
    if (socketRef.current && connectionState.isConnected) {
      socketRef.current.emit('start_stream', { asset });
    }
  }, [connectionState.isConnected]);

  const stopStream = useCallback(() => {
    if (socketRef.current && connectionState.isConnected) {
      socketRef.current.emit('stop_stream');
    }
  }, [connectionState.isConnected]);

  const changeAsset = useCallback((asset) => {
    if (socketRef.current && connectionState.isConnected) {
      socketRef.current.emit('change_asset', { asset });
    }
  }, [connectionState.isConnected]);

  const detectAsset = useCallback(() => {
    if (socketRef.current && connectionState.isConnected) {
      console.log('[AssetDetection] Requesting asset detection...');
      setAssetState(prev => ({ ...prev, isDetecting: true, detectionError: null }));
      socketRef.current.emit('detect_asset');
    } else {
      setAssetState(prev => ({ ...prev, detectionError: 'Not connected to backend', isDetecting: false }));
    }
  }, [connectionState.isConnected]);

  const setReconnectionCallback = useCallback((callback) => {
    reconnectionCallbackRef.current = callback;
  }, []);

  const calculateIndicators = useCallback((asset, indicatorsConfig = null) => {
    // Check actual socket connection state, not just the React state
    const actuallyConnected = socketRef.current && socketRef.current.connected;

    if (actuallyConnected) {
      console.log('[Indicators] Requesting indicator calculation for:', asset);
      setDataState(prev => ({ ...prev, isCalculatingIndicators: true, indicatorError: null }));

      const defaultConfig = {
        sma: { period: 20 },
        rsi: { period: 14 },
        bollinger: { period: 20, std_dev: 2 }
      };

      const config = indicatorsConfig || defaultConfig;

      // Check if config is instance-based (has 'type' and 'params' fields)
      const isInstanceBased = Object.values(config).some(val => val?.type && val?.params);

      if (isInstanceBased) {
        // New instance-based format
        console.log('[Indicators] Using instance-based format with', Object.keys(config).length, 'instances');
        socketRef.current.emit('calculate_indicators', {
          asset,
          instances: config
        });
      } else {
        // Legacy format (backward compatible)
        console.log('[Indicators] Using legacy format');
        socketRef.current.emit('calculate_indicators', {
          asset,
          indicators: config
        });
      }
    } else {
      console.error(`[Indicators] Cannot calculate - socket not connected. Socket exists: ${!!socketRef.current}, Actually connected: ${actuallyConnected}`);
      setDataState(prev => ({ ...prev, indicatorError: 'Not connected to backend', isCalculatingIndicators: false }));
    }
  }, []);

  const storeCsvCandles = useCallback((asset, candles) => {
    // Check actual socket connection state, not just the React state
    const actuallyConnected = socketRef.current && socketRef.current.connected;
    
    if (actuallyConnected) {
      console.log(`[CSV Storage] Storing ${candles.length} candles for ${asset}`);
      socketRef.current.emit('store_csv_candles', {
        asset,
        candles
      });
    } else {
      console.error(`[CSV Storage] Cannot store candles - socket not connected. Socket exists: ${!!socketRef.current}, Actually connected: ${actuallyConnected}`);
    }
  }, []);

  return {
    // Connection state
    isConnected: connectionState.isConnected,
    isConnecting: connectionState.isConnecting,
    error: connectionState.error,
    chromeStatus: connectionState.chromeStatus,

    // Stream state
    streamActive: streamState.active,
    streamAsset: streamState.asset,
    backendReconnected: streamState.backendReconnected,
    chromeReconnected: streamState.chromeReconnected,

    // Asset detection state
    detectedAsset: assetState.detectedAsset,
    detectionError: assetState.detectionError,
    isDetecting: assetState.isDetecting,

    // Data state
    lastMessage: dataState.lastMessage,
    historicalCandles: dataState.historicalCandles,
    indicatorData: dataState.indicatorData,
    indicatorError: dataState.indicatorError,
    isCalculatingIndicators: dataState.isCalculatingIndicators,

    // Socket reference and methods
    socketRef,
    startStream,
    stopStream,
    changeAsset,
    detectAsset,
    calculateIndicators,
    storeCsvCandles,
    setReconnectionCallback
  };
};
