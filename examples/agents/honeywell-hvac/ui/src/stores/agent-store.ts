// Stub stores for HVAC demo UI
// These stores are referenced in tests but don't exist in this standalone demo

export const useAgentStore = () => ({
  fetchAgent: async (_id?: number) => {},
  fetchAgents: async () => {},
  selectedAgent: null,
  agents: [],
  isLoading: false,
  error: null,
  createAgent: async () => {},
  updateAgent: async () => {},
  deleteAgent: async () => {},
  setSelectedAgent: () => {},
  setError: () => {},
  clearError: () => {},
  reset: () => {},
  getState: () => ({
    fetchAgent: async () => {},
    selectedAgent: null,
    agents: [],
  }),
});

export const usePoetStore = () => ({});
export const useTopicStore = () => ({});
export const useDocumentStore = () => ({});
export const useKnowledgeStore = () => ({});
export const useChatStore = () => ({});
