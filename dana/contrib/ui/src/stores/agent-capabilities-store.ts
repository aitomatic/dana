import { create } from 'zustand';
import type { AgentCapabilities } from '@/lib/api';

export interface AgentCapabilitiesState {
  // Current capabilities
  capabilities: AgentCapabilities | null;

  // Loading state
  isLoading: boolean;

  // Error state
  error: string | null;

  // Actions
  setCapabilities: (capabilities: AgentCapabilities | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearCapabilities: () => void;
  reset: () => void;
}

export const useAgentCapabilitiesStore = create<AgentCapabilitiesState>((set) => ({
  // State
  capabilities: null,
  isLoading: false,
  error: null,

  // Actions
  setCapabilities: (capabilities: AgentCapabilities | null) => {
    set({ capabilities, error: null });
  },

  setLoading: (loading: boolean) => {
    set({ isLoading: loading });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  clearCapabilities: () => {
    set({ capabilities: null, error: null });
  },

  reset: () => {
    set({
      capabilities: null,
      isLoading: false,
      error: null,
    });
  },
}));
