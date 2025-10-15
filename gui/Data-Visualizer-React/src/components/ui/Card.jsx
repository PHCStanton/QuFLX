import React from 'react';
import PropTypes from 'prop-types';
import { components, glassEffect } from '../../styles/designTokens';

/**
 * Card Component - Container with Solana-inspired glass effect
 */
const Card = ({ 
  children, 
  className = '', 
  glass = false,
  padding = 'default',
  onClick = null,
  style = {}
}) => {
  const paddingMap = {
    none: '0',
    sm: '0.75rem',
    default: components.card.padding,
    lg: '2rem',
  };

  const baseStyle = {
    background: components.card.bg,
    borderRadius: components.card.borderRadius,
    border: `1px solid ${components.card.border}`,
    padding: paddingMap[padding],
    boxShadow: components.card.shadow,
    ...(glass ? glassEffect : {}),
    ...(onClick ? { cursor: 'pointer' } : {}),
    ...style,
  };

  return (
    <div 
      className={`transition-all duration-200 ${className}`}
      style={baseStyle}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

Card.propTypes = {
  children: PropTypes.node.isRequired,
  className: PropTypes.string,
  glass: PropTypes.bool,
  padding: PropTypes.oneOf(['none', 'sm', 'default', 'lg']),
  onClick: PropTypes.func,
  style: PropTypes.object,
};

export default Card;
