/**
 * Utility functions for loading and parsing CSV data
 */

/**
 * Loads and parses CSV data from the backend
 * @param {string} assetId - The asset identifier
 * @param {string} selectedAssetFile - The filename of the CSV file
 * @param {Function} detectBackendUrl - Function to detect backend URL
 * @param {Function} parseTradingData - Function to parse raw data
 * @returns {Promise<Array>} Parsed chart data
 */
export const loadCsvData = async (assetId, selectedAssetFile, detectBackendUrl, parseTradingData) => {
  if (!assetId || !selectedAssetFile) {
    throw new Error('Asset ID and file selection are required');
  }

  const baseUrl = detectBackendUrl();
  const response = await fetch(`${baseUrl}/api/csv-data/${selectedAssetFile}`);

  if (!response.ok) {
    throw new Error(`Failed to load CSV data: ${response.status}`);
  }

  const text = await response.text();
  if (!text || typeof text !== 'string') {
    throw new Error('Invalid response: expected text data');
  }

  return parseCsvText(text, assetId, parseTradingData);
};

/**
 * Parses CSV text into chart data
 * @param {string} csvText - Raw CSV text
 * @param {string} assetId - Asset identifier for parsing
 * @param {Function} parseTradingData - Trading data parser function
 * @returns {Array} Parsed chart data
 */
export const parseCsvText = (csvText, assetId, parseTradingData) => {
  const lines = csvText.trim().split('\n');
  if (lines.length < 2) {
    throw new Error('CSV file is empty');
  }

  const headers = lines[0].split(',').map(h => h.trim());
  const rawData = lines.slice(1).map(line => {
    const values = line.split(',').map(v => v.trim());
    const obj = {};
    headers.forEach((header, idx) => {
      obj[header] = isNaN(values[idx]) ? values[idx] : parseFloat(values[idx]);
    });
    return obj;
  });

  if (!Array.isArray(rawData) || rawData.length === 0) {
    throw new Error('No valid data rows found in CSV');
  }

  const parsedData = parseTradingData(rawData, assetId);
  if (!Array.isArray(parsedData) || parsedData.length === 0) {
    throw new Error('Failed to parse trading data');
  }

  return parsedData;
};