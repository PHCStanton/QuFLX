// Feature flag to toggle between old and new implementations
const USE_NEW_ARCHITECTURE = import.meta.env.VITE_NEW_ARCHITECTURE === 'true';

import React from 'react';

// Import both implementations
import DataAnalysisContainer from './DataAnalysisContainer';
import DataAnalysisOld from '../DataAnalysis'; // Original implementation

const DataAnalysis = () => {
  // Use feature flag to switch between implementations
  return USE_NEW_ARCHITECTURE ? <DataAnalysisContainer /> : <DataAnalysisOld />;
};

export default DataAnalysis;