import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { getAgentAvatarSync } from '@/utils/avatar';
import { Settings, Play, MoreVert, Trash, Plus } from 'iconoir-react';
import { useAgentStore } from '@/stores/agent-store';
import { DeleteAgentDialog } from '@/components/delete-agent-dialog';
import { toast } from 'sonner';

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

export const MyAgentTab: React.FC<{
  agents: any[];
  navigate: (url: string) => void;
  handleCreateAgent: () => Promise<void>;
  creating: boolean;
}> = ({ agents, navigate, handleCreateAgent, creating }) => {
  const { deleteAgent, isDeleting } = useAgentStore();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [agentToDelete, setAgentToDelete] = useState<any>(null);

  const handleDeleteClick = (e: React.MouseEvent, agent: any) => {
    e.stopPropagation();
    setAgentToDelete(agent);
    setDeleteDialogOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (agentToDelete) {
      try {
        await deleteAgent(agentToDelete.id);
        setDeleteDialogOpen(false);
        setAgentToDelete(null);
      } catch (error) {
        console.error('Error deleting agent:', error);
      }
    }
  };

  const handleDeleteSuccess = () => {
    // Show success toast notification with custom styling
    toast.success(
      <div>
        <span style={{ fontWeight: 'bold' }}>{agentToDelete?.name}</span> has been deleted
        successfully
      </div>,
      {
        style: {
          background: '#f0fdf4',
          color: '#166534',
          border: '1px solid #bbf7d0',
          borderRadius: '8px',
          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
          fontSize: '14px',
          fontWeight: '500',
        },
      },
    );

    // Redirect to agents page with my tab selected after successful deletion
    navigate('/agents?tab=my');
  };

  const handleCancelDelete = () => {
    setDeleteDialogOpen(false);
    setAgentToDelete(null);
  };

  return (
    <>
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
                className="flex flex-col gap-4 p-6 bg-white rounded-2xl border border-gray-200 transition-shadow hover:shadow-md"
              >
                <div className="flex flex-col gap-4">
                  <div className="flex gap-2 justify-between">
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
                            parent.className = `flex justify-center items-center w-12 h-12 text-lg font-bold text-white bg-gradient-to-br ${getRandomAvatarColor(
                              agent.id,
                            )} rounded-full`;
                            parent.innerHTML = `<span className="text-white">${agent.name[0]}</span>`;
                          }
                        }}
                      />
                    </div>
                    <div className="flex gap-2">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="p-0 transform translate-x-4 -translate-y-2"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <MoreVert className="text-gray-700 size-4" strokeWidth={2} />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="start">
                          <DropdownMenuItem
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteClick(e, agent);
                            }}
                          >
                            <Trash className="text-gray-700 size-4" strokeWidth={2} />
                            <span className="text-sm font-medium text-gray-700">Delete Agent</span>
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </div>
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
                <div className="flex gap-2 justify-between items-center">
                  <Button
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/agents/${agent.id}`);
                    }}
                    variant="outline"
                    className="w-1/2 text-sm font-semibold text-gray-700"
                  >
                    <Settings style={{ width: '20', height: '20' }} />
                    Train
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
              </div>
            ))
        ) : (
          <div className="col-span-3">
            <div className="flex flex-col gap-2 items-center justify-center p-12 rounded-lg">
              <img 
                src="/images/empty-agent.svg" 
                alt="No agents" 
                className="w-24 h-24 mb-4"
              />
              <div className="text-lg text-center font-semibold text-gray-900">
                You haven't created any agents yet.
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
          </div>
        )}
      </div>

      {/* Delete Agent Dialog */}
      <DeleteAgentDialog
        isOpen={deleteDialogOpen}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmDelete}
        onSuccess={handleDeleteSuccess}
        isDeleting={isDeleting}
        agentName={agentToDelete?.name}
      />
    </>
  );
};
