import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type SmartChatMessage = {
  sender: 'user' | 'agent';
  text: string;
  timestamp?: number;
  id?: string;
};

interface SmartChatState {
  messages: SmartChatMessage[];
  addMessage: (msg: SmartChatMessage) => void;
  removeMessage: (index: number) => void;
  removeMessageById: (id: string) => void;
  clearMessages: () => void;
  setMessages: (msgs: SmartChatMessage[]) => void;
  updateMessage: (index: number, msg: Partial<SmartChatMessage>) => void;
  getMessageCount: () => number;
}

// Factory function to create agent-specific stores
export const createSmartChatStore = (agentId: string) => {
  return create<SmartChatState>()(
    persist(
      (set, get) => ({
        messages: [],
        addMessage: (msg) =>
          set((state) => {
            const messageWithId = {
              ...msg,
              id: msg.id || `${Date.now()}-${Math.random()}`,
              timestamp: msg.timestamp || Date.now(),
            };
            return {
              messages: [...state.messages, messageWithId],
            };
          }),
        removeMessage: (index) =>
          set((state) => ({
            messages: state.messages.filter((_, i) => i !== index),
          })),
        removeMessageById: (id) =>
          set((state) => ({
            messages: state.messages.filter((msg) => msg.id !== id),
          })),
        clearMessages: () => set({ messages: [] }),
        setMessages: (msgs) =>
          set({
            messages: msgs.map((msg) => ({
              ...msg,
              id: msg.id || `${Date.now()}-${Math.random()}`,
              timestamp: msg.timestamp || Date.now(),
            })),
          }),
        updateMessage: (index, msg) =>
          set((state) => ({
            messages: state.messages.map((m, i) => (i === index ? { ...m, ...msg } : m)),
          })),
        getMessageCount: () => get().messages.length,
      }),
      {
        name: `smart-chat-storage-${agentId}`,
        partialize: (state) => ({ messages: state.messages }),
      },
    ),
  );
};

// Default store for backward compatibility (will be deprecated)
export const useSmartChatStore = create<SmartChatState>()(
  persist(
    (set, get) => ({
      messages: [],
      addMessage: (msg) =>
        set((state) => {
          const messageWithId = {
            ...msg,
            id: msg.id || `${Date.now()}-${Math.random()}`,
            timestamp: msg.timestamp || Date.now(),
          };
          return {
            messages: [...state.messages, messageWithId],
          };
        }),
      removeMessage: (index) =>
        set((state) => ({
          messages: state.messages.filter((_, i) => i !== index),
        })),
      removeMessageById: (id) =>
        set((state) => ({
          messages: state.messages.filter((msg) => msg.id !== id),
        })),
      clearMessages: () => set({ messages: [] }),
      setMessages: (msgs) =>
        set({
          messages: msgs.map((msg) => ({
            ...msg,
            id: msg.id || `${Date.now()}-${Math.random()}`,
            timestamp: msg.timestamp || Date.now(),
          })),
        }),
      updateMessage: (index, msg) =>
        set((state) => ({
          messages: state.messages.map((m, i) => (i === index ? { ...m, ...msg } : m)),
        })),
      getMessageCount: () => get().messages.length,
    }),
    {
      name: 'smart-chat-storage',
      partialize: (state) => ({ messages: state.messages }),
    },
  ),
);

// Utility function to clear smart-chat-storage for a specific agent
export const clearSmartChatStorageForAgent = (agentId: string) => {
  try {
    // Clear from localStorage
    const storageKey = `smart-chat-storage-${agentId}`;
    localStorage.removeItem(storageKey);

    // Also clear any existing store instance
    const agentStore = createSmartChatStore(agentId);
    agentStore.getState().clearMessages();

    console.log(`[Storage Utility] Cleared smart-chat-storage for agent ${agentId}`);
    return true;
  } catch (error) {
    console.warn(`[Storage Utility] Failed to clear storage for agent ${agentId}:`, error);
    return false;
  }
};
