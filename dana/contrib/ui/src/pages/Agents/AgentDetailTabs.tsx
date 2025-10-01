/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState } from 'react';
import OverviewTab from './tabs/OverviewTab';
import KnowledgeBaseTab from './tabs/KnowledgeBaseTab';
import CodeTab from './tabs/CodeTab';
import WorkflowsTab from './tabs/WorkflowsTab';
import { ChatPane } from './ChatPane';
import {
  Code2,
  List,
  BookOpen,
  Network,
  CheckCircle,
  Building,
  Rocket,
  Globe,
  Play,
  Lock,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { useAgentStore } from '@/stores/agent-store';
import { useUIStore } from '@/stores/ui-store';
import { useAutoSwitchToKnowledgeTab } from '@/hooks';
import { getAgentAvatarSync } from '@/utils/avatar';
import type { NavigateFunction } from 'react-router-dom';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';

const TABS = ['Overview', 'Resources', 'Workflows', 'Code', 'Deployment'];

const TAB_ICONS = {
  Overview: <List className="w-4 h-4" />,
  Resources: <BookOpen className="w-4 h-4" />,
  Workflows: <Network className="w-4 h-4" />,
  Code: <Code2 className="w-4 h-4" />,
  Deployment: <Rocket className="w-4 h-4" />,
};

// Placeholder component for deployment status
const DeploymentStatusCard: React.FC<{
  agentId: number;
  onOpenDeploymentDialog: () => void;
}> = ({ agentId, onOpenDeploymentDialog }) => {
  return (
    <div className="p-4 rounded-lg border border-gray-200">
      <div className="flex justify-between items-center">
        <div>
          <h4 className="font-medium text-gray-900">Agent {agentId} Deployment</h4>
          <p className="text-sm text-gray-600">Status: Not deployed</p>
        </div>
        <Button onClick={onOpenDeploymentDialog} size="sm">
          Deploy Now
        </Button>
      </div>
    </div>
  );
};

export const AgentDetailTabs: React.FC<{
  children?: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  navigate: NavigateFunction;
}> = ({ activeTab, setActiveTab, navigate }) => {
  const { selectedAgent } = useAgentStore();
  const {
    isChatSidebarOpen,
    openChatSidebar,
    closeChatSidebar,
    agentDetailActiveTab,
    setAgentDetailActiveTab,
  } = useUIStore();

  // Auto-switch to Domain Knowledge tab when tree is updated (legacy method)
  useAutoSwitchToKnowledgeTab();

  // Deployment state
  const [showLocalAPI, setShowLocalAPI] = useState(false);
  const [showCloudDeployment, setShowCloudDeployment] = useState(false);
  const [showDockerDeployment, setShowDockerDeployment] = useState(false);
  const [showExportConfig, setShowExportConfig] = useState(false);
  const [deploymentStep, setDeploymentStep] = useState(0);
  const [deploymentLogs, setDeploymentLogs] = useState<
    Array<{ timestamp: string; message: string }>
  >([]);
  const [deploymentCompleted, setDeploymentCompleted] = useState(false);
  const [showDeploymentLogs, setShowDeploymentLogs] = useState(false);

  // Simulate deployment process
  const simulateDeployment = () => {
    setDeploymentStep(1);
    setShowDeploymentLogs(true);
    setDeploymentLogs([
      { timestamp: new Date().toLocaleTimeString(), message: 'Starting deployment...' },
    ]);

    setTimeout(() => setDeploymentStep(2), 1000);
    setTimeout(() => setDeploymentStep(3), 2000);
    setTimeout(() => setDeploymentStep(4), 3000);
    setTimeout(() => setDeploymentCompleted(true), 4000);
  };

  // Use global state if available, otherwise fall back to props
  const currentActiveTab = agentDetailActiveTab || activeTab || 'Overview';
  const handleTabChange = (tab: string) => {
    setAgentDetailActiveTab(tab);
    if (setActiveTab) {
      setActiveTab(tab);
    }
  };

  return (
    <div className="grid grid-cols-[1fr_max-content] h-full relative overflow-hidden">
      {/* Main content area */}
      <div className="overflow-auto grid grid-cols-1 grid-rows-[max-content_1fr] flex-1 h-full custom-scrollbar">
        {/* Tab bar */}
        <div className="flex justify-between items-center border-b border-gray-200 max-w-screen">
          <div className="flex">
            {TABS.map((tab) => (
              <button
                key={tab}
                className={`cursor-pointer px-4 py-4 h-14 font-medium text-sm flex items-center gap-2 transition-colors relative ${
                  currentActiveTab === tab
                    ? 'text-primary bg-white before:absolute before:bottom-[-1px] before:left-0 before:right-0 before:h-1 before:bg-white before:content-[""]'
                    : 'text-gray-500'
                }`}
                onClick={() => handleTabChange(tab)}
              >
                {TAB_ICONS[tab as keyof typeof TAB_ICONS]}
                {tab}
              </button>
            ))}
          </div>
          <div className="flex gap-2 items-center pr-2">
            {!isChatSidebarOpen && (
              <Button
                variant="link"
                // size="sm"
                className="flex gap-2 items-center px-2 py-2 text-gray-700 border-gray-200 hover:bg-brand-100 hover:text-gray-900"
                onClick={() => openChatSidebar()}
              >
                {/* Agent Avatar */}
                <div className="flex overflow-hidden justify-center items-center w-6 h-6 rounded-full">
                  <img
                    src={getAgentAvatarSync(selectedAgent?.id || 0)}
                    alt={`${selectedAgent?.name || 'Agent'} avatar`}
                    className="object-cover w-full h-full"
                    onError={(e) => {
                      // Fallback to colored circle if image fails to load
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const parent = target.parentElement;
                      if (parent) {
                        parent.className = `flex justify-center items-center w-6 h-6 rounded-full bg-brand-100`;
                        parent.innerHTML = `<span className="text-xs font-medium text-brand-700">${selectedAgent?.name?.[0] || 'A'}</span>`;
                      }
                    }}
                  />
                </div>

                {/* Chat Text */}
                <span className="text-sm font-semibold">
                  {selectedAgent?.name || 'Agent'} Playground
                </span>
              </Button>
            )}
          </div>
        </div>
        {/* Tab content */}
        {currentActiveTab === 'Overview' && <OverviewTab navigate={navigate} />}
        {currentActiveTab === 'Resources' && <KnowledgeBaseTab />}
        {currentActiveTab === 'Workflows' && <WorkflowsTab />}
        {currentActiveTab === 'Code' && <CodeTab />}
        {currentActiveTab === 'Deployment' && (
          <div className="p-6">
            <div className="mx-auto max-w-4xl">
              <div className="mb-8">
                <h2 className="mb-2 text-2xl font-bold text-gray-900">Agent Deployment</h2>
                <p className="text-gray-600">
                  Deploy your agent to production environments with enterprise-grade infrastructure
                </p>
              </div>

              {/* Deployment Options */}
              <div className="grid grid-cols-1 gap-6 mb-8 lg:grid-cols-2">
                {/* 1. Run & Share from Your Laptop (Community Edition) */}
                <div className="p-6 rounded-xl border border-green-200 transition-colors hover:border-green-300 hover:shadow-lg">
                  <div className="flex gap-3 items-center mb-4">
                    <div className="flex justify-center items-center w-10 h-10 bg-green-100 rounded-lg">
                      <Code2 className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">Run & Share Anywhere</h3>
                      <p className="text-sm text-gray-600">Community Edition</p>
                    </div>
                  </div>

                  <div className="mb-6 space-y-3">
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Serve agent via FastAPI server anywhere</span>
                    </div>
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>View and copy cURL for testing</span>
                    </div>
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Export agent folder with .na files</span>
                    </div>
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span>Portable and private</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Button
                      onClick={() => {
                        setShowLocalAPI(true);
                        setShowCloudDeployment(false);
                        setShowDockerDeployment(false);
                        setShowExportConfig(false);
                        setDeploymentStep(0);
                        setDeploymentLogs([]);
                        setDeploymentCompleted(false);
                      }}
                      className="w-full bg-green-600 hover:bg-green-700 text-white transition-all duration-200 hover:scale-[1.02]"
                      disabled={showLocalAPI}
                    >
                      <Play className="mr-2 w-4 h-4" />
                      {showLocalAPI ? 'Running...' : 'Start Local API'}
                    </Button>

                    <Button
                      onClick={() => {
                        setShowExportConfig(true);
                        setShowLocalAPI(false);
                        setShowCloudDeployment(false);
                        setShowDockerDeployment(false);
                      }}
                      variant="outline"
                      className="w-full border-blue-200 text-blue-700 hover:bg-blue-50"
                    >
                      <List className="mr-2 w-4 h-4" />
                      Export Agent Folder
                    </Button>
                  </div>
                </div>

                {/* 2. Deploy to Enterprise Infrastructure (Enterprise Only) */}
                <div className="p-6 rounded-xl border border-purple-200 transition-colors hover:border-purple-300 hover:shadow-lg">
                  <div className="flex gap-3 items-center mb-4">
                    <div className="flex justify-center items-center w-10 h-10 bg-purple-100 rounded-lg">
                      <Building className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Enterprise Deployment Package
                      </h3>
                      <p className="flex gap-1 items-center text-sm text-gray-600">
                        <span>
                          Required for banking, healthcare, semiconductor & regulated industries
                        </span>
                        <Lock className="w-4 h-4 text-purple-600" />
                      </p>
                    </div>
                  </div>

                  <div className="mb-6 space-y-3">
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <Lock className="w-4 h-4 text-purple-500" />
                      <span>SOC2, HIPAA, ISO27001 compliant infrastructure</span>
                    </div>
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <Lock className="w-4 h-4 text-purple-500" />
                      <span>Deploy to your private cloud with security controls</span>
                    </div>
                    <div className="flex gap-2 items-center text-sm text-gray-600">
                      <Lock className="w-4 h-4 text-purple-500" />
                      <span>RBAC, audit logs, compliance reporting</span>
                    </div>
                  </div>

                  <div className="space-y-3">
                    <Button
                      onClick={() => {}} // Disabled
                      className="w-full text-gray-600 bg-gray-400 opacity-50 transition-all duration-200 cursor-not-allowed"
                      disabled={true}
                      title="Coming Soon"
                    >
                      <Rocket className="mr-2 w-4 h-4" />
                      Deploy to Cloud (Coming Soon)
                    </Button>

                    <Button
                      onClick={() => {}} // Disabled
                      variant="outline"
                      className="w-full text-gray-500 bg-gray-100 border-gray-300 opacity-50 cursor-not-allowed"
                      disabled={true}
                      title="Coming Soon"
                    >
                      <Building className="mr-2 w-4 h-4" />
                      Get Docker Image (Coming Soon)
                    </Button>

                    {/* Contact Sales Link */}
                    <div className="pt-2 text-center">
                      <a
                        href="mailto:support@aitomatic.com?subject=Deployment%20Help"
                        className="inline-flex gap-2 items-center text-sm font-medium text-purple-600 transition-colors hover:text-purple-700"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                          />
                        </svg>
                        Need Help? Contact Us
                      </a>
                    </div>
                  </div>

                  {/* Why Enterprise? */}
                  <div className="p-4 mb-6 bg-purple-50 rounded-lg">
                    <div className="flex gap-3 items-start">
                      <div className="w-5 h-5 bg-purple-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <svg
                          className="w-3 h-3 text-purple-600"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      </div>
                      <div className="text-sm text-purple-800">
                        <p className="mb-1 font-medium">Why Enterprise Package?</p>
                        <p>
                          Banking, healthcare, and semiconductor industries require SOC2 compliance,
                          data residency controls, and audit trails. Community edition doesn't meet
                          these security standards.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Cloud Deployment Process */}
              {showCloudDeployment && !showDockerDeployment && (
                <div className="p-6 mb-8 bg-white rounded-xl border border-blue-200">
                  <div className="flex justify-between items-center mb-6">
                    <div className="flex gap-3 items-center">
                      <div className="flex justify-center items-center w-10 h-10 bg-blue-100 rounded-lg">
                        <Globe className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          Cloud Deployment Process
                        </h3>
                        <p className="text-sm text-gray-600">
                          Deploying your agent to Aitomatic Cloud
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => {
                        setShowCloudDeployment(false);
                        setDeploymentStep(0);
                        setDeploymentLogs([]);
                        setDeploymentCompleted(false);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      Back to Options
                    </Button>
                  </div>

                  {/* Deployment Steps */}
                  <div className="mb-6 space-y-6">
                    {/* Step 1: Authentication */}
                    <div
                      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                        deploymentStep >= 1
                          ? 'border-green-200 bg-green-50'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex gap-3 items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            deploymentStep >= 1
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {deploymentStep > 1 ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <span className="text-sm font-medium">1</span>
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">Authentication</h4>
                          <p className="text-sm text-gray-600">
                            Authenticating with Aitomatic Cloud workspace
                          </p>
                        </div>
                        {deploymentStep === 1 && (
                          <div className="w-6 h-6 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                        )}
                      </div>
                    </div>

                    {/* Step 2: Infrastructure Setup */}
                    <div
                      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                        deploymentStep >= 2
                          ? 'border-green-200 bg-green-50'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex gap-3 items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            deploymentStep >= 2
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {deploymentStep > 2 ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <span className="text-sm font-medium">2</span>
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">Infrastructure Setup</h4>
                          <p className="text-sm text-gray-600">
                            Provisioning compute resources and networking
                          </p>
                        </div>
                        {deploymentStep === 2 && (
                          <div className="w-6 h-6 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                        )}
                      </div>
                    </div>

                    {/* Step 3: Agent Deployment */}
                    <div
                      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                        deploymentStep >= 3
                          ? 'border-green-200 bg-green-50'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex gap-3 items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            deploymentStep >= 3
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {deploymentStep > 3 ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <span className="text-sm font-medium">3</span>
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">Agent Deployment</h4>
                          <p className="text-sm text-gray-600">
                            Deploying agent code and dependencies
                          </p>
                        </div>
                        {deploymentStep === 3 && (
                          <div className="w-6 h-6 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                        )}
                      </div>
                    </div>

                    {/* Step 4: Health Check */}
                    <div
                      className={`p-4 rounded-lg border-2 transition-all duration-300 ${
                        deploymentStep >= 4
                          ? 'border-green-200 bg-green-50'
                          : 'border-gray-200 bg-gray-50'
                      }`}
                    >
                      <div className="flex gap-3 items-center">
                        <div
                          className={`w-8 h-8 rounded-full flex items-center justify-center ${
                            deploymentStep >= 4
                              ? 'bg-green-500 text-white'
                              : 'bg-gray-300 text-gray-600'
                          }`}
                        >
                          {deploymentStep >= 4 ? (
                            <CheckCircle className="w-5 h-5" />
                          ) : (
                            <span className="text-sm font-medium">4</span>
                          )}
                        </div>
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900">Health Check</h4>
                          <p className="text-sm text-gray-600">
                            Verifying agent is running and healthy
                          </p>
                        </div>
                        {deploymentStep === 4 && !deploymentCompleted && (
                          <div className="w-6 h-6 rounded-full border-b-2 border-blue-600 animate-spin"></div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Deployment Logs */}
                  {showDeploymentLogs && (
                    <div className="overflow-y-auto p-4 mb-6 max-h-48 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                      {deploymentLogs.map((log, index) => (
                        <div key={index} className="mb-1">
                          <span className="text-gray-400">[{log.timestamp}]</span> {log.message}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Deployment Complete Section - Smooth transition in */}
                  {deploymentStep >= 4 && (
                    <div className="pt-6 mt-6 border-t border-gray-200">
                      <div className="mb-6 text-center">
                        <div className="flex justify-center items-center mx-auto mb-4 w-16 h-16 bg-green-100 rounded-full">
                          <CheckCircle className="w-8 h-8 text-green-600" />
                        </div>
                        <h3 className="mb-2 text-xl font-semibold text-gray-900">
                          Deployment Complete!
                        </h3>
                        <p className="text-gray-600">
                          Your agent is now live and ready to receive API calls
                        </p>
                      </div>

                      {/* API Endpoint Details */}
                      <div className="p-6 mb-6 bg-gray-50 rounded-lg">
                        <h4 className="mb-4 font-medium text-gray-900">Your Agent API Endpoint</h4>
                        <div className="space-y-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Base URL:</span>
                            <code className="px-3 py-1 font-mono text-sm text-blue-600 bg-white rounded border">
                              https://api.aitomatic.cloud
                            </code>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Agent ID:</span>
                            <code className="px-3 py-1 font-mono text-sm text-gray-800 bg-white rounded border">
                              {selectedAgent?.id || 'agent-123'}
                            </code>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Port:</span>
                            <code className="px-3 py-1 font-mono text-sm text-gray-800 bg-white rounded border">
                              443 (HTTPS)
                            </code>
                          </div>
                        </div>
                      </div>

                      {/* Simple Chat API Demo */}
                      <div className="p-6 mb-6 bg-blue-50 rounded-lg">
                        <h4 className="mb-4 font-medium text-gray-900">Simple Chat API Call</h4>
                        <div className="p-4 mb-4 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                          <div className="mb-2">
                            # Test your deployed agent with a simple chat API call:
                          </div>
                          <div className="text-blue-400">
                            curl -X POST https://api.aitomatic.cloud/agents/
                            {selectedAgent?.id || 'agent-123'}/chat \
                          </div>
                          <div className="text-blue-400">
                            {' '}
                            -H "Content-Type: application/json" \
                          </div>
                          <div className="text-blue-400">
                            {' '}
                            -H "Authorization: Bearer YOUR_API_KEY" \
                          </div>
                          <div className="text-blue-400">
                            {' '}
                            -d &apos;{'{'}&quot;message&quot;: &quot;Hello, how are you?&quot;{'}'}
                            &apos;
                          </div>
                        </div>
                        <p className="text-sm text-gray-600">
                          Copy this command to test your deployed agent from any application or
                          terminal
                        </p>
                      </div>

                      {/* Next Steps */}
                      <div className="p-6 bg-indigo-50 rounded-lg">
                        <h4 className="mb-3 font-medium text-gray-900">What&apos;s Next?</h4>
                        <div className="space-y-2 text-sm text-gray-600">
                          <div>
                            • <strong>Integrate</strong> this API into your applications
                          </div>
                          <div>
                            • <strong>Monitor</strong> agent performance and usage
                          </div>
                          <div>
                            • <strong>Scale</strong> your deployment as needed
                          </div>
                          <div>
                            • <strong>Manage</strong> your agent from the Aitomatic Cloud dashboard
                          </div>
                        </div>
                      </div>

                      {/* Close Button */}
                      <div className="mt-6 text-center">
                        <Button
                          onClick={() => {
                            setShowCloudDeployment(false);
                            setDeploymentStep(0);
                            setDeploymentLogs([]);
                            setDeploymentCompleted(false);
                          }}
                          variant="outline"
                          className="px-8"
                        >
                          Close
                        </Button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Docker Deployment Section */}
              {showDockerDeployment && !showCloudDeployment && (
                <div className="p-6 mb-8 bg-white rounded-xl border border-purple-200">
                  <div className="flex justify-between items-center mb-6">
                    <div className="flex gap-3 items-center">
                      <div className="flex justify-center items-center w-10 h-10 bg-purple-100 rounded-lg">
                        <Building className="w-5 h-5 text-purple-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">Docker Deployment</h3>
                        <p className="text-sm text-gray-600">
                          Deploy your agent to your own infrastructure
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => {
                        setShowDockerDeployment(false);
                        setDeploymentStep(0);
                        setDeploymentLogs([]);
                        setDeploymentCompleted(false);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      Back to Options
                    </Button>
                  </div>

                  {/* Docker Image Details */}
                  <div className="p-6 mb-6 bg-gray-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Docker Image Information</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Image Name:</span>
                        <code className="px-3 py-1 font-mono text-sm text-purple-600 bg-white rounded border">
                          aitomatic/dana-agent:{selectedAgent?.id || 'latest'}
                        </code>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Registry:</span>
                        <code className="px-3 py-1 font-mono text-sm text-gray-800 bg-white rounded border">
                          registry.aitomatic.cloud
                        </code>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Size:</span>
                        <span className="text-sm text-gray-900">~2.1 GB</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Base Image:</span>
                        <span className="text-sm text-gray-900">Ubuntu 22.04 + Python 3.11</span>
                      </div>
                    </div>
                  </div>

                  {/* Docker Commands */}
                  <div className="p-6 mb-6 bg-purple-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Quick Start Commands</h4>
                    <div className="space-y-4">
                      <div>
                        <div className="mb-2 text-sm font-medium text-gray-700">
                          1. Pull the Docker image:
                        </div>
                        <div className="p-4 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                          docker pull registry.aitomatic.cloud/aitomatic/dana-agent:
                          {selectedAgent?.id || 'latest'}
                        </div>
                      </div>

                      <div>
                        <div className="mb-2 text-sm font-medium text-gray-700">
                          2. Run the container:
                        </div>
                        <div className="p-4 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                          docker run -d \
                        </div>
                        <div className="px-4 pb-4 font-mono text-sm text-green-400 bg-gray-900 rounded-b-lg">
                          &nbsp;&nbsp;--name dana-agent-{selectedAgent?.id || 'latest'} \
                        </div>
                        <div className="px-4 pb-4 font-mono text-sm text-green-400 bg-gray-900 rounded-b-lg">
                          &nbsp;&nbsp;-p 8080:8080 \
                        </div>
                        <div className="px-4 pb-4 font-mono text-sm text-green-400 bg-gray-900 rounded-b-lg">
                          &nbsp;&nbsp;-e AGENT_ID={selectedAgent?.id || 'your-agent-id'} \
                        </div>
                        <div className="px-4 pb-4 font-mono text-sm text-green-400 bg-gray-900 rounded-b-lg">
                          &nbsp;&nbsp;registry.aitomatic.cloud/aitomatic/dana-agent:
                          {selectedAgent?.id || 'latest'}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Configuration Options */}
                  <div className="p-6 mb-6 bg-gray-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Configuration Options</h4>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="space-y-3">
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Custom port mapping</span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Environment variables</span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Volume mounts</span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Resource limits</span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Health checks</span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>Logging configuration</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Kubernetes Example */}
                  <div className="p-6 mb-6 bg-blue-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Kubernetes Deployment</h4>
                    <div className="mb-3 text-sm text-gray-600">
                      For Kubernetes users, here&apos;s a sample deployment YAML:
                    </div>
                    <div className="overflow-y-auto p-4 max-h-64 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                      <div className="text-blue-400">apiVersion: apps/v1</div>
                      <div className="text-blue-400">kind: Deployment</div>
                      <div className="text-blue-400">metadata:</div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;name: dana-agent-{selectedAgent?.id || 'latest'}
                      </div>
                      <div className="text-blue-400">spec:</div>
                      <div className="text-blue-400">&nbsp;&nbsp;replicas: 1</div>
                      <div className="text-blue-400">&nbsp;&nbsp;selector:</div>
                      <div className="text-blue-400">&nbsp;&nbsp;&nbsp;&nbsp;matchLabels:</div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;app: dana-agent
                      </div>
                      <div className="text-blue-400">&nbsp;&nbsp;template:</div>
                      <div className="text-blue-400">&nbsp;&nbsp;&nbsp;&nbsp;metadata:</div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;labels:
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;app: dana-agent
                      </div>
                      <div className="text-blue-400">&nbsp;&nbsp;&nbsp;&nbsp;spec:</div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;containers:
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- name: dana-agent
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;image:
                        registry.aitomatic.cloud/aitomatic/dana-agent:
                        {selectedAgent?.id || 'latest'}
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;ports:
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- containerPort: 8080
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;env:
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- name: AGENT_ID
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;value: &quot;
                        {selectedAgent?.id || 'your-agent-id'}&quot;
                      </div>
                    </div>
                  </div>

                  {/* API Testing */}
                  <div className="p-6 mb-6 bg-green-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Test Your Deployment</h4>
                    <div className="mb-3 text-sm text-gray-600">
                      Once deployed, test your agent with this curl command:
                    </div>
                    <div className="p-4 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                      <div className="text-blue-400">curl -X POST http://localhost:8000/chat \</div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;-H &quot;Content-Type: application/json&quot; \
                      </div>
                      <div className="text-blue-400">
                        &nbsp;&nbsp;-d &apos;{'{'}&quot;message&quot;: &quot;Hello, how are
                        you?&quot;{'}'}&apos;
                      </div>
                    </div>
                  </div>

                  {/* Close Button */}
                  <div className="text-center">
                    <Button
                      onClick={() => setShowDockerDeployment(false)}
                      variant="outline"
                      className="px-8"
                    >
                      Close
                    </Button>
                  </div>
                </div>
              )}

              {/* Local API Section */}
              {showLocalAPI && (
                <div className="p-6 mb-8 bg-white rounded-xl border border-green-200">
                  <div className="flex justify-between items-center mb-6">
                    <div className="flex gap-3 items-center">
                      <div className="flex justify-center items-center w-10 h-10 bg-green-100 rounded-lg">
                        <Code2 className="w-5 h-5 text-green-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                          Local Development Server
                        </h3>
                        <p className="text-sm text-gray-600">
                          Your agent is running locally for instant development & testing
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => {
                        setShowLocalAPI(false);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      Back to Options
                    </Button>
                  </div>

                  <div className="p-6 mb-6 bg-green-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Local API Endpoint</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Base URL:</span>
                        <code className="px-3 py-1 font-mono text-sm text-green-600 bg-white rounded border">
                          http://localhost:8080
                        </code>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Agent ID:</span>
                        <code className="px-3 py-1 font-mono text-sm text-gray-800 bg-white rounded border">
                          {selectedAgent?.id || 'N/A'}
                        </code>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Status:</span>
                        <span className="flex gap-2 items-center text-sm font-medium text-green-600">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          Running
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Port:</span>
                        <span className="text-sm text-gray-900">8080 (HTTP)</span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">API Path:</span>
                        <code className="px-3 py-1 font-mono text-sm text-blue-600 bg-white rounded border">
                          /api/chat/
                        </code>
                      </div>
                    </div>
                    <div className="p-3 mt-4 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="flex gap-3 items-start">
                        <div className="w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                          <svg
                            className="w-3 h-3 text-blue-600"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                        </div>
                        <div className="text-sm text-blue-800">
                          <p className="mb-1 font-medium">Ready to Test!</p>
                          <p>
                            Your agent is running locally. Use the cURL command below to test the
                            API endpoint.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Test with cURL */}
                  <div className="p-6 mb-6 bg-gray-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Test Your Agent API</h4>
                    <div className="relative p-4 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                      <div className="text-green-400">
                        curl -X POST http://localhost:8080/api/chat/ \
                      </div>
                      <div className="text-green-400"> -H "Content-Type: application/json" \</div>
                      <div className="text-green-400">
                        {' '}
                        -d &apos;{'{'}&quot;message&quot;: &quot;Can you analyze the current market
                        trends and provide investment recommendations?&quot;, &quot;agent_id&quot;:{' '}
                        {selectedAgent?.id || 'YOUR_AGENT_ID'}
                        {'}'}&apos;
                      </div>
                      <button
                        onClick={() => {
                          const curlCommand = `curl -X POST http://localhost:8080/api/chat/ \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Can you analyze the current market trends and provide investment recommendations?", "agent_id": ${selectedAgent?.id || 'YOUR_AGENT_ID'}}'`;
                          navigator.clipboard.writeText(curlCommand);
                          toast.success('cURL command copied to clipboard!');
                        }}
                        className="absolute top-2 right-2 p-2 text-gray-400 rounded transition-all duration-200 hover:text-white hover:bg-gray-800"
                        title="Copy cURL command"
                      >
                        <svg
                          className="w-4 h-4"
                          fill="none"
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2v8a2 2 0 002 2z"
                          />
                        </svg>
                      </button>
                    </div>
                    <p className="mt-3 text-sm text-gray-600">
                      Copy and paste this command into your terminal to test your agent. The API
                      will respond with your agent&apos;s logic and reasoning.
                    </p>
                  </div>

                  {/* Development Features */}
                  <div className="p-6 mb-6 bg-blue-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Development Features</h4>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="space-y-3">
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>Hot Reload:</strong> Code changes restart server automatically
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>Real-time Logs:</strong> See all requests and responses
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>Error Handling:</strong> Detailed debugging information
                          </span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>Fast Iteration:</strong> Test changes in seconds
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>Local Testing:</strong> No external dependencies
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>API Documentation:</strong> Auto-generated at /docs
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Quick Actions */}
                  <div className="p-6 bg-indigo-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Quick Actions</h4>
                    <div className="flex gap-3">
                      <Button
                        variant="outline"
                        className="flex-1 text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                        onClick={() => {
                          // Open API docs
                          window.open('http://localhost:8000/docs', '_blank');
                        }}
                      >
                        <BookOpen className="mr-2 w-4 h-4" />
                        View API Docs
                      </Button>
                      <Button
                        variant="outline"
                        className="flex-1 text-indigo-700 border-indigo-200 hover:bg-indigo-50"
                        onClick={() => {
                          // Copy endpoint to clipboard
                          navigator.clipboard.writeText('http://localhost:8000');
                          toast.success('Endpoint copied to clipboard!');
                        }}
                      >
                        <List className="mr-2 w-4 h-4" />
                        Copy Endpoint
                      </Button>
                    </div>
                  </div>
                </div>
              )}

              {/* Export Config Section */}
              {showExportConfig && (
                <div className="p-6 mb-8 bg-white rounded-xl border border-blue-200">
                  <div className="flex justify-between items-center mb-6">
                    <div className="flex gap-3 items-center">
                      <div className="flex justify-center items-center w-10 h-10 bg-blue-100 rounded-lg">
                        <List className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-gray-900">Export Agent Folder</h3>
                        <p className="text-sm text-gray-600">
                          Create portable agent packages with .na files
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={() => {
                        setShowExportConfig(false);
                      }}
                      variant="outline"
                      size="sm"
                    >
                      Back to Options
                    </Button>
                  </div>

                  {/* Agent Info */}
                  <div className="p-6 mb-6 bg-blue-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Agent Details</h4>
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Name:</span>
                        <span className="text-sm font-medium text-gray-900">
                          {selectedAgent?.name || 'My Agent'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">ID:</span>
                        <code className="px-3 py-1 font-mono text-sm text-gray-800 bg-white rounded border">
                          {selectedAgent?.id || 'agent-123'}
                        </code>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Description:</span>
                        <span className="text-sm text-gray-900">
                          {selectedAgent?.description || 'No description'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Created:</span>
                        <span className="text-sm text-gray-900">
                          {selectedAgent?.created_at
                            ? new Date(selectedAgent.created_at).toLocaleDateString()
                            : 'Unknown'}
                        </span>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Type:</span>
                        <span className="text-sm text-gray-900">Dana Agent</span>
                      </div>
                    </div>
                  </div>

                  {/* Agent Folder Structure */}
                  <div className="p-6 mb-6 bg-gray-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Agent Folder Structure</h4>
                    <div className="p-4 font-mono text-sm text-green-400 bg-gray-900 rounded-lg">
                      <div className="text-blue-400">agent_{selectedAgent?.id || '5_james'}/</div>
                      <div className="ml-4 text-gray-400">├── main.na</div>
                      <div className="ml-4 text-gray-400">├── knowledge.na</div>
                      <div className="ml-4 text-gray-400">├── methods.na</div>
                      <div className="ml-4 text-gray-400">├── tools.na</div>
                      <div className="ml-4 text-gray-400">├── workflows.na</div>
                      <div className="ml-4 text-gray-400">├── common.na</div>
                      <div className="ml-4 text-gray-400">├── domain_knowledge.json</div>
                      <div className="ml-4 text-gray-400">├── docs/</div>
                      <div className="ml-4 text-gray-400">├── knows/</div>
                      <div className="ml-4 text-gray-400">└── .cache/</div>
                    </div>
                    <p className="mt-3 text-sm text-gray-600">
                      Your agent consists of multiple .na files and supporting directories that work
                      together.
                    </p>
                  </div>

                  {/* Export Options */}
                  <div className="p-6 mb-6 bg-gray-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">Export Options</h4>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center p-4 bg-white rounded-lg border border-blue-200">
                        <div className="flex-1">
                          <div className="mb-1 font-medium text-gray-900">
                            Complete Agent Package
                          </div>
                          <div className="mb-2 text-sm text-gray-600">
                            Includes all .na files, configs, and supporting directories
                          </div>
                          <div className="inline-block px-2 py-1 text-xs text-blue-600 bg-blue-50 rounded">
                            Recommended for full agent transfer
                          </div>
                        </div>
                        <Button
                          onClick={async () => {
                            try {
                              const result = await apiService.exportAgentTar(
                                selectedAgent?.id || 0,
                                true,
                              );

                              if (result.success) {
                                // Download the tar file
                                const blob = await apiService.downloadAgentTar(
                                  selectedAgent?.id || 0,
                                  result.tar_path,
                                );
                                const url = window.URL.createObjectURL(blob);
                                const link = document.createElement('a');
                                link.href = url;
                                link.download = `agent_${selectedAgent?.id}_${new Date().toISOString().split('T')[0]}.tar.gz`;
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                window.URL.revokeObjectURL(url);

                                toast.success('Agent exported successfully!', {
                                  description: 'Your complete agent folder has been downloaded.',
                                });
                              } else {
                                toast.error('Export failed', {
                                  description: result.message || 'Failed to export agent folder.',
                                });
                              }
                            } catch {
                              toast.error('Export failed', {
                                description: 'Failed to export agent folder.',
                              });
                            }
                          }}
                          className="ml-4 text-white bg-blue-600 hover:bg-blue-700"
                        >
                          Export Folder
                        </Button>
                      </div>

                      <div className="flex justify-between items-center p-4 bg-white rounded-lg border border-gray-200">
                        <div className="flex-1">
                          <div className="mb-1 font-medium text-gray-900">Core Files Only</div>
                          <div className="mb-2 text-sm text-gray-600">
                            Just the essential .na files without cache and docs
                          </div>
                          <div className="inline-block px-2 py-1 text-xs text-gray-600 bg-gray-50 rounded">
                            Lightweight, for code sharing
                          </div>
                        </div>
                        <Button
                          variant="outline"
                          onClick={async () => {
                            try {
                              const result = await apiService.exportAgentTar(
                                selectedAgent?.id || 0,
                                false, // Don't include dependencies for core files only
                              );

                              if (result.success) {
                                // Download the tar file
                                const blob = await apiService.downloadAgentTar(
                                  selectedAgent?.id || 0,
                                  result.tar_path,
                                );
                                const url = window.URL.createObjectURL(blob);
                                const link = document.createElement('a');
                                link.href = url;
                                link.download = `agent_${selectedAgent?.id}_core_${new Date().toISOString().split('T')[0]}.tar.gz`;
                                document.body.appendChild(link);
                                link.click();
                                document.body.removeChild(link);
                                window.URL.revokeObjectURL(url);

                                toast.success('Core files exported!', {
                                  description: 'Your essential agent files have been downloaded.',
                                });
                              } else {
                                toast.error('Export failed', {
                                  description: result.message || 'Failed to export core files.',
                                });
                              }
                            } catch {
                              toast.error('Export failed', {
                                description: 'Failed to export core files.',
                              });
                            }
                          }}
                          className="ml-4"
                        >
                          Export Core Files
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Package Contents */}
                  <div className="p-6 mb-6 bg-indigo-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">What&apos;s Included</h4>
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                      <div className="space-y-3">
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>main.na:</strong> Main agent logic and entry point
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>knowledge.na:</strong> Agent knowledge base
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>methods.na:</strong> Agent methods and functions
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>tools.na:</strong> Available tools and capabilities
                          </span>
                        </div>
                      </div>
                      <div className="space-y-3">
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>workflows.na:</strong> Agent workflow definitions
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>common.na:</strong> Shared utilities and helpers
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>domain_knowledge.json:</strong> Structured knowledge data
                          </span>
                        </div>
                        <div className="flex gap-2 items-center text-sm text-gray-600">
                          <CheckCircle className="w-4 h-4 text-green-500" />
                          <span>
                            <strong>Supporting directories:</strong> docs, knows, .cache
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Sharing Instructions */}
                  <div className="p-6 bg-green-50 rounded-lg">
                    <h4 className="mb-4 font-medium text-gray-900">How to Share & Use</h4>
                    <div className="space-y-3 text-sm text-gray-600">
                      <div className="flex gap-2 items-start">
                        <div className="flex-shrink-0 mt-2 w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>
                          <strong>Team Collaboration:</strong> Share the agent folder with teammates
                          via zip, Git, or file sharing
                        </span>
                      </div>
                      <div className="flex gap-2 items-start">
                        <div className="flex-shrink-0 mt-2 w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>
                          <strong>Machine Transfer:</strong> Copy the folder to any machine with
                          Dana Studio
                        </span>
                      </div>
                      <div className="flex gap-2 items-start">
                        <div className="flex-shrink-0 mt-2 w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>
                          <strong>Version Control:</strong> Commit agent folders to Git repositories
                          for change tracking
                        </span>
                      </div>
                      <div className="flex gap-2 items-start">
                        <div className="flex-shrink-0 mt-2 w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>
                          <strong>Backup & Recovery:</strong> Keep copies of your agent folders for
                          safety
                        </span>
                      </div>
                      <div className="flex gap-2 items-start">
                        <div className="flex-shrink-0 mt-2 w-2 h-2 bg-green-500 rounded-full"></div>
                        <span>
                          <strong>Production Deployment:</strong> Use agent folders for consistent
                          deployment across environments
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Current Deployment Status - Only show when there's an actual deployment */}
              {!showCloudDeployment &&
                !showDockerDeployment &&
                !showLocalAPI &&
                !showExportConfig &&
                (selectedAgent as any)?.deployment && (
                  <div className="p-6 bg-white rounded-xl border border-gray-200">
                    <h3 className="mb-4 text-lg font-semibold text-gray-900">
                      Current Deployment Status
                    </h3>
                    <DeploymentStatusCard
                      agentId={selectedAgent?.id || 0}
                      onOpenDeploymentDialog={() => {
                        // This will open the deployment dialog if needed
                        setShowCloudDeployment(true);
                        simulateDeployment();
                      }}
                    />
                  </div>
                )}
            </div>
          </div>
        )}
      </div>

      {/* Chat pane */}
      {isChatSidebarOpen && (
        <ChatPane
          agentName={selectedAgent?.name || 'Agent'}
          isVisible={isChatSidebarOpen}
          onClose={() => closeChatSidebar()}
          selectedAgent={selectedAgent}
        />
      )}
    </div>
  );
};
