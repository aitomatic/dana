import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import DomainKnowledgeTab from './DomainKnowledgeTab';
import DocumentsTab from './DocumentsTab';
import ToolsTab from './ToolsTab';
import { Brain, FilesIcon } from 'lucide-react';
import { Tools } from 'iconoir-react';
import { useUIStore } from '@/stores/ui-store';

const KNOWLEDGE_SUBTABS = ['Domain Knowledge', 'Documents', 'Tools'] as const;
type KnowledgeSubTab = (typeof KNOWLEDGE_SUBTABS)[number];

const SUBTAB_ICONS = {
  'Domain Knowledge': <Brain className="w-4 h-4" />,
  Documents: <FilesIcon className="w-4 h-4" />,
  Tools: <Tools className="w-4 h-4" />,
};

const KnowledgeBaseTab: React.FC = () => {
  const { agent_id } = useParams<{ agent_id: string }>();
  const { knowledgeBaseActiveSubTab, setKnowledgeBaseActiveSubTab } = useUIStore();

  // Use global state if available, otherwise fall back to local state
  const [localActiveSubTab, setLocalActiveSubTab] = useState<KnowledgeSubTab>('Domain Knowledge');
  const activeSubTab = (knowledgeBaseActiveSubTab as KnowledgeSubTab) || localActiveSubTab;

  const handleSubTabChange = (subTab: KnowledgeSubTab) => {
    setKnowledgeBaseActiveSubTab(subTab);
    setLocalActiveSubTab(subTab);
  };

  const renderSubTabContent = () => {
    switch (activeSubTab) {
      case 'Domain Knowledge':
        return <DomainKnowledgeTab />;
      case 'Documents':
        return <DocumentsTab />;
      case 'Tools':
        return <ToolsTab />;
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
            onClick={() => handleSubTabChange(subTab)}
          >
            {SUBTAB_ICONS[subTab]}
            {subTab}
          </button>
        ))}
      </div>

      {/* Sub-tab content */}
      <div className="overflow-auto flex-1 custom-scrollbar">{renderSubTabContent()}</div>
    </div>
  );
};

export default KnowledgeBaseTab;
