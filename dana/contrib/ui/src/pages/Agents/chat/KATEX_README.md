# KaTeX Math Formula Rendering

This component now includes enhanced KaTeX styling for beautiful math formula rendering that works seamlessly with GitHub Markdown CSS.

## Features

✅ **Inline Math**: Single `$` delimiters for inline formulas  
✅ **Display Math**: Double `$$` delimiters for centered block formulas  
✅ **LaTeX Support**: Full LaTeX command support  
✅ **Responsive Design**: Optimized for mobile and desktop  
✅ **Theme Support**: Light and dark theme compatibility  
✅ **Background Context**: Adapts to user vs agent message backgrounds  
✅ **Professional Styling**: Beautiful gradients, shadows, and spacing  

## Usage

### Basic Math Syntax

#### Inline Math
```markdown
The quadratic formula is $x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}$
```

#### Display Math
```markdown
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```

### Common LaTeX Commands

| Command | Example | Result |
|---------|---------|---------|
| `\frac{a}{b}` | `$\frac{1}{2}$` | Fraction |
| `\sqrt{x}` | `$\sqrt{16}$` | Square root |
| `\sum_{i=1}^{n}` | `$\sum_{i=1}^{n} x_i$` | Summation |
| `\int_{a}^{b}` | `$\int_{0}^{1} f(x) dx$` | Integral |
| `\pi` | `$\pi$` | Pi constant |
| `\alpha, \beta` | `$\alpha, \beta$` | Greek letters |
| `\begin{pmatrix}...\end{pmatrix}` | Matrix syntax | Matrix |

### Math Examples

#### Financial Formulas
```markdown
**Compound Interest:**
$$
FV = PV(1 + r)^n
$$

Where:
- **FV** = Future Value
- **PV** = Present Value
- **r** = Interest Rate
- **n** = Number of Periods
```

#### Physics Formulas
```markdown
**Einstein's Mass-Energy Equivalence:**
$$
E = mc^2
$$

**Gravitational Force:**
$$
F = G\frac{m_1 m_2}{r^2}
$$
```

#### Statistics
```markdown
**Normal Distribution:**
$$
f(x) = \frac{1}{\sigma\sqrt{2\pi}} e^{-\frac{1}{2}\left(\frac{x-\mu}{\sigma}\right)^2}
$$
```

## Implementation Details

### CSS Files

1. **`katex-styling.css`** - Enhanced KaTeX styling with:
   - Beautiful gradients and shadows
   - Responsive design
   - Theme-specific colors
   - Background context awareness

2. **`markdown-theme-switcher.css`** - Theme switching and overrides

### Component Props

```tsx
<MarkdownViewerSmall
  theme="light"                    // 'light' | 'dark'
  backgroundContext="agent"        // 'user' | 'agent' | 'default'
  useMath={true}                   // Enable/disable math rendering
>
  {markdownContent}
</MarkdownViewerSmall>
```

### Math Processing

The component includes intelligent math preprocessing:
- Converts `\[...\]` to `$$...$$` for better KaTeX compatibility
- Cleans up malformed math delimiters
- Preserves proper spacing around formulas

## Styling Features

### Display Math
- **Background**: Subtle gradient backgrounds
- **Borders**: Rounded corners with soft shadows
- **Spacing**: Generous padding and margins
- **Responsive**: Adapts to screen size

### Inline Math
- **Integration**: Seamlessly blends with text
- **Spacing**: Proper vertical alignment
- **Fonts**: Professional mathematical typography

### Theme Support
- **Light Theme**: Soft grays and whites
- **Dark Theme**: Deep blues and grays
- **User Messages**: Gray background adaptation
- **Agent Messages**: White background adaptation

## Demo Components

### MathDemo
A comprehensive demo showcasing various math formulas:
- Basic arithmetic and algebra
- Calculus and integrals
- Statistics and probability
- Financial mathematics
- Physics formulas

### Usage
```tsx
import MathDemo from './math-demo';

// Use in your app
<MathDemo />
```

## Customization

### Adding Custom Math Styles

You can extend the KaTeX styling by adding rules to `katex-styling.css`:

```css
/* Custom math element styling */
.katex .custom-element {
  color: #your-color !important;
  font-weight: bold !important;
}

/* Custom background for specific math types */
.katex-display.financial {
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe) !important;
  border-color: #0ea5e9 !important;
}
```

### Theme-Specific Customization

```css
/* Light theme customizations */
.markdown-body-light .katex-display {
  /* Your custom styles */
}

/* Dark theme customizations */
.markdown-body-dark .katex-display {
  /* Your custom styles */
}
```

## Troubleshooting

### Common Issues

1. **Math not rendering**: Ensure `useMath={true}` is set
2. **Font loading issues**: Check that KaTeX CSS is properly imported
3. **Spacing problems**: Verify math delimiters have proper spacing

### Debug Mode

Enable debug logging by checking the browser console for KaTeX-related messages.

## Dependencies

- **KaTeX**: `^0.16.22` - Math typesetting library
- **rehype-katex**: `^7.0.1` - KaTeX plugin for rehype
- **remark-math**: `^6.0.0` - Math plugin for remark

## Browser Support

- **Modern browsers**: Full support
- **Mobile devices**: Responsive design
- **Print**: Optimized print styles

## Performance

- **Lazy loading**: Dark theme CSS only loads when needed
- **Optimized fonts**: KaTeX fonts are optimized for math rendering
- **Efficient processing**: Minimal preprocessing overhead

---

For more examples and advanced usage, check out the `MathDemo` component!
