import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/test-utils';
import { DragOverComponent } from '../drag-over-component';

describe('DragOverComponent', () => {
  it('renders drag over component with title', () => {
    render(<DragOverComponent title="Drop Files Here" />);
    expect(screen.getByText('Drop Files Here')).toBeInTheDocument();
  });

  it('renders with description', () => {
    render(
      <DragOverComponent title="Drop Files Here" description="Drag and drop files to upload" />,
    );
    expect(screen.getByText('Drop Files Here')).toBeInTheDocument();
    expect(screen.getByText('Drag and drop files to upload')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<DragOverComponent title="Drop Files Here" className="custom-drag" />);
    const container = screen.getByText('Drop Files Here').closest('div')?.parentElement;
    expect(container).toHaveClass('custom-drag');
  });

  it('renders without description when not provided', () => {
    render(<DragOverComponent title="Drop Files Here" />);
    expect(screen.getByText('Drop Files Here')).toBeInTheDocument();
    expect(screen.queryByText('Drag and drop files to upload')).not.toBeInTheDocument();
  });

  it('has proper styling classes', () => {
    render(<DragOverComponent title="Drop Files Here" />);
    const container = screen.getByText('Drop Files Here').closest('div')?.parentElement;
    expect(container).toHaveClass('flex', 'fixed', 'inset-0', 'z-50');
  });
});
