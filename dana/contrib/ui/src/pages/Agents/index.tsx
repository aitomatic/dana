import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { MyAgentTab } from './MyAgentTab';
import { ExploreTab } from './ExploreTab';


const DOMAINS = ['All domains', 'Finance', 'Semiconductor', 'Sales', 'Engineering', 'Research'];


export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, fetchAgents, createAgent } = useAgentStore();
  const [myAgentSearch, setMyAgentSearch] = useState('');
  const [exploreSearch, setExploreSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All domains');
  const [creating, setCreating] = useState(false);
  const [prebuiltAgents, setPrebuiltAgents] = useState<any[]>([]);

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

  // Tabs: My Agent, Explore
  const [activeTab, setActiveTab] = useState(() => (agents && agents.length === 0 ? 'Explore' : 'My Agent'));
  useEffect(() => {
    if (agents && agents.length === 0) setActiveTab('Explore');
  }, [agents]);

  useEffect(() => {
    fetchAgents();
    fetchPrebuiltAgents();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  console.log('prebuiltAgents', prebuiltAgents);

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
          navigate={navigate}
          DOMAINS={DOMAINS}
        />
      )}
    </div>
  );
}
