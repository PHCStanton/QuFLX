import { useState, useCallback } from 'react';
import { fetchCurrencyPairs } from '../../../utils/fileUtils';
import { parseTradingData } from '../../../utils/tradingData';

export function useCSVData() {
  const [availableAssets, setAvailableAssets] = useState([]);
  const [selectedAsset, setSelectedAsset] = useState('');

  const loadAvailableAssets = useCallback(async (timeframe) => {
    try {
      const pairs = await fetchCurrencyPairs(timeframe);
      setAvailableAssets(pairs);

      // Auto-select first asset if none selected
      if (!selectedAsset && pairs.length > 0) {
        setSelectedAsset(pairs[0].id);
      }

      return pairs;
    } catch (error) {
      console.error('Error loading available assets:', error);
      return [];
    }
  }, [selectedAsset]);

  const loadCSVData = useCallback(async (assetId, timeframe) => {
    if (!assetId) return null;

    try {
      const assetInfo = availableAssets.find(a => a.id === assetId);
      if (!assetInfo) return null;

      // Fetch CSV data
      const response = await fetch(`/api/csv-data/${assetInfo.file}`, {
        cache: 'no-store'
      });

      if (!response.ok) {
        throw new Error(`Failed to load data: ${response.statusText}`);
      }

      const csvText = await response.text();
      const data = parseTradingData(csvText, assetId);

      console.log(`Loaded ${data.length} data points for ${assetId}`);
      return data;
    } catch (error) {
      console.error('Error loading CSV data:', error);
      throw error;
    }
  }, [availableAssets]);

  return {
    availableAssets,
    selectedAsset,
    setSelectedAsset,
    loadAvailableAssets,
    loadCSVData
  };
}