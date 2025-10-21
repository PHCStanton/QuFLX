import { useState, useCallback, useEffect } from 'react';

/**
 * Hook for managing streaming state and controls
 * Handles stream lifecycle, asset detection, and state transitions
 */
export const useStreamControl = (socket) => {
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

  useEffect(() => {
    if (!socket) return;

    const handleStreamStarted = (data) => {
      console.log('Stream started:', data);
      setStreamState(prev => ({
        ...prev,
        active: true,
        asset: data?.asset || prev.asset
      }));
    };

    const handleStreamStopped = () => {
      console.log('Stream stopped');
      setStreamState(prev => ({ ...prev, active: false }));
    };

    const handleAssetChanged = (data) => {
      console.log('Asset changed:', data);
      setStreamState(prev => ({ ...prev, asset: data?.asset || prev.asset }));
    };

    const handleBackendReconnected = () => {
      console.log('[Reconnection] Backend reconnected');
      setStreamState(prev => ({ ...prev, backendReconnected: true }));
      
      // Reset flag after delay
      setTimeout(() => {
        setStreamState(prev => ({ ...prev, backendReconnected: false }));
      }, 3000);
    };

    const handleChromeReconnected = () => {
      console.log('[Reconnection] Chrome reconnected');
      setStreamState(prev => ({ ...prev, chromeReconnected: true }));
      
      // Reset flag after delay
      setTimeout(() => {
        setStreamState(prev => ({ ...prev, chromeReconnected: false }));
      }, 3000);
    };

    const handleAssetDetected = (data) => {
      console.log('[AssetDetection] Asset detected:', data);
      setAssetState(prev => ({
        ...prev,
        detectedAsset: data.asset,
        detectionError: null,
        isDetecting: false
      }));
    };

    const handleAssetDetectionFailed = (data) => {
      console.error('[AssetDetection] Detection failed:', data);
      setAssetState(prev => ({
        ...prev,
        detectionError: data.error,
        detectedAsset: null,
        isDetecting: false
      }));
    };

    // Register event handlers
    socket.on('stream_started', handleStreamStarted);
    socket.on('stream_stopped', handleStreamStopped);
    socket.on('asset_changed', handleAssetChanged);
    socket.on('backend_reconnected', handleBackendReconnected);
    socket.on('chrome_reconnected', handleChromeReconnected);
    socket.on('asset_detected', handleAssetDetected);
    socket.on('asset_detection_failed', handleAssetDetectionFailed);

    return () => {
      // Cleanup event handlers
      socket.off('stream_started', handleStreamStarted);
      socket.off('stream_stopped', handleStreamStopped);
      socket.off('asset_changed', handleAssetChanged);
      socket.off('backend_reconnected', handleBackendReconnected);
      socket.off('chrome_reconnected', handleChromeReconnected);
      socket.off('asset_detected', handleAssetDetected);
      socket.off('asset_detection_failed', handleAssetDetectionFailed);
    };
  }, [socket]);

  // Stream control actions
  const startStream = useCallback((asset) => {
    if (socket) {
      socket.emit('start_stream', { asset });
    }
  }, [socket]);

  const stopStream = useCallback(() => {
    if (socket) {
      socket.emit('stop_stream');
    }
  }, [socket]);

  const changeAsset = useCallback((asset) => {
    if (socket) {
      socket.emit('change_asset', { asset });
    }
  }, [socket]);

  const detectAsset = useCallback(() => {
    if (socket) {
      console.log('[AssetDetection] Requesting asset detection...');
      setAssetState(prev => ({ ...prev, isDetecting: true, detectionError: null }));
      socket.emit('detect_asset');
    } else {
      setAssetState(prev => ({
        ...prev,
        detectionError: 'Not connected to backend',
        isDetecting: false
      }));
    }
  }, [socket]);

  return {
    stream: streamState,
    assetDetection: assetState,
    actions: {
      startStream,
      stopStream,
      changeAsset,
      detectAsset
    }
  };
};