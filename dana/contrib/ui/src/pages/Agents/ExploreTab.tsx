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
    <div className="flex gap-2 flex-wrap mb-6">
      {DOMAINS.map((domain) => (
        <Button
          key={domain}
          variant={selectedDomain === domain ? 'default' : 'outline'}
          className={`rounded-full px-5 py-1 text-base font-medium ${selectedDomain === domain ? '' : 'bg-white'}`}
          onClick={() => setSelectedDomain(domain)}
        >
          {domain}
        </Button>
      ))}
    </div>
    {/* Agent cards grid */}
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
      {filteredAgents.map((agent) => (
        <div
          key={agent.id}
          className="bg-white rounded-2xl border border-gray-200 p-6 flex flex-col gap-4 hover:shadow-md transition-shadow cursor-pointer"
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
          <div className="flex items-center gap-4">
            <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${agent.avatarColor || 'bg-gray-200'} flex items-center justify-center text-white text-lg font-bold`}>
              {!agent.avatarColor && <span className="text-gray-500">{agent.name[0]}</span>}
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
          <div className="text-gray-600 text-sm min-h-[40px]">{agent.details || ''}</div>
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
      ))}
    </div>
  </>
); 