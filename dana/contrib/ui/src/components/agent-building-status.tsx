import { useAgentBuildingStore } from '@/stores/agent-building-store';
import { cn } from '@/lib/utils';

export function AgentBuildingStatus() {
  const { currentAgent, isGenerating, isAnalyzing, error } = useAgentBuildingStore();

  if (!currentAgent) {
    return (
      <div className="p-4 bg-gray-50 rounded-lg">
        <p className="text-sm text-gray-600">No agent being built</p>
      </div>
    );
  }

  return (
    <div className="p-4 bg-white border border-gray-200 rounded-lg">


      <div className="space-y-2">
        <div>
          <span className="text-sm font-medium text-gray-700">Name:</span>
          <span className="ml-2 text-sm text-gray-900">{currentAgent.name}</span>
        </div>

        <div>
          <span className="text-sm font-medium text-gray-700">Description:</span>
          <span className="ml-2 text-sm text-gray-900">{currentAgent.description}</span>
        </div>

        {currentAgent.id && (
          <div>
            <span className="text-sm font-medium text-gray-700">Agent ID:</span>
            <span className="ml-2 text-sm text-gray-900">{currentAgent.id}</span>
          </div>
        )}

        {currentAgent.agent_folder && (
          <div>
            <span className="text-sm font-medium text-gray-700">Folder:</span>
            <span className="ml-2 text-sm text-gray-900">{currentAgent.agent_folder}</span>
          </div>
        )}

        <div>
          <span className="text-sm font-medium text-gray-700">Ready for Code Generation:</span>
          <span className={cn(
            'ml-2 text-sm',
            currentAgent.ready_for_code_generation ? 'text-green-600' : 'text-yellow-600'
          )}>
            {currentAgent.ready_for_code_generation ? 'Yes' : 'No'}
          </span>
        </div>

        <div>
          <span className="text-sm font-medium text-gray-700">Conversation Messages:</span>
          <span className="ml-2 text-sm text-gray-900">{currentAgent.conversation_context.length}</span>
        </div>

        {(isGenerating || isAnalyzing) && (
          <div className="mt-3 p-2 bg-blue-50 rounded">
            <p className="text-sm text-blue-700">
              {isGenerating ? 'Generating agent code...' : 'Analyzing agent description...'}
            </p>
          </div>
        )}

        {error && (
          <div className="mt-3 p-2 bg-red-50 rounded">
            <p className="text-sm text-red-700">Error: {error}</p>
          </div>
        )}

        {currentAgent.created_at && (
          <div className="mt-3 pt-2 border-t border-gray-200">
            <p className="text-xs text-gray-500">
              Created: {new Date(currentAgent.created_at).toLocaleString()}
            </p>
            {currentAgent.updated_at && (
              <p className="text-xs text-gray-500">
                Updated: {new Date(currentAgent.updated_at).toLocaleString()}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default AgentBuildingStatus; 