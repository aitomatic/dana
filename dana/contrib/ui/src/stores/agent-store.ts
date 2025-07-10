import { create } from "zustand";
import type {
  AgentCreate,
  AgentFilters,
  AgentRead,
  AgentState,
} from "@/types/agent";
import { apiService } from "@/lib/api";
export type { AgentState } from "@/types/agent";

export const useAgentStore = create<AgentState>((set) => ({
  // State
  agents: [],
  selectedAgent: null,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null,
  total: 0,
  skip: 0,
  limit: 10,
  isCreateAgentDialogOpen: false,
  isEditAgentDialogOpen: false,
  isDeleteAgentDialogOpen: false,
  // Actions
  fetchAgents: async (filters?: AgentFilters) => {
    set({ isLoading: true, error: null });

    try {
      const agents = await apiService.getAgents(filters);
      set({
        agents,
        isLoading: false,
        total: agents.length,
        skip: filters?.skip || 0,
        limit: filters?.limit || 10,
      });
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch agents";
      set({
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  fetchAgent: async (agentId: number) => {
    set({ isLoading: true, error: null });

    try {
      const agent = await apiService.getAgent(agentId);
      set({
        selectedAgent: agent,
        isLoading: false,
      });
      return agent;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch agent";
      set({
        isLoading: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  createAgent: async (agent: AgentCreate) => {
    set({ isCreating: true, error: null });

    try {
      const newAgent = await apiService.createAgent(agent);
      set((state) => ({
        agents: [...state.agents, newAgent],
        isCreating: false,
      }));
      return newAgent;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to create agent";
      set({
        isCreating: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  updateAgent: async (agentId: number, agent: AgentCreate) => {
    set({ isUpdating: true, error: null });

    try {
      const updatedAgent = await apiService.updateAgent(agentId, agent);
      set((state) => ({
        agents: state.agents.map((a) => (a.id === agentId ? updatedAgent : a)),
        selectedAgent:
          state.selectedAgent?.id === agentId
            ? updatedAgent
            : state.selectedAgent,
        isUpdating: false,
      }));
      return updatedAgent;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to update agent";
      set({
        isUpdating: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  deleteAgent: async (agentId: number) => {
    set({ isDeleting: true, error: null });

    try {
      await apiService.deleteAgent(agentId);
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== agentId),
        selectedAgent:
          state.selectedAgent?.id === agentId ? null : state.selectedAgent,
        isDeleting: false,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to delete agent";
      set({
        isDeleting: false,
        error: errorMessage,
      });
      throw error;
    }
  },

  setSelectedAgent: (agent: AgentRead | null) => {
    set({ selectedAgent: agent });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  clearError: () => {
    set({ error: null });
  },
  // Dialog Actions
  openCreateAgentDialog: () => set({ isCreateAgentDialogOpen: true }),
  closeCreateAgentDialog: () => set({ isCreateAgentDialogOpen: false }),
  openEditAgentDialog: (agent: AgentRead) =>
    set({
      isEditAgentDialogOpen: true,
      selectedAgent: agent,
    }),
  closeEditAgentDialog: () =>
    set({
      isEditAgentDialogOpen: false,
      selectedAgent: null,
    }),
  openDeleteAgentDialog: (agent: AgentRead) =>
    set({
      isDeleteAgentDialogOpen: true,
      selectedAgent: agent,
    }),
  closeDeleteAgentDialog: () =>
    set({
      isDeleteAgentDialogOpen: false,
      selectedAgent: null,
    }),

  reset: () => {
    set({
      agents: [],
      selectedAgent: null,
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isDeleting: false,
      error: null,
      total: 0,
      skip: 0,
      limit: 10,
    });
  },
}));
