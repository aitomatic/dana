import React, { useState } from 'react';
import OverviewTab from './tabs/OverviewTab';
import DomainKnowledgeTab from './tabs/DomainKnowledgeTab';
import DocumentsTab from './tabs/DocumentsTab';
import WorkflowsTab from './tabs/WorkflowsTab';
import ToolsTab from './tabs/ToolsTab';
import CodeTab from './tabs/CodeTab';

const TABS = [
  'Overview',
  'Domain Knowledge',
  'Documents',
  'Workflows',
  'Tools',
  'Code',
];

export const AgentDetailTabs: React.FC<{
  tpl: any;
  onShowComparison: () => void;
  children?: React.ReactNode;
}> = ({ tpl, onShowComparison, children }) => {
  const [activeTab, setActiveTab] = useState('Overview');
  return (
    <div className="flex-1 flex flex-col overflow-auto h-full">
      {/* Tab bar */}
      <div className="flex gap-2">
        {TABS.map(tab => (
          <button
            key={tab}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${activeTab === tab ? 'border-blue-600 text-blue-700' : 'border-transparent text-gray-500 hover:text-blue-600'}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>
      {/* Tab content */}
      {activeTab === 'Overview' && <OverviewTab tpl={tpl} onShowComparison={onShowComparison} />}
      {activeTab === 'Domain Knowledge' && <DomainKnowledgeTab />}
      {activeTab === 'Documents' && <DocumentsTab />}
      {activeTab === 'Workflows' && <WorkflowsTab />}
      {activeTab === 'Tools' && <ToolsTab />}
      {activeTab === 'Code' && <CodeTab />}
      {children}
    </div>
  );
}; 