import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Checkbox } from '@/components/ui/checkbox';
import { Badge } from '@/components/ui/badge';
import { Search, GridPlus, Xmark } from 'iconoir-react';
import { toast } from 'sonner';
import { apiService } from '@/lib/api';
import type { AgentRead } from '@/types/agent';
import type { AssignmentResult } from '@/types/domainKnowledge';

interface AssignAgentsDialogProps {
  isOpen: boolean;
  onClose: () => void;
  knowledgePackId: number;
  knowledgePackName: string;
  onSuccess: (results: AssignmentResult[]) => void;
}

export function AssignAgentsDialog({
  isOpen,
  onClose,
  knowledgePackId,
  knowledgePackName,
  onSuccess,
}: AssignAgentsDialogProps) {
  const [agents, setAgents] = useState<AgentRead[]>([]);
  const [filteredAgents, setFilteredAgents] = useState<AgentRead[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAgentIds, setSelectedAgentIds] = useState<Set<number>>(new Set());
  const [isLoadingAgents, setIsLoadingAgents] = useState(false);
  const [isAssigning, setIsAssigning] = useState(false);

  // Fetch agents when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchAgents();
    }
  }, [isOpen]);

  // Filter agents based on search term
  useEffect(() => {
    if (!searchTerm.trim()) {
      setFilteredAgents(agents);
    } else {
      const filtered = agents.filter((agent) =>
        agent.name.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredAgents(filtered);
    }
  }, [agents, searchTerm]);

  const fetchAgents = async () => {
    setIsLoadingAgents(true);
    try {
      const agentsData = await apiService.getAgents();
      setAgents(agentsData);
      setFilteredAgents(agentsData);
    } catch (error) {
      console.error('Failed to fetch agents:', error);
      toast.error('Failed to load agents');
    } finally {
      setIsLoadingAgents(false);
    }
  };

  const handleAgentToggle = (agentId: number) => {
    setSelectedAgentIds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(agentId)) {
        newSet.delete(agentId);
      } else {
        newSet.add(agentId);
      }
      return newSet;
    });
  };

  const handleRemoveAgent = (agentId: number) => {
    setSelectedAgentIds((prev) => {
      const newSet = new Set(prev);
      newSet.delete(agentId);
      return newSet;
    });
  };

  const handleDeselectAll = () => {
    setSelectedAgentIds(new Set());
  };

  const handleAssign = async () => {
    if (selectedAgentIds.size === 0) {
      toast.error('Please select at least one agent');
      return;
    }

    setIsAssigning(true);
    const results: AssignmentResult[] = [];

    try {
      // Process each selected agent
      for (const agentId of selectedAgentIds) {
        const agent = agents.find((a) => a.id === agentId);
        const agentName = agent?.name || `Agent ${agentId}`;

        try {
          const response = await apiService.associateKnowledgePackToAgent(agentId, knowledgePackId);
          
          if (response.success) {
            results.push({
              agentId,
              agentName,
              success: true,
            });
          } else {
            results.push({
              agentId,
              agentName,
              success: false,
              error: response.message || 'Unknown error',
            });
          }
        } catch (error: any) {
          results.push({
            agentId,
            agentName,
            success: false,
            error: error?.message || 'Failed to assign knowledge pack',
          });
        }
      }

      // Show success message
      const successCount = results.filter((r) => r.success).length;
      const failCount = results.filter((r) => !r.success).length;

      if (successCount > 0) {
        toast.success(`Successfully assigned to ${successCount} agent${successCount > 1 ? 's' : ''}`);
      }
      if (failCount > 0) {
        toast.error(`Failed to assign to ${failCount} agent${failCount > 1 ? 's' : ''}`);
      }

      // Call success callback with results
      onSuccess(results);
      
      // Close dialog
      onClose();
    } catch (error) {
      console.error('Error during assignment:', error);
      toast.error('An unexpected error occurred');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleClose = () => {
    if (!isAssigning) {
      setSearchTerm('');
      setSelectedAgentIds(new Set());
      onClose();
    }
  };

  const selectedAgents = agents.filter((agent) => selectedAgentIds.has(agent.id));

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] max-h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <GridPlus className="w-5 h-5" />
            Assign Knowledge Pack to Agents
          </DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4 py-4 flex-1 overflow-hidden">
          {/* Knowledge Pack Info */}
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <span className="font-medium">Knowledge Pack:</span> {knowledgePackName}
            </p>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 w-4 h-4 text-gray-400 transform -translate-y-1/2" />
            <Input
              placeholder="Search agents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10"
            />
          </div>

          {/* Selected Agents */}
          {selectedAgents.length > 0 && (
            <div className="flex flex-wrap gap-2 items-center">
              <span className="text-sm text-gray-600 font-medium">Selected:</span>
              {selectedAgents.map((agent) => (
                <Badge key={agent.id} variant="secondary" className="flex items-center gap-1">
                  {agent.name}
                  <button
                    onClick={() => handleRemoveAgent(agent.id)}
                    className="ml-1 hover:bg-gray-300 rounded-full p-0.5"
                  >
                    <Xmark className="w-3 h-3" />
                  </button>
                </Badge>
              ))}
              <Badge 
                variant="outline" 
                className="flex items-center gap-1 cursor-pointer hover:bg-gray-100 transition-colors"
                onClick={handleDeselectAll}
              >
                Deselect all
       
              </Badge>
            </div>
          )}

          {/* Agents List */}
          <div className="flex-1 overflow-y-auto border rounded-lg">
            {isLoadingAgents ? (
              <div className="flex justify-center items-center p-8">
                <div className="text-center">
                  
                  <p className="text-sm text-gray-600">Loading agents...</p>
                </div>
              </div>
            ) : filteredAgents.length === 0 ? (
              <div className="flex justify-center items-center p-8">
                <p className="text-sm text-gray-600">
                  {searchTerm ? 'No agents found matching your search' : 'No agents available'}
                </p>
              </div>
            ) : (
              <div className="divide-y">
                {filteredAgents.map((agent) => (
                  <div
                    key={agent.id}
                    className="flex gap-3 p-3 hover:bg-gray-50 cursor-pointer"
                    onClick={() => handleAgentToggle(agent.id)}
                  >
                    <Checkbox
                      checked={selectedAgentIds.has(agent.id)}
                      onChange={() => handleAgentToggle(agent.id)}
                      onClick={(e) => e.stopPropagation()}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <p className="font-medium text-sm">{agent.name}</p>
                      {agent.description && (
                        <p className="text-xs text-gray-500 mt-1">{agent.description}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isAssigning}>
            Cancel
          </Button>
          <Button
            onClick={handleAssign}
            disabled={selectedAgentIds.size === 0 || isAssigning}
            className="gap-2"
          >
            {isAssigning}
            {isAssigning ? 'Assigning...' : `Assign to ${selectedAgentIds.size} Agent${selectedAgentIds.size !== 1 ? 's' : ''}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
