import React, { useState } from 'react';
import OverviewTab from './tabs/OverviewTab';
import KnowledgeBaseTab from './tabs/KnowledgeBaseTab';
import ToolsTab from './tabs/ToolsTab';
import CodeTab from './tabs/CodeTab';
import { ChatPane } from './ChatPane';
import { Code2, List, BookOpen } from 'lucide-react';
import { Tools } from 'iconoir-react';
import { IconMessage } from '@tabler/icons-react';
import { useAgentStore } from '@/stores/agent-store';

const TABS = ['Overview', 'Knowledge Base', 'Tools', 'Code'];

const TAB_ICONS = {
  Overview: <List className="w-4 h-4" />,
  'Knowledge Base': <BookOpen className="w-4 h-4" />,
  Tools: <Tools className="w-4 h-4" />,
  Code: <Code2 className="w-4 h-4" />,
};

export const AgentDetailTabs: React.FC<{
  onShowComparison: () => void;
  children?: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}> = ({ onShowComparison, children, activeTab, setActiveTab }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { selectedAgent } = useAgentStore();
  return (
    <div className="grid grid-cols-[1fr_max-content] h-full relative max-h-[calc(100vh-100px)]">
      {/* Main content area */}
      <div className="flex overflow-auto flex-col flex-1 gap-2 p-2 h-full">
        {/* Tab bar */}
        <div className="flex overflow-scroll justify-between items-center max-w-screen">
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
          <div className="flex gap-2 items-center pr-6">
            <IconMessage
              className={`w-6 h-6 cursor-pointer transition-colors ${isChatOpen ? 'text-blue-500' : 'text-gray-500 hover:text-gray-700'}`}
              onClick={() => setIsChatOpen(!isChatOpen)}
            />
          </div>
        </div>
        {/* Tab content */}
        {activeTab === 'Overview' && <OverviewTab onShowComparison={onShowComparison} />}
        {activeTab === 'Knowledge Base' && <KnowledgeBaseTab />}
        {activeTab === 'Tools' && <ToolsTab />}
        {activeTab === 'Code' && <CodeTab />}
        {children}
      </div>

      {/* Chat pane */}
      {isChatOpen && (
        <ChatPane
          agentName={selectedAgent?.name || 'Agent'}
          isVisible={isChatOpen}
          onClose={() => setIsChatOpen(false)}
        />
      )}
    </div>
  );
};
