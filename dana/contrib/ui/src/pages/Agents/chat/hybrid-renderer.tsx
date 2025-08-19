import React from 'react';
import { MarkdownViewerSmall } from './markdown-viewer';
import { HTMLRenderer } from './html-renderer';

interface HybridRendererProps {
  content: string;
  className?: string;
  useMath?: boolean;
  theme?: 'light' | 'dark';
  backgroundContext?: 'user' | 'agent' | 'default';
  forceHtml?: boolean; // Force HTML rendering regardless of detection
}

export const HybridRenderer: React.FC<HybridRendererProps> = ({
  content,
  className = '',
  useMath = true,
  theme = 'light',
  backgroundContext = 'default',
  forceHtml = false,
}) => {
  // Detect if content contains HTML tags
  const containsHTML = (text: string): boolean => {
    const htmlRegex = /<[^>]*>/;
    return htmlRegex.test(text);
  };

  // Detect if content is from a tool that generates HTML (auto-force HTML mode)
  const isToolGeneratedHTML = (text: string): boolean => {
    // Simple pattern matching for tool-generated content
    return text.includes('options-container') || 
           text.includes('option-button') || 
           text.includes('handleOptionClick') ||
           text.includes('data-option');
  };

  // Detect if content is primarily HTML (improved detection logic)
  const isPrimarilyHTML = (text: string): boolean => {
    // Check for specific HTML patterns that indicate tool-generated content
    const hasButtonTags = /<button[^>]*>/i.test(text);
    const hasOptionsContainer = /<div[^>]*class=['"]?options-container['"]?[^>]*>/i.test(text);
    const hasClickHandlers = /onclick\s*=\s*['"][^'"]*['"]/.test(text);
    
    // If we have button-specific patterns, definitely render as HTML
    if (hasButtonTags || hasOptionsContainer || hasClickHandlers) {
      return true;
    }
    
    // Fallback to improved tag counting
    const htmlTagCount = (text.match(/<[^>]*>/g) || []).length;
    const markdownCount = (text.match(/[#*`\-_\[\]]/g) || []).length; // Removed () to avoid counting HTML attributes
    
    // Lower threshold: if we have multiple HTML tags and they're not significantly outnumbered by markdown
    return htmlTagCount > 3 && (htmlTagCount >= markdownCount * 0.6);
  };

  // Check if content should be rendered as HTML
  const shouldRenderAsHTML = forceHtml || isToolGeneratedHTML(content) || (containsHTML(content) && isPrimarilyHTML(content));

  if (shouldRenderAsHTML) {
    return (
      <HTMLRenderer
        html={content}
        className={className}
        theme={theme}
        backgroundContext={backgroundContext}
      />
    );
  }

  // Default to Markdown rendering
  return (
    <MarkdownViewerSmall
      classname={className}
      useMath={useMath}
      theme={theme}
      backgroundContext={backgroundContext}
    >
      {content}
    </MarkdownViewerSmall>
  );
};

export default HybridRenderer;
