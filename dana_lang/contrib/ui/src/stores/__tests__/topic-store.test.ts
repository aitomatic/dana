import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTopicStore } from '../topic-store';
import type { TopicRead, TopicCreate, TopicFilters } from '@/types/topic';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    getTopics: vi.fn(),
    getTopic: vi.fn(),
    createTopic: vi.fn(),
    updateTopic: vi.fn(),
    deleteTopic: vi.fn(),
  },
}));

import { apiService } from '@/lib/api';

describe('Topic Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the store state
    useTopicStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useTopicStore.getState();

      expect(state.topics).toEqual([]);
      expect(state.selectedTopic).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.isCreating).toBe(false);
      expect(state.isUpdating).toBe(false);
      expect(state.isDeleting).toBe(false);
      expect(state.error).toBeNull();
      expect(state.total).toBe(0);
      expect(state.skip).toBe(0);
      expect(state.limit).toBe(100);
    });
  });

  describe('fetchTopics', () => {
    it('should fetch topics successfully', async () => {
      const mockTopics: TopicRead[] = [
        {
          id: 1,
          name: 'Test Topic 1',
          description: 'A test topic',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          name: 'Test Topic 2',
          description: 'Another test topic',
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ];

      (apiService.getTopics as any).mockResolvedValue(mockTopics);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.fetchTopics();
      });

      expect(apiService.getTopics).toHaveBeenCalledWith(undefined);
      expect(result.current.topics).toEqual(mockTopics);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.total).toBe(2);
    });

    it('should fetch topics with filters', async () => {
      const mockTopics: TopicRead[] = [
        {
          id: 1,
          name: 'Filtered Topic',
          description: 'A filtered topic',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];

      const filters: TopicFilters = {
        skip: 0,
        limit: 10,
        search: 'Filtered',
      };

      (apiService.getTopics as any).mockResolvedValue(mockTopics);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.fetchTopics(filters);
      });

      expect(apiService.getTopics).toHaveBeenCalledWith(filters);
      expect(result.current.topics).toEqual(mockTopics);
      expect(result.current.skip).toBe(0);
      expect(result.current.limit).toBe(10);
    });

    it('should handle fetch topics error', async () => {
      const error = new Error('Failed to fetch topics');
      (apiService.getTopics as any).mockRejectedValue(error);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.fetchTopics();
      });

      expect(result.current.topics).toEqual([]);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Failed to fetch topics');
    });
  });

  describe('fetchTopic', () => {
    it('should fetch single topic successfully', async () => {
      const mockTopic: TopicRead = {
        id: 1,
        name: 'Test Topic',
        description: 'A test topic',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiService.getTopic as any).mockResolvedValue(mockTopic);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.fetchTopic(1);
      });

      expect(apiService.getTopic).toHaveBeenCalledWith(1);
      expect(result.current.selectedTopic).toEqual(mockTopic);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle fetch topic error', async () => {
      const error = new Error('Failed to fetch topic');
      (apiService.getTopic as any).mockRejectedValue(error);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.fetchTopic(1);
      });

      expect(result.current.selectedTopic).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe('Failed to fetch topic');
    });
  });

  describe('createTopic', () => {
    it('should create topic successfully', async () => {
      const newTopic: TopicCreate = {
        name: 'New Topic',
        description: 'A new topic',
      };

      const createdTopic: TopicRead = {
        id: 3,
        ...newTopic,
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      };

      (apiService.createTopic as any).mockResolvedValue(createdTopic);

      const { result } = renderHook(() => useTopicStore());

      // Set initial topics
      act(() => {
        result.current.topics = [
          {
            id: 1,
            name: 'Existing Topic',
            description: 'An existing topic',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];
      });

      await act(async () => {
        await result.current.createTopic(newTopic);
      });

      expect(apiService.createTopic).toHaveBeenCalledWith(newTopic);
      expect(result.current.topics).toHaveLength(2);
      expect(result.current.topics).toContainEqual(createdTopic);
      expect(result.current.isCreating).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle create topic error', async () => {
      const newTopic: TopicCreate = {
        name: 'New Topic',
        description: 'A new topic',
      };

      const error = new Error('Failed to create topic');
      (apiService.createTopic as any).mockRejectedValue(error);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.createTopic(newTopic);
      });

      expect(result.current.isCreating).toBe(false);
      expect(result.current.error).toBe('Failed to create topic');
    });
  });

  describe('updateTopic', () => {
    it('should update topic successfully', async () => {
      const topicId = 1;
      const updateData: TopicCreate = {
        name: 'Updated Topic',
        description: 'An updated topic',
      };

      const updatedTopic: TopicRead = {
        id: topicId,
        ...updateData,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      (apiService.updateTopic as any).mockResolvedValue(updatedTopic);

      const { result } = renderHook(() => useTopicStore());

      // Set initial topics
      act(() => {
        result.current.topics = [
          {
            id: topicId,
            name: 'Original Topic',
            description: 'Original description',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];
        result.current.selectedTopic = result.current.topics[0];
      });

      await act(async () => {
        await result.current.updateTopic(topicId, updateData);
      });

      expect(apiService.updateTopic).toHaveBeenCalledWith(topicId, updateData);
      expect(result.current.topics[0]).toEqual(updatedTopic);
      expect(result.current.selectedTopic).toEqual(updatedTopic);
      expect(result.current.isUpdating).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle update topic error', async () => {
      const topicId = 1;
      const updateData: TopicCreate = {
        name: 'Updated Topic',
        description: 'An updated topic',
      };

      const error = new Error('Failed to update topic');
      (apiService.updateTopic as any).mockRejectedValue(error);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.updateTopic(topicId, updateData);
      });

      expect(result.current.isUpdating).toBe(false);
      expect(result.current.error).toBe('Failed to update topic');
    });
  });

  describe('deleteTopic', () => {
    it('should delete topic successfully', async () => {
      const topicId = 1;

      (apiService.deleteTopic as any).mockResolvedValue({ message: 'Topic deleted' });

      const { result } = renderHook(() => useTopicStore());

      // Set initial topics
      act(() => {
        result.current.topics = [
          {
            id: topicId,
            name: 'Topic to Delete',
            description: 'This topic will be deleted',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            name: 'Topic to Keep',
            description: 'This topic will remain',
            created_at: '2024-01-02T00:00:00Z',
            updated_at: '2024-01-02T00:00:00Z',
          },
        ];
        result.current.selectedTopic = result.current.topics[0];
      });

      await act(async () => {
        await result.current.deleteTopic(topicId);
      });

      expect(apiService.deleteTopic).toHaveBeenCalledWith(topicId);
      expect(result.current.topics).toHaveLength(1);
      expect(result.current.topics[0].id).toBe(2);
      expect(result.current.selectedTopic).toBeNull();
      expect(result.current.isDeleting).toBe(false);
      expect(result.current.error).toBeNull();
    });

    it('should handle delete topic error', async () => {
      const topicId = 1;

      const error = new Error('Failed to delete topic');
      (apiService.deleteTopic as any).mockRejectedValue(error);

      const { result } = renderHook(() => useTopicStore());

      await act(async () => {
        await result.current.deleteTopic(topicId);
      });

      expect(result.current.isDeleting).toBe(false);
      expect(result.current.error).toBe('Failed to delete topic');
    });
  });

  describe('UI Actions', () => {
    it('should set selected topic', () => {
      const { result } = renderHook(() => useTopicStore());

      const mockTopic: TopicRead = {
        id: 1,
        name: 'Test Topic',
        description: 'A test topic',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      act(() => {
        result.current.setSelectedTopic(mockTopic);
      });

      expect(result.current.selectedTopic).toEqual(mockTopic);
    });

    it('should clear selected topic', () => {
      const { result } = renderHook(() => useTopicStore());

      // Set selected topic first
      act(() => {
        result.current.selectedTopic = {
          id: 1,
          name: 'Test Topic',
          description: 'A test topic',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        };
      });

      expect(result.current.selectedTopic).toBeTruthy();

      act(() => {
        result.current.setSelectedTopic(null);
      });

      expect(result.current.selectedTopic).toBeNull();
    });

    it('should clear error', () => {
      const { result } = renderHook(() => useTopicStore());

      // Set an error first
      act(() => {
        result.current.error = 'Test error';
      });

      expect(result.current.error).toBe('Test error');

      act(() => {
        result.current.clearError();
      });

      expect(result.current.error).toBeNull();
    });
  });

  describe('Reset', () => {
    it('should reset store to initial state', () => {
      const { result } = renderHook(() => useTopicStore());

      // Modify state
      act(() => {
        result.current.topics = [
          {
            id: 1,
            name: 'Test Topic',
            description: 'A test topic',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
        ];
        result.current.selectedTopic = result.current.topics[0];
        result.current.isLoading = true;
        result.current.isCreating = true;
        result.current.isUpdating = true;
        result.current.isDeleting = true;
        result.current.error = 'Test error';
        result.current.total = 1;
        result.current.skip = 10;
        result.current.limit = 50;
      });

      // Reset
      act(() => {
        result.current.reset();
      });

      expect(result.current.topics).toEqual([]);
      expect(result.current.selectedTopic).toBeNull();
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isCreating).toBe(false);
      expect(result.current.isUpdating).toBe(false);
      expect(result.current.isDeleting).toBe(false);
      expect(result.current.error).toBeNull();
      expect(result.current.total).toBe(0);
      expect(result.current.skip).toBe(0);
      expect(result.current.limit).toBe(100);
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete topic workflow', async () => {
      const { result } = renderHook(() => useTopicStore());

      const mockTopics: TopicRead[] = [
        {
          id: 1,
          name: 'Topic 1',
          description: 'First topic',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          name: 'Topic 2',
          description: 'Second topic',
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ];

      (apiService.getTopics as any).mockResolvedValue(mockTopics);

      // Fetch topics
      await act(async () => {
        await result.current.fetchTopics();
      });

      expect(result.current.topics).toEqual(mockTopics);

      // Select a topic
      act(() => {
        result.current.setSelectedTopic(mockTopics[0]);
      });

      expect(result.current.selectedTopic).toEqual(mockTopics[0]);

      // Update topic
      const updateData: TopicCreate = { name: 'Updated Topic', description: 'Updated description' };
      const updatedTopic = { ...mockTopics[0], ...updateData };

      (apiService.updateTopic as any).mockResolvedValue(updatedTopic);

      await act(async () => {
        await result.current.updateTopic(1, updateData);
      });

      expect(result.current.topics[0]).toEqual(updatedTopic);
      expect(result.current.selectedTopic).toEqual(updatedTopic);

      // Delete topic
      (apiService.deleteTopic as any).mockResolvedValue({ message: 'Deleted' });

      await act(async () => {
        await result.current.deleteTopic(1);
      });

      expect(result.current.topics).toHaveLength(1);
      expect(result.current.selectedTopic).toBeNull();
    });

    it('should handle concurrent operations', async () => {
      const { result } = renderHook(() => useTopicStore());

      const mockTopics: TopicRead[] = [
        {
          id: 1,
          name: 'Topic 1',
          description: 'First topic',
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ];

      (apiService.getTopics as any).mockResolvedValue(mockTopics);
      (apiService.createTopic as any).mockResolvedValue({
        id: 2,
        name: 'New Topic',
        description: 'New topic',
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z',
      });

      // Perform concurrent operations
      await act(async () => {
        await Promise.all([
          result.current.fetchTopics(),
          result.current.createTopic({ name: 'New Topic', description: 'New topic' }),
        ]);
      });

      expect(result.current.topics).toHaveLength(2);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isCreating).toBe(false);
      expect(result.current.error).toBeNull();
    });
  });
});
