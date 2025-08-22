import React, { useEffect, useRef, useMemo } from 'react';
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
      'p',
      'div',
      'span',
      'strong',
      'b',
      'em',
      'i',
      'u',
      'h1',
      'h2',
      'h3',
      'h4',
      'h5',
      'h6',
      'ul',
      'ol',
      'li',
      'blockquote',
      'code',
      'pre',
      'br',
      'hr',
      'a',
      'img',
      'button',
    ];

    const allowedAttributes = [
      'class',
      'id',
      'style',
      'href',
      'src',
      'alt',
      'title',
      'target',
      'data-option',
      'data-*',
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
        attributes.forEach((attr) => {
          const attrName = attr.name.toLowerCase();
          // Allow explicitly listed attributes or data-* attributes
          const isAllowed =
            allowedAttributes.includes(attrName) ||
            attrName.startsWith('data-') ||
            allowedAttributes.some((allowed) => allowed === 'data-*');

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

  // Set up event delegation for option button clicks
  useEffect(() => {
    if (!containerRef.current) return;

    const handleContainerClick = (event: Event) => {
      const target = event.target as Element;
      const button = target.closest('.option-button');

      if (!button) return;

      // Check if this button is in the active message
      if (!isButtonInActiveMessage(button)) {
        console.log('Button in inactive message, ignoring click');
        return;
      }

      // Process the active button click
      handleActiveOptionClick(button);
    };

    // Add single event listener to container
    containerRef.current.addEventListener('click', handleContainerClick);

    console.log('Event delegation listener attached to container');

    // Cleanup function
    return () => {
      if (containerRef.current) {
        containerRef.current.removeEventListener('click', handleContainerClick);
        console.log('Event delegation listener removed from container');
      }
    };
  }, []); // Run only once on mount

  // Function to check if a button is in the active message
  const isButtonInActiveMessage = (button: Element): boolean => {
    // Find the message container for this button
    const messageContainer = button.closest('[data-message-id]');
    if (!messageContainer) {
      // If no message ID, assume it's the current message (fallback)
      return true;
    }

    // Check if this is the latest message with options
    const messageId = messageContainer.getAttribute('data-message-id');

    const isActive = messageId === currentMessageId;
    console.log(
      `Button message ID: ${messageId}, Current: ${currentMessageId}, Active: ${isActive}`,
    );

    return isActive;
  };

  // Generate a stable message ID that only changes when HTML content changes
  const currentMessageId = useMemo(() => {
    // Create a hash based on content length and first few characters
    // This ensures the ID only changes when content actually changes
    const contentHash =
      sanitizedHTML.length.toString(36) +
      sanitizedHTML
        .substring(0, 10)
        .split('')
        .map((c) => c.charCodeAt(0))
        .join('');
    return `message-${contentHash}`;
  }, [sanitizedHTML]);

  // Function to handle active option button clicks
  const handleActiveOptionClick = (button: Element) => {
    const optionText = button.textContent || '';
    console.log(`Active option button clicked: "${optionText}"`);
    console.log('Available global functions:', {
      sendMessageDirect: typeof (window as any).sendMessageDirect,
      setInput: typeof (window as any).setInput,
      sendMessage: typeof (window as any).sendMessage,
    });

    // Strategy: Try direct send first, then fallback approaches
    let messageSent = false;

    // Approach 1: Try direct message sending (preferred)
    if (typeof (window as any).sendMessageDirect === 'function' && !messageSent) {
      try {
        console.log(`Sending message directly: "${optionText}"`);
        (window as any).sendMessageDirect(optionText);
        messageSent = true;
        console.log('Message sent directly via sendMessageDirect');
        return; // Exit early since message was sent
      } catch (e) {
        console.log(`Direct send failed:`, e);
      }
    } else {
      console.log('sendMessageDirect not available, trying fallback approaches');
    }

    // Approach 2: Try to find and call global send functions (fallback)
    const globalSendFunctions = ['sendMessage', 'handleSendMessage', 'submitMessage'];
    for (const funcName of globalSendFunctions) {
      if (typeof (window as any)[funcName] === 'function' && !messageSent) {
        try {
          console.log(`Trying global function: ${funcName}`);

          // Try to update input state if available
          if ((window as any).setInput) {
            console.log(`Setting input via setInput: "${optionText}"`);
            (window as any).setInput(optionText);
          } else if ((window as any).setInputText) {
            console.log(`Setting input via setInputText: "${optionText}"`);
            (window as any).setInputText(optionText);
          }

          // Call the send function with a small delay to ensure state update
          setTimeout(() => {
            (window as any)[funcName]();
            console.log(`Message sent via global ${funcName} function with delay`);
          }, 50);
          messageSent = true;
          break;
        } catch (e) {
          console.log(`Global ${funcName} call failed:`, e);
        }
      }
    }

    // Approach 3: If global approach failed, try DOM manipulation with proper state sync
    if (!messageSent) {
      console.log('Global approach failed, trying DOM fallback');

      const chatInput = document.querySelector(
        'textarea[placeholder="Ask me anything"]',
      ) as HTMLTextAreaElement;

      if (chatInput) {
        console.log(`Found chat input, setting value: "${optionText}"`);

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
          const sendButton = allButtons.find((button) => {
            const hasSendHandler =
              button.getAttribute('data-testid')?.includes('send') ||
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
              cancelable: true,
            });
            chatInput.dispatchEvent(enterEvent);
            console.log('Message sent via Enter key fallback');
          }
        }, 100); // Increased delay to allow React state update
      } else {
        // No chat input found
        console.log(`Would send: ${optionText}`);
        console.log('No chat input found - searching for alternative selectors');

        // Try alternative selectors
        const alternativeInputs = [
          'textarea[placeholder="Type your message"]',
          'textarea',
          'input[type="text"]',
        ];

        for (const selector of alternativeInputs) {
          const input = document.querySelector(selector) as HTMLTextAreaElement | HTMLInputElement;
          if (input) {
            console.log(`Found alternative input with selector: ${selector}`);
            input.value = optionText;
            input.dispatchEvent(new Event('input', { bubbles: true }));
            input.dispatchEvent(new Event('change', { bubbles: true }));
            input.focus();
            return;
          }
        }

        alert(`Would send: ${optionText}\n\nNo chat input found`);
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        `html-renderer html-renderer-${theme} html-renderer-${backgroundContext} w-full ${textSizeClasses}`,
        className,
      )}
      data-message-id={currentMessageId}
      dangerouslySetInnerHTML={{ __html: sanitizedHTML }}
    />
  );
};

export default HTMLRenderer;
