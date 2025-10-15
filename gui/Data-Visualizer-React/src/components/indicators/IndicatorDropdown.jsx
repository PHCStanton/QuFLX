import React, { useState, useRef, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getIndicatorsByCategory, INDICATOR_CATEGORIES } from '../../constants/indicatorDefinitions';
import { colors, typography, spacing, components } from '../../styles/designTokens';

/**
 * IndicatorDropdown - Categorized dropdown for selecting indicator types
 * Supports keyboard navigation and accessibility
 */
const IndicatorDropdown = ({ onSelect, buttonLabel = 'Add Indicator' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const dropdownRef = useRef(null);
  const searchInputRef = useRef(null);
  const buttonRef = useRef(null);

  const indicatorsByCategory = getIndicatorsByCategory();

  // Filter indicators based on search term
  const filteredCategories = Object.entries(indicatorsByCategory).reduce((acc, [category, indicators]) => {
    const filtered = indicators.filter(ind =>
      ind.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ind.description.toLowerCase().includes(searchTerm.toLowerCase())
    );
    if (filtered.length > 0) {
      acc[category] = filtered;
    }
    return acc;
  }, {});

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
        setSearchTerm('');
      }
    };

    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
        setSearchTerm('');
        buttonRef.current?.focus();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  useEffect(() => {
    if (isOpen && searchInputRef.current) {
      setTimeout(() => searchInputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  const handleIndicatorSelect = (indicator) => {
    onSelect(indicator);
    setIsOpen(false);
    setSearchTerm('');
    buttonRef.current?.focus();
  };

  const handleToggle = () => {
    setIsOpen(!isOpen);
    setSearchTerm('');
  };

  return (
    <div ref={dropdownRef} style={{ position: 'relative' }}>
      <button
        ref={buttonRef}
        onClick={handleToggle}
        aria-expanded={isOpen}
        aria-haspopup="true"
        style={{
          padding: `${spacing.sm} ${spacing.md}`,
          background: colors.brandPrimary,
          color: colors.textPrimary,
          border: 'none',
          borderRadius: components.card.borderRadius,
          fontSize: typography.fontSize.base,
          fontWeight: typography.fontWeight.medium,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: spacing.sm,
          transition: 'all 0.2s',
        }}
        onMouseEnter={(e) => {
          e.target.style.background = colors.brandHover;
        }}
        onMouseLeave={(e) => {
          e.target.style.background = colors.brandPrimary;
        }}
      >
        <span>+</span>
        <span>{buttonLabel}</span>
      </button>

      {isOpen && (
        <div
          role="menu"
          style={{
            position: 'absolute',
            top: 'calc(100% + 8px)',
            left: 0,
            zIndex: 1000,
            background: components.dropdown.bg,
            border: `1px solid ${components.dropdown.border}`,
            borderRadius: components.dropdown.borderRadius,
            boxShadow: components.dropdown.shadow,
            minWidth: '320px',
            maxHeight: '480px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Search Input */}
          <div style={{ padding: spacing.md, borderBottom: `1px solid ${components.dropdown.border}` }}>
            <input
              ref={searchInputRef}
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search indicators..."
              aria-label="Search indicators"
              style={{
                width: '100%',
                padding: `${spacing.sm} ${spacing.md}`,
                background: colors.backgroundSecondary,
                border: `1px solid ${components.input.border}`,
                borderRadius: components.input.borderRadius,
                color: colors.textPrimary,
                fontSize: typography.fontSize.sm,
                outline: 'none',
              }}
              onFocus={(e) => {
                e.target.style.borderColor = colors.brandPrimary;
              }}
              onBlur={(e) => {
                e.target.style.borderColor = components.input.border;
              }}
            />
          </div>

          {/* Categorized Indicators List */}
          <div style={{ overflowY: 'auto', flex: 1 }}>
            {Object.keys(filteredCategories).length === 0 ? (
              <div style={{ padding: spacing.lg, textAlign: 'center', color: colors.textSecondary }}>
                No indicators found
              </div>
            ) : (
              Object.entries(filteredCategories).map(([category, indicators]) => (
                <div key={category} style={{ marginBottom: spacing.xs }}>
                  {/* Category Header */}
                  <div
                    style={{
                      padding: `${spacing.sm} ${spacing.md}`,
                      background: colors.backgroundSecondary,
                      color: colors.textSecondary,
                      fontSize: typography.fontSize.xs,
                      fontWeight: typography.fontWeight.semibold,
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em',
                    }}
                  >
                    {category}
                  </div>

                  {/* Category Indicators */}
                  {indicators.map((indicator) => (
                    <button
                      key={indicator.id}
                      role="menuitem"
                      onClick={() => handleIndicatorSelect(indicator)}
                      style={{
                        width: '100%',
                        padding: spacing.md,
                        background: 'transparent',
                        border: 'none',
                        textAlign: 'left',
                        cursor: 'pointer',
                        transition: 'background 0.2s',
                        color: colors.textPrimary,
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.background = colors.backgroundSecondary;
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.background = 'transparent';
                      }}
                    >
                      <div style={{ fontSize: typography.fontSize.sm, fontWeight: typography.fontWeight.medium }}>
                        {indicator.name}
                      </div>
                      <div
                        style={{
                          fontSize: typography.fontSize.xs,
                          color: colors.textSecondary,
                          marginTop: spacing.xs,
                        }}
                      >
                        {indicator.description}
                      </div>
                    </button>
                  ))}
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

IndicatorDropdown.propTypes = {
  onSelect: PropTypes.func.isRequired,
  buttonLabel: PropTypes.string,
};

export default IndicatorDropdown;
