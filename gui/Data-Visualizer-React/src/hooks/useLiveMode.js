import { useState, useEffect } from 'react';

/**
 * Custom hook for managing live mode state
 * Centralizes live mode logic and ensures consistent state transitions
 */
export const useLiveMode = ({
  dataSource,
  chromeConnected,
  streamActive,
  streamAsset
}) => {
  const [isLiveMode, setIsLiveMode] = useState(false);

  // Automatically update live mode based on data source and stream state
  useEffect(() => {
    if (dataSource === 'platform') {
      // In platform mode, live mode is active when streaming
      setIsLiveMode(streamActive && !!streamAsset);
    } else {
      // In CSV mode, always false
      setIsLiveMode(false);
    }
  }, [dataSource, streamActive, streamAsset]);

  // Derived states for UI feedback
  const canEnterLiveMode = dataSource === 'platform' && chromeConnected;
  const isStreamReady = canEnterLiveMode && !streamActive;
  const isStreaming = canEnterLiveMode && streamActive;

  return {
    isLiveMode,
    canEnterLiveMode,
    isStreamReady,
    isStreaming
  };
};