import React from 'react';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';

const SignalItem = ({ signal }) => (
  <div style={{
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: spacing.sm,
    background: colors.bgSecondary,
    borderRadius: borderRadius.lg,
  }}>
    <div style={{ display: 'flex', alignItems: 'center', gap: spacing.sm, flex: 1 }}>
      <div style={{
        width: '6px',
        height: '6px',
        borderRadius: '50%',
        background: signal.color
      }}></div>
      <span style={{
        fontSize: typography.fontSize.xs,
        color: colors.textPrimary
      }}>
        {signal.label}
      </span>
    </div>
    <div style={{
      padding: `${spacing.xs} ${spacing.sm}`,
      background: signal.color,
      borderRadius: borderRadius.md,
      fontSize: typography.fontSize.xs,
      fontWeight: typography.fontWeight.semibold,
      color: '#000',
      minWidth: '40px',
      textAlign: 'center'
    }}>
      {signal.percentage}
    </div>
  </div>
);

const SignalList = ({ signals }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
    {(signals || []).map((signal, idx) => (
      <SignalItem key={signal.label || idx} signal={signal} />
    ))}
  </div>
);

export default SignalList;