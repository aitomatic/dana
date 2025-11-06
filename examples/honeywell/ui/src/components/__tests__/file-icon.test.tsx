import { describe, it, expect } from 'vitest';
import { render, screen } from '../../test/test-utils';
import FileIcon from '../file-icon';

describe('FileIcon', () => {
  it('renders file icon with resource', () => {
    render(<FileIcon resource={{ name: 'test.txt', resource_type: 'file' }} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('renders PDF icon for PDF files', () => {
    render(<FileIcon resource={{ name: 'document.pdf', resource_type: 'file' }} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('renders image icon for image files', () => {
    render(<FileIcon resource={{ name: 'image.jpg', resource_type: 'file' }} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('renders code icon for code files', () => {
    render(<FileIcon resource={{ name: 'script.html', resource_type: 'file' }} />);
    expect(screen.getByRole('img')).toBeInTheDocument();
  });

  it('renders plan icon for plan resource type', () => {
    render(<FileIcon resource={{ name: 'plan', resource_type: 'plan' }} />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders interview icon for interview resource type', () => {
    render(<FileIcon resource={{ name: 'interview', resource_type: 'interview' }} />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders database icon for database resource type', () => {
    render(<FileIcon resource={{ name: 'database', resource_type: 'database' }} />);
    const svg = document.querySelector('svg');
    expect(svg).toBeInTheDocument();
  });

  it('renders folder icon for unknown file types', () => {
    render(<FileIcon resource={{ name: 'unknown.xyz', resource_type: 'file' }} />);
    expect(screen.getByAltText('Folder icon')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(
      <FileIcon resource={{ name: 'test.txt', resource_type: 'file' }} className="custom-icon" />,
    );
    const container = screen.getByRole('img').parentElement;
    expect(container).toHaveClass('custom-icon');
  });

  it('renders with custom dimensions', () => {
    render(
      <FileIcon resource={{ name: 'test.txt', resource_type: 'file' }} width={30} height={30} />,
    );
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('width', '30');
    expect(img).toHaveAttribute('height', '30');
  });
});
