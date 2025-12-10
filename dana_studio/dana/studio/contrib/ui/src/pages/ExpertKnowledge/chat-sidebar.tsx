/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { apiService } from '@/lib/api';
import { createSmartChatStore } from '@/stores/smart-chat-store';
import { useCaptureKnowledgeStore } from '@/stores';
import { ArrowUp, Expand, Collapse } from 'iconoir-react';
import { HybridRenderer } from '@/pages/Agents/chat/hybrid-renderer';
import { useTimerContext } from '@/contexts/TimerContext';
import { SESSION_STATUS } from '@/lib/constants';

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
if (typeof window !== 'undefined' && !document.getElementById('session-animated-placeholder-styles')) {
  const styleSheet = document.createElement('style');
  styleSheet.id = 'session-animated-placeholder-styles';
  styleSheet.textContent = cursorBlinkStyle;
  document.head.appendChild(styleSheet);
}

// Animated placeholder component - only shown for new users (no messages sent)
const PLACEHOLDER_MESSAGES = [
  'Share your expert knowledge...',
  'Describe your experience...',
  'Tell me about your expertise...',
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
    update_note: 'Update Interview Notes',
    analyze_response: 'Analyze Response',
    extract_insights: 'Extract Insights',
    generate_questions: 'Generate Questions',
    summarize_session: 'Summarize Session',
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

// Main chat component for Capture Knowledge Session
const CaptureKnowledgeSessionChat: React.FC<{
  sessionId: number;
}> = ({ sessionId }) => {
  const [input, setInput] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  // Welcome message tracking refs
  const hasShownWelcomeMessageRef = useRef(false);
  const welcomeMessageTimeoutRef = useRef<number | null>(null);

  // Debug refs to track previous values
  const prevMessagesRef = useRef<any[]>([]);
  const prevInputRef = useRef<string>('');
  const prevContributionTemplateRef = useRef<any>(null);
  const prevCurrentSessionRef = useRef<any>(null);
  const renderCountRef = useRef<number>(0);

  // Create session-specific chat store
  const useSessionChatStore = useMemo(() => {
    return createSmartChatStore(`session-${sessionId}`);
  }, [sessionId]);

  // Call the store hook unconditionally at top level
  const messages = useSessionChatStore((s) => s.messages);
  const addMessage = useSessionChatStore((s) => s.addMessage);
  const removeMessageById = useSessionChatStore((s) => s.removeMessageById);
  const setMessages = useSessionChatStore((s) => s.setMessages);
  const setMessageButtonsActive = useSessionChatStore((s) => s.setMessageButtonsActive);
  const deactivateAllButtons = useSessionChatStore((s) => s.deactivateAllButtons);

  // Access template data and session from capture knowledge store
  const { contributionTemplate, currentSession } = useCaptureKnowledgeStore();
  
  // Access timer context to start timer on first message
  const { timer } = useTimerContext();

  // Check if session is completed
  const isSessionCompleted = currentSession?.status === SESSION_STATUS.COMPLETED;

  // Debug logging for component renders and state changes
  useEffect(() => {
    renderCountRef.current += 1;
    const renderCount = renderCountRef.current;
    
    const messagesChanged = messages !== prevMessagesRef.current;
    const messagesArrayChanged = messages.length !== prevMessagesRef.current.length || 
      (messages.length > 0 && messages[0] !== prevMessagesRef.current[0]);
    const inputChanged = input !== prevInputRef.current;
    const templateChanged = contributionTemplate !== prevContributionTemplateRef.current;
    const sessionChanged = currentSession !== prevCurrentSessionRef.current;
    
    console.log(`[ChatSidebar] Render #${renderCount}`, {
      sessionId,
      messagesChanged,
      messagesArrayChanged,
      messagesLength: messages.length,
      prevMessagesLength: prevMessagesRef.current.length,
      inputChanged,
      templateChanged,
      sessionChanged,
      isSending,
      isTyping,
      isFocused,
    });
    
    if (messagesChanged || messagesArrayChanged) {
      console.log('[ChatSidebar] Messages array reference or content changed', {
        sessionId,
        prevLength: prevMessagesRef.current.length,
        newLength: messages.length,
        prevFirstMessageId: prevMessagesRef.current[0]?.id,
        newFirstMessageId: messages[0]?.id,
        messagesArrayReferenceChanged: messages !== prevMessagesRef.current,
        messageObjectsChanged: messages.length > 0 && messages[0] !== prevMessagesRef.current[0],
      });
      prevMessagesRef.current = messages;
    }
    
    if (inputChanged) {
      prevInputRef.current = input;
    }
    if (templateChanged) {
      prevContributionTemplateRef.current = contributionTemplate;
    }
    if (sessionChanged) {
      prevCurrentSessionRef.current = currentSession;
    }
  }, [messages, input, contributionTemplate, currentSession, isSending, isTyping, isFocused, sessionId]);

  // Debug logging for template loading
  useEffect(() => {
    console.log('🔍 ChatSidebar - Template state changed:', {
      hasTemplate: !!contributionTemplate,
      templateName: contributionTemplate?.name,
      templateDomain: contributionTemplate?.template_metadata?.domain,
      hasReadmeContent: !!contributionTemplate?.readme_content,
      messagesCount: messages.length,
      hasShownWelcome: hasShownWelcomeMessageRef.current,
    });
  }, [contributionTemplate, messages.length]);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const messagesContainerRef = useRef<HTMLDivElement | null>(null);
  const [processingStatusHistory, setProcessingStatusHistory] = useState<ProcessingStatusMessage[]>(
    [],
  );
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const [conversationLoaded, setConversationLoaded] = useState(false);
  const hasAnyMessagesRef = useRef(false); // Track if conversation has any messages at all

  // Progress API state management
  const [progressData, setProgressData] = useState<{
    topics: Array<{ topic_name: string }>;
    overall_completeness: number;
    current_topic: string | null;
  } | null>(null);
  const [progressLoading, setProgressLoading] = useState(false);
  const [progressError, setProgressError] = useState<string | null>(null);

  // Ref to store latest progress data for use in setTimeout callbacks (avoids stale closures)
  const progressDataRef = useRef<{
    topics: Array<{ topic_name: string }>;
    overall_completeness: number;
    current_topic: string | null;
  } | null>(null);

  // Update ref whenever progressData changes
  useEffect(() => {
    progressDataRef.current = progressData;
  }, [progressData]);

  // Function to fetch progress with retry logic
  const fetchProgressWithRetry = useCallback(
    async (
      sessionId: number,
      maxAttempts: number = 3,
      initialDelay: number = 1000,
    ): Promise<{
      topics: Array<{ topic_name: string }>;
      overall_completeness: number;
      current_topic: string | null;
    } | null> => {
      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          console.log(`🔄 Fetching progress (attempt ${attempt}/${maxAttempts}) for session ${sessionId}`);
          const response = await apiService.getSessionProgress(sessionId);

          if (response && response.success && response.data) {
            const topics = response.data.topics || [];
            
            // If first attempt returns empty topics and session is new, wait longer before retry
            if (attempt === 1 && topics.length === 0 && !hasAnyMessagesRef.current) {
              console.log('⚠️ Empty topics on first attempt for new session, waiting longer...');
              if (attempt < maxAttempts) {
                const delay = initialDelay * Math.pow(2, attempt); // Exponential backoff: 2s, 4s
                await new Promise((resolve) => setTimeout(resolve, delay));
                continue;
              }
            }

            console.log(`✅ Progress fetched successfully: ${topics.length} topics found`);
            return {
              topics: topics,
              overall_completeness: response.data.overall_completeness || 0,
              current_topic: response.data.current_topic || null,
            };
          } else {
            console.warn(`⚠️ Progress API returned unsuccessful response:`, response);
            if (attempt < maxAttempts) {
              const delay = initialDelay * Math.pow(1.5, attempt - 1); // Exponential backoff
              console.log(`⏳ Retrying in ${delay}ms...`);
              await new Promise((resolve) => setTimeout(resolve, delay));
            }
          }
        } catch (error: any) {
          console.error(`❌ Progress fetch attempt ${attempt} failed:`, error);
          if (attempt < maxAttempts) {
            const delay = initialDelay * Math.pow(1.5, attempt - 1); // Exponential backoff
            console.log(`⏳ Retrying in ${delay}ms...`);
            await new Promise((resolve) => setTimeout(resolve, delay));
          } else {
            console.error('❌ Progress fetch failed after all attempts');
            throw error;
          }
        }
      }

      // Maximum wait time exceeded, return null (welcome message will show message about topics on right side)
      console.warn('⚠️ Progress fetch failed after all retries');
      return null;
    },
    [],
  );

  // Function to extract topics from progress data
  const extractTopicsFromProgress = useCallback(
    (
      progressData: {
        topics: Array<{ topic_name: string }>;
        overall_completeness: number;
        current_topic: string | null;
      } | null,
    ): string[] => {
      if (!progressData || !progressData.topics || !Array.isArray(progressData.topics)) {
        return [];
      }

      return progressData.topics.map((topic) => topic.topic_name).filter((name) => name && name.trim());
    },
    [],
  );

  // Function to get topics for welcome message (only from progress API, no README fallback)
  const getTopicsForWelcomeMessage = useCallback((): string[] => {
    // Use ref to get latest progress data (avoids stale closure issues in setTimeout callbacks)
    const currentProgressData = progressDataRef.current;
    
    // Only use topics from progress data
    const progressTopics = extractTopicsFromProgress(currentProgressData);
    if (progressTopics.length > 0) {
      console.log(`✅ Using ${progressTopics.length} topics from progress API`);
      return progressTopics;
    }

    // No fallback - return empty array (will show message about topics on right side)
    console.log('⚠️ No topics found from progress API');
    return [];
  }, [extractTopicsFromProgress]);

  // Function to show welcome message with typing effect
  const showWelcomeMessageWithTypingEffect = useCallback(() => {
    // Prevent duplicate welcome messages using ref to avoid stale closures
    if (hasShownWelcomeMessageRef.current) {
      console.log('⚠️ Welcome message already shown, skipping');
      return null;
    }

    console.log('🎬 Starting welcome message with typing effect');
    // Mark that we're showing a welcome message
    hasShownWelcomeMessageRef.current = true;

    // Show typing effect for 2 seconds before displaying the welcome message
    setIsTyping(true);

    const timeoutId = setTimeout(() => {
      setIsTyping(false);
      
      // Get template information
      const templateName = contributionTemplate?.name || 'this template';
      const domain = contributionTemplate?.template_metadata?.domain || 'your expertise';
      const topics = getTopicsForWelcomeMessage();

      console.log('📝 Generating welcome message:', {
        templateName,
        domain,
        topicsCount: topics.length,
        topics: topics.slice(0, 3), // Show first 3 topics for debugging
      });

      // Generate welcome message
      let welcomeText = `Welcome to the Capture Knowledge session for **${templateName}**!\n\n`;
      welcomeText += `I'm here to help you capture your expertise in **${domain}**. `;
      
      if (topics.length > 0) {
        welcomeText += `This session covers the following topics:\n`;
        topics.forEach(topic => {
          welcomeText += `- ${topic}\n`;
        });
        welcomeText += `\nWhich topic area would you like to start with? `;
      } else {
        welcomeText += `\nYou can see the topics we'll cover on the right side of the screen. `;
      }
      
      welcomeText += `Or feel free to share any knowledge that comes to mind — I'll guide the conversation from there.\n\n`;

      console.log('✅ Adding welcome message to chat');
      const welcomeMessage = {
        sender: 'agent' as const,
        text: welcomeText,
        timestamp: Date.now(),
        hasActiveButtons: true, // Welcome message should have active buttons
      };
      addMessage(welcomeMessage);

      // Activate buttons for the welcome message
      const allMessages = useSessionChatStore?.getState().messages || [];
      const latestMessage = allMessages[allMessages.length - 1];
      if (latestMessage && latestMessage.id) {
        setMessageButtonsActive(latestMessage.id);
      }
    }, 2000);

    // Store the timeout ID for cleanup purposes
    welcomeMessageTimeoutRef.current = timeoutId;
    return timeoutId;
  }, [addMessage, contributionTemplate, getTopicsForWelcomeMessage, setMessageButtonsActive, useSessionChatStore]);

  // Load conversation when session opens
  useEffect(() => {
    const loadConversationHistory = async () => {
      if (!sessionId || conversationLoaded) return;

      try {
        const response = await apiService.getSessionConversation(sessionId);
        if (response && response.messages && Array.isArray(response.messages)) {
          // Track if conversation has any messages
          hasAnyMessagesRef.current = response.messages.length > 0;
          
          // Convert conversation messages to smart chat format
          const smartMessages = response.messages.map((msg: any) => ({
            sender: msg.sender === 'user' ? 'user' : 'agent',
            text: msg.content,
            timestamp: new Date(msg.created_at || Date.now()).getTime(),
            id: `msg-${msg.id || Math.random()}`,
            hasActiveButtons: false,
          }));
          setMessages(smartMessages);
        } else {
          // No messages in conversation
          hasAnyMessagesRef.current = false;
        }
        // Note: Don't show welcome message here - wait for template to be loaded
      } catch (error: any) {
        console.error('Failed to load conversation history:', error);
        // On error, assume no messages
        hasAnyMessagesRef.current = false;
        // Note: Don't show welcome message here - wait for template to be loaded
      }
      
      // Mark as loaded AFTER we've set hasAnyMessagesRef
      setConversationLoaded(true);
    };

    loadConversationHistory();
  }, [sessionId, conversationLoaded, setMessages]);

  // Fetch progress when session loads
  useEffect(() => {
    const loadProgress = async () => {
      if (!sessionId) return;

      try {
        setProgressLoading(true);
        setProgressError(null);
        const result = await fetchProgressWithRetry(sessionId);
        if (result) {
          setProgressData(result);
          console.log(`✅ Progress loaded: ${result.topics.length} topics`);
        } else {
          setProgressData(null);
          console.log('⚠️ Progress fetch returned null, will use README fallback');
        }
      } catch (error: any) {
        const errorMessage = error?.message || 'Failed to load progress';
        console.error('❌ Failed to load progress:', errorMessage);
        setProgressError(errorMessage);
        setProgressData(null);
        // Log error for debugging (using progressError state)
        if (errorMessage) {
          console.debug('Progress error state set:', errorMessage);
        }
      } finally {
        setProgressLoading(false);
      }
    };

    loadProgress();
  }, [sessionId, fetchProgressWithRetry]);

  // Debug log progress errors
  useEffect(() => {
    if (progressError) {
      console.debug('Progress error state:', progressError);
    }
  }, [progressError]);

  // Show welcome message when template becomes available and conversation has no messages at all
  useEffect(() => {
    // Don't show welcome message if conditions aren't met
    if (!contributionTemplate || !conversationLoaded || hasAnyMessagesRef.current || hasShownWelcomeMessageRef.current) {
      return;
    }

    // Set up timeout mechanism: if progress takes too long (>3 seconds), proceed with README fallback
    const progressTimeout = setTimeout(() => {
      if (!hasShownWelcomeMessageRef.current) {
        console.log('⏰ Progress loading timeout, proceeding with welcome message (will use README fallback if needed)');
        showWelcomeMessageWithTypingEffect();
      }
    }, 3000);

    // If progress is not loading, we can show welcome message immediately
    // (either progress loaded successfully, failed, or was never needed)
    if (!progressLoading) {
      clearTimeout(progressTimeout);
      console.log('🎉 Showing welcome message for truly new conversation:', contributionTemplate.name);
      showWelcomeMessageWithTypingEffect();
      return;
    }

    // Cleanup timeout if component unmounts or dependencies change
    return () => {
      clearTimeout(progressTimeout);
    };
  }, [contributionTemplate, conversationLoaded, progressLoading, showWelcomeMessageWithTypingEffect]);

  // Cleanup welcome message timeout on unmount or session change
  useEffect(() => {
    return () => {
      if (welcomeMessageTimeoutRef.current) {
        clearTimeout(welcomeMessageTimeoutRef.current);
        welcomeMessageTimeoutRef.current = null;
      }
    };
  }, [sessionId]);

  // Reset refs and progress state when session changes
  useEffect(() => {
    hasShownWelcomeMessageRef.current = false;
    setConversationLoaded(false); // This will trigger reload
    hasAnyMessagesRef.current = false;
    // Reset progress state
    setProgressData(null);
    setProgressLoading(false);
    setProgressError(null);
  }, [sessionId]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesContainerRef.current) {
      // Scroll the messages container directly, not the page
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [messages]);

  // Auto-scroll when new thinking messages are added
  useEffect(() => {
    if (messagesContainerRef.current && processingStatusHistory.length > 0) {
      // Scroll the messages container directly, not the page
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth',
      });
    }
  }, [processingStatusHistory]);

  const handleSendMessage = useCallback(
    async (messageText?: string) => {
      const textToSend = messageText || input.trim();
      if (!textToSend || !sessionId || isSessionCompleted) return;

      // Resume timer if paused when user sends a message
      if (timer && timer.isPaused) {
        console.log('[Timer] Message sent while paused, resuming timer');
        timer.resume();
      }

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
        setIsSending(true);

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

        // Send message via API
        const result = await apiService.chatWithSession(sessionId, userInput);

        // Remove the thinking message by ID if it exists
        if (thinkingMessageId) {
          removeMessageById(thinkingMessageId);
        }

          // Add the actual response
          if (result && result.success && result.agent_response) {
            const agentResponse = {
              sender: 'agent' as const,
              text: result.agent_response,
              timestamp: Date.now(),
            };
            addMessage(agentResponse);

            // Refresh Complete button state after message is sent
            if ((window as any).refreshCompleteButton) {
              console.log('[Chat] Refreshing Complete button state after message sent');
              (window as any).refreshCompleteButton();
            }

          // Check if the response contains buttons and activate them
          const responseText = agentResponse.text;
          const hasButtons =
            responseText.includes('<button') ||
            responseText.includes('option-button') ||
            responseText.includes('options-container');

          if (hasButtons) {
            // Find the message we just added and activate its buttons
            const allMessages = useSessionChatStore?.getState().messages || [];
            const latestMessage = allMessages[allMessages.length - 1];
            if (latestMessage && latestMessage.id) {
              setMessageButtonsActive(latestMessage.id);
            }
          }

          // Trigger progress refresh after agent response with retry logic
          if ((window as any).refreshSessionProgress) {
            console.log('🔄 Triggering progress refresh after agent response');
            
            // Retry mechanism with exponential backoff
            const refreshWithRetry = async (attempt = 1, maxAttempts = 3, delay = 1000) => {
              try {
                console.log(`🔄 Refresh attempt ${attempt}/${maxAttempts}`);
                await (window as any).refreshSessionProgress();
                console.log('✅ Progress refresh successful');
              } catch (error) {
                console.error(`❌ Progress refresh attempt ${attempt} failed:`, error);
                
                if (attempt < maxAttempts) {
                  const nextDelay = delay * Math.pow(1.5, attempt - 1); // Exponential backoff
                  console.log(`⏳ Retrying in ${nextDelay}ms...`);
                  setTimeout(() => refreshWithRetry(attempt + 1, maxAttempts, delay), nextDelay);
                } else {
                  console.error('❌ Progress refresh failed after all attempts');
                }
              }
            };
            
            // Initial delay to ensure backend has written notes
            setTimeout(() => refreshWithRetry(), 1000); // Increased from 500ms to 1000ms
          }

          // Process internal conversation for tool execution tracking
          if (result.internal_conversation && Array.isArray(result.internal_conversation)) {
            const toolMessages: ProcessingStatusMessage[] = result.internal_conversation.map((msg: any, index: number) => ({
              id: `tool-${Date.now()}-${index}`,
              toolName: msg.tool_name || 'unknown_tool',
              message: msg.content || msg.message || 'Processing...',
              status: msg.status || 'in_progress',
              progression: msg.progression,
              timestamp: new Date(),
            }));
            setProcessingStatusHistory(toolMessages);
          }
        } else {
          addMessage({
            sender: 'agent' as const,
            text: result?.error || 'Sorry, I could not process your request.',
            timestamp: Date.now(),
          });
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
      } finally {
        setIsSending(false);
      }
    },
    [
      input,
      sessionId,
      addMessage,
      removeMessageById,
      setMessageButtonsActive,
      deactivateAllButtons,
      useSessionChatStore,
      messages,
      timer,
      isSessionCompleted,
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

  return (
    <div className="flex overflow-hidden flex-col h-full group">
      <div ref={messagesContainerRef} className="flex overflow-y-auto overflow-x-hidden flex-col flex-1 min-h-0 max-h-full gap-2 px-2 py-2 custom-scrollbar">
        {messages.length === 0 && !isTyping ? (
          <div className="flex flex-col justify-center items-center h-full">
            <div className="max-w-lg text-center">
              <h4 className="mb-2 text-base font-semibold text-gray-900 dark:text-gray-100">
                Let's start capturing your expert knowledge
              </h4>
           
            </div>
          </div>
        ) : (
          <>
            {/* Show typing indicator when welcome message is being prepared */}
            {isTyping && messages.length === 0 && (
              <div className="rounded-sm px-3 py-2 text-sm self-start text-left bg-white">
                <div className="flex gap-2 items-center">
                  <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                  <span className="text-sm text-gray-700">Preparing the session...</span>
                </div>
              </div>
            )}
            
            {messages.map((msg, idx) => {
              const isThinking = msg.id && msg.id.startsWith('thinking-');
              const messageKey = msg.id || `msg-${idx}-${msg.sender}-${msg.text.substring(0, 20)}`;

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
      <div className="flex-shrink-0 p-3">
        <div className="relative">
          {/* Animated placeholder overlay */}
          {!input && !isSending && !isSessionCompleted && (
            <div className="absolute top-3 left-3 z-10 text-sm text-gray-500 pointer-events-none">
              <AnimatedPlaceholder
                hasMessages={messages.some((msg) => msg.sender === 'user')}
                isFocused={isFocused}
                hasInteracted={hasInteracted}
              />
            </div>
          )}
          {/* Completed session message */}
          {isSessionCompleted && (
            <div className="absolute top-3 left-3 z-10 text-sm text-gray-500 pointer-events-none">
              This session has been completed. Chat is disabled.
            </div>
          )}
          <textarea
            className="w-full min-h-[100px] max-h-[120px] pl-3 pr-12 py-3 text-sm rounded-lg bg-gray-100 border-gray-300
              focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-transparent resize-none overflow-y-auto
              disabled:opacity-60 disabled:cursor-not-allowed"
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
            disabled={isSending || isSessionCompleted}
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
            title={isSessionCompleted ? 'This session has been completed. Chat is disabled.' : ''}
          />
          {input.trim() && (
            <button
              onClick={() => handleSendMessage()}
              className="absolute right-3 bottom-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:shadow-md hover:cursor-pointer disabled:opacity-60 disabled:cursor-not-allowed"
              title={isSessionCompleted ? 'This session has been completed. Chat is disabled.' : 'Send message'}
              disabled={isSending || isSessionCompleted}
            >
              <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Export component with session props
interface ChatSidebarProps {
  sessionId: number;
}

export function ChatSidebar({ sessionId }: ChatSidebarProps) {
  return (
    <CaptureKnowledgeSessionChat
      sessionId={sessionId}
    />
  );
}