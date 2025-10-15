import React from 'react';
import PropTypes from 'prop-types';
import { colors, typography, spacing } from '../../styles/designTokens';

/**
 * MetricDisplay - Display key metrics with label and value
 */
const MetricDisplay = ({ 
  label, 
  value, 
  change = null,
  size = 'default',
  mono = false,
  className = ''
}) => {
  const sizeMap = {
    sm: {
      label: typography.fontSize.xs,
      value: typography.fontSize.lg,
    },
    default: {
      label: typography.fontSize.sm,
      value: typography.fontSize['2xl'],
    },
    lg: {
      label: typography.fontSize.base,
      value: typography.fontSize['3xl'],
    },
  };

  const getChangeColor = (change) => {
    if (!change) return null;
    const numChange = typeof change === 'string' ? parseFloat(change) : change;
    return numChange >= 0 ? colors.accentGreen : colors.accentRed;
  };

  return (
    <div className={className}>
      <div 
        style={{ 
          fontSize: sizeMap[size].label,
          color: colors.textSecondary,
          marginBottom: spacing.xs,
        }}
      >
        {label}
      </div>
      <div 
        style={{ 
          fontSize: sizeMap[size].value,
          fontWeight: typography.fontWeight.bold,
          color: colors.textPrimary,
          fontFamily: mono ? typography.fontFamily.mono : typography.fontFamily.sans,
          display: 'flex',
          alignItems: 'center',
          gap: spacing.sm,
        }}
      >
        {value}
        {change !== null && (
          <span 
            style={{ 
              fontSize: sizeMap[size].label,
              color: getChangeColor(change),
              fontWeight: typography.fontWeight.medium,
            }}
          >
            {typeof change === 'number' && change > 0 ? '+' : ''}{change}
            {typeof change === 'string' && !change.includes('%') ? '%' : ''}
          </span>
        )}
      </div>
    </div>
  );
};

MetricDisplay.propTypes = {
  label: PropTypes.string.isRequired,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  change: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  size: PropTypes.oneOf(['sm', 'default', 'lg']),
  mono: PropTypes.bool,
  className: PropTypes.string,
};

export default MetricDisplay;
