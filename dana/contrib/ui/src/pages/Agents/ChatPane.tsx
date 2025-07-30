import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp } from 'iconoir-react';
import { SidebarExpand } from 'iconoir-react';
import { useParams } from 'react-router-dom';
import { apiService } from '@/lib/api';
import { MarkdownViewerSmall } from './chat/markdown-viewer';
import { useVariableUpdates } from '@/hooks/useVariableUpdates';
import { getAgentAvatarSync } from '@/utils/avatar';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
}

interface ChatPaneProps {
  agentName?: string;
  onClose: () => void;
  isVisible: boolean;
}

export const ChatPane: React.FC<ChatPaneProps> = ({ agentName = 'Agent', onClose, isVisible }) => {
  const { agent_id } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate unique WebSocket ID for this chat session
  const [websocketId] = useState(
    () => `chatpane-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
  );

  // WebSocket for variable updates (console logging only)
  const { updates, disconnect } = useVariableUpdates(websocketId, {
    maxUpdates: 50,
    autoConnect: true,
  });

  // Handle variable updates - show step changes as thinking messages
  useEffect(() => {
    if (updates.length > 0) {
      const latestUpdate = updates[updates.length - 1];
      // Update current step for thinking message
      if (latestUpdate.variable === 'step') {
        // Try both property names to be safe
        const stepValue = latestUpdate.newValue || '';

        if (stepValue) {
          try {
            // Parse the stringified object
            console.log('==============================================');
            console.log('stepValue', stepValue);
            const stepObject = JSON.parse(stepValue.replaceAll("'", '"'));
            console.log('stepObject', stepObject);
            const action = stepObject.action || stepObject.description || stepObject.name || '';
            console.log('==============================================');
            setCurrentStep(action);
          } catch (error) {
            // If parsing fails, use the raw value
            console.log(`📝 Failed to parse step object, using raw value: "${stepValue}"`);
            setCurrentStep(stepValue);
          }
        }
      }
    }
  }, [updates]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history when component mounts or agent_id changes
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!agent_id || !isVisible) return;

      setIsLoadingHistory(true);
      try {
        // Try to load chat history (test_chat + smart_chat)
        const chatHistory = await apiService.getTestChatHistory(agent_id);

        if (chatHistory && chatHistory.length > 0) {
          // Convert API response to Message format and sort by timestamp
          const historyMessages: Message[] = chatHistory
            .map((chat: any, index: number) => ({
              id: `history-${index}`,
              text: chat.text,
              sender: chat.sender as 'user' | 'agent',
              timestamp: new Date(chat.created_at),
            }))
            .sort((a: any, b: any) => a.timestamp.getTime() - b.timestamp.getTime());

          setMessages(historyMessages);
        } else {
          // No history found, show welcome message
          setMessages([]);
          setMessages([
            {
              id: 'welcome',
              text: `Hello! I'm ${agentName}. How can I help you today?`,
              sender: 'agent',
              timestamp: new Date(),
            },
          ]);
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
        // On error, show welcome message
        setMessages([
          {
            id: 'welcome',
            text: `Hello! I'm ${agentName}. How can I help you today?`,
            sender: 'agent',
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadChatHistory();
  }, [agent_id, agentName, isVisible]);

  // Clean up WebSocket when component becomes invisible or unmounts
  useEffect(() => {
    if (!isVisible) {
      disconnect();
    }
    // Clean up on unmount
    return () => {
      disconnect();
    };
  }, [isVisible, disconnect]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading || !agent_id) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setCurrentStep(''); // Reset current step when starting new request

    try {
      // Call the new agent test API using apiService with WebSocket ID
      const data = await apiService.testAgentById(
        agent_id,
        userMessage.text,
        { user_id: 'chat_pane_user', session_id: `chatpane_${Date.now()}` },
        websocketId,
      );

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.success
          ? data.agent_response
          : `Error: ${data.error || 'Unknown error occurred'}`,
        sender: 'agent',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error: any) {
      console.error('Error testing agent:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error while processing your message: ${error.message || 'Please try again.'}`,
        sender: 'agent',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setCurrentStep(''); // Clear step when done
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div
      className={`w-[420px] min-w-[380px] bg-white max-h-[calc(100vh-64px)] rounded-lg shadow-md overflow-y-auto flex flex-col m-2  transform transition-transform duration-300 ease-in-out z-50 ${
        isVisible ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <div className="flex gap-3 items-center">
          <div className="flex overflow-hidden justify-center items-center w-8 h-8 rounded-full">
            <img
              src={getAgentAvatarSync(agent_id || '0')}
              alt={`${agentName} avatar`}
              className="object-cover w-full h-full"
              onError={(e) => {
                // Fallback to colored circle if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  parent.innerHTML = `<div class="flex justify-center items-center w-full h-full text-sm font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400">${agentName?.[0] || 'A'}</div>`;
                }
              }}
            />
          </div>
          <h3 className="font-semibold text-gray-900">{agentName}</h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 transition-colors cursor-pointer hover:text-gray-600"
        >
          <SidebarExpand width={20} height={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex overflow-y-auto flex-col flex-1 p-4 space-y-4">
        {isLoadingHistory ? (
          <div className="flex justify-center items-center h-full">
            <div className="grid grid-cols-[max-content_1fr] gap-2 items-center">
              <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
              <div className="text-sm text-gray-700">
                <span className="font-medium">Loading chat history...</span>
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-white text-gray-900 border border-gray-200'
                      : 'bg-gray-100 text-gray-900'
                  }`}
                >
                  <MarkdownViewerSmall>{message.text ?? 'Empty message'}</MarkdownViewerSmall>
                  <p className="mt-1 text-xs opacity-70">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="grid grid-cols-[max-content_1fr] gap-2 items-center">
                  <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                  <div className="text-sm text-gray-700">
                    <span className="font-medium">Thinking...</span>
                    {currentStep && (
                      <div className="mt-1 text-xs italic text-blue-600">{currentStep}</div>
                    )}
                  </div>
                </div>
              </div>
            )}
          </>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4">
        <div className="flex relative">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message"
            className="w-full min-h-[100px] max-h-[120px] pl-3 pr-12 py-3 text-sm rounded-lg bg-gray-100 border-gray-300
              focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-transparent resize-none overflow-y-auto"
            rows={2}
            disabled={isLoading}
          />
          {inputText.trim() && (
            <button
              onClick={handleSendMessage}
              className="absolute bottom-3 right-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:text-blue-600"
              title="Send message"
              disabled={isLoading}
            >
              <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
