import React from 'react';
import DanaAvatar from '/agent-avatar/javis-avatar.svg';
import AgentGenerationChat from '@/components/agent-generation-chat';

export const AgentDetailSidebar: React.FC = () => (
  <div className="w-[320px] min-w-[280px] p-2 bg-gray-50">
    <div className='bg-white flex flex-col h-full shadow-md rounded-lg'>
      <div className="flex items-center gap-3 mb-4 border-b border-gray-200 p-4">
        <img className="w-10 h-10 rounded-full" src={DanaAvatar} alt="Dana avatar" />
        <div>
          <div className="font-semibold text-gray-900">Dana</div>
          <div className="text-xs text-gray-500">Agent builder assistant</div>
        </div>
      </div>
      <div className="flex-1 flex flex-col mb-4">
        <AgentGenerationChat
          onCodeGenerated={() => { }}
          currentCode={''}
          className="h-full"
          onGenerationStart={() => { }}
          onPhaseChange={() => { }}
          onReadyForCodeGeneration={() => { }}
        />
      </div>
    </div>
  </div>
); 