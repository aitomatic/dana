import { useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { IconPlus, IconMessageCircle, IconEdit, IconTrash } from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { Skeleton } from '@/components/ui/skeleton';

// Import image as a module
import emptyAgentImage from '/images/empty-agent.svg';

export default function AgentsPage() {
  const navigate = useNavigate();
  const { agents, isLoading, error, fetchAgents } = useAgentStore();

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  const handleChatWithAgent = (agentId: number) => {
    navigate(`/${agentId}/chat`);
  };

  const handleEditAgent = (agent: any) => {
    // TODO: Implement edit agent dialog
    console.log('Edit agent:', agent);
  };

  const handleDeleteAgent = (agent: any) => {
    // TODO: Implement delete agent dialog
    console.log('Delete agent:', agent);
  };

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex justify-between items-center mb-8">
          <h1 className="text-3xl font-bold">Agents</h1>
          <Button onClick={() => navigate('/agents/create')} variant="default">
            <IconPlus className="w-4 h-4 mr-2" />
            New Agent
          </Button>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="border rounded-lg p-6 space-y-4">
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
              <div className="flex space-x-2">
                <Skeleton className="h-8 w-20" />
                <Skeleton className="h-8 w-8" />
                <Skeleton className="h-8 w-8" />
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex justify-center items-center p-8 h-full">
        <div className="flex flex-col items-center max-w-md text-center">
          <h1 className="py-4 text-2xl font-semibold text-gray-900">Error Loading Agents</h1>
          <p className="mb-8 leading-relaxed text-gray-600">{error}</p>
          <Button onClick={() => fetchAgents()} variant="default">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  if (agents.length === 0) {
    return (
      <div className="flex justify-center items-center p-8 h-full">
        <div className="flex flex-col items-center max-w-md text-center">
          {/* DXA Logo */}
          <img src={emptyAgentImage} alt="empty dxa" className="width-[192px] h-[192px]" />

          {/* Content */}
          <h1 className="py-4 text-2xl font-semibold text-gray-900">No Domain-Expert Agent</h1>
          <p className="mb-8 leading-relaxed text-gray-600">
            Create your first Domain-Expert Agent to explore the power of agent
          </p>

          {/* New Agent Button */}
          <Button onClick={() => navigate('/agents/create')} variant="default" size="lg">
            <IconPlus className="w-4 h-4" />
            New Agent
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Agents ({agents.length})</h1>
        <Button onClick={() => navigate('/agents/create')} variant="default">
          <IconPlus className="w-4 h-4 mr-2" />
          New Agent
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <div key={agent.id} className="border rounded-lg p-6 hover:shadow-md transition-shadow">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{agent.name}</h3>
                <p className="text-sm text-gray-600 mt-1">{agent.description}</p>
              </div>
              <div className="flex space-x-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleEditAgent(agent)}
                  className="h-8 w-8 p-0"
                >
                  <IconEdit className="w-4 h-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleDeleteAgent(agent)}
                  className="h-8 w-8 p-0 text-red-600 hover:text-red-700"
                >
                  <IconTrash className="w-4 h-4" />
                </Button>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <Button
                onClick={() => handleChatWithAgent(agent.id)}
                variant="default"
                size="sm"
                className="flex-1 mr-2"
              >
                <IconMessageCircle className="w-4 h-4 mr-2" />
                Chat
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
