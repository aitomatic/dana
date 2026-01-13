import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useTopicOperations } from '../use-api';

// Mock the stores
const mockTopicStore = {
  fetchTopics: vi.fn(),
  fetchTopic: vi.fn(),
  createTopic: vi.fn(),
  updateTopic: vi.fn(),
  deleteTopic: vi.fn(),
  topics: [] as any[],
  selectedTopic: null as any,
  isLoading: false,
  isCreating: false,
  isUpdating: false,
  isDeleting: false,
  error: null as string | null,
  setSelectedTopic: vi.fn(),
  clearError: vi.fn(),
};

const mockUIStore = {
  addNotification: vi.fn(),
};

vi.mock('../../stores/topic-store', () => ({
  useTopicStore: () => mockTopicStore,
}));

vi.mock('../../stores/ui-store', () => ({
  useUIStore: () => mockUIStore,
}));

describe('useTopicOperations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset mock store state
    mockTopicStore.topics = [];
    mockTopicStore.selectedTopic = null;
    mockTopicStore.isLoading = false;
    mockTopicStore.isCreating = false;
    mockTopicStore.isUpdating = false;
    mockTopicStore.isDeleting = false;
    mockTopicStore.error = null;
  });

  it('should return topic operations with notification handling', () => {
    const { result } = renderHook(() => useTopicOperations());

    expect(result.current).toHaveProperty('fetchTopics');
    expect(result.current).toHaveProperty('fetchTopic');
    expect(result.current).toHaveProperty('createTopic');
    expect(result.current).toHaveProperty('updateTopic');
    expect(result.current).toHaveProperty('deleteTopic');
    expect(result.current).toHaveProperty('topics');
    expect(result.current).toHaveProperty('selectedTopic');
    expect(result.current).toHaveProperty('isLoading');
    expect(result.current).toHaveProperty('isCreating');
    expect(result.current).toHaveProperty('isUpdating');
    expect(result.current).toHaveProperty('isDeleting');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('setSelectedTopic');
    expect(result.current).toHaveProperty('clearError');
  });

  it('should handle createTopic with success notification', async () => {
    mockTopicStore.createTopic.mockResolvedValue(undefined);

    const { result } = renderHook(() => useTopicOperations());

    const newTopic = {
      name: 'Test Topic',
      description: 'A test topic',
    };

    await act(async () => {
      await result.current.createTopic(newTopic);
    });

    expect(mockTopicStore.createTopic).toHaveBeenCalledWith(newTopic);
    expect(mockUIStore.addNotification).toHaveBeenCalledWith({
      type: 'success',
      title: 'Topic Created',
      message: 'Topic created successfully',
      duration: 3000,
    });
  });

  it('should handle createTopic with error notification', async () => {
    mockTopicStore.createTopic.mockRejectedValue(new Error('Creation failed'));

    const { result } = renderHook(() => useTopicOperations());

    const newTopic = {
      name: 'Test Topic',
      description: 'A test topic',
    };

    await act(async () => {
      await result.current.createTopic(newTopic);
    });

    expect(mockTopicStore.createTopic).toHaveBeenCalledWith(newTopic);
    expect(mockUIStore.addNotification).toHaveBeenCalledWith({
      type: 'error',
      title: 'Creation Failed',
      message: 'Failed to create topic',
      duration: 5000,
    });
  });

  it('should handle updateTopic with success notification', async () => {
    mockTopicStore.updateTopic.mockResolvedValue(undefined);

    const { result } = renderHook(() => useTopicOperations());

    const topicId = 1;
    const updateData = {
      name: 'Updated Topic',
      description: 'An updated topic',
    };

    await act(async () => {
      await result.current.updateTopic(topicId, updateData);
    });

    expect(mockTopicStore.updateTopic).toHaveBeenCalledWith(topicId, updateData);
    expect(mockUIStore.addNotification).toHaveBeenCalledWith({
      type: 'success',
      title: 'Topic Updated',
      message: 'Topic updated successfully',
      duration: 3000,
    });
  });

  it('should handle updateTopic with error notification', async () => {
    mockTopicStore.updateTopic.mockRejectedValue(new Error('Update failed'));

    const { result } = renderHook(() => useTopicOperations());

    const topicId = 1;
    const updateData = {
      name: 'Updated Topic',
      description: 'An updated topic',
    };

    await act(async () => {
      await result.current.updateTopic(topicId, updateData);
    });

    expect(mockTopicStore.updateTopic).toHaveBeenCalledWith(topicId, updateData);
    expect(mockUIStore.addNotification).toHaveBeenCalledWith({
      type: 'error',
      title: 'Update Failed',
      message: 'Failed to update topic',
      duration: 5000,
    });
  });

  it('should handle deleteTopic with success notification', async () => {
    mockTopicStore.deleteTopic.mockResolvedValue(undefined);

    const { result } = renderHook(() => useTopicOperations());

    const topicId = 1;

    await act(async () => {
      await result.current.deleteTopic(topicId);
    });

    expect(mockTopicStore.deleteTopic).toHaveBeenCalledWith(topicId);
    expect(mockUIStore.addNotification).toHaveBeenCalledWith({
      type: 'success',
      title: 'Topic Deleted',
      message: 'Topic deleted successfully',
      duration: 3000,
    });
  });

  it('should handle deleteTopic with error notification', async () => {
    mockTopicStore.deleteTopic.mockRejectedValue(new Error('Deletion failed'));

    const { result } = renderHook(() => useTopicOperations());

    const topicId = 1;

    await act(async () => {
      await result.current.deleteTopic(topicId);
    });

    expect(mockTopicStore.deleteTopic).toHaveBeenCalledWith(topicId);
    expect(mockUIStore.addNotification).toHaveBeenCalledWith({
      type: 'error',
      title: 'Deletion Failed',
      message: 'Failed to delete topic',
      duration: 5000,
    });
  });

  it('should return store state correctly', () => {
    const mockTopics = [
      { id: 1, name: 'Topic 1', description: 'Test topic' },
      { id: 2, name: 'Topic 2', description: 'Test topic 2' },
    ];

    const mockSelectedTopic = { id: 1, name: 'Selected Topic', description: 'Selected topic' };

    // Update the mock store with new values
    mockTopicStore.topics = mockTopics;
    mockTopicStore.selectedTopic = mockSelectedTopic;
    mockTopicStore.isLoading = true;
    mockTopicStore.isCreating = false;
    mockTopicStore.isUpdating = true;
    mockTopicStore.isDeleting = false;
    mockTopicStore.error = 'Test error';

    const { result } = renderHook(() => useTopicOperations());

    expect(result.current.topics).toEqual(mockTopics);
    expect(result.current.selectedTopic).toEqual(mockSelectedTopic);
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isCreating).toBe(false);
    expect(result.current.isUpdating).toBe(true);
    expect(result.current.isDeleting).toBe(false);
    expect(result.current.error).toBe('Test error');
  });
});
