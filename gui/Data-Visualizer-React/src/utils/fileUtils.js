// Helper: retry with exponential backoff
async function fetchWithRetry(url, options = {}, attempts = 3, baseDelayMs = 300) {
  let attempt = 0;
  while (attempt < attempts) {
    try {
      const res = await fetch(url, options);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      return json;
    } catch (err) {
      attempt += 1;
      if (attempt >= attempts) throw err;
      const wait = baseDelayMs * Math.pow(2, attempt - 1);
      await new Promise(r => setTimeout(r, wait));
    }
  }
}

export const fetchCurrencyPairs = async (timeframe = null) => {
  const url = timeframe 
    ? `/api/available-csv-files?timeframe=${timeframe}`
    : '/api/available-csv-files';
  const cacheKey = timeframe ? `pairs_cache_${timeframe}` : 'pairs_cache_all';

  try {
    // Try with retry/backoff
    const data = await fetchWithRetry(url, { cache: 'no-store' }, 3, 400);

    if (!data.files || data.files.length === 0) {
      console.warn('No CSV files found, returning empty array');
      return [];
    }

    // Group files by asset
    const pairGroups = {};
    data.files.forEach(file => {
      const asset = file.asset;
      if (!pairGroups[asset]) {
        pairGroups[asset] = [];
      }
      pairGroups[asset].push(file);
    });

    // Create currency pairs array with formatted names
    const pairs = Object.keys(pairGroups).map(assetId => {
      const files = pairGroups[assetId];
      
      // Filter out tick data files - only keep candle files
      const candleFiles = files.filter(f => !f.filename.includes('tick'));
      const filesToConsider = candleFiles.length > 0 ? candleFiles : files;
      
      // Pick the largest file (most data) or newest file
      const bestFile = filesToConsider.reduce((best, current) => {
        // Prefer larger files (more candle data)
        if (current.size > best.size) return current;
        // If same size, prefer newer filename (by string comparison)
        if (current.size === best.size && current.filename > best.filename) return current;
        return best;
      }, filesToConsider[0]);

      const displayName = bestFile.filename.replace('.csv', '');

      return {
        id: assetId,
        name: displayName,
        file: bestFile.filename,
        path: bestFile.path,
        timeframe: bestFile.timeframe,
        size: bestFile.size
      };
    });

    // Cache successful result for fallback
    try {
      localStorage.setItem(cacheKey, JSON.stringify({ timestamp: Date.now(), pairs }));
    } catch {}

    console.log(`Loaded ${pairs.length} currency pairs from backend`);
    return pairs;
  } catch (error) {
    console.error('Error fetching currency pairs, using cached fallback if available:', error);
    // Fallback to cache
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { pairs } = JSON.parse(cached);
        console.warn('Using cached currency pairs');
        return pairs || [];
      }
    } catch {}
    // Return empty array on error
    return [];
  }
};
