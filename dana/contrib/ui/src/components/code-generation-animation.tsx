import { useState, useEffect, useCallback } from 'react';
import { cn } from '@/lib/utils';

interface CodeGenerationAnimationProps {
  targetCode: string;
  onAnimationComplete: (finalCode: string) => void;
  speed?: number; // Characters per second
  className?: string;
}

export const CodeGenerationAnimation = ({
  targetCode,
  onAnimationComplete,
  speed = 30, // Default 30 characters per second
  className,
}: CodeGenerationAnimationProps) => {
  const [currentCode, setCurrentCode] = useState('');
  const [isAnimating, setIsAnimating] = useState(false);
  const [cursorVisible, setCursorVisible] = useState(true);

  // Cursor blink effect
  useEffect(() => {
    if (!isAnimating) return;

    const cursorInterval = setInterval(() => {
      setCursorVisible((prev) => !prev);
    }, 500);

    return () => clearInterval(cursorInterval);
  }, [isAnimating]);

  // Animation effect
  useEffect(() => {
    if (!targetCode || targetCode === currentCode) return;

    setIsAnimating(true);
    setCurrentCode('');

    const delay = 1000 / speed; // Convert speed to delay
    let currentIndex = 0;

    const animate = () => {
      if (currentIndex < targetCode.length) {
        setCurrentCode(targetCode.slice(0, currentIndex + 1));
        currentIndex++;
        setTimeout(animate, delay);
      } else {
        setIsAnimating(false);
        setCursorVisible(false);
        onAnimationComplete(targetCode);
      }
    };

    // Start animation after a brief delay
    setTimeout(animate, 100);
  }, [targetCode, speed, onAnimationComplete]);

  return (
    <div className={cn('relative h-full', className)}>
      <div className="font-mono text-sm whitespace-pre-wrap leading-6 text-gray-900">
        {currentCode}
        {isAnimating && cursorVisible && (
          <span className="inline-block w-0.5 h-5 bg-blue-600 ml-0.5 animate-pulse" />
        )}
      </div>
    </div>
  );
};

// Hook for managing code generation animation state
export const useCodeGenerationAnimation = () => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedCode, setGeneratedCode] = useState('');

  const startGeneration = useCallback((targetCode: string) => {
    setIsGenerating(true);
    setGeneratedCode(targetCode);
  }, []);

  const completeGeneration = useCallback((finalCode: string) => {
    setIsGenerating(false);
    setGeneratedCode('');
  }, []);

  return {
    isGenerating,
    generatedCode,
    startGeneration,
    completeGeneration,
  };
};
