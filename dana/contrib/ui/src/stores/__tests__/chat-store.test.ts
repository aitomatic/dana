import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useChatStore } from '../chat-store';
import { apiService } from '@/lib/api';
import type { ChatResponse } from '@/lib/api';
import type { ConversationRead } from '@/types/conversation';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    chatWithAgent: vi.fn(),
    getConversations: vi.fn(),
    getConversation: vi.fn(),
    createConversation: vi.fn(),
    updateConversation: vi.fn(),
    deleteConversation: vi.fn(),
  },
}));

const mockApiService = vi.mocked(apiService);

describe('Chat Store', () => {
  beforeEach(() => {
    // Reset the store before each test
    useChatStore.getState().reset();
    vi.clearAllMocks();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useChatStore.getState();

      expect(state.messages).toEqual([]);
      expect(state.conversations).toEqual([]);
      expect(state.selectedConversation).toBeNull();
      expect(state.currentAgentId).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.isSending).toBe(false);
      expect(state.isCreating).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('sendMessage', () => {
    it('should send message successfully and update messages', async () => {
      const mockResponse: ChatResponse = {
        success: true,
        message: 'Hello',
        conversation_id: 1,
        message_id: 2,
        agent_response: 'Hi there!',
        context: { user_id: 1 },
        error: undefined,
      };

      mockApiService.chatWithAgent.mockResolvedValue(mockResponse);

      const { sendMessage } = useChatStore.getState();

      const result = await sendMessage('Hello', 1, 1);

      expect(result).toEqual(mockResponse);
      expect(mockApiService.chatWithAgent).toHaveBeenCalledWith({
        message: 'Hello',
        agent_id: 1,
        conversation_id: 1,
        context: { user_id: 1 },
      });

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(2);
      expect(state.messages[0].sender).toBe('user');
      expect(state.messages[0].content).toBe('Hello');
      expect(state.messages[1].sender).toBe('agent');
      expect(state.messages[1].content).toBe('Hi there!');
      expect(state.isSending).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle new conversation creation', async () => {
      const mockResponse: ChatResponse = {
        success: true,
        message: 'Hello',
        conversation_id: 2,
        message_id: 1,
        agent_response: 'Hi there!',
        context: { user_id: 1 },
        error: undefined,
      };

      mockApiService.chatWithAgent.mockResolvedValue(mockResponse);

      const { sendMessage } = useChatStore.getState();

      const result = await sendMessage('Hello', 1);

      expect(result).toEqual(mockResponse);
      expect(mockApiService.chatWithAgent).toHaveBeenCalledWith({
        message: 'Hello',
        agent_id: 1,
        conversation_id: undefined,
        context: { user_id: 1 },
      });

      const state = useChatStore.getState();
      expect(state.messages).toHaveLength(2);
      expect(state.isSending).toBe(false);
    });

    it('should handle API errors', async () => {
      const errorMessage = 'API Error';
      mockApiService.chatWithAgent.mockRejectedValue(new Error(errorMessage));

      const { sendMessage } = useChatStore.getState();

      await expect(sendMessage('Hello', 1)).rejects.toThrow(errorMessage);

      const state = useChatStore.getState();
      expect(state.messages).toEqual([]); // Should remove temporary message
      expect(state.isSending).toBe(false);
      expect(state.error).toBe(errorMessage);
    });

    it('should immediately add user message to UI', async () => {
      const mockResponse: ChatResponse = {
        success: true,
        message: 'Hello',
        conversation_id: 1,
        message_id: 2,
        agent_response: 'Hi there!',
        context: { user_id: 1 },
        error: undefined,
      };

      mockApiService.chatWithAgent.mockResolvedValue(mockResponse);

      const { sendMessage } = useChatStore.getState();

      // Start sending message
      const sendPromise = sendMessage('Hello', 1, 1);

      // Check that user message is immediately added
      const stateAfterSend = useChatStore.getState();
      expect(stateAfterSend.messages).toHaveLength(1);
      expect(stateAfterSend.messages[0].sender).toBe('user');
      expect(stateAfterSend.messages[0].content).toBe('Hello');
      expect(stateAfterSend.isSending).toBe(true);

      // Wait for completion
      await sendPromise;
    });
  });

  describe('fetchConversations', () => {
    it('should fetch conversations successfully', async () => {
      const mockConversations: ConversationRead[] = [
        {
          id: 1,
          title: 'Chat 1',
          agent_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          title: 'Chat 2',
          agent_id: 1,
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z',
        },
      ];

      mockApiService.getConversations.mockResolvedValue(mockConversations);

      const { fetchConversations } = useChatStore.getState();

      await fetchConversations(1);

      expect(mockApiService.getConversations).toHaveBeenCalledWith(1);

      const state = useChatStore.getState();
      expect(state.conversations).toEqual(mockConversations);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle fetch conversations error', async () => {
      const errorMessage = 'Failed to fetch conversations';
      mockApiService.getConversations.mockRejectedValue(new Error(errorMessage));

      const { fetchConversations } = useChatStore.getState();

      await fetchConversations(1);

      const state = useChatStore.getState();
      expect(state.conversations).toEqual([]);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(errorMessage);
    });
  });

  describe('fetchConversation', () => {
    it('should fetch conversation with messages successfully', async () => {
      const mockConversation = {
        id: 1,
        title: 'Test Conversation',
        agent_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        messages: [
          {
            id: 1,
            conversation_id: 1,
            sender: 'user' as const,
            content: 'Hello',
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
          },
          {
            id: 2,
            conversation_id: 1,
            sender: 'agent' as const,
            content: 'Hi there!',
            created_at: '2024-01-01T00:00:01Z',
            updated_at: '2024-01-01T00:00:01Z',
          },
        ],
      };

      mockApiService.getConversation.mockResolvedValue(mockConversation);

      const { fetchConversation } = useChatStore.getState();

      await fetchConversation(1);

      expect(mockApiService.getConversation).toHaveBeenCalledWith(1);

      const state = useChatStore.getState();
      expect(state.selectedConversation).toEqual(mockConversation);
      expect(state.messages).toEqual(mockConversation.messages);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should handle fetch conversation error', async () => {
      const errorMessage = 'Failed to fetch conversation';
      mockApiService.getConversation.mockRejectedValue(new Error(errorMessage));

      const { fetchConversation } = useChatStore.getState();

      await fetchConversation(1);

      const state = useChatStore.getState();
      expect(state.selectedConversation).toBeNull();
      expect(state.messages).toEqual([]);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe(errorMessage);
    });
  });

  describe('createConversation', () => {
    it('should create conversation successfully', async () => {
      const mockConversation: ConversationRead = {
        id: 1,
        title: 'New Chat',
        agent_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      };

      mockApiService.createConversation.mockResolvedValue(mockConversation);

      const { createConversation } = useChatStore.getState();

      const result = await createConversation({
        title: 'New Chat',
        agent_id: 1,
      });

      expect(result).toEqual(mockConversation);
      expect(mockApiService.createConversation).toHaveBeenCalledWith({
        title: 'New Chat',
        agent_id: 1,
      });

      const state = useChatStore.getState();
      expect(state.conversations).toContain(mockConversation);
      expect(state.isCreating).toBe(false);
    });
  });

  describe('Utility Functions', () => {
    it('should set current agent ID', () => {
      const { setCurrentAgentId } = useChatStore.getState();

      setCurrentAgentId(1);

      const state = useChatStore.getState();
      expect(state.currentAgentId).toBe(1);
    });

    it('should clear messages', () => {
      const { setCurrentAgentId, clearMessages } = useChatStore.getState();

      // Set some initial state
      setCurrentAgentId(1);

      clearMessages();

      const state = useChatStore.getState();
      expect(state.messages).toEqual([]);
      expect(state.currentAgentId).toBe(1); // Should not affect other state
    });

    it('should set and clear error', () => {
      const { setError, clearError } = useChatStore.getState();

      setError('Test error');

      let state = useChatStore.getState();
      expect(state.error).toBe('Test error');

      clearError();

      state = useChatStore.getState();
      expect(state.error).toBeNull();
    });

    it('should reset store to initial state', () => {
      const { setCurrentAgentId, setError, reset } = useChatStore.getState();

      // Set some state
      setCurrentAgentId(1);
      setError('Test error');

      reset();

      const state = useChatStore.getState();
      expect(state.currentAgentId).toBeNull();
      expect(state.error).toBeNull();
      expect(state.messages).toEqual([]);
      expect(state.conversations).toEqual([]);
      expect(state.selectedConversation).toBeNull();
      expect(state.isLoading).toBe(false);
      expect(state.isSending).toBe(false);
      expect(state.isCreating).toBe(false);
    });
  });
}); 