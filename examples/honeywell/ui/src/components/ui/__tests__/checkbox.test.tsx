import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '../../../test/test-utils';
import { Checkbox } from '../checkbox';

describe('Checkbox', () => {
  it('renders Checkbox', () => {
    render(<Checkbox data-testid="checkbox" />);
    expect(screen.getByTestId('checkbox')).toBeInTheDocument();
  });

  it('can be checked and unchecked', () => {
    render(<Checkbox data-testid="checkbox" />);
    const checkbox = screen.getByTestId('checkbox');
    expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    // Radix Checkbox doesn't use native checked, so just check aria-checked
    expect(checkbox).toHaveAttribute('data-state', 'checked');
    fireEvent.click(checkbox);
    expect(checkbox).toHaveAttribute('data-state', 'unchecked');
  });

  it('can be disabled', () => {
    render(<Checkbox data-testid="checkbox" disabled />);
    const checkbox = screen.getByTestId('checkbox');
    expect(checkbox).toBeDisabled();
  });
});
