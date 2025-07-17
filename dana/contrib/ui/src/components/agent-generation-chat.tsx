import { useState, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { apiService } from '@/lib/api';
import type {
  MessageData,
  AgentGenerationResponse,
  AgentCapabilities,
  MultiFileProject,
} from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Send, Loader2, Upload } from 'lucide-react';
import { MarkdownViewerSmall } from '@/pages/Agents/chat/markdown-viewer';
import { useAgentCapabilitiesStore } from '@/stores/agent-capabilities-store';
import { useAgentBuildingStore } from '@/stores/agent-building-store';
import { FileUpload } from '@/components/file-upload';

// Message interface for the chat
interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface AgentGenerationChatProps {
  onCodeGenerated: (
    code: string,
    name?: string,
    description?: string,
    multiFileProject?: MultiFileProject,
    agentId?: string,
    agentFolder?: string,
  ) => void;
  currentCode?: string;
  className?: string;
  onGenerationStart?: () => void;
  enableMultiFile?: boolean;
  // Two-phase generation props
  onPhaseChange?: (phase: 'description' | 'code_generation') => void;
  onReadyForCodeGeneration?: (agentId: number) => void;
}

// Helper function to format suggested questions into a readable message
const formatSuggestedQuestionsMessage = (
  agentName: string,
  agentDescription: string,
  suggestedQuestions?: string[],
  followUpMessage?: string,
): string => {
  console.log('🏗️ Formatting suggested questions:', { agentName, agentDescription, suggestedQuestions, followUpMessage });

  let message = '';

  // Add follow-up message if available
  if (followUpMessage) {
    message += `${followUpMessage}\n\n`;
  }

  // Add suggested questions if available
  if (suggestedQuestions && suggestedQuestions.length > 0) {
    message += '**Here are some questions to help me understand your agent better:**\n\n';
    suggestedQuestions.forEach((question, index) => {
      message += `${index + 1}. ${question}\n`;
    });
  } else {
    // Fallback message if no suggested questions
    message += `I'm working on understanding your requirements for the **${agentName}** agent. Could you provide more details about:\n\n`;
    message += `1. What specific tasks should this agent perform?\n`;
    message += `2. What knowledge or data sources should it have access to?\n`;
    message += `3. Are there any specific workflows or processes it should follow?\n`;
  }

  console.log('🔚 Final formatted message:', message);
  return message;
};

// Add type declarations for window properties
declare global {
  interface Window {
    latestGeneratedAgentId?: number;
    latestGeneratedAgentFolder?: string;
  }
}

const AgentGenerationChat = ({
  onCodeGenerated,
  currentCode,
  className,
  onGenerationStart,
  onPhaseChange,
  onReadyForCodeGeneration,
}: AgentGenerationChatProps) => {
  // Zustand stores
  const { setCapabilities, setLoading, setError } = useAgentCapabilitiesStore();
  const {
    currentAgent,
    isGenerating,
    setGenerating,
    setAnalyzing,
    setError: setBuildingError,
    initializeAgent,
    updateAgentData,
    setPhase,
    setReadyForCodeGeneration,
    setAgentId,
    setAgentFolder,
    setDanaCode,
    setMultiFileProject,
    setCapabilities: setBuildingCapabilities,
    addConversationMessage,
  } = useAgentBuildingStore();

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content:
        "Hi! I'm here to help you create a Dana agent. Let's start by describing what kind of agent you'd like to build. Tell me about the agent's purpose, capabilities, or any specific requirements you have.",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [showFileUpload, setShowFileUpload] = useState(false);

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
    setGenerating(true);

    // Update store loading state
    setLoading(true);
    setError(null);

    // Add message to building store
    addConversationMessage('user', userMessage.content);

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

      // Call the appropriate API based on current phase
      let response: AgentGenerationResponse;

      // If no agent exists yet, initialize one for description phase
      if (!currentAgent) {
        initializeAgent('New Agent', userMessage.content);
      }

      // Get the current agent state after potential initialization
      const agent = useAgentBuildingStore.getState().currentAgent;

      if (agent?.phase === 'description' || !agent) {
        // Phase 1: Use description endpoint
        const descriptionResponse = await apiService.describeAgent({
          messages: apiMessages,
          agent_id: agent?.id || undefined,
          agent_data: agent?.agent_data, // Send current agent data for modification
        });

        // Convert to AgentGenerationResponse format
        response = {
          success: descriptionResponse.success,
          dana_code: undefined,
          agent_name: descriptionResponse.agent_name,
          agent_description: descriptionResponse.agent_description,
          capabilities: descriptionResponse.capabilities,
          needs_more_info: !descriptionResponse.ready_for_code_generation,
          follow_up_message: descriptionResponse.follow_up_message,
          suggested_questions: descriptionResponse.suggested_questions,
          agent_id: descriptionResponse.agent_id,
          ready_for_code_generation: descriptionResponse.ready_for_code_generation,
          error: descriptionResponse.error,
          folder_path: descriptionResponse.folder_path,
          agent_folder: descriptionResponse.agent_folder,
        };

        // Update building store
        if (descriptionResponse.agent_id) {
          setAgentId(descriptionResponse.agent_id);
        }
        setReadyForCodeGeneration(descriptionResponse.ready_for_code_generation);

        // Update current agent data with the response
        if (descriptionResponse.success) {
          const updatedAgentData = {
            name: descriptionResponse.agent_name,
            description: descriptionResponse.agent_description,
            config: {},
            generation_phase: 'description',
            agent_description_draft: {
              name: descriptionResponse.agent_name,
              description: descriptionResponse.agent_description,
              capabilities: descriptionResponse.capabilities?.workflow || [],
              knowledge_domains: descriptionResponse.capabilities?.knowledge || [],
              workflows: descriptionResponse.capabilities?.workflow || [],
            },
            generation_metadata: {
              conversation_context: apiMessages,
              created_at: new Date().toISOString()
            }
          };
          updateAgentData({
            name: descriptionResponse.agent_name,
            description: descriptionResponse.agent_description,
            agent_data: updatedAgentData
          });
        }

        // Notify parent components
        if (onPhaseChange) {
          onPhaseChange('description');
        }

        if (descriptionResponse.ready_for_code_generation && onReadyForCodeGeneration) {
          onReadyForCodeGeneration(descriptionResponse.agent_id);
        }
      } else {
        // Phase 2: Use code generation endpoint
        if (!currentAgent?.id) {
          throw new Error('Agent ID is required for code generation');
        }

        response = await apiService.generateAgentCode(currentAgent.id, {
          agent_id: currentAgent.id,
          multi_file: true,
        });

        // Update phase
        setPhase('code_generation');
        if (onPhaseChange) {
          onPhaseChange('code_generation');
        }
      }

      if (response.success) {
        // Debug logging
        console.log('🔍 Agent Generation Response:', response);
        console.log('🎯 Capabilities:', response.capabilities);

        // Store capabilities in Zustand store
        if (response.capabilities) {
          setCapabilities(response.capabilities);
          console.log('✅ Capabilities stored in Zustand store');
        }

        // Store agent_id and agent_folder for test chat and file upload
        if (response.agent_id) {
          window.latestGeneratedAgentId = response.agent_id;
          setAgentId(response.agent_id);
        }
        // Normalize folder path from backend response (agent_folder or folder_path)
        console.log('🔍 Response:', response);
        const folderPath = (response as any).folder_path ?? response.agent_folder;
        console.log('🔍 Folder Path:', folderPath);
        if (folderPath) {
          setAgentFolder(folderPath);
          // Also update the agent object in the store for consistency
          updateAgentData({ folder_path: folderPath });
        }

        // Format the assistant message based on phase
        let formattedMessage: string;

        if (agent?.phase === 'description' || !agent) {
          // Phase 1: Display the message directly from backend
          formattedMessage = response.follow_up_message || 'I understand your request. Let me help you create an agent.';

          // Add "Build Agent" button message if ready for code generation
          if (response.ready_for_code_generation) {
            formattedMessage += '\n\n---\n\n';
            formattedMessage += '**Ready to build your agent!** You can now: Click the "Build Agent" button to generate the code';
          }
        } else {
          // Phase 2: Code generation completed
          formattedMessage = `I've generated Dana code for your agent! Here's what I created:\n\n`;
          formattedMessage += `**Agent Name:** ${response.agent_name || 'Custom Agent'}\n`;
          formattedMessage += `**Description:** ${response.agent_description || 'A specialized agent for your needs'}\n\n`;
          formattedMessage += `The code has been loaded into the editor on the right. You can review and modify it as needed.`;

          formattedMessage += '\n\n---\n\n';
          formattedMessage += 'Your agent code has been generated successfully! You can now test it in the right panel.';
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
        addConversationMessage('assistant', formattedMessage);

        // Call the callback to update the editor (only for Phase 2)
        if (agent?.phase === 'code_generation' && response.dana_code) {
          setDanaCode(response.dana_code);
          if (response.multi_file_project) {
            setMultiFileProject(response.multi_file_project);
          }
          onCodeGenerated(
            response.dana_code,
            response.agent_name,
            response.agent_description,
            response.multi_file_project,
            response.agent_id ? String(response.agent_id) : undefined,
            response.agent_folder,
          );
        }

        // Show appropriate success message
        if (agent?.phase === 'description' || !agent) {
          if (response.needs_more_info) {
            toast.success('Agent description updated! Feel free to provide more details to enhance it further.');
          } else if (response.ready_for_code_generation) {
            toast.success('Agent description complete! Agent folder created. You can now upload files and generate the code.');
          } else {
            toast.success('Agent description updated successfully!');
          }
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
      setBuildingError(error instanceof Error ? error.message : 'Failed to generate agent code');

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
      setGenerating(false);
      setLoading(false);
    }
  }, [inputMessage, isGenerating, messages, currentCode, onCodeGenerated, currentAgent, initializeAgent, updateAgentData]);

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

  const handleProceedToBuild = async () => {
    const agent = useAgentBuildingStore.getState().currentAgent;
    if (!agent?.ready_for_code_generation) return;

    setGenerating(true);
    setLoading(true);

    try {
      // Gather all conversation messages
      const apiMessages: MessageData[] = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }));

      // Compose agent summary for backend using capabilities from /describe endpoint
      const agentSummary: any = {
        name: agent.name,
        description: agent.description,
        capabilities: agent.capabilities,
        id: agent.id,
      };
      if ('folder_path' in agent && agent.folder_path) {
        agentSummary.folder_path = agent.folder_path;
      }

      // Compose payload
      const ragPromptAddition = `\n\nWhen generating the agent code, please ensure the following:\n\n1. In the file [1mknowledges.na[0m, declare a RAG resource for knowledge retrieval, for example:\n   rag_resource = use("rag", sources=["./docs"])\n\n   Also, list or describe the knowledge domains or files available to the agent.\n\n2. In the file [1mmethods.na[0m, demonstrate how the agent can use the knowledges (or rag_resource) resource to retrieve information. For example, show a method that queries the knowledge base using the RAG resource and returns relevant information to the user.\n\n3. Make sure the agent's methods leverage the knowledge resource for answering questions or solving tasks that require external knowledge.\n\nExample for methods.na:\n\ndef answer_question(question: str) -> str:\n    # Use the RAG resource to retrieve relevant information\n    context = rag_resource.retrieve(question)\n    return f"Based on the documents, here's what I found: {context}"\n`;
      const payload = {
        prompt: `Build the agent now. ${ragPromptAddition}`,
        messages: apiMessages,
        agent_summary: agentSummary,
        multi_file: true, // or false, as needed
      };

      // Call the new endpoint
      const response = await apiService.generateAgentFromPrompt(payload);

      if (response.success && response.dana_code) {
        setDanaCode(response.dana_code);
        if (response.multi_file_project) {
          setMultiFileProject(response.multi_file_project);
        }
        onCodeGenerated(
          response.dana_code,
          response.agent_name,
          response.agent_description,
          response.multi_file_project,
          response.agent_id ? String(response.agent_id) : undefined,
          response.agent_folder,
        );
        // Add success message, etc.
        const successMessage: ChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Your agent code has been generated successfully! You can now test it in the right panel.',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, successMessage]);
        addConversationMessage('assistant', successMessage.content);
        toast.success('Agent code generated successfully!');
      } else {
        throw new Error(response.error || 'Failed to generate agent code');
      }
    } catch (error) {
      console.error('Failed to generate agent code:', error);
      const errorMessage: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error while generating the agent code. Please try again.',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      toast.error('Failed to generate agent code. Please try again.');
      setPhase('description');
      if (onPhaseChange) {
        onPhaseChange('description');
      }
    } finally {
      setGenerating(false);
      setLoading(false);
    }
  };

  return (
    <div
      className={cn('flex flex-col h-full bg-white rounded-lg border border-gray-200', className)}
    >
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
                    message.role === 'user'
                      ? 'text-blue-100 opacity-80'
                      : 'text-gray-500 opacity-80',
                  )}
                >
                  {message.role === 'user' ? 'User' : 'DANA Agent'}
                </div>
                {message.role === 'user' ? (
                  <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                ) : (
                  <div>
                    <MarkdownViewerSmall>{message.content}</MarkdownViewerSmall>
                    {/* Show Build Agent button in the most recent assistant message when ready */}
                    {(() => {
                      const agent = useAgentBuildingStore.getState().currentAgent;
                      const isLastMessage = messages[messages.length - 1]?.id === message.id;
                      const shouldShowButton = agent?.phase === 'description' &&
                        agent?.ready_for_code_generation &&
                        agent?.id &&
                        isLastMessage;

                      return shouldShowButton;
                    })() && (
                        <div className="mt-3 pt-3 border-t border-gray-200">
                          <Button
                            onClick={handleProceedToBuild}
                            disabled={isGenerating}
                            className="w-full px-4 py-2 text-white bg-green-600 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                          >
                            {isGenerating ? (
                              <>
                                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                                Generating Code...
                              </>
                            ) : (
                              <>
                                <Send className="w-4 h-4 mr-2" />
                                Build Agent
                              </>
                            )}
                          </Button>
                        </div>
                      )}
                  </div>
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
          </div>
        ))}

        {isGenerating && (
          <div className="flex gap-3 justify-start">
            <div className="flex flex-col">
              {/* Loading message bubble with sender label inside */}
              <div className="px-4 py-2 text-gray-900 bg-gray-100 rounded-lg">
                <div className="mb-1 text-xs font-medium text-gray-500 opacity-80">DANA Agent</div>
                <div className="flex gap-2 items-center">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Understanding your request...</span>
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
        {showFileUpload && (
          <div className="mb-4 p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium text-gray-900">Upload Knowledge Files</h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowFileUpload(false)}
              >
                ×
              </Button>
            </div>
            <FileUpload
              agentId={window.latestGeneratedAgentId?.toString()}
              conversationContext={currentAgent?.conversation_context}
              agentInfo={currentAgent}
              onFilesUploaded={(files) => {
                console.log('Files uploaded in chat:', files);
                setShowFileUpload(false);

                // Use the generated response from the backend for each file
                files.forEach(file => {
                  if (file.generatedResponse) {
                    // Add the user upload message
                    const userMessage: ChatMessage = {
                      id: Date.now().toString(),
                      role: 'user',
                      content: `Uploaded knowledge file: ${file.name}`,
                      timestamp: new Date(),
                    };
                    setMessages(prev => [...prev, userMessage]);

                    // Add the assistant response from backend
                    const assistantMessage: ChatMessage = {
                      id: (Date.now() + 1).toString(),
                      role: 'assistant',
                      content: file.generatedResponse,
                      timestamp: new Date(),
                    };
                    setMessages(prev => [...prev, assistantMessage]);

                    // Add to conversation context in Zustand store
                    addConversationMessage('user', userMessage.content);
                    addConversationMessage('assistant', assistantMessage.content);

                    // Update capabilities if provided
                    if (file.updatedCapabilities) {
                      setCapabilities(file.updatedCapabilities);
                      setBuildingCapabilities(file.updatedCapabilities);
                    }

                    // Update agent readiness if provided
                    if (file.readyForCodeGeneration !== undefined) {
                      console.log('🔄 Updating agent readiness:', file.readyForCodeGeneration);
                      setReadyForCodeGeneration(file.readyForCodeGeneration);
                    }
                  }
                });
              }}
              compact={true}
            />
          </div>
        )}

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
            variant="outline"
            onClick={() => setShowFileUpload(!showFileUpload)}
            disabled={isGenerating}
            className="px-3 py-2"
            title="Upload knowledge files"
          >
            <Upload className="w-4 h-4" />
          </Button>
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
