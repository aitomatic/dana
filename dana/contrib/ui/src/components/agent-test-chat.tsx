import { useState, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Send, Loader2, Trash2, ChevronDown, ChevronUp, X } from 'lucide-react';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';
import { useVariableUpdates } from '@/hooks/useVariableUpdates';
import LogViewer from '@/components/LogViewer';

// Message interface for the test chat
interface TestChatMessage {
  id: string;
  role: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

interface AgentTestChatProps {
  agentCode: string;
  agentName: string;
  agentDescription: string;
  className?: string;
  currentFolder?: string;
}

const AgentTestChat = ({
  agentCode,
  agentName,
  agentDescription,
  className,
  currentFolder,
}: AgentTestChatProps) => {
  const [messages, setMessages] = useState<TestChatMessage[]>([
    {
      id: '1',
      role: 'agent',
      content: "Hi, I'm Georgia! How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [hideLogs, setHideLogs] = useState(false);

  // Generate unique WebSocket ID for this test session
  const [websocketId] = useState(
    () => `agenttest-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
  );

  // WebSocket for variable updates and log streaming
  const { logUpdates, disconnect, clearLogUpdates } = useVariableUpdates(websocketId, {
    maxUpdates: 50,
    autoConnect: true,
  });

  // Ref for the messages container to enable auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Clean up WebSocket on component unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Clear messages function
  const handleClearMessages = useCallback(() => {
    setMessages([
      {
        id: '1',
        role: 'agent',
        content: "Hi, I'm Georgia! How can I help you today?",
        timestamp: new Date(),
      },
    ]);
    clearLogUpdates(); // Also clear logs when clearing messages
    setHideLogs(false); // Reset hide logs state
  }, [clearLogUpdates]);

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isTesting) return;

    const userMessage: TestChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsTesting(true);
    clearLogUpdates(); // Clear previous logs when starting new request
    setHideLogs(false); // Show logs section when starting new request

    try {
      // Test the agent directly with the new API including WebSocket ID for log streaming
      const response = await apiService.testAgent({
        agent_code: agentCode,
        message: userMessage.content,
        agent_name: agentName || 'Test Agent',
        agent_description: agentDescription || 'A test agent',
        context: { user_id: 1, test_mode: true },
        folder_path: currentFolder,
        websocket_id: websocketId, // Pass WebSocket ID for real-time log streaming
      });

      if (response.success) {
        // Add agent response
        const agentMessage: TestChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'agent',
          content: response.agent_response,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, agentMessage]);
      } else {
        throw new Error(response.error || 'Failed to get agent response');
      }
    } catch (error) {
      console.error('Failed to test agent:', error);

      // Add error message
      const errorMessage: TestChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: `Sorry, I encountered an error while testing: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your agent code and try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      toast.error('Failed to test agent. Please check your code.');
    } finally {
      setIsTesting(false);
    }
  }, [inputMessage, isTesting, agentCode, agentName, agentDescription, currentFolder]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage],
  );

  const canSend = inputMessage.trim().length > 0 && !isTesting;

  return (
    <div className={cn('flex flex-col h-full bg-[#EFF4FE]', className)}>
      {/* Header with clear button */}
      <div className="flex justify-between items-center bg-gray-50 border-b border-gray-200">
        <Button
          onClick={handleClearMessages}
          variant="ghost"
          size="sm"
          className="p-0 w-8 h-8 text-gray-50 cursor-pointer hover:text-red-500 hover:bg-red-50"
          title="Clear messages"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Messages */}
      <div className="overflow-y-auto flex-1 p-3 space-y-3">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn('flex gap-3', message.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900',
                // : message.content.includes('error') || message.content.includes('Sorry')
                //   ? 'bg-red-100 text-red-800 border border-red-200'
                //   : 'bg-gray-100 text-gray-900',
              )}
            >
              {/* Sender label inside bubble */}
              <div
                className={cn(
                  'text-xs font-medium mb-1',
                  message.role === 'user' ? 'text-blue-100 opacity-80' : 'text-gray-500 opacity-80',
                )}
              >
                {message.role === 'user' ? 'User' : 'Georgia'}
              </div>
              {message.role === 'agent' ? (
                <MarkdownViewerSmall>{message.content}</MarkdownViewerSmall>
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}
              <div
                className={cn(
                  'text-xs mt-1',
                  message.role === 'user' ? 'text-blue-100' : 'text-gray-500',
                )}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isTesting && (
          <div className="flex gap-3 justify-start">
            <div className="px-3 py-2 text-gray-900 bg-gray-100 rounded-lg">
              <div className="flex gap-2 items-center">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Testing agent...</span>
              </div>
            </div>
          </div>
        )}

        {/* Invisible div for auto-scroll target */}
        <div ref={messagesEndRef} />
      </div>

      {/* Collapsible Live Logs Section */}
      {(isTesting || logUpdates.length > 0) && !hideLogs && (
        <div className="bg-gray-50 border-t border-gray-200">
          {/* Toggle Button */}
          <div className="flex items-center justify-between px-3 py-2 hover:bg-gray-100 transition-colors">
            <div 
              className="flex items-center gap-2 cursor-pointer flex-1"
              onClick={() => setShowLogs(!showLogs)}
            >
              <span className="text-sm font-medium text-gray-600">
                Backend Logs
              </span>
              {isTesting && (
                <div className="flex items-center gap-1">
                  <Loader2 className="w-3 h-3 animate-spin text-blue-500" />
                  <span className="text-xs text-blue-600">Live</span>
                </div>
              )}
              {logUpdates.length > 0 && (
                <span className="bg-blue-100 text-blue-800 text-xs px-2 py-0.5 rounded-full font-medium">
                  {logUpdates.length}
                </span>
              )}
              {showLogs ? (
                <ChevronUp className="w-4 h-4 text-gray-400" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400" />
              )}
            </div>
            
            {/* Close button */}
            {!isTesting && (
              <button
                onClick={() => {
                  setHideLogs(true);
                  setShowLogs(false);
                }}
                className="p-1 hover:bg-gray-200 rounded transition-colors"
                title="Hide logs"
              >
                <X className="w-3 h-3 text-gray-400" />
              </button>
            )}
          </div>
          
          {/* Logs Content - Only show when expanded */}
          {showLogs && (
            <div className="px-3 pb-2">
              <LogViewer 
                logs={logUpdates}
                showTimestamps={true}
                autoScroll={true}
                maxHeight="120px"
              />
            </div>
          )}
        </div>
      )}

      {/* Input */}
      <div className="p-3 bg-gray-50 border-t border-gray-200">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Chat with agent"
              className="px-3 py-2 w-full text-sm rounded-lg border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isTesting}
            />
          </div>
          <Button
            onClick={handleSendMessage}
            disabled={!canSend}
            size="sm"
            className="px-4"
            aria-label="Send message"
          >
            {isTesting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default AgentTestChat;
