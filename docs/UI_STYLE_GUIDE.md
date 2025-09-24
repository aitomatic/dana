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
/* Brand Colors (New Dark Theme) */
--brand-25: 248 249 250; /* #F8F9FA */
--brand-50: 241 243 245; /* #F1F3F5 */
--brand-100: 233 236 239; /* #E9ECEF */
--brand-200: 206 212 218; /* #CED4DA */
--brand-300: 173 181 189; /* #ADB5BD */
--brand-400: 108 117 125; /* #6C757D */
--brand-500: 16 24 40; /* #101828 */
--brand-600: 12 17 29; /* #0C111D */
--brand-700: 8 12 20; /* #080C14 */
--brand-800: 4 6 10; /* #04060A */
--brand-900: 2 3 5; /* #020305 */
--brand-950: 1 1 2; /* #010102 */
```

#### Blue Colors (RGB values for opacity support)
```css
/* Blue Colors (Formerly Brand Colors) */
--blue-25: 241 245 254; /* #F1F5FE */
--blue-50: 239 244 254; /* #EFF4FE */
--blue-100: 225 235 254; /* #E1EBFE */
--blue-200: 201 216 252; /* #C9D8FC */
--blue-300: 168 191 249; /* #A8BFF9 */
--blue-400: 134 156 243; /* #869CF3 */
--blue-500: 105 121 235; /* #6979EB */
--blue-600: 61 69 220; /* #3D45DC */
--blue-700: 62 66 196; /* #3E42C4 */
--blue-800: 53 58 158; /* #353A9E */
--blue-900: 49 54 126; /* #31367E */
--blue-950: 29 31 73; /* #1D1F49 */
```

#### Semantic Colors (RGB values for opacity support)
```css
/* Success Colors */
--success-25: 250 255 251; /* #FAFFFB */
--success-50: 240 253 244; /* #F0FDF4 */
--success-100: 220 252 231; /* #DCFCE7 */
--success-200: 187 247 208; /* #BBF7D0 */
--success-300: 134 239 172; /* #86EFAC */
--success-400: 74 222 128; /* #4ADE80 */
--success-500: 34 197 94; /* #22C55E */
--success-600: 22 163 74; /* #16A34A */
--success-700: 21 128 61; /* #15803D */
--success-800: 22 101 52; /* #166534 */
--success-900: 20 83 45; /* #14532D */
--success-950: 5 46 22; /* #052E16 */

/* Warning Colors */
--warning-25: 255 253 250; /* #FFFDFA */
--warning-50: 255 251 235; /* #FFFBF0 */
--warning-100: 254 243 199; /* #FEF3C7 */
--warning-200: 253 230 138; /* #FDE68A */
--warning-300: 252 211 77; /* #FCD34D */
--warning-400: 251 191 36; /* #FBBF24 */
--warning-500: 245 158 11; /* #F59E0B */
--warning-600: 217 119 6; /* #D97706 */
--warning-700: 180 83 9; /* #B45309 */
--warning-800: 146 64 14; /* #92400E */
--warning-900: 120 53 15; /* #78350F */
--warning-950: 69 26 3; /* #451A03 */

/* Error Colors */
--error-25: 255 251 250; /* #FFFBF9 */
--error-50: 254 242 242; /* #FEF2F2 */
--error-100: 254 226 226; /* #FEE2E2 */
--error-200: 254 202 202; /* #FECACA */
--error-300: 252 165 165; /* #FCA5A5 */
--error-400: 248 113 113; /* #F87171 */
--error-500: 239 68 68; /* #EF4444 */
--error-600: 220 38 38; /* #DC2626 */
--error-700: 185 28 28; /* #B91C1C */
--error-800: 153 27 27; /* #991B1B */
--error-900: 127 29 29; /* #7F1D1D */
--error-950: 69 10 10; /* #450A0A */
```

#### Neutral Colors (RGB values for opacity support)
```css
/* Gray Scale */
--gray-25: 252 252 253; /* #FCFCFD */
--gray-50: 249 250 251; /* #F9FAFB */
--gray-100: 242 244 247; /* #F2F4F7 */
--gray-200: 228 231 236; /* #E4E7EC */
--gray-300: 208 213 221; /* #D0D5DD */
--gray-400: 152 162 179; /* #98A2B3 */
--gray-500: 102 112 133; /* #667085 */
--gray-600: 71 84 103; /* #475467 */
--gray-700: 52 64 84; /* #344054 */
--gray-800: 24 34 48; /* #182230 */
--gray-900: 16 24 40; /* #101828 */
--gray-950: 12 17 29; /* #0C111D */
```

#### Additional Colors
```css
/* Purple/Indigo colors */
--purple-25: 253 252 255; /* #FDFCFF */
--purple-50: 250 245 255; /* #FAF5FF */
--indigo-25: 248 250 255; /* #F8FAFF */
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
--radius: 0.625rem;
--radius-sm: calc(var(--radius) - 4px);
--radius-md: calc(var(--radius) - 2px);
--radius-lg: var(--radius);
--radius-xl: calc(var(--radius) + 4px);
```

### Shadows
```css
/* Custom shadow variables */
--shadow-color: 0, 0, 0;
--shadow-opacity-sm: 0.05;
--shadow-opacity-default: 0.1;
--shadow-opacity-md: 0.1;
--shadow-opacity-lg: 0.12;
--shadow-opacity-xl: 0.14;
--shadow-opacity-2xl: 0.25;
--shadow-opacity-inner: 0.06;

/* Shadow definitions */
--shadow-xs: 0 1px 2px 0 rgba(var(--shadow-color), var(--shadow-opacity-sm));
--shadow: 0 1px 3px 0 rgba(var(--shadow-color), var(--shadow-opacity-default)), 0 1px 2px 0 rgba(var(--shadow-color), 0.06);
--shadow-md: 0 4px 6px -1px rgba(var(--shadow-color), var(--shadow-opacity-md)), 0 2px 4px -1px rgba(var(--shadow-color), 0.06);
--shadow-lg: 0 10px 15px -3px rgba(var(--shadow-color), var(--shadow-opacity-lg)), 0 4px 6px -2px rgba(var(--shadow-color), 0.05);
--shadow-xl: 0 20px 25px -5px rgba(var(--shadow-color), var(--shadow-opacity-xl)), 0 10px 10px -5px rgba(var(--shadow-color), 0.04);
--shadow-2xl: 0 25px 50px -12px rgba(var(--shadow-color), var(--shadow-opacity-2xl));
--shadow-inner: inset 0 2px 4px 0 rgba(var(--shadow-color), var(--shadow-opacity-inner));
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

### Component Variants

#### Button Variants
- **default**: Primary brand button (`bg-brand-500 text-white`)
- **destructive**: Error/danger actions (`bg-error-600 text-white`)
- **outline**: Secondary actions (`border border-gray-200 bg-white text-gray-700`)
- **secondary**: Subtle actions (`bg-brand-50 text-brand-700`)
- **ghost**: Minimal actions (`text-gray-700 hover:bg-gray-100`)
- **link**: Text-based actions (`text-brand-500 hover:text-brand-600`)
- **success**: Success actions (`bg-success-600 text-white`)
- **warning**: Warning actions (`bg-warning-600 text-white`)
- **tertiary**: Neutral actions (`bg-gray-100 text-gray-700`)

#### Button Sizes
- **sm**: Small (h-8, px-3)
- **default**: Medium (h-9, px-4)
- **lg**: Large (h-10, px-6) - **Default size**
- **icon**: Icon-only (size-10)

#### Input Sizes
- **sm**: Small (h-8, px-2.5)
- **default**: Medium (h-9, px-3)
- **lg**: Large (h-10, px-4) - **Default size**

#### Badge Variants
- **default**: Primary badge (`border-transparent bg-primary text-primary-foreground`)
- **secondary**: Secondary badge (`border-transparent bg-secondary text-secondary-foreground`)
- **destructive**: Error badge (`border-transparent bg-destructive text-destructive-foreground`)
- **outline**: Outlined badge (`text-foreground`)

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
- Provide visible focus indicators
- Use `tabIndex` appropriately

### Color Contrast
- Ensure minimum 4.5:1 contrast ratio for normal text
- Ensure minimum 3:1 contrast ratio for large text
- Don't rely solely on color to convey information
- Test with color blindness simulators

### Screen Reader Support
- Use semantic HTML elements
- Provide alternative text for images
- Use proper heading hierarchy
- Provide descriptive link text

## Implementation Best Practices

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

### Error Handling
- Use error boundaries for component errors
- Provide user-friendly error messages
- Log errors for debugging
- Handle loading and error states gracefully

### Responsive Design
- Use mobile-first approach
- Test on multiple screen sizes
- Use Tailwind's responsive prefixes
- Implement proper touch targets (minimum 44px)

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
- Use React Testing Library

### Integration Testing
- Test user workflows
- Test API integrations
- Test error scenarios
- Test responsive behavior

### Visual Regression Testing
- Use Storybook for component documentation
- Capture screenshots for visual regression testing
- Test across different browsers and devices

## Performance Guidelines

### Bundle Size
- Use dynamic imports for large components
- Optimize images and assets
- Remove unused dependencies
- Use tree shaking effectively

### Runtime Performance
- Minimize re-renders
- Use proper dependency arrays in hooks
- Implement proper cleanup in useEffect
- Use React DevTools Profiler

### Loading Performance
- Implement proper loading states
- Use skeleton screens
- Optimize critical rendering path
- Use service workers for caching

## Conclusion

This style guide should be followed consistently across all UI development in the Dana platform. Regular reviews and updates ensure the guide remains relevant and effective. All team members should be familiar with these standards and apply them in their daily development work.

For questions or suggestions about this style guide, please refer to the development team or create an issue in the project repository.
