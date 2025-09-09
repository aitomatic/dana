/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { MyAgentTab } from './MyAgentTab';
import { ExploreTab } from './ExploreTab';

const DOMAINS = ['All domains', 'Finance', 'Semiconductor', 'Sales', 'Engineering', 'Research'];

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

  const [prebuiltAgents, setPrebuiltAgents] = useState<any[]>([]);

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
    setCreating(true);
    try {
      // Minimal default agent payload
      const newAgent = await apiService.createAgent({
        name: 'Untitled Agent',
        description: '',
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
            <span className="flex gap-2 items-center">

              Pre-trained Agents
            </span>
          </button>
          <button
            className={`py-3 cursor-pointer font-semibold border-b-2 transition-all duration-300 rounded-t-lg ${
              activeTab === 'My Agent'
                ? 'border-brand-500 text-brand-600'
                : 'border-transparent text-gray-500 hover:text-brand-600'
            }`}
            onClick={() => setActiveTab('my')}
          >
            <span className="flex gap-2 items-center">
              My Agents
            </span>
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
    </div>
  );
}
