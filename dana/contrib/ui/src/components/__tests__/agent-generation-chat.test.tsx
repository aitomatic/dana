import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import AgentGenerationChat from '../agent-generation-chat';
import { apiService } from '@/lib/api';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    generateAgent: vi.fn(),
  },
}));

// Mock toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('AgentGenerationChat', () => {
  const mockOnCodeGenerated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the chat interface', () => {
    render(
      <AgentGenerationChat
        onCodeGenerated={mockOnCodeGenerated}
        currentCode=""
      />
    );

    expect(screen.getByText('Agent Generator')).toBeInTheDocument();
    expect(screen.getByText(/Hi! I'm here to help you create a Dana agent/)).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Describe the agent you want to create...')).toBeInTheDocument();
  });

  it('sends a message when user types and clicks send', async () => {
    const mockResponse = {
      success: true,
      dana_code: 'agent TestAgent:\n    name : str = "Test Agent"\n    description : str = "A test agent"',
      agent_name: 'Test Agent',
      agent_description: 'A test agent',
    };

    (apiService.generateAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentGenerationChat
        onCodeGenerated={mockOnCodeGenerated}
        currentCode=""
      />
    );

    const input = screen.getByPlaceholderText('Describe the agent you want to create...');
    const sendButton = screen.getByRole('button');

    fireEvent.change(input, { target: { value: 'I want a weather agent' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(apiService.generateAgent).toHaveBeenCalledWith({
        messages: [
          { role: 'assistant', content: expect.stringContaining('Hi! I\'m here to help') },
          { role: 'user', content: 'I want a weather agent' },
        ],
        current_code: '',
      });
    });

    await waitFor(() => {
      expect(mockOnCodeGenerated).toHaveBeenCalledWith(
        mockResponse.dana_code,
        mockResponse.agent_name,
        mockResponse.agent_description
      );
    });
  });

  it('handles API errors gracefully', async () => {
    const mockError = new Error('API Error');
    (apiService.generateAgent as any).mockRejectedValue(mockError);

    render(
      <AgentGenerationChat
        onCodeGenerated={mockOnCodeGenerated}
        currentCode=""
      />
    );

    const input = screen.getByPlaceholderText('Describe the agent you want to create...');
    const sendButton = screen.getByRole('button');

    fireEvent.change(input, { target: { value: 'I want a weather agent' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Sorry, I encountered an error/)).toBeInTheDocument();
    });
  });

  it('sends current code when provided', async () => {
    const currentCode = 'agent ExistingAgent:\n    name : str = "Existing"';
    const mockResponse = {
      success: true,
      dana_code: 'agent UpdatedAgent:\n    name : str = "Updated"',
      agent_name: 'Updated Agent',
      agent_description: 'Updated description',
    };

    (apiService.generateAgent as any).mockResolvedValue(mockResponse);

    render(
      <AgentGenerationChat
        onCodeGenerated={mockOnCodeGenerated}
        currentCode={currentCode}
      />
    );

    const input = screen.getByPlaceholderText('Describe the agent you want to create...');
    const sendButton = screen.getByRole('button');

    fireEvent.change(input, { target: { value: 'Update this agent' } });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(apiService.generateAgent).toHaveBeenCalledWith({
        messages: [
          { role: 'assistant', content: expect.stringContaining('Hi! I\'m here to help') },
          { role: 'user', content: 'Update this agent' },
        ],
        current_code: currentCode,
      });
    });
  });
}); 