import { create } from 'zustand';
import type { Agent, DanaAgentForm } from '@/types/agent';

export interface AgentState {
  // Agent Data
  agents: Agent[];
  selectedAgent: Agent | null;

  // Dialog States
  isCreateAgentDialogOpen: boolean;
  isEditAgentDialogOpen: boolean;
  isDeleteAgentDialogOpen: boolean;

  // Loading States
  isLoadingAgents: boolean;
  isCreatingAgent: boolean;
  isUpdatingAgent: boolean;
  isDeletingAgent: boolean;

  // Error States
  error: string | null;

  // Actions
  // Dialog Actions
  openCreateAgentDialog: () => void;
  closeCreateAgentDialog: () => void;
  openEditAgentDialog: (agent: Agent) => void;
  closeEditAgentDialog: () => void;
  openDeleteAgentDialog: (agent: Agent) => void;
  closeDeleteAgentDialog: () => void;

  // Agent Actions
  setSelectedAgent: (agent: Agent | null) => void;
  clearError: () => void;
  reset: () => void;
}

export const useAgentStore = create<AgentState>((set, get) => ({
  // Initial State
  agents: [],
  selectedAgent: null,
  isCreateAgentDialogOpen: false,
  isEditAgentDialogOpen: false,
  isDeleteAgentDialogOpen: false,
  isLoadingAgents: false,
  isCreatingAgent: false,
  isUpdatingAgent: false,
  isDeletingAgent: false,
  error: null,

  // Dialog Actions
  openCreateAgentDialog: () => set({ isCreateAgentDialogOpen: true }),
  closeCreateAgentDialog: () => set({ isCreateAgentDialogOpen: false }),
  openEditAgentDialog: (agent: Agent) => set({
    isEditAgentDialogOpen: true,
    selectedAgent: agent
  }),
  closeEditAgentDialog: () => set({
    isEditAgentDialogOpen: false,
    selectedAgent: null
  }),
  openDeleteAgentDialog: (agent: Agent) => set({
    isDeleteAgentDialogOpen: true,
    selectedAgent: agent
  }),
  closeDeleteAgentDialog: () => set({
    isDeleteAgentDialogOpen: false,
    selectedAgent: null
  }),

  // Agent Actions
  setSelectedAgent: (agent: Agent | null) => set({ selectedAgent: agent }),
  clearError: () => set({ error: null }),
  reset: () => {
    set({
      agents: [],
      selectedAgent: null,
      isCreateAgentDialogOpen: false,
      isEditAgentDialogOpen: false,
      isDeleteAgentDialogOpen: false,
      isLoadingAgents: false,
      isCreatingAgent: false,
      isUpdatingAgent: false,
      isDeletingAgent: false,
      error: null,
    });
  },
}));
