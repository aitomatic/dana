import React from 'react';
import { Button } from '@/components/ui/button';
import { getAgentAvatarSync } from '@/utils/avatar';

// Function to generate random avatar colors based on agent ID
const getRandomAvatarColor = (agentId: string | number): string => {
  const colors = [
    'from-blue-400 to-blue-600',
    'from-green-400 to-green-600',
    'from-purple-400 to-purple-600',
    'from-pink-400 to-pink-600',
    'from-indigo-400 to-indigo-600',
    'from-red-400 to-red-600',
    'from-yellow-400 to-yellow-600',
    'from-teal-400 to-teal-600',
    'from-orange-400 to-orange-600',
    'from-cyan-400 to-cyan-600',
    'from-emerald-400 to-emerald-600',
    'from-violet-400 to-violet-600',
  ];

  // Use agent ID to consistently generate the same color for the same agent
  const hash = String(agentId)
    .split('')
    .reduce((a, b) => {
      a = (a << 5) - a + b.charCodeAt(0);
      return a & a;
    }, 0);

  return colors[Math.abs(hash) % colors.length];
};

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
  navigate: (url: string) => void;
}> = ({ agents, navigate }) => {
  return (
    <>
      
      <div className="flex justify-between items-center mb-6 text-gray-600">     <p>Custom agents trained by you</p></div>
     
      {/* User's agents list */}
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
        {agents && agents.length > 0 ? (
          agents
            .sort((a, b) => {
              // Sort by creation date descending (newest first)
              const dateA = new Date(a.created_at || 0).getTime();
              const dateB = new Date(b.created_at || 0).getTime();
              return dateB - dateA;
            })
            .map((agent) => (
              <div
                key={agent.id}
                className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-gray-200 transition-shadow cursor-pointer hover:shadow-md"
                onClick={() => navigate(`/agents/${agent.id}`)}
              >
                <div className="flex gap-4 flex-col">
                  <div className="flex gap-2 items-center justify-between">
                    <div className="w-12 h-12 rounded-full overflow-hidden flex items-center justify-center">
                      <img
                        src={getAgentAvatarSync(agent.id)}
                        alt={`${agent.name} avatar`}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          // Fallback to colored circle if image fails to load
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const parent = target.parentElement;
                          if (parent) {
                            parent.className = `w-12 h-12 rounded-full bg-gradient-to-br ${getRandomAvatarColor(agent.id)} flex items-center justify-center text-white text-lg font-bold`;
                            parent.innerHTML = `<span className="text-white">${agent.name[0]}</span>`;
                          }
                        }}
                      />
                    </div>
                    <span className="text-sm px-3 py-1 rounded-full text-gray-600 font-medium border border-gray-200 ml-2">
                      {agent.config?.domain || 'Other'}
                    </span>
                  </div>
                  <div className="flex flex-col flex-1">
                    <div className="flex gap-2 items-center">
                      <span
                        className="text-lg font-semibold text-gray-900 line-clamp-1"
                        style={{
                          display: '-webkit-box',
                          WebkitLineClamp: 1,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                        }}
                      >
                        {agent.name}
                      </span>
                    </div>
                    <span
                      className="mt-1 text-sm text-medium text-gray-600 line-clamp-2 max-h-[20px]"
                      style={{
                        display: '-webkit-box',
                        WebkitLineClamp: 2,
                        WebkitBoxOrient: 'vertical',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {agent.description || 'Domain expertise is not yet defined'}
                    </span>
                  </div>
                </div>
                <div className="text-gray-500 text-sm min-h-[40px]">
                  {agent.details ||
                    (agent.created_at ? `Created ${formatDate(agent.created_at)}` : '')}
                </div>
                <div className="flex gap-2 justify-between items-center">
                  <Button variant="outline" className="w-1/2 text-sm font-semibold text-gray-500">
                    Train
                  </Button>
                  <Button                     
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/agents/${agent.id}/chat`);
                    }}
                    variant="outline"
                    className="w-1/2 text-sm font-semibold text-gray-500"
                  >
                    Use
                  </Button>
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
