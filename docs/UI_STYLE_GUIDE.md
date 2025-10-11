# Dana UI Style Guide

## Table of Contents
1. [Overview](#overview)
2. [Design System](#design-system)
3. [Component Architecture](#component-architecture)
4. [Naming Conventions](#naming-conventions)
5. [Code Standards](#code-standards)
6. [Accessibility Guidelines](#accessibility-guidelines)
7. [Implementation Best Practices](#implementation-best-practices)
8. [File Organization](#file-organization)
9. [Testing Standards](#testing-standards)
10. [Performance Guidelines](#performance-guidelines)

## Overview

This style guide establishes standards for UI development in the Dana platform, ensuring consistency, maintainability, and scalability across all user interfaces.

### Technology Stack
- **Frontend Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS 4
- **UI Components**: Radix UI + Custom components
- **Icons**: Iconoir React + Tabler Icons
- **State Management**: Zustand
- **Routing**: React Router DOM
- **Code Editor**: Monaco Editor
- **Forms**: React Hook Form
- **Tables**: TanStack React Table

## Design System

### Color Palette

#### Brand Colors (RGB values for opacity support)
```css
/* Primary Dark Brand Colors */
--brand-25: 250 250 250; /* #FAFAFA - Lightest tint */
--brand-50: 245 245 245; /* #F5F5F5 - Very light */
--brand-100: 229 229 229; /* #E5E5E5 - Light */
--brand-200: 212 212 212; /* #D4D4D4 - Soft */
--brand-300: 163 163 163; /* #A3A3A3 - Medium light */
--brand-400: 115 115 115; /* #737373 - Medium */
--brand-500: 15 15 15; /* #0F0F0F - Primary brand dark */
--brand-600: 12 12 12; /* #0C0C0C - Dark */
--brand-700: 10 10 10; /* #0A0A0A - Deep dark */
--brand-800: 7 7 7; /* #070707 - Darker */
--brand-900: 5 5 5; /* #050505 - Very dark */
--brand-950: 3 3 3; /* #030303 - Deepest dark */
```

#### Purple Accent Colors (RGB values for opacity support)
```css
/* Purple Accent Colors */
--purple-25: 252 250 255; /* #FCFAFF - Lightest purple tint */
--purple-50: 245 243 254; /* #F5F3FE - Very light purple */
--purple-100: 235 230 253; /* #EBE6FD - Light purple */
--purple-200: 215 205 251; /* #D7CDFB - Soft purple */
--purple-300: 175 159 247; /* #AF9FF7 - Medium light purple */
--purple-400: 139 117 255; /* #8B75FF - Purple light */
--purple-500: 107 79 255; /* #6B4FFF - Primary purple accent */
--purple-600: 85 56 232; /* #5538E8 - Purple dark */
--purple-700: 68 45 186; /* #442DBA - Deep purple */
--purple-800: 54 36 149; /* #362495 - Darker purple */
--purple-900: 45 30 125; /* #2D1E7D - Very dark purple */
--purple-950: 29 19 73; /* #1D1349 - Deepest purple */
```

#### Blue Colors (RGB values for opacity support)
```css
/* Secondary Blue Colors */
--blue-25: 241 248 255; /* #F1F8FF */
--blue-50: 239 246 255; /* #EFF6FF */
--blue-100: 219 234 254; /* #DBEAFE */
--blue-200: 191 219 254; /* #BFDBFE */
--blue-300: 147 197 253; /* #93C5FD */
--blue-400: 96 165 250; /* #60A5FA */
--blue-500: 79 127 255; /* #4F7FFF - Secondary blue */
--blue-600: 37 99 235; /* #2563EB */
--blue-700: 29 78 216; /* #1D4ED8 */
--blue-800: 30 64 175; /* #1E40AF */
--blue-900: 30 58 138; /* #1E3A8A */
--blue-950: 23 37 84; /* #172554 */
```

#### Cyan/Teal Colors (RGB values for opacity support)
```css
/* Cyan Accent Colors */
--cyan-25: 240 253 255; /* #F0FDFF */
--cyan-50: 236 254 255; /* #ECFEFF */
--cyan-100: 207 250 254; /* #CFFAFE */
--cyan-200: 165 243 252; /* #A5F3FC */
--cyan-300: 103 232 249; /* #67E8F9 */
--cyan-400: 79 204 255; /* #4FCCFF - Primary cyan accent */
--cyan-500: 6 182 212; /* #06B6D4 */
--cyan-600: 8 145 178; /* #0891B2 */
--cyan-700: 14 116 144; /* #0E7490 */
--cyan-800: 21 94 117; /* #155E75 */
--cyan-900: 22 78 99; /* #164E63 */
--cyan-950: 8 51 68; /* #083344 */
```

#### Pink/Rose Colors (RGB values for opacity support)
```css
/* Pink Accent Colors */
--pink-25: 255 248 252; /* #FFF8FC */
--pink-50: 253 242 248; /* #FDF2F8 */
--pink-100: 252 231 243; /* #FCE7F3 */
--pink-200: 251 207 232; /* #FBCFE8 */
--pink-300: 249 168 212; /* #F9A8D4 */
--pink-400: 244 114 182; /* #F472B6 */
--pink-500: 255 107 157; /* #FF6B9D - Primary pink accent */
--pink-600: 219 39 119; /* #DB2777 */
--pink-700: 190 24 93; /* #BE185D */
--pink-800: 157 23 77; /* #9D174D */
--pink-900: 131 24 67; /* #831843 */
--pink-950: 80 7 36; /* #500724 */
```

#### Background & Surface Colors (RGB values for opacity support)
```css
/* Dark Theme Backgrounds */
--background-darkest: 5 5 7; /* #050507 - Deepest background */
--background-darker: 10 11 15; /* #0A0B0F - Darker background */
--background-dark: 16 17 23; /* #101117 - Dark background */
--surface-darker: 18 19 26; /* #12131A - Darker surface */
--surface-dark: 26 27 33; /* #1A1B21 - Dark surface */
--surface: 32 33 41; /* #202129 - Base surface */
--surface-light: 42 43 51; /* #2A2B33 - Light surface */
```

#### Neutral Colors (RGB values for opacity support)
```css
/* Gray Scale (Optimized for dark theme) */
--gray-25: 252 252 253; /* #FCFCFD */
--gray-50: 249 250 251; /* #F9FAFB */
--gray-100: 242 244 247; /* #F2F4F7 */
--gray-200: 228 231 236; /* #E4E7EC */
--gray-300: 208 213 221; /* #D0D5DD */
--gray-400: 152 162 179; /* #98A2B3 */
--gray-500: 107 108 116; /* #6B6C74 - Tertiary text */
--gray-600: 71 84 103; /* #475467 */
--gray-700: 52 64 84; /* #344054 */
--gray-800: 24 34 48; /* #182230 */
--gray-900: 16 24 40; /* #101828 */
--gray-950: 12 17 29; /* #0C111D */
```

#### Text Colors (RGB values for opacity support)
```css
/* Text Colors (Optimized for dark backgrounds) */
--text-primary: 255 255 255; /* #FFFFFF - Primary text on dark */
--text-secondary: 184 185 192; /* #B8B9C0 - Secondary text */
--text-tertiary: 107 108 116; /* #6B6C74 - Tertiary text */
--text-quaternary: 82 83 91; /* #52535B - Quaternary text */
--text-disabled: 62 63 70; /* #3E3F46 - Disabled text */
```

#### Semantic Colors (RGB values for opacity support)
```css
/* Success Colors */
--success-25: 240 254 251; /* #F0FEFB */
--success-50: 236 253 245; /* #ECFDF5 */
--success-100: 209 250 229; /* #D1FAE5 */
--success-200: 167 243 208; /* #A7F3D0 */
--success-300: 110 231 183; /* #6EE7B7 */
--success-400: 79 255 176; /* #4FFFB0 - Primary success accent */
--success-500: 16 185 129; /* #10B981 */
--success-600: 5 150 105; /* #059669 */
--success-700: 4 120 87; /* #047857 */
--success-800: 6 95 70; /* #065F46 */
--success-900: 6 78 59; /* #064E3B */
--success-950: 2 44 34; /* #022C22 */

/* Warning Colors */
--warning-25: 255 253 250; /* #FFFDFA */
--warning-50: 255 251 235; /* #FFFBEB */
--warning-100: 254 243 199; /* #FEF3C7 */
--warning-200: 253 230 138; /* #FDE68A */
--warning-300: 252 211 77; /* #FCD34D */
--warning-400: 255 232 79; /* #FFE84F - Primary warning accent */
--warning-500: 245 158 11; /* #F59E0B */
--warning-600: 217 119 6; /* #D97706 */
--warning-700: 180 83 9; /* #B45309 */
--warning-800: 146 64 14; /* #92400E */
--warning-900: 120 53 15; /* #78350F */
--warning-950: 69 26 3; /* #451A03 */

/* Error Colors */
--error-25: 255 251 250; /* #FFFBFA */
--error-50: 254 242 242; /* #FEF2F2 */
--error-100: 254 226 226; /* #FEE2E2 */
--error-200: 254 202 202; /* #FECACA */
--error-300: 252 165 165; /* #FCA5A5 */
--error-400: 248 113 113; /* #F87171 */
--error-500: 255 79 79; /* #FF4F4F - Primary error */
--error-600: 220 38 38; /* #DC2626 */
--error-700: 185 28 28; /* #B91C1C */
--error-800: 153 27 27; /* #991B1B */
--error-900: 127 29 29; /* #7F1D1D */
--error-950: 69 10 10; /* #450A0A */

/* Info Colors */
--info-25: 240 249 255; /* #F0F9FF */
--info-50: 240 249 255; /* #F0F9FF */
--info-100: 224 242 254; /* #E0F2FE */
--info-200: 186 230 253; /* #BAE6FD */
--info-300: 125 211 252; /* #7DD3FC */
--info-400: 79 159 255; /* #4F9FFF - Primary info */
--info-500: 14 165 233; /* #0EA5E9 */
--info-600: 2 132 199; /* #0284C7 */
--info-700: 3 105 161; /* #0369A1 */
--info-800: 7 89 133; /* #075985 */
--info-900: 12 74 110; /* #0C4A6E */
--info-950: 8 47 73; /* #082F49 */
```

#### Gradient Definitions
```css
/* Primary Gradients */
--gradient-purple-primary: linear-gradient(135deg, rgb(107, 79, 255) 0%, rgb(155, 127, 255) 100%);
--gradient-blue-secondary: linear-gradient(135deg, rgb(79, 127, 255) 0%, rgb(79, 204, 255) 100%);
--gradient-pink-accent: linear-gradient(135deg, rgb(255, 107, 157) 0%, rgb(155, 127, 255) 100%);

/* Background Gradients */
--gradient-dark-vertical: linear-gradient(180deg, rgb(26, 27, 33) 0%, rgb(10, 11, 15) 100%);
--gradient-dark-radial: radial-gradient(circle at center, rgba(107, 79, 255, 0.2) 0%, transparent 70%);

/* Glow Effects */
--gradient-glow-purple: radial-gradient(circle at center, rgba(107, 79, 255, 0.3) 0%, transparent 70%);
--gradient-glow-blue: radial-gradient(circle at center, rgba(79, 127, 255, 0.3) 0%, transparent 70%);
--gradient-glow-cyan: radial-gradient(circle at center, rgba(79, 204, 255, 0.3) 0%, transparent 70%);

/* Animated Gradients (for interactive elements) */
--gradient-animated: linear-gradient(
  270deg,
  rgb(107, 79, 255),
  rgb(155, 127, 255),
  rgb(79, 127, 255),
  rgb(79, 204, 255)
);
```


### Typography

#### Font Family
```css
font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol', 'Noto Color Emoji';
```

#### Font Sizes
- **xs**: 12px (0.75rem)
- **sm**: 14px (0.875rem)
- **base**: 16px (1rem)
- **lg**: 18px (1.125rem)
- **xl**: 20px (1.25rem)
- **2xl**: 24px (1.5rem)
- **3xl**: 30px (1.875rem)
- **4xl**: 36px (2.25rem)

#### Font Weights
- **normal**: 400
- **medium**: 500
- **semibold**: 600
- **bold**: 700
- **extrabold**: 800

### Spacing System

#### Base Spacing Scale
- **0**: 0px
- **1**: 4px (0.25rem)
- **2**: 8px (0.5rem)
- **3**: 12px (0.75rem)
- **4**: 16px (1rem)
- **5**: 20px (1.25rem)
- **6**: 24px (1.5rem)
- **8**: 32px (2rem)
- **10**: 40px (2.5rem)
- **12**: 48px (3rem)
- **16**: 64px (4rem)
- **20**: 80px (5rem)
- **24**: 96px (6rem)

### Border Radius
```css
--radius: 0.75rem; /* Updated to 12px for modern feel */
--radius-sm: calc(var(--radius) - 4px);
--radius-md: calc(var(--radius) - 2px);
--radius-lg: var(--radius);
--radius-xl: calc(var(--radius) + 4px);
--radius-2xl: 1.5rem; /* 24px */
--radius-full: 9999px;
```

### Shadows & Effects
```css
/* Custom shadow variables (Updated for dark theme) */
--shadow-color: 0, 0, 0;
--shadow-opacity-sm: 0.12;
--shadow-opacity-default: 0.16;
--shadow-opacity-md: 0.20;
--shadow-opacity-lg: 0.24;
--shadow-opacity-xl: 0.30;
--shadow-opacity-2xl: 0.40;
--shadow-opacity-inner: 0.10;

/* Shadow definitions */
--shadow-xs: 0 1px 2px 0 rgba(var(--shadow-color), var(--shadow-opacity-sm));
--shadow: 0 1px 3px 0 rgba(var(--shadow-color), var(--shadow-opacity-default)), 0 1px 2px 0 rgba(var(--shadow-color), 0.08);
--shadow-md: 0 4px 6px -1px rgba(var(--shadow-color), var(--shadow-opacity-md)), 0 2px 4px -1px rgba(var(--shadow-color), 0.08);
--shadow-lg: 0 10px 15px -3px rgba(var(--shadow-color), var(--shadow-opacity-lg)), 0 4px 6px -2px rgba(var(--shadow-color), 0.10);
--shadow-xl: 0 20px 25px -5px rgba(var(--shadow-color), var(--shadow-opacity-xl)), 0 10px 10px -5px rgba(var(--shadow-color), 0.08);
--shadow-2xl: 0 25px 50px -12px rgba(var(--shadow-color), var(--shadow-opacity-2xl));
--shadow-inner: inset 0 2px 4px 0 rgba(var(--shadow-color), var(--shadow-opacity-inner));

/* Glow Shadows (Ctrl.xyz style) */
--shadow-glow-purple: 0 0 40px rgba(107, 79, 255, 0.3);
--shadow-glow-blue: 0 0 40px rgba(79, 127, 255, 0.3);
--shadow-glow-cyan: 0 0 40px rgba(79, 204, 255, 0.3);
--shadow-glow-pink: 0 0 40px rgba(255, 107, 157, 0.3);

/* Glassmorphism Effects (Ctrl.xyz style) */
--glass-light: rgba(255, 255, 255, 0.05);
--glass-medium: rgba(255, 255, 255, 0.08);
--glass-strong: rgba(255, 255, 255, 0.12);
--glass-blur: blur(20px);
```

## Component Architecture

### Component Structure

All UI components should follow this structure:

```tsx
import * as React from 'react';
import { tv, type VariantProps } from 'tailwind-variants';
import { cn } from '@/lib/utils';

// Define variants using tailwind-variants
const componentVariants = tv({
  base: "base-styles-here",
  variants: {
    variant: {
      default: "default-variant-styles",
      secondary: "secondary-variant-styles",
    },
    size: {
      sm: "small-size-styles",
      md: "medium-size-styles",
      lg: "large-size-styles",
    },
  },
  defaultVariants: {
    variant: 'default',
    size: 'md',
  },
});

interface ComponentProps 
  extends React.ComponentProps<'div'>, 
    VariantProps<typeof componentVariants> {
  // Additional props specific to this component
}

const Component = React.forwardRef<HTMLDivElement, ComponentProps>(
  ({ className, variant, size, ...props }, ref) => {
    return (
      <div
        ref={ref}
        data-slot="component"
        className={cn(componentVariants({ variant, size, className }))}
        {...props}
      />
    );
  }
);

Component.displayName = 'Component';

export { Component };
```

**Note**: Some components use `class-variance-authority` (cva) instead of `tailwind-variants` (tv). Both are acceptable, but prefer `tailwind-variants` for new components.

### Component Variants (Updated with Ctrl.xyz colors)

#### Button Variants
- **default**: Primary brand button (`bg-brand-500 text-white hover:bg-brand-600`)
- **gradient**: Gradient brand button (`bg-gradient-brand-primary text-white`)
- **destructive**: Error/danger actions (`bg-error-500 text-white hover:bg-error-600`)
- **outline**: Secondary actions (`border border-gray-700 bg-transparent text-gray-100 hover:bg-gray-800`)
- **secondary**: Subtle actions (`bg-surface-dark text-gray-100 hover:bg-surface`)
- **ghost**: Minimal actions (`text-gray-100 hover:bg-surface-dark`)
- **link**: Text-based actions (`text-brand-500 hover:text-brand-400`)
- **success**: Success actions (`bg-success-400 text-gray-900 hover:bg-success-500`)
- **warning**: Warning actions (`bg-warning-400 text-gray-900 hover:bg-warning-500`)
- **glass**: Glassmorphism button (`bg-glass-medium backdrop-blur-xl border border-glass-light`)

#### Button Sizes
- **sm**: Small (h-8, px-3, text-sm)
- **default**: Medium (h-9, px-4, text-base)
- **lg**: Large (h-10, px-6, text-lg) - **Default size**
- **icon**: Icon-only (size-10)

#### Input Sizes
- **sm**: Small (h-8, px-2.5, text-sm)
- **default**: Medium (h-9, px-3, text-base)
- **lg**: Large (h-10, px-4, text-lg) - **Default size**

#### Card Variants (Updated for dark theme)
- **default**: Standard card (`bg-surface-dark border border-gray-800`)
- **glass**: Glassmorphism card (`bg-glass-medium backdrop-blur-xl border border-glass-light`)
- **elevated**: Elevated card (`bg-surface-dark border border-gray-800 shadow-lg`)
- **interactive**: Interactive card (`bg-surface-dark hover:bg-surface hover:border-brand-500`)
- **gradient**: Gradient border card (`bg-surface-dark border-2 border-transparent bg-gradient-brand-primary`)

#### Badge Variants
- **default**: Primary badge (`bg-brand-500 text-white`)
- **secondary**: Secondary badge (`bg-surface-dark text-gray-100`)
- **success**: Success badge (`bg-success-400 text-gray-900`)
- **warning**: Warning badge (`bg-warning-400 text-gray-900`)
- **error**: Error badge (`bg-error-500 text-white`)
- **outline**: Outlined badge (`border border-brand-500 text-brand-400`)

## Naming Conventions

### Files and Directories
- **Components**: PascalCase (`Button.tsx`, `DataTable.tsx`)
- **Pages**: PascalCase (`Agents/index.tsx`, `Library/index.tsx`)
- **Hooks**: camelCase with `use` prefix (`use-sidebar.ts`, `useAgentStore.ts`)
- **Utilities**: camelCase (`utils.ts`, `api.ts`)
- **Types**: PascalCase (`types.ts`)

### Component Names
- Use PascalCase for component names
- Use descriptive names that indicate purpose
- Include component type in name when ambiguous (`Button`, `Input`, `Dialog`)

### CSS Classes
- Use Tailwind CSS utility classes
- Use `cn()` utility for conditional classes
- Use semantic class names for custom styles
- Follow BEM methodology for complex custom components

### Variables and Functions
- Use camelCase for variables and functions
- Use descriptive names
- Prefix boolean variables with `is`, `has`, `can`, `should`
- Use verb-noun pattern for functions (`fetchAgent`, `updateUser`)

## Code Standards

### TypeScript Standards
- Use strict TypeScript configuration
- Define interfaces for all props
- Use generic types where appropriate
- Export types alongside components
- Use `React.ComponentProps` for extending HTML element props

### Import Organization
```tsx
// 1. React imports
import * as React from 'react';

// 2. Third-party library imports
import { tv, type VariantProps } from 'tailwind-variants';
import { Slot } from '@radix-ui/react-slot';

// 3. Internal imports (utilities first, then components)
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

// 4. Type imports
import type { ComponentProps } from '@/types';
```

### Component Props
- Always define prop interfaces
- Use `React.ComponentProps` for HTML element props
- Use `VariantProps` for tailwind-variants or cva
- Make props optional when appropriate
- Provide default values in variants
- Include `data-slot` attribute for component identification

### Event Handlers
- Use descriptive names (`handleSubmit`, `onFileSelect`)
- Use arrow functions for inline handlers
- Use `useCallback` for complex handlers passed as props
- Prefix with `on` for callback props

## Accessibility Guidelines

### ARIA Labels
- Always provide `aria-label` for icon buttons
- Use `aria-describedby` for form validation
- Use `aria-expanded` for collapsible content
- Use `aria-selected` for selectable items

### Keyboard Navigation
- Ensure all interactive elements are keyboard accessible
- Use proper tab order
- Provide keyboard shortcuts for common actions
- Use `onKeyDown` handlers for custom keyboard interactions

### Focus Management
- Use `focus-visible` styles for keyboard focus
- Manage focus in modals and dialogs
- Provide visible focus indicators with brand colors
- Use `tabIndex` appropriately

### Color Contrast
- Ensure minimum 4.5:1 contrast ratio for normal text
- Ensure minimum 3:1 contrast ratio for large text
- Text colors optimized for dark backgrounds
- Test with color blindness simulators

### Screen Reader Support
- Use semantic HTML elements
- Provide alternative text for images
- Use proper heading hierarchy
- Provide descriptive link text

## Implementation Best Practices

### Dark Theme First
- All components designed for dark backgrounds
- Use appropriate text colors for dark theme
- Leverage glassmorphism effects for depth
- Use gradient accents sparingly for emphasis

### State Management
- Use Zustand for global state
- Use React hooks for local component state
- Use React Hook Form for form state
- Keep state as close to where it's used as possible

### Performance Optimization
- Use `React.memo` for expensive components
- Use `useCallback` and `useMemo` appropriately
- Implement virtual scrolling for large lists
- Use code splitting for route-based components
- Optimize gradient and glassmorphism effects

### Error Handling
- Use error boundaries for component errors
- Provide user-friendly error messages with semantic colors
- Log errors for debugging
- Handle loading and error states gracefully

### Responsive Design
- Use mobile-first approach
- Test on multiple screen sizes
- Use Tailwind's responsive prefixes
- Implement proper touch targets (minimum 44px)

### Animation & Transitions
```css
/* Transition timing */
--transition-fast: 150ms ease;
--transition-normal: 300ms ease;
--transition-slow: 500ms ease;

/* Hover animations */
.hover-lift {
  transition: transform var(--transition-normal);
}

.hover-lift:hover {
  transform: translateY(-2px);
}

/* Glow pulse animation */
@keyframes glow-pulse {
  0%, 100% { opacity: 0.6; }
  50% { opacity: 1; }
}

.animate-glow {
  animation: glow-pulse 3s ease-in-out infinite;
}

/* Gradient shift animation */
@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

.animate-gradient {
  background-size: 200% 200%;
  animation: gradient-shift 10s ease infinite;
}
```

## File Organization

### Directory Structure
```
src/
├── components/          # Reusable UI components
│   ├── ui/             # Base UI components (buttons, inputs, etc.)
│   ├── agent-editor/   # Agent-specific components
│   ├── library/        # Library-specific components
│   └── table/          # Table components
├── hooks/              # Custom React hooks
├── pages/              # Page components
│   ├── Agents/         # Agent management pages
│   └── Library/        # Library pages
├── stores/             # Zustand state stores
├── types/              # TypeScript type definitions
└── lib/                # Utility functions
```

### Component Organization
- Group related components in subdirectories
- Use index files for clean imports
- Keep component files focused and single-purpose
- Separate complex components into smaller pieces

## Testing Standards

### Component Testing
- Write unit tests for all components
- Test component variants and states
- Test accessibility features
- Test dark theme rendering
- Use React Testing Library

### Integration Testing
- Test user workflows
- Test API integrations
- Test error scenarios
- Test responsive behavior
- Test gradient and animation effects

### Visual Regression Testing
- Use Storybook for component documentation
- Capture screenshots for visual regression testing
- Test across different browsers and devices
- Test glassmorphism effects across platforms

## Performance Guidelines

### Bundle Size
- Use dynamic imports for large components
- Optimize images and assets
- Remove unused dependencies
- Use tree shaking effectively
- Lazy load heavy animations

### Runtime Performance
- Minimize re-renders
- Use proper dependency arrays in hooks
- Implement proper cleanup in useEffect
- Use React DevTools Profiler
- Optimize gradient rendering

### Loading Performance
- Implement proper loading states with skeleton screens
- Use skeleton screens matching dark theme
- Optimize critical rendering path
- Use service workers for caching
- Preload critical assets

## Usage Examples

### Primary Button with Gradient
```tsx
<Button variant="gradient" size="lg">
  Get Started
</Button>
```

### Glass Card Component
```tsx
<Card variant="glass" className="p-6">
  <CardHeader>
    <CardTitle>Feature Title</CardTitle>
  </CardHeader>
  <CardContent>
    <p className="text-gray-300">Content here</p>
  </CardContent>
</Card>
```

### Interactive Card with Hover Effect
```tsx
<Card variant="interactive" className="hover-lift">
  <div className="flex items-center gap-4">
    <div className="w-12 h-12 rounded-lg bg-gradient-brand-primary flex items-center justify-center">
      <Icon />
    </div>
    <div>
      <h3 className="text-white font-semibold">Title</h3>
      <p className="text-gray-400 text-sm">Description</p>
    </div>
  </div>
</Card>
```

## Conclusion

This style guide should be followed consistently across all UI development in the Dana platform. The updated color palette from Ctrl.xyz provides a modern, premium aesthetic optimized for dark theme interfaces with vibrant gradient accents.

Regular reviews and updates ensure the guide remains relevant and effective. All team members should be familiar with these standards and apply them in their daily development work.

For questions or suggestions about this style guide, please refer to the development team or create an issue in the project repository.
