// React and React Router
import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import React from 'react';

// Components
import ChatSession from './chat-session';
// import ChatBox from './chat-box';
import { cn } from '@/lib/utils';

import ChatBox, { type ChatBoxRef } from './chat-box';
import { ChevronDown, ChevronUp, X } from 'lucide-react';

// Stores
import { useChatStore } from '@/stores/chat-store';

// Hooks
import { useVariableUpdates } from '@/hooks/useVariableUpdates';

// Components
import LogViewer from '@/components/LogViewer';

interface AgentChatViewProps {
  isSidebarCollapsed: boolean;
  agentId?: string;
  conversationId?: string;
}

const AgentChatView: React.FC<AgentChatViewProps> = ({
  isSidebarCollapsed,
  agentId,
  conversationId,
}) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const [files] = useState<any[]>([]);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [showLogs, setShowLogs] = useState(false);
  const [hideLogs, setHideLogs] = useState(false);

  // Generate unique WebSocket ID for this chat session
  const [websocketId] = useState(
    () => `chatview-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
  );

  // Refs to control ChatBox input state for global functions
  const chatBoxRef = useRef<ChatBoxRef | null>(null);

  const {
    messages,
    isSending,
    error,
    sendMessage,
    fetchConversation,
    setCurrentAgentId,
    clearMessages,
    setError,
    clearError,
    // Session conversation methods for prebuilt agents
    loadSessionConversation,
    createSessionConversation,
  } = useChatStore();

  // WebSocket for variable updates and log streaming
  const { updates, logUpdates, disconnect, clearLogUpdates } = useVariableUpdates(websocketId, {
    maxUpdates: 50,
    autoConnect: true,
  });

  // Set up global functions for HTMLRenderer to use
  useEffect(() => {
    // Function to set input text in the chat box
    const setInputText = (text: string) => {
      if (chatBoxRef.current?.setMessage) {
        chatBoxRef.current.setMessage(text);
      }
    };

    // Function to send the current message
    const sendCurrentMessage = () => {
      if (chatBoxRef.current?.submitMessage) {
        chatBoxRef.current.submitMessage();
      }
    };

    // Function to send a message directly without setting input
    const sendMessageDirect = (messageText: string) => {
      if (chatBoxRef.current?.sendMessageDirect) {
        chatBoxRef.current.sendMessageDirect(messageText);
      }
    };

    // Set up global functions on window object
    (window as any).setInput = setInputText;
    (window as any).setInputText = setInputText;
    (window as any).sendMessage = sendCurrentMessage;
    (window as any).handleSendMessage = sendCurrentMessage;
    (window as any).submitMessage = sendCurrentMessage;
    (window as any).sendMessageDirect = sendMessageDirect;

    // Cleanup function
    return () => {
      delete (window as any).setInput;
      delete (window as any).setInputText;
      delete (window as any).sendMessage;
      delete (window as any).handleSendMessage;
      delete (window as any).submitMessage;
      delete (window as any).sendMessageDirect;
    };
  }, []);

  // Handle variable updates - show step changes for thinking messages
  useEffect(() => {
    if (updates.length > 0) {
      const latestUpdate = updates[updates.length - 1];
      // Update current step for thinking message
      if (latestUpdate.variable === 'step') {
        const stepValue = latestUpdate.newValue || '';

        if (stepValue) {
          try {
            // Parse the stringified object
            const stepObject = JSON.parse(stepValue.replaceAll("'", '"'));
            const action = stepObject.action || stepObject.description || stepObject.name || '';
            setCurrentStep(action);
          } catch (error) {
            // If parsing fails, use the raw value
            setCurrentStep(stepValue);
          }
        }
      }
    }
  }, [updates]);

  // Set current agent ID when component mounts
  useEffect(() => {
    if (agentId) {
      setCurrentAgentId(agentId); // Pass agentId directly (supports both string and number)
    }
  }, [agentId, setCurrentAgentId]);

  // Fetch conversation if conversationId is provided
  useEffect(() => {
    console.log('Chat view: conversationId changed to:', conversationId);
    if (conversationId && agentId) {
      // Check if this is a session conversation (starts with 'session_')
      if (conversationId.startsWith('session_')) {
        console.log('Loading session conversation:', conversationId);
        if (typeof agentId === 'string') {
          loadSessionConversation(conversationId, agentId);
        }
        return;
      }

      // Check if this is a temporary conversation ID (very large number)
      const conversationIdNum = parseInt(conversationId);
      if (isNaN(conversationIdNum) || conversationIdNum > 1000000000) {
        // Invalid or temporary ID (timestamp-based)
        console.log('Invalid or temporary conversation ID detected:', conversationId);
        // Don't fetch, just keep the current messages
        return;
      }

      console.log('Fetching conversation:', conversationId);
      fetchConversation(conversationIdNum);
    } else if (!conversationId && !isSending) {
      // Only clear messages if there's no conversation ID AND we're not currently sending a message
      // This prevents clearing messages when starting a new conversation where a message is being sent
      console.log('Clearing messages - no conversation ID and not sending');
      clearMessages();
    }
  }, [
    conversationId,
    agentId,
    fetchConversation,
    clearMessages,
    loadSessionConversation,
    isSending,
  ]);

  // Debug: Log messages when they change
  useEffect(() => {
    console.log('Chat messages updated:', messages);
    console.log('Messages length:', messages?.length);
  }, [messages]);

  // Clean up WebSocket on component unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  const onSendMessage = async (data: any) => {
    if (!agentId) {
      setError('Agent ID is required');
      return;
    }

    try {
      clearError();
      clearLogUpdates(); // Clear previous logs when starting new request
      setHideLogs(false); // Show logs section when starting new request

      let effectiveConversationId = conversationId;

      // If this is a new conversation, handle differently for prebuilt vs regular agents
      if (!conversationId) {
        if (typeof agentId === 'string') {
          // For prebuilt agents, create a session conversation
          const sessionId = createSessionConversation(agentId);
          effectiveConversationId = sessionId;
          // Navigate AFTER sending message to avoid race condition
        } else {
          // For regular agents, use undefined conversation ID to let backend create one
          effectiveConversationId = undefined;
        }
      }

      const response = await sendMessage(
        data, // Pass the entire data object which includes message and files
        agentId, // Pass agentId directly (supports both string and number)
        effectiveConversationId,
        websocketId,
      );

      const responseConversationId = response.conversation_id;

      const isPrebuiltAgent = isNaN(Number(agentId));

      // Navigate to the conversation URL after getting response
      if (!conversationId) {
        if (isPrebuiltAgent && effectiveConversationId) {
          // For prebuilt agents, navigate to session conversation
          navigate(`/agents/${agentId}/chat/${effectiveConversationId}`);
        } else if (!isPrebuiltAgent && responseConversationId) {
          // For regular agents, navigate to the actual conversation URL
          navigate(`/agents/${agentId}/chat/${responseConversationId}`);
        }
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      // Error is already set in the store
    }
  };

  const renderWelcomeContent = () => {
    const contentClassName = `
      flex flex-col items-center justify-center h-full gap-8
      transition-all duration-300 ease-in-out
      w-full
      opacity-100
    `;

    return (
      <div className="flex relative items-center w-full h-full fade-in">
        <div className={contentClassName}>
          <div className="flex flex-col items-center">
            <span className="text-[36px] font-medium text-gray-400">How can I help you today?</span>
          </div>
          <div className={`flex flex-col gap-2 transition-all duration-300 w-[700px]`}>
            <ChatBox
              files={files}
              isShowUpload={true}
              agentId={agentId}
              placeholder="Ask me anything"
              handleSendMessage={onSendMessage}
              ref={chatBoxRef} // Pass the ref to ChatBox
            />
          </div>
        </div>
      </div>
    );
  };

  // Show error message if there's an error
  if (error) {
    return (
      <div className="flex justify-center items-center w-full h-full">
        <div className="text-center text-red-500">
          <p className="text-lg font-medium">Error</p>
          <p className="text-sm">{error}</p>
          <button
            onClick={clearError}
            className="px-4 py-2 mt-4 text-white bg-blue-500 rounded hover:bg-blue-600"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex w-full h-full">
      <div className="w-full overflow-y-auto custom-scrollbar h-[calc(100vh-64px)] fade-in">
        {conversationId || messages.length > 0 ? (
          <div className="flex justify-center items-center w-full h-full">
            <div className="flex relative justify-center items-center w-full h-full">
              <div
                id="chat-container"
                className={cn('flex flex-col justify-center items-center w-full h-full', 'w-full')}
              >
                <div
                  className={cn(
                    'grid grid-rows-[1fr_max-content_max-content] justify-between w-full h-full',
                    isSidebarCollapsed ? 'pr-6 pl-10' : 'px-4',
                    'max-w-[760px] 3xl:max-w-[1200px]',
                    'opacity-100',
                  )}
                >
                  {/* Message container with fixed height and scroll */}
                  <div
                    ref={chatContainerRef}
                    className="overflow-y-auto items-center pt-2 pb-4 custom-scrollbar fade-in w-full min-w-[760px] 3xl:min-w-[1200px]"
                  >
                    <ChatSession
                      messages={messages}
                      isBotThinking={isSending}
                      currentStep={currentStep}
                    />
                  </div>

                  {/* Collapsible Live Logs Section */}
                  {(isSending || logUpdates.length > 0) && !hideLogs && (
                    <div className="border-t pb-6 border-gray-200 dark:border-gray-700 w-full max-w-[760px] 3xl:max-w-[1200px]">
                      {/* Toggle Button */}
                      <div className="flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                        <div
                          className="flex items-center gap-2 cursor-pointer flex-1"
                          onClick={() => setShowLogs(!showLogs)}
                        >
                          <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                            Backend Logs
                          </span>
                          {isSending && (
                            <div className="flex items-center gap-1">
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                              <span className="text-xs text-blue-600 dark:text-blue-400">Live</span>
                            </div>
                          )}
                          {logUpdates.length > 0 && (
                            <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-0.5 rounded-full font-medium">
                              {logUpdates.length}
                            </span>
                          )}
                          {showLogs ? (
                            <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                          ) : (
                            <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
                          )}
                        </div>

                        {/* Close button */}
                        {!isSending && (
                          <button
                            onClick={() => {
                              setHideLogs(true);
                              setShowLogs(false);
                            }}
                            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                            title="Hide logs"
                          >
                            <X className="w-3 h-3 text-gray-400 dark:text-gray-500" />
                          </button>
                        )}
                      </div>

                      {/* Logs Content - Only show when expanded */}
                      {showLogs && (
                        <div className="px-4 pb-4">
                          <LogViewer
                            logs={logUpdates}
                            showTimestamps={true}
                            autoScroll={true}
                            maxHeight="200px"
                          />
                        </div>
                      )}
                    </div>
                  )}

                  {/* Fixed chat box at bottom */}
                  <div className="sticky bottom-6 w-full bg-background">
                    <ChatBox
                      files={files}
                      isShowUpload={true}
                      agentId={agentId}
                      placeholder="Ask me anything"
                      handleSendMessage={onSendMessage}
                      ref={chatBoxRef} // Pass the ref to ChatBox
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className={cn('flex relative items-center w-full h-full fade-in')}>
            {renderWelcomeContent()}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentChatView;
