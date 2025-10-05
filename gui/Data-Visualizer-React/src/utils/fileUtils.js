export const fetchCurrencyPairs = async () => {
  try {
    // Fetch actual CSV files from the backend API (using Vite proxy)
    const response = await fetch('/api/available-csv-files');
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
      
      // Check if this is an OTC pair (case-insensitive check in filename)
      const isOTC = firstFile.filename.toLowerCase().includes('_otc');
      
      // Format display name
      let displayName = assetId.toUpperCase();
      
      // Add proper slash for forex pairs (e.g., EURUSD -> EUR/USD)
      displayName = displayName.replace(/([A-Z]{3})([A-Z]{3})/, '$1/$2');
      
      // Clearly mark OTC pairs with a badge
      if (isOTC) {
        displayName = `${displayName} (OTC)`;
      }
      
      return {
        id: assetId,
        name: displayName,
        file: firstFile.filename,
        path: firstFile.path,
        timeframe: firstFile.timeframe,
        size: firstFile.size,
        isOTC: isOTC
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
