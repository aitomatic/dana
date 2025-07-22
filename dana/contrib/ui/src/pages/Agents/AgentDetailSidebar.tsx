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
  const clearMessages = useSmartChatStore((s) => s.clearMessages);
  const bottomRef = useRef<HTMLDivElement | null>(null);

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
    const userMsg = { sender: 'user' as const, text: input };
    addMessage(userMsg);
    setInput('');
    setLoading(true);
    try {
      const response = await apiService.smartChat(agent_id, input);
      addMessage({
        sender: 'agent' as const,
        text: response.follow_up_message || response.agent_response || response.message || '...',
      });
    } catch (e) {
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
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`rounded-lg px-3 py-2 max-w-[85%] text-sm ${
              msg.sender === 'user'
                ? 'bg-blue-100 self-end text-right'
                : 'bg-gray-100 self-start text-left'
            }`}
          >
            {msg.text}
          </div>
        ))}
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
