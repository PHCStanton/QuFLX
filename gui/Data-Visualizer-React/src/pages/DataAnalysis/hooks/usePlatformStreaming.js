import { useState, useCallback, useEffect } from 'react';

// Simplified 3-state machine for Platform mode
const PLATFORM_STATES = {
  DISCONNECTED: 'disconnected',  // Chrome not available
  READY: 'ready',                // Connected, can start
  STREAMING: 'streaming'         // Active stream
};

export function usePlatformStreaming(chromeConnected) {
  const [streamState, setStreamState] = useState(PLATFORM_STATES.DISCONNECTED);
  const [detectedAsset, setDetectedAsset] = useState(null);
  const [streamError, setStreamError] = useState(null);
  const [isDetecting, setIsDetecting] = useState(false);

  // Update state based on Chrome connection
  useEffect(() => {
    if (!chromeConnected) {
      setStreamState(PLATFORM_STATES.DISCONNECTED);
      setDetectedAsset(null);
    } else if (chromeConnected && streamState === PLATFORM_STATES.DISCONNECTED) {
      setStreamState(PLATFORM_STATES.READY);
      setStreamError(null);
    }
  }, [chromeConnected, streamState]);

  const handleDetectAsset = useCallback(() => {
    setIsDetecting(true);
    setStreamError(null);
    setStreamState(PLATFORM_STATES.DETECTING);
    // WebSocket detection will be handled by parent component
  }, []);

  const handleAssetDetected = useCallback((asset) => {
    setDetectedAsset(asset);
    setStreamState(PLATFORM_STATES.ASSET_DETECTED);
    setStreamError(null);
    setIsDetecting(false);
  }, []);

  const handleDetectionError = useCallback((error) => {
    setStreamError(error);
    setStreamState(PLATFORM_STATES.ERROR);
    setDetectedAsset(null);
    setIsDetecting(false);
  }, []);

  const handleStartStream = useCallback(() => {
    if (!detectedAsset) {
      setStreamError('No asset detected');
      setStreamState(PLATFORM_STATES.ERROR);
      return;
    }

    console.log(`[PlatformStreaming] Starting stream for ${detectedAsset}...`);
    setStreamState(PLATFORM_STATES.STREAMING);
    // Streaming will be handled by parent component
  }, [detectedAsset]);

  const handleStopStream = useCallback(() => {
    console.log('[PlatformStreaming] Stopping stream...');
    setStreamState(PLATFORM_STATES.READY);
    setDetectedAsset(null);
    // Stop streaming will be handled by parent component
  }, []);

  const reset = useCallback(() => {
    setStreamState(chromeConnected ? PLATFORM_STATES.READY : PLATFORM_STATES.DISCONNECTED);
    setDetectedAsset(null);
    setStreamError(null);
    setIsDetecting(false);
  }, [chromeConnected]);

  return {
    streamState,
    detectedAsset,
    streamError,
    isDetecting,
    handleDetectAsset,
    handleAssetDetected,
    handleDetectionError,
    handleStartStream,
    handleStopStream,
    reset
  };
}