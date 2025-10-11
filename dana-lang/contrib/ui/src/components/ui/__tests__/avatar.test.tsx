import { describe, it, expect } from 'vitest';
import { render, screen } from '../../../test/test-utils';
import { Avatar, AvatarImage, AvatarFallback } from '../avatar';

describe('Avatar', () => {
  it('renders Avatar with fallback', () => {
    render(
      <Avatar>
        <AvatarFallback>AB</AvatarFallback>
      </Avatar>,
    );
    expect(screen.getByText('AB')).toBeInTheDocument();
  });

  it('renders Avatar with image and fallback', () => {
    render(
      <Avatar>
        <AvatarImage src="/test.png" alt="Test Avatar" />
        <AvatarFallback>AB</AvatarFallback>
      </Avatar>,
    );
    // In jsdom, the image won't load, so fallback will be shown
    expect(screen.getByText('AB')).toBeInTheDocument();
    // Do not check for the image element, as it is not present in the DOM
  });
});
