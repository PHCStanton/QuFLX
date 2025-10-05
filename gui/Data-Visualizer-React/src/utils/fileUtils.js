export const fetchCurrencyPairs = async (timeframe = null) => {
  try {
    // Fetch actual CSV files from the backend API (using Vite proxy)
    const url = timeframe 
      ? `/api/available-csv-files?timeframe=${timeframe}`
      : '/api/available-csv-files';
    const response = await fetch(url);
    const data = await response.json();
    
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
      const firstFile = files[0];
      
      // Use the actual filename as the display name for clarity
      const displayName = firstFile.filename.replace('.csv', '');
      
      return {
        id: assetId,
        name: displayName,
        file: firstFile.filename,
        path: firstFile.path,
        timeframe: firstFile.timeframe,
        size: firstFile.size
      };
    });
    
    console.log(`Loaded ${pairs.length} currency pairs from backend`);
    return pairs;
  } catch (error) {
    console.error('Error fetching currency pairs:', error);
    // Return empty array on error
    return [];
  }
};
