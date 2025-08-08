import React, { useState, useEffect, useRef, useCallback } from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import { apiService } from '@/lib/api';
import { useParams } from 'react-router-dom';
import { useSmartChatStore } from '@/stores/smart-chat-store';
import { useAgentStore } from '@/stores/agent-store';
import { useUIStore } from '@/stores/ui-store';
import { ArrowUp } from 'iconoir-react';
import { MarkdownViewerSmall } from './chat/markdown-viewer';

// Constants for resize functionality
const MIN_WIDTH = 380;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 420;
const RESIZE_HANDLE_WIDTH = 2;

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
          ${isResizing ? 'bg-white shadow-sm' : 'bg-white group-hover:bg-primary shadow-sm'}
        `}
        style={{
          zIndex: 60,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};

const SmartAgentChat: React.FC<{ agentName?: string }> = ({ agentName }) => {
  // Custom scrollbar styles
  const scrollbarStyles = `
    .custom-scrollbar::-webkit-scrollbar {
      width: 4px;
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
  const { setAgentDetailActiveTab, setKnowledgeBaseActiveSubTab } = useUIStore();
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingMessage, setThinkingMessage] = useState('Thinking...');

  // Function to handle CTA button click
  const handleCTAClick = () => {
    setInput('Add knowledge about ');
    // Focus the input field after a short delay to ensure it's rendered
    setTimeout(() => {
      const textarea = document.querySelector(
        'textarea[placeholder="Type your message"]',
      ) as HTMLTextAreaElement;
      if (textarea) {
        textarea.focus();
        textarea.setSelectionRange(textarea.value.length, textarea.value.length);
      }
    }, 100);
  };

  // Function to handle "Add documents" CTA button click
  const handleAddDocumentsClick = () => {
    setAgentDetailActiveTab('Knowledge Base');
    setKnowledgeBaseActiveSubTab('Documents');

    // Add a message to the chat panel
    addMessage({
      sender: 'agent',
      text: 'Now, please upload your files in Documents panel',
    });
  };

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
              ? `Hi! I'm here to help you to train **${displayName}**. Here are the next steps I'd recommend to make ${displayName} better:`
              : `Hi! I'm Dana. I'm here to help you to train your agent. First of all, what expertise your agent should have?`,
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

    const userInput = input;
    setInput('');
    setLoading(true);

    try {
      setIsThinking(true);
      setThinkingMessage(thinkingMessages[Math.floor(Math.random() * thinkingMessages.length)]);
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
          // Only refresh agent data for numeric IDs (regular agents)
          if (!isNaN(Number(agent_id))) {
            await fetchAgent(parseInt(agent_id));
          }
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
      setIsThinking(false);
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

  // const handleFileUpload = () => {
  //   const fileInput = document.createElement('input');
  //   fileInput.type = 'file';
  //   fileInput.accept = '*/*';
  //   fileInput.onchange = (e) => {
  //     const file = (e.target as HTMLInputElement).files?.[0];
  //     if (file) {
  //       // TODO: Implement file upload functionality
  //       console.log('File selected:', file.name);
  //       // For now, just add a message indicating file upload intent
  //       addMessage({
  //         sender: 'user',
  //         text: `📎 Uploaded: ${file.name}`,
  //       });
  //     }
  //   };
  //   fileInput.click();
  // };

  return (
    <>
      <style>{scrollbarStyles}</style>
      <div className="flex overflow-y-auto flex-col h-full group">
        <div
          className="flex overflow-y-auto flex-col flex-1 gap-2 px-2 py-2 custom-scrollbar"
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
            const isWelcomeMessage =
              msg.sender === 'agent' &&
              (msg.text.includes("Hi! I'm Dana") ||
                msg.text.includes("Hi! I'm here to help you to train") ||
                msg.text.includes('Welcome! How can I assist you'));

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
                  <>
                    <MarkdownViewerSmall>{msg.text}</MarkdownViewerSmall>
                    {isWelcomeMessage && (
                      <div className="mt-3 flex flex-col gap-2">
                        <button
                          onClick={handleCTAClick}
                          className="px-4 py-2 cursor-pointer text-sm font-medium text-gray-700 border border-gray-300 bg-white rounded-md hover:bg-gray-100 transition-colors duration-200 shadow-sm"
                        >
                          Add knowledge on a topic
                        </button>
                        <button
                          onClick={handleAddDocumentsClick}
                          className="px-4 py-2 cursor-pointer text-sm font-medium text-gray-700 border border-gray-300 bg-white rounded-md hover:bg-gray-100 transition-colors duration-200 shadow-sm"
                        >
                          Add documents
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            );
          })}
          {isThinking && (
            <div className="flex gap-2 items-center">
              <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
              <span className="text-gray-700">{thinkingMessage}</span>
            </div>
          )}
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
            {/* <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={handleFileUpload}
                  className="absolute bottom-3 left-3 p-1 text-gray-400"
                  disabled={loading}
                >
                  <div className="flex justify-center items-center p-2 text-gray-700 rounded-full border border-gray-300 cursor-pointer hover:bg-gray-200">
                    <Attachment className="w-4 h-4" />
                  </div>
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Add files</p>
              </TooltipContent>
            </Tooltip> */}
            {input.trim() && (
              <button
                onClick={sendMessage}
                className="absolute right-3 bottom-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:text-blue-600"
                title="Send message"
                disabled={loading}
              >
                <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export const AgentDetailSidebar: React.FC = () => {
  const selectedAgent = useAgentStore((s) => s.selectedAgent);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    // Try to get saved width from localStorage
    const savedWidth = localStorage.getItem('agent-detail-sidebar-width');
    if (savedWidth) {
      const width = parseInt(savedWidth, 10);
      return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
    }
    return DEFAULT_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);

  // Save width to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('agent-detail-sidebar-width', sidebarWidth.toString());
  }, [sidebarWidth]);

  const handleResize = useCallback((newWidth: number) => {
    setSidebarWidth(newWidth);
  }, []);

  return (
    <div
      className="relative max-h-[calc(100vh-64px)] border-r border-gray-200 overflow-visible flex flex-col bg-gray-50"
      style={{
        width: `${sidebarWidth}px`,
        minWidth: `${MIN_WIDTH}px`,
        maxWidth: `${MAX_WIDTH}px`,
      }}
    >
      <ResizeHandle onResize={handleResize} isResizing={isResizing} setIsResizing={setIsResizing} />
      <div className="flex flex-col h-full bg-white overflow-y-auto">
        <div className="flex h-14 gap-3 items-center p-2 border-b border-gray-200">
          <img className="w-10 h-10 rounded-full" src={DanaAvatar} alt="Dana avatar" />
          <div>
            <div className="font-semibold text-sm  text-gray-900">Dana</div>
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
