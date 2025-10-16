import React from 'react';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

const PositionItem = ({ position }) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.sm,
    background: colors.bgSecondary,
    borderRadius: borderRadius.lg,
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm }}>
      <div style={{
        width: '8px',
        height: '8px',
        borderRadius: '50%',
        background: position.color
      }}></div>
      <span style={{
        fontSize: typography.fontSize.sm,
        color: colors.textPrimary
      }}>
        {position.label}
      </span>
    </div>
    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.md }}>
      <span style={{
        fontSize: typography.fontSize.sm,
        color: colors.textSecondary
      }}>
        {position.value}
      </span>
      <div style={{
        padding: `${spacing.xs} ${spacing.sm}`,
        background: position.color,
        borderRadius: borderRadius.md,
        fontSize: typography.fontSize.xs,
        fontWeight: typography.fontWeight.semibold,
        color: '#000',
        minWidth: '45px',
        textAlign: 'center'
      }}>
        {position.percentage}
      </div>
    </div>
  </div>
);

const PositionList = ({ positions }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
    {positions.map((position, idx) => (
      <PositionItem key={idx} position={position} />
    ))}
  </div>
);

export default PositionList;