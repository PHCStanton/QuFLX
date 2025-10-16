import React, { useState } from 'react';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';
import { useResponsiveGrid } from '../hooks/useResponsiveGrid';
import PositionList from '../components/PositionList';
import SignalList from '../components/SignalList';

const LiveTrading = () => {
  const gridColumns = useResponsiveGrid();

  const cardStyle = {
    background: colors.cardBg,
    border: `1px solid ${colors.cardBorder}`,
    borderRadius: borderRadius.xl,
    padding: spacing.lg,
  };

  const containerStyle = {
    display: 'grid',
    gridTemplateColumns: gridColumns,
    gap: spacing.md,
    padding: `${spacing.md} ${spacing.lg}`,
    minHeight: 'calc(100vh - 120px)',
  };

  // Center chart height scales with viewport to maximize space
  const centerChartMinHeight = typeof window !== 'undefined'
    ? Math.max(480, Math.floor(window.innerHeight - 360))
    : 480;

  return (
    <div style={containerStyle}>
      {/* LEFT COLUMN - Active Positions & Signal Monitor */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
        {/* Active Positions */}
        <div style={cardStyle}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: spacing.lg
          }}>
            <h3 style={{
              margin: 0,
              fontSize: typography.fontSize.lg,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>
              Active Positions
            </h3>
            <div style={{ display: 'flex', gap: spacing.sm }}>
              <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>⚙️</div>
              <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>♻️</div>
            </div>
          </div>

          <PositionList positions={[
            { label: 'Open 196', value: '29007', percentage: '90%', color: colors.accentGreen },
            { label: 'Open 141', value: '6922', percentage: '91%', color: colors.accentRed },
            { label: 'Open 181', value: '4904', percentage: '104%', color: colors.accentRed },
            { label: 'Open rollit', value: '4903', percentage: '95%', color: colors.accentRed }
          ]} />
        </div>

        {/* Signal Monitor */}
        <div style={cardStyle}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: spacing.lg
          }}>
            <h3 style={{
              margin: 0,
              fontSize: typography.fontSize.lg,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>
              Signal Monitor
            </h3>
            <div style={{ display: 'flex', gap: spacing.sm }}>
              <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>⚙️</div>
              <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>♻️</div>
            </div>
          </div>

          <SignalList signals={[
            { label: 'Pgilen Trader', chart: true, percentage: '96%', color: colors.accentGreen },
            { label: 'Trien klepoit', chart: true, percentage: '96%', color: colors.accentGreen },
            { label: 'L:erd BeIS', chart: true, percentage: '35%', color: colors.accentGreen },
            { label: 'Opaerted', chart: true, percentage: '5%', color: colors.accentRed },
            { label: 'L:ail:1.26', chart: true, percentage: '15%', color: colors.accentRed },
            { label: 'Open 9,4', chart: true, percentage: '5%', color: colors.accentGreen }
          ]} />

          {/* Mini candlestick chart placeholder */}
          <div style={{
            marginTop: spacing.md,
            height: '60px',
            background: colors.bgPrimary,
            borderRadius: borderRadius.lg,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: typography.fontSize.xs,
            color: colors.textSecondary
          }}>
            Mini Chart
          </div>
        </div>
      </div>

      {/* CENTER COLUMN - Live Chart */}
      <div style={{ ...cardStyle, display: 'flex', flexDirection: 'column' }}>
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
              background: colors.accentGreen
            }}></div>
            <h2 style={{
              margin: 0,
              fontSize: typography.fontSize.xl,
              fontWeight: typography.fontWeight.bold,
              color: colors.textPrimary
            }}>
              CAMER
            </h2>
          </div>
          <div style={{ display: 'flex', gap: spacing.sm }}>
            {/* Chart controls */}
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

        {/* Chart area */}
        <div style={{
          flex: 1,
          background: colors.bgPrimary,
          borderRadius: borderRadius.lg,
          minHeight: `${centerChartMinHeight}px`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: colors.textSecondary
        }}>
          Live Chart Placeholder (integrate MultiPaneChart here)
        </div>

        {/* Recent Trades */}
        <div style={{ marginTop: spacing.lg }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: spacing.md
          }}>
            <h3 style={{
              margin: 0,
              fontSize: typography.fontSize.lg,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>
              Recent Trades
            </h3>
            <div style={{ display: 'flex', gap: spacing.sm }}>
              <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>⚙️</div>
              <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>📤</div>
            </div>
          </div>

          {/* Trades table */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr auto auto auto',
            gap: spacing.md,
            padding: spacing.sm,
            background: colors.bgSecondary,
            borderRadius: borderRadius.lg,
            fontSize: typography.fontSize.xs,
            color: colors.textSecondary
          }}>
            <div>01e293b</div>
            <div></div>
            <div style={{
              padding: `${spacing.xs} ${spacing.sm}`,
              background: colors.accentGreen,
              borderRadius: borderRadius.md,
              color: '#000',
              fontWeight: typography.fontWeight.semibold
            }}>
              BUY
            </div>
            <div style={{
              padding: `${spacing.xs} ${spacing.sm}`,
              background: colors.accentRed,
              borderRadius: borderRadius.md,
              color: '#000',
              fontWeight: typography.fontWeight.semibold
            }}>
              SUL
            </div>
            <div>Actfns</div>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr auto',
            gap: spacing.md,
            padding: spacing.sm,
            background: colors.bgSecondary,
            borderRadius: borderRadius.lg,
            fontSize: typography.fontSize.xs,
            color: colors.textSecondary,
            marginTop: spacing.sm
          }}>
            {['02:002710938', '02:002710928'].map((id, idx) => (
              <React.Fragment key={idx}>
                <div>{id}</div>
                <div style={{
                  display: 'flex',
                  gap: spacing.sm
                }}>
                  <div style={{
                    padding: `${spacing.xs} ${spacing.sm}`,
                    background: colors.accentGreen,
                    borderRadius: borderRadius.md,
                    color: '#000',
                    fontWeight: typography.fontWeight.semibold
                  }}>
                    BUY
                  </div>
                  <div style={{
                    padding: `${spacing.xs} ${spacing.sm}`,
                    background: colors.accentRed,
                    borderRadius: borderRadius.md,
                    color: '#000',
                    fontWeight: typography.fontWeight.semibold
                  }}>
                    SELL
                  </div>
                </div>
                <div>#ef4444</div>
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* RIGHT COLUMN - Live Signal Panel */}
      <div style={{ ...cardStyle, display: 'flex', flexDirection: 'column' }}>
        <h3 style={{
          margin: 0,
          marginBottom: spacing.lg,
          fontSize: typography.fontSize.xl,
          fontWeight: typography.fontWeight.semibold,
          color: colors.textPrimary
        }}>
          Live Signal Panel
        </h3>

        {/* Confidence */}
        <div style={{
          textAlign: 'center',
          padding: spacing.xl,
          background: colors.bgSecondary,
          borderRadius: borderRadius.xl,
          marginBottom: spacing.lg
        }}>
          <div style={{
            fontSize: typography.fontSize.sm,
            color: colors.textSecondary,
            marginBottom: spacing.sm
          }}>
            Confidence
          </div>
          <div style={{
            fontSize: '4rem',
            fontWeight: typography.fontWeight.bold,
            color: colors.textPrimary,
            marginBottom: spacing.md
          }}>
            87%
          </div>
          <div style={{
            fontSize: typography.fontSize['2xl'],
            fontWeight: typography.fontWeight.bold,
            color: colors.textPrimary,
            marginBottom: spacing.lg
          }}>
            CALL
          </div>

          {/* Indicator readings */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: spacing.md
          }}>
            <div style={{
              fontSize: typography.fontSize.sm,
              color: colors.textSecondary
            }}>
              RSI: 68
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: spacing.xs
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: colors.accentRed
              }}></div>
              <span style={{
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary
              }}>
                179%
              </span>
            </div>
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            marginBottom: spacing.lg
          }}>
            <div style={{
              fontSize: typography.fontSize.sm,
              color: colors.textSecondary
            }}>
              MACD: Bullish
            </div>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: spacing.xs
            }}>
              <div style={{
                width: '8px',
                height: '8px',
                borderRadius: '50%',
                background: colors.accentGreen
              }}></div>
              <span style={{
                fontSize: typography.fontSize.sm,
                color: colors.textSecondary
              }}>
                179%
              </span>
            </div>
          </div>

          {/* Waveform visualization */}
          <div style={{
            height: '60px',
            background: colors.bgPrimary,
            borderRadius: borderRadius.lg,
            marginBottom: spacing.lg,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <svg width="280" height="40" style={{ overflow: 'visible' }}>
              <path
                d="M 0,20 Q 35,10 70,20 T 140,20 T 210,20 T 280,20"
                stroke={colors.accentGreen}
                strokeWidth="2"
                fill="none"
              />
            </svg>
          </div>

          {/* Execute button */}
          <button style={{
            width: '100%',
            padding: spacing.lg,
            background: colors.accentGreen,
            border: 'none',
            borderRadius: borderRadius.lg,
            fontSize: typography.fontSize.base,
            fontWeight: typography.fontWeight.bold,
            color: '#000',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.background = colors.brandHover}
          onMouseLeave={(e) => e.target.style.background = colors.accentGreen}
          >
            EXECUTE TRADE
          </button>
        </div>
      </div>
    </div>
  );
};

export default LiveTrading;
