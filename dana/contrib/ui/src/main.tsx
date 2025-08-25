import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/layout';
import AgentsPage from './pages/Agents';
import AgentDetailPage from './pages/Agents/detail';
import LibraryPage from './pages/Library';
import './index.css';
import AgentChat from './pages/Agents/chat';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        richColors
        closeButton
        duration={4000}
        toastOptions={{
          style: {
            background: '#ffffff',
            color: '#374151',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            fontSize: '14px',
            fontWeight: '500',
          },
          // @ts-ignore
          success: {
            style: {
              background: '#c8e3d0',
              color: '#1fad49',
              border: '1px solid #bbf7d0',
            },
            iconTheme: {
              primary: '#22c55e',
              secondary: '#f0fdf4',
            },
          },
          error: {
            style: {
              background: '#fef2f2',
              color: '#dc2626',
              border: '1px solid #fecaca',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#fef2f2',
            },
          },
          warning: {
            style: {
              background: '#fffbeb',
              color: '#d97706',
              border: '1px solid #fed7aa',
            },
            iconTheme: {
              primary: '#f59e0b',
              secondary: '#fffbeb',
            },
          },
          info: {
            style: {
              background: '#eff6ff',
              color: '#1d4ed8',
              border: '1px solid #bfdbfe',
            },
            iconTheme: {
              primary: '#3b82f6',
              secondary: '#eff6ff',
            },
          },
        }}
      />
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
