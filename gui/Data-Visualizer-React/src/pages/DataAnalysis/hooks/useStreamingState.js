import { useState, useCallback } from 'react';

// Simplified streaming state management
export function useStreamingState() {
  const [streamingState, setStreamingState] = useState({
    mode: 'csv', // 'csv' | 'platform'
    status: 'idle', // 'idle' | 'connected' | 'streaming' | 'error'
    asset: null,
    error: null
  });

  const [chartConfig, setChartConfig] = useState({
    timeframe: '1m',
    isLiveMode: false
  });

  const [uiState, setUiState] = useState({
    loading: false,
    loadingStatus: '',
    statistics: null
  });

  // Actions to update state
  const setMode = useCallback((mode) => {
    setStreamingState(prev => ({
      ...prev,
      mode,
      asset: null, // Clear asset when switching modes
      status: 'idle',
      error: null
    }));

    // Clear chart data when switching modes
    setChartConfig(prev => ({
      ...prev,
      isLiveMode: false
    }));

    setUiState(prev => ({
      ...prev,
      statistics: null
    }));
  }, []);

  const setAsset = useCallback((asset) => {
    setStreamingState(prev => ({
      ...prev,
      asset,
      error: null
    }));
  }, []);

  const setStatus = useCallback((status, error = null) => {
    setStreamingState(prev => ({
      ...prev,
      status,
      error
    }));
  }, []);

  const setTimeframe = useCallback((timeframe) => {
    setChartConfig(prev => ({
      ...prev,
      timeframe
    }));
  }, []);

  const setLiveMode = useCallback((isLive) => {
    setChartConfig(prev => ({
      ...prev,
      isLiveMode: isLive
    }));
  }, []);

  const setLoading = useCallback((loading, status = '') => {
    setUiState(prev => ({
      ...prev,
      loading,
      loadingStatus: status
    }));
  }, []);

  const setStatistics = useCallback((statistics) => {
    setUiState(prev => ({
      ...prev,
      statistics
    }));
  }, []);

  return {
    // State
    streamingState,
    chartConfig,
    uiState,

    // Actions
    setMode,
    setAsset,
    setStatus,
    setTimeframe,
    setLiveMode,
    setLoading,
    setStatistics
  };
}