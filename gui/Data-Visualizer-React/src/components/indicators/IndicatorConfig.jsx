import React, { useState, useCallback } from 'react';

const INDICATOR_LIBRARY = {
  // Overlay indicators (shown on price chart)
  overlay: [
    {
      id: 'sma',
      name: 'Simple Moving Average (SMA)',
      defaultConfig: { period: 20 },
      fields: [{ name: 'period', label: 'Period', type: 'number', min: 1, max: 200, default: 20 }]
    },
    {
      id: 'ema',
      name: 'Exponential Moving Average (EMA)',
      defaultConfig: { period: 20 },
      fields: [{ name: 'period', label: 'Period', type: 'number', min: 1, max: 200, default: 20 }]
    },
    {
      id: 'bollinger',
      name: 'Bollinger Bands',
      defaultConfig: { period: 20, std_dev: 2 },
      fields: [
        { name: 'period', label: 'Period', type: 'number', min: 1, max: 200, default: 20 },
        { name: 'std_dev', label: 'Std Dev', type: 'number', min: 0.5, max: 5, step: 0.1, default: 2 }
      ]
    }
  ],
  // Oscillator indicators (separate pane below chart)
  oscillator: [
    {
      id: 'rsi',
      name: 'Relative Strength Index (RSI)',
      defaultConfig: { period: 14 },
      fields: [{ name: 'period', label: 'Period', type: 'number', min: 1, max: 50, default: 14 }]
    },
    {
      id: 'macd',
      name: 'MACD',
      defaultConfig: { fast: 12, slow: 26, signal: 9 },
      fields: [
        { name: 'fast', label: 'Fast Period', type: 'number', min: 1, max: 50, default: 12 },
        { name: 'slow', label: 'Slow Period', type: 'number', min: 1, max: 100, default: 26 },
        { name: 'signal', label: 'Signal Period', type: 'number', min: 1, max: 50, default: 9 }
      ]
    },
    {
      id: 'stochastic',
      name: 'Stochastic Oscillator',
      defaultConfig: { k_period: 14, d_period: 3 },
      fields: [
        { name: 'k_period', label: 'K Period', type: 'number', min: 1, max: 50, default: 14 },
        { name: 'd_period', label: 'D Period', type: 'number', min: 1, max: 20, default: 3 }
      ]
    }
  ]
};

export default function IndicatorConfig({ 
  activeIndicators = {}, 
  onIndicatorsChange,
  disabled = false 
}) {
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('overlay');

  const handleAddIndicator = useCallback((indicator) => {
    const newIndicators = {
      ...activeIndicators,
      [indicator.id]: indicator.defaultConfig
    };
    onIndicatorsChange(newIndicators);
    setShowAddModal(false);
  }, [activeIndicators, onIndicatorsChange]);

  const handleRemoveIndicator = useCallback((indicatorId) => {
    const newIndicators = { ...activeIndicators };
    delete newIndicators[indicatorId];
    onIndicatorsChange(newIndicators);
  }, [activeIndicators, onIndicatorsChange]);

  const handleConfigChange = useCallback((indicatorId, field, value) => {
    const newIndicators = {
      ...activeIndicators,
      [indicatorId]: {
        ...activeIndicators[indicatorId],
        [field]: parseFloat(value)
      }
    };
    onIndicatorsChange(newIndicators);
  }, [activeIndicators, onIndicatorsChange]);

  const getIndicatorInfo = (indicatorId) => {
    const allIndicators = [...INDICATOR_LIBRARY.overlay, ...INDICATOR_LIBRARY.oscillator];
    return allIndicators.find(ind => ind.id === indicatorId);
  };

  return (
    <div className="space-y-4">
      {/* Active Indicators */}
      <div className="space-y-2">
        {Object.keys(activeIndicators).length === 0 ? (
          <div className="text-center py-4" style={{ color: 'var(--text-muted)' }}>
            <p className="text-sm">No indicators added yet</p>
            <p className="text-xs mt-1">Click "Add Indicator" to get started</p>
          </div>
        ) : (
          Object.entries(activeIndicators).map(([indicatorId, config]) => {
            const indicatorInfo = getIndicatorInfo(indicatorId);
            if (!indicatorInfo) return null;

            return (
              <div
                key={indicatorId}
                className="glass rounded-lg p-3"
                style={{ borderColor: 'var(--card-border)' }}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="font-medium" style={{ color: 'var(--text-primary)' }}>
                    {indicatorInfo.name}
                  </span>
                  <button
                    onClick={() => handleRemoveIndicator(indicatorId)}
                    disabled={disabled}
                    className="text-red-400 hover:text-red-300 disabled:opacity-50"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                
                {/* Indicator Config Fields */}
                <div className="grid grid-cols-2 gap-2">
                  {indicatorInfo.fields.map(field => (
                    <div key={field.name}>
                      <label className="text-xs" style={{ color: 'var(--text-muted)' }}>
                        {field.label}
                      </label>
                      <input
                        type={field.type}
                        value={config[field.name] || field.default}
                        onChange={(e) => handleConfigChange(indicatorId, field.name, e.target.value)}
                        min={field.min}
                        max={field.max}
                        step={field.step || 1}
                        disabled={disabled}
                        className="w-full px-2 py-1 rounded text-sm bg-gray-800/50 border border-gray-700 focus:border-purple-500 focus:outline-none disabled:opacity-50"
                        style={{ color: 'var(--text-primary)' }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Add Indicator Button */}
      <button
        onClick={() => setShowAddModal(true)}
        disabled={disabled}
        className="w-full px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
        style={{
          backgroundColor: 'var(--accent-purple)',
          color: 'var(--text-primary)'
        }}
      >
        + Add Indicator
      </button>

      {/* Add Indicator Modal */}
      {showAddModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowAddModal(false)}>
          <div 
            className="glass rounded-xl p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <h3 className="text-xl font-semibold mb-4" style={{ color: 'var(--text-primary)' }}>
              Add Indicator
            </h3>

            {/* Category Tabs */}
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setSelectedCategory('overlay')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedCategory === 'overlay' ? 'bg-purple-600' : 'bg-gray-700'
                }`}
              >
                Overlay
              </button>
              <button
                onClick={() => setSelectedCategory('oscillator')}
                className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                  selectedCategory === 'oscillator' ? 'bg-purple-600' : 'bg-gray-700'
                }`}
              >
                Oscillator
              </button>
            </div>

            {/* Indicator List */}
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {INDICATOR_LIBRARY[selectedCategory].map(indicator => {
                const isAlreadyAdded = activeIndicators.hasOwnProperty(indicator.id);
                
                return (
                  <button
                    key={indicator.id}
                    onClick={() => !isAlreadyAdded && handleAddIndicator(indicator)}
                    disabled={isAlreadyAdded}
                    className={`w-full text-left px-4 py-3 rounded-lg transition-colors ${
                      isAlreadyAdded 
                        ? 'bg-gray-800 opacity-50 cursor-not-allowed' 
                        : 'bg-gray-800 hover:bg-gray-700'
                    }`}
                  >
                    <div className="font-medium" style={{ color: 'var(--text-primary)' }}>
                      {indicator.name}
                    </div>
                    {isAlreadyAdded && (
                      <div className="text-xs mt-1" style={{ color: 'var(--text-muted)' }}>
                        Already added
                      </div>
                    )}
                  </button>
                );
              })}
            </div>

            <button
              onClick={() => setShowAddModal(false)}
              className="w-full mt-4 px-4 py-2 rounded-lg bg-gray-700 hover:bg-gray-600 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
