import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { MyAgentTab } from './MyAgentTab';
import { ExploreTab } from './ExploreTab';
import { Button } from '@/components/ui/button';
import { Plus } from 'iconoir-react';

const DOMAINS = ['All domains', 'Finance', 'Semiconductor', 'Sales', 'Engineering', 'Research'];

export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, fetchAgents } = useAgentStore();
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
  const [activeTab, setActiveTab] = useState(() =>
    agents && agents.length === 0 ? 'Explore' : 'My Agent',
  );
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
      const newAgent = await apiService.createAgent({
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
    <div className="flex flex-col p-8 w-full h-full">
      {/* Top section with Search and Train Agent button */}
      <div className="flex flex-col gap-4 mb-6 md:flex-row md:items-center md:justify-between">
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
              className="py-2 pr-4 pl-10 w-full text-base text-gray-900 bg-white rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <Button
            onClick={handleCreateAgent}
            variant="default"
            disabled={creating}
            className="flex hover:bg-brand-700 items-center gap-2">
            <Plus style={{ width: '20', height: '20' }} />
            <label className="text-sm font-semibold">Train an Agent</label>
          </Button>
        </div>
      </div>
      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200">
        <button
          className={` py-2 cursor-pointer font-semibold border-b-2 transition-colors ${activeTab === 'My Agent' ? 'border-blue-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-brand-600'}`}
          onClick={() => setActiveTab('My Agent')}
        >
          My Agent
        </button>
        <button
          className={`ml-2 py-2 cursor-pointer font-semibold border-b-2 transition-colors ${activeTab === 'Explore' ? 'border-blue-600 text-brand-600' : 'border-transparent text-gray-500 hover:text-brand-600'}`}
          onClick={() => setActiveTab('Explore')}
        >
          Pre-trained Agent
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
        />
      )}
      {activeTab === 'Explore' && (
        <ExploreTab
          filteredAgents={filteredAgents}
          selectedDomain={selectedDomain}
          setSelectedDomain={setSelectedDomain}
          navigate={navigate}
          DOMAINS={DOMAINS}
        />
      )}
    </div>
  );
}
