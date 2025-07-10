import * as React from 'react';
import { Slot } from '@radix-ui/react-slot';
import { tv, type VariantProps } from 'tailwind-variants';

import { cn } from '@/lib/utils';

const buttonVariants = tv({
  base: "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-md text-sm font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive cursor-pointer",
  variants: {
    variant: {
      default:
        'bg-brand-600 text-white shadow-xs hover:bg-brand-700 focus-visible:ring-brand-200 dark:focus-visible:ring-brand-800',
      destructive:
        'bg-error-600 text-white shadow-xs hover:bg-error-700 focus-visible:ring-error-200 dark:focus-visible:ring-error-800 dark:bg-error-600',
      outline:
        'border border-gray-200 bg-white text-gray-700 shadow-xs hover:bg-gray-50 hover:border-gray-300 dark:bg-gray-800 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-gray-900/20 dark:hover:border-gray-600',
      secondary:
        'bg-brand-50 text-brand-700 shadow-xs hover:bg-brand-100 dark:bg-brand-900/20 dark:text-brand-300 dark:hover:bg-brand-900/40',
      ghost:
        'text-gray-700 hover:bg-gray-100 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-gray-800 dark:hover:text-gray-100',
      link: 'text-brand-600 underline-offset-4 hover:text-brand-700 hover:underline dark:text-brand-400 dark:hover:text-brand-300',
      success:
        'bg-success-600 text-white shadow-xs hover:bg-success-700 focus-visible:ring-success-200 dark:focus-visible:ring-success-800',
      warning:
        'bg-warning-600 text-white shadow-xs hover:bg-warning-700 focus-visible:ring-warning-200 dark:focus-visible:ring-warning-800',
      tertiary:
        'bg-gray-100 text-gray-700 shadow-xs hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700',
    },
    size: {
      default: 'h-9 px-4 py-2 has-[>svg]:px-3',
      sm: 'h-8 rounded-md gap-1.5 px-3 has-[>svg]:px-2.5',
      lg: 'h-10 rounded-md px-6 has-[>svg]:px-4',
      icon: 'size-10',
    },
  },
  defaultVariants: {
    variant: 'default',
    size: 'lg',
  },
});

interface ButtonProps extends React.ComponentProps<'button'>, VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  leftSection?: React.ReactNode;
}

function Button({
  className,
  variant,
  size,
  asChild = false,
  leftSection,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : 'button';

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size, className }))}
      {...props}
    >
      {leftSection}
      {children}
    </Comp>
  );
}

const IconButton = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    return (
      <Button
        ref={ref}
        variant={variant}
        size={size}
        className={className}
        asChild={asChild}
        {...props}
      />
    );
  },
);
IconButton.displayName = 'IconButton';

export { Button, IconButton };
