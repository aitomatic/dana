import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { TopicRead, TopicCreate, TopicFilters, TopicState } from '@/types/topic';

export interface TopicStore extends TopicState {
  // Actions
  // Topic CRUD Operations
  fetchTopics: (filters?: TopicFilters) => Promise<void>;
  fetchTopic: (topicId: number) => Promise<void>;
  createTopic: (topic: TopicCreate) => Promise<void>;
  updateTopic: (topicId: number, topic: TopicCreate) => Promise<void>;
  deleteTopic: (topicId: number) => Promise<void>;

  // Selection and UI Actions
  setSelectedTopic: (topic: TopicRead | null) => void;
  clearError: () => void;
  reset: () => void;
}

export const useTopicStore = create<TopicStore>((set) => ({
  // Initial State
  topics: [],
  selectedTopic: null,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null,
  total: 0,
  skip: 0,
  limit: 100,

  // Actions
  fetchTopics: async (filters?: TopicFilters) => {
    set({ isLoading: true, error: null });

    try {
      const topics = await apiService.getTopics(filters);
      set({
        topics,
        isLoading: false,
        skip: filters?.skip || 0,
        limit: filters?.limit || 100,
        total: topics.length, // Note: API doesn't return total count, using array length
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch topics';
      set({
        topics: [],
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  fetchTopic: async (topicId: number) => {
    set({ isLoading: true, error: null });

    try {
      const topic = await apiService.getTopic(topicId);
      set({
        selectedTopic: topic,
        isLoading: false,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch topic';
      set({
        selectedTopic: null,
        isLoading: false,
        error: errorMessage,
      });
    }
  },

  createTopic: async (topic: TopicCreate) => {
    set({ isCreating: true, error: null });

    try {
      const newTopic = await apiService.createTopic(topic);
      set((state) => ({
        topics: [...state.topics, newTopic],
        isCreating: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to create topic';
      set({
        isCreating: false,
        error: errorMessage,
      });
    }
  },

  updateTopic: async (topicId: number, topic: TopicCreate) => {
    set({ isUpdating: true, error: null });

    try {
      const updatedTopic = await apiService.updateTopic(topicId, topic);
      set((state) => ({
        topics: state.topics.map((t) => (t.id === topicId ? updatedTopic : t)),
        selectedTopic: state.selectedTopic?.id === topicId ? updatedTopic : state.selectedTopic,
        isUpdating: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to update topic';
      set({
        isUpdating: false,
        error: errorMessage,
      });
    }
  },

  deleteTopic: async (topicId: number) => {
    set({ isDeleting: true, error: null });

    try {
      await apiService.deleteTopic(topicId);
      set((state) => ({
        topics: state.topics.filter((t) => t.id !== topicId),
        selectedTopic: state.selectedTopic?.id === topicId ? null : state.selectedTopic,
        isDeleting: false,
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to delete topic';
      set({
        isDeleting: false,
        error: errorMessage,
      });
    }
  },

  setSelectedTopic: (topic: TopicRead | null) => {
    set({ selectedTopic: topic });
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      topics: [],
      selectedTopic: null,
      isLoading: false,
      isCreating: false,
      isUpdating: false,
      isDeleting: false,
      error: null,
      total: 0,
      skip: 0,
      limit: 100,
    });
  },
}));
