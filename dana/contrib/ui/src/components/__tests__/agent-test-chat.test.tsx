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

    expect(screen.getByPlaceholderText('Type a message to test your agent...')).toBeInTheDocument();
    expect(screen.getByRole('button')).toBeInTheDocument();
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

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');
    const sendButton = screen.getByRole('button');

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

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');
    const sendButton = screen.getByRole('button');

    // Type and send a message
    fireEvent.change(messageInput, { target: { value: 'Hello, agent!' } });
    fireEvent.click(sendButton);

    // Check that the message appears in the chat
    await waitFor(() => {
      expect(screen.getByText('Hello, agent!')).toBeInTheDocument();
    });

    // Check that error message appears
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

    const sendButton = screen.getByRole('button');

    // Try to send empty message
    fireEvent.click(sendButton);

    // Check that API was not called
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

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');

    // Type message and press Enter
    fireEvent.change(messageInput, { target: { value: 'Test with Enter key' } });
    fireEvent.keyPress(messageInput, { key: 'Enter', code: 'Enter', charCode: 13 });

    // Check that the message was sent
    await waitFor(() => {
      expect(screen.getByText('Test with Enter key')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(apiService.testAgent).toHaveBeenCalledWith(
        expect.objectContaining({
          agent_code: mockAgentCode,
          message: 'Test with Enter key',
          agent_name: mockAgentName,
          agent_description: mockAgentDescription,
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

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');
    const sendButton = screen.getByRole('button');

    // Send a message
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
    const mockPromise = new Promise((resolve) => {
      resolvePromise = resolve;
    });

    (apiService.testAgent as any).mockReturnValue(mockPromise);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');
    const sendButton = screen.getByRole('button');

    // Send a message
    fireEvent.change(messageInput, { target: { value: 'Test message' } });
    fireEvent.click(sendButton);

    // Check that loading state is shown
    await waitFor(() => {
      expect(screen.getByText((content) => content.includes('Testing agent'))).toBeInTheDocument();
    });

    // Resolve the promise
    resolvePromise!({
      success: true,
      agent_response: 'Test response',
    });

    // Check that loading state is removed
    await waitFor(() => {
      expect(screen.queryByText(/sending/i)).not.toBeInTheDocument();
    });
  });

  it('should display multiple messages in conversation', async () => {
    const mockResponses = [
      { success: true, agent_response: 'First response' },
      { success: true, agent_response: 'Second response' },
    ];

    (apiService.testAgent as any)
      .mockResolvedValueOnce(mockResponses[0])
      .mockResolvedValueOnce(mockResponses[1]);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');
    const sendButton = screen.getByRole('button');

    // Send first message
    fireEvent.change(messageInput, { target: { value: 'First message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('First message')).toBeInTheDocument();
      expect(screen.getByText('First response')).toBeInTheDocument();
    });

    // Send second message
    fireEvent.change(messageInput, { target: { value: 'Second message' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Second message')).toBeInTheDocument();
      expect(screen.getByText('Second response')).toBeInTheDocument();
    });

    // Check that both conversations are displayed
    expect(screen.getAllByText(/message/i)).toHaveLength(2);
    expect(screen.getAllByText(/response/i)).toHaveLength(2);
  });

  it('should handle special characters in messages', async () => {
    const mockResponse = {
      success: true,
      agent_response: 'Response with special chars: !@#$%^&*()',
    };

    (apiService.testAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentTestChat
        agentCode={mockAgentCode}
        agentName={mockAgentName}
        agentDescription={mockAgentDescription}
      />,
    );

    const messageInput = screen.getByPlaceholderText('Type a message to test your agent...');
    const sendButton = screen.getByRole('button');

    // Send message with special characters
    fireEvent.change(messageInput, { target: { value: 'Test with special chars: !@#$%^&*()' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText('Test with special chars: !@#$%^&*()')).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText('Response with special chars: !@#$%^&*()')).toBeInTheDocument();
    });
  });
});
