/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { MyAgentTab } from './MyAgentTab';
import { ExploreTab } from './ExploreTab';
import { Play } from 'iconoir-react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import {
  type AgentSuggestion,
  type BuildAgentFromSuggestionRequest,
  type WorkflowInfo,
} from '@/lib/api';
import { useCallback } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  ConnectionMode,
  NodeTypes,
  MarkerType,
} from 'reactflow';
import 'reactflow/dist/style.css';

const DOMAINS = ['All domains', 'Finance', 'Semiconductor', 'Sales', 'Engineering', 'Research'];

// Custom Node Component for React Flow
const WorkflowStepNode: React.FC<{
  data: { label: string; index: number; isMethodAvailable: boolean };
}> = ({ data }) => {
  return (
    <div className="relative group">
      <div
        className={`w-32 h-16 rounded-xl border-2 flex flex-col items-center justify-center text-center p-2 transition-all duration-300 shadow-md hover:shadow-lg ${
          data.isMethodAvailable
            ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-blue-400 hover:from-blue-100 hover:to-purple-100'
            : 'bg-gradient-to-br from-gray-50 to-gray-100 border-gray-400'
        }`}
      >
        {/* Node icon */}
        <div
          className={`w-6 h-6 rounded-full mb-1 flex items-center justify-center ${
            data.isMethodAvailable ? 'bg-gradient-to-r from-blue-500 to-purple-600' : 'bg-gray-400'
          }`}
        >
          <span className="text-white text-xs font-bold">{data.index}</span>
        </div>

        {/* Node label */}
        <span
          className={`text-xs font-medium leading-tight ${
            data.isMethodAvailable ? 'text-gray-800' : 'text-gray-500'
          }`}
        >
          {data.label}
        </span>

        {/* Method indicator */}
        {data.isMethodAvailable && (
          <div className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full border border-white">
            <div className="w-full h-full bg-green-400 rounded-full animate-pulse"></div>
          </div>
        )}
      </div>

      {/* Handle for connections - React Flow will use these */}
      <div className="absolute left-0 top-1/2 transform -translate-y-1/2 -translate-x-1 w-2 h-2 bg-blue-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
      <div className="absolute right-0 top-1/2 transform -translate-y-1/2 translate-x-1 w-2 h-2 bg-blue-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"></div>
    </div>
  );
};

// Node types for React Flow
const nodeTypes: NodeTypes = {
  workflowStep: WorkflowStepNode,
};

// Workflow Chart Component using React Flow
const WorkflowChart: React.FC<{
  workflow: { name: string; steps: string[] };
  methods: string[];
}> = ({ workflow, methods }) => {
  if (!workflow.steps || workflow.steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-gray-500 text-sm">
        <span>No workflow steps defined</span>
      </div>
    );
  }

  // Calculate center Y position for vertical alignment
  const centerY = 80;

  // Convert workflow steps to React Flow nodes
  const initialNodes: Node[] = workflow.steps.map((step, index) => ({
    id: `step-${index}`,
    type: 'workflowStep',
    position: { x: index * 180, y: centerY },
    data: {
      label: step
        .replace(/_/g, ' ')
        .replace(/([A-Z])/g, ' $1')
        .trim(),
      index: index + 1,
      isMethodAvailable: methods.includes(step),
    },
    draggable: false,
  }));

  // Add start and end nodes
  const startNode: Node = {
    id: 'start',
    type: 'input',
    position: { x: -200, y: centerY },
    data: { label: 'User message' },
    draggable: false,
    style: {
      background: '#dcfce7',
      border: '2px solid #22c55e',
      borderRadius: '12px',
      fontSize: '12px',
      fontWeight: 'bold',
      color: '#15803d',
      padding: '8px 12px',
    },
  };

  const endNode: Node = {
    id: 'end',
    type: 'output',
    position: { x: workflow.steps.length * 180, y: centerY },
    data: { label: 'Task Completed' },
    draggable: false,
    style: {
      background: '#dbeafe',
      border: '2px solid #3b82f6',
      borderRadius: '12px',
      fontSize: '12px',
      fontWeight: 'bold',
      color: '#1d4ed8',
      padding: '8px 12px',
    },
  };

  const nodes = [startNode, ...initialNodes, endNode];

  // Create edges between nodes
  const initialEdges: Edge[] = [];

  // Connect start to first step
  if (workflow.steps.length > 0) {
    initialEdges.push({
      id: 'start-to-step-0',
      source: 'start',
      target: 'step-0',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#3b82f6', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' },
    });
  }

  // Connect sequential steps
  for (let i = 0; i < workflow.steps.length - 1; i++) {
    initialEdges.push({
      id: `step-${i}-to-step-${i + 1}`,
      source: `step-${i}`,
      target: `step-${i + 1}`,
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#3b82f6', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' },
    });
  }

  // Connect last step to end
  if (workflow.steps.length > 0) {
    initialEdges.push({
      id: `step-${workflow.steps.length - 1}-to-end`,
      source: `step-${workflow.steps.length - 1}`,
      target: 'end',
      type: 'smoothstep',
      animated: true,
      style: { stroke: '#3b82f6', strokeWidth: 2 },
      markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' },
    });
  }

  const [flowNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [flowEdges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const onConnect = useCallback(() => {
    // Prevent new connections since this is a display-only flow
  }, []);

  return (
    <div className="h-64 w-full border border-gray-200 rounded-lg overflow-hidden">
      <ReactFlow
        nodes={flowNodes}
        edges={flowEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        connectionMode={ConnectionMode.Loose}
        fitView
        fitViewOptions={{
          padding: 0.1,
          includeHiddenNodes: false,
          minZoom: 0.5,
          maxZoom: 1.5,
        }}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
      >
        <Controls position="top-right" />
        <Background color="#f1f5f9" gap={16} />
      </ReactFlow>
    </div>
  );
};

// Tab configuration with URL-friendly identifiers
const TAB_CONFIG = {
  explore: 'Explore',
  my: 'My Agent',
} as const;

type TabId = keyof typeof TAB_CONFIG;

export default function AgentsPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { agents, fetchAgents } = useAgentStore();
  const [myAgentSearch, setMyAgentSearch] = useState('');
  const [exploreSearch, setExploreSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All domains');
  const [creating, setCreating] = useState(false);
  const [headerCollapsed, setHeaderCollapsed] = useState(false);
  const [showCreateAgentPopup, setShowCreateAgentPopup] = useState(false);
  const [userInput, setUserInput] = useState('');
  const [suggestions, setSuggestions] = useState<AgentSuggestion[]>([]);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [suggestionError, setSuggestionError] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [workflowInfos, setWorkflowInfos] = useState<Record<string, WorkflowInfo>>({});

  const [prebuiltAgents, setPrebuiltAgents] = useState<any[]>([]);

  // Agent display information mapping for UI
  const agentDisplayInfo: Record<string, { name: string; description: string }> = {
    sofia: {
      name: 'Essential Agent',
      description:
        'Financial Analysis Expert with focus on behavioral finance, technical analysis, and risk management',
    },
    jordan_belfort: {
      name: 'Data Analysis',
      description: 'Operational agent specialized in data processing and analysis workflows',
    },
    nova: {
      name: 'Autonomous',
      description: 'Self-directed agent capable of independent decision-making and task execution',
    },
    // Fallback mappings by name
    Sofia: {
      name: 'Q&A Agent',
      description:
        'Financial Analysis Expert with focus on behavioral finance, technical analysis, and risk management',
    },
    'Jordan Belfort': {
      name: 'Operational Agent',
      description: 'Specialized in data processing and analysis workflows',
    },
    Nova: {
      name: 'Autonomous Agent',
      description: 'Self-directed agent capable of independent decision-making and task execution',
    },
  };

  // Get activeTab from URL params, default to 'explore'
  const activeTabId = (searchParams.get('tab') as TabId) || 'explore';
  const activeTab = TAB_CONFIG[activeTabId];

  // Function to update activeTab in URL
  const setActiveTab = (tabId: TabId) => {
    const newSearchParams = new URLSearchParams(searchParams);
    newSearchParams.set('tab', tabId);
    setSearchParams(newSearchParams);
  };

  // Function to fetch prebuilt agents using axios API service
  const fetchPrebuiltAgents = async () => {
    try {
      const data = await apiService.getPrebuiltAgents();
      setPrebuiltAgents(data);
    } catch (error) {
      console.error('Error fetching prebuilt agents:', error);
      // Set empty array if API fails
      setPrebuiltAgents([]);
    }
  };

  useEffect(() => {
    // If no agents and no tab specified, default to explore
    if (agents && agents.length === 0 && !searchParams.get('tab')) {
      setActiveTab('explore');
    }
  }, [agents, searchParams]);

  useEffect(() => {
    fetchAgents();
    fetchPrebuiltAgents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Smart header behavior - collapse after scroll or user interaction
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY > 100) {
        setHeaderCollapsed(true);
      }
    };

    const handleUserInteraction = () => {
      setHeaderCollapsed(true);
    };

    window.addEventListener('scroll', handleScroll);

    // Collapse header after user interactions
    const searchInputs = document.querySelectorAll('input[type="text"]');
    searchInputs.forEach((input) => {
      input.addEventListener('focus', handleUserInteraction);
    });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      searchInputs.forEach((input) => {
        input.removeEventListener('focus', handleUserInteraction);
      });
    };
  }, []);

  // Filter prebuilt agents by domain and search
  const filteredAgents = prebuiltAgents.filter((agent: any) => {
    const domain = agent.config?.domain || 'Other';
    const matchesDomain = selectedDomain === 'All domains' || domain === selectedDomain;
    const matchesSearch =
      agent.name.toLowerCase().includes(exploreSearch.toLowerCase()) ||
      (agent.description || '').toLowerCase().includes(exploreSearch.toLowerCase()) ||
      (agent.details || '').toLowerCase().includes(exploreSearch.toLowerCase());
    return matchesDomain && matchesSearch;
  });

  const handleCreateAgent = async () => {
    setShowCreateAgentPopup(true);
  };

  const handleGetSuggestions = async () => {
    if (!userInput.trim()) return;

    setLoadingSuggestions(true);
    setSuggestionError('');

    try {
      const response = await apiService.getAgentSuggestions(userInput.trim());
      setSuggestions(response.suggestions);

      // Fetch workflow information for each suggestion
      const workflowData: Record<string, WorkflowInfo> = {};
      await Promise.all(
        response.suggestions.map(async (suggestion) => {
          try {
            const workflowInfo = await apiService.getPrebuiltAgentWorkflowInfo(suggestion.key);
            workflowData[suggestion.key] = workflowInfo;
          } catch (error) {
            console.error(`Failed to get workflow info for ${suggestion.key}:`, error);
            // Set empty workflow info as fallback
            workflowData[suggestion.key] = { workflows: [], methods: [] };
          }
        }),
      );

      setWorkflowInfos(workflowData);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Error getting suggestions:', error);
      setSuggestionError('Failed to get suggestions. Please try again.');
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const handleCreateAgentFromInput = async () => {
    setCreating(true);
    try {
      // Create agent with user input
      const newAgent = await apiService.createAgent({
        name: 'Untitled Agent',
        description: userInput,
        config: {},
      });
      if (newAgent && newAgent.id) {
        navigate(`/agents/${newAgent.id}`);
      }
    } catch (e) {
      console.error('Error creating agent:', e);
      // Optionally show error toast
    } finally {
      setCreating(false);
      setShowCreateAgentPopup(false);
      setUserInput('');
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  const handleCancelCreate = () => {
    setShowCreateAgentPopup(false);
    setUserInput('');
    setSuggestions([]);
    setShowSuggestions(false);
    setSuggestionError('');
  };

  const handleTryAgain = () => {
    setShowSuggestions(false);
    setSuggestions([]);
    setSuggestionError('');
  };

  const handleBuildFromSuggestion = async (suggestion: AgentSuggestion) => {
    setCreating(true);
    try {
      const buildRequest: BuildAgentFromSuggestionRequest = {
        prebuilt_key: suggestion.key,
        user_input: userInput,
        agent_name: `${suggestion.name} Assistant`,
      };

      const newAgent = await apiService.buildAgentFromSuggestion(buildRequest);
      if (newAgent && newAgent.id) {
        navigate(`/agents/${newAgent.id}`);
      }
    } catch (error) {
      console.error('Error building agent from suggestion:', error);
    } finally {
      setCreating(false);
      setShowCreateAgentPopup(false);
      setUserInput('');
      setSuggestions([]);
      setShowSuggestions(false);
    }
  };

  return (
    <div className="flex overflow-hidden flex-col w-full h-full">
      {/* Hero Section with Animated Background */}
      <div
        className={`hidden relative overflow-hidden transition-all duration-700 ease-out ${
          headerCollapsed
            ? 'bg-gradient-to-r to-purple-900 min-h-[200px] from-slate-900'
            : 'py-16 bg-gradient-to-br via-purple-900 min-h-[600px] from-slate-900 to-slate-900'
        }`}
      >
        {/* Animated Background Elements - Only show when expanded */}
        {!headerCollapsed && (
          <>
            <div className="absolute inset-0">
              <div className="absolute top-0 left-0 w-72 h-72 bg-purple-500 rounded-full opacity-20 mix-blend-multiply filter blur-xl animate-blob"></div>
              <div className="absolute top-0 right-0 w-72 h-72 bg-yellow-500 rounded-full opacity-20 mix-blend-multiply filter blur-xl animate-blob animation-delay-2000"></div>
              <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-500 rounded-full opacity-20 mix-blend-multiply filter blur-xl animate-blob animation-delay-4000"></div>
            </div>

            {/* Grid Pattern Overlay */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg%20width%3D%2260%22%20height%3D%2260%22%20viewBox%3D%220%200%2060%2060%22%20xmlns%3D%22http%3A//www.w3.org/2000/svg%22%3E%3Cg%20fill%3D%22none%22%20fill-rule%3D%22evenodd%22%3E%3Cg%20fill%3D%22%23ffffff%22%20fill-opacity%3D%220.05%22%3E%3Ccircle%20cx%3D%2230%22%20cy%3D%2230%22%20r%3D%221%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-30"></div>
          </>
        )}

        {/* Main Content with Smooth Transitions */}
        <div
          className={`relative z-10 flex flex-col items-center justify-center text-center transition-all duration-700 ease-out ${
            headerCollapsed ? 'overflow-hidden h-0' : 'px-6 min-h-[600px]'
          }`}
        >
          {/* Main Title with Enhanced Typography */}
          <div
            className={`transition-all duration-700 ease-out ${
              headerCollapsed ? 'mb-0 opacity-0 scale-75' : 'mb-8 opacity-100 scale-100'
            }`}
          >
            <h1 className="mb-2 text-7xl font-black tracking-tight leading-none text-white md:text-8xl">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 via-pink-400 to-yellow-400">
                Dana
              </span>
            </h1>
            <h2 className="mb-2 text-5xl font-black tracking-tight text-white md:text-6xl">
              Agent Studio
            </h2>
          </div>

          {/* Enhanced Subtitle */}
          <p
            className={`text-xl md:text-2xl text-gray-200 max-w-4xl leading-relaxed font-light transition-all duration-700 ease-out ${
              headerCollapsed ? 'mb-0 opacity-0 scale-75' : 'mb-12 opacity-100 scale-100'
            }`}
          >
            The complete platform for{' '}
            <span className="font-semibold text-purple-300">building, training, and deploying</span>{' '}
            Dana Expert Agents
          </p>

          {/* Feature Cards with Better Design */}
          <div
            className={`grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl transition-all duration-700 ease-out ${
              headerCollapsed ? 'mb-0 opacity-0 scale-75' : 'mb-16 opacity-100 scale-100'
            }`}
          >
            {/* Agent Maker - Available Now */}
            <div className="p-8 rounded-2xl border backdrop-blur-sm transition-all duration-500 group bg-white/10 border-white/20 hover:bg-white/20 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/20">
              <div className="flex justify-center items-center mx-auto mb-6 w-16 h-16 bg-gradient-to-r from-purple-400 to-pink-400 rounded-2xl shadow-lg">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h3 className="mb-3 text-xl font-bold text-white">Agent Maker</h3>
              <p className="text-sm leading-relaxed text-gray-300">
                Create Dana Expert Agents with domain expertise and learning capabilities
              </p>
            </div>

            {/* Experience Learner - Coming Soon */}
            <div className="relative p-8 rounded-2xl border backdrop-blur-sm transition-all duration-500 group bg-white/5 border-white/10 hover:scale-105">
              <div className="absolute top-4 right-4">
                <span className="px-2 py-1 text-xs font-semibold text-yellow-300 rounded-full border bg-yellow-500/20 border-yellow-400/40">
                  Coming Soon
                </span>
              </div>
              <div className="flex justify-center items-center mx-auto mb-6 w-16 h-16 bg-gradient-to-r from-pink-400 to-yellow-400 rounded-2xl shadow-lg opacity-60">
                <svg
                  className="w-8 h-8 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                  />
                </svg>
              </div>
              <h3 className="mb-3 text-xl font-bold text-white opacity-60">Experience Learner</h3>
              <p className="text-sm leading-relaxed text-gray-400 opacity-60">
                Dana Expert Agents that evolve and improve through continuous learning and feedback
              </p>
            </div>

            {/* App Generators - Coming Soon */}
            <div className="relative p-8 rounded-2xl border backdrop-blur-sm transition-all duration-500 group bg-white/5 border-white/10 hover:scale-105">
              <div className="absolute top-4 right-4">
                <span className="px-2 py-1 text-xs font-semibold text-yellow-300 rounded-full border bg-yellow-500/20 border-yellow-400/40">
                  Coming Soon
                </span>
              </div>
              <div className="flex justify-center items-center mx-auto mb-6 w-16 h-16 bg-gradient-to-r from-yellow-400 to-purple-400 rounded-2xl shadow-lg opacity-60">
                <svg
                  className="w-6 h-6 text-white"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                  />
                </svg>
              </div>
              <h3 className="mb-3 text-xl font-bold text-white opacity-60">App Generators</h3>
              <p className="text-sm leading-relaxed text-gray-400 opacity-60">
                Deploy Dana Expert Agents to web, iOS, and Android with built-in app generation
              </p>
            </div>
          </div>

          {/* Enhanced CTA Buttons */}
          <div
            className={`flex flex-col items-center gap-4 transition-all duration-700 ease-out ${
              headerCollapsed ? 'opacity-0 scale-75' : 'opacity-100 scale-100'
            }`}
          >
            <button
              onClick={() => {
                const element = document.getElementById('pre-trained-agents');
                element?.scrollIntoView({ behavior: 'smooth' });
              }}
              className="flex gap-3 items-center text-lg text-gray-300 transition-colors duration-300 cursor-pointer hover:text-white group"
            >
              <svg
                className="w-6 h-6 animate-bounce group-hover:animate-pulse"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M19 14l-7 7m0 0l-7-7m7 7V3"
                />
              </svg>
              <span className="font-medium">Explore agents below</span>
            </button>
          </div>
        </div>

        {/* Enhanced Floating Elements - Only show when expanded */}
        {!headerCollapsed && (
          <>
            <div className="absolute top-20 right-20 w-4 h-4 bg-yellow-400 rounded-full animate-ping"></div>
            <div className="absolute bottom-20 left-20 w-3 h-3 bg-purple-400 rounded-full animate-pulse"></div>
            <div className="absolute top-40 left-40 w-2 h-2 bg-pink-400 rounded-full animate-bounce"></div>
          </>
        )}

        {/* Compact Header with Highlights - Show when collapsed */}
        <div
          className={`absolute inset-0 flex items-center justify-center transition-all duration-700 ease-out ${
            headerCollapsed ? 'opacity-100 scale-100' : 'opacity-0 scale-75 pointer-events-none'
          }`}
        >
          <div className="flex flex-col gap-4 items-center">
            {/* Main Title with Gradient Highlight */}
            <h1 className="text-3xl font-bold text-white">
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                Dana Agent Studio
              </span>
            </h1>

            {/* Feature Status Badges */}
            <div className="flex gap-3 items-center">
              <span className="px-3 py-1.5 text-sm font-semibold bg-green-500/20 text-green-300 border border-green-400/40 rounded-full shadow-lg">
                🚀 Agent Maker
              </span>
            </div>

            {/* Subtle Description */}
            <p className="max-w-md text-sm text-center text-gray-300">
              The complete platform for building, training, and deploying Dana Expert Agents
            </p>
          </div>
        </div>
      </div>

      {/* Content Section */}
      <div className="flex-1 p-8 bg-white">
        {/* Search and Navigation */}
        <div className="flex flex-col gap-4 mb-8 md:flex-row md:items-center md:justify-between">
          <div className="flex flex-col gap-4 justify-between items-center w-full md:flex-row">
            <div className="relative w-full md:w-72">
              <svg
                className="absolute left-3 top-1/2 w-5 h-5 text-gray-400 transform -translate-y-1/2"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                />
              </svg>
              <input
                type="text"
                placeholder="Search agents..."
                value={activeTab === 'My Agent' ? myAgentSearch : exploreSearch}
                onChange={(e) =>
                  activeTab === 'My Agent'
                    ? setMyAgentSearch(e.target.value)
                    : setExploreSearch(e.target.value)
                }
                className="py-3 pr-4 pl-10 w-full text-base text-gray-900 rounded-sm border border-gray-200 transition-all duration-300 focus:outline-none focus:bg-white focus:shadow-md"
              />
            </div>
          </div>
        </div>

        {/* Enhanced Tabs */}
        <div className="flex gap-4 mb-8 border-b border-gray-200">
          <button
            className={`py-3  cursor-pointer font-semibold border-b-2 transition-all duration-300 rounded-t-lg ${
              activeTab === 'Explore'
                ? 'border-brand-500 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-brand-600'
            }`}
            onClick={() => setActiveTab('explore')}
          >
            <span className="flex gap-2 items-center">Pre-trained Agents</span>
          </button>
          <button
            className={`py-3 cursor-pointer font-semibold border-b-2 transition-all duration-300 rounded-t-lg ${
              activeTab === 'My Agent'
                ? 'border-brand-500 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-brand-600'
            }`}
            onClick={() => setActiveTab('my')}
          >
            <span className="flex gap-2 items-center">My Agents</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'My Agent' && (
          <MyAgentTab
            agents={agents.filter(
              (agent) =>
                agent.name.toLowerCase().includes(myAgentSearch.toLowerCase()) ||
                (agent.description || '').toLowerCase().includes(myAgentSearch.toLowerCase()),
            )}
            navigate={navigate}
            handleCreateAgent={handleCreateAgent}
            creating={creating}
          />
        )}
        {activeTab === 'Explore' && (
          <div id="pre-trained-agents">
            <ExploreTab
              filteredAgents={filteredAgents}
              selectedDomain={selectedDomain}
              setSelectedDomain={setSelectedDomain}
              navigate={navigate}
              DOMAINS={DOMAINS}
              handleCreateAgent={handleCreateAgent}
              creating={creating}
            />
          </div>
        )}
      </div>

      {/* Create Agent Popup */}
      <Dialog open={showCreateAgentPopup} onOpenChange={setShowCreateAgentPopup}>
        <DialogContent
          className={`${showSuggestions && suggestions.length > 0 ? 'sm:max-w-[1000px]' : 'sm:max-w-xl'} max-h-[80vh] overflow-y-auto`}
        >
          <DialogHeader>
            <DialogTitle>Train Your Own Agent</DialogTitle>
          </DialogHeader>

          <div className="flex space-y-4 flex-col">
            <div className="flex w-full flex-col gap-2">
              <label className="block text-md font-medium text-gray-700 mb-4">
                What your agent will do?
              </label>
              <textarea
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="e.g. I want an agent that can help me with financial analysis"
                className="w-full p-3 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent"
                rows={4}
                autoFocus
              />
              {/* Regenerate Button */}
              {showSuggestions && suggestions.length > 0 && (
                <div className="flex">
                  <Button
                    onClick={handleGetSuggestions}
                    variant="outline"
                    size="sm"
                    className="text-sm"
                    disabled={loadingSuggestions}
                  >
                    {loadingSuggestions ? (
                      <div className="flex items-center gap-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                        <span>Regenerating...</span>
                      </div>
                    ) : (
                      'Regenerate Suggestions'
                    )}
                  </Button>
                </div>
              )}
            </div>

            {/* Error State */}
            {suggestionError && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{suggestionError}</p>
              </div>
            )}

            {/* Suggestions */}
            {showSuggestions && suggestions.length > 0 && (
              <div className="space-y-4">
                <div className="flex flex-col justify-between">
                  <h3 className="text-lg font-medium text-gray-900">
                    Templates that fit your agent
                  </h3>
                  <p className="text-sm text-gray-500">
                    Agent template includes pre-built code and workflows to get you started.
                  </p>
                </div>

                <div className="space-y-6">
                  {suggestions.map((suggestion, index) => {
                    const workflowInfo = workflowInfos[suggestion.key] || {
                      workflows: [],
                      methods: [],
                    };
                    const mainWorkflow =
                      workflowInfo.workflows.find((w) => w.name === 'final_workflow') ||
                      workflowInfo.workflows[0];

                    return (
                      <div
                        key={suggestion.key}
                        className="relative overflow-hidden bg-gradient-to-br from-white to-gray-50 border border-gray-200 rounded-xl p-6 shadow-sm hover:shadow-md transition-all duration-300"
                      >
                        {/* Background Pattern */}
                        <div className="absolute inset-0 opacity-5">
                          <div className="absolute top-0 left-0 w-32 h-32 bg-gradient-to-br from-blue-400 to-purple-600 rounded-full blur-3xl"></div>
                          <div className="absolute bottom-0 right-0 w-24 h-24 bg-gradient-to-br from-pink-400 to-orange-500 rounded-full blur-3xl"></div>
                        </div>

                        <div className="relative z-10">
                          {/* Header Section */}
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <div className="flex items-center gap-3 mb-2">
                                <div>
                                  <div>
                                    <h4 className="font-semibold text-md text-gray-900">
                                      {(() => {
                                        console.log('Suggestion debug:', {
                                          key: suggestion.key,
                                          name: suggestion.name,
                                        });
                                        const agentInfo =
                                          agentDisplayInfo[suggestion.key] ||
                                          agentDisplayInfo[suggestion.name];
                                        return agentInfo?.name || suggestion.name;
                                      })()}
                                    </h4>
                                    <p className="text-sm text-gray-500 mt-1">
                                      {(() => {
                                        const agentInfo =
                                          agentDisplayInfo[suggestion.key] ||
                                          agentDisplayInfo[suggestion.name];
                                        return agentInfo?.description || '';
                                      })()}
                                    </p>
                                  </div>
                                </div>
                              </div>
                            </div>

                            <Button
                              onClick={() => handleBuildFromSuggestion(suggestion)}
                              variant="default"
                              size="lg"
                              disabled={creating}
                            >
                              {creating ? (
                                <div className="flex items-center gap-2">
                                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                                  <span className="text-sm">Starting...</span>
                                </div>
                              ) : (
                                <div className="flex items-center gap-2">
                                  <span className="text-sm font-semibold">Select</span>
                                </div>
                              )}
                            </Button>
                          </div>

                          {/* Workflow Chart Visualization */}
                          {mainWorkflow && mainWorkflow.steps.length > 0 && (
                            <div className=" ">
                              <h5 className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
                                <span>Workflow Chart</span>
                              </h5>

                              {/* Interactive Workflow Chart */}
                              <WorkflowChart
                                workflow={mainWorkflow}
                                methods={workflowInfo.methods}
                              />
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="flex gap-2 sm:flex-row">
            {!showSuggestions && (
              <Button
                onClick={handleGetSuggestions}
                variant="default"
                className="w-full "
                disabled={loadingSuggestions || !userInput.trim()}
              >
                {loadingSuggestions ? 'Getting started...' : 'Start training'}
              </Button>
            )}
            {/* <Button
              onClick={handleCreateAgentFromInput}
              variant="outline"
              className="w-full sm:w-auto"
              disabled={creating || !userInput.trim()}
            >
              {creating ? 'Creating...' : 'Create Custom Agent'}
            </Button> */}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
