import React, { useState, useRef, useEffect } from 'react';
import { Send, X } from 'lucide-react';
import { useParams } from 'react-router-dom';
import { apiService } from '@/lib/api';
import { MarkdownViewerSmall } from './chat/markdown-viewer';

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
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

    try {
      // Call the new agent test API using apiService
      const data = await apiService.testAgentById(agent_id, userMessage.text);

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
      className={`absolute top-0 right-0 flex flex-col w-96 h-full bg-white border-l border-gray-200 shadow-lg transform transition-transform duration-300 ease-in-out z-50 ${
        isVisible ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="flex justify-between items-center p-4 border-b border-gray-200">
        <h3 className="font-semibold text-gray-900">Test Chat with {agentName}</h3>
        <button
          onClick={onClose}
          className="p-1 text-gray-400 transition-colors hover:text-gray-600"
        >
          <X className="w-5 h-5" />
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
              className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                message.sender === 'user'
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
            <div className="px-4 py-2 bg-gray-100 rounded-lg">
              <div className="flex space-x-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.1s' }}
                ></div>
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: '0.2s' }}
                ></div>
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
