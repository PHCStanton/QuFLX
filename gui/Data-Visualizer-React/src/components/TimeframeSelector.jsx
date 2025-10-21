import React from 'react';
import PropTypes from 'prop-types';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

/**
 * TimeframeSelector - Component for selecting chart timeframe
 */
const TimeframeSelector = ({ timeframe, onTimeframeChange }) => {
  const timeframes = ['1m', '5m', '15m', '1h', '4h'];

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
  };

  return (
    <div style={cardStyle}>
      <h3 style={{
        margin: 0,
        marginBottom: spacing.md,
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.semibold,
        color: colors.textPrimary
      }}>
        Timeframe
      </h3>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.sm }}>
        {timeframes.map(tf => (
          <button
            key={tf}
            onClick={() => onTimeframeChange(tf)}
            style={{
              padding: `${spacing.sm} ${spacing.md}`,
              background: timeframe === tf ? colors.accentGreen : colors.bgSecondary,
              border: 'none',
              borderRadius: borderRadius.lg,
              fontSize: typography.fontSize.sm,
              fontWeight: typography.fontWeight.semibold,
              color: timeframe === tf ? '#000' : colors.textPrimary,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {tf}
          </button>
        ))}
      </div>
    </div>
  );
};

TimeframeSelector.propTypes = {
  timeframe: PropTypes.string.isRequired,
  onTimeframeChange: PropTypes.func.isRequired,
};

export default TimeframeSelector;