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
      set((state) => {
        // Only update messages where hasActiveButtons value actually changes
        let hasChanges = false;
        const updatedMessages = state.messages.map((msg) => {
          const newHasActiveButtons = msg.id === messageId;
          // Only create new object if the value actually changed
          if (msg.hasActiveButtons !== newHasActiveButtons) {
            hasChanges = true;
            return { ...msg, hasActiveButtons: newHasActiveButtons };
          }
          // Return same object reference if no change
          return msg;
        });
        // Only update state if there were actual changes
        return hasChanges ? { messages: updatedMessages } : state;
      }),
    deactivateAllButtons: () =>
      set((state) => {
        // Only update messages that currently have hasActiveButtons: true
        let hasChanges = false;
        const updatedMessages = state.messages.map((msg) => {
          // Only create new object if hasActiveButtons is currently true
          if (msg.hasActiveButtons === true) {
            hasChanges = true;
            return { ...msg, hasActiveButtons: false };
          }
          // Return same object reference if already false
          return msg;
        });
        // Only update state if there were actual changes
        return hasChanges ? { messages: updatedMessages } : state;
      }),
    deactivatePreviousButtons: () =>
      set((state) => {
        // Find the latest agent message with buttons
        const agentMessages = state.messages.filter((msg) => msg.sender === 'agent');
        const latestAgentMessage = agentMessages[agentMessages.length - 1];
        const targetMessageId = latestAgentMessage?.id;

        // Only update messages where hasActiveButtons value actually changes
        let hasChanges = false;
        const updatedMessages = state.messages.map((msg) => {
          const newHasActiveButtons = msg.id === targetMessageId && msg.sender === 'agent';
          // Only create new object if the value actually changed
          if (msg.hasActiveButtons !== newHasActiveButtons) {
            hasChanges = true;
            return { ...msg, hasActiveButtons: newHasActiveButtons };
          }
          // Return same object reference if no change
          return msg;
        });
        // Only update state if there were actual changes
        return hasChanges ? { messages: updatedMessages } : state;
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
    set((state) => {
      // Only update messages where hasActiveButtons value actually changes
      let hasChanges = false;
      const updatedMessages = state.messages.map((msg) => {
        const newHasActiveButtons = msg.id === messageId;
        // Only create new object if the value actually changed
        if (msg.hasActiveButtons !== newHasActiveButtons) {
          hasChanges = true;
          return { ...msg, hasActiveButtons: newHasActiveButtons };
        }
        // Return same object reference if no change
        return msg;
      });
      // Only update state if there were actual changes
      return hasChanges ? { messages: updatedMessages } : state;
    }),
  deactivateAllButtons: () =>
    set((state) => {
      // Only update messages that currently have hasActiveButtons: true
      let hasChanges = false;
      const updatedMessages = state.messages.map((msg) => {
        // Only create new object if hasActiveButtons is currently true
        if (msg.hasActiveButtons === true) {
          hasChanges = true;
          return { ...msg, hasActiveButtons: false };
        }
        // Return same object reference if already false
        return msg;
      });
      // Only update state if there were actual changes
      return hasChanges ? { messages: updatedMessages } : state;
    }),
  deactivatePreviousButtons: () =>
    set((state) => {
      // Find the latest agent message with buttons
      const agentMessages = state.messages.filter((msg) => msg.sender === 'agent');
      const latestAgentMessage = agentMessages[agentMessages.length - 1];
      const targetMessageId = latestAgentMessage?.id;

      // Only update messages where hasActiveButtons value actually changes
      let hasChanges = false;
      const updatedMessages = state.messages.map((msg) => {
        const newHasActiveButtons = msg.id === targetMessageId && msg.sender === 'agent';
        // Only create new object if the value actually changed
        if (msg.hasActiveButtons !== newHasActiveButtons) {
          hasChanges = true;
          return { ...msg, hasActiveButtons: newHasActiveButtons };
        }
        // Return same object reference if no change
        return msg;
      });
      // Only update state if there were actual changes
      return hasChanges ? { messages: updatedMessages } : state;
    }),
}));
