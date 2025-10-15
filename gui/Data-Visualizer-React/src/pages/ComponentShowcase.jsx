import React, { useState } from 'react';
import { Card, MetricDisplay, SignalBadge, TradeButton, Modal } from '../components/ui';
import { colors, spacing } from '../styles/designTokens';

/**
 * ComponentShowcase - Demo page for testing new UI components
 */
const ComponentShowcase = () => {
  const [modalOpen, setModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleButtonClick = () => {
    setLoading(true);
    setTimeout(() => setLoading(false), 2000);
  };

  return (
    <div style={{ 
      background: colors.bgPrimary, 
      minHeight: '100vh',
      padding: spacing['2xl'],
    }}>
      <h1 style={{ 
        color: colors.textPrimary,
        fontSize: '2.5rem',
        fontWeight: 600,
        marginBottom: spacing['2xl'],
      }}>
        QuantumFlux Component Library
      </h1>

      {/* Cards Section */}
      <section style={{ marginBottom: spacing['3xl'] }}>
        <h2 style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>Cards</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: spacing.lg }}>
          <Card>
            <h3 style={{ color: colors.textPrimary, marginBottom: spacing.sm }}>Standard Card</h3>
            <p style={{ color: colors.textSecondary }}>Clean card design with default padding</p>
          </Card>
          
          <Card glass>
            <h3 style={{ color: colors.textPrimary, marginBottom: spacing.sm }}>Glass Effect Card</h3>
            <p style={{ color: colors.textSecondary }}>Frosted glass aesthetic with backdrop blur</p>
          </Card>
          
          <Card padding="lg" onClick={() => alert('Clicked!')}>
            <h3 style={{ color: colors.textPrimary, marginBottom: spacing.sm }}>Clickable Card</h3>
            <p style={{ color: colors.textSecondary }}>Large padding with click interaction</p>
          </Card>
        </div>
      </section>

      {/* Metrics Section */}
      <section style={{ marginBottom: spacing['3xl'] }}>
        <h2 style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>Metrics Display</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: spacing.lg }}>
          <Card>
            <MetricDisplay label="Win Rate" value="73.5%" change="+5.2" />
          </Card>
          
          <Card>
            <MetricDisplay label="Total Profit" value="$12,450" change={-3.1} mono />
          </Card>
          
          <Card>
            <MetricDisplay label="Active Trades" value="8" size="lg" />
          </Card>
          
          <Card>
            <MetricDisplay label="Sharpe Ratio" value="2.45" size="sm" />
          </Card>
        </div>
      </section>

      {/* Signal Badges Section */}
      <section style={{ marginBottom: spacing['3xl'] }}>
        <h2 style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>Signal Badges</h2>
        <Card>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.md }}>
            <SignalBadge signal="call" confidence={87} />
            <SignalBadge signal="put" confidence={92} />
            <SignalBadge signal="neutral" />
            <SignalBadge signal="call" size="lg" confidence={75} />
            <SignalBadge signal="put" size="sm" confidence={68} />
          </div>
        </Card>
      </section>

      {/* Buttons Section */}
      <section style={{ marginBottom: spacing['3xl'] }}>
        <h2 style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>Trade Buttons</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.md }}>
          <TradeButton onClick={handleButtonClick} loading={loading}>
            Execute Trade
          </TradeButton>
          
          <TradeButton variant="secondary" onClick={() => alert('Secondary clicked')}>
            Cancel
          </TradeButton>
          
          <TradeButton variant="danger" onClick={() => alert('Danger clicked')}>
            Close Position
          </TradeButton>
          
          <TradeButton size="lg" onClick={() => alert('Large clicked')}>
            Large Button
          </TradeButton>
          
          <TradeButton size="sm" onClick={() => alert('Small clicked')}>
            Small Button
          </TradeButton>
          
          <TradeButton disabled>
            Disabled
          </TradeButton>
          
          <TradeButton fullWidth onClick={() => alert('Full width clicked')}>
            Full Width Button
          </TradeButton>
        </div>
      </section>

      {/* Modal Section */}
      <section style={{ marginBottom: spacing['3xl'] }}>
        <h2 style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>Modal</h2>
        <TradeButton onClick={() => setModalOpen(true)}>
          Open Modal
        </TradeButton>
        
        <Modal
          isOpen={modalOpen}
          onClose={() => setModalOpen(false)}
          title="Indicator Configuration"
          size="lg"
          footer={
            <>
              <TradeButton variant="secondary" onClick={() => setModalOpen(false)}>
                Cancel
              </TradeButton>
              <TradeButton onClick={() => { alert('Saved!'); setModalOpen(false); }}>
                Save
              </TradeButton>
            </>
          }
        >
          <div>
            <p style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>
              Configure your indicator parameters below:
            </p>
            
            <div style={{ marginBottom: spacing.md }}>
              <label style={{ color: colors.textPrimary, display: 'block', marginBottom: spacing.xs }}>
                Period
              </label>
              <input 
                type="number" 
                defaultValue={20}
                style={{
                  width: '100%',
                  background: colors.cardBg,
                  border: `1px solid ${colors.cardBorder}`,
                  color: colors.textPrimary,
                  padding: spacing.sm,
                  borderRadius: '8px',
                }}
              />
            </div>
            
            <div>
              <label style={{ color: colors.textPrimary, display: 'block', marginBottom: spacing.xs }}>
                Indicator Type
              </label>
              <select 
                style={{
                  width: '100%',
                  background: colors.cardBg,
                  border: `1px solid ${colors.cardBorder}`,
                  color: colors.textPrimary,
                  padding: spacing.sm,
                  borderRadius: '8px',
                }}
              >
                <option>SMA</option>
                <option>EMA</option>
                <option>RSI</option>
                <option>MACD</option>
              </select>
            </div>
          </div>
        </Modal>
      </section>

      {/* Complex Layout Example */}
      <section>
        <h2 style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>Complex Layout Example</h2>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: spacing.lg }}>
          <Card padding="lg">
            <div style={{ marginBottom: spacing.lg }}>
              <h3 style={{ color: colors.textPrimary, fontSize: '1.5rem', marginBottom: spacing.md }}>
                Current Signal
              </h3>
              <SignalBadge signal="call" confidence={89} size="lg" />
            </div>
            
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: spacing.md }}>
              <MetricDisplay label="RSI" value="45.2" size="sm" />
              <MetricDisplay label="MACD" value="0.015" size="sm" mono />
              <MetricDisplay label="Volume" value="1.2M" size="sm" />
            </div>
          </Card>
          
          <Card padding="lg">
            <h3 style={{ color: colors.textPrimary, fontSize: '1.5rem', marginBottom: spacing.lg }}>
              Quick Actions
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: spacing.sm }}>
              <TradeButton fullWidth>Execute CALL</TradeButton>
              <TradeButton fullWidth variant="danger">Execute PUT</TradeButton>
              <TradeButton fullWidth variant="secondary">View History</TradeButton>
            </div>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default ComponentShowcase;
