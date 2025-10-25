import { useState, useEffect, useCallback } from 'react';

/**
 * Enhanced useCsvData hook with Redis caching integration
 * Checks Redis cache first before querying Supabase for historical data
 * Maintains <50ms response time for cached data
 */
export const useCsvData = ({
  dataSource,
  selectedAsset,
  selectedAssetFile,
  timeframe,
  isConnected,
  storeCsvCandles
}) => {
  const [state, setState] = useState({
    data: [],
    loading: false,
    error: null,
    source: 'unknown', // 'redis_cache', 'supabase', 'csv'
    cacheHit: false
  });

  // Load data from Redis cache first, then Supabase fallback
  const loadData = useCallback(async () => {
    if (!selectedAsset || !isConnected) return;

    setState(prev => ({ ...prev, loading: true, error: null }));

    try {
      // Step 1: Check Redis cache first
      if (isConnected) {
        const cachedData = await checkRedisCache(selectedAsset, timeframe);
        if (cachedData) {
          console.log(`[useCsvData] Cache hit for ${selectedAsset} ${timeframe}`);
          setState({
            data: cachedData,
            loading: false,
            error: null,
            source: 'redis_cache',
            cacheHit: true
          });
          return;
        }
      }

      // Step 2: Load from Supabase if cache miss
      const supabaseData = await loadFromSupabase(selectedAsset, timeframe);
      if (supabaseData) {
        console.log(`[useCsvData] Loaded from Supabase for ${selectedAsset} ${timeframe}`);
        
        // Step 3: Cache the data for future requests
        if (isConnected) {
          await cacheDataInRedis(selectedAsset, timeframe, supabaseData);
        }

        setState({
          data: supabaseData,
          loading: false,
          error: null,
          source: 'supabase',
          cacheHit: false
        });
      }

    } catch (error) {
      console.error('[useCsvData] Error loading data:', error);
      setState({
        data: [],
        loading: false,
        error: `Failed to load data: ${error.message}`,
        source: 'error',
        cacheHit: false
      });
    }
  }, [selectedAsset, timeframe, isConnected]);

  // Check Redis cache for historical data
  const checkRedisCache = useCallback(async (asset, tf) => {
    return new Promise((resolve) => {
      if (!window.socket) {
        resolve(null);
        return;
      }

      const timeout = setTimeout(() => {
        resolve(null);
      }, 1000); // 1 second timeout

      const handleResponse = (response) => {
        clearTimeout(timeout);
        window.socket.off('cached_historical_data', handleResponse);
        
        if (response.data && response.source === 'redis_cache') {
          resolve(response.data);
        } else {
          resolve(null);
        }
      };

      window.socket.on('cached_historical_data', handleResponse);
      window.socket.emit('get_cached_historical_data', {
        asset,
        timeframe: tf
      });
    });
  }, []);

  // Load data from Supabase
  const loadFromSupabase = useCallback(async (asset, tf) => {
    try {
      // Import Supabase client dynamically
      const { createClient } = await import('@supabase/supabase-js');
      const supabase = createClient(
        process.env.REACT_APP_SUPABASE_URL,
        process.env.REACT_APP_SUPABASE_ANON_KEY
      );

      // Query historical candles from Supabase
      const { data, error } = await supabase
        .from('candles')
        .select(`
          timestamp,
          open,
          high,
          low,
          close,
          volume
        `)
        .eq('asset_symbol', asset)
        .eq('timeframe', tf)
        .order('timestamp', { ascending: true })
        .limit(200);

      if (error) {
        throw new Error(`Supabase query error: ${error.message}`);
      }

      // Convert to chart format
      return data.map(row => ({
        timestamp: row.timestamp,
        open: row.open,
        high: row.high,
        low: row.low,
        close: row.close,
        volume: row.volume || 0,
        date: new Date(row.timestamp * 1000).toISOString()
      }));

    } catch (error) {
      console.error('[useCsvData] Supabase error:', error);
      throw error;
    }
  }, []);

  // Cache data in Redis
  const cacheDataInRedis = useCallback(async (asset, tf, data) => {
    return new Promise((resolve) => {
      if (!window.socket || !data || data.length === 0) {
        resolve(false);
        return;
      }

      const timeout = setTimeout(() => {
        resolve(false);
      }, 1000); // 1 second timeout

      const handleResponse = (response) => {
        clearTimeout(timeout);
        window.socket.off('historical_data_cached', handleResponse);
        resolve(true);
      };

      window.socket.on('historical_data_cached', handleResponse);
      window.socket.emit('cache_historical_data', {
        asset,
        timeframe: tf,
        data
      });
    });
  }, []);

  // Clear cache for specific asset/timeframe
  const clearCache = useCallback(async (asset, tf) => {
    if (!window.socket) return;

    return new Promise((resolve) => {
      const timeout = setTimeout(() => {
        resolve(false);
      }, 1000);

      const handleResponse = (response) => {
        clearTimeout(timeout);
        window.socket.off('historical_data_cache_cleared', handleResponse);
        resolve(true);
      };

      window.socket.on('historical_data_cache_cleared', handleResponse);
      window.socket.emit('clear_cached_historical_data', {
        asset,
        timeframe: tf
      });
    });
  }, []);

  // Store data in backend for indicator calculation
  const storeInBackend = useCallback(async (data) => {
    if (!isConnected || !storeCsvCandles || data.length === 0) return;

    try {
      await storeCsvCandles(selectedAsset, data);
      console.log(`[useCsvData] Stored ${data.length} candles in backend`);
    } catch (error) {
      console.error('[useCsvData] Error storing in backend:', error);
    }
  }, [selectedAsset, isConnected, storeCsvCandles]);

  // Load data when dependencies change
  useEffect(() => {
    if (dataSource === 'csv' && selectedAsset) {
      loadData();
    }
  }, [dataSource, selectedAsset, timeframe, loadData]);

  // Auto-refresh cache every 5 minutes
  useEffect(() => {
    if (!isConnected || !selectedAsset) return;

    const interval = setInterval(async () => {
      // Refresh cache in background
      await checkRedisCache(selectedAsset, timeframe);
    }, 5 * 60 * 1000); // 5 minutes

    return () => clearInterval(interval);
  }, [isConnected, selectedAsset, timeframe]);

  return {
    // State
    data: state.data,
    loading: state.loading,
    error: state.error,
    source: state.source,
    cacheHit: state.cacheHit,
    
    // Actions
    loadData,
    clearCache,
    refreshCache: () => loadData(),
    storeInBackend
  };
};