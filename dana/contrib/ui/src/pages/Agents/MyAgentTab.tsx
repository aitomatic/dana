import React, { useState } from 'react';
import { IconSearch } from '@tabler/icons-react';
import { Button } from '@/components/ui/button';
import { useAgentStore } from '@/stores';

// Helper function to format dates in a user-friendly way
const formatDate = (dateString: string | undefined): string => {
  if (!dateString) return '';

  try {
    const date = new Date(dateString);
    const now = new Date();

    // Check if it's the same day by comparing dates (not time)
    const dateOnly = new Date(date.getFullYear(), date.getMonth(), date.getDate());
    const nowOnly = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const diffTime = nowOnly.getTime() - dateOnly.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return 'Today';
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else if (diffDays < 30) {
      const weeks = Math.floor(diffDays / 7);
      return weeks === 1 ? '1 week ago' : `${weeks} weeks ago`;
    } else if (diffDays < 365) {
      const months = Math.floor(diffDays / 30);
      return months === 1 ? '1 month ago' : `${months} months ago`;
    } else {
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
  } catch (error) {
    return '';
  }
};

export const MyAgentTab: React.FC<{
  agents: any[];
  search: string;
  setSearch: (s: string) => void;
  navigate: (url: string) => void;
}> = ({ agents, search, setSearch, navigate }) => {
  const [creating, setCreating] = useState(false);
  const { createAgent } = useAgentStore();

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
    <>
      <div className="bg-gradient-to-r from-[#b7c6f9] to-[#e0e7ff] rounded-2xl p-8 mb-8 flex flex-col md:flex-row items-center justify-between">
        <div className="flex flex-col gap-2">
          <h2 className="mb-2 text-2xl font-bold text-gray-900">
            Train production-ready AI agents
          </h2>
          <p className="max-w-xl text-base text-gray-600">
            Create your first Domain-Expert Agent to explore the power of agent
          </p>
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
      <div className="flex justify-between items-center mb-8">
        <div className="text-lg font-semibold">My Trained Agents</div>
        <div className="flex gap-4 items-center w-full max-w-xl">
          <div className="relative flex-1">
            <IconSearch className="absolute left-3 top-1/2 w-5 h-5 text-gray-400 transform -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="py-2 pr-4 pl-10 w-full text-base text-gray-900 bg-white rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-brand-500"
            />
          </div>
        </div>
      </div>
      {/* User's agents list */}
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
        {agents && agents.length > 0 ? (
          agents
            .filter(
              (agent) =>
                agent.name.toLowerCase().includes(search.toLowerCase()) ||
                (agent.description || '').toLowerCase().includes(search.toLowerCase()),
            )
            .sort((a, b) => {
              // Sort by creation date descending (newest first)
              const dateA = new Date(a.created_at || 0).getTime();
              const dateB = new Date(b.created_at || 0).getTime();
              return dateB - dateA;
            })
            .map((agent) => (
              <div
                key={agent.id}
                className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-gray-200 transition-shadow cursor-pointer hover:shadow-lg"
                onClick={() => navigate(`/agents/${agent.id}`)}
              >
                <div className="flex gap-4 items-center">
                  <div className="flex justify-center items-center w-12 h-12 text-lg font-bold text-gray-500 bg-gray-200 rounded-full">
                    {agent.name[0]}
                  </div>
                  <div className="flex flex-col flex-1">
                    <div className="flex gap-2 items-center">
                      <span className="text-lg font-semibold text-gray-900">{agent.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium border border-gray-200 ml-2">
                        {agent.config?.domain || 'Other'}
                      </span>
                    </div>
                    <span className="mt-1 text-sm text-gray-500">{agent.description}</span>
                    {agent.created_at && (
                      <span className="mt-2 text-xs text-gray-400">
                        Created {formatDate(agent.created_at)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))
        ) : (
          <div className="col-span-3 py-12 text-lg text-center text-gray-400">
            No agents found. Click "+ New Agent" to create your first agent.
          </div>
        )}
      </div>
    </>
  );
};
