import { create } from 'zustand';
import type { AgentCapabilities, MultiFileProject } from '@/lib/api';

export interface BuildingAgent {
  // Basic agent info
  id?: number;
  name: string;
  description: string;

  // Generation phase info
  phase: 'description' | 'code_generation';
  ready_for_code_generation: boolean;

  // Agent data for API calls
  agent_data?: any;

  // Generated content
  dana_code?: string;
  multi_file_project?: MultiFileProject;
  capabilities?: AgentCapabilities;

  // File paths
  folder_path?: string;
  auto_stored_files?: string[];

  // Conversation context
  conversation_context: Array<{
    role: 'user' | 'assistant';
    content: string;
  }>;

  // Metadata
  created_at?: string;
  updated_at?: string;
}

export interface AgentBuildingState {
  // Current building agent
  currentAgent: BuildingAgent | null;

  // Loading states
  isGenerating: boolean;
  isAnalyzing: boolean;

  // Error state
  error: string | null;

  // Actions
  initializeAgent: (name: string, description: string) => void;
  updateAgentData: (updates: Partial<BuildingAgent>) => void;
  setPhase: (phase: 'description' | 'code_generation') => void;
  setReadyForCodeGeneration: (ready: boolean) => void;
  setAgentId: (id: number) => void;
  setAgentFolder: (folder: string) => void;
  setDanaCode: (code: string) => void;
  setMultiFileProject: (project: MultiFileProject) => void;
  setCapabilities: (capabilities: AgentCapabilities) => void;
  addConversationMessage: (role: 'user' | 'assistant', content: string) => void;
  setGenerating: (generating: boolean) => void;
  setAnalyzing: (analyzing: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useAgentBuildingStore = create<AgentBuildingState>((set) => ({
  // State
  currentAgent: null,
  isGenerating: false,
  isAnalyzing: false,
  error: null,

  // Actions
  initializeAgent: (name: string, description: string) => {
    const newAgent: BuildingAgent = {
      name,
      description,
      phase: 'description',
      ready_for_code_generation: false,
      conversation_context: [],
      created_at: new Date().toISOString(),
    };

    set({
      currentAgent: newAgent,
      error: null
    });
  },

  updateAgentData: (updates: Partial<BuildingAgent>) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, ...updates, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setPhase: (phase: 'description' | 'code_generation') => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, phase, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setReadyForCodeGeneration: (ready: boolean) => {
    console.log('🏪 Zustand Store: Setting ready_for_code_generation to:', ready);
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, ready_for_code_generation: ready, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setAgentId: (id: number) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, id, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setAgentFolder: (folder: string) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, folder_path: folder, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setDanaCode: (code: string) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, dana_code: code, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setMultiFileProject: (project: MultiFileProject) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, multi_file_project: project, updated_at: new Date().toISOString() }
        : null
    }));
  },

  setCapabilities: (capabilities: AgentCapabilities) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? { ...state.currentAgent, capabilities, updated_at: new Date().toISOString() }
        : null
    }));
  },

  addConversationMessage: (role: 'user' | 'assistant', content: string) => {
    set((state) => ({
      currentAgent: state.currentAgent
        ? {
          ...state.currentAgent,
          conversation_context: [...state.currentAgent.conversation_context, { role, content }],
          updated_at: new Date().toISOString()
        }
        : null
    }));
  },

  setGenerating: (generating: boolean) => {
    set({ isGenerating: generating });
  },

  setAnalyzing: (analyzing: boolean) => {
    set({ isAnalyzing: analyzing });
  },

  setError: (error: string | null) => {
    set({ error });
  },

  reset: () => {
    set({
      currentAgent: null,
      isGenerating: false,
      isAnalyzing: false,
      error: null,
    });
  },
})); 