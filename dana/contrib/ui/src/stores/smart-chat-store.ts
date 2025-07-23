import { create } from 'zustand';

export type SmartChatMessage = { sender: 'user' | 'agent'; text: string };

interface SmartChatState {
  messages: SmartChatMessage[];
  addMessage: (msg: SmartChatMessage) => void;
  removeMessage: (index: number) => void;
  clearMessages: () => void;
  setMessages: (msgs: SmartChatMessage[]) => void;
}

export const useSmartChatStore = create<SmartChatState>((set) => ({
  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  removeMessage: (index) => set((state) => ({
    messages: state.messages.filter((_, i) => i !== index)
  })),
  clearMessages: () => set({ messages: [] }),
  setMessages: (msgs) => set({ messages: msgs }),
}));
