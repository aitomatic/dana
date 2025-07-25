import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { StrictMode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../components/layout';
import AgentsPage from '../pages/Agents';
import AgentDetailPage from '../pages/Agents/detail';
import LibraryPage from '../pages/Library';
import AgentChat from '../pages/Agents/chat';
import * as agentStore from '../stores/agent-store';

// Mock the stores to avoid API calls during testing
vi.mock('../stores/chat-store', () => ({
  useChatStore: () => ({
    messages: [],
    conversations: [],
    selectedConversation: null,
    currentAgentId: null,
    isLoading: false,
    isSending: false,
    isCreating: false,
    error: null,
    sendMessage: vi.fn(),
    fetchConversations: vi.fn(),
    fetchConversation: vi.fn(),
    createConversation: vi.fn(),
    updateConversation: vi.fn(),
    deleteConversation: vi.fn(),
    setCurrentAgentId: vi.fn(),
    setSelectedConversation: vi.fn(),
    clearMessages: vi.fn(),
    setError: vi.fn(),
    clearError: vi.fn(),
    reset: vi.fn(),
  }),
}));

const TestApp = () => (
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <Navigate to="/agents" replace />
            </Layout>
          }
        />
        <Route
          path="/agents"
          element={
            <Layout>
              <AgentsPage />
            </Layout>
          }
        />
        <Route
          path="/agents/:agent_id"
          element={
            <Layout>
              <AgentDetailPage />
            </Layout>
          }
        />
        <Route
          path="/agents/:agent_id/chat"
          element={
            <Layout>
              <AgentChat />
            </Layout>
          }
        />
        <Route
          path="/agents/:agent_id/chat/:conversation_id"
          element={
            <Layout>
              <AgentChat />
            </Layout>
          }
        />
        <Route
          path="/library"
          element={
            <Layout>
              <LibraryPage />
            </Layout>
          }
        />
      </Routes>
    </BrowserRouter>
  </StrictMode>
);

describe('Routes', () => {
  let agentStoreSpy: ReturnType<typeof vi.spyOn>;
  const mockAgent = {
    id: 1,
    name: 'Test Agent',
    description: 'A test agent',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };
  let originalGetElementById: typeof document.getElementById;

  beforeEach(() => {
    // Mock document.getElementById to avoid jsdom error from chat-session
    originalGetElementById = document.getElementById;
    document.getElementById = vi.fn(() => null);
  });

  afterEach(() => {
    if (agentStoreSpy) agentStoreSpy.mockRestore();
    document.getElementById = originalGetElementById;
    vi.clearAllTimers();
  });

  it('should render agents page at /agents', () => {
    agentStoreSpy = vi.spyOn(agentStore, 'useAgentStore').mockReturnValue({
      agents: [mockAgent],
      fetchAgents: vi.fn(),
      isLoading: false,
    });
    window.history.pushState({}, '', '/agents');
    render(<TestApp />);
    expect(screen.getAllByText('Domain-Expert Agents').length).toBeGreaterThan(0);
  });


  it('should render agent detail page at /agents/:agent_id', () => {
    agentStoreSpy = vi.spyOn(agentStore, 'useAgentStore').mockReturnValue({
      agents: [],
      fetchAgents: vi.fn(),
      isLoading: false,
    });
    window.history.pushState({}, '', '/agents/1');
    const { container } = render(<TestApp />);
    expect(container.textContent).toContain('Agent Not Found');
  });

  it('should render chat page at /agents/:agent_id/chat', () => {
    window.history.pushState({}, '', '/agents/1/chat');
    render(<TestApp />);
    expect(screen.getByText('Agent Chat')).toBeInTheDocument();
  });

  it('should render chat page with conversation at /agents/:agent_id/chat/:conversation_id', () => {
    window.history.pushState({}, '', '/agents/1/chat/123');
    render(<TestApp />);
    expect(screen.getByText('Agent Chat')).toBeInTheDocument();
  });

  it('should render library page at /library', () => {
    window.history.pushState({}, '', '/library');
    render(<TestApp />);
    expect(screen.getByRole('heading', { name: 'Library' })).toBeInTheDocument();
  });

  it('should redirect from / to /agents', () => {
    agentStoreSpy = vi.spyOn(agentStore, 'useAgentStore').mockReturnValue({
      agents: [mockAgent],
      fetchAgents: vi.fn(),
      isLoading: false,
    });
    window.history.pushState({}, '', '/');
    render(<TestApp />);
    expect(screen.getAllByText('Domain-Expert Agents').length).toBeGreaterThan(0);
  });
});
