import React, { useState, useEffect, useRef } from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import { apiService } from '@/lib/api';
import { useParams } from 'react-router-dom';
import { useSmartChatStore } from '@/stores/smart-chat-store';
import { useAgentStore } from '@/stores/agent-store';
import { Plus } from 'lucide-react';
import { MarkdownViewerSmall } from './chat/markdown-viewer';

const SmartAgentChat: React.FC<{ agentName?: string }> = ({ agentName }) => {
  // Custom scrollbar styles
  const scrollbarStyles = `
    .custom-scrollbar::-webkit-scrollbar {
      width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
      background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
      background: transparent;
      border-radius: 3px;
    }
    .custom-scrollbar:hover::-webkit-scrollbar-thumb {
      background: #d1d5db;
    }
  `;
  const { agent_id } = useParams<{ agent_id: string }>();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const messages = useSmartChatStore((s) => s.messages);
  const addMessage = useSmartChatStore((s) => s.addMessage);
  const removeMessage = useSmartChatStore((s) => s.removeMessage);
  const clearMessages = useSmartChatStore((s) => s.clearMessages);
  const setMessages = useSmartChatStore((s) => s.setMessages);
  const { fetchAgent } = useAgentStore();
  const bottomRef = useRef<HTMLDivElement | null>(null);

  // Humanized thinking messages
  const thinkingMessages = [
    'Let me think about this...',
    'Processing your request...',
    'Analyzing what you need...',
    'Working on that for you...',
    'Gathering my thoughts...',
    'One moment while I consider this...',
    'Let me work through this...',
    'Thinking through your request...',
    'Processing this information...',
    'Just a second, organizing my response...',
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
          setMessages(history);
        } else {
          const displayName = agentName && agentName !== 'Untitled Agent' ? agentName : '';
          clearMessages();
          addMessage({
            sender: 'agent',
            text: displayName
              ? `Hi! I'm here to help you to customize **${displayName}**. What would you like to do?`
              : `Hi! I'm here to help you get started. What would you like you agent to do?`,
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
      if (
        response.success &&
        (response.updates_applied?.length > 0 || response.updated_domain_tree)
      ) {
        try {
          await fetchAgent(parseInt(agent_id));
        } catch (fetchError) {
          console.warn('Failed to refresh agent data:', fetchError);
        }
      }

      // If the response indicates a knowledge status update, refresh domain knowledge and status
      if (response.status === 'knowledge_status_update') {
        try {
          await apiService.getDomainKnowledge(agent_id);
          await apiService.getKnowledgeStatus(agent_id);
          // Optionally, trigger a UI update or notification here
        } catch (err) {
          console.warn('Failed to refresh domain knowledge/status:', err);
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

  const handleFileUpload = () => {
    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.accept = '*/*';
    fileInput.onchange = (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (file) {
        // TODO: Implement file upload functionality
        console.log('File selected:', file.name);
        // For now, just add a message indicating file upload intent
        addMessage({
          sender: 'user',
          text: `📎 Uploaded: ${file.name}`,
        });
      }
    };
    fileInput.click();
  };

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div className="flex overflow-y-auto flex-col h-full group">
        <div
          className="flex overflow-y-auto flex-col flex-1 gap-2 p-4 custom-scrollbar"
          style={{
            scrollbarWidth: 'thin',
            scrollbarColor: 'transparent transparent',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.scrollbarColor = '#d1d5db transparent';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.scrollbarColor = 'transparent transparent';
          }}
        >
          {messages.map((msg, idx) => {
            const isThinking = loading && idx === messages.length - 1 && msg.sender === 'agent';
            return (
              <div
                key={idx}
                className={`rounded-sm px-3 py-2 text-sm ${
                  msg.sender === 'user'
                    ? 'bg-gray-100'
                    : isThinking
                      ? ' self-start text-left border border-gray-100'
                      : ' self-start text-left'
                }`}
              >
                {isThinking ? (
                  <div className="flex gap-2 items-center">
                    <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                    <span className="text-gray-700">{msg.text}</span>
                  </div>
                ) : (
                  <MarkdownViewerSmall>{msg.text}</MarkdownViewerSmall>
                )}
              </div>
            );
          })}
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
            <button
              onClick={handleFileUpload}
              className="absolute bottom-3 left-3 p-1 text-gray-400"
              title="Add files"
              disabled={loading}
            >
              <div className="flex justify-center items-center w-7 h-7 rounded-full border border-gray-300 cursor-pointer">
                <Plus className="w-4 h-4" />
              </div>
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export const AgentDetailSidebar: React.FC = () => {
  const selectedAgent = useAgentStore((s) => s.selectedAgent);
  return (
    <div className="w-[420px] min-w-[380px] max-h-[calc(100vh-64px)] overflow-y-auto flex flex-col p-2 bg-gray-50">
      <div className="flex flex-col h-full bg-white rounded-lg shadow-md">
        <div className="flex gap-3 items-center p-2 border-b border-gray-200">
          <img className="w-10 h-10 rounded-full" src={DanaAvatar} alt="Dana avatar" />
          <div>
            <div className="font-semibold text-gray-900">Dana</div>
            <div className="text-xs text-gray-500">Agent builder assistant</div>
          </div>
        </div>
        <div className="flex overflow-y-auto flex-col flex-1">
          <SmartAgentChat agentName={selectedAgent?.name} />
        </div>
      </div>
    </div>
  );
};
