import { create } from 'zustand';

interface AgentStore {
  isOpenCreateAgentDialog: boolean;
  setIsOpenCreateAgentDialog: (isOpen: boolean) => void;
}

export const useAgentStore = create<AgentStore>(set => ({
  isOpenCreateAgentDialog: false,
  setIsOpenCreateAgentDialog: isOpen =>
    set({ isOpenCreateAgentDialog: isOpen }),
}));
