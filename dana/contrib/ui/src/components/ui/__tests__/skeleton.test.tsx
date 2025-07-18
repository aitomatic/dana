import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/test-utils';
import { Skeleton } from '../skeleton';

describe('Skeleton', () => {
  it('renders skeleton', () => {
    render(<Skeleton data-testid="skeleton" />);
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
  });

  it('applies skeleton classes', () => {
    render(<Skeleton data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveClass('animate-pulse', 'rounded-md', 'bg-accent');
  });

  it('applies custom className', () => {
    render(<Skeleton className="custom-skeleton" data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveClass('custom-skeleton');
  });

  it('renders with custom width and height', () => {
    render(<Skeleton className="w-20 h-10" data-testid="skeleton" />);
    const skeleton = screen.getByTestId('skeleton');
    expect(skeleton).toHaveClass('w-20', 'h-10');
  });

  it('renders skeleton with children', () => {
    render(
      <Skeleton data-testid="skeleton">
        <div>Content</div>
      </Skeleton>,
    );
    expect(screen.getByTestId('skeleton')).toBeInTheDocument();
    expect(screen.getByText('Content')).toBeInTheDocument();
  });
});
