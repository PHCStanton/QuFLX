import React, { memo } from 'react';
import PropTypes from 'prop-types';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

/**
 * PlatformModeControls - Component for platform mode streaming controls
 * Uses simplified state management through useLiveMode hook
 */
const PlatformModeControls = memo(({
  canEnterLiveMode,
  isStreamReady,
  isStreaming,
  detectedAsset,
  onDetectAsset,
  onStartStream,
  onStopStream
}) => {
  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg
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
        Platform Mode
      </h3>

      {!canEnterLiveMode && (
        <div style={{
          padding: spacing.md,
          background: colors.accentRed,
          borderRadius: borderRadius.lg,
          fontSize: typography.fontSize.sm,
          color: '#000',
          fontWeight: typography.fontWeight.semibold,
          textAlign: 'center'
        }}>
          Chrome not connected
        </div>
      )}

      {canEnterLiveMode && !detectedAsset && !isStreaming && (
        <button
          onClick={onDetectAsset}
          style={{
            width: '100%',
            padding: spacing.md,
            background: colors.accentGreen,
            border: 'none',
            borderRadius: borderRadius.lg,
            fontSize: typography.fontSize.base,
            fontWeight: typography.fontWeight.bold,
            color: '#000',
            cursor: 'pointer'
          }}
          disabled={!isStreamReady}
        >
          Detect Asset
        </button>
      )}

      {detectedAsset && !isStreaming && (
        <div>
          <div style={{
            padding: spacing.md,
            background: colors.bgSecondary,
            borderRadius: borderRadius.lg,
            marginBottom: spacing.sm,
            fontSize: typography.fontSize.sm,
            color: colors.textPrimary
          }}>
            Detected: {detectedAsset.asset}
          </div>
          <button
            onClick={onStartStream}
            style={{
              width: '100%',
              padding: spacing.md,
              background: colors.accentGreen,
              border: 'none',
              borderRadius: borderRadius.lg,
              fontSize: typography.fontSize.base,
              fontWeight: typography.fontWeight.bold,
              color: '#000',
              cursor: 'pointer'
            }}
          >
            Start Stream
          </button>
        </div>
      )}

      {isStreaming && (
        <button
          onClick={onStopStream}
          style={{
            width: '100%',
            padding: spacing.md,
            background: colors.accentRed,
            border: 'none',
            borderRadius: borderRadius.lg,
            fontSize: typography.fontSize.base,
            fontWeight: typography.fontWeight.bold,
            color: '#000',
            cursor: 'pointer'
          }}
        >
          Stop Stream
        </button>
      )}
    </div>
  );
});

PlatformModeControls.propTypes = {
  canEnterLiveMode: PropTypes.bool.isRequired,
  isStreamReady: PropTypes.bool.isRequired,
  isStreaming: PropTypes.bool.isRequired,
  detectedAsset: PropTypes.object,
  onDetectAsset: PropTypes.func.isRequired,
  onStartStream: PropTypes.func.isRequired,
  onStopStream: PropTypes.func.isRequired
};

PlatformModeControls.displayName = 'PlatformModeControls';

export default PlatformModeControls;