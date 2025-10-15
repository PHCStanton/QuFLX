import React, { useState } from 'react';
import PropTypes from 'prop-types';
import IndicatorDropdown from './IndicatorDropdown';
import IndicatorConfigModal from './IndicatorConfigModal';
import { colors, typography, spacing, components } from '../../styles/designTokens';

/**
 * IndicatorManager - Manages multiple indicator instances
 * Supports adding, configuring, and removing indicator instances
 */
const IndicatorManager = ({ indicators, onChange }) => {
  const [selectedIndicator, setSelectedIndicator] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleIndicatorSelect = (indicator) => {
    setSelectedIndicator(indicator.id);
    setIsModalOpen(true);
  };

  const handleIndicatorSave = (config) => {
    const { instanceName, type, params, definition } = config;
    
    // Add new indicator instance
    const newIndicators = {
      ...indicators,
      [instanceName]: {
        type,
        params,
        color: definition.color,
        definition
      }
    };
    
    onChange(newIndicators);
    setIsModalOpen(false);
    setSelectedIndicator(null);
  };

  const handleRemoveIndicator = (instanceName) => {
    const { [instanceName]: removed, ...remaining } = indicators;
    onChange(remaining);
  };

  const handleModalClose = () => {
    setIsModalOpen(false);
    setSelectedIndicator(null);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.md }}>
      {/* Active Indicators List */}
      {Object.keys(indicators).length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
          <h3
            style={{
              margin: 0,
              fontSize: typography.fontSize.sm,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textSecondary,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
            }}
          >
            Active Indicators
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.xs }}>
            {Object.entries(indicators).map(([instanceName, config]) => (
              <div
                key={instanceName}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: spacing.md,
                  background: colors.backgroundSecondary,
                  borderRadius: components.card.borderRadius,
                  border: `1px solid ${components.card.border}`,
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md, flex: 1 }}>
                  {/* Color Indicator */}
                  <div
                    style={{
                      width: '12px',
                      height: '12px',
                      borderRadius: '2px',
                      background: config.color,
                      flexShrink: 0,
                    }}
                  />
                  
                  {/* Instance Name and Type */}
                  <div style={{ flex: 1 }}>
                    <div style={{ 
                      fontSize: typography.fontSize.sm, 
                      fontWeight: typography.fontWeight.medium,
                      color: colors.textPrimary 
                    }}>
                      {instanceName}
                    </div>
                    {config.definition && (
                      <div style={{ 
                        fontSize: typography.fontSize.xs, 
                        color: colors.textSecondary,
                        marginTop: spacing.xs 
                      }}>
                        {config.definition.name}
                      </div>
                    )}
                  </div>
                  
                  {/* Parameters Display */}
                  <div style={{ 
                    fontSize: typography.fontSize.xs, 
                    color: colors.textSecondary,
                    fontFamily: 'monospace'
                  }}>
                    {Object.entries(config.params).map(([key, value]) => (
                      <span key={key} style={{ marginRight: spacing.sm }}>
                        {key}: {value}
                      </span>
                    ))}
                  </div>
                </div>

                {/* Remove Button */}
                <button
                  onClick={() => handleRemoveIndicator(instanceName)}
                  aria-label={`Remove ${instanceName}`}
                  style={{
                    padding: spacing.sm,
                    background: 'transparent',
                    border: 'none',
                    color: colors.textSecondary,
                    fontSize: typography.fontSize.lg,
                    cursor: 'pointer',
                    lineHeight: 1,
                    transition: 'color 0.2s',
                  }}
                  onMouseEnter={(e) => {
                    e.target.style.color = colors.error;
                  }}
                  onMouseLeave={(e) => {
                    e.target.style.color = colors.textSecondary;
                  }}
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Add Indicator Button */}
      <IndicatorDropdown onSelect={handleIndicatorSelect} />

      {/* Configuration Modal */}
      <IndicatorConfigModal
        isOpen={isModalOpen}
        onClose={handleModalClose}
        indicatorType={selectedIndicator}
        onSave={handleIndicatorSave}
      />
    </div>
  );
};

IndicatorManager.propTypes = {
  indicators: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default IndicatorManager;
