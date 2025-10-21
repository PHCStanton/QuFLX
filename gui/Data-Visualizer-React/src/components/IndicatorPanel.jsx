import React from 'react';
import PropTypes from 'prop-types';
import IndicatorManager from './indicators/IndicatorManager';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

/**
 * IndicatorPanel - Component for managing indicators in the chart
 */
const IndicatorPanel = ({ indicators, onChange }) => {
  return (
    <div style={{
      marginTop: spacing.lg,
      padding: spacing.md,
      background: colors.bgSecondary,
      borderRadius: borderRadius.lg,
      border: `1px solid ${colors.borderPrimary}`
    }}>
      <h3 style={{
        margin: 0,
        marginBottom: spacing.md,
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.semibold,
        color: colors.textPrimary
      }}>
        Indicators
      </h3>

      <IndicatorManager
        indicators={indicators}
        onChange={onChange}
      />
    </div>
  );
};

IndicatorPanel.propTypes = {
  indicators: PropTypes.object.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default IndicatorPanel;