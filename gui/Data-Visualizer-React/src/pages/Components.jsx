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
        marginBottom: '32px'
      }}>
        {['colors', 'typography', 'cards', 'buttons', 'forms'].map(tab => (
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
              transition: 'all 0.2s'
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

export default Components;
