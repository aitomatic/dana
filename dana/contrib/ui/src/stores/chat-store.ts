import { create } from 'zustand';

// Type definitions for chat
export type Message = {
  id: number;
  conversationId: number;
  sender: 'user' | 'agent';
  content: string;
  createdAt: string;
};

export type Conversation = {
  id: number;
  title: string;
  createdAt: string;
  updatedAt: string;
};

interface ChatState {
  conversations: Conversation[];
  messages: Record<number, Message[]>; // conversationId -> messages
  currentConversationId: number | null;
  loading: boolean;
  error: string | null;
  // Actions
  setConversations: (conversations: Conversation[]) => void;
  setMessages: (conversationId: number, messages: Message[]) => void;
  setCurrentConversation: (conversationId: number | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  conversations: [],
  messages: {},
  currentConversationId: null,
  loading: false,
  error: null,
  setConversations: (conversations) => set({ conversations }),
  setMessages: (conversationId, messages) => set((state) => ({
    messages: { ...state.messages, [conversationId]: messages },
  })),
  setCurrentConversation: (conversationId) => set({ currentConversationId: conversationId }),
  setLoading: (loading) => set({ loading }),
  setError: (error) => set({ error }),
  clearError: () => set({ error: null }),
})); 