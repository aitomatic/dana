import { create } from 'zustand';

export type SmartChatMessage = { sender: 'user' | 'agent'; text: string };

interface SmartChatState {
  messages: SmartChatMessage[];
  addMessage: (msg: SmartChatMessage) => void;
  clearMessages: () => void;
}

export const useSmartChatStore = create<SmartChatState>((set) => ({
  messages: [],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  clearMessages: () => set({ messages: [] }),
}));
