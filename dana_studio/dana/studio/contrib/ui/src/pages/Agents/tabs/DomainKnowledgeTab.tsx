import React, { useState, useEffect } from 'react';
import DomainKnowledgeTree from './DomainKnowledgeTree';
import { useParams } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { KnowledgePackSelector } from './KnowledgePackSelector';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Trash, RefreshCw } from 'lucide-react';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

const DomainKnowledgeTab: React.FC = () => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const agent = useAgentStore((s) => s.selectedAgent);

  // Use agent_id from URL params or fall back to selected agent's id
  const agentId = agent_id || agent?.id;

  const [assignedKpId, setAssignedKpId] = useState<number | null>(null);
  const [assignedKpName, setAssignedKpName] = useState<string>('');
  const [showSelector, setShowSelector] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showRemoveDialog, setShowRemoveDialog] = useState(false);

  // Load assigned KP from agent config on mount
  useEffect(() => {
    if (agent?.config?.associated_kps && Array.isArray(agent.config.associated_kps) && agent.config.associated_kps.length > 0) {
      const kpId = agent.config.associated_kps[0]; // Use first associated KP
      setAssignedKpId(kpId);
      // Fetch the KP name
      apiService.getKnowledgePack(kpId)
        .then((kpResponse) => {
          const kpName = kpResponse?.kp_metadata?.domain 
            || kpResponse?.data?.kp_metadata?.domain
            || kpResponse?.domain
            || `Knowledge Pack ${kpId}`;
          setAssignedKpName(kpName);
        })
        .catch((error) => {
          console.error('Failed to fetch KP name:', error);
          setAssignedKpName(`Knowledge Pack ${kpId}`);
        });
    }
  }, [agent?.config?.associated_kps]);

  const handleAssignKp = async (kpId: number) => {
    if (!agentId || isNaN(Number(agentId))) return;

    setIsLoading(true);
    try {
      const response = await apiService.associateKnowledgePackToAgent(Number(agentId), kpId);
      if (response.success) {
        // Fetch the KP details to get the name
        const kpResponse = await apiService.getKnowledgePack(kpId);
        console.log('[DomainKnowledgeTab] KP Response:', kpResponse);
        
        // Try multiple possible paths for the domain name
        const kpName = kpResponse?.kp_metadata?.domain 
          || kpResponse?.data?.kp_metadata?.domain
          || kpResponse?.domain
          || `Knowledge Pack ${kpId}`;
        
        console.log('[DomainKnowledgeTab] Extracted KP name:', kpName);
        
        setAssignedKpId(kpId);
        setAssignedKpName(kpName);
        toast.success('Knowledge pack assigned successfully');
      } else {
        toast.error(response.message || 'Failed to assign knowledge pack');
      }
    } catch (error: any) {
      console.error('Failed to assign knowledge pack:', error);
      toast.error(error?.message || 'Failed to assign knowledge pack');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemoveKp = async () => {
    if (!agentId || isNaN(Number(agentId)) || !assignedKpId) return;

    setIsLoading(true);
    try {
      const response = await apiService.disassociateKnowledgePackFromAgent(
        Number(agentId),
        assignedKpId
      );
      if (response.success) {
        toast.success('Knowledge pack removed successfully');
        setAssignedKpId(null);
        setAssignedKpName('');
        setShowRemoveDialog(false);
      } else {
        toast.error(response.message || 'Failed to remove knowledge pack');
      }
    } catch (error: any) {
      console.error('Failed to remove knowledge pack:', error);
      toast.error(error?.message || 'Failed to remove knowledge pack');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Knowledge Pack Assignment Banner */}
      <div className="px-4 pb-3 bg-white border-b border-gray-200">
        {assignedKpId ? (
          <div className="flex items-center ">
            <div className="flex items-center gap-3 mr-4">
            
              <div>
                <div className="flex items-center gap-2 ">
                  <span className="text-sm font-medium text-gray-900">
                  Assigned Knowledge Pack 
                  </span>
                 
                </div>
                <p className="text-xs text-gray-500 mt-1">
                <Badge variant="secondary">{assignedKpName}</Badge>
                </p>
              </div>
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowSelector(true)}
                disabled={isLoading}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Replace
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setShowRemoveDialog(true)}
                disabled={isLoading}
              >
                <Trash className="w-4 h-4 mr-2" />
                Remove
              </Button>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <BookOpen className="w-5 h-5 text-gray-400" />
              <div>
                <p className="text-sm font-medium text-gray-900">
                  No Knowledge Pack Assigned
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Viewing agent's own domain knowledge
                </p>
              </div>
            </div>
            <Button
              variant="default"
              size="sm"
              onClick={() => setShowSelector(true)}
              disabled={isLoading}
            >
              <BookOpen className="w-4 h-4 mr-2" />
              Assign Knowledge Pack
            </Button>
          </div>
        )}
      </div>

      {/* Domain Knowledge Tree */}
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <DomainKnowledgeTree agentId={agentId} knowledgePackId={assignedKpId} />
      </div>

      {/* Knowledge Pack Selector Modal */}
      <KnowledgePackSelector
        isOpen={showSelector}
        onClose={() => setShowSelector(false)}
        agentId={agentId || ''}
        currentKpId={assignedKpId || undefined}
        onSelect={handleAssignKp}
      />

      {/* Remove Confirmation Dialog */}
      <Dialog open={showRemoveDialog} onOpenChange={setShowRemoveDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Remove Knowledge Pack?</DialogTitle>
            <DialogDescription>
              Are you sure you want to remove the assigned knowledge pack "{assignedKpName}"? 
              The agent will use its own domain knowledge instead.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => setShowRemoveDialog(false)}
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              variant="destructive" 
              onClick={handleRemoveKp}
              disabled={isLoading}
            >
              {isLoading ? 'Removing...' : 'Remove'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DomainKnowledgeTab;
