import React, { useState, useRef, useEffect } from 'react';
import { Send, X } from 'lucide-react';
import { SidebarExpand } from 'iconoir-react';
import { useParams } from 'react-router-dom';
import { apiService } from '@/lib/api';
import { MarkdownViewerSmall } from './chat/markdown-viewer';
import { useVariableUpdates } from '@/hooks/useVariableUpdates';

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
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: `Hello! I'm ${agentName}. How can I help you today?`,
      sender: 'agent',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Generate unique WebSocket ID for this chat session
  const [websocketId] = useState(() => `chatpane-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`);

  // WebSocket for variable updates (console logging only)
  const { updates } = useVariableUpdates(websocketId, {
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
        websocketId
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
      className={` bg-white w-[420px] min-w-[380px] max-h-[calc(100vh-64px)] rounded-lg shadow-md overflow-y-auto flex flex-col m-2 bg-gray-50 transform transition-transform duration-300 ease-in-out z-50 ${isVisible ? 'translate-x-0' : 'translate-x-full'
        }`}
    >
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Chat with {agentName}</h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 transition-colors hover:text-gray-600 cursor-pointer"
        >
         <SidebarExpand width={20} height={20} />
        </button>
      </div>

      {/* Messages */}
      <div className="flex overflow-y-auto flex-col flex-1 p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${message.sender === 'user'
                ? 'bg-white text-gray-900 shadow-lg'
                : 'bg-gray-100 text-gray-900'
                }`}
            >
              <MarkdownViewerSmall>{message.text ?? 'Empty message'}</MarkdownViewerSmall>
              <p className="mt-1 text-xs opacity-70">{message.timestamp.toLocaleTimeString()}</p>
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="px-4 py-2 bg-blue-50 border-l-4 border-blue-400 rounded-lg">
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"></div>
                  <div
                    className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.1s' }}
                  ></div>
                  <div
                    className="w-2 h-2 bg-blue-400 rounded-full animate-bounce"
                    style={{ animationDelay: '0.2s' }}
                  ></div>
                </div>
                <div className="text-sm text-blue-700">
                  <span className="font-medium">Thinking...</span>
                  {currentStep && (
                    <div className="text-xs text-blue-600 mt-1 italic">
                      {currentStep}
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex space-x-2">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Type your message..."
            className="flex-1 p-2 text-sm rounded-lg border border-gray-300 resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || isLoading}
            className="px-3 py-2 text-white bg-blue-500 rounded-lg transition-colors hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
