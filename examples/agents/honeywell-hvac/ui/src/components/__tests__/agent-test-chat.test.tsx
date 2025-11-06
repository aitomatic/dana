import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import AgentTestChat from '../agent-test-chat';

// Mock the API service
vi.mock('../../lib/api', () => ({
  apiService: {
    testAgent: vi.fn(),
  },
}));

import { apiService } from '../../lib/api';

describe('AgentTestChat', () => {
  const mockAgentCode = 'agent test code';
  const mockAgentName = 'Test Agent';
  const mockAgentDescription = 'A test agent';

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render the test chat interface', () => {
    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    expect(screen.getByPlaceholderText('Chat with agent')).toBeInTheDocument();
    // Get the send button specifically by aria-label
    expect(screen.getByRole('button', { name: 'Send message' })).toBeInTheDocument();
  });

  it('should send a message and receive response', async () => {
    const mockResponse = {
      success: true,
      agent_response: 'Hello! I am your test agent. How can I help you today?',
    };

    (apiService.testAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    // Type and send a message
    fireEvent.change(messageInput, { target: { value: 'Hello, agent!' } });
    fireEvent.click(sendButton);

    // Check that the message appears in the chat
    await waitFor(() => {
      expect(screen.getByText('Hello, agent!')).toBeInTheDocument();
    });

    // Check that the API was called correctly
    await waitFor(() => {
      expect(apiService.testAgent).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_code: mockAgentCode,
          message: 'Hello, agent!',
          agent_name: mockAgentName,
          agent_description: mockAgentDescription,
        }),
      );
    });

    // Check that the agent response appears
    await waitFor(() => {
      expect(
        screen.getByText('Hello! I am your test agent. How can I help you today?'),
      ).toBeInTheDocument();
    });
  });

  it('should handle API errors gracefully', async () => {
    const mockError = new Error('API Error');
    (apiService.testAgent as any).mockRejectedValue(mockError);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    // Type and send a message
    fireEvent.change(messageInput, { target: { value: 'Hello, agent!' } });
    fireEvent.click(sendButton);

    // Check that the message appears in the chat
    await waitFor(() => {
      expect(screen.getByText('Hello, agent!')).toBeInTheDocument();
    });

    // Check that an error message appears
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('should not send empty messages', () => {
    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const sendButton = screen.getByRole('button', { name: 'Send message' });

    // Try to send empty message
    fireEvent.click(sendButton);

    // Check that the API was not called
    expect(apiService.testAgent).not.toHaveBeenCalled();
  });

  it('should handle Enter key to send messages', async () => {
    const mockResponse = {
      success: true,
      agent_response: 'Response to Enter key test',
    };

    (apiService.testAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');

    // Type message and press Enter
    fireEvent.change(messageInput, { target: { value: 'Test with Enter key' } });
    fireEvent.keyPress(messageInput, { key: 'Enter', code: 'Enter', charCode: 13 });

    // Check that the message was sent
    await waitFor(() => {
      expect(screen.getByText('Test with Enter key')).toBeInTheDocument();
    });

    // Check that the API was called
    await waitFor(() => {
      expect(apiService.testAgent).toHaveBeenCalledWith(
        expect.objectContaining({
          message: 'Test with Enter key',
        }),
      );
    });
  });

  it('should clear input after sending message', async () => {
    const mockResponse = {
      success: true,
      agent_response: 'Test response',
    };

    (apiService.testAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    // Type and send a message
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Check that input is cleared
    await waitFor(() => {
      expect(messageInput).toHaveValue('');
    });
  });

  it('should show loading state while waiting for response', async () => {
    // Create a promise that we can control
    let resolvePromise: (value: any) => void;
    const promise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (apiService.testAgent as any).mockReturnValue(promise);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    // Type and send a message
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Check that loading state is shown
    await waitFor(() => {
      expect(screen.getByText('Testing agent...')).toBeInTheDocument();
    });

    // Check that send button is disabled and shows loading
    expect(sendButton).toBeDisabled();

    // Resolve the promise
    resolvePromise!({
      success: true,
      agent_response: 'Test response',
    });

    // Wait for loading to disappear
    await waitFor(() => {
      expect(screen.queryByText('Testing agent...')).not.toBeInTheDocument();
    });
  });

  it('should display multiple messages in conversation', async () => {
    const mockResponse1 = {
      success: true,
      agent_response: 'First response',
    };
    const mockResponse2 = {
      success: true,
      agent_response: 'Second response',
    };

    (apiService.testAgent as any)
      .mockResolvedValueOnce(mockResponse1)
      .mockResolvedValueOnce(mockResponse2);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    // Send first message
    fireEvent.change(messageInput, { target: { value: 'First message' } });
    fireEvent.click(sendButton);

    // Wait for first response
    await waitFor(() => {
      expect(screen.getByText('First response')).toBeInTheDocument();
    });

    // Send second message
    fireEvent.change(messageInput, { target: { value: 'Second message' } });
    fireEvent.click(sendButton);

    // Wait for second response
    await waitFor(() => {
      expect(screen.getByText('Second response')).toBeInTheDocument();
    });

    // Check that all messages are displayed
    expect(screen.getByText('First message')).toBeInTheDocument();
    expect(screen.getByText('Second message')).toBeInTheDocument();
    expect(screen.getByText('First response')).toBeInTheDocument();
    expect(screen.getByText('Second response')).toBeInTheDocument();
  });

  it('should handle special characters in messages', async () => {
    const mockResponse = {
      success: true,
      agent_response: 'Response with special chars: @#$%^&*()',
    };

    (apiService.testAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Chat with agent');
    const sendButton = screen.getByRole('button', { name: 'Send message' });

    const specialMessage = 'Message with special chars: @#$%^&*()_+-=[]{}|;:,.<>?';

    // Type and send message with special characters
    fireEvent.change(messageInput, { target: { value: specialMessage } });
    fireEvent.click(sendButton);

    // Check that the message appears correctly
    await waitFor(() => {
      expect(screen.getByText(specialMessage)).toBeInTheDocument();
    });

    // Check that the API was called with the correct message
    await waitFor(() => {
      expect(apiService.testAgent).toHaveBeenCalledWith(
        expect.objectContaining({
          message: specialMessage,
        }),
      );
    });
  });
});
