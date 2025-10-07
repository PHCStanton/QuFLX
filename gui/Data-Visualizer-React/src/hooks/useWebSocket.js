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
  const socketRef = useRef(null);

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
      setIsConnecting(true);
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

  return {
    isConnected,
    isConnecting,
    lastMessage,
    error,
    chromeStatus,
    streamActive,
    streamAsset,
    // Expose the socketRef so pages can access the raw socket when needed
    socketRef,
    startStream,
    stopStream,
    changeAsset
  };
};
