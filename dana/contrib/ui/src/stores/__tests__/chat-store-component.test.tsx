import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen, waitFor } from '../../test/test-utils';
import { useChatStore } from '../chat-store';

// Example component that uses the chat store
const ChatStatus = () => {
  const { conversations, selectedConversation, isLoading, error } = useChatStore();

  return (
    <div>
      <div data-testid="conversation-count">Conversations: {conversations.length}</div>
      <div data-testid="current-conversation">Current: {selectedConversation?.id || 'None'}</div>
      <div data-testid="loading-status">Loading: {isLoading ? 'Yes' : 'No'}</div>
      {error && <div data-testid="error-message">Error: {error}</div>}
    </div>
  );
};

describe('Chat Store with Components', () => {
  beforeEach(() => {
    // Reset store state before each test
    useChatStore.setState({
      conversations: [],
      messages: [],
      selectedConversation: null,
      isLoading: false,
      error: null,
    });
  });

  it('should render initial state correctly', () => {
    render(<ChatStatus />);

    expect(screen.getByTestId('conversation-count')).toHaveTextContent('Conversations: 0');
    expect(screen.getByTestId('current-conversation')).toHaveTextContent('Current: None');
    expect(screen.getByTestId('loading-status')).toHaveTextContent('Loading: No');
    expect(screen.queryByTestId('error-message')).not.toBeInTheDocument();
  });

  it('should update when store state changes', async () => {
    render(<ChatStatus />);

    // Update store state
    useChatStore.setState({
      conversations: [
        {
          id: 1,
          title: 'Test',
          agent_id: 1,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
      selectedConversation: {
        id: 1,
        title: 'Test',
        agent_id: 1,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
        messages: [],
      },
      isLoading: true,
      error: 'Test error',
    });

    // Wait for the component to update
    await waitFor(() => {
      expect(screen.getByTestId('conversation-count')).toHaveTextContent('Conversations: 1');
    });

    expect(screen.getByTestId('current-conversation')).toHaveTextContent('Current: 1');
    expect(screen.getByTestId('loading-status')).toHaveTextContent('Loading: Yes');
    expect(screen.getByTestId('error-message')).toHaveTextContent('Error: Test error');
  });
});
