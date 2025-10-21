import React from 'react';
import PropTypes from 'prop-types';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

/**
 * DataSourceSelector - Component for selecting data source (CSV or Platform)
 */
const DataSourceSelector = ({ dataSource, onDataSourceChange }) => {
  const dataSources = [
    { id: 'csv', name: 'CSV' },
    { id: 'platform', name: 'Platform' },
  ];

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
  };

  return (
    <div style={cardStyle}>
      <h3 style={{
        margin: 0,
        marginBottom: spacing.md,
        fontSize: typography.fontSize.lg,
        fontWeight: typography.fontWeight.semibold,
        color: colors.textPrimary
      }}>
        Data Source
      </h3>
      <div style={{ display: 'flex', gap: spacing.sm }}>
        {dataSources.map(source => (
          <button
            key={source.id}
            onClick={() => onDataSourceChange(source.id)}
            style={{
              flex: 1,
              padding: `${spacing.sm} ${spacing.md}`,
              background: dataSource === source.id ? colors.accentGreen : colors.bgSecondary,
              border: 'none',
              borderRadius: borderRadius.lg,
              fontSize: typography.fontSize.sm,
              fontWeight: typography.fontWeight.semibold,
              color: dataSource === source.id ? '#000' : colors.textPrimary,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            {source.name}
          </button>
        ))}
      </div>
    </div>
  );
};

DataSourceSelector.propTypes = {
  dataSource: PropTypes.string.isRequired,
  onDataSourceChange: PropTypes.func.isRequired,
};

export default DataSourceSelector;