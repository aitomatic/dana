import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../../../test/test-utils';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../collapsible';

describe('Collapsible', () => {
  it('renders collapsible with trigger', () => {
    render(
      <Collapsible>
        <CollapsibleTrigger>Toggle</CollapsibleTrigger>
        <CollapsibleContent>Content</CollapsibleContent>
      </Collapsible>,
    );

    expect(screen.getByText('Toggle')).toBeInTheDocument();
  });

  it('expands and collapses on trigger click', () => {
    render(
      <Collapsible>
        <CollapsibleTrigger>Toggle</CollapsibleTrigger>
        <CollapsibleContent>Content</CollapsibleContent>
      </Collapsible>,
    );

    const trigger = screen.getByText('Toggle');
    expect(trigger).toBeInTheDocument();

    // Initially collapsed
    expect(screen.queryByText('Content')).not.toBeInTheDocument();

    // Click to expand
    fireEvent.click(trigger);
    expect(screen.getByText('Content')).toBeInTheDocument();

    // Click to collapse
    fireEvent.click(trigger);
    expect(screen.queryByText('Content')).not.toBeInTheDocument();
  });

  it('starts expanded when open prop is true', () => {
    render(
      <Collapsible open>
        <CollapsibleTrigger>Toggle</CollapsibleTrigger>
        <CollapsibleContent>Content</CollapsibleContent>
      </Collapsible>,
    );

    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('calls onOpenChange when triggered', () => {
    const mockOnOpenChange = vi.fn();
    render(
      <Collapsible onOpenChange={mockOnOpenChange}>
        <CollapsibleTrigger>Toggle</CollapsibleTrigger>
        <CollapsibleContent>Content</CollapsibleContent>
      </Collapsible>,
    );

    const trigger = screen.getByText('Toggle');
    fireEvent.click(trigger);
    expect(mockOnOpenChange).toHaveBeenCalledWith(true);

    fireEvent.click(trigger);
    expect(mockOnOpenChange).toHaveBeenCalledWith(false);
  });

  it('applies custom className to trigger', () => {
    render(
      <Collapsible>
        <CollapsibleTrigger className="custom-trigger">Toggle</CollapsibleTrigger>
        <CollapsibleContent>Content</CollapsibleContent>
      </Collapsible>,
    );

    const trigger = screen.getByText('Toggle');
    expect(trigger).toHaveClass('custom-trigger');
  });
});
