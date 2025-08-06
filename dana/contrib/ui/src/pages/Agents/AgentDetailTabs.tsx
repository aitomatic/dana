import React, { useState } from 'react';
import OverviewTab from './tabs/OverviewTab';
import KnowledgeBaseTab from './tabs/KnowledgeBaseTab';
import ToolsTab from './tabs/ToolsTab';
import CodeTab from './tabs/CodeTab';
import { ChatPane } from './ChatPane';
import { Code2, List, BookOpen } from 'lucide-react';
import { Tools } from 'iconoir-react';
import { Button } from '@/components/ui/button';
import { useAgentStore } from '@/stores/agent-store';
import { getAgentAvatarSync } from '@/utils/avatar';
import type { NavigateFunction } from 'react-router-dom';

const TABS = ['Overview', 'Knowledge Base', 'Tools', 'Code'];

const TAB_ICONS = {
  Overview: <List className="w-4 h-4" />,
  'Knowledge Base': <BookOpen className="w-4 h-4" />,
  Tools: <Tools className="w-4 h-4" />,
  Code: <Code2 className="w-4 h-4" />,
};

export const AgentDetailTabs: React.FC<{
  children?: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  navigate: NavigateFunction;
}> = ({ children, activeTab, setActiveTab, navigate }) => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { selectedAgent } = useAgentStore();
  return (
    <div className="grid grid-cols-[1fr_max-content] h-full relative overflow-hidden">
      {/* Main content area */}
      <div className=" overflow-auto grid grid-cols-1 grid-rows-[max-content_1fr] flex-1 gap-2 p-2 h-full">
        {/* Tab bar */}
        <div className="flex justify-between items-center max-w-screen h-[40px]">
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
          <div className="flex gap-2 items-center">
            {!isChatOpen && (
              <Button
                variant="outline"
                // size="sm"
                className="flex gap-2 items-center px-3 py-2 text-gray-700 bg-white rounded-full border-gray-200 hover:bg-gray-50"
                onClick={() => setIsChatOpen(!isChatOpen)}
              >
                {/* Agent Avatar */}
                <div className="flex overflow-hidden justify-center items-center w-6 h-6 rounded-full">
                  <img
                    src={getAgentAvatarSync(selectedAgent?.id || 0)}
                    alt={`${selectedAgent?.name || 'Agent'} avatar`}
                    className="object-cover w-full h-full"
                    onError={(e) => {
                      // Fallback to colored circle if image fails to load
                      const target = e.target as HTMLImageElement;
                      target.style.display = 'none';
                      const parent = target.parentElement;
                      if (parent) {
                        parent.className = `flex justify-center items-center w-6 h-6 rounded-full bg-brand-100`;
                        parent.innerHTML = `<span className="text-xs font-medium text-brand-700">${selectedAgent?.name?.[0] || 'A'}</span>`;
                      }
                    }}
                  />
                </div>

                {/* Chat Text */}
                <span className="text-sm font-medium">
                  Chat with {selectedAgent?.name || 'Agent'}
                </span>
              </Button>
            )}
          </div>
        </div>
        {/* Tab content */}
        {activeTab === 'Overview' && <OverviewTab navigate={navigate} />}
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
