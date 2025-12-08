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
  messageId?: string;
  hasActiveButtons?: boolean;
}

export const HybridRenderer: React.FC<HybridRendererProps> = ({
  content,
  className = '',
  useMath = true,
  theme = 'light',
  backgroundContext = 'default',
  forceHtml = false,
  messageId,
  hasActiveButtons = true,
}) => {
  // Normalize content: convert escaped newlines to actual newlines
  const normalizeContent = (text: string): string => {
    let normalized = text;
    
    // Convert escaped newlines (\n) to actual newlines
    normalized = normalized.replace(/\\n/g, '\n');
    
    // Convert escaped tabs (\t) to spaces for better formatting
    normalized = normalized.replace(/\\t/g, '  ');
    
    return normalized;
  };

  // Normalize content before processing
  const normalizedContent = normalizeContent(content);

  // Detect if content contains HTML tags
  const containsHTML = (text: string): boolean => {
    const htmlRegex = /<[^>]*>/;
    return htmlRegex.test(text);
  };

  // Detect if content is from a tool that generates HTML (auto-force HTML mode)
  const isToolGeneratedHTML = (text: string): boolean => {
    // Simple pattern matching for tool-generated content
    return (
      text.includes('options-container') ||
      text.includes('option-button') ||
      text.includes('handleOptionClick') ||
      text.includes('data-option')
    );
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
    const markdownCount = (text.match(/[#*`\-_[]/g) || []).length; // Removed () to avoid counting HTML attributes

    // Lower threshold: if we have multiple HTML tags and they're not significantly outnumbered by markdown
    return htmlTagCount > 3 && htmlTagCount >= markdownCount * 0.6;
  };

  // Smart newline-to-HTML conversion that avoids double conversion and excessive breaks
  const convertNewlinesToHTML = (text: string): string => {
    // Block-level HTML elements that don't need <br> tags between them
    const blockElements = [
      'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote', 'pre', 'hr',
      'table', 'thead', 'tbody', 'tr', 'td', 'th'
    ];
    
    let htmlContent = text;
    
    // Step 1: Remove newlines that are already after <br> tags (avoid double conversion from backend)
    // This handles cases where backend converted \n to <br>\n
    htmlContent = htmlContent.replace(/<br\s*\/?>\s*\n+/gi, '<br>');
    
    // Step 2: Remove newlines between block-level HTML elements (they don't need <br> tags)
    // Pattern: closing block tag, whitespace/newlines, opening block tag
    const blockElementPattern = new RegExp(
      `</(${blockElements.join('|')})>\\s*\\n+\\s*<(${blockElements.join('|')})`,
      'gi'
    );
    htmlContent = htmlContent.replace(blockElementPattern, (match) => {
      // Replace newlines with a single space between block elements
      return match.replace(/\s*\n+\s*/g, ' ');
    });
    
    // Step 3: Collapse multiple consecutive newlines (2+) into a single <br>
    // This handles empty lines from backend spacing (response_parts.append(""))
    htmlContent = htmlContent.replace(/\n{2,}/g, '<br>');
    
    // Step 4: Convert remaining single newlines to <br>
    // These are intentional line breaks in the content
    htmlContent = htmlContent.replace(/\n/g, '<br>');
    
    // Step 5: Clean up any excessive <br> tags (more than 2 consecutive)
    // Allow up to 2 <br> tags for paragraph spacing, but collapse more
    htmlContent = htmlContent.replace(/(<br\s*\/?>){3,}/gi, '<br><br>');
    
    return htmlContent;
  };

  // Check if content should be rendered as HTML
  const shouldRenderAsHTML =
    forceHtml ||
    isToolGeneratedHTML(normalizedContent) ||
    (containsHTML(normalizedContent) && isPrimarilyHTML(normalizedContent));

  if (shouldRenderAsHTML) {
    // Convert newlines to <br> tags for HTML rendering using smart conversion
    const htmlContent = convertNewlinesToHTML(normalizedContent);
    
    return (
      <HTMLRenderer
        html={htmlContent}
        className={className}
        theme={theme}
        backgroundContext={backgroundContext}
        messageId={messageId}
        hasActiveButtons={hasActiveButtons}
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
      {normalizedContent}
    </MarkdownViewerSmall>
  );
};

export default HybridRenderer;
