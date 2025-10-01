import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import DomainKnowledgeTab from './DomainKnowledgeTab';
import DocumentsTab from './DocumentsTab';
import ToolsTab from './ToolsTab';
import { Brain, FilesIcon } from 'lucide-react';
import { Tools, Clock, CheckCircle, SystemRestart, Xmark, QuestionMark, Eye, EyeClosed } from 'iconoir-react';
import { useUIStore } from '@/stores/ui-store';
import { useKnowledgeStore } from '@/stores/knowledge-store';

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
  const { knowledgeStatus: statusData } = useKnowledgeStore();

  // Use global state if available, otherwise fall back to local state
  const [localActiveSubTab, setLocalActiveSubTab] = useState<KnowledgeSubTab>('Domain Knowledge');
  const activeSubTab = (knowledgeBaseActiveSubTab as KnowledgeSubTab) || localActiveSubTab;
  
  // State for legend visibility
  const [showLegend, setShowLegend] = useState(true);

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
      <div className="overflow-auto flex-1 custom-scrollbar relative">{renderSubTabContent()}</div>

      {/* Show Legend Button - Only show when legend is hidden */}
      {activeSubTab === 'Domain Knowledge' && !showLegend && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
          <button
            onClick={() => setShowLegend(true)}
            className="flex items-center gap-2 px-3 py-2 text-sm text-gray-600 bg-white rounded-lg shadow-lg border border-gray-200 hover:bg-gray-50 transition-colors"
            title="Show Legend"
          >
            <Eye className="w-4 h-4" />
            <span>Show Legend</span>
          </button>
        </div>
      )}

      {/* Status Legend - Only show for Domain Knowledge sub-tab and when toggled on */}
      {activeSubTab === 'Domain Knowledge' && showLegend && (
        <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10">
          <div className="flex gap-4 items-center px-4 py-2 bg-white rounded-lg shadow-lg border border-gray-200 text-sm text-gray-600">
            {/* Hide Legend Button */}
            <button
              onClick={() => setShowLegend(false)}
              className="flex items-center gap-1 px-2 py-1 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded transition-colors"
              title="Hide Legend"
            >
              <EyeClosed className="w-3 h-3" />
              <span>Hide</span>
            </button>
            
            {/* Separator */}
            <div className="w-px h-4 bg-gray-300"></div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border-2 border-amber-500 bg-amber-100"></div>
   
              <span>Pending</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border-2 border-blue-500 bg-blue-100"></div>
           
              <span>In Progress</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border-2 border-green-500 bg-green-100"></div>

              <span>Success</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border-2 border-red-500 bg-red-100"></div>
       
              <span>Failed</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded border-2 border-gray-500 bg-gray-100"></div>
              <span>Knowledge generation required</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeBaseTab;
