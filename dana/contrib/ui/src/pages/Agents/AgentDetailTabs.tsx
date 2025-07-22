import React, { useState } from 'react';
import OverviewTab from './tabs/OverviewTab';
import DomainKnowledgeTab from './tabs/DomainKnowledgeTab';
import DocumentsTab from './tabs/DocumentsTab';
import WorkflowsTab from './tabs/WorkflowsTab';
import ToolsTab from './tabs/ToolsTab';
import CodeTab from './tabs/CodeTab';
import { Brain, Code2, FilesIcon, List } from 'lucide-react';
import { Network, Tools } from 'iconoir-react';

const TABS = ['Overview', 'Domain Knowledge', 'Documents', 'Workflows', 'Tools', 'Code'];

const TAB_ICONS = {
  Overview: <List className="w-4 h-4" />,
  'Domain Knowledge': <Brain className="w-4 h-4" />,
  Documents: <FilesIcon className="w-4 h-4" />,
  Workflows: <Network className="w-4 h-4" />,
  Tools: <Tools className="w-4 h-4" />,
  Code: <Code2 className="w-4 h-4" />,
};

export const AgentDetailTabs: React.FC<{
  onShowComparison: () => void;
  children?: React.ReactNode;
}> = ({ onShowComparison, children }) => {
  const [activeTab, setActiveTab] = useState('Overview');
  return (
    <div className="flex overflow-auto flex-col flex-1 gap-2 p-2 h-full">
      {/* Tab bar */}
      <div className="flex gap-2">
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`cursor-pointer px-4 py-2 font-medium text-sm flex items-center gap-2 transition-colors ${activeTab === tab ? 'bg-white rounded-sm shadow' : 'border-transparent text-gray-500'}`}
            onClick={() => setActiveTab(tab)}
          >
            {TAB_ICONS[tab as keyof typeof TAB_ICONS]}
            {tab}
          </button>
        ))}
      </div>
      {/* Tab content */}
      {activeTab === 'Overview' && <OverviewTab onShowComparison={onShowComparison} />}
      {activeTab === 'Domain Knowledge' && <DomainKnowledgeTab />}
      {activeTab === 'Documents' && <DocumentsTab />}
      {activeTab === 'Workflows' && <WorkflowsTab />}
      {activeTab === 'Tools' && <ToolsTab />}
      {activeTab === 'Code' && <CodeTab />}
      {children}
    </div>
  );
};
