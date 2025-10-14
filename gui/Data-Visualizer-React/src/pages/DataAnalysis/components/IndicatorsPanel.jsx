import React from 'react';

const IndicatorsPanel = ({
  indicatorData,
  indicatorError,
  isCalculatingIndicators,
  handleCalculateIndicators,
  selectedAsset,
  streamAsset,
  detectedAsset,
  dataSource
}) => {
  return (
    <div
      className="glass rounded-xl p-6"
      style={{ borderColor: 'var(--card-border)' }}
    >
      <div className="flex items-center justify-between mb-4">
        <h3
          className="text-xl font-semibold"
          style={{ color: 'var(--text-primary)' }}
        >Technical Indicators</h3>
        <button
          onClick={handleCalculateIndicators}
          disabled={isCalculatingIndicators || (!selectedAsset && !streamAsset && !detectedAsset)}
          className="px-4 py-2 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          style={{
            backgroundColor: 'var(--accent-purple)',
            color: 'var(--text-primary)'
          }}
          onMouseEnter={(e) => !isCalculatingIndicators && (e.target.style.backgroundColor = 'var(--accent-blue)')}
          onMouseLeave={(e) => !isCalculatingIndicators && (e.target.style.backgroundColor = 'var(--accent-purple)')}
        >
          {isCalculatingIndicators ? (
            <span className="flex items-center gap-2">
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              Calculating...
            </span>
          ) : 'Calculate Indicators'}
        </button>
      </div>

      {indicatorError && (
        <div className="mb-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30">
          <p className="text-sm text-red-400">{indicatorError}</p>
        </div>
      )}

      {indicatorData && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* SMA Indicator */}
            {indicatorData.indicators?.sma && (
              <div className="glass rounded-lg p-4" style={{ borderColor: 'var(--card-border)' }}>
                <div className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                  SMA ({indicatorData.indicators.sma.period})
                </div>
                <div className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                  {indicatorData.indicators.sma.value.toFixed(5)}
                </div>
                <div className={`text-sm font-medium ${
                  indicatorData.indicators.sma.signal === 'BUY' ? 'text-green-400' : 'text-red-400'
                }`}>
                  {indicatorData.indicators.sma.signal}
                </div>
              </div>
            )}

            {/* RSI Indicator */}
            {indicatorData.indicators?.rsi && (
              <div className="glass rounded-lg p-4" style={{ borderColor: 'var(--card-border)' }}>
                <div className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                  RSI ({indicatorData.indicators.rsi.period})
                </div>
                <div className="text-lg font-semibold mb-1" style={{ color: 'var(--text-primary)' }}>
                  {indicatorData.indicators.rsi.value.toFixed(2)}
                </div>
                <div className={`text-sm font-medium ${
                  indicatorData.indicators.rsi.signal === 'BUY' ? 'text-green-400' :
                  indicatorData.indicators.rsi.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {indicatorData.indicators.rsi.signal}
                </div>
              </div>
            )}

            {/* Bollinger Bands */}
            {indicatorData.indicators?.bollinger && (
              <div className="glass rounded-lg p-4" style={{ borderColor: 'var(--card-border)' }}>
                <div className="text-sm mb-2" style={{ color: 'var(--text-muted)' }}>
                  Bollinger Bands ({indicatorData.indicators.bollinger.period})
                </div>
                <div className="text-sm space-y-1" style={{ color: 'var(--text-primary)' }}>
                  <div>Upper: {indicatorData.indicators.bollinger.upper_band.toFixed(5)}</div>
                  <div>Middle: {indicatorData.indicators.bollinger.middle_band.toFixed(5)}</div>
                  <div>Lower: {indicatorData.indicators.bollinger.lower_band.toFixed(5)}</div>
                </div>
                <div className={`text-sm font-medium mt-2 ${
                  indicatorData.indicators.bollinger.signal === 'BUY' ? 'text-green-400' :
                  indicatorData.indicators.bollinger.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'
                }`}>
                  {indicatorData.indicators.bollinger.signal}
                </div>
              </div>
            )}
          </div>

          {/* Overall Signal */}
          {indicatorData.signals?.overall && (
            <div className="glass rounded-lg p-4" style={{ borderColor: 'var(--card-border)' }}>
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm mb-1" style={{ color: 'var(--text-muted)' }}>Overall Signal</div>
                  <div className={`text-2xl font-bold ${
                    indicatorData.signals.overall.signal === 'BUY' ? 'text-green-400' :
                    indicatorData.signals.overall.signal === 'SELL' ? 'text-red-400' : 'text-yellow-400'
                  }`}>
                    {indicatorData.signals.overall.signal}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm mb-1" style={{ color: 'var(--text-muted)' }}>Confidence</div>
                  <div className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
                    {(indicatorData.signals.overall.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              <div className="mt-2 text-xs" style={{ color: 'var(--text-muted)' }}>
                {indicatorData.signals.overall.buy_count} BUY • {indicatorData.signals.overall.sell_count} SELL • {indicatorData.signals.overall.total_indicators} Total
              </div>
            </div>
          )}

          <div className="text-xs text-center" style={{ color: 'var(--text-muted)' }}>
            Data Points: {indicatorData.data_points} • Asset: {indicatorData.asset}
          </div>
        </div>
      )}

      {!indicatorData && !indicatorError && (
        <div className="text-center py-8" style={{ color: 'var(--text-muted)' }}>
          <p>Click "Calculate Indicators" to analyze technical indicators for the selected asset.</p>
          <p className="text-xs mt-2">Requires minimum 20 data points (candles) to calculate.</p>
        </div>
      )}
    </div>
  );
};

export default IndicatorsPanel;