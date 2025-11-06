// Stub stores for HVAC demo UI
export const useTopicStore = () => ({
  fetchTopics: async () => {},
  fetchTopic: async () => {},
  createTopic: async () => {},
  updateTopic: async () => {},
  deleteTopic: async () => {},
  topics: [],
  selectedTopic: null,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null,
  setSelectedTopic: () => {},
  clearError: () => {},
});
