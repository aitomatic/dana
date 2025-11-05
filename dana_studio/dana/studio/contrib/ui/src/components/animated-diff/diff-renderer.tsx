import React from 'react';
import { type DiffSection, getChangedSections, truncateDiffForAnimation } from '@/lib/diff-utils';

interface DiffRendererProps {
  sections: DiffSection[];
  maxChars?: number;
}

/**
 * DiffRenderer - Displays template changes statically (no animation)
 * Shows additions in green and removals in red
 */
export const DiffRenderer: React.FC<DiffRendererProps> = ({
  sections,
  maxChars = 800,
}) => {
  // Get only changed sections and truncate if needed
  const changedSections = getChangedSections({ sections, oldContent: null, newContent: null });
  const displaySections = truncateDiffForAnimation(changedSections, maxChars);

  // Don't show anything if there are no visible changes
  if (displaySections.length === 0) {
    return null;
  }

  // Show all changes statically
  return (
    <div className="space-y-1 font-mono text-sm">
      {displaySections.map((section, idx) => (
        <div
          key={idx}
          className={`${
            section.type === 'add'
              ? 'text-green-700 bg-green-50 border-l-2 border-green-500'
              : 'text-red-700 bg-red-50 border-l-2 border-red-500 line-through'
          } px-2 py-1 rounded`}
        >
          <span className="font-semibold">{section.type === 'add' ? '+' : '-'}</span>{' '}
          {section.content}
        </div>
      ))}
    </div>
  );
};

// Add fade-out animation CSS
if (typeof window !== 'undefined' && !document.getElementById('diff-renderer-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'diff-renderer-styles';
  styleSheet.textContent = `
    @keyframes fade-out {
      from {
        opacity: 1;
      }
      to {
        opacity: 0.3;
      }
    }
    .animate-fade-out {
      animation: fade-out 500ms ease-in forwards;
    }
  `;
  document.head.appendChild(styleSheet);
}

