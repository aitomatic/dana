import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/utils';
import { type DiffSection } from '@/lib/diff-utils';
import { TypewriterText } from './typewriter';

interface TemplateDiff {
  sections: DiffSection[];
  oldContent?: string | null;
  newContent?: string | null;
}

interface AnimatedMarkdownProps {
  content: string;
  className?: string;
  animate?: boolean;
  animationSpeed?: number;
  diff?: TemplateDiff | null;
  onAnimationComplete?: () => void;
}

/**
 * AnimatedMarkdown - Renders markdown with animation for changed sections
 * Only animates the parts that changed, keeps unchanged sections static
 */
export const AnimatedMarkdown: React.FC<AnimatedMarkdownProps> = ({
  content,
  className = '',
  animate = true,
  animationSpeed = 30,
  diff = null,
  onAnimationComplete,
}) => {
  const [currentSectionIndex, setCurrentSectionIndex] = useState(0);
  const [isAnimating, setIsAnimating] = useState(false);
  const [animationComplete, setAnimationComplete] = useState(false);

  // Track when diff changes to start animation
  useEffect(() => {
    console.log('🎬 AnimatedMarkdown - diff changed:', {
      hasDiff: !!diff,
      sections: diff?.sections?.length || 0,
      animate,
      diff,
    });
    
    if (diff && diff.sections && diff.sections.length > 0 && animate) {
      console.log('✨ AnimatedMarkdown - Starting animation with sections:', diff.sections);
      
      // Find first section that needs animation (add or remove)
      const firstAnimatableIndex = diff.sections.findIndex(
        s => s.type === 'add' || s.type === 'remove'
      );
      
      if (firstAnimatableIndex !== -1) {
        console.log('🎯 Starting animation at index:', firstAnimatableIndex);
        setIsAnimating(true);
        setCurrentSectionIndex(firstAnimatableIndex);
        setAnimationComplete(false);
      } else {
        console.log('⚠️ No animatable sections found');
        setIsAnimating(false);
      }
    } else {
      console.log('⚠️ AnimatedMarkdown - Not animating:', {
        noDiff: !diff,
        noSections: !diff?.sections || diff.sections.length === 0,
        animateDisabled: !animate,
      });
      setIsAnimating(false);
    }
  }, [diff, animate]);

  const handleSectionComplete = () => {
    if (!diff || !diff.sections) return;

    // Move to next section that needs animation (add or remove)
    let nextIndex = currentSectionIndex + 1;
    while (nextIndex < diff.sections.length) {
      const section = diff.sections[nextIndex];
      if (section.type === 'add' || section.type === 'remove') {
        setCurrentSectionIndex(nextIndex);
        return;
      }
      nextIndex++;
    }

    // No more sections to animate - complete
    setIsAnimating(false);
    setAnimationComplete(true);
    if (onAnimationComplete) {
      onAnimationComplete();
    }
  };

  // If we have a diff and should animate
  if (diff && diff.sections && diff.sections.length > 0 && animate && !animationComplete) {
    return (
      <div className={cn('relative', className)}>
        {isAnimating && (
          <div className="absolute top-2 right-2 z-10">
            <div className="flex items-center gap-2 px-3 py-1 bg-blue-50 border border-blue-200 rounded-md text-xs text-blue-700">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              <span>Updating template...</span>
            </div>
          </div>
        )}

        <div className="space-y-0">
          {diff.sections.map((section, idx) => {
            // Unchanged sections - render immediately as static markdown
            if (section.type === 'unchanged') {
              return (
                <div key={idx} className="inline">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{section.content}</ReactMarkdown>
                </div>
              );
            }

            // Added sections - type out with green highlight
            if (section.type === 'add') {
              const shouldAnimate = idx <= currentSectionIndex;
              const isCurrentlyAnimating = idx === currentSectionIndex && isAnimating;

              if (!shouldAnimate) {
                // Not reached yet - show nothing
                return null;
              }

              return (
                <div
                  key={idx}
                  className="inline bg-green-50 border-l-2 border-green-500 px-2 py-1 my-1"
                >
                  {isCurrentlyAnimating ? (
                    <TypewriterText
                      text={section.content}
                      speed={animationSpeed}
                      onComplete={handleSectionComplete}
                      showCursor={true}
                    />
                  ) : (
                    <span>{section.content}</span>
                  )}
                </div>
              );
            }

            // Removed sections - show with strikethrough and fade out
            if (section.type === 'remove') {
              const shouldShow = idx <= currentSectionIndex;
              const isCurrentlyAnimating = idx === currentSectionIndex && isAnimating;

              if (!shouldShow) {
                return null;
              }

              // If this is the current section, trigger fade out and move to next
              if (isCurrentlyAnimating) {
                setTimeout(() => handleSectionComplete(), 800); // Fade out duration
              }

              return (
                <div
                  key={idx}
                  className={cn(
                    'inline bg-red-50 border-l-2 border-red-500 px-2 py-1 my-1 line-through',
                    isCurrentlyAnimating ? 'animate-fade-out' : 'opacity-30'
                  )}
                >
                  {section.content}
                </div>
              );
            }

            return null;
          })}
        </div>
      </div>
    );
  }

  // No diff or animation disabled - render normal static markdown
  return (
    <div className={cn('relative', className)}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
    </div>
  );
};

// Add fade-out animation CSS if not already present
if (typeof window !== 'undefined' && !document.getElementById('animated-markdown-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'animated-markdown-styles';
  styleSheet.textContent = `
    @keyframes fade-out {
      from {
        opacity: 1;
      }
      to {
        opacity: 0;
      }
    }
    .animate-fade-out {
      animation: fade-out 800ms ease-out forwards;
    }
  `;
  document.head.appendChild(styleSheet);
}

