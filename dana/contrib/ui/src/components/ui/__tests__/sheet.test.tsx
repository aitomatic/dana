import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '../../../test/test-utils';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../sheet';

describe('Sheet', () => {
  it('renders sheet trigger', () => {
    render(
      <Sheet>
        <SheetTrigger>Open Sheet</SheetTrigger>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Sheet Title</SheetTitle>
            <SheetDescription>Sheet Description</SheetDescription>
          </SheetHeader>
        </SheetContent>
      </Sheet>,
    );

    expect(screen.getByText('Open Sheet')).toBeInTheDocument();
  });

  it('opens sheet on trigger click', () => {
    render(
      <Sheet>
        <SheetTrigger>Open Sheet</SheetTrigger>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Sheet Title</SheetTitle>
          </SheetHeader>
          <div>Sheet Content</div>
        </SheetContent>
      </Sheet>,
    );

    const trigger = screen.getByText('Open Sheet');
    fireEvent.click(trigger);

    expect(screen.getByText('Sheet Title')).toBeInTheDocument();
    expect(screen.getByText('Sheet Content')).toBeInTheDocument();
  });

  it('renders sheet with header and content', () => {
    render(
      <Sheet open>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Sheet Title</SheetTitle>
            <SheetDescription>Sheet Description</SheetDescription>
          </SheetHeader>
          <div>Sheet Content</div>
        </SheetContent>
      </Sheet>,
    );

    expect(screen.getByText('Sheet Title')).toBeInTheDocument();
    expect(screen.getByText('Sheet Description')).toBeInTheDocument();
    expect(screen.getByText('Sheet Content')).toBeInTheDocument();
  });

  it('calls onOpenChange when triggered', () => {
    const mockOnOpenChange = vi.fn();
    render(
      <Sheet onOpenChange={mockOnOpenChange}>
        <SheetTrigger>Open Sheet</SheetTrigger>
        <SheetContent>
          <SheetHeader>
            <SheetTitle>Sheet Title</SheetTitle>
          </SheetHeader>
        </SheetContent>
      </Sheet>,
    );

    const trigger = screen.getByText('Open Sheet');
    fireEvent.click(trigger);
    expect(mockOnOpenChange).toHaveBeenCalledWith(true);
  });

  it('applies custom className to content', () => {
    render(
      <Sheet open>
        <SheetContent className="custom-sheet">
          <SheetHeader>
            <SheetTitle>Sheet Title</SheetTitle>
          </SheetHeader>
        </SheetContent>
      </Sheet>,
    );

    const content = screen.getByRole('dialog');
    expect(content).toHaveClass('custom-sheet');
  });
});
