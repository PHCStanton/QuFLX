# QuantumFlux Design System

## Overview

The QuantumFlux design system provides a Solana-inspired, professional trading terminal aesthetic with a dark theme, green/red accents, and clean typography. All design tokens and components are built to ensure consistency across the application.

## Design Tokens

### Import Design Tokens

```javascript
import { colors, spacing, typography, components } from './styles/designTokens';
```

### Color Palette

#### Background Colors
```javascript
colors.bgPrimary      // #0a0e1a - Deep space background
colors.bgSecondary    // #141824 - Slightly lighter background
colors.cardBg         // #1e293b - Card background
colors.cardBorder     // #334155 - Subtle borders
```

#### Accent Colors
```javascript
colors.accentGreen    // #10b981 - Success, buy, CALL
colors.accentRed      // #ef4444 - Danger, sell, PUT
colors.accentBlue     // #3b82f6 - Info/highlight
colors.accentPurple   // #8b5cf6 - Secondary accent
colors.accentYellow   // #f59e0b - Warning
```

#### Text Colors
```javascript
colors.textPrimary    // #f8fafc - White text
colors.textSecondary  // #94a3b8 - Muted text
colors.textTertiary   // #64748b - Very muted text
```

#### Opacity Variants
```javascript
colors.greenAlpha[10]  // rgba(16, 185, 129, 0.1)
colors.greenAlpha[20]  // rgba(16, 185, 129, 0.2)
colors.greenAlpha[30]  // rgba(16, 185, 129, 0.3)

colors.redAlpha[10]    // rgba(239, 68, 68, 0.1)
colors.redAlpha[20]    // rgba(239, 68, 68, 0.2)
colors.redAlpha[30]    // rgba(239, 68, 68, 0.3)
```

### Typography

```javascript
typography.fontFamily.sans  // "Inter", system fonts
typography.fontFamily.mono  // "JetBrains Mono", monospace

typography.fontSize.xs      // 12px
typography.fontSize.sm      // 14px
typography.fontSize.base    // 16px
typography.fontSize.lg      // 18px
typography.fontSize.xl      // 20px
typography.fontSize['2xl']  // 24px
typography.fontSize['3xl']  // 30px
typography.fontSize['4xl']  // 36px

typography.fontWeight.normal    // 400
typography.fontWeight.medium    // 500
typography.fontWeight.semibold  // 600
typography.fontWeight.bold      // 700
```

### Spacing

```javascript
spacing.xs     // 4px
spacing.sm     // 8px
spacing.md     // 16px
spacing.lg     // 24px
spacing.xl     // 32px
spacing['2xl'] // 48px
spacing['3xl'] // 64px
```

### Component Tokens

Pre-configured styles for common components:

```javascript
components.card        // Card styling
components.button      // Button variants (primary, secondary, danger)
components.badge       // Badge variants (success, error, info)
components.input       // Input field styling
components.modal       // Modal styling
```

### Glass Effect

Apply frosted glass effect to any element:

```javascript
import { glassEffect } from './styles/designTokens';

<div style={glassEffect}>
  // Content with glass effect
</div>
```

---

## Component Library

### Card

Container component with optional glass effect.

```javascript
import { Card } from './components/ui';

// Standard card
<Card>
  <h3>Title</h3>
  <p>Content</p>
</Card>

// Glass effect
<Card glass>
  <h3>Frosted Glass Card</h3>
</Card>

// Custom padding
<Card padding="lg">
  <h3>Large Padding</h3>
</Card>

// Clickable (automatically gets role="button", tabIndex, keyboard support)
<Card onClick={() => console.log('clicked')}>
  <h3>Click me</h3>
</Card>
```

**Props:**
- `children` (node, required) - Card content
- `className` (string) - Additional CSS classes
- `glass` (bool) - Apply glass effect
- `padding` ('none' | 'sm' | 'default' | 'lg') - Padding size
- `onClick` (func) - Click handler (automatically adds keyboard support)
- `style` (object) - Inline styles

**Accessibility:**
- When `onClick` is provided, Card automatically becomes keyboard accessible with `role="button"`, `tabIndex="0"`, and Enter/Space key support

---

### MetricDisplay

Display key metrics with label and value, optionally showing change.

```javascript
import { MetricDisplay } from './components/ui';

// Basic metric
<MetricDisplay 
  label="Win Rate" 
  value="73.5%" 
/>

// With change indicator
<MetricDisplay 
  label="Total Profit" 
  value="$12,450" 
  change={-3.1}
  mono
/>

// Large size
<MetricDisplay 
  label="Active Trades" 
  value="8" 
  size="lg"
/>
```

**Props:**
- `label` (string, required) - Metric label
- `value` (string | number, required) - Metric value
- `change` (string | number) - Change indicator (green if positive, red if negative)
- `size` ('sm' | 'default' | 'lg') - Display size
- `mono` (bool) - Use monospace font for value
- `className` (string) - Additional CSS classes

---

### SignalBadge

Display trading signals (CALL/PUT/NEUTRAL) with optional confidence score.

```javascript
import { SignalBadge } from './components/ui';

// Basic signals
<SignalBadge signal="call" />
<SignalBadge signal="put" />
<SignalBadge signal="neutral" />

// With confidence
<SignalBadge signal="call" confidence={87} />

// Different sizes
<SignalBadge signal="put" size="lg" confidence={92} />
<SignalBadge signal="call" size="sm" confidence={68} />
```

**Props:**
- `signal` ('call' | 'put' | 'neutral' | 'buy' | 'sell' | 'hold' | 'long' | 'short', required) - Signal type
- `confidence` (number) - Confidence percentage (0-100)
- `size` ('sm' | 'default' | 'lg') - Badge size
- `className` (string) - Additional CSS classes

---

### TradeButton

Primary action button with loading states and variants.

```javascript
import { TradeButton } from './components/ui';

// Primary button
<TradeButton onClick={handleClick}>
  Execute Trade
</TradeButton>

// Secondary variant
<TradeButton variant="secondary" onClick={handleCancel}>
  Cancel
</TradeButton>

// Danger variant
<TradeButton variant="danger" onClick={handleClose}>
  Close Position
</TradeButton>

// With loading state
<TradeButton loading={isLoading}>
  Processing...
</TradeButton>

// Disabled
<TradeButton disabled>
  Not Available
</TradeButton>

// Full width
<TradeButton fullWidth>
  Full Width Action
</TradeButton>

// With icon
<TradeButton icon={<span>🚀</span>}>
  Launch
</TradeButton>
```

**Props:**
- `children` (node, required) - Button content
- `onClick` (func) - Click handler
- `variant` ('primary' | 'secondary' | 'danger') - Button style variant
- `size` ('sm' | 'default' | 'lg') - Button size
- `disabled` (bool) - Disabled state
- `loading` (bool) - Loading state (shows spinner)
- `fullWidth` (bool) - Full width button
- `className` (string) - Additional CSS classes
- `icon` (node) - Icon element

---

### Modal

Accessible overlay dialog with focus management.

```javascript
import { Modal } from './components/ui';
import { TradeButton } from './components/ui';

const [isOpen, setIsOpen] = useState(false);

<TradeButton onClick={() => setIsOpen(true)}>
  Open Modal
</TradeButton>

<Modal
  isOpen={isOpen}
  onClose={() => setIsOpen(false)}
  title="Configure Indicator"
  size="lg"
  footer={
    <>
      <TradeButton variant="secondary" onClick={() => setIsOpen(false)}>
        Cancel
      </TradeButton>
      <TradeButton onClick={handleSave}>
        Save
      </TradeButton>
    </>
  }
>
  <p>Modal content goes here</p>
</Modal>
```

**Props:**
- `isOpen` (bool, required) - Modal open state
- `onClose` (func, required) - Close handler
- `title` (string, required) - Modal title
- `children` (node, required) - Modal body content
- `footer` (node) - Footer content (usually buttons)
- `size` ('sm' | 'default' | 'lg' | 'xl') - Modal width
- `closeOnOverlayClick` (bool) - Close when clicking overlay (default: true)
- `ariaDescribedBy` (string) - Optional description for screen readers

**Accessibility Features:**
- ✅ `role="dialog"` and `aria-modal="true"`
- ✅ `aria-labelledby` linked to unique title ID (prevents collisions)
- ✅ `aria-describedby` support for descriptions
- ✅ Focus trap (Tab/Shift+Tab cycles within modal)
- ✅ Focus management (auto-focus close button, return focus on close)
- ✅ Keyboard navigation (Escape to close)
- ✅ Unique IDs using React's `useId()` hook (supports multiple modals)
- ✅ Screen reader friendly

---

## Integration with Existing CSS Variables

The design tokens are designed to complement the existing CSS custom properties. Here's how to use them together:

### Using Design Tokens in New Components

```javascript
// Preferred: Use design tokens for new components
import { colors, spacing, typography } from './styles/designTokens';

const MyComponent = () => (
  <div style={{
    background: colors.cardBg,
    padding: spacing.lg,
    color: colors.textPrimary,
    fontFamily: typography.fontFamily.sans,
  }}>
    Content
  </div>
);
```

### Using CSS Variables for Consistency

If you need to use CSS variables (for TailwindCSS or existing styles), reference them like this:

```javascript
// Using existing CSS variables
<div style={{ 
  background: 'var(--bg-primary)',
  color: 'var(--text-primary)',
}}>
  Content
</div>
```

### Mapping Between Systems

| Design Token | CSS Variable | Value |
|--------------|--------------|-------|
| `colors.bgPrimary` | `var(--bg-primary)` | `#0a0e1a` |
| `colors.cardBg` | `var(--card-bg)` | `#1e293b` |
| `colors.cardBorder` | `var(--card-border)` | `#334155` |
| `colors.accentGreen` | `var(--accent-green)` | `#10b981` |
| `colors.accentRed` | `var(--accent-red)` | `#ef4444` |
| `colors.accentBlue` | `var(--accent-blue)` | `#3b82f6` |
| `colors.textPrimary` | `var(--text-primary)` | `#f8fafc` |
| `colors.textSecondary` | `var(--text-secondary)` | `#94a3b8` |

### Best Practices

1. **New Components**: Use design tokens (`import { colors } from './styles/designTokens'`)
2. **Existing Pages**: Gradually migrate to design tokens or keep CSS variables for consistency
3. **Mixed Approach**: OK to use both, but prefer design tokens for better type safety and IDE support

---

## Usage Examples

### Example 1: Metric Dashboard

```javascript
import { Card, MetricDisplay } from './components/ui';
import { spacing } from './styles/designTokens';

const MetricDashboard = () => (
  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: spacing.lg }}>
    <Card>
      <MetricDisplay label="Win Rate" value="73.5%" change="+5.2" />
    </Card>
    <Card>
      <MetricDisplay label="Total Profit" value="$12,450" change={-3.1} mono />
    </Card>
    <Card>
      <MetricDisplay label="Active Trades" value="8" />
    </Card>
    <Card>
      <MetricDisplay label="Sharpe Ratio" value="2.45" />
    </Card>
  </div>
);
```

### Example 2: Signal Panel

```javascript
import { Card, SignalBadge, TradeButton, MetricDisplay } from './components/ui';
import { colors, spacing } from './styles/designTokens';

const SignalPanel = ({ signal, confidence, metrics }) => (
  <Card padding="lg">
    <div style={{ marginBottom: spacing.lg }}>
      <h3 style={{ color: colors.textPrimary, marginBottom: spacing.md }}>
        Current Signal
      </h3>
      <SignalBadge signal={signal} confidence={confidence} size="lg" />
    </div>
    
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: spacing.md, marginBottom: spacing.lg }}>
      <MetricDisplay label="RSI" value={metrics.rsi} size="sm" />
      <MetricDisplay label="MACD" value={metrics.macd} size="sm" mono />
      <MetricDisplay label="Volume" value={metrics.volume} size="sm" />
    </div>
    
    <TradeButton fullWidth>
      Execute {signal.toUpperCase()}
    </TradeButton>
  </Card>
);
```

### Example 3: Indicator Configuration Modal

```javascript
import { Modal, TradeButton } from './components/ui';
import { colors, spacing, components } from './styles/designTokens';
import { useState } from 'react';

const IndicatorConfigModal = ({ isOpen, onClose, onSave }) => {
  const [period, setPeriod] = useState(20);
  const [type, setType] = useState('SMA');

  const handleSave = () => {
    onSave({ period, type });
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Configure Indicator"
      size="lg"
      ariaDescribedBy="modal-description"
      footer={
        <>
          <TradeButton variant="secondary" onClick={onClose}>
            Cancel
          </TradeButton>
          <TradeButton onClick={handleSave}>
            Add Indicator
          </TradeButton>
        </>
      }
    >
      <div>
        <p id="modal-description" style={{ color: colors.textSecondary, marginBottom: spacing.lg }}>
          Configure your indicator parameters below:
        </p>
        <div style={{ marginBottom: spacing.md }}>
          <label style={{ color: colors.textPrimary, display: 'block', marginBottom: spacing.xs }}>
            Period
          </label>
          <input 
            type="number" 
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            style={{
              width: '100%',
              background: components.input.bg,
              border: `1px solid ${components.input.border}`,
              color: components.input.text,
              padding: components.input.padding,
              borderRadius: components.input.borderRadius,
            }}
          />
        </div>
        
        <div>
          <label style={{ color: colors.textPrimary, display: 'block', marginBottom: spacing.xs }}>
            Indicator Type
          </label>
          <select 
            value={type}
            onChange={(e) => setType(e.target.value)}
            style={{
              width: '100%',
              background: components.input.bg,
              border: `1px solid ${components.input.border}`,
              color: components.input.text,
              padding: components.input.padding,
              borderRadius: components.input.borderRadius,
            }}
          >
            <option>SMA</option>
            <option>EMA</option>
            <option>RSI</option>
            <option>MACD</option>
            <option>Bollinger Bands</option>
          </select>
        </div>
      </div>
    </Modal>
  );
};
```

---

## Testing Components

Visit `/components` route in the application to see a live showcase of all components with interactive examples.

---

## Accessibility Checklist

When building with these components:

- ✅ All interactive elements are keyboard accessible
- ✅ Focus states are visible (design tokens include focus styles)
- ✅ ARIA attributes are included where needed
- ✅ Color contrast meets WCAG AA standards (3:1 minimum)
- ✅ Focus trap implemented in Modal
- ✅ Focus return on Modal close
- ✅ Semantic HTML structure

---

## Performance Considerations

1. **Import Only What You Need**: Import specific components instead of the entire library
   ```javascript
   // Good
   import { Card, TradeButton } from './components/ui';
   
   // Avoid (imports everything)
   import * as UI from './components/ui';
   ```

2. **Memoize Static Content**: Use React.memo for components that don't change frequently
   ```javascript
   import React from 'react';
   export default React.memo(MyComponent);
   ```

3. **Lazy Load Modals**: Only render modals when needed
   ```javascript
   {isOpen && <Modal>...</Modal>}
   ```

---

## Migration Guide

### Migrating Existing Pages

1. **Install Dependencies**: Components are already available, no new dependencies needed

2. **Import Components**:
   ```javascript
   import { Card, MetricDisplay, SignalBadge, TradeButton } from '../components/ui';
   import { colors, spacing, typography } from '../styles/designTokens';
   ```

3. **Replace Existing Elements**:
   ```javascript
   // Before
   <div className="bg-slate-800 p-6 rounded-xl">
     <h3>Win Rate</h3>
     <p>73.5%</p>
   </div>
   
   // After
   <Card>
     <MetricDisplay label="Win Rate" value="73.5%" />
   </Card>
   ```

4. **Maintain Consistency**: Keep existing CSS variables or gradually migrate to design tokens

---

## Support & Questions

For questions or issues with the design system:
1. Check the ComponentShowcase page (`/components` route) for live examples
2. Review this documentation
3. Examine the implementation in `src/components/ui/` directory

---

**Last Updated**: October 15, 2025
**Version**: 1.0.0
