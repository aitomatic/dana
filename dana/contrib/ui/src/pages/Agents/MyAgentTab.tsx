import React from 'react';
import { IconSearch } from '@tabler/icons-react';

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
        day: 'numeric' 
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
}> = ({ agents, search, setSearch, navigate }) => (
  <>
    <div className="flex items-center justify-between mb-8">
      <div className='text-lg font-semibold'>My Trained Agents</div>
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
      </div>

    </div>
    {/* User's agents list */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {agents && agents.length > 0 ? (
        agents
          .filter((agent) =>
            agent.name.toLowerCase().includes(search.toLowerCase()) ||
            (agent.description || '').toLowerCase().includes(search.toLowerCase())
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
            className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-4 hover:shadow-lg transition-shadow cursor-pointer"
            onClick={() => navigate(`/agents/${agent.id}`)}
          >
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-full bg-gray-200 flex items-center justify-center text-gray-500 text-lg font-bold">
                {agent.name[0]}
              </div>
              <div className="flex flex-col flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-lg font-semibold text-gray-900">{agent.name}</span>
                  <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium border border-gray-200 ml-2">
                    {agent.config?.domain || 'Other'}
                  </span>
                </div>
                <span className="text-gray-500 text-sm mt-1">{agent.description}</span>
                {agent.created_at && (
                  <span className="text-gray-400 text-xs mt-2">
                    Created {formatDate(agent.created_at)}
                  </span>
                )}
              </div>
            </div>
          </div>
        ))
      ) : (
        <div className="text-gray-400 text-lg col-span-3 text-center py-12">No agents found. Click "+ New Agent" to create your first agent.</div>
      )}
    </div>
  </>
); 