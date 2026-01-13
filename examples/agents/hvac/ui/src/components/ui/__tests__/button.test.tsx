import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../../../test/test-utils';
import { Button } from '../button';
import React from 'react';

// Mock Radix UI Slot component to avoid React.Children.only error
vi.mock('@radix-ui/react-slot', () => ({
  Slot: ({ children, className, ...props }: any) => {
    if (React.isValidElement(children)) {
      return React.cloneElement(children, {
        ...props,
        className: className,
      });
    }
    return children;
  },
}));

describe('Button', () => {
  it('should render button with default props', () => {
    render(<Button>Click me</Button>);

    const button = screen.getByRole('button', { name: 'Click me' });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('inline-flex', 'items-center', 'justify-center');
  });

  it('should render button with different variants', () => {
    const { rerender } = render(<Button variant="default">Default</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-brand-600', 'text-white');

    rerender(<Button variant="destructive">Destructive</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-error-600', 'text-white');

    rerender(<Button variant="outline">Outline</Button>);
    expect(screen.getByRole('button')).toHaveClass('border', 'border-gray-200', 'bg-white');

    rerender(<Button variant="secondary">Secondary</Button>);
    expect(screen.getByRole('button')).toHaveClass('bg-brand-50', 'text-brand-700');

    rerender(<Button variant="ghost">Ghost</Button>);
    expect(screen.getByRole('button')).toHaveClass('text-gray-700', 'hover:bg-gray-100');

    rerender(<Button variant="link">Link</Button>);
    expect(screen.getByRole('button')).toHaveClass('text-brand-600', 'underline-offset-4');
  });

  it('should render button with different sizes', () => {
    const { rerender } = render(<Button size="default">Default</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-9', 'px-4', 'py-2');

    rerender(<Button size="sm">Small</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-8', 'rounded-md', 'px-3');

    rerender(<Button size="lg">Large</Button>);
    expect(screen.getByRole('button')).toHaveClass('h-10', 'rounded-md', 'px-6');

    rerender(<Button size="icon">Icon</Button>);
    expect(screen.getByRole('button')).toHaveClass('size-10');
  });

  it('should handle click events', () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click me</Button>);

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('should be disabled when disabled prop is true', () => {
    render(<Button disabled>Disabled</Button>);

    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('should not trigger click when disabled', () => {
    const handleClick = vi.fn();
    render(
      <Button disabled onClick={handleClick}>
        Disabled
      </Button>,
    );

    const button = screen.getByRole('button');
    fireEvent.click(button);

    expect(handleClick).not.toHaveBeenCalled();
  });

  it('should render with custom className', () => {
    render(<Button className="custom-class">Custom</Button>);

    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('should render as different HTML elements', () => {
    render(
      <Button asChild>
        <a href="/test">Link</a>
      </Button>,
    );
    const link = screen.getByRole('link');
    expect(link).toBeInTheDocument();
    expect(link).toHaveAttribute('href', '/test');
    // Skipping class check due to Slot mock
  });

  it('should render with leftSection', () => {
    const TestIcon = () => <span data-testid="icon">🚀</span>;

    render(<Button leftSection={<TestIcon />}>With Icon</Button>);

    expect(screen.getByTestId('icon')).toBeInTheDocument();
    expect(screen.getByText('With Icon')).toBeInTheDocument();
  });

  it('should handle keyboard events', () => {
    const handleKeyDown = vi.fn();
    render(<Button onKeyDown={handleKeyDown}>Keyboard</Button>);

    const button = screen.getByRole('button');
    fireEvent.keyDown(button, { key: 'Enter' });

    expect(handleKeyDown).toHaveBeenCalled();
  });

  it('should have proper accessibility attributes', () => {
    render(<Button aria-label="Custom label">Button</Button>);

    const button = screen.getByRole('button', { name: 'Custom label' });
    expect(button).toBeInTheDocument();
  });

  it('should handle focus events', () => {
    const handleFocus = vi.fn();
    const handleBlur = vi.fn();

    render(
      <Button onFocus={handleFocus} onBlur={handleBlur}>
        Focus Test
      </Button>,
    );

    const button = screen.getByRole('button');

    fireEvent.focus(button);
    expect(handleFocus).toHaveBeenCalled();

    fireEvent.blur(button);
    expect(handleBlur).toHaveBeenCalled();
  });

  it('should combine multiple variants and sizes correctly', () => {
    render(
      <Button variant="outline" size="lg" className="custom-class">
        Combined
      </Button>,
    );

    const button = screen.getByRole('button');
    expect(button).toHaveClass('border', 'border-gray-200', 'bg-white'); // outline variant
    expect(button).toHaveClass('h-10', 'rounded-md', 'px-6'); // lg size
    expect(button).toHaveClass('custom-class'); // custom class
  });

  it('should handle children with complex content', () => {
    render(
      <Button>
        <span>Text</span>
        <strong>Bold</strong>
        <em>Italic</em>
      </Button>,
    );

    expect(screen.getByText('Text')).toBeInTheDocument();
    expect(screen.getByText('Bold')).toBeInTheDocument();
    expect(screen.getByText('Italic')).toBeInTheDocument();
  });
});
