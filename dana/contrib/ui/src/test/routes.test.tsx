import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { createRoot } from 'react-dom/client';
import { StrictMode } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '../components/layout';
import AgentsPage from '../pages/Agents';
import { CreateAgentPage } from '../pages/Agents/create';
import AgentDetailPage from '../pages/Agents/detail';
import LibraryPage from '../pages/Library';
import AgentChat from '../pages/Agents/chat';

// Mock the stores to avoid API calls during testing
vi.mock('../stores/agent-store', () => ({
  useAgentStore: () => ({
    agents: [],
    fetchAgents: vi.fn(),
    isLoading: false,
  }),
}));

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

// Test component to render routes
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
          path="/agents/create"
          element={
            <Layout hideLayout={true}>
              <CreateAgentPage />
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
  it('should render agents page at /agents', () => {
    window.history.pushState({}, '', '/agents');
    render(<TestApp />);

    // Check that the agents page content is rendered
    expect(screen.getByText('Domain-Expert Agents')).toBeInTheDocument();
  });

  it('should render create agent page at /agents/create', () => {
    window.history.pushState({}, '', '/agents/create');
    render(<TestApp />);

    // Check that the create agent page content is rendered
    expect(screen.getByText('Create Agent')).toBeInTheDocument();
  });

  it('should render agent detail page at /agents/:agent_id', () => {
    window.history.pushState({}, '', '/agents/1');
    render(<TestApp />);

    // Check that the agent detail page content is rendered
    expect(screen.getByText('Agent Not Found')).toBeInTheDocument();
  });

  it('should render chat page at /agents/:agent_id/chat', () => {
    window.history.pushState({}, '', '/agents/1/chat');
    render(<TestApp />);

    // Check that the chat page content is rendered
    expect(screen.getByText('Agent Chat')).toBeInTheDocument();
  });

  it('should render chat page with conversation at /agents/:agent_id/chat/:conversation_id', () => {
    window.history.pushState({}, '', '/agents/1/chat/123');
    render(<TestApp />);

    // Check that the chat page content is rendered
    expect(screen.getByText('Agent Chat')).toBeInTheDocument();
  });

  it('should render library page at /library', () => {
    window.history.pushState({}, '', '/library');
    render(<TestApp />);

    // Check that the library page content is rendered
    expect(screen.getByText('Library')).toBeInTheDocument();
  });

  it('should redirect from / to /agents', () => {
    window.history.pushState({}, '', '/');
    render(<TestApp />);

    // Check that it redirects to agents page
    expect(screen.getByText('Domain-Expert Agents')).toBeInTheDocument();
  });
}); 