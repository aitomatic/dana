import React from 'react';
import { Button } from '@/components/ui/button';
import { apiService } from '@/lib/api';

export const ExploreTab: React.FC<{
  filteredAgents: any[];
  selectedDomain: string;
  setSelectedDomain: (d: string) => void;
  navigate: (url: string) => void;
  DOMAINS: string[];
}> = ({ filteredAgents, selectedDomain, setSelectedDomain, navigate, DOMAINS }) => (
  <>
    {/* Domain tabs */}
    <div className="flex flex-wrap gap-2 mb-6">
      {DOMAINS.map((domain) => (
        <Button
          key={domain}
          variant={selectedDomain === domain ? 'secondary' : 'outline'}
          className={`rounded-full px-5 py-1 text-base font-medium ${selectedDomain === domain ? '' : 'bg-white'}`}
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
          className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-gray-200 transition-shadow cursor-pointer hover:shadow-md"
          onClick={async () => {
            console.log('agent', agent);
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
        >
          <div className="flex gap-4 items-center">
            <div
              className={`w-12 h-12 rounded-full bg-gradient-to-br ${agent.avatarColor || 'bg-gray-200'} flex items-center justify-center text-white text-lg font-bold`}
            >
              {!agent.avatarColor && <span className="text-gray-500">{agent.name[0]}</span>}
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
                <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 font-medium border border-gray-200 ml-2">
                  {agent.config?.domain || 'Other'}
                </span>
              </div>
              <span
                className="mt-1 text-sm text-gray-500 line-clamp-2"
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
          <div className="text-gray-600 text-sm min-h-[40px]">{agent.details || ''}</div>
          <div className="flex justify-between items-center pt-3 border-t border-gray-200">
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
      ))}
    </div>
  </>
);
