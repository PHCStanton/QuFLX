import { useState, useCallback, useEffect } from 'react';
import { loadCsvData } from '../utils/csvDataLoader';
import { detectBackendUrl } from '../utils/urlHelper';
import { parseTradingData } from '../utils/tradingData';

/**
 * Custom hook for managing CSV data loading
 * Handles loading, parsing, and error states
 */
export const useCsvData = ({
  dataSource,
  selectedAsset,
  selectedAssetFile,
  timeframe,
  isConnected,
  storeCsvCandles
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState([]);

  const loadData = useCallback(async () => {
    if (dataSource !== 'csv' || !selectedAsset || !selectedAssetFile) {
      setData([]);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const parsedData = await loadCsvData(
        selectedAsset,
        selectedAssetFile,
        detectBackendUrl,
        parseTradingData
      );

      setData(parsedData);

      // Store in backend if connected
      if (isConnected) {
        storeCsvCandles(selectedAsset, parsedData);
      }
    } catch (err) {
      setError(err.message);
      setData([]);
    } finally {
      setIsLoading(false);
    }
  }, [
    dataSource,
    selectedAsset,
    selectedAssetFile,
    isConnected,
    storeCsvCandles
  ]);

  // Load data when dependencies change
  useEffect(() => {
    loadData();
  }, [loadData, timeframe]);

  return {
    data,
    isLoading,
    error,
    loadData
  };
};