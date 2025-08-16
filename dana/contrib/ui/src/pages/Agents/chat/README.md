# Markdown Viewer Component

This component now uses GitHub Markdown CSS instead of custom styling, providing a clean, familiar look that matches GitHub READMEs.

## Features

- **GitHub Markdown Styling**: Uses official GitHub Markdown CSS for consistent, professional appearance
- **Theme Support**: Supports both light and dark themes
- **Math Rendering**: KaTeX integration for mathematical expressions
- **Responsive Design**: Adapts to different screen sizes

## Usage

### Basic Usage

```tsx
import { MarkdownViewerSmall } from './markdown-viewer';

<MarkdownViewerSmall>
  # Hello World
  
  This is **bold text** and *italic text*.
  
  ```python
  print("Hello, World!")
  ```
</MarkdownViewerSmall>
```

### With Theme

```tsx
// Light theme (default)
<MarkdownViewerSmall theme="light">
  # Light Theme Content
</MarkdownViewerSmall>

// Dark theme
<MarkdownViewerSmall theme="dark">
  # Dark Theme Content
</MarkdownViewerSmall>
```

### With Custom Classes

```tsx
<MarkdownViewerSmall 
  classname="custom-markdown-styles"
  theme="light"
>
  # Custom Styled Content
</MarkdownViewerSmall>
```

## Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `children` | `string` | `''` | Markdown content to render |
| `classname` | `string` | `''` | Additional CSS classes |
| `useMath` | `boolean` | `true` | Enable KaTeX math rendering |
| `theme` | `'light' \| 'dark'` | `'light'` | Theme for markdown styling |
| `citations` | `any[]` | `undefined` | Citation data for references |

## Styling

The component now uses GitHub Markdown CSS which provides:

- Clean typography with proper hierarchy
- Consistent spacing and margins
- Professional code block styling
- Responsive table layouts
- Proper list formatting
- Link styling that matches GitHub

### Strong Tags

Strong tags (`**text**`) now render as standard bold text without custom backgrounds or borders, matching GitHub's default styling.

## Demo

Check out the `markdown-demo.tsx` component to see the new styling in action with both light and dark themes.

## Dependencies

- `github-markdown-css`: Official GitHub Markdown CSS
- `react-markdown`: Markdown rendering
- `remark-math`: Math expression support
- `rehype-katex`: KaTeX math rendering
- `katex`: Math typesetting library

## Migration from Custom CSS

If you were previously using custom CSS classes like `styles.content`, replace them with the `markdown-body` class that's automatically applied by this component.

## What Was Fixed

The original issue was that `<strong>` tags had custom styling with:
- `border-radius: 4px !important`
- `border: 1px solid rgba(59, 130, 246, 0.2) !important`
- Blue background and padding

This styling came from the custom CSS module `MarkdownViewer.module.css`. By switching to GitHub Markdown CSS, strong tags now render as standard bold text without any custom backgrounds or borders, exactly like they appear on GitHub.
