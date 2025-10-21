import React from 'react';
import PropTypes from 'prop-types';
import { colors, typography, spacing, components } from '../styles/designTokens';

/**
 * StatsPanel - Displays price statistics and indicator readings
 * Uses backend-driven indicator values for consistency
 */
const StatsPanel = ({
  chartData,
  indicatorData,
  indicatorError,
  getLatestPrice,
  getPriceChange,
  getVolume,
  getIndicatorReading
}) => {
  const renderIndicatorValue = (reading) => {
    if (!reading) return null;

    const { value, signal, additionalValues } = reading;
    
    let signalColor = colors.textSecondary;
    if (signal === 'BUY') signalColor = colors.success;
    if (signal === 'SELL') signalColor = colors.error;

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.xs }}>
        {/* Primary value and signal */}
        <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
          <span style={{ fontFamily: typography.fontFamily.mono }}>
            {value}
          </span>
          {signal && (
            <span style={{
              color: signalColor,
              fontSize: typography.fontSize.xs,
              fontWeight: typography.fontWeight.medium
            }}>
              {signal}
            </span>
          )}
        </div>

        {/* Additional values */}
        {Object.entries(additionalValues || {}).map(([key, val]) => (
          <div
            key={key}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: spacing.sm,
              fontSize: typography.fontSize.xs,
              color: colors.textSecondary
            }}
          >
            <span style={{ textTransform: 'capitalize' }}>{key}:</span>
            <span style={{ fontFamily: typography.fontFamily.mono }}>{val}</span>
          </div>
        ))}
      </div>
    );
  };

  const renderStatCard = (label, value, error = false) => (
    <div style={{
      padding: spacing.md,
      background: colors.backgroundSecondary,
      borderRadius: components.card.borderRadius,
      border: `1px solid ${error ? colors.error : components.card.border}`
    }}>
      <div style={{
        fontSize: typography.fontSize.xs,
        color: colors.textSecondary,
        marginBottom: spacing.xs
      }}>
        {label}
      </div>
      <div style={{
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.medium,
        color: error ? colors.error : colors.textPrimary,
        fontFamily: typography.fontFamily.mono
      }}>
        {value}
      </div>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
      {/* Quick Stats */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
        <h3 style={{
          margin: 0,
          fontSize: typography.fontSize.sm,
          fontWeight: typography.fontWeight.semibold,
          color: colors.textSecondary,
          textTransform: 'uppercase',
          letterSpacing: '0.05em'
        }}>
          Quick Stats
        </h3>
        
        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
          {renderStatCard('Latest Price', getLatestPrice() || '—')}
          {renderStatCard('Change %', getPriceChange() ? `${getPriceChange()}%` : '—')}
          {renderStatCard('Avg Volume', getVolume() || '—')}
        </div>
      </div>

      {/* Indicator Readings */}
      {(indicatorData?.indicators && Object.keys(indicatorData.indicators).length > 0) && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
          <h3 style={{
            margin: 0,
            fontSize: typography.fontSize.sm,
            fontWeight: typography.fontWeight.semibold,
            color: colors.textSecondary,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
          }}>
            Indicator Readings
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
            {Object.keys(indicatorData.indicators).map(instanceName => {
              const reading = getIndicatorReading(instanceName);
              if (!reading) return null;

              return (
                <div
                  key={instanceName}
                  style={{
                    padding: spacing.md,
                    background: colors.backgroundSecondary,
                    borderRadius: components.card.borderRadius,
                    border: `1px solid ${components.card.border}`
                  }}
                >
                  <div style={{
                    fontSize: typography.fontSize.sm,
                    color: colors.textSecondary,
                    marginBottom: spacing.xs
                  }}>
                    {instanceName}
                  </div>
                  {renderIndicatorValue(reading)}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Error Display */}
      {indicatorError && renderStatCard('Error', indicatorError, true)}
    </div>
  );
};

StatsPanel.propTypes = {
  chartData: PropTypes.array.isRequired,
  indicatorData: PropTypes.object,
  indicatorError: PropTypes.string,
  getLatestPrice: PropTypes.func.isRequired,
  getPriceChange: PropTypes.func.isRequired,
  getVolume: PropTypes.func.isRequired,
  getIndicatorReading: PropTypes.func.isRequired
};

export default StatsPanel;