import React, { useState, useEffect, useRef } from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import { apiService } from '@/lib/api';
import { useParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useSmartChatStore } from '@/stores/smart-chat-store';
import { useAgentStore } from '@/stores/agent-store';

const SmartAgentChat: React.FC<{ agentName?: string }> = ({ agentName }) => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messages = useSmartChatStore((s) => s.messages);
  const addMessage = useSmartChatStore((s) => s.addMessage);
  const removeMessage = useSmartChatStore((s) => s.removeMessage);
  const clearMessages = useSmartChatStore((s) => s.clearMessages);
  const { fetchAgent } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Humanized thinking messages
  const thinkingMessages = [
    "Let me think about this...",
    "Processing your request...",
    "Analyzing what you need...", 
    "Working on that for you...",
    "Gathering my thoughts...",
    "One moment while I consider this...",
    "Let me work through this...",
    "Thinking through your request...",
    "Processing this information...",
    "Just a second, organizing my response..."
  ];

  useEffect(() => {
    if (bottomRef.current) {
      bottomRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  useEffect(() => {
    const fetchHistory = async () => {
      if (!agent_id) return;
      clearMessages(); // Prevent duplicate messages in dev/StrictMode
      try {
        const history = await apiService.getSmartChatHistory(agent_id);
        if (Array.isArray(history) && history.length > 0) {
          history.forEach((msg: { sender: 'user' | 'agent'; text: string }) => addMessage(msg));
        } else {
          const displayName = agentName && agentName !== 'Untitled Agent' ? agentName : '';
          addMessage({
            sender: 'agent',
            text: displayName
              ? `Hi! I'm here to help you with ${displayName}. What would you like to do?`
              : `Hi! I'm here to help you get started. What would you like to do?`,
          });
        }
      } catch (e) {
        addMessage({ sender: 'agent', text: 'Welcome! How can I assist you with this agent?' });
      }
    };
    fetchHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agent_id]);

  const sendMessage = async () => {
    if (!input.trim() || !agent_id) return;
    
    // Add user message
    const userMsg = { sender: 'user' as const, text: input };
    addMessage(userMsg);
    
    // Show humanized thinking message
    const randomThinking = thinkingMessages[Math.floor(Math.random() * thinkingMessages.length)];
    const thinkingMsg = { sender: 'agent' as const, text: randomThinking };
    addMessage(thinkingMsg);
    
    const userInput = input;
    setInput('');
    setLoading(true);
    
    try {
      const response = await apiService.smartChat(agent_id, userInput);
      
      // Remove the thinking message
      removeMessage(messages.length - 1); // Remove the last message (thinking message)
      
      // Add the actual response
      addMessage({
        sender: 'agent' as const,
        text: response.follow_up_message || response.agent_response || response.message || '...',
      });
      
      // Reload the agent data if the smart chat updated agent properties
      if (response.success && (response.updates_applied?.length > 0 || response.updated_domain_tree)) {
        try {
          await fetchAgent(parseInt(agent_id));
        } catch (fetchError) {
          console.warn('Failed to refresh agent data:', fetchError);
        }
      }
      
    } catch (e) {
      // Remove the thinking message
      removeMessage(messages.length - 1);
      addMessage({ sender: 'agent' as const, text: 'Sorry, something went wrong.' });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendMessage();
  };

  return (
    <div className="flex overflow-y-auto flex-col h-full">
      <div className="flex overflow-y-auto flex-col flex-1 gap-2 p-2">
        {messages.map((msg, idx) => {
          const isThinking = loading && idx === messages.length - 1 && msg.sender === 'agent';
          return (
            <div
              key={idx}
              className={`rounded-lg px-3 py-2 max-w-[85%] text-sm ${
                msg.sender === 'user'
                  ? 'bg-blue-100 self-end text-right'
                  : isThinking
                  ? 'bg-amber-50 self-start text-left border border-amber-200'
                  : 'bg-gray-100 self-start text-left'
              }`}
            >
              {isThinking ? (
                <div className="flex items-center gap-2">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                  <span className="text-amber-700">{msg.text}</span>
                </div>
              ) : (
                msg.text
              )}
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>
      <div className="flex gap-2 p-2 border-t">
        <input
          className="flex-1 px-2 py-1 text-sm rounded border"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask the agent assistant..."
          disabled={loading}
        />
        <Button onClick={sendMessage} disabled={loading || !input.trim()} size="sm">
          Send
        </Button>
      </div>
    </div>
  );
};

export const AgentDetailSidebar: React.FC = () => {
  const selectedAgent = useAgentStore((s) => s.selectedAgent);
  return (
    <div className="w-[320px] min-w-[280px] max-h-[calc(100vh-64px)] overflow-y-auto flex flex-col p-2 bg-gray-50">
      <div className="flex flex-col h-full bg-white rounded-lg shadow-md">
        <div className="flex gap-3 items-center p-4 mb-4 border-b border-gray-200">
          <img className="w-10 h-10 rounded-full" src={DanaAvatar} alt="Dana avatar" />
          <div>
            <div className="font-semibold text-gray-900">Dana</div>
            <div className="text-xs text-gray-500">Agent builder assistant</div>
          </div>
        </div>
        <div className="flex overflow-y-auto flex-col flex-1 mb-4">
          <SmartAgentChat agentName={selectedAgent?.name} />
        </div>
      </div>
    </div>
  );
};
