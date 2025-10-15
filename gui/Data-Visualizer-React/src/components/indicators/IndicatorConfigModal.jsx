import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Modal from '../ui/Modal';
import { getIndicatorDefinition, createDefaultParams } from '../../constants/indicatorDefinitions';
import { colors, typography, spacing, components } from '../../styles/designTokens';

/**
 * IndicatorConfigModal - Dynamic configuration modal for indicator parameters
 * Generates input fields based on indicator definition
 */
const IndicatorConfigModal = ({ 
  isOpen, 
  onClose, 
  indicatorType, 
  initialParams = null,
  onSave 
}) => {
  const [params, setParams] = useState({});
  const [instanceName, setInstanceName] = useState('');
  const [errors, setErrors] = useState({});

  const definition = getIndicatorDefinition(indicatorType);

  useEffect(() => {
    if (definition) {
      // Initialize with provided params or defaults
      const defaultParams = createDefaultParams(indicatorType);
      setParams(initialParams || defaultParams);
      
      // Generate default instance name (e.g., "SMA-20", "RSI-14")
      if (!initialParams) {
        const primaryParam = definition.parameters[0];
        setInstanceName(`${definition.id.toUpperCase()}-${defaultParams[primaryParam.name]}`);
      }
    }
  }, [indicatorType, initialParams, definition]);

  const handleParamChange = (paramName, value) => {
    setParams(prev => ({
      ...prev,
      [paramName]: parseFloat(value) || 0
    }));
    
    // Update instance name if it's the primary parameter
    if (definition.parameters[0].name === paramName) {
      setInstanceName(`${definition.id.toUpperCase()}-${value}`);
    }
    
    // Clear error for this field
    if (errors[paramName]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[paramName];
        return newErrors;
      });
    }
  };

  const validateParams = () => {
    const newErrors = {};
    
    definition.parameters.forEach(param => {
      const value = params[param.name];
      
      if (value === undefined || value === null || value === '') {
        newErrors[param.name] = 'Required';
      } else if (param.min !== undefined && value < param.min) {
        newErrors[param.name] = `Min: ${param.min}`;
      } else if (param.max !== undefined && value > param.max) {
        newErrors[param.name] = `Max: ${param.max}`;
      }
    });
    
    if (!instanceName.trim()) {
      newErrors.instanceName = 'Instance name is required';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSave = () => {
    if (!validateParams()) {
      return;
    }
    
    onSave({
      type: indicatorType,
      instanceName: instanceName.trim(),
      params,
      definition
    });
    
    onClose();
  };

  if (!definition) return null;

  const footer = (
    <>
      <button
        onClick={onClose}
        style={{
          padding: `${spacing.sm} ${spacing.lg}`,
          background: 'transparent',
          border: `1px solid ${components.button.borderColor}`,
          borderRadius: components.button.borderRadius,
          color: colors.textSecondary,
          fontSize: typography.fontSize.base,
          cursor: 'pointer',
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.target.style.borderColor = colors.textPrimary;
          e.target.style.color = colors.textPrimary;
        }}
        onMouseLeave={(e) => {
          e.target.style.borderColor = components.button.borderColor;
          e.target.style.color = colors.textSecondary;
        }}
      >
        Cancel
      </button>
      <button
        onClick={handleSave}
        style={{
          padding: `${spacing.sm} ${spacing.lg}`,
          background: colors.brandPrimary,
          border: 'none',
          borderRadius: components.button.borderRadius,
          color: colors.textPrimary,
          fontSize: typography.fontSize.base,
          fontWeight: typography.fontWeight.medium,
          cursor: 'pointer',
          transition: 'background 0.2s',
        }}
        onMouseEnter={(e) => {
          e.target.style.background = colors.brandHover;
        }}
        onMouseLeave={(e) => {
          e.target.style.background = colors.brandPrimary;
        }}
      >
        Add Indicator
      </button>
    </>
  );

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Configure ${definition.name}`}
      footer={footer}
      size="default"
    >
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        {/* Description */}
        <p style={{ 
          margin: 0, 
          color: colors.textSecondary, 
          fontSize: typography.fontSize.sm,
          lineHeight: typography.lineHeight.relaxed 
        }}>
          {definition.description}
        </p>

        {/* Instance Name */}
        <div>
          <label
            htmlFor="instance-name"
            style={{
              display: 'block',
              marginBottom: spacing.sm,
              color: colors.textPrimary,
              fontSize: typography.fontSize.sm,
              fontWeight: typography.fontWeight.medium,
            }}
          >
            Instance Name
          </label>
          <input
            id="instance-name"
            type="text"
            value={instanceName}
            onChange={(e) => {
              setInstanceName(e.target.value);
              if (errors.instanceName) {
                setErrors(prev => {
                  const newErrors = { ...prev };
                  delete newErrors.instanceName;
                  return newErrors;
                });
              }
            }}
            placeholder="e.g., SMA-20, RSI-14"
            style={{
              width: '100%',
              padding: spacing.md,
              background: colors.backgroundSecondary,
              border: `1px solid ${errors.instanceName ? colors.error : components.input.border}`,
              borderRadius: components.input.borderRadius,
              color: colors.textPrimary,
              fontSize: typography.fontSize.base,
              outline: 'none',
            }}
            onFocus={(e) => {
              if (!errors.instanceName) {
                e.target.style.borderColor = colors.brandPrimary;
              }
            }}
            onBlur={(e) => {
              if (!errors.instanceName) {
                e.target.style.borderColor = components.input.border;
              }
            }}
          />
          {errors.instanceName && (
            <p style={{ 
              margin: `${spacing.xs} 0 0`, 
              color: colors.error, 
              fontSize: typography.fontSize.xs 
            }}>
              {errors.instanceName}
            </p>
          )}
        </div>

        {/* Parameter Inputs */}
        {definition.parameters.map((param) => (
          <div key={param.name}>
            <label
              htmlFor={`param-${param.name}`}
              style={{
                display: 'block',
                marginBottom: spacing.sm,
                color: colors.textPrimary,
                fontSize: typography.fontSize.sm,
                fontWeight: typography.fontWeight.medium,
              }}
            >
              {param.label}
            </label>
            <input
              id={`param-${param.name}`}
              type="number"
              value={params[param.name] || ''}
              onChange={(e) => handleParamChange(param.name, e.target.value)}
              min={param.min}
              max={param.max}
              step={param.step || 1}
              style={{
                width: '100%',
                padding: spacing.md,
                background: colors.backgroundSecondary,
                border: `1px solid ${errors[param.name] ? colors.error : components.input.border}`,
                borderRadius: components.input.borderRadius,
                color: colors.textPrimary,
                fontSize: typography.fontSize.base,
                outline: 'none',
              }}
              onFocus={(e) => {
                if (!errors[param.name]) {
                  e.target.style.borderColor = colors.brandPrimary;
                }
              }}
              onBlur={(e) => {
                if (!errors[param.name]) {
                  e.target.style.borderColor = components.input.border;
                }
              }}
            />
            {errors[param.name] && (
              <p style={{ 
                margin: `${spacing.xs} 0 0`, 
                color: colors.error, 
                fontSize: typography.fontSize.xs 
              }}>
                {errors[param.name]}
              </p>
            )}
            {(param.min !== undefined || param.max !== undefined) && !errors[param.name] && (
              <p style={{ 
                margin: `${spacing.xs} 0 0`, 
                color: colors.textSecondary, 
                fontSize: typography.fontSize.xs 
              }}>
                {param.min !== undefined && `Min: ${param.min}`}
                {param.min !== undefined && param.max !== undefined && ' • '}
                {param.max !== undefined && `Max: ${param.max}`}
              </p>
            )}
          </div>
        ))}

        {/* Color Preview */}
        <div style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: spacing.md,
          padding: spacing.md,
          background: colors.backgroundSecondary,
          borderRadius: components.card.borderRadius,
        }}>
          <div
            style={{
              width: '24px',
              height: '24px',
              borderRadius: '4px',
              background: definition.color,
            }}
          />
          <span style={{ 
            color: colors.textSecondary, 
            fontSize: typography.fontSize.sm 
          }}>
            Indicator Color
          </span>
        </div>
      </div>
    </Modal>
  );
};

IndicatorConfigModal.propTypes = {
  isOpen: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  indicatorType: PropTypes.string,
  initialParams: PropTypes.object,
  onSave: PropTypes.func.isRequired,
};

export default IndicatorConfigModal;
