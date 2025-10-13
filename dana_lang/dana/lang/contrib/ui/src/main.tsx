import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'sonner';
import { Layout } from './components/layout';
import AgentsPage from './pages/Agents';
import AgentDetailPage from './pages/Agents/detail';
import LibraryPage from './pages/Library';
import DocumentationPage from './pages/Documentation';
import SupportPage from './pages/Support';
import StyleGuidePage from './pages/StyleGuide';
import './index.css';
import AgentChat from './pages/Agents/chat';
import { analytics } from './lib/analytics';

// Initialize Google Analytics
analytics.initialize();

// Initialize session tracking
analytics.initializeSession();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Toaster
        position="top-right"
        closeButton
        duration={4000}
        expand={true}
        visibleToasts={5}
        toastOptions={{
          style: {
            background: '#101828',
            color: '#ffffff',
            border: '1px solid #101828',
            borderRadius: '8px',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            fontSize: '14px',
            fontWeight: '500',
          },
          // @ts-expect-error - Sonner toast options
          success: {
            style: {
              background: '#101828',
              color: '#ffffff',
              border: '1px solid #101828',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#101828',
            },
          },
          error: {
            style: {
              background: '#101828',
              color: '#ffffff',
              border: '1px solid #101828',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#101828',
            },
          },
          warning: {
            style: {
              background: '#101828',
              color: '#ffffff',
              border: '1px solid #101828',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#101828',
            },
          },
          info: {
            style: {
              background: '#101828',
              color: '#ffffff',
              border: '1px solid #101828',
            },
            iconTheme: {
              primary: '#ffffff',
              secondary: '#101828',
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
        <Route
          path="/documentation"
          element={
            <Layout>
              <DocumentationPage />
            </Layout>
          }
        />
        <Route
          path="/support"
          element={
            <Layout>
              <SupportPage />
            </Layout>
          }
        />
        <Route
          path="/style-guide"
          element={
            <Layout hideLayout={true}>
              <StyleGuidePage />
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
