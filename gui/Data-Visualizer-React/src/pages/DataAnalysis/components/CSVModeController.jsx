import React from 'react';

const CSVModeController = ({
  selectedAsset,
  setSelectedAsset,
  availableAssets,
  loading,
  loadHistoricalData
}) => {
  return (
    <div>
      <label
        className="block text-sm font-medium mb-2"
        style={{ color: 'var(--text-secondary)' }}
      >
        CSV File
      </label>
      <select
        value={selectedAsset}
        onChange={(e) => setSelectedAsset(e.target.value)}
        className="w-full glass border rounded-lg px-4 py-2 focus:outline-none focus:ring-2"
        style={{
          backgroundColor: 'var(--card-bg)',
          borderColor: 'var(--card-border)',
          color: 'var(--text-primary)'
        }}
      >
        {availableAssets.map(asset => (
          <option key={asset.id} value={asset.id}>{asset.name}</option>
        ))}
      </select>
      <div className="mt-4">
        <button
          onClick={loadHistoricalData}
          disabled={loading}
          className="px-6 py-2 rounded-lg font-medium transition-colors disabled:cursor-not-allowed"
          style={{
            backgroundColor: loading ? 'var(--card-border)' : 'var(--accent-blue)',
            color: 'var(--text-primary)'
          }}
          onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = 'var(--accent-purple)')}
          onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = 'var(--accent-blue)')}
        >
          {loading ? 'Loading...' : 'Load CSV Data'}
        </button>
      </div>
    </div>
  );
};

export default CSVModeController;