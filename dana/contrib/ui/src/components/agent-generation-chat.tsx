import { useState, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { apiService } from '@/lib/api';
import type { MessageData, AgentGenerationResponse, AgentCapabilities } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Send, Sparkles, Loader2 } from 'lucide-react';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';
import { useAgentCapabilitiesStore } from '@/stores/agent-capabilities-store';

// Message interface for the chat
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AgentGenerationChatProps {
  onCodeGenerated: (code: string, name?: string, description?: string) => void;
  currentCode?: string;
  className?: string;
  onGenerationStart?: () => void;
}

// Helper function to format capabilities into a readable message
const formatCapabilitiesMessage = (
  agentName: string,
  agentDescription: string,
  capabilities?: AgentCapabilities,
): string => {
  console.log('🏗️ Formatting capabilities:', { agentName, agentDescription, capabilities });

  let message = `I've generated Dana code for your agent! Here's what I created:\n\n`;
  message += `**Agent Name:** ${agentName}\n`;
  message += `**Description:** ${agentDescription}\n\n`;

  if (capabilities) {
    console.log('✅ Capabilities found, adding to message');
    message += `## Agent Analysis\n\n`;

    if (capabilities.summary) {
      console.log('📊 Adding summary:', capabilities.summary);
      message += `**Summary:** ${capabilities.summary}\n\n`;
    }

    if (capabilities.knowledge && capabilities.knowledge.length > 0) {
      console.log('🧠 Adding knowledge domains:', capabilities.knowledge);
      message += `**Knowledge Domains:**\n`;
      capabilities.knowledge.forEach((domain) => {
        message += `• ${domain}\n`;
      });
      message += `\n`;
    }

    if (capabilities.workflow && capabilities.workflow.length > 0) {
      console.log('🔄 Adding workflow:', capabilities.workflow);
      message += `**Workflow:**\n`;
      capabilities.workflow.forEach((step, index) => {
        message += `${index + 1}. ${step}\n`;
      });
      message += `\n`;
    }

    if (capabilities.tools && capabilities.tools.length > 0) {
      console.log('🛠️ Adding tools:', capabilities.tools);
      message += `**Available Tools & Capabilities:**\n`;
      capabilities.tools.forEach((tool) => {
        message += `• ${tool}\n`;
      });
      message += `\n`;
    }
  } else {
    console.log('❌ No capabilities found');
  }

  message += `The code has been loaded into the editor on the right. You can review and modify it as needed.`;
  console.log('🔚 Final formatted message:', message);
  return message;
};

const AgentGenerationChat = ({
  onCodeGenerated,
  currentCode,
  className,
  onGenerationStart,
}: AgentGenerationChatProps) => {
  // Zustand store for capabilities
  const { setCapabilities, setLoading, setError } = useAgentCapabilitiesStore();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hi! I'm here to help you create a Dana agent. Tell me what kind of agent you'd like to build, and I'll generate the code for you. You can describe the agent's purpose, capabilities, or any specific requirements you have.",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);

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
    if (!inputMessage.trim() || isGenerating) return;

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsGenerating(true);

    // Update store loading state
    setLoading(true);
    setError(null);

    // Notify parent that generation is starting
    if (onGenerationStart) {
      onGenerationStart();
    }

    try {
      // Convert messages to API format
      const apiMessages: MessageData[] = messages
        .filter((msg) => msg.role === 'user' || msg.role === 'assistant')
        .map((msg) => ({
          role: msg.role,
          content: msg.content,
        }));

      // Add the current user message
      apiMessages.push({
        role: 'user',
        content: userMessage.content,
      });

      // Call the agent generation API
      const response: AgentGenerationResponse = await apiService.generateAgent({
        messages: apiMessages,
        current_code: currentCode,
      });

      if (response.success && response.dana_code) {
        // Debug logging
        console.log('🔍 Agent Generation Response:', response);
        console.log('🎯 Capabilities:', response.capabilities);

        // Store capabilities in Zustand store
        if (response.capabilities) {
          setCapabilities(response.capabilities);
          console.log('✅ Capabilities stored in Zustand store');
        }

        // Format the assistant message with capabilities
        let formattedMessage = formatCapabilitiesMessage(
          response.agent_name || 'Custom Agent',
          response.agent_description || 'A specialized agent for your needs',
          response.capabilities,
        );

        // If API needs more information, add follow-up questions
        if (response.needs_more_info) {
          console.log('❓ API suggests gathering more information');

          formattedMessage += "\n\n---\n\n";
          formattedMessage += response.follow_up_message || "I could create an even better agent with more details. Could you provide additional information?";

          // Pick one suggested question if available
          if (response.suggested_questions && response.suggested_questions.length > 0) {
            // Select a random question from the suggestions
            const randomIndex = Math.floor(Math.random() * response.suggested_questions.length);
            const selectedQuestion = response.suggested_questions[randomIndex];
            formattedMessage += `\n\n**${selectedQuestion}**`;
          }
        }

        console.log('📝 Formatted Message:', formattedMessage);

        // Add assistant response
        const assistantMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: formattedMessage,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, assistantMessage]);

        // Call the callback to update the editor
        onCodeGenerated(response.dana_code, response.agent_name, response.agent_description);

        if (response.needs_more_info) {
          toast.success('Agent created! Feel free to provide more details to enhance it further.');
        } else {
          toast.success('Agent code generated successfully!');
        }
      } else {
        throw new Error(response.error || 'Failed to generate agent code');
      }
    } catch (error) {
      console.error('Failed to generate agent:', error);

      // Update store error state
      setError(error instanceof Error ? error.message : 'Failed to generate agent code');

      // Add error message
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error while generating the agent code. Please try again or provide more specific details about what you need.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      toast.error('Failed to generate agent code. Please try again.');
    } finally {
      setIsGenerating(false);
      setLoading(false);
    }
  }, [inputMessage, isGenerating, messages, currentCode, onCodeGenerated]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage],
  );

  const canSend = inputMessage.trim().length > 0 && !isGenerating;

  return (
    <div
      className={cn('flex flex-col h-full bg-white rounded-lg border border-gray-200', className)}
    >
      {/* Header */}
      <div className="flex gap-2 items-center p-4 border-b border-gray-200">
        <Sparkles className="w-5 h-5 text-blue-600" />
        <h3 className="font-semibold text-gray-900">Agent Generator</h3>
      </div>

      {/* Messages */}
      <div className="overflow-y-auto flex-1 p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn('flex gap-3', message.role === 'user' ? 'justify-end' : 'justify-start')}
          >
            <div className="flex flex-col">
              {/* Message bubble with sender label inside */}
              <div
                className={cn(
                  'max-w-[80%] rounded-lg px-4 py-2',
                  message.role === 'user' ? 'bg-blue-600 text-white' : 'bg-gray-100 text-gray-900',
                )}
              >
                {/* Sender label inside bubble */}
                <div
                  className={cn(
                    'text-xs font-medium mb-1',
                    message.role === 'user' ? 'text-blue-100 opacity-80' : 'text-gray-500 opacity-80',
                  )}
                >
                  {message.role === 'user' ? 'User' : 'DANA Agent'}
                </div>
                {message.role === 'user' ? <div className="text-sm whitespace-pre-wrap">{message.content}</div> : <MarkdownViewerSmall>{message.content}</MarkdownViewerSmall>}
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
          </div>
        ))}

        {isGenerating && (
          <div className="flex gap-3 justify-start">
            <div className="flex flex-col">
              {/* Loading message bubble with sender label inside */}
              <div className="px-4 py-2 text-gray-900 bg-gray-100 rounded-lg">
                <div className="text-xs font-medium mb-1 text-gray-500 opacity-80">DANA Agent</div>
                <div className="flex gap-2 items-center">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Building Georgia...</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Invisible div for auto-scroll target */}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex gap-2">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe how you want to create the agent"
            className="flex-1 px-3 py-2 text-sm rounded-lg border border-gray-300 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            rows={2}
            disabled={isGenerating}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!canSend}
            className="px-4 py-2 text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isGenerating ? (
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

export default AgentGenerationChat;
