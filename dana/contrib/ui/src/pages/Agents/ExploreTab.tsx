import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { apiService } from '@/lib/api';
import { getAgentAvatarSync } from '@/utils/avatar';
import { Plus, Settings, Download } from 'iconoir-react';
import { useUIStore } from '@/stores/ui-store';

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
}) => {
  const [selectedAgent, setSelectedAgent] = useState<any>(null);
  const [isPopupOpen, setIsPopupOpen] = useState(false);
  const { setAgentDetailActiveTab } = useUIStore();

  const handleCardClick = (agent: any) => {
    setSelectedAgent(agent);
    setIsPopupOpen(true);
  };

  const handleCustomizeFromAgent = async () => {
    if (!selectedAgent) return;

    try {
      if (selectedAgent.is_prebuilt) {
        const newAgent = await apiService.cloneAgentFromPrebuilt(selectedAgent.key);
        if (newAgent && newAgent.id) {
          // Set Overview tab before navigating
          setAgentDetailActiveTab('Overview');
          navigate(`/agents/${newAgent.id}`);
        }
      } else {
        // Set Overview tab before navigating to chat
        setAgentDetailActiveTab('Overview');
        navigate(`/agents/${selectedAgent.id}/chat`);
      }
    } catch (err) {
      console.error(err);
    }
    setIsPopupOpen(false);
  };

  const handleSaveAndUseAgent = async () => {
    if (!selectedAgent) return;

    try {
      if (selectedAgent.is_prebuilt) {
        const newAgent = await apiService.cloneAgentFromPrebuilt(selectedAgent.key);
        if (newAgent && newAgent.id) {
          // Set Overview tab before navigating to chat
          setAgentDetailActiveTab('Overview');
          navigate(`/agents/${newAgent.id}/chat`);
        }
      } else {
        // Set Overview tab before navigating to chat
        setAgentDetailActiveTab('Overview');
        navigate(`/agents/${selectedAgent.id}/chat`);
      }
    } catch (err) {
      console.error(err);
    }
    setIsPopupOpen(false);
  };

  return (
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
            onClick={() => handleCardClick(agent)}
            className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-gray-200 transition-shadow hover:shadow-md cursor-pointer"
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
            <div className="text-gray-500 text-sm h-[40px] max-h-[40px] overflow-hidden">
              {agent.details || ''}
            </div>
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
            {/* {
              <div className="flex gap-2 justify-between items-center">
                <Button
                  onClick={async (e) => {
                    e.stopPropagation();
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
                  <Download style={{ width: '20', height: '20' }} />
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
                  Use agent
                </Button>
              </div>
            } */}
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

      {/* Agent Details Popup */}
      <Dialog open={isPopupOpen} onOpenChange={setIsPopupOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="flex flex-col gap-3 mb-4">
              <div className="flex overflow-hidden  justify-center items-center w-12 h-12 rounded-full">
                {selectedAgent && (
                  <img
                    src={getAgentAvatarSync(selectedAgent.id)}
                    alt={`${selectedAgent.name} avatar`}
                    className="object-cover w-full h-full"
                    onError={(e) => {
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const parent = target.parentElement;
                      if (parent) {
                        parent.className = `flex justify-center items-center w-12 h-12 text-lg font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400 rounded-full`;
                        parent.innerHTML = `<span className="text-white">${selectedAgent.name[0]}</span>`;
                      }
                    }}
                  />
                )}
              </div>
              <div>
                <DialogTitle className="text-lg font-semibold text-gray-900">
                  {selectedAgent?.name}
                </DialogTitle>
              </div>
            </div>

            <div className="space-y-4 mb-4">
              <div>
                <h4 className="text-sm font-medium text-gray-800 mb-1">Description</h4>
                <p className="text-sm text-gray-600">
                  {selectedAgent?.description || 'No description available'}
                </p>
              </div>

              {/* Domain */}
              {selectedAgent?.config?.domain && (
                <div>
                  <h4 className="text-sm font-medium text-gray-800 mb-1">Domain</h4>
                  <p className="text-sm text-gray-600">{selectedAgent.config.domain}</p>
                </div>
              )}

              {/* Topics (combines old specialties and new topics) */}
              {(() => {
                const oldSpecialties = selectedAgent?.config?.specialties || [];
                const newTopics = selectedAgent?.config?.topics || [];
                const allTopics = [...oldSpecialties, ...newTopics];
                const uniqueTopics = Array.from(new Set(allTopics));

                return (
                  uniqueTopics.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-800 mb-1">Topics</h4>
                      <div className="flex flex-wrap gap-1">
                        {uniqueTopics.map((topic: string, index: number) => (
                          <span
                            key={index}
                            className="capitalize px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full"
                          >
                            {topic}
                          </span>
                        ))}
                      </div>
                    </div>
                  )
                );
              })()}

              {/* Tasks (combines old skills and new tasks) */}
              {(() => {
                const oldSkills = selectedAgent?.config?.skills || [];
                const newTasks = selectedAgent?.config?.tasks || [];
                const allTasks = [...oldSkills, ...newTasks];
                const uniqueTasks = Array.from(new Set(allTasks));

                return (
                  uniqueTasks.length > 0 && (
                    <div>
                      <h4 className="text-sm font-medium text-gray-800 mb-1">Tasks</h4>
                      <div className="flex flex-wrap gap-1">
                        {uniqueTasks.map((task: string, index: number) => (
                          <span
                            key={index}
                            className="capitalize px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full"
                          >
                            {task}
                          </span>
                        ))}
                      </div>
                    </div>
                  )
                );
              })()}

              {/* Expertise Level & Personality */}
              {(selectedAgent?.config?.expertise_level || selectedAgent?.config?.personality) && (
                <div className="flex gap-4"></div>
              )}
            </div>
          </DialogHeader>

          <DialogFooter className="flex-col gap-2 sm:flex-row">
            <Button
              onClick={handleCustomizeFromAgent}
              variant="outline"
              className="w-full sm:w-1/2 text-sm font-semibold text-gray-700"
            >
              <Settings style={{ width: '16', height: '16' }} />
              Customize from this agent
            </Button>
            <Button
              onClick={handleSaveAndUseAgent}
              variant="default"
              className="w-full sm:w-1/2 text-sm font-semibold"
            >
              <Download style={{ width: '16', height: '16' }} />
              Save to My Agent and Use
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};
