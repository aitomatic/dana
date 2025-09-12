import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import { apiService } from '@/lib/api';
import { useParams } from 'react-router-dom';
import { createSmartChatStore, clearSmartChatStorageForAgent } from '@/stores/smart-chat-store';
import { useAgentStore } from '@/stores/agent-store';
import { useKnowledgeStore } from '@/stores/knowledge-store';
import { useUIStore } from '@/stores/ui-store';
import { ArrowUp, Expand, Collapse } from 'iconoir-react';
import { HybridRenderer } from './chat/hybrid-renderer';
import { useSmartChatWebSocket, type ChatUpdateMessage } from '@/hooks/useSmartChatWebSocket';

// Constants for resize functionality
const MIN_WIDTH = 380;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 420;
const RESIZE_HANDLE_WIDTH = 2;

// Function to convert snake_case tool names to friendly display names
const formatToolName = (toolName: string): string => {
  const toolNameMap: Record<string, string> = {
    generate_knowledge: 'Generate Knowledge',
    modify_tree: 'Modify Tree',
    ask_question: 'General Q&A',
    search_documents: 'Search Documents',
    analyze_data: 'Analyze Data',
    create_summary: 'Create Summary',
    extract_information: 'Extract Information',
    process_request: 'Process Request',
    update_knowledge: 'Update Knowledge',
    validate_input: 'Validate Input',
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

// Resize handle component
const ResizeHandle: React.FC<{
  onResize: (width: number) => void;
  isResizing: boolean;
  setIsResizing: (resizing: boolean) => void;
}> = ({ onResize, isResizing, setIsResizing }) => {
  const handleRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef<number>(0);
  const startWidthRef = useRef<number>(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (!handleRef.current) return;

      setIsResizing(true);
      startXRef.current = e.clientX;
      startWidthRef.current = handleRef.current.parentElement?.offsetWidth || DEFAULT_WIDTH;

      // Add global mouse event listeners
      const handleMouseMove = (e: MouseEvent) => {
        const deltaX = e.clientX - startXRef.current;
        const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidthRef.current + deltaX));
        onResize(newWidth);
      };

      const handleMouseUp = () => {
        setIsResizing(false);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [onResize, setIsResizing],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isResizing) {
        setIsResizing(false);
      }
    };
  }, [isResizing, setIsResizing]);

  return (
    <div
      ref={handleRef}
      className={`
        absolute top-0 right-0 h-full z-50
        hover:bg-gray-200 hover:shadow-sm transition-all duration-200
        ${isResizing ? 'bg-primary' : 'hover:bg-gray-200'}
        group
      `}
      onMouseDown={handleMouseDown}
      style={{
        width: `${RESIZE_HANDLE_WIDTH}px`,
        cursor: 'col-resize',
      }}
      title="Drag to resize sidebar"
    >
      {/* Visual indicator line */}
      <div
        className={`
          absolute top-1/2 left-1/2 transform -translate-x-1/3 -translate-y-1/2
          w-2 h-8 rounded-full transition-all duration-200 border border-gray-300
          ${isResizing ? 'bg-white shadow-sm' : 'bg-white shadow-sm group-hover:bg-primary'}
        `}
        style={{
          zIndex: 60,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
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
    <div className="flex flex-col gap-2 self-start px-3 py-2 text-left bg-gray-50 rounded-lg border border-gray-200">
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

const SmartAgentChat: React.FC<{
  agentName?: string;
  onConnectionStateChange?: (state: string) => void;
}> = ({ agentName, onConnectionStateChange }) => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [isTyping, setIsTyping] = useState(false);

  // Create agent-specific store
  const agentStore = useMemo(() => {
    if (!agent_id) return null;
    return createSmartChatStore(agent_id);
  }, [agent_id]);

  // Use agent-specific store methods
  const messages = agentStore ? agentStore((s) => s.messages) : [];
  const addMessage = agentStore ? agentStore((s) => s.addMessage) : () => {};
  const removeMessageById = agentStore ? agentStore((s) => s.removeMessageById) : () => {};
  const clearMessages = agentStore ? agentStore((s) => s.clearMessages) : () => {};
  const setMessages = agentStore ? agentStore((s) => s.setMessages) : () => {};
  const getMessageCount = agentStore ? agentStore((s) => s.getMessageCount) : () => 0;

  // Make sendMessage globally available for HTMLRenderer to call
  useEffect(() => {
    (window as any).sendMessage = () => {
      if (input.trim() && agent_id) {
        sendMessage();
      }
    };

    (window as any).setInput = (value: string) => {
      setInput(value);
    };

    return () => {
      delete (window as any).sendMessage;
      delete (window as any).setInput;
    };
  }, [input, agent_id]);

  // fetchAgent removed - now using direct API calls to avoid loading skeleton
  const { setAgentDetailActiveTab, setKnowledgeBaseActiveSubTab } = useUIStore();
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [processingStatusHistory, setProcessingStatusHistory] = useState<ProcessingStatusMessage[]>(
    [],
  );
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [hasLoadedHistory, setHasLoadedHistory] = useState(false);
  const [previousAgentId, setPreviousAgentId] = useState<string | null>(null);
  const welcomeMessageTimeoutRef = useRef<number | null>(null);
  const hasShownWelcomeMessageRef = useRef(false);

  // Function to show welcome message with typing effect
  const showWelcomeMessageWithTypingEffect = useCallback(
    (displayName: string, agentDomain: string) => {
      // Prevent duplicate welcome messages using ref to avoid stale closures
      if (hasShownWelcomeMessageRef.current) {
        return null;
      }

      // Mark that we're showing a welcome message
      hasShownWelcomeMessageRef.current = true;

      // Show typing effect for 2 seconds before displaying the welcome message
      setIsTyping(true);

      const timeoutId = setTimeout(() => {
        setIsTyping(false);
        addMessage({
          sender: 'agent',
          text: displayName
            ? `Great — you've started with the ${displayName} - the expert in ${agentDomain}.
Now let's shape it into an agent that really works for you. To begin, tell me:
- What kind of ${agentDomain.toLowerCase()} expertise should it focus on?
- Who will this agent primarily assist (e.g. individuals, analysts, business owners)?

💡 Tip: If you have a **job description**, you can paste it here — I'll use it to tailor the agent's knowledge base.`
            : `Exciting — you're about to build your own custom agent from the ground up! 🚀

To get started, let's define its foundation:

- What **domain or expertise** should your agent specialize in? (e.g. healthcare, semiconductor, education)
- **Who** will it assist? (e.g. financial analysts, IT engineers)?

💡 Tip: You can provide a **job description**, and I'll draft the starting expertise for your agent.`,
        });
      }, 2000);

      // Store the timeout ID for cleanup purposes
      welcomeMessageTimeoutRef.current = timeoutId;
      return timeoutId;
    },
    [addMessage],
  );

  // Function to show fallback welcome message with typing effect
  const showFallbackWelcomeMessageWithTypingEffect = useCallback(() => {
    // Prevent duplicate welcome messages using ref to avoid stale closures
    if (hasShownWelcomeMessageRef.current) {
      return null;
    }

    // Mark that we're showing a welcome message
    hasShownWelcomeMessageRef.current = true;

    // Show typing effect for 2 seconds before displaying the fallback welcome message
    setIsTyping(true);

    const timeoutId = setTimeout(() => {
      setIsTyping(false);
      addMessage({ sender: 'agent', text: 'Welcome! How can I assist you with this agent?' });
    }, 2000);

    // Store the timeout ID for cleanup purposes
    welcomeMessageTimeoutRef.current = timeoutId;
    return timeoutId;
  }, [addMessage]);

  // Agent switch detection and cleanup
  useEffect(() => {
    if (agent_id && agent_id !== previousAgentId) {
      // Agent has changed, reset state and clear messages
      console.log(`[Agent Switch] Switching from ${previousAgentId} to ${agent_id}`);

      if (previousAgentId) {
        // Clear any pending welcome message timeout
        if (welcomeMessageTimeoutRef.current) {
          clearTimeout(welcomeMessageTimeoutRef.current);
          welcomeMessageTimeoutRef.current = null;
        }

        // Clear messages from previous agent
        clearMessages();
        setHasLoadedHistory(false);
        setIsLoadingHistory(false);
        setIsTyping(false);
        hasShownWelcomeMessageRef.current = false;
      }

      setPreviousAgentId(agent_id);
    }
  }, [agent_id, previousAgentId, clearMessages]);

  // Cleanup function to clear smart-chat-storage when user leaves training view
  const cleanupOnExit = useCallback(() => {
    if (agent_id) {
      try {
        clearSmartChatStorageForAgent(agent_id);
        console.log(`[Exit Cleanup] Cleared smart-chat-storage for agent ${agent_id}`);
      } catch (error) {
        console.warn('Failed to clear storage on exit:', error);
      }
    }
  }, [agent_id]);

  // Cleanup effect for agent changes
  useEffect(() => {
    return () => {
      // When component unmounts or agent changes, ensure cleanup
      if (agent_id && previousAgentId && agent_id !== previousAgentId) {
        console.log(`[Cleanup] Cleaning up messages for agent ${previousAgentId}`);
        // The agent-specific store will handle its own cleanup
      }
    };
  }, [agent_id, previousAgentId]);

  // Comprehensive cleanup effect for component unmounting
  useEffect(() => {
    return () => {
      // Clean up all state when component unmounts
      console.log(`[Unmount] Cleaning up component for agent ${agent_id}`);

      // Clear any pending welcome message timeout
      if (welcomeMessageTimeoutRef.current) {
        clearTimeout(welcomeMessageTimeoutRef.current);
        welcomeMessageTimeoutRef.current = null;
      }

      // Clear smart-chat-storage when component unmounts
      cleanupOnExit();

      // Reset all local state
      setHasLoadedHistory(false);
      setIsLoadingHistory(false);
      setPreviousAgentId(null);
      setIsTyping(false);
      hasShownWelcomeMessageRef.current = false;

      // Clear any pending operations
      if (loading) {
        setLoading(false);
      }
    };
  }, [agent_id, loading, cleanupOnExit]);

  // Option click handling is now done directly in HTMLRenderer
  // No global handlers needed

  // WebSocket integration for real-time updates
  const handleChatUpdate = useCallback((message: ChatUpdateMessage) => {
    const newStatusMessage: ProcessingStatusMessage = {
      id: `${Date.now()}-${Math.random()}`,
      toolName: message.tool_name,
      message: message.content,
      status: message.status,
      progression: message.progression,
      timestamp: new Date(),
    };

    setProcessingStatusHistory((prev) => {
      // If this is an update to an existing tool, replace it
      const existingIndex = prev.findIndex((msg) => msg.toolName === message.tool_name);
      if (existingIndex !== -1) {
        const updated = [...prev];
        updated[existingIndex] = newStatusMessage;
        return updated;
      }
      // Otherwise add as new message
      return [...prev, newStatusMessage];
    });

    // Don't clear processing status - keep it in history
    // Only remove very old messages (older than 1 hour) to prevent memory issues
    setTimeout(
      () => {
        setProcessingStatusHistory((prev) =>
          prev.filter(
            (msg) => Date.now() - msg.timestamp.getTime() < 60 * 60 * 1000, // 1 hour
          ),
        );
      },
      60 * 60 * 1000,
    );
  }, []);

  const { connectionState } = useSmartChatWebSocket({
    agentId: agent_id || '',
    onChatUpdate: handleChatUpdate,
    onConnect: () => console.log('🟢 WebSocket connected'),
    onDisconnect: () => console.log('🔴 WebSocket disconnected'),
    onError: (error) => console.error('❌ WebSocket error:', error),
    enabled: !!agent_id, // Only enable when we have an agent_id
  });

  // Notify parent component of connection state changes
  useEffect(() => {
    onConnectionStateChange?.(connectionState);
  }, [connectionState, onConnectionStateChange]);

  // Function to handle CTA button click
  const handleCTAClick = () => {
    setInput('Add knowledge about ');
    // Focus the input field after a short delay to ensure it's rendered
    setTimeout(() => {
      const textarea = document.querySelector(
        'textarea[placeholder="Type your message"]',
      ) as HTMLTextAreaElement;
      if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
      }
    }, 100);
  };

  // Function to handle "Add documents" CTA button click
  const handleAddDocumentsClick = () => {
    setAgentDetailActiveTab('Knowledge Base');
    setKnowledgeBaseActiveSubTab('Documents');

    // Add a message to the chat panel
    addMessage({
      sender: 'agent',
      text: 'Now, please upload your files in Documents panel',
    });
  };

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!agent_id || !agentStore || isLoadingHistory || hasLoadedHistory) return;

      setIsLoadingHistory(true);
      try {
        const history = await apiService.getSmartChatHistory(agent_id);
        if (Array.isArray(history) && history.length > 0) {
          // Only set messages if we don't already have them or if they're different
          const currentMessageCount = getMessageCount();
          if (currentMessageCount === 0 || currentMessageCount !== history.length) {
            setMessages(history);
          }
        } else {
          // Only add welcome message if we don't have any messages
          if (getMessageCount() === 0) {
            const displayName = agentName && agentName !== 'Untitled Agent' ? agentName : '';
            const selectedAgent = useAgentStore.getState().selectedAgent;
            const agentDomain = selectedAgent?.config?.domain || 'Domain';

            // Use the centralized function to show welcome message with typing effect
            showWelcomeMessageWithTypingEffect(displayName, agentDomain);
          }
        }
        setHasLoadedHistory(true);
      } catch (e) {
        console.error('Failed to fetch chat history:', e);
        // Only add welcome message if we don't have any messages
        if (getMessageCount() === 0) {
          // Use the centralized function to show fallback welcome message with typing effect
          showFallbackWelcomeMessageWithTypingEffect();
        }
        setHasLoadedHistory(true);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent_id, agentName, agentStore]);

  // Cleanup effect to handle component unmounting
  useEffect(() => {
    return () => {
      // Clean up any pending operations when component unmounts
      if (loading) {
        setLoading(false);
      }
    };
  }, [loading]);

  // Effect to ensure message persistence across re-renders (but not across agents)
  useEffect(() => {
    // If we have messages but haven't loaded history, don't overwrite them
    // But only if we're still on the same agent
    if (getMessageCount() > 0 && !hasLoadedHistory && agent_id === previousAgentId) {
      setHasLoadedHistory(true);
    }
  }, [getMessageCount, hasLoadedHistory, agent_id, previousAgentId]);

  // Debug effect to track message changes
  useEffect(() => {
    console.log(
      `[Debug] Messages changed: ${getMessageCount()} messages, hasLoadedHistory: ${hasLoadedHistory}, agent_id: ${agent_id}`,
    );
  }, [messages, hasLoadedHistory, agent_id]);

  // Message recovery mechanism
  useEffect(() => {
    // If we had messages but they're suddenly gone, try to recover them
    if (hasLoadedHistory && getMessageCount() === 0 && agent_id && agentStore) {
      console.warn('[Recovery] Messages were lost, attempting to restore from API...');
      const recoverMessages = async () => {
        try {
          const history = await apiService.getSmartChatHistory(agent_id);
          if (Array.isArray(history) && history.length > 0) {
            setMessages(history);
            console.log(`[Recovery] Successfully restored ${history.length} messages`);
          }
        } catch (e) {
          console.error('[Recovery] Failed to restore messages:', e);
        }
      };
      recoverMessages();
    }
  }, [hasLoadedHistory, getMessageCount, agent_id, agentStore]);

  // Manual message clearing function for agent switches
  // const clearMessagesForNewAgent = useCallback(() => {
  //   if (agentStore) {
  //     // Clear any pending welcome message timeout
  //     if (welcomeMessageTimeoutRef.current) {
  //       clearTimeout(welcomeMessageTimeoutRef.current);
  //       welcomeMessageTimeoutRef.current = null;
  //     }

  //     clearMessages();
  //     setHasLoadedHistory(false);
  //     setIsLoadingHistory(false);
  //     setIsTyping(false);
  //     setHasShownWelcomeMessage(false);
  //     console.log(`[Manual Clear] Cleared messages for agent ${agent_id}`);
  //   }
  // }, [agentStore, clearMessages, agent_id]);

  // Cleanup effect for welcome message timeouts
  useEffect(() => {
    return () => {
      // Clear any pending welcome message timeout when component unmounts or dependencies change
      if (welcomeMessageTimeoutRef.current) {
        clearTimeout(welcomeMessageTimeoutRef.current);
        welcomeMessageTimeoutRef.current = null;
      }
    };
  }, [showWelcomeMessageWithTypingEffect, showFallbackWelcomeMessageWithTypingEffect]);

  // Debug utility to check store state
  // const debugStoreState = useCallback(() => {
  //   if (agentStore) {
  //     const state = agentStore.getState();
  //     console.log(`[Debug Store] Agent ${agent_id} store state:`, {
  //       messageCount: state.messages.length,
  //       hasLoadedHistory,
  //       isLoadingHistory,
  //       previousAgentId
  //     });
  //   }
  // }, [agentStore, agent_id, hasLoadedHistory, isLoadingHistory, previousAgentId]);

  const sendMessage = async () => {
    if (!input.trim() || !agent_id || !agentStore) return;

    // Clear previous thinking messages when starting new processing
    setProcessingStatusHistory([]);

    // Add user message
    const userMsg = { sender: 'user' as const, text: input };
    addMessage(userMsg);

    const userInput = input;
    setInput('');
    setLoading(true);

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

      const response = await apiService.smartChat(agent_id, userInput);

      // Remove the thinking message by ID if it exists
      if (thinkingMessageId) {
        removeMessageById(thinkingMessageId);
      }

      // Add the actual response
      addMessage({
        sender: 'agent' as const,
        text: response.follow_up_message || response.agent_response || response.message || '...',
      });

      // Refresh agent data silently if the smart chat updated agent properties
      if (
        response.success &&
        (response.updates_applied?.length > 0 || response.updated_domain_tree)
      ) {
        try {
          // Only refresh agent data for numeric IDs (regular agents)
          // Use silent refresh to avoid showing loading skeleton
          if (!isNaN(Number(agent_id))) {
            const updatedAgent = await apiService.getAgent(parseInt(agent_id));
            // Update the agent store without triggering loading state
            const currentState = useAgentStore.getState();
            useAgentStore.setState({
              ...currentState,
              selectedAgent: updatedAgent,
            });
          }
        } catch (fetchError) {
          console.warn('Failed to refresh agent data:', fetchError);
        }
      }

      // If the response indicates a knowledge status update, trigger centralized store refresh
      if (response.status === 'knowledge_status_update' || response.updated_domain_tree) {
        // Use our centralized knowledge store for domain knowledge updates
        // This will automatically handle debouncing and avoid duplicate calls
        const knowledgeStore = useKnowledgeStore.getState();
        if (agent_id) {
          knowledgeStore.fetchKnowledgeData(agent_id, true); // Force refresh
        }
      }
    } catch (e) {
      console.error('Failed to send message:', e);

      // Remove the thinking message by ID if it exists
      if (thinkingMessageId) {
        removeMessageById(thinkingMessageId);
      }

      addMessage({ sender: 'agent' as const, text: 'Sorry, something went wrong.' });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !isComposing) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleCompositionStart = () => {
    setIsComposing(true);
  };

  const handleCompositionEnd = () => {
    setIsComposing(false);
  };

  // const handleFileUpload = () => {
  //   const fileInput = document.createElement('input');
  //   fileInput.type = 'file';
  //   fileInput.accept = '*/*';
  //   fileInput.onchange = (e) => {
  //     const file = (e.target as HTMLInputElement).files?.[0];
  //     if (file) {
  //       // TODO: Implement file upload functionality
  //       console.log('File selected:', file.name);
  //       // For now, just add a message indicating file upload intent
  //       addMessage({
  //         sender: 'user',
  //         text: `📎 Uploaded: ${file.name}`,
  //       });
  //     }
  //   };
  //   fileInput.click();
  // };

  return (
    <>
      <div className="flex overflow-y-auto flex-col h-full group">
        <div className="flex overflow-y-auto flex-col flex-1 gap-2 px-2 py-2 custom-scrollbar">
          {isLoadingHistory && (
            <div className="flex gap-2 items-center self-start px-3 py-2 text-left">
              <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
              <span className="text-sm text-gray-700">Loading chat history...</span>
            </div>
          )}
          {messages.map((msg, idx) => {
            const isThinking = msg.id && msg.id.startsWith('thinking-');
            const isWelcomeMessage =
              msg.sender === 'agent' &&
              (msg.text.includes("Hi! I'm Dana") ||
                msg.text.includes("Hi! I'm here to help you to train") ||
                msg.text.includes('Welcome! How can I assist you'));

            return (
              <div
                key={idx}
                className={`rounded-sm px-3 py-2 text-sm ${
                  msg.sender === 'user'
                    ? 'border border-gray-100 bg-gray-50'
                    : isThinking
                      ? ' self-start text-left border border-gray-100'
                      : ' self-start text-left bg-white'
                }`}
              >
                {isThinking ? (
                  <div className="flex gap-2 items-center px-3 py-2">
                    <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                    <span className="text-sm text-gray-700">{msg.text}</span>
                  </div>
                ) : (
                  <>
                    <HybridRenderer
                      content={msg.text}
                      backgroundContext={msg.sender === 'user' ? 'user' : 'agent'}
                    />
                    {isWelcomeMessage && (
                      <div className="flex flex-col gap-2 mt-3">
                        <button
                          onClick={handleCTAClick}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white rounded-md border border-gray-300 shadow-sm transition-colors duration-200 cursor-pointer hover:bg-gray-100"
                        >
                          Add knowledge on a topic
                        </button>
                        <button
                          onClick={handleAddDocumentsClick}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white rounded-md border border-gray-300 shadow-sm transition-colors duration-200 cursor-pointer hover:bg-gray-100"
                        >
                          Add documents
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
          {isTyping && (
            <div className="flex gap-2 items-center self-start px-3 py-2 text-left bg-white rounded-sm border border-gray-100">
              <div className="flex gap-1">
                <div
                  className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0ms' }}
                ></div>
                <div
                  className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '150ms' }}
                ></div>
                <div
                  className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '300ms' }}
                ></div>
              </div>
            </div>
          )}
          <ProcessingStatusHistory
            messages={processingStatusHistory}
            isExpanded={isHistoryExpanded}
            onToggle={() => setIsHistoryExpanded(!isHistoryExpanded)}
          />

          <div ref={bottomRef} />
        </div>
        <div className="p-3">
          <div className="relative">
            <textarea
              className="w-full min-h-[100px] max-h-[120px] pl-3 pr-12 py-3 text-sm rounded-lg bg-gray-100 border-gray-300
              focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-transparent resize-none overflow-y-auto"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              onCompositionStart={handleCompositionStart}
              onCompositionEnd={handleCompositionEnd}
              placeholder="Type your message"
              disabled={loading}
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
            {/* <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={handleFileUpload}
                  className="absolute bottom-3 left-3 p-1 text-gray-400"
                  disabled={loading}
                >
                  <div className="flex justify-center items-center p-2 text-gray-700 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-200">
                    <Attachment className="w-4 h-4" />
                  </div>
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Add files</p>
              </TooltipContent>
            </Tooltip> */}
            {input.trim() && (
              <button
                onClick={sendMessage}
                className="absolute right-3 bottom-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:text-blue-600"
                title="Send message"
                disabled={loading}
              >
                <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export const AgentDetailSidebar: React.FC = () => {
  const selectedAgent = useAgentStore((s) => s.selectedAgent);
  const [connectionState, setConnectionState] = useState<string>('disconnected');
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    // Try to get saved width from localStorage
    const savedWidth = localStorage.getItem('agent-detail-sidebar-width');
    if (savedWidth) {
      const width = parseInt(savedWidth, 10);
      return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
    }
    return DEFAULT_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);

  // Save width to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('agent-detail-sidebar-width', sidebarWidth.toString());
  }, [sidebarWidth]);

  const handleResize = useCallback((newWidth: number) => {
    setSidebarWidth(newWidth);
  }, []);

  return (
    <div
      className="relative max-h-[calc(100vh-64px)] border-r border-gray-200 overflow-visible flex flex-col bg-gray-50"
      style={{
        width: `${sidebarWidth}px`,
        minWidth: `${MIN_WIDTH}px`,
        maxWidth: `${MAX_WIDTH}px`,
      }}
    >
      <ResizeHandle onResize={handleResize} isResizing={isResizing} setIsResizing={setIsResizing} />
      <div className="flex overflow-y-auto flex-col h-full bg-white">
        <div className="flex gap-3 items-center p-2 h-14 border-b border-gray-200">
          <img className="w-10 h-10 rounded-full" src={DanaAvatar} alt="Dana avatar" />
          <div className="flex-1">
            <div className="text-sm font-semibold text-gray-900">Dana</div>
            <div className="text-xs text-gray-500">Agent builder assistant</div>
          </div>
          <div className="flex gap-1 items-center">
            <div
              className={`w-2 h-2 rounded-full ${
                connectionState === 'connected'
                  ? 'bg-green-500'
                  : connectionState === 'connecting'
                    ? 'bg-yellow-500'
                    : 'bg-red-500'
              }`}
            />
            <span className="text-xs text-gray-500 capitalize">{connectionState}</span>
          </div>
        </div>
        <div className="flex overflow-y-auto flex-col flex-1">
          <SmartAgentChat
            agentName={selectedAgent?.name}
            onConnectionStateChange={setConnectionState}
          />
        </div>
      </div>
    </div>
  );
};
