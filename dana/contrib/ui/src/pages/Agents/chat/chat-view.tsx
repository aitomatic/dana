// React and React Router
import { useRef, useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import React from 'react';

// Components
import ChatSession from './chat-session';
// import ChatBox from './chat-box';
import { cn } from '@/lib/utils';

import ChatBox from './chat-box';

// Stores
import { useChatStore } from '@/stores/chat-store';

// Hooks
import { useVariableUpdates } from '@/hooks/useVariableUpdates';

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

  // Generate unique WebSocket ID for this chat session
  const [websocketId] = useState(() => `chatview-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

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
  } = useChatStore();

  // WebSocket for variable updates
  const { updates } = useVariableUpdates(websocketId, {
    maxUpdates: 50,
    autoConnect: true,
  });

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
      setCurrentAgentId(parseInt(agentId));
    }
  }, [agentId, setCurrentAgentId]);

  // Fetch conversation if conversationId is provided
  useEffect(() => {
    console.log('Chat view: conversationId changed to:', conversationId);
    if (conversationId) {
      // Check if this is a temporary conversation ID (very large number)
      const conversationIdNum = parseInt(conversationId);
      if (conversationIdNum > 1000000000) {
        // Temporary ID (timestamp-based)
        console.log('Temporary conversation ID detected, not fetching from API');
        // Don't fetch, just keep the current messages
        return;
      }

      console.log('Fetching conversation:', conversationId);
      fetchConversation(conversationIdNum);
    } else {
      console.log('Clearing messages - no conversation ID');
      clearMessages();
    }
  }, [conversationId, fetchConversation, clearMessages]);

  // Debug: Log messages when they change
  useEffect(() => {
    console.log('Chat messages updated:', messages);
    console.log('Messages length:', messages?.length);
  }, [messages]);

  const onSendMessage = async (data: any) => {
    if (!agentId) {
      setError('Agent ID is required');
      return;
    }

    try {
      clearError();

      // If this is a new conversation, create a temporary conversation ID and navigate immediately
      if (!conversationId) {
        const tempConversationId = Date.now();
        navigate(`/agents/${agentId}/chat/${tempConversationId}`);
      }

      const response = await sendMessage(
        data.message,
        parseInt(agentId),
        conversationId ? parseInt(conversationId) : undefined,
        websocketId
      );

      // If this was a new conversation, navigate to the actual conversation URL
      if (!conversationId && response.conversation_id) {
        navigate(`/agents/${agentId}/chat/${response.conversation_id}`);
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
            <span className="text-[36px] font-medium text-gray-400">
              How can I help you today?
            </span>
          </div>
          <div className={`flex flex-col gap-2 transition-all duration-300 w-[700px]`}>
            <ChatBox
              files={files}
              isShowUpload={false}
              placeholder="Ask me anything"
              handleSendMessage={onSendMessage}
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
      <div className="w-full overflow-y-auto scrollbar-hide h-[calc(100vh-64px)] fade-in">
        {conversationId || messages.length > 0 ? (
          <div className="flex justify-center items-center w-full h-full">
            <div className="flex relative justify-center items-center w-full h-full">
              <div
                id="chat-container"
                className={cn('flex flex-col justify-center items-center w-full h-full', 'w-full')}
              >
                <div
                  className={cn(
                    'flex relative flex-col justify-between w-full h-full',
                    isSidebarCollapsed ? 'pr-6 pl-10' : 'px-4',
                    'max-w-[760px] 3xl:max-w-[1200px]',
                    'opacity-100',
                  )}
                >
                  {/* Message container with fixed height and scroll */}
                  <div
                    ref={chatContainerRef}
                    className="overflow-y-auto items-center pt-2 pb-4 scrollbar-hide fade-in"
                  >
                    <ChatSession messages={messages} isBotThinking={isSending} currentStep={currentStep} />
                  </div>

                  {/* Fixed chat box at bottom */}
                  <div className="sticky bottom-6 w-full bg-background">
                    <ChatBox
                      files={files}
                      isShowUpload={false}
                      placeholder="Ask me anything"
                      handleSendMessage={onSendMessage}
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
