import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAgentStore } from '@/stores/agent-store';
import { AgentPerformanceComparisonModal } from './AgentPerformanceComparisonModal';
import { AgentDetailHeader } from './AgentDetailHeader';
import { AgentDetailSidebar } from './AgentDetailSidebar';
import { AgentDetailTabs } from './AgentDetailTabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { IconQuestionMark } from '@tabler/icons-react';
import { XIcon } from 'lucide-react';

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
  const { fetchAgent, isLoading, error } = useAgentStore();
  const [agent, setAgent] = useState<any>(null);
  const [showComparison, setShowComparison] = useState(false);
  const [showCancelConfirmation, setShowCancelConfirmation] = useState(false);
  // LIFTED TAB STATE
  const [activeTab, setActiveTab] = useState('Overview');

  useEffect(() => {
    if (agent_id) {
      fetchAgent(parseInt(agent_id)).then(setAgent).catch(console.error);
    }
  }, [agent_id, fetchAgent]);

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

  if (error || (!isLoading && !agent)) {
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
    <div className="flex flex-col w-full h-screen bg-gray-50">
      <AgentDetailHeader
        onBack={() => navigate('/agents')}
        title="Train Your Agent"
        onDeploy={() => navigate('/agents')}
        onCancel={() => setShowCancelConfirmation(true)}
      />
      <div className="grid grid-cols-[max-content_1fr] flex-1 w-full h-full">
        <AgentDetailSidebar />
        {/* Pass activeTab and setActiveTab to AgentDetailTabs */}
        <AgentDetailTabs
          onShowComparison={() => setShowComparison(true)}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />
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
              Save your trained agent before exiting?
            </div>
            <div className="text-sm text-gray-600">
              You're about to leave the agent creation process. If you exit now, all your current
              configurations will be lost.
            </div>
          </DialogDescription>
          <DialogFooter className="grid grid-cols-2 gap-2 sm:gap-2">
            <Button variant="outline" onClick={() => setShowCancelConfirmation(false)}>
              Discard
            </Button>
            <Button
              variant="default"
              onClick={() => {
                setShowCancelConfirmation(false);
                navigate('/agents');
              }}
            >
              Save And Exit
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
