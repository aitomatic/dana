import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { ChatRequest, ChatResponse } from '@/lib/api';
import type { ConversationRead, ConversationWithMessages, ConversationCreate } from '@/types/conversation';
import type { MessageRead } from '@/types/conversation';

export interface ChatStore {
  // State
  messages: MessageRead[];
  conversations: ConversationRead[];
  selectedConversation: ConversationWithMessages | null;
  currentAgentId: number | null;
  isLoading: boolean;
  isSending: boolean;
  isCreating: boolean;
  error: string | null;

  // Actions
  sendMessage: (message: string, agentId: number, conversationId?: number) => Promise<ChatResponse>;
  fetchConversations: (agentId: number) => Promise<void>;
  fetchConversation: (conversationId: number) => Promise<void>;
  createConversation: (conversation: ConversationCreate) => Promise<ConversationRead>;
  updateConversation: (conversationId: number, conversation: ConversationCreate) => Promise<ConversationRead>;
  deleteConversation: (conversationId: number) => Promise<void>;
  setCurrentAgentId: (agentId: number | null) => void;
  setSelectedConversation: (conversation: ConversationWithMessages | null) => void;
  clearMessages: () => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

export const useChatStore = create<ChatStore>((set, get) => ({
  // Initial State
  messages: [],
  conversations: [],
  selectedConversation: null,
  currentAgentId: null,
  isLoading: false,
  isSending: false,
  isCreating: false,
  error: null,

  // Actions
  sendMessage: async (message: string, agentId: number, conversationId?: number) => {
    set({ isSending: true, error: null });

    try {
      const request: ChatRequest = {
        message,
        agent_id: agentId,
        conversation_id: conversationId,
        context: { user_id: 1 }, // TODO: Get from auth context
      };

      const response = await apiService.chatWithAgent(request);

      // Update messages if we have a conversation
      if (response.conversation_id) {
        const { messages } = get();
        const newMessages: MessageRead[] = [
          {
            id: response.message_id - 1, // User message ID
            conversation_id: response.conversation_id,
            sender: 'user',
            content: message,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: response.message_id, // Agent message ID
            conversation_id: response.conversation_id,
            sender: 'agent',
            content: response.agent_response,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
        ];

        set({
          messages: [...messages, ...newMessages],
          isSending: false
        });
      } else {
        set({ isSending: false });
      }

      return response;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to send message';
      set({
        error: errorMessage,
        isSending: false
      });
      throw error;
    }
  },

  fetchConversations: async (agentId: number) => {
    set({ isLoading: true, error: null });

    try {
      const conversations = await apiService.getConversations(agentId);
      set({
        conversations,
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch conversations';
      set({
        conversations: [],
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  fetchConversation: async (conversationId: number) => {
    set({ isLoading: true, error: null });

    try {
      const conversation = await apiService.getConversation(conversationId);
      console.log('Fetched conversation:', conversation);
      console.log('Conversation messages:', conversation.messages);
      set({
        selectedConversation: conversation,
        messages: conversation.messages,
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch conversation';
      console.error('Error fetching conversation:', error);
      set({
        selectedConversation: null,
        messages: [],
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  createConversation: async (conversation: ConversationCreate) => {
    set({ isCreating: true, error: null });

    try {
      // Ensure agent_id is set from current agent
      const conversationWithAgent = {
        ...conversation,
        agent_id: conversation.agent_id || get().currentAgentId || 1,
      };

      const newConversation = await apiService.createConversation(conversationWithAgent);
      const { conversations } = get();
      set({
        conversations: [newConversation, ...conversations],
        isCreating: false,
      });
      return newConversation;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create conversation';
      set({
        isCreating: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  updateConversation: async (conversationId: number, conversation: ConversationCreate) => {
    set({ isCreating: true, error: null });

    try {
      const updatedConversation = await apiService.updateConversation(conversationId, conversation);
      const { conversations } = get();
      set({
        conversations: conversations.map(c =>
          c.id === conversationId ? updatedConversation : c
        ),
        isCreating: false,
      });
      return updatedConversation;
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update conversation';
      set({
        isCreating: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  deleteConversation: async (conversationId: number) => {
    set({ isCreating: true, error: null });

    try {
      await apiService.deleteConversation(conversationId);
      const { conversations } = get();
      set({
        conversations: conversations.filter(c => c.id !== conversationId),
        isCreating: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete conversation';
      set({
        isCreating: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  setCurrentAgentId: (agentId: number | null) => {
    set({ currentAgentId: agentId });
  },

  setSelectedConversation: (conversation: ConversationWithMessages | null) => {
    set({
      selectedConversation: conversation,
      messages: conversation?.messages || []
    });
  },

  clearMessages: () => {
    set({ messages: [] });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      messages: [],
      conversations: [],
      selectedConversation: null,
      currentAgentId: null,
      isLoading: false,
      isSending: false,
      isCreating: false,
      error: null,
    });
  },
})); 