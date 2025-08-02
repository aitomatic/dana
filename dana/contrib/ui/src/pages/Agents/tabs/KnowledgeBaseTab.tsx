import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import DomainKnowledgeTab from './DomainKnowledgeTab';
import DocumentsTab from './DocumentsTab';
import WorkflowsTab from './WorkflowsTab';
import { Brain, FilesIcon, Network } from 'lucide-react';

const KNOWLEDGE_SUBTABS = ['Domain Knowledge', 'Documents', 'Workflows'] as const;
type KnowledgeSubTab = (typeof KNOWLEDGE_SUBTABS)[number];

const SUBTAB_ICONS = {
  'Domain Knowledge': <Brain className="w-4 h-4" />,
  Documents: <FilesIcon className="w-4 h-4" />,
  Workflows: <Network className="w-4 h-4" />,
};

const KnowledgeBaseTab: React.FC = () => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const [activeSubTab, setActiveSubTab] = useState<KnowledgeSubTab>('Domain Knowledge');

  const renderSubTabContent = () => {
    switch (activeSubTab) {
      case 'Domain Knowledge':
        return <DomainKnowledgeTab />;
      case 'Documents':
        return <DocumentsTab />;
      case 'Workflows':
        return <WorkflowsTab />;
      default:
        return <DomainKnowledgeTab />;
    }
  };

  if (!agent_id) {
    return (
      <div className="flex justify-center items-center h-full">
        <div className="text-gray-500">No agent selected</div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-white rounded-lg">
      {/* Sub-tab navigation */}
      <div className="flex gap-2 px-4 py-4">
        {KNOWLEDGE_SUBTABS.map((subTab) => (
          <button
            key={subTab}
            className={`cursor-pointer px-3 py-2 font-medium text-sm flex items-center gap-2 rounded-full transition-colors ${
              activeSubTab === subTab
                ? 'text-primary shadow-sm border bg-gray-100 border-gray-200'
                : 'text-gray-500 border border-gray-200 hover:text-gray-800 hover:bg-gray-100'
            }`}
            onClick={() => setActiveSubTab(subTab)}
          >
            {SUBTAB_ICONS[subTab]}
            {subTab}
          </button>
        ))}
      </div>

      {/* Sub-tab content */}
      <div className="overflow-auto flex-1">{renderSubTabContent()}</div>
    </div>
  );
};

export default KnowledgeBaseTab;
