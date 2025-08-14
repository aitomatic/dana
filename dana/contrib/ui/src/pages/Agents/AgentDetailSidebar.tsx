import React, { useState, useEffect, useRef, useCallback } from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import { apiService } from '@/lib/api';
import { useParams } from 'react-router-dom';
import { useSmartChatStore } from '@/stores/smart-chat-store';
import { useAgentStore } from '@/stores/agent-store';
import { useKnowledgeStore } from '@/stores/knowledge-store';
import { useUIStore } from '@/stores/ui-store';
import { ArrowUp, Expand, Collapse } from 'iconoir-react';
import { MarkdownViewerSmall } from './chat/markdown-viewer';
import { useSmartChatWebSocket, type ChatUpdateMessage } from '@/hooks/useSmartChatWebSocket';

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
          ${isResizing ? 'bg-white shadow-sm' : 'bg-white shadow-sm group-hover:bg-primary'}
        `}
        style={{
          zIndex: 60,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};

// Processing status message type
interface ProcessingStatusMessage {
  id: string;
  toolName: string;
  message: string;
  status: 'init' | 'in_progress' | 'finish' | 'error';
  progression?: number;
  timestamp: Date;
}

// Collapsible processing status history component
const ProcessingStatusHistory: React.FC<{
  messages: ProcessingStatusMessage[];
  isExpanded: boolean;
  onToggle: () => void;
}> = ({ messages, isExpanded, onToggle }) => {
  if (messages.length === 0) return null;

  return (
    <div className="flex flex-col gap-2 self-start px-3 py-2 text-left border border-gray-200 rounded-lg bg-gray-50">
      <button
        onClick={onToggle}
        className="flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-800 transition-colors"
      >
        {isExpanded ? <Collapse className="w-4 h-4" /> : <Expand className="w-4 h-4" />}
        Reasoning ({messages.length})
      </button>
      
      {isExpanded && (
        <div className="flex flex-col gap-3 max-h-60 overflow-y-auto">
          {messages.map((msg) => (
            <div key={msg.id} className="flex flex-col gap-2 p-2 border border-gray-200 rounded bg-white">
              <div className="flex gap-2 items-center">
                {msg.status === 'in_progress' && (
                  <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                )}
                {msg.status === 'finish' && (
                  <div className="w-4 h-4 rounded-full bg-green-500 flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                )}
                {msg.status === 'error' && (
                  <div className="w-4 h-4 rounded-full bg-red-500 flex items-center justify-center">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                )}
                <span className="text-sm font-medium text-gray-600">{msg.toolName}</span>
                <span className="text-xs text-gray-400 ml-auto">
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <span className="text-sm text-gray-600">{msg.message}</span>
              {msg.progression !== undefined && (
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-gray-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${msg.progression * 100}%` }}
                  ></div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SmartAgentChat: React.FC<{
  agentName?: string;
  onConnectionStateChange?: (state: string) => void;
}> = ({ agentName, onConnectionStateChange }) => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isComposing, setIsComposing] = useState(false);
  const messages = useSmartChatStore((s) => s.messages);
  const addMessage = useSmartChatStore((s) => s.addMessage);
  const removeMessage = useSmartChatStore((s) => s.removeMessage);
  const clearMessages = useSmartChatStore((s) => s.clearMessages);
  const setMessages = useSmartChatStore((s) => s.setMessages);
  // fetchAgent removed - now using direct API calls to avoid loading skeleton
  const { setAgentDetailActiveTab, setKnowledgeBaseActiveSubTab } = useUIStore();
  const bottomRef = useRef<HTMLDivElement | null>(null);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingMessage, setThinkingMessage] = useState('Thinking...');
  const [processingStatusHistory, setProcessingStatusHistory] = useState<ProcessingStatusMessage[]>([]);
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(false);

  // WebSocket integration for real-time updates
  const handleChatUpdate = useCallback((message: ChatUpdateMessage) => {
    const newStatusMessage: ProcessingStatusMessage = {
      id: `${Date.now()}-${Math.random()}`,
      toolName: message.tool_name,
      message: message.content,
      status: message.status,
      progression: message.progression,
      timestamp: new Date(),
    };

    setProcessingStatusHistory(prev => {
      // If this is an update to an existing tool, replace it
      const existingIndex = prev.findIndex(msg => msg.toolName === message.tool_name);
      if (existingIndex !== -1) {
        const updated = [...prev];
        updated[existingIndex] = newStatusMessage;
        return updated;
      }
      // Otherwise add as new message
      return [...prev, newStatusMessage];
    });

    // Don't clear processing status - keep it in history
    // Only remove very old messages (older than 1 hour) to prevent memory issues
    setTimeout(() => {
      setProcessingStatusHistory(prev => 
        prev.filter(msg => 
          Date.now() - msg.timestamp.getTime() < 60 * 60 * 1000 // 1 hour
        )
      );
    }, 60 * 60 * 1000);
  }, []);

  const { connectionState } = useSmartChatWebSocket({
    agentId: agent_id || '',
    onChatUpdate: handleChatUpdate,
    onConnect: () => console.log('🟢 WebSocket connected'),
    onDisconnect: () => console.log('🔴 WebSocket disconnected'),
    onError: (error) => console.error('❌ WebSocket error:', error),
    enabled: !!agent_id, // Only enable when we have an agent_id
  });

  // Notify parent component of connection state changes
  useEffect(() => {
    onConnectionStateChange?.(connectionState);
  }, [connectionState, onConnectionStateChange]);

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

      // Refresh agent data silently if the smart chat updated agent properties
      if (
        response.success &&
        (response.updates_applied?.length > 0 || response.updated_domain_tree)
      ) {
        try {
          // Only refresh agent data for numeric IDs (regular agents)
          // Use silent refresh to avoid showing loading skeleton
          if (!isNaN(Number(agent_id))) {
            const updatedAgent = await apiService.getAgent(parseInt(agent_id));
            // Update the agent store without triggering loading state
            const currentState = useAgentStore.getState();
            useAgentStore.setState({
              ...currentState,
              selectedAgent: updatedAgent,
            });
          }
        } catch (fetchError) {
          console.warn('Failed to refresh agent data:', fetchError);
        }
      }

      // If the response indicates a knowledge status update, trigger centralized store refresh
      if (response.status === 'knowledge_status_update' || response.updated_domain_tree) {
        // Use our centralized knowledge store for domain knowledge updates
        // This will automatically handle debouncing and avoid duplicate calls
        const knowledgeStore = useKnowledgeStore.getState();
        if (agent_id) {
          knowledgeStore.fetchKnowledgeData(agent_id, true); // Force refresh
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
      <div className="flex overflow-y-auto flex-col h-full group">
        <div className="flex overflow-y-auto flex-col flex-1 gap-2 px-2 py-2 custom-scrollbar">
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
                className={`rounded-sm px-3 py-2 text-sm ${msg.sender === 'user'
                  ? 'border border-gray-100 bg-gray-50'
                  : isThinking
                    ? ' self-start text-left border border-gray-100'
                    : ' self-start text-left bg-white'
                  }`}
              >
                {isThinking ? (
                  <div className="flex gap-2 items-center px-3 py-2">
                    <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                    <span className="text-sm text-gray-700">{msg.text}</span>
                  </div>
                ) : (
                  <>
                    <MarkdownViewerSmall 
                      backgroundContext={msg.sender === 'user' ? 'user' : 'agent'}
                    >
                      {msg.text}
                    </MarkdownViewerSmall>
                    {isWelcomeMessage && (
                      <div className="flex flex-col gap-2 mt-3">
                        <button
                          onClick={handleCTAClick}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white rounded-md border border-gray-300 shadow-sm transition-colors duration-200 cursor-pointer hover:bg-gray-100"
                        >
                          Add knowledge on a topic
                        </button>
                        <button
                          onClick={handleAddDocumentsClick}
                          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white rounded-md border border-gray-300 shadow-sm transition-colors duration-200 cursor-pointer hover:bg-gray-100"
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
            <div className="flex gap-2 items-center self-start px-3 py-2 text-left">
              <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
              <span className="text-sm text-gray-700">{thinkingMessage}</span>
            </div>
          )}
          <ProcessingStatusHistory
            messages={processingStatusHistory}
            isExpanded={isHistoryExpanded}
            onToggle={() => setIsHistoryExpanded(!isHistoryExpanded)}
          />
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
  const [connectionState, setConnectionState] = useState<string>('disconnected');
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
      <div className="flex overflow-y-auto flex-col h-full bg-white">
        <div className="flex gap-3 items-center p-2 h-14 border-b border-gray-200">
          <img className="w-10 h-10 rounded-full" src={DanaAvatar} alt="Dana avatar" />
          <div className="flex-1">
            <div className="text-sm font-semibold text-gray-900">Dana</div>
            <div className="text-xs text-gray-500">Agent builder assistant</div>
          </div>
         
        </div>
        <div className="flex overflow-y-auto flex-col flex-1">
          <SmartAgentChat
            agentName={selectedAgent?.name}
            onConnectionStateChange={setConnectionState}
          />
        </div>
      </div>
    </div>
  );
};
