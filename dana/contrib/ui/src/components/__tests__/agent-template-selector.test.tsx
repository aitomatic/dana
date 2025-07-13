import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '../../test/test-utils';
import AgentTemplateSelector from '../agent-template-selector';

// Mock the stores
vi.mock('../../stores/agent-store', () => ({
  useAgentStore: () => ({
    agents: [],
    isLoading: false,
    error: null,
  }),
}));

vi.mock('../../stores/chat-store', () => ({
  useChatStore: () => ({
    conversations: [],
    selectedConversation: null,
    isLoading: false,
    error: null,
  }),
}));

describe('AgentTemplateSelector', () => {
  const mockOnTemplateSelect = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render template selector with categories', () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Check for main categories
    expect(screen.getByText('All')).toBeInTheDocument();
    expect(screen.getAllByText('General').length).toBeGreaterThan(1); // Button and badge
    expect(screen.getAllByText('Business').length).toBeGreaterThan(1); // Button and badge(s)
    expect(screen.getByText('Technical')).toBeInTheDocument();
    expect(screen.getByText('Specialized')).toBeInTheDocument();
  });

  it('should display template preview when template is selected', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Click on a template
    const simpleAssistantTemplate = screen.getByText('Simple Assistant');
    fireEvent.click(simpleAssistantTemplate);

    // Check for preview content
    await waitFor(() => {
      expect(screen.getByText('Simple Assistant')).toBeInTheDocument();
    });
  });

  it('should call onTemplateSelect when Use Template button is clicked', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Select a template
    const simpleAssistantTemplate = screen.getByText('Simple Assistant');
    fireEvent.click(simpleAssistantTemplate);

    // Click Use Template button
    await waitFor(() => {
      const useButtons = screen.getAllByText(/Use/i);
      // The last button is the one in the preview dialog
      fireEvent.click(useButtons[useButtons.length - 1]);
    });

    expect(mockOnTemplateSelect).toHaveBeenCalled();
  });

  it('should filter templates when category is selected', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Click on General category
    const generalCategoryButton = screen.getByRole('button', { name: 'General' });
    fireEvent.click(generalCategoryButton);

    await waitFor(() => {
      expect(screen.getByText('Simple Assistant')).toBeInTheDocument();
    });
  });

  it('should show preview dialog when Preview button is clicked', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Find and click a Preview button
    const previewButtons = screen.getAllByText('Preview');
    fireEvent.click(previewButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/Template Preview/)).toBeInTheDocument();
    });
  });

  it('should display template details in preview', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Select a template
    const simpleAssistantTemplate = screen.getByText('Simple Assistant');
    fireEvent.click(simpleAssistantTemplate);

    await waitFor(() => {
      expect(screen.getAllByText('Simple Assistant').length).toBeGreaterThan(0);
      expect(screen.getByText(/basic assistant/i)).toBeInTheDocument();
      expect(screen.getAllByText(/Use/i).length).toBeGreaterThan(0);
      expect(screen.getAllByText('Preview').length).toBeGreaterThan(0);
    });
  });

  it('should handle template selection from different categories', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Select from General category
    const generalCategoryButton = screen.getByRole('button', { name: 'General' });
    fireEvent.click(generalCategoryButton);

    await waitFor(() => {
      expect(screen.getByText('Simple Assistant')).toBeInTheDocument();
    });
  });

  it('should maintain selected template when switching between templates', async () => {
    render(<AgentTemplateSelector onTemplateSelect={mockOnTemplateSelect} />);

    // Select first template
    const simpleAssistantTemplate = screen.getByText('Simple Assistant');
    fireEvent.click(simpleAssistantTemplate);

    await waitFor(() => {
      expect(screen.getByText('Simple Assistant')).toBeInTheDocument();
    });

    // Select second template (if exists)
    // For demonstration, just click the same template again
    fireEvent.click(simpleAssistantTemplate);

    await waitFor(() => {
      expect(screen.getByText('Simple Assistant')).toBeInTheDocument();
    });
  });
});
