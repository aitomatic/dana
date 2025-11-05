import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import { apiService } from '@/lib/api';
import { createSmartChatStore } from '@/stores/smart-chat-store';
import { useKnowledgePackStore } from '@/stores';
import { ArrowUp, Expand, Collapse, LightBulb, Check, SystemRestart } from 'iconoir-react';
import { HybridRenderer } from '@/pages/Agents/chat/hybrid-renderer';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

// Removed animated placeholder styles - no longer needed

// Simple placeholder component - no animation needed
const SimplePlaceholder: React.FC<{
  isDisabled?: boolean;
}> = ({ isDisabled }) => {
  // If disabled, show disabled message
  if (isDisabled) {
    return <span className="text-gray-400">Chat disabled - knowledge generation in progress or completed</span>;
  }

  // Simple static placeholder
  return <span>Type your message</span>;
};

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

const SmartAgentChat: React.FC<{
  knowledgePackId: string;
}> = ({ knowledgePackId }) => {
  console.log('🚀 SmartAgentChat component mounted with knowledgePackId:', knowledgePackId);
  
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const [hasClickedGenerate, setHasClickedGenerate] = useState(false);

  // Get knowledge generation status and created knowledge pack from store
  const { 
    isGeneratingKnowledge, 
    createdKnowledgePack, 
    knowledgeStatus,
    setIsGeneratingKnowledge 
  } = useKnowledgePackStore();
  
  console.log('📦 SmartAgentChat - createdKnowledgePack:', {
    id: createdKnowledgePack?.id,
    hasOriginalDescription: !!createdKnowledgePack?.originalDescription,
    originalDescription: createdKnowledgePack?.originalDescription?.substring(0, 100) + '...',
    isGeneratingKnowledge
  });

  // Create knowledge pack specific chat store - since knowledgePackId is required, we can call this unconditionally
  const useKPChatStore = useMemo(() => {
    return createSmartChatStore(knowledgePackId);
  }, [knowledgePackId]);

  // Call the store hook unconditionally at top level
  const messages = useKPChatStore((s) => s.messages);
  const addMessage = useKPChatStore((s) => s.addMessage);
  const removeMessageById = useKPChatStore((s) => s.removeMessageById);
  const setMessages = useKPChatStore((s) => s.setMessages);
  const setMessageButtonsActive = useKPChatStore((s) => s.setMessageButtonsActive);
  const deactivateAllButtons = useKPChatStore((s) => s.deactivateAllButtons);

  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [processingStatusHistory, setProcessingStatusHistory] = useState<ProcessingStatusMessage[]>(
    [],
  );
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const [hasLoadedConversation, setHasLoadedConversation] = useState(false);
  const hasAttemptedAutoMessageRef = useRef(false);

  // Check if generation has been started (either by clicking button or from elsewhere)
  const hasGenerationStarted = useMemo(() => {
    // Check if user clicked button in this session
    if (hasClickedGenerate) return true;
    
    // Check if generation is currently running
    if (isGeneratingKnowledge) return true;
    
    // Check if there's a generation task ID (means generation was started)
    if (createdKnowledgePack?.generation_task_id) return true;
    
    // Check if any node is in completed state (means Generate Knowledge was clicked)
    // Don't check for in_progress or generating - those are part of question generation
    if (knowledgeStatus?.topics && knowledgeStatus.topics.length > 0) {
      const hasCompletedOrBeyond = knowledgeStatus.topics.some((topic: any) => 
        topic.status === 'completed' || 
        topic.status === 'success'
      );
      if (hasCompletedOrBeyond) return true;
    }
    
    return false;
  }, [hasClickedGenerate, isGeneratingKnowledge, createdKnowledgePack?.generation_task_id, knowledgeStatus]);

  // Check if Generate Knowledge button should be shown
  const shouldShowGenerateButton = useMemo(() => {
    // Don't show if generation already started
    if (hasGenerationStarted) return false;
    
    if (!knowledgeStatus?.topics || knowledgeStatus.topics.length === 0) {
      return false;
    }
    
    // Check if ALL nodes are either 'question_generated' or 'failed'
    return knowledgeStatus.topics.every((topic: any) => 
      topic.status === 'question_generated' || topic.status === 'failed'
    );
  }, [knowledgeStatus, hasGenerationStarted]);

  // Check if generation is complete
  const isGenerationComplete = useMemo(() => {
    if (!knowledgeStatus?.topics || knowledgeStatus.topics.length === 0) {
      return false;
    }
    
    // Check if ALL nodes are either 'completed' or 'failed'
    return knowledgeStatus.topics.every((topic: any) => 
      topic.status === 'completed' || topic.status === 'success' || topic.status === 'failed'
    );
  }, [knowledgeStatus]);

  // Check if knowledge content generation is in progress
  // This is when we have a MIX of question_generated and completed/failed
  const isKnowledgeGenerating = useMemo(() => {
    if (!knowledgeStatus?.topics || knowledgeStatus.topics.length === 0) {
      return false;
    }
    
    const hasQuestionGenerated = knowledgeStatus.topics.some((topic: any) => 
      topic.status === 'question_generated'
    );
    const hasCompleted = knowledgeStatus.topics.some((topic: any) => 
      topic.status === 'completed' || topic.status === 'success' || topic.status === 'failed'
    );
    
    // Only true if we have BOTH question_generated AND completed/failed nodes (mixed state)
    return hasQuestionGenerated && hasCompleted;
  }, [knowledgeStatus]);

  // Load conversation history from API on mount
  useEffect(() => {
    console.log('🔄 Conversation loading useEffect triggered');
    
    const loadConversationHistory = async () => {
      if (!knowledgePackId || hasLoadedConversation) return;

      console.log('🔄 Loading conversation history for knowledge pack:', knowledgePackId);

      try {
        const conversation = await apiService.getKnowledgePackConversation(
          parseInt(knowledgePackId),
        );

        if (conversation && conversation.messages && conversation.messages.length > 0) {
          console.log('✅ Loaded existing conversation with', conversation.messages.length, 'messages');
          // Convert API messages to SmartChatMessage format
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          const convertedMessages = conversation.messages.map((msg: any) => ({
            sender: msg.sender === 'user' ? 'user' : 'agent',
            text: msg.content,
            timestamp: new Date(msg.created_at).getTime(),
            id: `msg-${msg.id}`,
            hasActiveButtons: false,
          }));

          setMessages(convertedMessages);
        } else {
          console.log('ℹ️ No existing conversation found - new knowledge pack');
        }
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
      } catch (error: any) {
        // If 404, it means no conversation exists yet - this is normal for new knowledge packs
        if (error?.response?.status === 404) {
          console.log('ℹ️ No conversation exists yet (404) - new knowledge pack');
        } else {
          console.error('❌ Failed to load conversation history:', error);
        }
      } finally {
        // ✅ Set state AFTER API call completes (success or failure)
        setHasLoadedConversation(true);
        console.log('✅ Conversation loading completed, hasLoadedConversation set to true');
      }
    };

    loadConversationHistory();
  }, [knowledgePackId, setMessages, hasLoadedConversation]);


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

  const sendMessage = useCallback(
    async (messageText?: string) => {
      const textToSend = messageText || input.trim();
      if (!textToSend || !knowledgePackId) return;

      // Clear previous thinking messages when starting new processing
      setProcessingStatusHistory([]);

      // Deactivate all previous message buttons when user sends a new message
      deactivateAllButtons();

      // Add user message
      const userMsg = { sender: 'user' as const, text: textToSend };
      addMessage(userMsg);

      const userInput = textToSend;

      // Only clear input if we're using the input field (no messageText provided)
      if (!messageText) {
        setInput('');
      }
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

        // Automatically expand the thinking component when thinking process begins
        setIsHistoryExpanded(true);

        // Use Knowledge Pack chat endpoint
        const response = await apiService.chatWithKnowledgePack(
          parseInt(knowledgePackId),
          userInput,
        );

        // Remove the thinking message by ID if it exists
        if (thinkingMessageId) {
          removeMessageById(thinkingMessageId);
        }

        // Add the actual response
        const agentResponse = {
          sender: 'agent' as const,
          text: response.agent_response || '...',
        };
        addMessage(agentResponse);

        // Check if the response contains buttons and activate them
        const responseText = agentResponse.text;
        const hasButtons =
          responseText.includes('<button') ||
          responseText.includes('option-button') ||
          responseText.includes('options-container');

        if (hasButtons) {
          // Find the message we just added and activate its buttons
          const allMessages = useKPChatStore?.getState().messages || [];
          const latestMessage = allMessages[allMessages.length - 1];
          if (latestMessage && latestMessage.id) {
            setMessageButtonsActive(latestMessage.id);
          }
        }

        // Collapse the thinking component after response is generated
        setIsHistoryExpanded(false);

        // Handle Knowledge Pack tree updates
        if (response.is_tree_modified) {
          console.log('[KnowledgePack] Knowledge tree updated, refreshing view');
          // Refresh the knowledge tree data to show new nodes
          if (window.refreshKnowledgePackTree) {
            console.log('[KnowledgePack] Calling refreshKnowledgePackTree');
            window.refreshKnowledgePackTree();
          } else {
            console.warn('[KnowledgePack] refreshKnowledgePackTree function not available');
          }
        }
      } catch (e) {
        console.error('Failed to send message:', e);

        // Remove the thinking message by ID if it exists
        if (thinkingMessageId) {
          removeMessageById(thinkingMessageId);
        }

        addMessage({ sender: 'agent' as const, text: 'Sorry, something went wrong.' });

        // Collapse the thinking component even on error
        setIsHistoryExpanded(false);
      } finally {
        setLoading(false);
      }
    },
    [
      input,
      knowledgePackId,
      addMessage,
      removeMessageById,
      setMessageButtonsActive,
      deactivateAllButtons,
      useKPChatStore,
    ],
  );

  // Handle Generate Knowledge button click
  const handleGenerateKnowledge = async () => {
    if (!knowledgePackId) return;

    setHasClickedGenerate(true);
    
    try {
      const kpId = typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : parseInt(knowledgePackId);
      
      const response = await apiService.generateKnowledgePackKnowledge(kpId);
      
      if (response.success) {
        toast.success(
          'Knowledge generation started! This process runs in the background.',
          { duration: 6000 }
        );
        
        // Set flag in store to disable chat
        setIsGeneratingKnowledge(true);
      } else {
        toast.error(response.message || 'Failed to start knowledge generation');
      }
    } catch (error: any) {
      console.error('Error generating knowledge:', error);
      toast.error(error?.message || 'Failed to start knowledge generation');
    }
  };

  // Auto-first message system - sends user's original description as first message
  useEffect(() => {
    // console.log('🔄 Auto-first message useEffect triggered');
    
    const sendAutoFirstMessage = async () => {
      console.log('🔍 Auto-first message check:', {
        messagesLength: messages.length,
        hasAttemptedAutoMessage: hasAttemptedAutoMessageRef.current,
        hasLoadedConversation: hasLoadedConversation,
        originalDescription: createdKnowledgePack?.originalDescription,
        knowledgePackId
      });
      
      // Prevent duplicate attempts
      if (hasAttemptedAutoMessageRef.current) {
        console.log('❌ Auto-first message already attempted');
        return;
      }
      
      // CRITICAL: Wait for conversation history to load first
      // This prevents sending the auto-message on page refresh when messages exist
      if (!hasLoadedConversation) {
        console.log('❌ Auto-first message blocked: conversation history not loaded yet');
        return;
      }
      
      // Check all conditions
      if (messages.length > 0) {
        console.log('❌ Auto-first message blocked: messages already exist');
        return;
      }
      
      const originalDescription = createdKnowledgePack?.originalDescription;
      if (!originalDescription?.trim()) {
        console.log('❌ Auto-first message blocked: no original description');
        return;
      }
      
      if (originalDescription.trim().length < 10) {
        console.log('❌ Auto-first message blocked: description too short');
        return;
      }
      
      // All checks passed - mark as attempted
      hasAttemptedAutoMessageRef.current = true;
      
      // Handle very long descriptions (truncate if needed)
      const maxLength = 500;
      const truncatedDescription = originalDescription.length > maxLength 
        ? originalDescription.substring(0, maxLength) + "..."
        : originalDescription;
      
      // Format the auto message
      const autoMessage = `Add knowledge about: ${truncatedDescription.trim()}`;
      
      console.log('✅ Sending auto-first message:', autoMessage);
      
      // Add small delay for better UX
      setTimeout(async () => {
        try {
          await sendMessage(autoMessage);
          console.log('✅ Auto-first message sent successfully');
        } catch (error) {
          console.error('❌ Failed to send auto-first message:', error);
          // Graceful fallback - don't break the chat experience
        }
      }, 1000); // 1 second delay
    };

    // Trigger when we have the required data AND conversation has loaded
    if (createdKnowledgePack?.originalDescription && hasLoadedConversation) {
      sendAutoFirstMessage();
    }
  }, [createdKnowledgePack?.originalDescription, messages.length, sendMessage, hasLoadedConversation]);

  // Set up global functions for HTMLRenderer option buttons to use
  useEffect(() => {
    // Function to send a message directly
    const sendMessageDirect = (messageText: string) => {
      sendMessage(messageText);
    };

    // Function to set input text
    const setInputText = (text: string) => {
      setInput(text);
    };

    // Set up global functions on window object
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).sendMessageDirect = sendMessageDirect;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).setInput = setInputText;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).setInputText = setInputText;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    (window as any).sendMessage = () => sendMessage();

    // Cleanup function
    return () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).sendMessageDirect;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).setInput;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).setInputText;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).sendMessage;
    };
  }, [sendMessage]);

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

  return (
    <div className="flex overflow-y-auto flex-col h-full group">
      {/* Knowledge Generation Banner */}
      {isGeneratingKnowledge && (
        <div className="flex gap-2 items-center px-3 py-2 bg-cyan-50 border-b border-cyan-200">
          <span className="text-sm text-cyan-700">
            Knowledge generation in progress... Chat is temporarily disabled.
          </span>
        </div>
      )}

      {/* Generate Knowledge Button Section */}
      {!hasClickedGenerate && shouldShowGenerateButton && (
        <div className="px-3 py-4 bg-blue-50 border-b border-blue-200">
          <div className="flex flex-col gap-3">
            <div className="text-sm text-gray-700">
              All questions have been generated! Ready to generate knowledge?
            </div>
            <Button
              onClick={handleGenerateKnowledge}
              variant="default"
              size="sm"
              className="gap-2 w-full"
            >
              <LightBulb className="w-4 h-4" />
              <span>Generate Knowledge</span>
            </Button>
          </div>
        </div>
      )}

      {/* Knowledge Generation Status - Only show when content is being generated */}
      {isKnowledgeGenerating && (
        <div className="px-3 py-4 bg-blue-50 border-b border-blue-200">
          <div className="flex flex-col gap-3">
            <div className="flex gap-2 items-center text-blue-700">
              <SystemRestart className="w-5 h-5 animate-spin" />
              <span className="text-sm font-medium">Knowledge Generation in Progress</span>
            </div>
            <div className="text-sm text-gray-600">
              The knowledge generation process is currently running. Please wait...
            </div>
          </div>
        </div>
      )}

      <div className="flex overflow-y-auto flex-col flex-1 gap-2 px-2 py-2 custom-scrollbar">
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
        <ProcessingStatusHistory
          messages={processingStatusHistory}
          isExpanded={isHistoryExpanded}
          onToggle={() => setIsHistoryExpanded(!isHistoryExpanded)}
        />

        <div ref={bottomRef} />
      </div>
      <div className="p-3">
        {/* Show completion message in place of chat input when generation is complete */}
        {isGenerationComplete ? (
          <div className="px-4 py-6 bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg border-2 border-green-200">
            <div className="flex flex-col gap-4">
              <div className="flex gap-3 items-center text-green-700">
                <div className="flex justify-center items-center w-10 h-10 bg-green-100 rounded-full">
                  <Check className="w-6 h-6" />
                </div>
                <span className="text-lg font-semibold">Knowledge Generation Complete!</span>
              </div>
              <div className="text-sm text-gray-700 leading-relaxed">
                The knowledge generation process is completed. Please proceed to:
              </div>
              <div className="flex flex-col gap-3 pl-4">
                <div className="flex items-center gap-3 text-base text-blue-600 font-medium">
                  <span className="text-xl">→</span>
                  <span>Capture Templates tab</span>
                </div>
              </div>
              <div className="pt-2 mt-2 text-xs text-gray-500 border-t border-green-200">
                There's nothing more to do in this chat.
              </div>
            </div>
          </div>
        ) : (
          <div className="relative">
            {/* Simple placeholder overlay */}
            {!input && (
              <div className="absolute top-3 left-3 z-10 text-sm text-gray-500 pointer-events-none">
                <SimplePlaceholder
                  isDisabled={loading || isGeneratingKnowledge || hasGenerationStarted}
                />
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
                // Focus handler - no special logic needed
              }}
              onBlur={() => {
                // Blur handler - no special logic needed
              }}
              disabled={loading || isGeneratingKnowledge || hasGenerationStarted}
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
              title={
                isGeneratingKnowledge || hasGenerationStarted
                  ? 'Chat is disabled while knowledge generation is in progress or completed'
                  : ''
              }
            />
            {input.trim() && (
              <button
                onClick={() => sendMessage()}
                className="absolute right-3 bottom-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:text-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
                title={
                  isGeneratingKnowledge || hasGenerationStarted
                    ? 'Chat is disabled while knowledge generation is in progress or completed'
                    : 'Send message'
                }
                disabled={loading || isGeneratingKnowledge || hasGenerationStarted}
              >
                <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

// Export for Knowledge Pack use
export const KnowledgePackChatSidebar: React.FC<{ knowledgePackId?: string }> = ({
  knowledgePackId,
}) => {
  console.log('🎯 KnowledgePackChatSidebar mounted with knowledgePackId:', knowledgePackId);
  
  const [sidebarWidth, setSidebarWidth] = useState(DEFAULT_WIDTH);
  const [isResizing, setIsResizing] = useState(false);

  const handleResize = useCallback((newWidth: number) => {
    setSidebarWidth(newWidth);
  }, []);

  if (!knowledgePackId) {
    console.log('❌ KnowledgePackChatSidebar: No knowledgePackId provided, returning null');
    return null;
  }

  return (
    <div
      className="flex overflow-visible relative flex-col h-full bg-gray-50 border-r border-gray-200"
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
            <div className="text-xs text-gray-500">Building Knowledge Pack</div>
          </div>
        </div>
        <div className="flex overflow-y-auto flex-col flex-1">
          <SmartAgentChat knowledgePackId={knowledgePackId} />
        </div>
      </div>
    </div>
  );
};
