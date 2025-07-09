import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/layout";
import AgentsPage from "./pages/Agents";
import { CreateAgentPage } from "./pages/Agents/create";
import LibraryPage from "./pages/Library";
import SelectKnowledgePage from "./pages/Agents/select-knowledge";
import "./index.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <BrowserRouter>
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
          path="/agents/select-knowledge"
          element={
            <Layout hideLayout={true}>
              <SelectKnowledgePage />
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
  </StrictMode>
);
