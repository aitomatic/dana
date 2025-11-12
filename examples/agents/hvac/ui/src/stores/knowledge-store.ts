// Stub stores for HVAC demo UI
export const useKnowledgeStore = () => ({
  setTreeUpdateCallback: (_callback: () => void) => {},
  getState: () => ({
    setTreeUpdateCallback: () => {},
  }),
});
