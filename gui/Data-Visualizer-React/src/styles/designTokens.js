/**
 * QuantumFlux Design System
 * Solana-inspired professional trading terminal aesthetic
 */

export const colors = {
  // Primary Backgrounds
  bgPrimary: '#0a0e1a',           // Deep space
  bgSecondary: '#141824',         // Slightly lighter
  cardBg: '#1e293b',              // Card background
  cardBorder: '#334155',          // Subtle borders
  
  // Accents
  accentGreen: '#10b981',         // Primary green (success, buy, CALL)
  accentRed: '#ef4444',           // Primary red (danger, sell, PUT)
  accentBlue: '#3b82f6',          // Info/highlight
  accentPurple: '#8b5cf6',        // Secondary accent
  accentYellow: '#f59e0b',        // Warning/caution
  
  // Text
  textPrimary: '#f8fafc',         // White text
  textSecondary: '#94a3b8',       // Muted text
  textTertiary: '#64748b',        // Very muted
  
  // State Colors
  success: '#10b981',
  error: '#ef4444',
  warning: '#f59e0b',
  info: '#3b82f6',
  
  // Chart Colors
  chartUp: '#10b981',             // Bullish candles
  chartDown: '#ef4444',           // Bearish candles
  chartGrid: '#334155',           // Grid lines
  
  // Opacity variants
  greenAlpha: {
    10: 'rgba(16, 185, 129, 0.1)',
    20: 'rgba(16, 185, 129, 0.2)',
    30: 'rgba(16, 185, 129, 0.3)',
  },
  redAlpha: {
    10: 'rgba(239, 68, 68, 0.1)',
    20: 'rgba(239, 68, 68, 0.2)',
    30: 'rgba(239, 68, 68, 0.3)',
  },
};

export const spacing = {
  xs: '0.25rem',    // 4px
  sm: '0.5rem',     // 8px
  md: '1rem',       // 16px
  lg: '1.5rem',     // 24px
  xl: '2rem',       // 32px
  '2xl': '3rem',    // 48px
  '3xl': '4rem',    // 64px
};

export const typography = {
  fontFamily: {
    sans: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    mono: '"JetBrains Mono", "Fira Code", monospace',
  },
  fontSize: {
    xs: '0.75rem',      // 12px
    sm: '0.875rem',     // 14px
    base: '1rem',       // 16px
    lg: '1.125rem',     // 18px
    xl: '1.25rem',      // 20px
    '2xl': '1.5rem',    // 24px
    '3xl': '1.875rem',  // 30px
    '4xl': '2.25rem',   // 36px
  },
  fontWeight: {
    normal: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },
  lineHeight: {
    tight: 1.25,
    normal: 1.5,
    relaxed: 1.75,
  },
};

export const borderRadius = {
  sm: '0.25rem',    // 4px
  md: '0.5rem',     // 8px
  lg: '0.75rem',    // 12px
  xl: '1rem',       // 16px
  '2xl': '1.5rem',  // 24px
  full: '9999px',
};

export const shadows = {
  sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  glow: {
    green: '0 0 20px rgba(16, 185, 129, 0.3)',
    red: '0 0 20px rgba(239, 68, 68, 0.3)',
    blue: '0 0 20px rgba(59, 130, 246, 0.3)',
  },
};

export const transitions = {
  fast: '150ms ease-in-out',
  normal: '250ms ease-in-out',
  slow: '350ms ease-in-out',
};

export const zIndex = {
  base: 0,
  dropdown: 1000,
  sticky: 1100,
  modal: 1300,
  popover: 1400,
  tooltip: 1500,
};

// Component-specific design tokens
export const components = {
  card: {
    bg: colors.cardBg,
    border: colors.cardBorder,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
    shadow: shadows.md,
  },
  button: {
    primary: {
      bg: colors.accentGreen,
      hoverBg: '#059669',
      text: colors.textPrimary,
      borderRadius: borderRadius.lg,
      padding: `${spacing.sm} ${spacing.lg}`,
    },
    secondary: {
      bg: colors.cardBg,
      hoverBg: colors.cardBorder,
      text: colors.textPrimary,
      borderRadius: borderRadius.lg,
      padding: `${spacing.sm} ${spacing.lg}`,
    },
    danger: {
      bg: colors.accentRed,
      hoverBg: '#dc2626',
      text: colors.textPrimary,
      borderRadius: borderRadius.lg,
      padding: `${spacing.sm} ${spacing.lg}`,
    },
  },
  badge: {
    success: {
      bg: colors.greenAlpha[20],
      text: colors.accentGreen,
      borderRadius: borderRadius.full,
      padding: `${spacing.xs} ${spacing.md}`,
    },
    error: {
      bg: colors.redAlpha[20],
      text: colors.accentRed,
      borderRadius: borderRadius.full,
      padding: `${spacing.xs} ${spacing.md}`,
    },
    info: {
      bg: 'rgba(59, 130, 246, 0.2)',
      text: colors.accentBlue,
      borderRadius: borderRadius.full,
      padding: `${spacing.xs} ${spacing.md}`,
    },
  },
  input: {
    bg: colors.cardBg,
    border: colors.cardBorder,
    focusBorder: colors.accentGreen,
    text: colors.textPrimary,
    placeholder: colors.textTertiary,
    borderRadius: borderRadius.lg,
    padding: `${spacing.sm} ${spacing.md}`,
  },
  modal: {
    overlay: 'rgba(10, 14, 26, 0.8)',
    bg: colors.cardBg,
    border: colors.cardBorder,
    borderRadius: borderRadius.xl,
    padding: spacing.xl,
    shadow: shadows.xl,
  },
};

// Utility function to apply glass effect
export const glassEffect = {
  background: `${colors.cardBg}cc`,  // 80% opacity
  backdropFilter: 'blur(10px)',
  border: `1px solid ${colors.cardBorder}`,
};

export default {
  colors,
  spacing,
  typography,
  borderRadius,
  shadows,
  transitions,
  zIndex,
  components,
  glassEffect,
};
