import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/layout';
import AgentsPage from './pages/Agents';
import { CreateAgentPage } from './pages/Agents/create';
import AgentDetailPage from './pages/Agents/detail';
import LibraryPage from './pages/Library';
import './index.css';
import AgentChat from './pages/Agents/chat';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Toaster position="top-right" richColors closeButton duration={4000} />
      <Routes>
        {/* Routes with layout */}
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
            <Layout hideLayout={true}>
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

        {/* Routes without layout - add your layout-free pages here */}
        {/* Example:
        <Route path="/login" element={<Layout hideLayout={true}><LoginPage /></Layout>} />
        <Route path="/register" element={<Layout hideLayout={true}><RegisterPage /></Layout>} />
        <Route path="/landing" element={<Layout hideLayout={true}><LandingPage /></Layout>} />
        */}
      </Routes>
    </BrowserRouter>
  </StrictMode>,
);
