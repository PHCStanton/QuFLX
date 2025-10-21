import React from 'react';
import PropTypes from 'prop-types';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

/**
 * AssetSelector - Component for selecting CSV assets
 */
const AssetSelector = ({
  selectedAsset,
  selectedAssetFile,
  availableAssets,
  onAssetChange
}) => {
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
        Asset Selector
      </h3>
      <select
        value={selectedAsset}
        onChange={(e) => {
          const asset = availableAssets.find(a => a.id === e.target.value);
          onAssetChange(e.target.value, asset?.file || '');
        }}
        style={{
          width: '100%',
          padding: spacing.md,
          background: colors.bgSecondary,
          border: `1px solid ${colors.cardBorder}`,
          borderRadius: borderRadius.lg,
          fontSize: typography.fontSize.base,
          color: colors.textPrimary,
          cursor: 'pointer'
        }}
      >
        <option value="">Select Asset</option>
        {availableAssets.map(asset => (
          <option key={asset.id} value={asset.id}>{asset.name}</option>
        ))}
      </select>
    </div>
  );
};

AssetSelector.propTypes = {
  selectedAsset: PropTypes.string.isRequired,
  selectedAssetFile: PropTypes.string,
  availableAssets: PropTypes.arrayOf(PropTypes.shape({
    id: PropTypes.string.isRequired,
    name: PropTypes.string.isRequired,
    file: PropTypes.string
  })).isRequired,
  onAssetChange: PropTypes.func.isRequired,
};

export default AssetSelector;