import { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { IconPlus, IconSearch } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';

export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, fetchAgents, isLoading } = useAgentStore();
  const [search, setSearch] = useState('');

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  // Filter agents by search
  const filteredAgents = agents.filter(
    (agent) =>
      agent.name.toLowerCase().includes(search.toLowerCase()) ||
      (agent.description || '').toLowerCase().includes(search.toLowerCase()),
  );

  console.log(filteredAgents);

  return (
    <div className="flex flex-col h-full w-full p-8">
      {/* Top bar */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4 w-full max-w-xl">
          <div className="relative flex-1">
            <IconSearch className="absolute left-3 top-1/2 w-5 h-5 text-gray-400 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-10 pr-4 py-2 w-full rounded-lg border border-gray-200 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-brand-500 text-base"
            />
          </div>
          <Button
            variant="outline"
            className="flex items-center gap-2 px-4 py-2 rounded-lg border border-gray-200 text-gray-700 font-semibold"
          >
            <svg
              width="20"
              height="20"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              className="w-5 h-5"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M3 6h18M3 12h18M3 18h18"
              />
            </svg>
            Filter
          </Button>
        </div>
        <Button
          onClick={() => navigate('/agents/create')}
          variant="default"
          size="lg"
          className="ml-4"
        >
          <IconPlus className="w-5 h-5 mr-2" />
          Create New
        </Button>
      </div>

      {/* Agents list */}
      {isLoading ? (
        <div className="flex justify-center items-center h-full w-full">
          <span className="text-gray-400 text-lg">Loading agents...</span>
        </div>
      ) : filteredAgents.length === 0 ? (
        <div className="flex justify-center items-center h-full w-full">
          <div className="flex flex-col items-center max-w-md text-center">
            <img src={'/static/images/empty-agent.svg'} alt="empty dxa" className="size-48" />
            <h1 className="py-4 text-2xl font-semibold text-gray-900">No Domain-Expert Agent</h1>
            <p className="mb-8 leading-relaxed text-gray-600">
              Create your first Domain-Expert Agent to explore the power of agent
            </p>
            <Button onClick={() => navigate('/agents/create')} variant="default" size="lg">
              <IconPlus className="w-4 h-4" />
              New Agent
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {filteredAgents.map((agent) => (
            <div
              key={agent.id}
              className="bg-white rounded-lg border border-gray-200 p-6 flex hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => navigate(`/agents/${agent.id}`)}
            >
              <div className="flex flex-col gap-4">
                <img
                  src={`/agent-avatar${agent.config?.avatar}`}
                  alt="Agent avatar"
                  className="rounded-full w-12 h-12 object-cover border border-gray-200"
                />
                <div className="flex flex-col items-start">
                  <span className="text-xl font-bold text-gray-900">{agent.name}</span>
                  <span className="text-gray-500 text-base mt-1">
                    {agent.description || agent?.name || 'No description'}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
