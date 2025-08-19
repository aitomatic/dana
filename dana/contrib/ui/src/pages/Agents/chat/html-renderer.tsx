import React, { useEffect, useRef } from 'react';
import { cn } from '@/lib/utils';
import './html-renderer.css';

interface HTMLRendererProps {
  html: string;
  className?: string;
  theme?: 'light' | 'dark';
  backgroundContext?: 'user' | 'agent' | 'default';
}

export const HTMLRenderer: React.FC<HTMLRendererProps> = ({
  html,
  className = '',
  theme = 'light',
  backgroundContext = 'default',
}) => {
  // Define font size classes for consistency with MarkdownViewerSmall
  const textSizeClasses = 'text-xs xl:text-sm';

  // Sanitize HTML content to prevent XSS attacks
  const sanitizeHTML = (htmlContent: string): string => {
    // Basic sanitization - allow common safe tags including interactive elements
    const allowedTags = [
      'p', 'div', 'span', 'strong', 'b', 'em', 'i', 'u', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li', 'blockquote', 'code', 'pre', 'br', 'hr', 'a', 'img', 'button'
    ];
    
    const allowedAttributes = [
      'class', 'id', 'style', 'href', 'src', 'alt', 'title', 'target', 'data-option', 'data-*'
    ];

    // Create a temporary div to parse HTML
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = htmlContent;

    // Recursively sanitize nodes
    const sanitizeNode = (node: Node): void => {
      if (node.nodeType === Node.ELEMENT_NODE) {
        const element = node as Element;
        const tagName = element.tagName.toLowerCase();
        
        // Remove disallowed tags
        if (!allowedTags.includes(tagName)) {
          element.replaceWith(...Array.from(element.childNodes));
          return;
        }
        
        // Remove disallowed attributes
        const attributes = Array.from(element.attributes);
        attributes.forEach(attr => {
          const attrName = attr.name.toLowerCase();
          // Allow explicitly listed attributes or data-* attributes
          const isAllowed = allowedAttributes.includes(attrName) || 
                           attrName.startsWith('data-') ||
                           allowedAttributes.some(allowed => allowed === 'data-*');
          
          // Always remove onclick attributes since we handle clicks with React
          if (attrName === 'onclick') {
            element.removeAttribute(attr.name);
            return;
          }
          
          if (!isAllowed) {
            element.removeAttribute(attr.name);
          }
        });
        
        // Recursively sanitize children
        Array.from(element.childNodes).forEach(sanitizeNode);
      }
    };

    sanitizeNode(tempDiv);
    return tempDiv.innerHTML;
  };

  const sanitizedHTML = sanitizeHTML(html);
  const containerRef = useRef<HTMLDivElement>(null);

  // Set up click handlers after component mounts
  useEffect(() => {
    if (containerRef.current) {
      const buttons = containerRef.current.querySelectorAll('.option-button');
      
      buttons.forEach((button) => {
        // Get the button's text content directly
        const optionText = button.textContent || '';
        
        // Add click event listener that sends the button's text directly
        const handleClick = () => {
          // Strategy: Try multiple approaches to send the message
          let messageSent = false;
          
          // Approach 1: Try to find and call global send functions
          const globalSendFunctions = ['sendMessage', 'handleSendMessage', 'submitMessage'];
          for (const funcName of globalSendFunctions) {
            if (typeof (window as any)[funcName] === 'function' && !messageSent) {
              try {
                // Try to update input state if available
                if ((window as any).setInput) {
                  (window as any).setInput(optionText);
                } else if ((window as any).setInputText) {
                  (window as any).setInputText(optionText);
                }
                
                // Call the send function
                (window as any)[funcName]();
                messageSent = true;
                console.log(`Message sent via global ${funcName} function`);
                break;
              } catch (e) {
                console.log(`Global ${funcName} call failed:`, e);
              }
            }
          }
          
          // Approach 2: If global approach failed, try DOM manipulation with proper state sync
          if (!messageSent) {
            const chatInput = document.querySelector('textarea[placeholder="Type your message"]') as HTMLTextAreaElement;
            
            if (chatInput) {
              // Set the input value
              chatInput.value = optionText;
              
              // Trigger multiple events to ensure React state updates
              chatInput.dispatchEvent(new Event('input', { bubbles: true }));
              chatInput.dispatchEvent(new Event('change', { bubbles: true }));
              
              // Focus the input to ensure it's active
              chatInput.focus();
              
              // Wait a bit for React state to update, then try to send
              setTimeout(() => {
                // Look for send button
                const allButtons = Array.from(document.querySelectorAll('button'));
                const sendButton = allButtons.find(button => {
                  const hasSendHandler = button.getAttribute('data-testid')?.includes('send') ||
                                       button.className?.includes('send') ||
                                       button.title?.includes('Send') ||
                                       button.textContent?.includes('Send') ||
                                       button.getAttribute('aria-label')?.includes('send');
                  return hasSendHandler && button.offsetParent !== null;
                }) as HTMLButtonElement;
                
                if (sendButton) {
                  sendButton.click();
                  console.log('Message sent via DOM fallback with delay');
                } else {
                  // Final fallback: Enter key simulation
                  const enterEvent = new KeyboardEvent('keydown', {
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                  });
                  chatInput.dispatchEvent(enterEvent);
                  console.log('Message sent via Enter key fallback');
                }
              }, 100); // Increased delay to allow React state update
            } else {
              // No chat input found
              console.log(`Would send: ${optionText}`);
              alert(`Would send: ${optionText}\n\nNo chat input found`);
            }
          }
        };
        
        button.addEventListener('click', handleClick);
        
        // Cleanup function will be handled by React's useEffect cleanup
        return () => button.removeEventListener('click', handleClick);
      });
    }
  }, [sanitizedHTML]); // Re-run when HTML content changes

  return (
    <div
      ref={containerRef}
      className={cn(
        `html-renderer html-renderer-${theme} html-renderer-${backgroundContext} w-full ${textSizeClasses}`,
        className,
      )}
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
    />
  );
};

export default HTMLRenderer;
