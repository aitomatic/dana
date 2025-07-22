import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { MyAgentTab } from './MyAgentTab';
import { ExploreTab } from './ExploreTab';

// Mock agent data for demo UI
const MOCK_AGENTS = [
  {
    id: 1,
    name: 'Edison',
    description: 'Chip Design Consultant',
    domain: 'Finance',
    details: 'Advanced semiconductor design validation, process optimization, and failure analysis expertise',
    accuracy: 98,
    rating: 4.9,
    avatarColor: 'from-purple-400 to-blue-400',
  },
  {
    id: 2,
    name: 'Sophia',
    description: 'Personal Finance Advisor',
    domain: 'Finance',
    details: 'Comprehensive budgeting, savings optimization, and investment guidance for individual clients',
    accuracy: 97.2,
    rating: 4.8,
    avatarColor: 'from-purple-400 to-green-400',
  },
  {
    id: 3,
    name: 'Marcus',
    description: 'Investment Analysis Specialist',
    domain: 'Semiconductor',
    details: 'Expert in financial modeling, risk assessment, and market analysis with real-time data integration',
    accuracy: 99.2,
    rating: 5.0,
    avatarColor: 'from-green-400 to-blue-400',
  },
  {
    id: 4,
    name: 'Nova',
    description: 'Supply Chain Optimizer',
    domain: 'Semiconductor',
    details: 'Electronics component sourcing, inventory management, and production scheduling specialist',
    accuracy: 98,
    rating: 4.8,
    avatarColor: 'from-yellow-400 to-purple-400',
  },
  {
    id: 5,
    name: 'Darwin',
    description: 'Research Assistant',
    domain: 'Research',
    details: 'Paper analysis, citation management, and research methodology guidance',
    accuracy: 98,
    rating: 4.9,
    avatarColor: 'from-purple-400 to-pink-400',
  },
  {
    id: 6,
    name: 'Sophia',
    description: 'Personal Finance Advisor',
    domain: 'Finance',
    details: 'Comprehensive budgeting, savings optimization, and investment guidance for individual clients',
    accuracy: 98,
    rating: 4.9,
    avatarColor: 'from-blue-400 to-green-400',
  },
];

const DOMAINS = ['All domains', 'Finance', 'Semiconductor', 'Sales', 'Engineering', 'Research'];

// Helper type guard for mock agents
function isMockAgent(agent: any): agent is typeof MOCK_AGENTS[number] {
  return 'avatarColor' in agent && 'domain' in agent && 'details' in agent;
}

export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, fetchAgents, isLoading, createAgent } = useAgentStore();
  const [myAgentSearch, setMyAgentSearch] = useState('');
  const [exploreSearch, setExploreSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All domains');
  const [creating, setCreating] = useState(false);

  // Use mock data only if not loading and agents is empty
  const useMock = !isLoading && (!agents || agents.length === 0);
  const displayAgents = useMock ? MOCK_AGENTS : agents;

  // Tabs: My Agent, Explore
  const [activeTab, setActiveTab] = useState(() => (agents && agents.length === 0 ? 'Explore' : 'My Agent'));
  useEffect(() => {
    if (agents && agents.length === 0) setActiveTab('Explore');
  }, [agents]);

  useEffect(() => {
    fetchAgents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Filter by domain and search
  const filteredAgents = displayAgents.filter((agent) => {
    const domain = isMockAgent(agent) ? agent.domain : agent.config?.domain || 'Other';
    const matchesDomain = selectedDomain === 'All domains' || domain === selectedDomain;
    const details = isMockAgent(agent) ? agent.details : '';
    const searchValue = activeTab === 'Explore' ? exploreSearch : myAgentSearch;
    const matchesSearch =
      agent.name.toLowerCase().includes(searchValue.toLowerCase()) ||
      (agent.description || '').toLowerCase().includes(searchValue.toLowerCase()) ||
      (details && details.toLowerCase().includes(searchValue.toLowerCase()));
    return matchesDomain && matchesSearch;
  });

  const handleCreateAgent = async () => {
    setCreating(true);
    try {
      // Minimal default agent payload
      const newAgent = await createAgent({
        name: 'Untitled Agent',
        description: '',
        config: {},
      });
      if (newAgent && newAgent.id) {
        navigate(`/agents/${newAgent.id}`);
      }
    } catch (e) {
      // Optionally show error toast
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="flex flex-col h-full w-full p-8">
      <div className="bg-gradient-to-r from-[#b7c6f9] to-[#e0e7ff] rounded-2xl p-8 mb-8 flex flex-col md:flex-row items-center justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Train production-ready AI agents</h2>
          <p className="text-gray-600 text-base max-w-xl">Create your first Domain-Expert Agent to explore the power of agent</p>
        </div>
        <Button
          onClick={handleCreateAgent}
          variant="default"
          size="lg"
          className="mt-4 md:mt-0"
          disabled={creating}
        >
          {creating ? 'Creating...' : '+ New Agent'}
        </Button>
      </div>
      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${activeTab === 'My Agent' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-blue-600'}`}
          onClick={() => setActiveTab('My Agent')}
        >
          My Agent
        </button>
        <button
          className={`px-4 py-2 font-medium border-b-2 transition-colors ${activeTab === 'Explore' ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-blue-600'}`}
          onClick={() => setActiveTab('Explore')}
        >
          Explore
        </button>
      </div>
      {/* Tab Content */}
      {activeTab === 'My Agent' && (
        <MyAgentTab
          agents={agents}
          search={myAgentSearch}
          setSearch={setMyAgentSearch}
          navigate={navigate}
        />
      )}
      {activeTab === 'Explore' && (
        <ExploreTab
          filteredAgents={filteredAgents}
          search={exploreSearch}
          setSearch={setExploreSearch}
          selectedDomain={selectedDomain}
          setSelectedDomain={setSelectedDomain}
          handleCreateAgent={handleCreateAgent}
          creating={creating}
          navigate={navigate}
          isMockAgent={isMockAgent}
          DOMAINS={DOMAINS}
        />
      )}
    </div>
  );
}
