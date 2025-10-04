import React, { useState, useCallback } from "react";
import SimpleChart from './charts/SimpleChart';

const TradingChart = ({ data = [], indicators = {} }) => {
  const [error, setError] = useState(null);

  // Handle chart ready callback
  const handleChartReady = useCallback((chart) => {
    console.log('[TradingChart] Chart ready:', chart);
    setError(null);
  }, []);

  // Handle any errors that might occur
  const handleError = useCallback((errorMessage) => {
    console.error('[TradingChart] Error:', errorMessage);
    setError(errorMessage);
  }, []);

  // Render error state
  if (error) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px] bg-slate-800 rounded-lg text-red-400 p-4">
        <div className="text-center">
          <div className="text-5xl mb-4">⚠️</div>
          <h3 className="text-lg font-semibold text-slate-300 mb-2">Chart Error</h3>
          <p className="text-sm">{error}</p>
          <button
            onClick={() => setError(null)}
            className="mt-4 px-4 py-2 bg-slate-700 hover:bg-slate-600 rounded text-sm transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <SimpleChart
      data={data}
    />
  );
};

export default TradingChart;
