import React from 'react';
import { Button } from '@/components/ui/button';
import { apiService } from '@/lib/api';
import { getAgentAvatarSync } from '@/utils/avatar';
import { Plus, Settings, Play } from 'iconoir-react';

export const ExploreTab: React.FC<{
  filteredAgents: any[];
  selectedDomain: string;
  setSelectedDomain: (d: string) => void;
  navigate: (url: string) => void;
  DOMAINS: string[];
  handleCreateAgent: () => Promise<void>;
  creating: boolean;
}> = ({
  filteredAgents,
  selectedDomain,
  setSelectedDomain,
  navigate,
  DOMAINS,
  handleCreateAgent,
  creating,
}) => (
  <>
    {/* Domain tabs */}
    <div className="flex justify-between items-center mb-4 text-gray-600">
      <p>Pre-trained agents with built-in domain expertise by Aitomatic</p>
    </div>
    <div className="flex flex-wrap gap-2 mb-6">
      {DOMAINS.map((domain) => (
        <Button
          key={domain}
          variant={selectedDomain === domain ? 'secondary' : 'outline'}
          className={`rounded-full px-5 py-1 text-base font-medium ${selectedDomain === domain ? 'border-transparent border' : 'bg-white'}`}
          onClick={() => setSelectedDomain(domain)}
        >
          {domain}
        </Button>
      ))}
    </div>
    {/* Agent cards grid */}
    <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-3">
      {filteredAgents.map((agent) => (
        <div
          key={agent.id}
          className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-gray-200 transition-shadow hover:shadow-md"
        >
          <div className="flex flex-col gap-4">
            <div className="flex gap-2 justify-between items-center">
              <div className="flex overflow-hidden justify-center items-center w-12 h-12 rounded-full">
                <img
                  src={getAgentAvatarSync(agent.id)}
                  alt={`${agent.name} avatar`}
                  className="object-cover w-full h-full"
                  onError={(e) => {
                    // Fallback to colored circle if image fails to load
                    const target = e.target as HTMLImageElement;
                    target.style.display = 'none';
                    const parent = target.parentElement;
                    if (parent) {
                      parent.className = `flex justify-center items-center w-12 h-12 text-lg font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400 rounded-full`;
                      parent.innerHTML = `<span className="text-white">${agent.name[0]}</span>`;
                    }
                  }}
                />
              </div>
              {agent.config?.domain && (
                <span className="px-3 py-1 ml-2 text-sm font-medium text-gray-600 rounded-full border border-gray-200">
                  {agent.config.domain}
                </span>
              )}
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
                className="mt-1 text-sm font-medium text-gray-600 line-clamp-2 max-h-[20px]"
                style={{
                  display: '-webkit-box',
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: 'vertical',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                }}
              >
                {agent.description}
              </span>
            </div>
          </div>
          <div className="text-gray-500 text-sm min-h-[40px]">{agent.details || ''}</div>
          {/* <div className="flex justify-between items-center pt-3 border-t border-gray-200">
            <span className="text-xs text-gray-500">
              {agent.accuracy ? `${agent.accuracy}% accuracy` : ''}
            </span>
            <span className="flex gap-1 items-center text-sm font-semibold text-yellow-500">
              {agent.rating && (
                <>
                  <svg width="18" height="18" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.286 3.967a1 1 0 00.95.69h4.175c.969 0 1.371 1.24.588 1.81l-3.38 2.455a1 1 0 00-.364 1.118l1.287 3.966c.3.922-.755 1.688-1.54 1.118l-3.38-2.454a1 1 0 00-1.175 0l-3.38 2.454c-.784.57-1.838-.196-1.54-1.118l1.287-3.966a1 1 0 00-.364-1.118L2.04 9.394c-.783-.57-.38-1.81.588-1.81h4.175a1 1 0 00.95-.69l1.286-3.967z" />
                  </svg>
                  {new Intl.NumberFormat('en-US', {
                    minimumFractionDigits: 1,
                    maximumFractionDigits: 1,
                  }).format(agent.rating)}
                </>
              )}
            </span>
          </div> */}
          <div className="flex gap-2 justify-between items-center">
            <Button
              onClick={async () => {
                if (agent.is_prebuilt) {
                  try {
                    const newAgent = await apiService.cloneAgentFromPrebuilt(agent.key);
                    if (newAgent && newAgent.id) {
                      navigate(`/agents/${newAgent.id}`);
                    }
                  } catch (err) {
                    // Optionally show error toast
                    console.error(err);
                  }
                } else {
                  navigate(`/agents/${agent.id}/chat`);
                }
              }}
              variant="outline"
              className="w-1/2 text-sm font-semibold text-gray-700"
            >
              <Settings style={{ width: '20', height: '20' }} />
              Train from this
            </Button>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                navigate(`/agents/${agent.id}/chat`);
              }}
              variant="outline"
              className="w-1/2 text-sm font-semibold text-gray-700"
            >
              <Play style={{ width: '20', height: '20' }} />
              Try agent
            </Button>
          </div>
        </div>
      ))}
    </div>
    <div className="flex flex-col gap-2 justify-center p-8 mt-8 bg-gray-50 rounded-lg">
      <div className="text-lg font-semibold text-gray-900">
        Can't find a pre-trained agent for your domain?
      </div>
      <div className="text-sm text-gray-700">
        Train your own agent with support from <b>Dana</b>, our training expert.
      </div>
      <Button
        variant="default"
        className="w-[200px] px-4 py-1 mt-2 font-semibold"
        onClick={handleCreateAgent}
        disabled={creating}
      >
        <Plus style={{ width: '20', height: '20' }} />
        Train Your Own Agent
      </Button>
    </div>
  </>
);
