import { useEffect, useState, useCallback, useRef } from 'react';
import io from 'socket.io-client';

// Helper to detect the backend Socket.IO server URL
const detectSocketUrl = () => {
  try {
    const protocol = window?.location?.protocol || 'http:';
    const hostname = window?.location?.hostname || 'localhost';
    const defaultUrl = `${protocol}//${hostname}:3001`;
    // Allow override via env variable if provided
    const envUrl = import.meta?.env?.VITE_SOCKET_URL;
    return envUrl || defaultUrl;
  } catch {
    return 'http://localhost:3001';
  }
};

export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const [chromeStatus, setChromeStatus] = useState('not connected');
  const [isConnecting, setIsConnecting] = useState(false);
  const [streamActive, setStreamActive] = useState(false);
  const [streamAsset, setStreamAsset] = useState(null);
  const [backendReconnected, setBackendReconnected] = useState(false);
  const [chromeReconnected, setChromeReconnected] = useState(false);
  const [detectedAsset, setDetectedAsset] = useState(null);
  const [detectionError, setDetectionError] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);
  const [historicalCandles, setHistoricalCandles] = useState(null);
  const [indicatorData, setIndicatorData] = useState(null);
  const [indicatorError, setIndicatorError] = useState(null);
  const [isCalculatingIndicators, setIsCalculatingIndicators] = useState(false);
  const socketRef = useRef(null);
  const reconnectionCallbackRef = useRef(null);

  useEffect(() => {
    // Create socket connection with polling first to avoid initial errors
    const connectUrl = url || detectSocketUrl();
    setIsConnecting(true);
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
      setIsConnected(true);
      setIsConnecting(false);
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
      setIsConnecting(false);
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setError(err.message);
      setIsConnected(false);
      setIsConnecting(false);
    });
    
    socket.on('reconnect_error', (err) => {
      console.error('WebSocket reconnection error:', err);
    });
    
    socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed after all attempts');
      setError('Failed to reconnect to server');
      setIsConnecting(false);
    });

    socket.on('reconnect_attempt', () => {
      console.log('Attempting to reconnect...');
      setIsConnecting(true);
    });

    socket.on('reconnect', (attemptNumber) => {
      console.log(`Reconnected successfully after ${attemptNumber} attempt(s)`);
      setIsConnecting(false);
      
      // Trigger reconnection callback if provided
      if (reconnectionCallbackRef.current) {
        console.log('[Reconnection] Executing reconnection callback to clear state and reload data');
        reconnectionCallbackRef.current();
      }
    });

    socket.on('candle_update', (data) => {
      setLastMessage(data);
    });

    socket.on('stream_started', (data) => {
      console.log('Stream started:', data);
      setStreamActive(true);
      if (data?.asset) setStreamAsset(data.asset);
    });

    socket.on('stream_stopped', (data) => {
      console.log('Stream stopped:', data);
      setStreamActive(false);
    });

    socket.on('asset_changed', (data) => {
      console.log('Asset changed:', data);
      if (data?.asset) setStreamAsset(data.asset);
    });

    socket.on('connection_status', (data) => {
      console.log('Connection status:', data);
      setChromeStatus(data.chrome || 'not connected');
    });

    socket.on('backend_reconnected', (data) => {
      console.log('[Reconnection] Backend reconnected:', data);
      setBackendReconnected(true);
      
      // Trigger reconnection callback to clear state
      if (reconnectionCallbackRef.current) {
        console.log('[Reconnection] Backend reconnected - clearing state and reloading data');
        reconnectionCallbackRef.current();
      }
      
      // Reset flag after a short delay
      setTimeout(() => setBackendReconnected(false), 3000);
    });

    socket.on('chrome_reconnected', (data) => {
      console.log('[Reconnection] Chrome reconnected:', data);
      setChromeReconnected(true);
      
      // Reset flag after a short delay
      setTimeout(() => setChromeReconnected(false), 3000);
    });

    socket.on('asset_detected', (data) => {
      console.log('[AssetDetection] Asset detected:', data);
      setDetectedAsset(data.asset);
      setDetectionError(null);
      setIsDetecting(false);
    });

    socket.on('asset_detection_failed', (data) => {
      console.error('[AssetDetection] Detection failed:', data);
      setDetectionError(data.error);
      setDetectedAsset(null);
      setIsDetecting(false);
    });

    // Stage 1: Listen for historical candles loaded event
    socket.on('historical_candles_loaded', (data) => {
      console.log(`[HistoricalData] Received ${data.count} historical candles for ${data.asset}`);
      setHistoricalCandles(data);
    });

    // Stage 2: Listen for indicator calculation results
    socket.on('indicators_calculated', (data) => {
      console.log(`[Indicators] Received indicators for ${data.asset}:`, data.indicators);
      setIndicatorData(data);
      setIndicatorError(null);
      setIsCalculatingIndicators(false);
    });

    socket.on('indicators_error', (data) => {
      console.error('[Indicators] Calculation error:', data.error);
      setIndicatorError(data.error);
      setIndicatorData(null);
      setIsCalculatingIndicators(false);
    });

    return () => {
      console.log('Cleaning up WebSocket connection');
      socket.removeAllListeners();
      socket.disconnect();
      socket.close();
    };
  }, [url]);

  const startStream = useCallback((asset) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('start_stream', { asset });
    }
  }, [isConnected]);

  const stopStream = useCallback(() => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('stop_stream');
    }
  }, [isConnected]);

  const changeAsset = useCallback((asset) => {
    if (socketRef.current && isConnected) {
      socketRef.current.emit('change_asset', { asset });
    }
  }, [isConnected]);

  const detectAsset = useCallback(() => {
    if (socketRef.current && isConnected) {
      console.log('[AssetDetection] Requesting asset detection...');
      setIsDetecting(true);
      setDetectionError(null);
      socketRef.current.emit('detect_asset');
    } else {
      setDetectionError('Not connected to backend');
      setIsDetecting(false);
    }
  }, [isConnected]);

  const setReconnectionCallback = useCallback((callback) => {
    reconnectionCallbackRef.current = callback;
  }, []);

  const calculateIndicators = useCallback((asset, indicatorsConfig = null) => {
    if (socketRef.current && isConnected) {
      console.log('[Indicators] Requesting indicator calculation for:', asset);
      setIsCalculatingIndicators(true);
      setIndicatorError(null);
      
      const defaultConfig = {
        sma: { period: 20 },
        rsi: { period: 14 },
        bollinger: { period: 20, std_dev: 2 }
      };
      
      socketRef.current.emit('calculate_indicators', {
        asset,
        indicators: indicatorsConfig || defaultConfig
      });
    } else {
      setIndicatorError('Not connected to backend');
      setIsCalculatingIndicators(false);
    }
  }, [isConnected]);

  return {
    isConnected,
    isConnecting,
    lastMessage,
    error,
    chromeStatus,
    streamActive,
    streamAsset,
    backendReconnected,
    chromeReconnected,
    detectedAsset,
    detectionError,
    isDetecting,
    historicalCandles,
    indicatorData,
    indicatorError,
    isCalculatingIndicators,
    // Expose the socketRef so pages can access the raw socket when needed
    socketRef,
    startStream,
    stopStream,
    changeAsset,
    detectAsset,
    calculateIndicators,
    setReconnectionCallback
  };
};
