import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { IconSearch } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';

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
  const { agents, isLoading, createAgent } = useAgentStore();
  const [search, setSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All domains');
  const [creating, setCreating] = useState(false);

  // Use mock data only if not loading and agents is empty
  const useMock = !isLoading && (!agents || agents.length === 0);
  const displayAgents = useMock ? MOCK_AGENTS : agents;

  // Filter by domain and search
  const filteredAgents = displayAgents.filter((agent) => {
    const domain = isMockAgent(agent) ? agent.domain : agent.config?.domain || 'Other';
    const matchesDomain = selectedDomain === 'All domains' || domain === selectedDomain;
    const details = isMockAgent(agent) ? agent.details : '';
    const matchesSearch =
      agent.name.toLowerCase().includes(search.toLowerCase()) ||
      (agent.description || '').toLowerCase().includes(search.toLowerCase()) ||
      (details && details.toLowerCase().includes(search.toLowerCase()));
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
      {/* Header section */}
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

      {/* Domain tabs and search */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
        <div className="flex gap-2 flex-wrap">
          {DOMAINS.map((domain) => (
            <Button
              key={domain}
              variant={selectedDomain === domain ? 'default' : 'outline'}
              className={`rounded-full px-5 py-1 text-base font-medium ${selectedDomain === domain ? '' : 'bg-white'}`}
              onClick={() => setSelectedDomain(domain)}
            >
              {domain}
            </Button>
          ))}
        </div>
        <div className="relative w-full md:w-72">
          <IconSearch className="absolute left-3 top-1/2 w-5 h-5 text-gray-400 transform -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-200 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500 text-base"
          />
        </div>
      </div>

      {/* Agent cards grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {filteredAgents.map((agent) => (
          <div
            key={agent.id}
            className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-4 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/agents/${agent.id}/chat`)}
          >
            <div className="flex items-center gap-4">
              {isMockAgent(agent) ? (
                <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${agent.avatarColor} flex items-center justify-center text-white text-lg font-bold`}></div>
              ) : (
                <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-lg font-bold">
                  {agent.name[0]}
                </div>
              )}
              <div className="flex flex-col flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold text-gray-900">{agent.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium border border-gray-200 ml-2">
                    {isMockAgent(agent) ? agent.domain : agent.config?.domain || 'Other'}
                  </span>
                </div>
                <span className="text-gray-500 text-sm mt-1">{agent.description}</span>
              </div>
            </div>
            <div className="text-gray-600 text-sm min-h-[40px]">{isMockAgent(agent) ? agent.details : ''}</div>
            <div className="flex items-center justify-between mt-2">
              <span className="text-gray-500 text-xs">{isMockAgent(agent) ? `${agent.accuracy}% accuracy` : ''}</span>
              <span className="flex items-center gap-1 text-yellow-500 font-semibold text-sm">
                {isMockAgent(agent) ? (
                  <>
                    <svg width="18" height="18" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.286 3.967a1 1 0 00.95.69h4.175c.969 0 1.371 1.24.588 1.81l-3.38 2.455a1 1 0 00-.364 1.118l1.287 3.966c.3.922-.755 1.688-1.54 1.118l-3.38-2.454a1 1 0 00-1.175 0l-3.38 2.454c-.784.57-1.838-.196-1.54-1.118l1.287-3.966a1 1 0 00-.364-1.118L2.04 9.394c-.783-.57-.38-1.81.588-1.81h4.175a1 1 0 00.95-.69l1.286-3.967z" /></svg>
                    {agent.rating}
                  </>
                ) : null}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
