import React, { useState } from 'react';
import designTokens from '../styles/designTokens';

const Components = () => {
  const [activeTab, setActiveTab] = useState('colors');

  return (
    <div style={{ 
      fontFamily: designTokens.typography.fontFamily,
      color: designTokens.colors.textPrimary,
      maxWidth: '1400px',
      margin: '0 auto'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ 
          fontSize: '32px', 
          fontWeight: '600', 
          marginBottom: '8px',
          color: designTokens.colors.textPrimary
        }}>
          Component Showcase
        </h1>
        <p style={{ color: designTokens.colors.textSecondary, fontSize: '14px' }}>
          Developer reference for QuantumFlux design system and UI components
        </p>
      </div>

      {/* Tabs */}
      <div style={{ 
        display: 'flex', 
        gap: '8px', 
        borderBottom: `1px solid ${designTokens.colors.cardBorder}`,
        marginBottom: '32px',
        overflowX: 'auto'
      }}>
        {['colors', 'typography', 'cards', 'buttons', 'forms', 'badges', 'progress', 'stats', 'controls', 'alerts'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '12px 24px',
              background: 'transparent',
              border: 'none',
              borderBottom: activeTab === tab ? `2px solid ${designTokens.colors.accentGreen}` : '2px solid transparent',
              color: activeTab === tab ? designTokens.colors.accentGreen : designTokens.colors.textSecondary,
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              textTransform: 'capitalize',
              transition: 'all 0.2s',
              whiteSpace: 'nowrap'
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div>
        {activeTab === 'colors' && <ColorsTab />}
        {activeTab === 'typography' && <TypographyTab />}
        {activeTab === 'cards' && <CardsTab />}
        {activeTab === 'buttons' && <ButtonsTab />}
        {activeTab === 'forms' && <FormsTab />}
        {activeTab === 'badges' && <BadgesTab />}
        {activeTab === 'progress' && <ProgressTab />}
        {activeTab === 'stats' && <StatsTab />}
        {activeTab === 'controls' && <ControlsTab />}
        {activeTab === 'alerts' && <AlertsTab />}
      </div>
    </div>
  );
};

const ColorsTab = () => {
  const colorGroups = [
    {
      title: 'Backgrounds',
      colors: [
        { name: 'bgPrimary', value: designTokens.colors.bgPrimary, label: 'Primary Background' },
        { name: 'bgSecondary', value: designTokens.colors.bgSecondary, label: 'Secondary Background' },
        { name: 'cardBg', value: designTokens.colors.cardBg, label: 'Card Background' },
      ]
    },
    {
      title: 'Accents',
      colors: [
        { name: 'accentGreen', value: designTokens.colors.accentGreen, label: 'Green (Bullish)' },
        { name: 'accentRed', value: designTokens.colors.accentRed, label: 'Red (Bearish)' },
        { name: 'accentBlue', value: designTokens.colors.accentBlue, label: 'Blue (Info)' },
        { name: 'accentYellow', value: designTokens.colors.accentYellow, label: 'Yellow (Warning)' },
      ]
    },
    {
      title: 'Text',
      colors: [
        { name: 'textPrimary', value: designTokens.colors.textPrimary, label: 'Primary Text' },
        { name: 'textSecondary', value: designTokens.colors.textSecondary, label: 'Secondary Text' },
      ]
    },
    {
      title: 'Borders',
      colors: [
        { name: 'cardBorder', value: designTokens.colors.cardBorder, label: 'Card Border' },
      ]
    }
  ];

  return (
    <div>
      {colorGroups.map(group => (
        <div key={group.title} style={{ marginBottom: '40px' }}>
          <h3 style={{ 
            fontSize: '18px', 
            fontWeight: '600', 
            marginBottom: '16px',
            color: designTokens.colors.textPrimary
          }}>
            {group.title}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '16px' }}>
            {group.colors.map(color => (
              <div key={color.name} style={{
                background: designTokens.colors.cardBg,
                border: `1px solid ${designTokens.colors.cardBorder}`,
                borderRadius: designTokens.borderRadius.md,
                padding: '16px',
              }}>
                <div style={{
                  width: '100%',
                  height: '80px',
                  background: color.value,
                  borderRadius: designTokens.borderRadius.sm,
                  marginBottom: '12px',
                  border: `1px solid ${designTokens.colors.cardBorder}`
                }} />
                <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px' }}>
                  {color.label}
                </div>
                <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary, fontFamily: 'monospace' }}>
                  {color.value}
                </div>
                <div style={{ fontSize: '11px', color: designTokens.colors.textSecondary, fontFamily: 'monospace', marginTop: '4px' }}>
                  designTokens.colors.{color.name}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
};

const TypographyTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Font Sizes</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {Object.entries(designTokens.typography.fontSize).map(([key, value]) => (
          <div key={key} style={{
            background: designTokens.colors.cardBg,
            border: `1px solid ${designTokens.colors.cardBorder}`,
            borderRadius: designTokens.borderRadius.md,
            padding: '16px',
          }}>
            <div style={{ fontSize: value, fontWeight: '500', marginBottom: '8px' }}>
              The quick brown fox jumps over the lazy dog
            </div>
            <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary, fontFamily: 'monospace' }}>
              {key}: {value}
            </div>
          </div>
        ))}
      </div>

      <h3 style={{ fontSize: '18px', fontWeight: '600', marginTop: '40px', marginBottom: '24px' }}>Font Weights</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {Object.entries(designTokens.typography.fontWeight).map(([key, value]) => (
          <div key={key} style={{
            background: designTokens.colors.cardBg,
            border: `1px solid ${designTokens.colors.cardBorder}`,
            borderRadius: designTokens.borderRadius.md,
            padding: '16px',
          }}>
            <div style={{ fontWeight: value, fontSize: '16px', marginBottom: '8px' }}>
              The quick brown fox jumps over the lazy dog
            </div>
            <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary, fontFamily: 'monospace' }}>
              {key}: {value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

const CardsTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Card Variants</h3>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '24px' }}>
        
        {/* Standard Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.cardBorder}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '20px',
        }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>Standard Card</h4>
          <p style={{ fontSize: '14px', color: designTokens.colors.textSecondary }}>
            Default card with standard styling. Used for most content containers.
          </p>
        </div>

        {/* Green Accent Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.accentGreen}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '20px',
        }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px', color: designTokens.colors.accentGreen }}>
            Green Accent Card
          </h4>
          <p style={{ fontSize: '14px', color: designTokens.colors.textSecondary }}>
            Card with green border accent. Used for positive states or active selections.
          </p>
        </div>

        {/* Red Accent Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.accentRed}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '20px',
        }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px', color: designTokens.colors.accentRed }}>
            Red Accent Card
          </h4>
          <p style={{ fontSize: '14px', color: designTokens.colors.textSecondary }}>
            Card with red border accent. Used for warnings or negative states.
          </p>
        </div>

        {/* Glass Card */}
        <div style={{
          background: 'rgba(30, 41, 59, 0.5)',
          backdropFilter: 'blur(10px)',
          border: `1px solid ${designTokens.colors.cardBorder}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '20px',
        }}>
          <h4 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px' }}>Glass Card</h4>
          <p style={{ fontSize: '14px', color: designTokens.colors.textSecondary }}>
            Card with glass morphism effect. Used for overlays and modal content.
          </p>
        </div>

      </div>
    </div>
  );
};

const ButtonsTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Button Variants</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        
        {/* Primary Buttons */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Primary Buttons
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button style={{
              background: designTokens.components.button.primary.bg,
              color: designTokens.components.button.primary.text,
              border: 'none',
              borderRadius: designTokens.components.button.primary.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              Primary Button
            </button>
            <button style={{
              background: designTokens.components.button.primary.bg,
              color: designTokens.components.button.primary.text,
              border: 'none',
              borderRadius: designTokens.components.button.primary.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              opacity: 0.5,
              cursor: 'not-allowed'
            }}>
              Disabled Primary
            </button>
          </div>
        </div>

        {/* Secondary Buttons */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Secondary Buttons
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button style={{
              background: designTokens.components.button.secondary.bg,
              color: designTokens.components.button.secondary.text,
              border: `1px solid ${designTokens.colors.cardBorder}`,
              borderRadius: designTokens.components.button.secondary.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              Secondary Button
            </button>
            <button style={{
              background: designTokens.components.button.secondary.bg,
              color: designTokens.components.button.secondary.text,
              border: `1px solid ${designTokens.colors.cardBorder}`,
              borderRadius: designTokens.components.button.secondary.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              opacity: 0.5,
              cursor: 'not-allowed'
            }}>
              Disabled Secondary
            </button>
          </div>
        </div>

        {/* Danger Buttons */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Danger Buttons
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <button style={{
              background: designTokens.components.button.danger.bg,
              color: designTokens.components.button.danger.text,
              border: 'none',
              borderRadius: designTokens.components.button.danger.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              Danger Button
            </button>
            <button style={{
              background: designTokens.components.button.danger.bg,
              color: designTokens.components.button.danger.text,
              border: 'none',
              borderRadius: designTokens.components.button.danger.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              opacity: 0.5,
              cursor: 'not-allowed'
            }}>
              Disabled Danger
            </button>
          </div>
        </div>

        {/* Button Sizes */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Button Sizes
          </h4>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
            <button style={{
              background: designTokens.components.button.primary.bg,
              color: designTokens.components.button.primary.text,
              border: 'none',
              borderRadius: designTokens.components.button.primary.borderRadius,
              padding: '8px 16px',
              fontSize: '12px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              Small
            </button>
            <button style={{
              background: designTokens.components.button.primary.bg,
              color: designTokens.components.button.primary.text,
              border: 'none',
              borderRadius: designTokens.components.button.primary.borderRadius,
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              Medium
            </button>
            <button style={{
              background: designTokens.components.button.primary.bg,
              color: designTokens.components.button.primary.text,
              border: 'none',
              borderRadius: designTokens.components.button.primary.borderRadius,
              padding: '16px 32px',
              fontSize: '16px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}>
              Large
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

const FormsTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Form Elements</h3>
      
      <div style={{ maxWidth: '600px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* Text Input */}
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
            Text Input
          </label>
          <input 
            type="text" 
            placeholder="Enter text..."
            style={{
              width: '100%',
              padding: '12px',
              background: designTokens.colors.cardBg,
              border: `1px solid ${designTokens.colors.cardBorder}`,
              borderRadius: designTokens.borderRadius.sm,
              color: designTokens.colors.textPrimary,
              fontSize: '14px',
              outline: 'none',
            }}
          />
        </div>

        {/* Select Dropdown */}
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
            Select Dropdown
          </label>
          <select style={{
            width: '100%',
            padding: '12px',
            background: designTokens.colors.cardBg,
            border: `1px solid ${designTokens.colors.cardBorder}`,
            borderRadius: designTokens.borderRadius.sm,
            color: designTokens.colors.textPrimary,
            fontSize: '14px',
            outline: 'none',
            cursor: 'pointer'
          }}>
            <option>Option 1</option>
            <option>Option 2</option>
            <option>Option 3</option>
          </select>
        </div>

        {/* Textarea */}
        <div>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '500', marginBottom: '8px' }}>
            Textarea
          </label>
          <textarea 
            placeholder="Enter longer text..."
            rows={4}
            style={{
              width: '100%',
              padding: '12px',
              background: designTokens.colors.cardBg,
              border: `1px solid ${designTokens.colors.cardBorder}`,
              borderRadius: designTokens.borderRadius.sm,
              color: designTokens.colors.textPrimary,
              fontSize: '14px',
              outline: 'none',
              resize: 'vertical',
              fontFamily: designTokens.typography.fontFamily
            }}
          />
        </div>

        {/* Toggle/Checkbox */}
        <div>
          <label style={{ display: 'flex', alignItems: 'center', gap: '12px', cursor: 'pointer' }}>
            <input 
              type="checkbox" 
              style={{
                width: '20px',
                height: '20px',
                cursor: 'pointer',
                accentColor: designTokens.colors.accentGreen
              }}
            />
            <span style={{ fontSize: '14px', fontWeight: '500' }}>Checkbox Label</span>
          </label>
        </div>

      </div>
    </div>
  );
};

const BadgesTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Badges & Tags</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        
        {/* Signal Badges */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Signal Badges
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{
              background: designTokens.colors.greenAlpha[20],
              color: designTokens.colors.accentGreen,
              padding: '6px 16px',
              borderRadius: designTokens.borderRadius.full,
              fontSize: '13px',
              fontWeight: '600',
              border: `1px solid ${designTokens.colors.accentGreen}40`
            }}>
              CALL
            </span>
            <span style={{
              background: designTokens.colors.redAlpha[20],
              color: designTokens.colors.accentRed,
              padding: '6px 16px',
              borderRadius: designTokens.borderRadius.full,
              fontSize: '13px',
              fontWeight: '600',
              border: `1px solid ${designTokens.colors.accentRed}40`
            }}>
              PUT
            </span>
            <span style={{
              background: 'rgba(59, 130, 246, 0.2)',
              color: designTokens.colors.accentBlue,
              padding: '6px 16px',
              borderRadius: designTokens.borderRadius.full,
              fontSize: '13px',
              fontWeight: '600',
              border: `1px solid ${designTokens.colors.accentBlue}40`
            }}>
              BUY
            </span>
            <span style={{
              background: 'rgba(249, 115, 22, 0.2)',
              color: '#f97316',
              padding: '6px 16px',
              borderRadius: designTokens.borderRadius.full,
              fontSize: '13px',
              fontWeight: '600',
              border: '1px solid #f9731640'
            }}>
              SELL
            </span>
          </div>
        </div>

        {/* Status Badges */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Status Badges
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
            <span style={{
              background: designTokens.colors.greenAlpha[20],
              color: designTokens.colors.accentGreen,
              padding: '4px 12px',
              borderRadius: designTokens.borderRadius.md,
              fontSize: '12px',
              fontWeight: '500'
            }}>
              WIN
            </span>
            <span style={{
              background: designTokens.colors.redAlpha[20],
              color: designTokens.colors.accentRed,
              padding: '4px 12px',
              borderRadius: designTokens.borderRadius.md,
              fontSize: '12px',
              fontWeight: '500'
            }}>
              LOSS
            </span>
            <span style={{
              background: 'rgba(59, 130, 246, 0.2)',
              color: designTokens.colors.accentBlue,
              padding: '4px 12px',
              borderRadius: designTokens.borderRadius.md,
              fontSize: '12px',
              fontWeight: '500'
            }}>
              ACTIVE
            </span>
            <span style={{
              background: 'rgba(148, 163, 184, 0.2)',
              color: designTokens.colors.textSecondary,
              padding: '4px 12px',
              borderRadius: designTokens.borderRadius.md,
              fontSize: '12px',
              fontWeight: '500'
            }}>
              CLOSED
            </span>
            <span style={{
              background: 'rgba(245, 158, 11, 0.2)',
              color: designTokens.colors.accentYellow,
              padding: '4px 12px',
              borderRadius: designTokens.borderRadius.md,
              fontSize: '12px',
              fontWeight: '500'
            }}>
              PENDING
            </span>
          </div>
        </div>

        {/* Confidence Badges */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Confidence Levels
          </h4>
          <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
            <span style={{
              background: designTokens.colors.greenAlpha[20],
              color: designTokens.colors.accentGreen,
              padding: '8px 16px',
              borderRadius: designTokens.borderRadius.lg,
              fontSize: '14px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span style={{ fontSize: '18px' }}>87%</span>
              <span style={{ fontSize: '11px', opacity: 0.8 }}>HIGH</span>
            </span>
            <span style={{
              background: 'rgba(245, 158, 11, 0.2)',
              color: designTokens.colors.accentYellow,
              padding: '8px 16px',
              borderRadius: designTokens.borderRadius.lg,
              fontSize: '14px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span style={{ fontSize: '18px' }}>54%</span>
              <span style={{ fontSize: '11px', opacity: 0.8 }}>MEDIUM</span>
            </span>
            <span style={{
              background: designTokens.colors.redAlpha[20],
              color: designTokens.colors.accentRed,
              padding: '8px 16px',
              borderRadius: designTokens.borderRadius.lg,
              fontSize: '14px',
              fontWeight: '600',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span style={{ fontSize: '18px' }}>32%</span>
              <span style={{ fontSize: '11px', opacity: 0.8 }}>LOW</span>
            </span>
          </div>
        </div>

      </div>
    </div>
  );
};

const ProgressTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Progress Indicators</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
        
        {/* Standard Progress Bars */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Progress Bars
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Win Rate */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span>Win Rate</span>
                <span style={{ color: designTokens.colors.accentGreen, fontWeight: '600' }}>72%</span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: designTokens.colors.cardBorder,
                borderRadius: designTokens.borderRadius.full,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '72%',
                  height: '100%',
                  background: `linear-gradient(90deg, ${designTokens.colors.accentGreen}, #059669)`,
                  borderRadius: designTokens.borderRadius.full
                }} />
              </div>
            </div>

            {/* Risk Level */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span>Risk Level</span>
                <span style={{ color: designTokens.colors.accentYellow, fontWeight: '600' }}>45%</span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: designTokens.colors.cardBorder,
                borderRadius: designTokens.borderRadius.full,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '45%',
                  height: '100%',
                  background: `linear-gradient(90deg, ${designTokens.colors.accentYellow}, #ea580c)`,
                  borderRadius: designTokens.borderRadius.full
                }} />
              </div>
            </div>

            {/* Drawdown */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
                <span>Max Drawdown</span>
                <span style={{ color: designTokens.colors.accentRed, fontWeight: '600' }}>18%</span>
              </div>
              <div style={{
                width: '100%',
                height: '8px',
                background: designTokens.colors.cardBorder,
                borderRadius: designTokens.borderRadius.full,
                overflow: 'hidden'
              }}>
                <div style={{
                  width: '18%',
                  height: '100%',
                  background: `linear-gradient(90deg, ${designTokens.colors.accentRed}, #dc2626)`,
                  borderRadius: designTokens.borderRadius.full
                }} />
              </div>
            </div>
          </div>
        </div>

        {/* Loading Spinner */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Loading Spinners
          </h4>
          <div style={{ display: 'flex', gap: '24px', alignItems: 'center', flexWrap: 'wrap' }}>
            {/* Green Spinner */}
            <div style={{
              width: '40px',
              height: '40px',
              border: `4px solid ${designTokens.colors.cardBorder}`,
              borderTop: `4px solid ${designTokens.colors.accentGreen}`,
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            {/* Blue Spinner */}
            <div style={{
              width: '32px',
              height: '32px',
              border: `3px solid ${designTokens.colors.cardBorder}`,
              borderTop: `3px solid ${designTokens.colors.accentBlue}`,
              borderRadius: '50%',
              animation: 'spin 0.8s linear infinite'
            }} />
            {/* Small Spinner */}
            <div style={{
              width: '24px',
              height: '24px',
              border: `3px solid ${designTokens.colors.cardBorder}`,
              borderTop: `3px solid ${designTokens.colors.accentGreen}`,
              borderRadius: '50%',
              animation: 'spin 0.6s linear infinite'
            }} />
          </div>
          <style>{`
            @keyframes spin {
              0% { transform: rotate(0deg); }
              100% { transform: rotate(360deg); }
            }
          `}</style>
        </div>

      </div>
    </div>
  );
};

const StatsTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Statistics Cards</h3>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '24px' }}>
        
        {/* Profit/Loss Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.cardBorder}`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary, marginBottom: '8px', fontWeight: '500' }}>
            Total P/L
          </div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: designTokens.colors.accentGreen, marginBottom: '4px' }}>
            +$2,547.80
          </div>
          <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary }}>
            <span style={{ color: designTokens.colors.accentGreen }}>↑ 12.4%</span> from last month
          </div>
        </div>

        {/* Win Rate Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.cardBorder}`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary, marginBottom: '8px', fontWeight: '500' }}>
            Win Rate
          </div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: designTokens.colors.textPrimary, marginBottom: '4px' }}>
            72.3%
          </div>
          <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary }}>
            156 wins / 216 total trades
          </div>
        </div>

        {/* Sharpe Ratio Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.cardBorder}`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary, marginBottom: '8px', fontWeight: '500' }}>
            Sharpe Ratio
          </div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: designTokens.colors.accentBlue, marginBottom: '4px' }}>
            2.84
          </div>
          <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary }}>
            Excellent risk-adjusted returns
          </div>
        </div>

        {/* Max Drawdown Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.accentRed}40`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary, marginBottom: '8px', fontWeight: '500' }}>
            Max Drawdown
          </div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: designTokens.colors.accentRed, marginBottom: '4px' }}>
            -8.2%
          </div>
          <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary }}>
            Within acceptable limits
          </div>
        </div>

        {/* Active Positions Card */}
        <div style={{
          background: `linear-gradient(135deg, ${designTokens.colors.cardBg}, ${designTokens.colors.bgSecondary})`,
          border: `1px solid ${designTokens.colors.accentGreen}40`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary, marginBottom: '8px', fontWeight: '500' }}>
            Active Positions
          </div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: designTokens.colors.textPrimary, marginBottom: '4px' }}>
            4
          </div>
          <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary }}>
            Total exposure: $12,450
          </div>
        </div>

        {/* Confidence Score Card */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.cardBorder}`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary, marginBottom: '8px', fontWeight: '500' }}>
            Signal Confidence
          </div>
          <div style={{ fontSize: '28px', fontWeight: '700', color: designTokens.colors.accentGreen, marginBottom: '4px' }}>
            87%
          </div>
          <div style={{ fontSize: '12px', color: designTokens.colors.textSecondary }}>
            <span style={{ 
              background: designTokens.colors.greenAlpha[20],
              color: designTokens.colors.accentGreen,
              padding: '2px 8px',
              borderRadius: designTokens.borderRadius.sm,
              fontSize: '11px',
              fontWeight: '600'
            }}>HIGH</span> confidence signal
          </div>
        </div>

      </div>
    </div>
  );
};

const ControlsTab = () => {
  const [switchState, setSwitchState] = useState(true);
  const [sliderValue, setSliderValue] = useState(50);

  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Interactive Controls</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '40px', maxWidth: '600px' }}>
        
        {/* Toggle Switches */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Toggle Switches
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px' }}>Auto-trading Enabled</span>
              <div 
                onClick={() => setSwitchState(!switchState)}
                style={{
                  width: '52px',
                  height: '28px',
                  background: switchState ? designTokens.colors.accentGreen : designTokens.colors.cardBorder,
                  borderRadius: designTokens.borderRadius.full,
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.3s'
                }}
              >
                <div style={{
                  width: '22px',
                  height: '22px',
                  background: designTokens.colors.textPrimary,
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '3px',
                  left: switchState ? '27px' : '3px',
                  transition: 'left 0.3s',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                }} />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px' }}>Risk Management</span>
              <div style={{
                width: '52px',
                height: '28px',
                background: designTokens.colors.accentGreen,
                borderRadius: designTokens.borderRadius.full,
                position: 'relative',
                cursor: 'pointer'
              }}>
                <div style={{
                  width: '22px',
                  height: '22px',
                  background: designTokens.colors.textPrimary,
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '3px',
                  left: '27px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)'
                }} />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '14px', opacity: 0.5 }}>Live Signals (Disabled)</span>
              <div style={{
                width: '52px',
                height: '28px',
                background: designTokens.colors.cardBorder,
                borderRadius: designTokens.borderRadius.full,
                position: 'relative',
                cursor: 'not-allowed'
              }}>
                <div style={{
                  width: '22px',
                  height: '22px',
                  background: designTokens.colors.textPrimary,
                  borderRadius: '50%',
                  position: 'absolute',
                  top: '3px',
                  left: '3px',
                  boxShadow: '0 2px 4px rgba(0,0,0,0.2)',
                  opacity: 0.6
                }} />
              </div>
            </div>
          </div>
        </div>

        {/* Slider Controls */}
        <div>
          <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: designTokens.colors.textSecondary }}>
            Sliders
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Risk Percentage Slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px' }}>Risk per Trade</span>
                <span style={{ 
                  fontSize: '14px', 
                  fontWeight: '600',
                  color: sliderValue > 75 ? designTokens.colors.accentRed : 
                         sliderValue > 50 ? designTokens.colors.accentYellow : 
                         designTokens.colors.accentGreen
                }}>
                  {sliderValue}%
                </span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="100" 
                value={sliderValue}
                onChange={(e) => setSliderValue(Number(e.target.value))}
                style={{
                  width: '100%',
                  height: '8px',
                  borderRadius: designTokens.borderRadius.full,
                  outline: 'none',
                  WebkitAppearance: 'none',
                  background: `linear-gradient(to right, ${designTokens.colors.accentGreen} 0%, ${designTokens.colors.accentGreen} ${sliderValue}%, ${designTokens.colors.cardBorder} ${sliderValue}%, ${designTokens.colors.cardBorder} 100%)`,
                  cursor: 'pointer'
                }}
              />
            </div>

            {/* Position Size Slider */}
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                <span style={{ fontSize: '13px' }}>Position Size</span>
                <span style={{ fontSize: '14px', fontWeight: '600', color: designTokens.colors.accentBlue }}>
                  $1,500
                </span>
              </div>
              <input 
                type="range" 
                min="0" 
                max="5000"
                defaultValue="1500"
                style={{
                  width: '100%',
                  height: '8px',
                  borderRadius: designTokens.borderRadius.full,
                  outline: 'none',
                  WebkitAppearance: 'none',
                  background: `linear-gradient(to right, ${designTokens.colors.accentBlue} 0%, ${designTokens.colors.accentBlue} 30%, ${designTokens.colors.cardBorder} 30%, ${designTokens.colors.cardBorder} 100%)`,
                  cursor: 'pointer'
                }}
              />
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};

const AlertsTab = () => {
  return (
    <div>
      <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Alerts & Notifications</h3>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '600px' }}>
        
        {/* Success Alert */}
        <div style={{
          background: designTokens.colors.greenAlpha[10],
          border: `1px solid ${designTokens.colors.accentGreen}60`,
          borderLeft: `4px solid ${designTokens.colors.accentGreen}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '16px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <span style={{ fontSize: '20px' }}>✓</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: designTokens.colors.accentGreen, marginBottom: '4px' }}>
              Trade Executed Successfully
            </div>
            <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary }}>
              Your CALL order on EUR/USD has been filled at 1.0850
            </div>
          </div>
        </div>

        {/* Error Alert */}
        <div style={{
          background: designTokens.colors.redAlpha[10],
          border: `1px solid ${designTokens.colors.accentRed}60`,
          borderLeft: `4px solid ${designTokens.colors.accentRed}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '16px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <span style={{ fontSize: '20px' }}>✕</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: designTokens.colors.accentRed, marginBottom: '4px' }}>
              Trade Failed
            </div>
            <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary }}>
              Insufficient balance. Please deposit funds to continue trading.
            </div>
          </div>
        </div>

        {/* Warning Alert */}
        <div style={{
          background: 'rgba(245, 158, 11, 0.1)',
          border: `1px solid ${designTokens.colors.accentYellow}60`,
          borderLeft: `4px solid ${designTokens.colors.accentYellow}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '16px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <span style={{ fontSize: '20px' }}>⚠</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: designTokens.colors.accentYellow, marginBottom: '4px' }}>
              High Risk Detected
            </div>
            <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary }}>
              Current drawdown is approaching maximum limit (6.8% / 10%)
            </div>
          </div>
        </div>

        {/* Info Alert */}
        <div style={{
          background: 'rgba(59, 130, 246, 0.1)',
          border: `1px solid ${designTokens.colors.accentBlue}60`,
          borderLeft: `4px solid ${designTokens.colors.accentBlue}`,
          borderRadius: designTokens.borderRadius.md,
          padding: '16px',
          display: 'flex',
          gap: '12px',
          alignItems: 'flex-start'
        }}>
          <span style={{ fontSize: '20px' }}>ℹ</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '14px', fontWeight: '600', color: designTokens.colors.accentBlue, marginBottom: '4px' }}>
              New Signal Available
            </div>
            <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary }}>
              Quantum Flux detected a 87% confidence CALL signal on GBP/USD
            </div>
          </div>
        </div>

        {/* Signal Alert with Action */}
        <div style={{
          background: designTokens.colors.cardBg,
          border: `1px solid ${designTokens.colors.accentGreen}`,
          borderRadius: designTokens.borderRadius.lg,
          padding: '20px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
            <div>
              <div style={{ fontSize: '15px', fontWeight: '600', color: designTokens.colors.textPrimary, marginBottom: '4px' }}>
                High Confidence Signal Detected
              </div>
              <div style={{ fontSize: '13px', color: designTokens.colors.textSecondary }}>
                EUR/USD • 87% Confidence • CALL
              </div>
            </div>
            <span style={{
              background: designTokens.colors.greenAlpha[20],
              color: designTokens.colors.accentGreen,
              padding: '4px 12px',
              borderRadius: designTokens.borderRadius.full,
              fontSize: '12px',
              fontWeight: '600'
            }}>
              ACTIVE
            </span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={{
              background: designTokens.colors.accentGreen,
              color: designTokens.colors.textPrimary,
              border: 'none',
              borderRadius: designTokens.borderRadius.md,
              padding: '10px 20px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              flex: 1
            }}>
              Execute Trade
            </button>
            <button style={{
              background: 'transparent',
              color: designTokens.colors.textSecondary,
              border: `1px solid ${designTokens.colors.cardBorder}`,
              borderRadius: designTokens.borderRadius.md,
              padding: '10px 20px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer'
            }}>
              Dismiss
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};

export default Components;
