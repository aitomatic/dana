import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { apiService } from '@/lib/api';
import { MyAgentTab } from './MyAgentTab';
import { ExploreTab } from './ExploreTab';

const DOMAINS = ['All domains', 'Finance', 'Semiconductor', 'Sales', 'Engineering', 'Research'];

export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, fetchAgents } = useAgentStore();
  const [myAgentSearch, setMyAgentSearch] = useState('');
  const [exploreSearch, setExploreSearch] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All domains');

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

  return (
    <div className="flex flex-col p-8 w-full h-full">
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
          Pre-trained Agent
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
