import { create } from 'zustand';

export type SmartChatMessage = {
  sender: 'user' | 'agent';
  text: string;
  timestamp?: number;
  id?: string;
  hasActiveButtons?: boolean;
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

  // Button state management
  setMessageButtonsActive: (messageId: string) => void;
  deactivateAllButtons: () => void;
  deactivatePreviousButtons: () => void;
}

// Factory function to create agent-specific stores (no longer persists to localStorage)
// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const createSmartChatStore = (_agentId: string) => {
  return create<SmartChatState>()((set, get) => ({
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

    // Button state management methods
    setMessageButtonsActive: (messageId) =>
      set((state) => ({
        messages: state.messages.map((msg) => ({
          ...msg,
          hasActiveButtons: msg.id === messageId,
        })),
      })),
    deactivateAllButtons: () =>
      set((state) => ({
        messages: state.messages.map((msg) => ({
          ...msg,
          hasActiveButtons: false,
        })),
      })),
    deactivatePreviousButtons: () =>
      set((state) => {
        // Find the latest agent message with buttons
        const agentMessages = state.messages.filter((msg) => msg.sender === 'agent');
        const latestAgentMessage = agentMessages[agentMessages.length - 1];

        return {
          messages: state.messages.map((msg) => ({
            ...msg,
            hasActiveButtons: msg.id === latestAgentMessage?.id && msg.sender === 'agent',
          })),
        };
      }),
  }));
};

// Default store for backward compatibility (no longer persists to localStorage)
export const useSmartChatStore = create<SmartChatState>()((set, get) => ({
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

  // Button state management methods
  setMessageButtonsActive: (messageId) =>
    set((state) => ({
      messages: state.messages.map((msg) => ({
        ...msg,
        hasActiveButtons: msg.id === messageId,
      })),
    })),
  deactivateAllButtons: () =>
    set((state) => ({
      messages: state.messages.map((msg) => ({
        ...msg,
        hasActiveButtons: false,
      })),
    })),
  deactivatePreviousButtons: () =>
    set((state) => {
      // Find the latest agent message with buttons
      const agentMessages = state.messages.filter((msg) => msg.sender === 'agent');
      const latestAgentMessage = agentMessages[agentMessages.length - 1];

      return {
        messages: state.messages.map((msg) => ({
          ...msg,
          hasActiveButtons: msg.id === latestAgentMessage?.id && msg.sender === 'agent',
        })),
      };
    }),
}));
