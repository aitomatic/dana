import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { clearSmartChatStorageForAgent } from '@/stores/smart-chat-store';
import { AgentPerformanceComparisonModal } from './AgentPerformanceComparisonModal';
import { AgentDetailHeader } from './AgentDetailHeader';
import { AgentDetailSidebar } from './AgentDetailSidebar';
import { AgentDetailTabs } from './AgentDetailTabs';
import { Dialog, DialogContent, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { XIcon } from 'lucide-react';
import { toast } from 'sonner';

// Mock template data
export const TEMPLATES = [
  {
    id: 'georgia',
    name: 'Georgia',
    domain: 'Finance',
    title: 'Investment Analysis Specialist',
    description:
      'Expert in financial modeling, risk assessment, and market analysis with real-time data integration',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-pink-400 to-purple-400',
    profile: {
      role: 'Senior Financial Analyst & Advisor',
      personality: 'Professional, detail-oriented, proactive',
      communication: 'Clear, data-driven, consultative',
      specialties: 'Financial modeling, risk assessment, regulatory compliance',
    },
    performance: [
      ['Avg Response Time', '2.3s', '12s'],
      ['Accuracy', '98.7%', '73%'],
      ['Financial Compliance', 'SOX', '✗'],
      ['Company Context', 'Full', '✗'],
      ['Professional Format', 'Board', '✗'],
    ],
  },
  {
    id: 'sophia',
    name: 'Sophia',
    domain: 'Finance',
    title: 'Personal Finance Advisor',
    description:
      'Comprehensive budgeting, savings optimization, and investment guidance for individual clients',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-purple-400 to-blue-400',
  },
  {
    id: 'edison',
    name: 'Edison',
    domain: 'Semiconductor',
    title: 'Chip Design Consultant',
    description:
      'Advanced semiconductor design validation, process optimization, and failure analysis expertise',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-green-400 to-green-600',
  },
  {
    id: 'nova',
    name: 'Nova',
    domain: 'Semiconductor',
    title: 'Supply Chain Optimizer',
    description:
      'Electronics component sourcing, inventory management, and production scheduling specialist',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-yellow-400 to-yellow-600',
  },
  {
    id: 'darwin',
    name: 'Darwin',
    domain: 'Research',
    title: 'Research Assistant',
    description: 'Paper analysis, citation management, and research methodology guidance',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-purple-400 to-pink-400',
  },
];

export default function AgentDetailPage() {
  const { agent_id } = useParams();
  const navigate = useNavigate();
  const { fetchAgent, deleteAgent, updateAgent, isLoading, error, selectedAgent } = useAgentStore();
  const [showComparison, setShowComparison] = useState(false);
  const [showCancelConfirmation, setShowCancelConfirmation] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  // LIFTED TAB STATE
  const [activeTab, setActiveTab] = useState('Overview');

  const handleDeploy = async () => {
    if (!agent_id || isNaN(Number(agent_id)) || !selectedAgent) {
      // For prebuilt agents or invalid IDs, just navigate
      navigate('/agents');
      return;
    }

    try {
      // Update agent with status success in config
      await updateAgent(parseInt(agent_id), {
        name: selectedAgent.name,
        description: selectedAgent.description,
        config: {
          ...selectedAgent.config,
          status: 'success',
        },
      });
      navigate(`/agents/${agent_id}/chat`);
    } catch (error) {
      console.error('Failed to deploy agent:', error);
      // You might want to show an error message to the user here
    }
  };

  const handleSaveAndExit = async () => {
    if (!agent_id || isNaN(Number(agent_id)) || !selectedAgent) {
      // For prebuilt agents or invalid IDs, just navigate
      navigate('/agents');
      return;
    }

    try {
      // Update agent with status success in config
      const updatedAgent = {
        ...selectedAgent,
        config: {
          ...selectedAgent.config,
          status: 'success',
        },
      };

      await updateAgent(parseInt(agent_id), updatedAgent);
      navigate('/agents');
    } catch (error) {
      console.error('Failed to deploy agent:', error);
      // You might want to show an error message to the user here
    }
  };

  const handleClose = () => {
    // If agent has status 'success', navigate directly to agents page
    if (selectedAgent && selectedAgent.config && selectedAgent.config.status === 'success') {
      return navigate(-1);
    }

    // Otherwise, show the delete confirmation dialog
    setShowCancelConfirmation(true);
  };

  const handleDiscardAndExit = async () => {
    if (!agent_id) {
      // No agent_id, just close dialog and navigate
      setShowCancelConfirmation(false);
      navigate('/agents');
      return;
    }

    setIsDeleting(true);
    try {
      // Clear the smart-chat-storage for this agent before deleting
      try {
        await clearSmartChatStorageForAgent(agent_id);

        console.log(`[Storage Cleanup] Cleared smart-chat-storage for agent ${agent_id}`);
      } catch (storageError) {
        console.warn('Failed to clear chat storage:', storageError);
        // Continue with deletion even if storage cleanup fails
      }

      // Only try to delete if it's a numeric ID (regular agent)
      if (!isNaN(Number(agent_id))) {
        await deleteAgent(parseInt(agent_id));
      }

      setShowCancelConfirmation(false);

      // No toast message when user chooses "Do not save" - they're discarding unsaved changes
      // Only show success toast when user explicitly deletes a saved agent

      navigate('/agents');
    } catch (error) {
      console.error('Failed to delete agent:', error);
      // Show error toast notification
      toast.error('Failed to delete agent');
    } finally {
      setIsDeleting(false);
    }
  };

  useEffect(() => {
    if (agent_id) {
      // Only fetch agent details for numeric IDs (regular agents)
      // Prebuilt agents with string IDs will be handled differently
      if (!isNaN(Number(agent_id))) {
        fetchAgent(parseInt(agent_id)).catch(console.error);
      } else {
        // For prebuilt agents, we might need to fetch different data or show different UI
        console.log('Prebuilt agent detected:', agent_id);
        // For now, set a placeholder or redirect to appropriate handler
      }
    }
  }, [agent_id, fetchAgent]);

  // Cleanup effect to clear smart-chat-storage when component unmounts
  useEffect(() => {
    return () => {
      // If the component unmounts and we have an agent_id, clear the storage
      // This handles cases where user navigates away without explicitly saving/discarding
      if (agent_id) {
        try {
          clearSmartChatStorageForAgent(agent_id);
        } catch (error) {
          console.warn('Failed to clear storage on unmount:', error);
        }
      }
    };
  }, [agent_id]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center w-full h-full">
        {/* Skeleton loader for agent detail */}
        <div className="p-8 w-full max-w-2xl">
          <div className="space-y-6 animate-pulse">
            <div className="mb-4 w-1/3 h-8 bg-gray-200 rounded" />
            <div className="mb-2 w-1/2 h-6 bg-gray-200 rounded" />
            <div className="mb-2 w-2/3 h-4 bg-gray-200 rounded" />
            <div className="mb-2 w-1/2 h-4 bg-gray-200 rounded" />
            <div className="mb-2 w-1/4 h-4 bg-gray-200 rounded" />
            <div className="w-full h-64 bg-gray-200 rounded" />
          </div>
        </div>
      </div>
    );
  }

  if (error || (!isLoading && !selectedAgent)) {
    return (
      <div className="flex justify-center items-center w-full h-full">
        <div className="flex flex-col items-center max-w-md text-center">
          <h1 className="py-4 text-2xl font-semibold text-gray-900">Agent Not Found</h1>
          <p className="mb-8 leading-relaxed text-gray-600">
            {error || "The agent you're looking for doesn't exist or has been removed."}
          </p>
          <button onClick={() => navigate('/agents')} className="text-blue-600 underline">
            Back to Agents
          </button>
        </div>
      </div>
    );
  }

  // --- Step 2: Training view ---
  return (
    <div className="flex overflow-hidden flex-col w-full h-screen bg-gray-50">
      <AgentDetailHeader title="Train Your Agent" onDeploy={handleDeploy} onCancel={handleClose} />
      <div className="flex overflow-hidden flex-1 w-full h-full">
        <AgentDetailSidebar />
        {/* Pass activeTab and setActiveTab to AgentDetailTabs */}
        <div className="flex-1 min-w-0">
          <AgentDetailTabs activeTab={activeTab} setActiveTab={setActiveTab} navigate={navigate} />
        </div>
      </div>
      <AgentPerformanceComparisonModal
        open={showComparison}
        onClose={() => setShowComparison(false)}
      />

      {/* Cancel Confirmation Dialog */}
      <Dialog open={showCancelConfirmation} onOpenChange={setShowCancelConfirmation}>
        <DialogContent className="sm:max-w-md" showCloseButton={false}>
          <div className="grid grid-cols-[1fr_max-content] items-center">
            <div className="bg-[#FEF0C7] p-2 rounded-full max-w-max">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
              >
                <path
                  d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z"
                  stroke="#F79009"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M9 9C9 5.49997 14.5 5.5 14.5 9C14.5 11.5 12 10.9999 12 13.9999"
                  stroke="#F79009"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M12 18.01L12.01 17.9989"
                  stroke="#F79009"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </div>
            <XIcon
              className="text-gray-700 cursor-pointer"
              onClick={() => setShowCancelConfirmation(false)}
            />
          </div>
          <DialogDescription className="flex flex-col gap-2">
            <div className="text-lg font-semibold text-gray-900">
              Save to your agents before close?
            </div>
            <div className="mb-4 text-sm text-gray-600">
              You haven’t made any changes. If you close now, the agent will not be saved to your
              agents.
            </div>
          </DialogDescription>
          <DialogFooter className="grid grid-cols-2 gap-2 sm:gap-2">
            <Button variant="outline" onClick={handleDiscardAndExit} disabled={isDeleting}>
              {isDeleting ? 'Do not save' : 'Do not save'}
            </Button>
            <Button variant="default" onClick={handleSaveAndExit} disabled={isDeleting}>
              Save & Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
