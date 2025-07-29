import React from 'react';
import { useAgentStore } from '@/stores/agent-store';
import { getAgentAvatarSync } from '@/utils/avatar';


const OverviewTab: React.FC<{ onShowComparison: () => void }> = () => {
  const agent = useAgentStore((s) => s.selectedAgent);

  return (
    <div className="flex flex-col gap-8 md:flex-row">
      <div className="flex flex-col flex-1 gap-4 p-6 bg-white rounded-lg border border-gray-200">
        <div className="flex gap-3 flex-col">
          <div className="w-16 h-16 rounded-full overflow-hidden flex items-center justify-center">
            <img
              src={getAgentAvatarSync(agent?.id || 0)}
              alt={`${agent?.name || 'Agent'} avatar`}
              className="w-full h-full object-cover"
              onError={(e) => {
                // Fallback to colored circle if image fails to load
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
                const parent = target.parentElement;
                if (parent) {
                  parent.className = `w-12 h-12 rounded-full bg-gradient-to-br from-pink-400 to-purple-400 flex items-center justify-center text-white text-lg font-bold`;
                  parent.innerHTML = `<span className="text-white">${agent?.name?.[0] || 'A'}</span>`;
                }
              }}
            />
          </div>
          <div className='flex flex-col'>
            <div className='text-2xl font-semibold text-gray-900'>{agent?.name}</div>
          </div>
          {/* <div>
            <div className="text-lg font-semibold text-gray-900">Agent name</div>
            <div className="text-2xl font-bold text-gray-900">{agent?.name}</div>
          </div> */}
        </div>
        <div className="flex flex-col gap-2 text-sm rounded-lg">
          {/* <div className="text-sm font-semibold text-gray-500">Agent Profile</div> */}
          <div className="flex items-center text-sm text-gray-700">
            <div className="w-20">Domain:</div>
            <div className='text-gray-900 font-medium'>{agent?.config?.domain ?? '-'}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="w-20">Topic:</div>
            <div className='text-gray-900 font-medium'>{agent?.config?.topic || '-'}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="w-20">Tasks:</div>
            <div className='text-gray-900 font-medium'>{agent?.config?.task || agent?.config?.tasks || '-'}</div>
          </div>
        </div>
        {/* <div className="flex flex-col gap-2">
          <div className="text-sm font-semibold text-gray-500">Agent Performance</div>
          <table className="overflow-hidden w-full text-sm rounded-lg border">
            <thead>
              <tr className="bg-gray-50">
                <th className="p-2 text-left">No</th>
                <th className="p-2 text-left">Response Quality</th>
                <th className="p-2 text-left">{agent?.name}</th>
                <th className="p-2 text-left">Generic AI</th>
              </tr>
            </thead>
          </table>
        </div>
        <Button variant="outline" className="mt-2" onClick={onShowComparison}>
          Performance Comparison
        </Button> */}
      </div>
    </div>
  );
};

export default OverviewTab;
