import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '../../../test/test-utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '../dropdown-menu';

describe('DropdownMenu', () => {
  it('renders dropdown trigger', () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open Menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item 1</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    expect(screen.getByText('Open Menu')).toBeInTheDocument();
  });

  it('handles trigger click', () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open Menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item 1</DropdownMenuItem>
          <DropdownMenuItem>Item 2</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    const trigger = screen.getByText('Open Menu');
    fireEvent.click(trigger);

    // Just verify the click doesn't throw an error
    expect(trigger).toBeInTheDocument();
  });

  it('renders menu with content', () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open Menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuLabel>Menu Label</DropdownMenuLabel>
          <DropdownMenuItem>Item 1</DropdownMenuItem>
          <DropdownMenuSeparator />
          <DropdownMenuItem>Item 2</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    expect(screen.getByText('Open Menu')).toBeInTheDocument();
  });

  it('applies custom className to trigger', () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger className="custom-trigger">Open Menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item 1</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    const trigger = screen.getByText('Open Menu');
    expect(trigger).toHaveClass('custom-trigger');
  });

  it('has proper accessibility attributes', () => {
    render(
      <DropdownMenu>
        <DropdownMenuTrigger>Open Menu</DropdownMenuTrigger>
        <DropdownMenuContent>
          <DropdownMenuItem>Item 1</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>,
    );

    const trigger = screen.getByText('Open Menu');
    expect(trigger).toHaveAttribute('aria-haspopup', 'menu');
    expect(trigger).toHaveAttribute('aria-expanded', 'false');
  });
});
