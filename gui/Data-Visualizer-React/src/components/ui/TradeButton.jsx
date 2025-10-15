import React, { useState } from 'react';
import PropTypes from 'prop-types';
import { components, colors, typography, transitions } from '../../styles/designTokens';

/**
 * TradeButton - Primary action button with hover states and loading support
 */
const TradeButton = ({ 
  children,
  onClick,
  variant = 'primary',
  size = 'default',
  disabled = false,
  loading = false,
  fullWidth = false,
  className = '',
  icon = null,
}) => {
  const [isHovered, setIsHovered] = useState(false);

  const variantStyles = {
    primary: {
      bg: components.button.primary.bg,
      hoverBg: components.button.primary.hoverBg,
      text: components.button.primary.text,
    },
    secondary: {
      bg: components.button.secondary.bg,
      hoverBg: components.button.secondary.hoverBg,
      text: components.button.secondary.text,
    },
    danger: {
      bg: components.button.danger.bg,
      hoverBg: components.button.danger.hoverBg,
      text: components.button.danger.text,
    },
  };

  const sizeMap = {
    sm: {
      fontSize: typography.fontSize.sm,
      padding: '0.375rem 1rem',
    },
    default: {
      fontSize: typography.fontSize.base,
      padding: components.button.primary.padding,
    },
    lg: {
      fontSize: typography.fontSize.lg,
      padding: '0.75rem 2rem',
    },
  };

  const style = variantStyles[variant];
  const sizeStyle = sizeMap[size];

  return (
    <button
      className={`transition-all duration-200 ${className}`}
      style={{
        background: disabled ? colors.textTertiary : (isHovered ? style.hoverBg : style.bg),
        color: style.text,
        fontSize: sizeStyle.fontSize,
        fontWeight: typography.fontWeight.semibold,
        padding: sizeStyle.padding,
        borderRadius: components.button.primary.borderRadius,
        border: 'none',
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.5 : 1,
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '0.5rem',
        width: fullWidth ? '100%' : 'auto',
        transition: transitions.normal,
      }}
      onClick={disabled || loading ? undefined : onClick}
      onMouseEnter={() => !disabled && !loading && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      disabled={disabled || loading}
    >
      {loading && (
        <div 
          style={{
            width: '1rem',
            height: '1rem',
            border: `2px solid ${style.text}`,
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
      )}
      {icon && !loading && <span>{icon}</span>}
      {children}
    </button>
  );
};

TradeButton.propTypes = {
  children: PropTypes.node.isRequired,
  onClick: PropTypes.func,
  variant: PropTypes.oneOf(['primary', 'secondary', 'danger']),
  size: PropTypes.oneOf(['sm', 'default', 'lg']),
  disabled: PropTypes.bool,
  loading: PropTypes.bool,
  fullWidth: PropTypes.bool,
  className: PropTypes.string,
  icon: PropTypes.node,
};

export default TradeButton;
