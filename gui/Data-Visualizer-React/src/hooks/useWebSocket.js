import { useEffect, useState, useCallback, useRef } from 'react';
import io from 'socket.io-client';

export const useWebSocket = (url) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const [chromeStatus, setChromeStatus] = useState('not connected');
  const socketRef = useRef(null);

  useEffect(() => {
    // Create socket connection with polling first to avoid initial errors
    const socket = io(url, {
      transports: ['polling', 'websocket'],
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
      setError(null);
    });

    socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setIsConnected(false);
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setError(err.message);
      setIsConnected(false);
    });
    
    socket.on('reconnect_error', (err) => {
      console.error('WebSocket reconnection error:', err);
    });
    
    socket.on('reconnect_failed', () => {
      console.error('WebSocket reconnection failed after all attempts');
      setError('Failed to reconnect to server');
    });

    socket.on('tick_update', (data) => {
      setLastMessage(data);
    });

    socket.on('stream_started', (data) => {
      console.log('Stream started:', data);
    });

    socket.on('stream_stopped', (data) => {
      console.log('Stream stopped:', data);
    });

    socket.on('asset_changed', (data) => {
      console.log('Asset changed:', data);
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
    lastMessage,
    error,
    chromeStatus,
    startStream,
    stopStream,
    changeAsset
  };
};
