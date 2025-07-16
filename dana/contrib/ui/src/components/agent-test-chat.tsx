import { useState, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Send, Loader2 } from 'lucide-react';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';

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

    try {
      // Test the agent directly with the new API
      const response = await apiService.testAgent({
        agent_code: agentCode,
        message: userMessage.content,
        agent_name: agentName || 'Test Agent',
        agent_description: agentDescription || 'A test agent',
        context: { user_id: 1, test_mode: true },
        folder_path: currentFolder,
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
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.content.includes('error') || message.content.includes('Sorry')
                    ? 'bg-red-100 text-red-800 border border-red-200'
                    : 'bg-gray-100 text-gray-900',
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

      {/* Input */}
      <div className="p-3 bg-gray-50 border-t border-gray-200">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Chat with agent"
              className="px-3 py-2 w-full text-sm rounded-lg border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isTesting}
            />
          </div>
          <Button onClick={handleSendMessage} disabled={!canSend} size="sm" className="px-4">
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
