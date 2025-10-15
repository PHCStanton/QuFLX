import React, { useEffect, useRef, useId } from 'react';
import PropTypes from 'prop-types';
import { components, colors, typography, spacing, zIndex } from '../../styles/designTokens';

/**
 * Modal - Overlay dialog for configurations and confirmations
 * Implements ARIA best practices and focus management
 */
const Modal = ({ 
  isOpen,
  onClose,
  title,
  children,
  footer = null,
  size = 'default',
  closeOnOverlayClick = true,
  ariaDescribedBy = null,
}) => {
  const modalRef = useRef(null);
  const closeButtonRef = useRef(null);
  const previousActiveElement = useRef(null);
  const uniqueId = useId();
  const titleId = `modal-title-${uniqueId}`;

  useEffect(() => {
    if (isOpen) {
      previousActiveElement.current = document.activeElement;
      document.body.style.overflow = 'hidden';
      
      setTimeout(() => {
        if (closeButtonRef.current) {
          closeButtonRef.current.focus();
        }
      }, 0);
    } else {
      document.body.style.overflow = 'unset';
      
      if (previousActiveElement.current && previousActiveElement.current.focus) {
        previousActiveElement.current.focus();
      }
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

    const handleTab = (e) => {
      if (!isOpen || !modalRef.current) return;

      const focusableElements = modalRef.current.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      const firstElement = focusableElements[0];
      const lastElement = focusableElements[focusableElements.length - 1];

      if (e.key === 'Tab') {
        if (e.shiftKey && document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        } else if (!e.shiftKey && document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    document.addEventListener('keydown', handleEscape);
    document.addEventListener('keydown', handleTab);
    
    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('keydown', handleTab);
    };
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
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
      {...(ariaDescribedBy ? { 'aria-describedby': ariaDescribedBy } : {})}
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
        ref={modalRef}
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
            id={titleId}
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
            ref={closeButtonRef}
            onClick={onClose}
            aria-label="Close modal"
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
  ariaDescribedBy: PropTypes.string,
};

export default Modal;
