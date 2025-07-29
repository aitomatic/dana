import React from 'react';

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
    'from-violet-400 to-violet-600'
  ];
  
  // Use agent ID to consistently generate the same color for the same agent
  const hash = String(agentId).split('').reduce((a, b) => {
    a = ((a << 5) - a) + b.charCodeAt(0);
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

      <div className="flex justify-between items-center mb-8">
        <div className="text-lg font-semibold">My Trained Agents</div>
      </div>
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
                className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-4 hover:shadow-lg transition-shadow cursor-pointer"
                onClick={() => navigate(`/agents/${agent.id}`)}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${agent.avatarColor || getRandomAvatarColor(agent.id)} flex items-center justify-center text-white text-lg font-bold`}>
                    <span className={agent.avatarColor ? "text-white" : "text-white"}>{agent.name[0]}</span>
                  </div>
                  <div className="flex flex-col flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-semibold text-gray-900 line-clamp-1" style={{ display: '-webkit-box', WebkitLineClamp: 1, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis' }}>{agent.name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium border border-gray-200 ml-2">
                        {agent.config?.domain || 'Other'}
                      </span>
                    </div>
                    <span className="text-gray-500 text-sm mt-1 line-clamp-2" style={{ display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden', textOverflow: 'ellipsis' }}>{agent.description}</span>
                  </div>
                </div>
                <div className="text-gray-600 text-sm min-h-[40px]">{agent.details || (agent.created_at ? `Created ${formatDate(agent.created_at)}` : '')}</div>
                <div className="flex items-center justify-between mt-2">
                  <span className="text-gray-500 text-xs">{agent.accuracy ? `${agent.accuracy}% accuracy` : ''}</span>
                  <span className="flex items-center gap-1 text-yellow-500 font-semibold text-sm">
                    {agent.rating && (
                      <>
                        <svg width="18" height="18" fill="currentColor" viewBox="0 0 20 20"><path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.286 3.967a1 1 0 00.95.69h4.175c.969 0 1.371 1.24.588 1.81l-3.38 2.455a1 1 0 00-.364 1.118l1.287 3.966c.3.922-.755 1.688-1.54 1.118l-3.38-2.454a1 1 0 00-1.175 0l-3.38 2.454c-.784.57-1.838-.196-1.54-1.118l1.287-3.966a1 1 0 00-.364-1.118L2.04 9.394c-.783-.57-.38-1.81.588-1.81h4.175a1 1 0 00.95-.69l1.286-3.967z" /></svg>
                        {new Intl.NumberFormat('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(agent.rating)}
                      </>
                    )}
                  </span>
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
