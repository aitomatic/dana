import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { IconArrowLeft, IconMessage } from '@tabler/icons-react';
import { useAgentStore } from '@/stores/agent-store';

export default function AgentDetailPage() {
  const { agent_id } = useParams();
  const navigate = useNavigate();
  const { agents, fetchAgents, isLoading } = useAgentStore();
  const [agent, setAgent] = useState<any>(null);

  useEffect(() => {
    fetchAgents();
  }, [fetchAgents]);

  useEffect(() => {
    if (agent_id && agents.length > 0) {
      const foundAgent = agents.find(a => a.id.toString() === agent_id);
      setAgent(foundAgent || null);
    }
  }, [agent_id, agents]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full w-full">
        <span className="text-gray-400 text-lg">Loading agent...</span>
      </div>
    );
  }

  if (!agent) {
    return (
      <div className="flex justify-center items-center h-full w-full">
        <div className="flex flex-col items-center max-w-md text-center">
          <h1 className="py-4 text-2xl font-semibold text-gray-900">Agent Not Found</h1>
          <p className="mb-8 leading-relaxed text-gray-600">
            The agent you're looking for doesn't exist or has been removed.
          </p>
          <Button onClick={() => navigate('/agents')} variant="default">
            <IconArrowLeft className="w-4 h-4 mr-2" />
            Back to Agents
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full w-full p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-8">
        <Button
          variant="outline"
          onClick={() => navigate('/agents')}
          className="flex items-center gap-2"
        >
          <IconArrowLeft className="w-4 h-4" />
          Back to Agents
        </Button>
        <h1 className="text-2xl font-bold text-gray-900">{agent.name}</h1>
      </div>

      {/* Agent Details */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Agent Info */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex items-start gap-4 mb-6">
              <img
                src={`/agent-avatar${agent.config?.avatar}`}
                alt="Agent avatar"
                className="rounded-full w-16 h-16 object-cover border border-gray-200"
              />
              <div className="flex-1">
                <h2 className="text-xl font-bold text-gray-900 mb-2">{agent.name}</h2>
                <p className="text-gray-600">{agent.description || 'No description available'}</p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-semibold text-gray-700 mb-2">Configuration</h3>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(agent.config, null, 2)}
                </pre>
              </div>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="space-y-4">
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Actions</h3>
            <div className="space-y-3">
              <Button
                onClick={() => navigate(`/${agent_id}/chat`)}
                className="w-full justify-start"
                size="lg"
              >
                <IconMessage className="w-4 h-4 mr-2" />
                Start Chat
              </Button>
              <Button
                variant="outline"
                onClick={() => navigate(`/agents/${agent_id}/edit`)}
                className="w-full justify-start"
              >
                Edit Agent
              </Button>
            </div>
          </div>

          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Agent Info</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-600">ID:</span>
                <span className="font-mono">{agent.id}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Created:</span>
                <span>{new Date(agent.created_at).toLocaleDateString()}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-600">Updated:</span>
                <span>{new Date(agent.updated_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 