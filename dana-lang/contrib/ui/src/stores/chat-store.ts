/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { ChatRequest, ChatResponse } from '@/lib/api';
import type {
  ConversationRead,
  ConversationWithMessages,
  ConversationCreate,
} from '@/types/conversation';
import type { MessageRead } from '@/types/conversation';

// Session-based conversation for prebuilt agents
export interface SessionConversation {
  id: string;
  agentId: string;
  title: string;
  messages: MessageRead[];
  created_at: string;
  updated_at: string;
}

export interface ChatStore {
  // State
  messages: MessageRead[];
  conversations: ConversationRead[];
  selectedConversation: ConversationWithMessages | null;
  currentAgentId: number | string | null; // Support both string and number agent IDs
  currentSessionId: string | null; // For prebuilt agent session tracking
  sessionConversations: SessionConversation[]; // Session-based conversations for prebuilt agents
  isLoading: boolean;
  isSending: boolean;
  isCreating: boolean;
  error: string | null;

  // Actions
  sendMessage: (
    message: string,
    agentId: number | string,
    conversationId?: number | string,
    websocketId?: string,
  ) => Promise<ChatResponse>;
  fetchConversations: (agentId: number) => Promise<void>; // Keep as number since only regular agents have conversations
  fetchConversation: (conversationId: number) => Promise<void>;
  createConversation: (conversation: ConversationCreate) => Promise<ConversationRead>;
  updateConversation: (
    conversationId: number,
    conversation: ConversationCreate,
  ) => Promise<ConversationRead>;
  deleteConversation: (conversationId: number) => Promise<void>;
  setCurrentAgentId: (agentId: number | string | null) => void;
  setSelectedConversation: (conversation: ConversationWithMessages | null) => void;

  // Session-based conversation methods for prebuilt agents
  loadSessionConversation: (sessionId: string, agentId: string) => void;
  createSessionConversation: (agentId: string) => string;
  saveSessionConversation: (sessionId: string, messages: MessageRead[]) => void;
  getSessionConversations: (agentId: string) => SessionConversation[];
  deleteSessionConversation: (sessionId: string) => void;

  clearMessages: () => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

// Session storage helpers
const SESSION_STORAGE_KEY = 'prebuilt_agent_conversations';

const saveToSessionStorage = (conversations: SessionConversation[]) => {
  try {
    sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(conversations));
  } catch (error) {
    console.warn('Failed to save to session storage:', error);
  }
};

const loadFromSessionStorage = (): SessionConversation[] => {
  try {
    const stored = sessionStorage.getItem(SESSION_STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  } catch (error) {
    console.warn('Failed to load from session storage:', error);
    return [];
  }
};

export const useChatStore = create<ChatStore>((set, get) => ({
  // Initial State
  messages: [],
  conversations: [],
  selectedConversation: null,
  currentAgentId: null,
  currentSessionId: null,
  sessionConversations: loadFromSessionStorage(),
  isLoading: false,
  isSending: false,
  isCreating: false,
  error: null,

  // Actions
  sendMessage: async (
    messageData: string | { message: string; role: string; files?: any[] },
    agentId: number | string,
    conversationId?: number | string,
    websocketId?: string,
  ) => {
    // Handle both string messages and message objects with files
    const message = typeof messageData === 'string' ? messageData : messageData.message;
    const files = typeof messageData === 'string' ? undefined : messageData.files;

    // Create message content that includes file information
    let messageContent = message;
    if (files && files.length > 0) {
      const fileList = files.map((f) => `📎 ${f.name}`).join('\n');
      messageContent = `${message}${message ? '\n\n' : ''}Attached files:\n${fileList}`;
    }

    // Immediately add user message to show it in the UI BEFORE setting isSending
    const { messages } = get();
    const tempUserMessage: MessageRead = {
      id: Date.now(), // Temporary ID
      // @ts-expect-error conversationId can be string or number
      conversation_id: conversationId || 0,
      sender: 'user',
      content: messageContent,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    set({
      messages: [...messages, tempUserMessage],
      isSending: true,
      error: null,
    });

    try {
      // For prebuilt agents with session IDs, don't send conversation_id to backend
      const isSessionConversation =
        typeof conversationId === 'string' && conversationId.startsWith('session_');

      // Handle conversation ID for request
      let requestConversationId: number | undefined;
      if (!isSessionConversation && conversationId) {
        // Only send conversation_id if it's a valid number and not a session conversation
        const numericId =
          typeof conversationId === 'string' ? parseInt(conversationId) : conversationId;
        requestConversationId = !isNaN(numericId) && numericId < 1000000000 ? numericId : undefined;
      }

      const request: ChatRequest = {
        message: messageContent,
        agent_id: agentId,
        conversation_id: requestConversationId,
        context: { user_id: 1 }, // TODO: Get from auth context
        websocket_id: websocketId,
      };

      const response = await apiService.chatWithAgent(request);

      // Update messages with the actual response
      // Handle both regular agents (conversation_id > 0) and prebuilt agents (conversation_id = 0)
      if (response.conversation_id !== null && response.conversation_id !== undefined) {
        const currentMessages = get().messages;

        // Update the last message (temporary user message) with proper IDs from response
        const updatedUserMessage: MessageRead = {
          ...currentMessages[currentMessages.length - 1], // Keep the existing user message
          id: response.message_id || Date.now() - 1, // Update with response ID
          conversation_id: response.conversation_id, // Update with proper conversation ID
        };

        // Create agent response message
        const agentMessage: MessageRead = {
          id: (response.message_id || Date.now()) + 1, // Ensure unique ID for agent message
          conversation_id: response.conversation_id,
          sender: 'agent',
          content: response.agent_response,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        };

        // Update messages: replace temp user message with updated one, add agent message
        const updatedMessages: MessageRead[] = [
          ...currentMessages.slice(0, -1), // All messages except the last (temp user message)
          updatedUserMessage, // Updated user message with proper IDs
          agentMessage, // New agent response
        ];

        set({
          messages: updatedMessages,
          isSending: false,
        });

        // For prebuilt agents (conversation_id = 0), save to session storage
        if (response.conversation_id === 0 && typeof agentId === 'string') {
          const currentSessionId = get().currentSessionId;
          if (currentSessionId) {
            get().saveSessionConversation(currentSessionId, updatedMessages);
          }
        }
      } else {
        set({ isSending: false });
      }

      return response;
    } catch (error) {
      // Remove the temporary user message on error
      const currentMessages = get().messages;
      set({
        messages: currentMessages.slice(0, -1),
        error: error instanceof Error ? error.message : 'Failed to send message',
        isSending: false,
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

      if (conversation.messages && Array.isArray(conversation.messages)) {
        set({
          selectedConversation: conversation,
          messages: conversation.messages,
          isLoading: false,
        });
      } else {
        set({
          selectedConversation: conversation,
          messages: [],
          isLoading: false,
        });
      }
    } catch (error) {
      // Check if it's a 404 error (conversation doesn't exist yet)
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        if (axiosError.response?.status === 404) {
          // Don't show error for 404, just set empty state
          set({
            selectedConversation: null,
            messages: [],
            isLoading: false,
            error: null, // Don't show error for missing conversations
          });
          return;
        }
      }

      // For other errors, show the error message
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch conversation';
      console.error('Error fetching conversation:', errorMessage);
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
      // Only create conversations for numeric agent IDs (regular agents)
      const currentAgentId = get().currentAgentId;
      if (typeof currentAgentId === 'string') {
        throw new Error('Cannot create conversations for prebuilt agents');
      }

      const conversationWithAgent = {
        ...conversation,
        agent_id: conversation.agent_id || currentAgentId || 1,
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
        conversations: conversations.map((c) =>
          c.id === conversationId ? updatedConversation : c,
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
        conversations: conversations.filter((c) => c.id !== conversationId),
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

  setCurrentAgentId: (agentId: number | string | null) => {
    set({ currentAgentId: agentId });
  },

  setSelectedConversation: (conversation: ConversationWithMessages | null) => {
    set({
      selectedConversation: conversation,
      messages: conversation?.messages || [],
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

  // Session-based conversation methods for prebuilt agents
  loadSessionConversation: (sessionId: string, agentId: string) => {
    const sessionConversations = get().sessionConversations;
    const sessionConv = sessionConversations.find(
      (conv) => conv.id === sessionId && conv.agentId === agentId,
    );

    if (sessionConv) {
      set({
        messages: sessionConv.messages,
        currentSessionId: sessionId,
      });
    } else {
      // Create new session conversation if not found
      const newSessionId = get().createSessionConversation(agentId);
      set({ currentSessionId: newSessionId });
    }
  },

  createSessionConversation: (agentId: string): string => {
    const sessionId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`;
    const newConversation: SessionConversation = {
      id: sessionId,
      agentId,
      title: 'New chat',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    const sessionConversations = [...get().sessionConversations, newConversation];
    set({ sessionConversations, currentSessionId: sessionId });
    saveToSessionStorage(sessionConversations);

    return sessionId;
  },

  saveSessionConversation: (sessionId: string, messages: MessageRead[]) => {
    const sessionConversations = get().sessionConversations.map((conv) =>
      conv.id === sessionId
        ? {
            ...conv,
            messages,
            title: messages.length > 0 ? messages[0].content.slice(0, 50) + '...' : 'New chat',
            updated_at: new Date().toISOString(),
          }
        : conv,
    );

    set({ sessionConversations });
    saveToSessionStorage(sessionConversations);
  },

  getSessionConversations: (agentId: string): SessionConversation[] => {
    return get().sessionConversations.filter((conv) => conv.agentId === agentId);
  },

  deleteSessionConversation: (sessionId: string) => {
    const sessionConversations = get().sessionConversations.filter((conv) => conv.id !== sessionId);
    set({ sessionConversations });
    saveToSessionStorage(sessionConversations);

    // If we deleted the current session, clear messages
    if (get().currentSessionId === sessionId) {
      set({ currentSessionId: null, messages: [] });
    }
  },

  reset: () => {
    set({
      messages: [],
      conversations: [],
      selectedConversation: null,
      currentAgentId: null,
      currentSessionId: null,
      sessionConversations: [],
      isLoading: false,
      isSending: false,
      isCreating: false,
      error: null,
    });
    // Clear session storage as well
    sessionStorage.removeItem(SESSION_STORAGE_KEY);
  },
}));
