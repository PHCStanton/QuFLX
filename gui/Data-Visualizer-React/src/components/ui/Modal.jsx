import React, { useEffect } from 'react';
import PropTypes from 'prop-types';
import { components, colors, typography, spacing, zIndex } from '../../styles/designTokens';

/**
 * Modal - Overlay dialog for configurations and confirmations
 */
const Modal = ({ 
  isOpen,
  onClose,
  title,
  children,
  footer = null,
  size = 'default',
  closeOnOverlayClick = true,
}) => {
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  useEffect(() => {
    const handleEscape = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sizeMap = {
    sm: '400px',
    default: '600px',
    lg: '800px',
    xl: '1000px',
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: components.modal.overlay,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: zIndex.modal,
        padding: spacing.lg,
      }}
      onClick={closeOnOverlayClick ? onClose : undefined}
    >
      <div
        style={{
          background: components.modal.bg,
          borderRadius: components.modal.borderRadius,
          border: `1px solid ${components.modal.border}`,
          boxShadow: components.modal.shadow,
          maxWidth: sizeMap[size],
          width: '100%',
          maxHeight: '90vh',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            padding: components.modal.padding,
            borderBottom: `1px solid ${components.modal.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <h2
            style={{
              fontSize: typography.fontSize['2xl'],
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary,
              margin: 0,
            }}
          >
            {title}
          </h2>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: colors.textSecondary,
              fontSize: typography.fontSize['2xl'],
              cursor: 'pointer',
              padding: spacing.xs,
              lineHeight: 1,
              transition: 'color 0.2s',
            }}
            onMouseEnter={(e) => e.target.style.color = colors.textPrimary}
            onMouseLeave={(e) => e.target.style.color = colors.textSecondary}
          >
            ×
          </button>
        </div>

        {/* Body */}
        <div
          style={{
            padding: components.modal.padding,
            overflowY: 'auto',
            flex: 1,
          }}
        >
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div
            style={{
              padding: components.modal.padding,
              borderTop: `1px solid ${components.modal.border}`,
              display: 'flex',
              justifyContent: 'flex-end',
              gap: spacing.md,
            }}
          >
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

Modal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  title: PropTypes.string.isRequired,
  children: PropTypes.node.isRequired,
  footer: PropTypes.node,
  size: PropTypes.oneOf(['sm', 'default', 'lg', 'xl']),
  closeOnOverlayClick: PropTypes.bool,
};

export default Modal;
