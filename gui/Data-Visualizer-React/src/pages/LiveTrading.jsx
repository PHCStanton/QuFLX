import React, { useState } from 'react';
import { colors, typography, spacing, borderRadius } from '../styles/designTokens';
import { useResponsiveGrid } from '../hooks/useResponsiveGrid';
import PositionList from '../components/PositionList';
import SignalList from '../components/SignalList';
import { useWebSocket } from '../hooks/useWebSocketV2';
import ErrorBoundary from '../components/ErrorBoundary';
import MultiPaneChart from '../components/charts/MultiPaneChart';
import { Link } from 'react-router-dom';

const LiveTrading = () => {
  const gridColumns = useResponsiveGrid();
  // Invoke WebSocket hook to access connection, stream, and live data
  const { connection, stream, data } = useWebSocket();
  const streamActive = stream?.isActive;
  const streamAsset = stream?.currentAsset;

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
              background: streamActive ? colors.accentGreen : colors.textSecondary
            }}></div>
            <h2 style={{
              margin: 0,
              fontSize: typography.fontSize.xl,
              fontWeight: typography.fontWeight.bold,
              color: colors.textPrimary
            }}>
              {streamAsset || 'Live'}
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

        {/* Inserted info banner to enforce separation of concerns */}
        <div style={{
          background: colors.bgSecondary,
          border: `1px dashed ${colors.cardBorder}`,
          borderRadius: borderRadius.md,
          padding: spacing.sm,
          marginBottom: spacing.md,
          color: colors.textSecondary
        }}>
          Live controls (Detect Asset, Start Stream, Add Indicators) are managed in the Data Analysis tab.
          <span style={{ marginLeft: spacing.sm }}>
            <Link to="/" style={{
              padding: `${spacing.xs} ${spacing.sm}`,
              background: colors.accentGreen,
              borderRadius: borderRadius.md,
              color: '#000',
              textDecoration: 'none',
              fontWeight: typography.fontWeight.semibold
            }}>
              Open Data Analysis →
            </Link>
          </span>
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
          color: colors.textSecondary,
          padding: spacing.sm
        }}>
          {data?.current?.length > 0 ? (
            <ErrorBoundary>
              <MultiPaneChart
                data={data.current}
                backendIndicators={data.indicators?.data}
                height={centerChartMinHeight}
              />
            </ErrorBoundary>
          ) : (
            <div style={{ textAlign: 'center' }}>
              Live chart will appear when stream starts
            </div>
          )}
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
            gridTemplateColumns: 'auto 1fr auto auto auto',
            gap: spacing.md,
            padding: spacing.sm,
            background: colors.bgSecondary,
            borderRadius: borderRadius.lg,
            fontSize: typography.fontSize.xs,
            color: colors.textSecondary,
            marginTop: spacing.sm
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
        </div>
      </div>

      {/* RIGHT COLUMN - Live Signal Panel */}
      <div style={{ ...cardStyle, display: 'flex', flexDirection: 'column', gap: spacing.lg }}>
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
            Live Signal Panel
          </h3>
          <div style={{ display: 'flex', gap: spacing.sm }}>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>⚙️</div>
            <div style={{ fontSize: typography.fontSize.sm, color: colors.textSecondary }}>♻️</div>
          </div>
        </div>

        {/* Confidence score */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'auto 1fr auto',
          gap: spacing.md,
          alignItems: 'center'
        }}>
          <div style={{
            width: '8px',
            height: '100%',
            background: colors.accentGreen,
            borderRadius: borderRadius.md
          }}></div>
          <div style={{
            fontSize: typography.fontSize.xs,
            color: colors.textSecondary
          }}>
            Confidence: 45% +10%
          </div>
          <button style={{
            padding: `${spacing.xs} ${spacing.md}`,
            background: colors.accentGreen,
            border: 'none',
            borderRadius: borderRadius.md,
            color: '#000',
            fontWeight: typography.fontWeight.semibold,
            cursor: 'pointer'
          }}>
            EXECUTE TRADE
          </button>
        </div>

        {/* Indicator readings */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: spacing.md
        }}>
          <div style={{
            background: colors.bgSecondary,
            borderRadius: borderRadius.lg,
            padding: spacing.md
          }}>
            <h4 style={{
              margin: 0,
              marginBottom: spacing.sm,
              fontSize: typography.fontSize.md,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>RSI</h4>
            <div style={{
              height: '80px',
              background: colors.bgPrimary,
              borderRadius: borderRadius.md,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.textSecondary,
              fontSize: typography.fontSize.xs
            }}>
              RSI Chart
            </div>
          </div>

          <div style={{
            background: colors.bgSecondary,
            borderRadius: borderRadius.lg,
            padding: spacing.md
          }}>
            <h4 style={{
              margin: 0,
              marginBottom: spacing.sm,
              fontSize: typography.fontSize.md,
              fontWeight: typography.fontWeight.semibold,
              color: colors.textPrimary
            }}>MACD</h4>
            <div style={{
              height: '80px',
              background: colors.bgPrimary,
              borderRadius: borderRadius.md,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: colors.textSecondary,
              fontSize: typography.fontSize.xs
            }}>
              MACD Chart
            </div>
          </div>
        </div>

        {/* Info */}
        <div style={{
          background: colors.bgSecondary,
          borderRadius: borderRadius.lg,
          padding: spacing.md,
          fontSize: typography.fontSize.xs,
          color: colors.textSecondary
        }}>
          <div>Executed: 0 | Fail: 25 | Interest: 9.50%</div>
          <div>RSI: 82.52 | MACD: 0.014</div>
        </div>
      </div>
    </div>
  );
};

export default LiveTrading;
