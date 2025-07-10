// React and React Router
import { useRef, useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import React from 'react';

// Components
import ChatSession from './chat-session';
// import ChatBox from './chat-box';
import { cn } from '@/lib/utils';

import ChatBox from './chat-box';

// Stores
import { useChatStore } from '@/stores/chat-store';

interface AgentChatViewProps {
  isSidebarCollapsed: boolean;
  agentId?: string;
  conversationId?: string;
}

const AgentChatView: React.FC<AgentChatViewProps> = ({ isSidebarCollapsed, agentId, conversationId }) => {
  const chatContainerRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { chat_id } = useParams();
  const [files] = useState<any[]>([]);

  const {
    messages,
    isLoading,
    isSending,
    error,
    sendMessage,
    fetchConversation,
    setCurrentAgentId,
    clearMessages,
    setError,
    clearError,
  } = useChatStore();

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
      console.log('Fetching conversation:', conversationId);
      fetchConversation(parseInt(conversationId));
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
      const response = await sendMessage(data.message, parseInt(agentId), conversationId ? parseInt(conversationId) : undefined);

      // If this is a new conversation, navigate to the conversation URL
      if (!conversationId && response.conversation_id) {
        navigate(`/${agentId}/chat/${response.conversation_id}`);
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
      <div className="relative flex items-center w-full h-full fade-in">
        <div className={contentClassName}>
          <div className="flex flex-col items-center">
            <span className="text-[36px] font-medium text-gray-400">
              Hi, how can I help you today?
            </span>
            <span className="text-[36px] font-medium text-gray-700">How can I help you today?</span>
          </div>
          <div className={`flex flex-col gap-2 w-[700px] transition-all duration-300`}>
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
      <div className="flex items-center justify-center w-full h-full">
        <div className="text-red-500 text-center">
          <p className="text-lg font-medium">Error</p>
          <p className="text-sm">{error}</p>
          <button
            onClick={clearError}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
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
        {chat_id ? (
          <div className="flex items-center justify-center w-full h-full">
            <div className="relative flex items-center justify-center w-full h-full">
              <div
                id="chat-container"
                className={cn('flex flex-col items-center justify-center w-full h-full', 'w-full')}
              >
                <div
                  className={cn(
                    'relative flex flex-col justify-between h-full w-full',
                    isSidebarCollapsed ? 'pl-10 pr-6' : 'px-4',
                    'max-w-[760px] 3xl:max-w-[1200px]',
                    'opacity-100',
                  )}
                >
                  {/* Message container with fixed height and scroll */}
                  <div
                    ref={chatContainerRef}
                    className="items-center pt-2 pb-4 overflow-y-auto scrollbar-hide fade-in"
                  >
                    <ChatSession messages={messages} isBotThinking={isSending} />
                  </div>

                  {/* Fixed chat box at bottom */}
                  <div className="sticky w-full bg-background bottom-6">
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
          <div className={cn('relative flex items-center w-full h-full fade-in')}>
            {renderWelcomeContent()}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentChatView;
