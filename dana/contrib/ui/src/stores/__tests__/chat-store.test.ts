import { describe, it, expect, beforeEach } from 'vitest';
import { useChatStore } from '../chat-store';
import type { Conversation, Message } from '../chat-store';

describe('Chat Store', () => {
  beforeEach(() => {
    // Reset store state before each test
    useChatStore.setState({
      conversations: [],
      messages: {},
      currentConversationId: null,
      loading: false,
      error: null,
    });
  });

  describe('State Management', () => {
    it('should have initial state', () => {
      const state = useChatStore.getState();

      expect(state.conversations).toEqual([]);
      expect(state.messages).toEqual({});
      expect(state.currentConversationId).toBeNull();
      expect(state.loading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('should set conversations', () => {
      const conversations: Conversation[] = [
        {
          id: 1,
          title: 'Test Conversation',
          createdAt: '2024-01-01T00:00:00Z',
          updatedAt: '2024-01-01T00:00:00Z',
        },
      ];

      useChatStore.getState().setConversations(conversations);

      expect(useChatStore.getState().conversations).toEqual(conversations);
    });

    it('should set messages for a conversation', () => {
      const conversationId = 1;
      const messages: Message[] = [
        {
          id: 1,
          conversationId,
          sender: 'user',
          content: 'Hello',
          createdAt: '2024-01-01T00:00:00Z',
        },
        {
          id: 2,
          conversationId,
          sender: 'agent',
          content: 'Hi there!',
          createdAt: '2024-01-01T00:01:00Z',
        },
      ];

      useChatStore.getState().setMessages(conversationId, messages);

      expect(useChatStore.getState().messages[conversationId]).toEqual(messages);
    });

    it('should set current conversation', () => {
      const conversationId = 1;

      useChatStore.getState().setCurrentConversation(conversationId);

      expect(useChatStore.getState().currentConversationId).toBe(conversationId);
    });

    it('should clear current conversation', () => {
      // First set a conversation
      useChatStore.getState().setCurrentConversation(1);
      expect(useChatStore.getState().currentConversationId).toBe(1);

      // Then clear it
      useChatStore.getState().setCurrentConversation(null);
      expect(useChatStore.getState().currentConversationId).toBeNull();
    });

    it('should set loading state', () => {
      useChatStore.getState().setLoading(true);
      expect(useChatStore.getState().loading).toBe(true);

      useChatStore.getState().setLoading(false);
      expect(useChatStore.getState().loading).toBe(false);
    });

    it('should set and clear error', () => {
      const errorMessage = 'Something went wrong';

      useChatStore.getState().setError(errorMessage);
      expect(useChatStore.getState().error).toBe(errorMessage);

      useChatStore.getState().clearError();
      expect(useChatStore.getState().error).toBeNull();
    });
  });

  describe('Message Management', () => {
    it('should preserve existing messages when adding new ones', () => {
      const conversationId1 = 1;
      const conversationId2 = 2;

      const messages1: Message[] = [
        {
          id: 1,
          conversationId: conversationId1,
          sender: 'user',
          content: 'Hello from conversation 1',
          createdAt: '2024-01-01T00:00:00Z',
        },
      ];

      const messages2: Message[] = [
        {
          id: 2,
          conversationId: conversationId2,
          sender: 'user',
          content: 'Hello from conversation 2',
          createdAt: '2024-01-01T00:00:00Z',
        },
      ];

      // Set messages for first conversation
      useChatStore.getState().setMessages(conversationId1, messages1);

      // Set messages for second conversation
      useChatStore.getState().setMessages(conversationId2, messages2);

      // Both conversations should have their messages
      expect(useChatStore.getState().messages[conversationId1]).toEqual(messages1);
      expect(useChatStore.getState().messages[conversationId2]).toEqual(messages2);
    });
  });
}); 