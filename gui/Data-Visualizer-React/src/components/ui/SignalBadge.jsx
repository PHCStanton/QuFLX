import React from 'react';
import PropTypes from 'prop-types';
import { components, colors, typography } from '../../styles/designTokens';

/**
 * SignalBadge - Display trading signals (CALL/PUT/NEUTRAL) with confidence
 */
const SignalBadge = ({ 
  signal, 
  confidence = null,
  size = 'default',
  className = ''
}) => {
  const getSignalStyle = (signal) => {
    const normalized = signal.toLowerCase();
    switch (normalized) {
      case 'call':
      case 'buy':
      case 'long':
        return {
          bg: components.badge.success.bg,
          color: components.badge.success.text,
          label: 'CALL',
        };
      case 'put':
      case 'sell':
      case 'short':
        return {
          bg: components.badge.error.bg,
          color: components.badge.error.text,
          label: 'PUT',
        };
      case 'neutral':
      case 'hold':
        return {
          bg: components.badge.info.bg,
          color: components.badge.info.text,
          label: 'NEUTRAL',
        };
      default:
        return {
          bg: components.badge.info.bg,
          color: components.badge.info.text,
          label: signal.toUpperCase(),
        };
    }
  };

  const sizeMap = {
    sm: {
      fontSize: typography.fontSize.xs,
      padding: `${components.badge.success.padding.split(' ')[0]} ${components.badge.success.padding.split(' ')[1]}`,
    },
    default: {
      fontSize: typography.fontSize.sm,
      padding: components.badge.success.padding,
    },
    lg: {
      fontSize: typography.fontSize.base,
      padding: '0.5rem 1.25rem',
    },
  };

  const signalStyle = getSignalStyle(signal);

  return (
    <div 
      className={`inline-flex items-center gap-2 ${className}`}
      style={{
        background: signalStyle.bg,
        color: signalStyle.color,
        borderRadius: components.badge.success.borderRadius,
        padding: sizeMap[size].padding,
        fontSize: sizeMap[size].fontSize,
        fontWeight: typography.fontWeight.semibold,
      }}
    >
      <span>{signalStyle.label}</span>
      {confidence !== null && (
        <span style={{ 
          opacity: 0.8,
          fontSize: typography.fontSize.xs,
        }}>
          {confidence}%
        </span>
      )}
    </div>
  );
};

SignalBadge.propTypes = {
  signal: PropTypes.oneOf(['call', 'put', 'neutral', 'buy', 'sell', 'hold', 'long', 'short']).isRequired,
  confidence: PropTypes.number,
  size: PropTypes.oneOf(['sm', 'default', 'lg']),
  className: PropTypes.string,
};

export default SignalBadge;
