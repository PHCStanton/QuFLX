import React from 'react';
import PropTypes from 'prop-types';
import MultiPaneChart from './charts/MultiPaneChart';
import ErrorBoundary from './ErrorBoundary';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

/**
 * ChartContainer - Component for displaying the main chart with controls
 */
const ChartContainer = ({
  data,
  indicators,
  backendIndicators,
  height,
  streamActive,
  streamAsset,
  selectedAsset
}) => {
  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    display: 'flex',
    flexDirection: 'column'
  };

  const chartHeight = typeof window !== 'undefined'
    ? Math.max(560, Math.floor(window.innerHeight - 240))
    : 600;

  return (
    <div style={cardStyle}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: spacing.lg
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: spacing.md
        }}>
          <div style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: streamActive ? colors.accentGreen : colors.textSecondary
          }}></div>
          <h2 style={{
            margin: 0,
            fontSize: typography.fontSize.xl,
            fontWeight: typography.fontWeight.bold,
            color: colors.textPrimary
          }}>
            {streamAsset || selectedAsset || 'Select Asset'}
          </h2>
        </div>
        <div style={{ display: 'flex', gap: spacing.sm }}>
          {['⚙️', '📤', '⭐', '←', '↓', '↑', '→', '⊙', '⊚'].map((icon, idx) => (
            <div key={idx} style={{
              fontSize: typography.fontSize.sm,
              color: colors.textSecondary,
              cursor: 'pointer'
            }}>
              {icon}
            </div>
          ))}
        </div>
      </div>

      <div style={{ flex: 1, minHeight: '500px' }}>
        {data.length > 0 ? (
          <ErrorBoundary>
            <MultiPaneChart
              data={data}
              indicators={indicators}
              backendIndicators={backendIndicators}
              height={chartHeight}
            />
          </ErrorBoundary>
        ) : (
          <div style={{
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: colors.bgPrimary,
            borderRadius: borderRadius.lg,
            color: colors.textSecondary,
            fontSize: typography.fontSize.base
          }}>
            Select asset to view chart
          </div>
        )}
      </div>
    </div>
  );
};

ChartContainer.propTypes = {
  data: PropTypes.array.isRequired,
  indicators: PropTypes.object.isRequired,
  backendIndicators: PropTypes.object,
  height: PropTypes.number,
  streamActive: PropTypes.bool,
  streamAsset: PropTypes.string,
  selectedAsset: PropTypes.string
};

export default ChartContainer;