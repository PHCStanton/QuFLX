/**
 * Utility functions for indicator management and formatting
 */

/**
 * Formats indicator objects into instance-based format for backend API
 * @param {Object} indicators - Object with indicator instance names as keys
 * @returns {Object} Formatted instances object for API calls
 */
export const formatIndicatorInstances = (indicators) => {
  return Object.entries(indicators).reduce((acc, [instanceName, ind]) => {
    acc[instanceName] = {
      type: ind.type,
      params: ind.params
    };
    return acc;
  }, {});
};

/**
 * Gets the current asset based on data source mode
 * @param {string} dataSource - 'csv' or 'platform'
 * @param {string} selectedAsset - Asset for CSV mode
 * @param {string} streamAsset - Asset for Platform mode
 * @returns {string|null} Current asset or null
 */
export const getCurrentAsset = (dataSource, selectedAsset, streamAsset) => {
  if (dataSource === 'csv') {
    return selectedAsset;
  } else if (dataSource === 'platform') {
    return streamAsset;
  }
  return null;
};

/**
 * Determines if indicators should be calculated based on current state
 * @param {string} dataSource - Current data source mode
 * @param {string} selectedAsset - Selected asset for CSV mode
 * @param {string} streamAsset - Stream asset for Platform mode
 * @returns {boolean} Whether indicators should be calculated
 */
export const shouldCalculateIndicators = (dataSource, selectedAsset, streamAsset) => {
  return (dataSource === 'csv' && selectedAsset) || (dataSource === 'platform' && streamAsset);
};