import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { IconArrowLeft } from '@tabler/icons-react';
import { useAgentStore } from '@/stores/agent-store';
import { ArrowLeft } from 'iconoir-react';
import { AgentPerformanceComparisonModal } from './AgentPerformanceComparisonModal';
import { AgentDetailHeader } from './AgentDetailHeader';
import { AgentDetailSidebar } from './AgentDetailSidebar';
import { AgentDetailTabs } from './AgentDetailTabs';

// Mock template data
const TEMPLATES = [
  {
    id: 'georgia',
    name: 'Georgia',
    domain: 'Finance',
    title: 'Investment Analysis Specialist',
    description: 'Expert in financial modeling, risk assessment, and market analysis with real-time data integration',
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
    description: 'Comprehensive budgeting, savings optimization, and investment guidance for individual clients',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-purple-400 to-blue-400',
  },
  {
    id: 'edison',
    name: 'Edison',
    domain: 'Semiconductor',
    title: 'Chip Design Consultant',
    description: 'Advanced semiconductor design validation, process optimization, and failure analysis expertise',
    accuracy: 96,
    rating: 4.8,
    avatarColor: 'from-green-400 to-green-600',
  },
  {
    id: 'nova',
    name: 'Nova',
    domain: 'Semiconductor',
    title: 'Supply Chain Optimizer',
    description: 'Electronics component sourcing, inventory management, and production scheduling specialist',
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
  const [view, setView] = useState<'select' | 'train'>('select');
  const [selectedTemplate, setSelectedTemplate] = useState<any>(null);
  const [showComparison, setShowComparison] = useState(false);
  const tpl = selectedTemplate || TEMPLATES[0];

  useEffect(() => {
    if (agent_id) {
      fetchAgent(parseInt(agent_id))
        .then(setAgent)
        .catch(console.error);
    }
  }, [agent_id, fetchAgent]);

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-full w-full">
        <span className="text-gray-400 text-lg">Loading agent...</span>
      </div>
    );
  }

  if (error || (!isLoading && !agent)) {
    return (
      <div className="flex justify-center items-center h-full w-full">
        <div className="flex flex-col items-center max-w-md text-center">
          <h1 className="py-4 text-2xl font-semibold text-gray-900">Agent Not Found</h1>
          <p className="mb-8 leading-relaxed text-gray-600">
            {error || "The agent you're looking for doesn't exist or has been removed."}
          </p>
          <button onClick={() => navigate('/agents')} className="text-blue-600 underline">Back to Agents</button>
        </div>
      </div>
    );
  }

  // --- Step 2: Training view ---
  return (
    <div className="h-screen w-full flex flex-col bg-gray-50">
      <AgentDetailHeader
        onBack={() => navigate('/agents')}
        title="Train Your Agent"
        onDeploy={() => { }}
        onCancel={() => navigate('/agents')}
      />
      <div className="flex flex-1 h-full w-full">
        <AgentDetailSidebar />
        <AgentDetailTabs tpl={tpl} onShowComparison={() => setShowComparison(true)} />
      </div>
      <AgentPerformanceComparisonModal open={showComparison} onClose={() => setShowComparison(false)} />
    </div>
  );
} 