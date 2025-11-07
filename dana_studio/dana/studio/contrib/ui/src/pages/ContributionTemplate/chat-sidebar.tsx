/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { useContributionStore } from '@/stores/contribution-store';
import { createSmartChatStore } from '@/stores/smart-chat-store';
import { ArrowUp, Expand, Collapse } from 'iconoir-react';
import { toast } from 'sonner';
import { HybridRenderer } from '@/pages/Agents/chat/hybrid-renderer';
import { DiffRenderer } from '@/components/animated-diff';
import { parseDiffResponse, getChangedSections } from '@/lib/diff-utils';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { IconChevronDown } from '@tabler/icons-react';

// CSS for blinking cursor animation
const cursorBlinkStyle = `
  .cursor-blink {
    animation: blink 1s infinite;
  }

  @keyframes blink {
    0%, 50% {
      opacity: 1;
    }
    51%, 100% {
      opacity: 0;
    }
  }
`;

// Add styles to head
if (typeof window !== 'undefined' && !document.getElementById('ct-animated-placeholder-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'ct-animated-placeholder-styles';
  styleSheet.textContent = cursorBlinkStyle;
  document.head.appendChild(styleSheet);
}

// Animated placeholder component - only shown for new users (no messages sent)
const PLACEHOLDER_MESSAGES = [
  'Ask about the interview template...',
  'Request changes to questions...',
  'Add new interview sections...',
];

const AnimatedPlaceholder: React.FC<{
  hasMessages: boolean;
  isFocused: boolean;
  hasInteracted: boolean;
}> = ({ hasMessages, isFocused, hasInteracted }) => {
  const placeholders = PLACEHOLDER_MESSAGES;

  const [currentPlaceholder, setCurrentPlaceholder] = useState(0);
  const [currentText, setCurrentText] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    // Only animate if there are no messages, textarea is not focused, and user hasn't interacted yet
    if (hasMessages || isFocused || hasInteracted) {
      setCurrentText('');
      return;
    }

    const typingSpeed = 100;
    const deletingSpeed = 50;
    const pauseDuration = 2000;

    const timeout = setTimeout(
      () => {
        if (!isDeleting && currentText === placeholders[currentPlaceholder]) {
          // If we've finished typing, pause then start deleting
          setTimeout(() => setIsDeleting(true), pauseDuration);
        } else if (isDeleting && currentText === '') {
          // If we've finished deleting, move to next placeholder and start typing
          setIsDeleting(false);
          setCurrentPlaceholder((prev) => (prev + 1) % placeholders.length);
        } else if (isDeleting) {
          // Delete current text
          setCurrentText(currentText.slice(0, -1));
        } else {
          // Type current text
          setCurrentText(placeholders[currentPlaceholder].slice(0, currentText.length + 1));
        }
      },
      isDeleting ? deletingSpeed : typingSpeed,
    );

    return () => clearTimeout(timeout);
  }, [
    currentText,
    isDeleting,
    currentPlaceholder,
    placeholders,
    hasMessages,
    isFocused,
    hasInteracted,
  ]);

  // If user has sent messages OR is focused OR has interacted, show simple static placeholder
  if (hasMessages || isFocused || hasInteracted) {
    return <span>Type your message</span>;
  }

  return (
    <span className="inline-block relative">
      {currentText}
      <span className="inline-block w-0.5 h-4 ml-0.5 bg-gray-400 cursor-blink"></span>
    </span>
  );
};

// Function to convert snake_case tool names to friendly display names
const formatToolName = (toolName: string): string => {
  const toolNameMap: Record<string, string> = {
    modify_template: 'Modify Template',
    update_questions: 'Update Questions',
    add_section: 'Add Section',
    analyze_template: 'Analyze Template',
    validate_template: 'Validate Template',
  };

  // If we have a specific mapping, use it
  if (toolNameMap[toolName]) {
    return toolNameMap[toolName];
  }

  // Otherwise, convert snake_case to Title Case
  return toolName
    .split('_')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(' ');
};

// Processing status message type
interface ProcessingStatusMessage {
  id: string;
  toolName: string;
  message: string;
  status: 'init' | 'in_progress' | 'finish' | 'error';
  progression?: number;
  timestamp: Date;
}

// Collapsible processing status history component
const ProcessingStatusHistory: React.FC<{
  messages: ProcessingStatusMessage[];
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ messages, isExpanded, onToggle }) => {
  if (messages.length === 0) return null;

  return (
    <div
      className={`flex flex-col gap-2 self-start px-2 py-2 text-left bg-gray-50 rounded-lg border border-gray-200 ${isExpanded ? 'w-full' : ''}`}
    >
      <button
        onClick={onToggle}
        className="flex gap-2 items-center text-sm font-medium text-gray-600 transition-colors hover:text-gray-800"
      >
        {isExpanded ? <Collapse className="w-4 h-4" /> : <Expand className="w-4 h-4" />}
        {isExpanded ? 'Hide thinking' : 'Show thinking'} ({messages.length})
      </button>

      {isExpanded && (
        <div className="flex overflow-y-auto flex-col gap-3 max-h-60">
          {messages.map((msg) => (
            <div
              key={msg.id}
              className="flex flex-col gap-2 p-2 bg-white rounded border border-gray-200"
            >
              <div className="flex gap-2 items-center">
                {msg.status === 'in_progress' && (
                  <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                )}
                {msg.status === 'finish' && (
                  <div className="flex justify-center items-center w-4 h-4 bg-green-500 rounded-full">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                )}
                {msg.status === 'error' && (
                  <div className="flex justify-center items-center w-4 h-4 bg-red-500 rounded-full">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                )}
                <span className="text-sm font-medium text-gray-600">
                  {formatToolName(msg.toolName)}
                </span>
                <span className="ml-auto text-xs text-gray-400">
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <div className="text-sm text-gray-600">
                <HybridRenderer content={msg.message} backgroundContext="agent" />
              </div>
              {msg.progression !== undefined && (
                <div className="w-full h-2 bg-gray-200 rounded-full">
                  <div
                    className="h-2 bg-gray-600 rounded-full transition-all duration-300"
                    style={{ width: `${msg.progression * 100}%` }}
                  ></div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// Main chat component for Capture Template
const ContributionTemplateChat: React.FC<{
  templateId: number;
}> = ({ templateId }) => {
  const {
    currentTemplate,
    isSendingMessage,
    sendMessage,
    loadConversation,
    duplicateCurrentTemplate,
    isCreatingTemplate,
  } = useContributionStore();

  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [chatMode, setChatMode] = useState<'chat' | 'editor'>('chat');

  // Create template-specific chat store
  const useTemplateChatStore = useMemo(() => {
    return createSmartChatStore(`template-${templateId}`);
  }, [templateId]);

  // Call the store hook unconditionally at top level
  const messages = useTemplateChatStore((s) => s.messages);
  const addMessage = useTemplateChatStore((s) => s.addMessage);
  const removeMessageById = useTemplateChatStore((s) => s.removeMessageById);
  const setMessages = useTemplateChatStore((s) => s.setMessages);
  const setMessageButtonsActive = useTemplateChatStore((s) => s.setMessageButtonsActive);
  const deactivateAllButtons = useTemplateChatStore((s) => s.deactivateAllButtons);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [processingStatusHistory, setProcessingStatusHistory] = useState<ProcessingStatusMessage[]>(
    [],
  );
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const hasLoadedConversationRef = useRef(false);

  // Check if this is a master template (cannot be modified)
  const isMasterTemplate = currentTemplate?.is_master || false;

  // Load conversation when template opens
  useEffect(() => {
    const loadConversationHistory = async () => {
      if (!templateId || hasLoadedConversationRef.current) return;

      hasLoadedConversationRef.current = true;

      try {
        const conversationMessages = await loadConversation(templateId);

        if (conversationMessages && conversationMessages.length > 0) {
          // Convert conversation messages to smart chat format
          const smartMessages = conversationMessages.map((msg: any) => ({
            sender: msg.sender === 'assistant' ? 'agent' : msg.sender,
            text: msg.content,
            timestamp: new Date(msg.created_at || Date.now()).getTime(),
            id: `msg-${msg.id || Math.random()}`,
            hasActiveButtons: false,
          }));
          setMessages(smartMessages);
        }
      } catch (error: any) {
        console.error('Failed to load conversation history:', error);
      }
    };

    loadConversationHistory();
  }, [templateId, loadConversation, setMessages]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Auto-scroll when new thinking messages are added
  useEffect(() => {
    if (bottomRef.current && processingStatusHistory.length > 0) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [processingStatusHistory]);

  const handleSendMessage = useCallback(
    async (messageText?: string) => {
      const textToSend = messageText || input.trim();
      if (!textToSend || !templateId || isMasterTemplate) return;

      // Clear previous thinking messages when starting new processing
      setProcessingStatusHistory([]);

      // Deactivate all previous message buttons when user sends a new message
      deactivateAllButtons();

      // Add user message
      const userMsg = {
        sender: 'user' as const,
        text: textToSend,
        timestamp: Date.now(),
      };
      addMessage(userMsg);

      const userInput = textToSend;

      // Only clear input if we're using the input field (no messageText provided)
      if (!messageText) {
        setInput('');
      }

      // Store the thinking message ID for later removal
      let thinkingMessageId: string | null = null;

      try {
        // Add thinking message with unique ID
        const thinkingMsg = {
          sender: 'agent' as const,
          text: 'Thinking...',
          id: `thinking-${Date.now()}-${Math.random()}`,
        };
        addMessage(thinkingMsg);
        thinkingMessageId = thinkingMsg.id!;

        // Automatically expand the thinking component when thinking process begins
        setIsHistoryExpanded(true);

        // Send message via contribution store
        const result = await sendMessage(userInput, chatMode);

        // Remove the thinking message by ID if it exists
        if (thinkingMessageId) {
          removeMessageById(thinkingMessageId);
        }

        // Add the actual response
        if (result) {
          // Add main response message
          const agentResponse = {
            sender: 'agent' as const,
            text: result.response || '...',
            timestamp: Date.now(),
          };
          addMessage(agentResponse);

          // If there's a diff, add it as a separate message with special marker
          if (result.templateModified && result.templateDiff) {
            const diffMessage = {
              sender: 'agent' as const,
              text: `__TEMPLATE_DIFF__${JSON.stringify(result.templateDiff)}`,
              timestamp: Date.now(),
            };
            addMessage(diffMessage);
          }

          // Check if the response contains buttons and activate them
          const responseText = agentResponse.text;
          const hasButtons =
            responseText.includes('<button') ||
            responseText.includes('option-button') ||
            responseText.includes('options-container');

          if (hasButtons) {
            // Find the message we just added and activate its buttons
            const allMessages = useTemplateChatStore?.getState().messages || [];
            const latestMessage = allMessages[allMessages.length - 1];
            if (latestMessage && latestMessage.id) {
              setMessageButtonsActive(latestMessage.id);
            }
          }

          // Show toast notification if template was modified
          if (result.templateModified) {
            toast.success('✨ Template updated', {
              description: 'The interview template has been updated with your changes.',
              duration: 3000,
            });
          }
        }

        // Collapse the thinking component after response is generated
        setIsHistoryExpanded(false);
      } catch (error: any) {
        console.error('Failed to send message:', error);

        // Remove the thinking message by ID if it exists
        if (thinkingMessageId) {
          removeMessageById(thinkingMessageId);
        }

        addMessage({
          sender: 'agent' as const,
          text: error?.message || 'Sorry, something went wrong.',
          timestamp: Date.now(),
        });

        // Collapse the thinking component even on error
        setIsHistoryExpanded(false);
      }
    },
    [
      input,
      templateId,
      isMasterTemplate,
      addMessage,
      removeMessageById,
      setMessageButtonsActive,
      deactivateAllButtons,
      sendMessage,
      useTemplateChatStore,
      chatMode,
    ],
  );

  // Set up global functions for HTMLRenderer option buttons to use
  useEffect(() => {
    // Function to send a message directly
    const sendMessageDirect = (messageText: string) => {
      handleSendMessage(messageText);
    };

    // Function to set input text
    const setInputText = (text: string) => {
      setInput(text);
    };

    // Set up global functions on window object
    (window as any).sendMessageDirect = sendMessageDirect;
    (window as any).setInput = setInputText;
    (window as any).setInputText = setInputText;
    (window as any).sendMessage = () => handleSendMessage();

    // Cleanup function
    return () => {
      delete (window as any).sendMessageDirect;
      delete (window as any).setInput;
      delete (window as any).setInputText;
      delete (window as any).sendMessage;
    };
  }, [handleSendMessage]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  const handleCloneTemplate = useCallback(async () => {
    try {
      await duplicateCurrentTemplate();
      toast.success('✨ Template cloned successfully', {
        description: 'You can now start modifying your own copy of the template.',
        duration: 3000,
      });
    } catch (error: any) {
      console.error('Failed to clone template:', error);
      toast.error('Failed to clone template', {
        description: error?.message || 'Please try again.',
        duration: 3000,
      });
    }
  }, [duplicateCurrentTemplate]);

  return (
    <div className="flex overflow-y-auto overflow-x-hidden flex-col h-full group">
      <div className="flex overflow-y-auto overflow-x-hidden flex-col flex-1 gap-2 px-2 py-2 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="flex flex-col justify-center items-center h-full">
            <div className="max-w-lg text-center">
              <h4 className="mb-2 text-base font-semibold text-gray-900 dark:text-gray-100">
                Let's start adjusting the capture template
              </h4>
              <p className="text-xs text-gray-500 dark:text-gray-500">
                💡 Tip: Provide a persona of the expert you are capturing knowledge from.
              </p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((msg, idx) => {
              const isThinking = msg.id && msg.id.startsWith('thinking-');
              const isDiffMessage = msg.text.startsWith('__TEMPLATE_DIFF__');
              const messageKey = msg.id || `msg-${idx}-${msg.sender}-${msg.text.substring(0, 20)}`;

              // Parse diff message if it's a diff
              if (isDiffMessage) {
                try {
                  const diffData = JSON.parse(msg.text.replace('__TEMPLATE_DIFF__', ''));
                  const parsedDiff = parseDiffResponse(diffData);
                  
                  // Only render if there are visible changes (add/remove sections)
                  if (parsedDiff) {
                    const changedSections = getChangedSections(parsedDiff);
                    if (changedSections.length > 0) {
                      return (
                        <div
                          key={messageKey}
                          className="rounded-sm px-3 py-2 text-sm self-start text-left bg-gray-50 border border-gray-200"
                        >
                          <div className="mb-2 text-xs font-semibold text-gray-700">
                            📝 Template Changes:
                          </div>
                          <DiffRenderer
                            sections={parsedDiff.sections}
                            maxChars={800}
                          />
                        </div>
                      );
                    }
                  }
                  // Return null if no visible changes - don't show the block at all
                  return null;
                } catch (e) {
                  console.error('Failed to parse diff message:', e);
                  return null;
                }
              }

              return (
                <div
                  key={messageKey}
                  className={`rounded-sm px-3 py-2 text-sm ${
                    msg.sender === 'user'
                      ? 'border border-gray-100 bg-gray-50'
                      : isThinking
                        ? 'self-start text-left border border-gray-100'
                        : 'self-start text-left bg-white'
                  }`}
                >
                  {isThinking ? (
                    <div className="flex gap-2 items-center">
                      <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                      <span className="text-sm text-gray-700">{msg.text}</span>
                    </div>
                  ) : (
                    <HybridRenderer
                      content={msg.text}
                      backgroundContext={msg.sender === 'user' ? 'user' : 'agent'}
                      messageId={msg.id}
                      hasActiveButtons={msg.hasActiveButtons ?? false}
                    />
                  )}
                </div>
              );
            })}
          </>
        )}
        <ProcessingStatusHistory
          messages={processingStatusHistory}
          isExpanded={isHistoryExpanded}
          onToggle={() => setIsHistoryExpanded(!isHistoryExpanded)}
        />

        <div ref={bottomRef} />
      </div>

      {/* Input Area */}
      <div className="p-3">
        {isMasterTemplate ? (
          // Show clone button for master templates
          <div className="flex flex-col gap-3 p-4 text-sm text-center bg-gray-50 rounded-lg border border-gray-200">
            <div>
              <p className="font-medium text-gray-700">Master Template (Read-Only)</p>
              <p className="mt-1 text-xs text-gray-500">
                This is a master template and cannot be modified directly.
              </p>
            </div>
            <button
              onClick={handleCloneTemplate}
              disabled={isCreatingTemplate}
              className="flex gap-2 justify-center items-center px-4 py-2 mx-auto font-medium text-white bg-gray-700 cursor-pointer rounded-sm transition-colors hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isCreatingTemplate ? (
                <>
                  <div className="w-4 h-4 rounded-full border-2 border-white animate-spin border-t-transparent"></div>
                  <span>Cloning template...</span>
                </>
              ) : (
                <>
                  <span>Clone and modify template</span>
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="flex flex-col gap-2">
            {/* Mode Dropdown */}
            <div className="flex justify-end">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="outline" size="sm" className="gap-2">
                    Mode: {chatMode === 'chat' ? 'Chat' : 'Editor'}
                    <IconChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem onClick={() => setChatMode('chat')}>
                    Chat
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => setChatMode('editor')}>
                    Editor
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
            <div className="relative">
            {/* Animated placeholder overlay */}
            {!input && !isSendingMessage && (
              <div className="absolute top-3 left-3 z-10 text-sm text-gray-500 pointer-events-none">
                <AnimatedPlaceholder
                  hasMessages={messages.some((msg) => msg.sender === 'user')}
                  isFocused={isFocused}
                  hasInteracted={hasInteracted}
                />
              </div>
            )}
            <textarea
              className="w-full min-h-[100px] max-h-[120px] pl-3 pr-12 py-3 text-sm rounded-lg bg-gray-100 border-gray-300
                focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-transparent resize-none overflow-y-auto"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              onFocus={() => {
                setIsFocused(true);
                setHasInteracted(true);
              }}
              onBlur={() => setIsFocused(false)}
              disabled={isSendingMessage}
              rows={1}
              style={{
                height: 'auto',
                minHeight: '100px',
              }}
              onInput={(e) => {
                const target = e.target as HTMLTextAreaElement;
                target.style.height = 'auto';
                target.style.height = Math.min(target.scrollHeight, 120) + 'px';
              }}
            />
            {input.trim() && (
              <button
                onClick={() => handleSendMessage()}
                className="absolute right-3 bottom-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:shadow-md hover:cursor-pointer"
                title="Send message"
                disabled={isSendingMessage}
              >
                <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
              </button>
            )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// Export component with template props
interface ChatSidebarProps {
  templateId: number;
}

export function ChatSidebar({ templateId }: ChatSidebarProps) {
  return <ContributionTemplateChat templateId={templateId} />;
}

