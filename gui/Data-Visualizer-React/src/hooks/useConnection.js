import { useState, useEffect } from 'react';
import io from 'socket.io-client';
import { detectSocketUrl } from '../utils/urlHelper';

/**
 * Hook for managing WebSocket connection state
 * Handles connection lifecycle and status updates
 */
export const useConnection = (url) => {
  const [state, setState] = useState({
    isConnected: false,
    isConnecting: false,
    error: null,
    chromeStatus: 'not connected'
  });

  const [socket, setSocket] = useState(null);

  useEffect(() => {
    const connectUrl = url || detectSocketUrl();
    setState(prev => ({ ...prev, isConnecting: true }));

    const newSocket = io(connectUrl, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 5,
      forceNew: true,
      timeout: 10000
    });

    setSocket(newSocket);

    newSocket.on('connect', () => {
      console.log('WebSocket connected with session:', newSocket.id);
      setState(prev => ({
        ...prev,
        isConnected: true,
        isConnecting: false,
        error: null
      }));
    });

    newSocket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false
      }));
    });

    newSocket.on('connect_error', (err) => {
      console.error('WebSocket connection error:', err);
      setState(prev => ({
        ...prev,
        isConnected: false,
        isConnecting: false,
        error: err.message
      }));
    });

    newSocket.on('connection_status', (data) => {
      console.log('Connection status:', data);
      setState(prev => ({ ...prev, chromeStatus: data.chrome || 'not connected' }));
    });

    return () => {
      console.log('Cleaning up WebSocket connection');
      if (newSocket) {
        newSocket.removeAllListeners();
        if (newSocket.connected || newSocket.io?.engine?.readyState === 'open') {
          newSocket.disconnect();
        } else if (newSocket.io?.engine?.readyState === 'opening') {
          newSocket.io.engine?.close?.();
        }
      }
    };
  }, [url]);

  return {
    socket,
    state
  };
};