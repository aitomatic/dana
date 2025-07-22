import React from 'react';
import { Button } from '@/components/ui/button';
import { useAgentStore } from '@/stores/agent-store';

const OverviewTab: React.FC<{ onShowComparison: () => void }> = ({ onShowComparison }) => {
  const agent = useAgentStore((s) => s.selectedAgent);
  return (
    <div className="flex flex-col gap-8 md:flex-row">
      <div className="flex flex-col flex-1 gap-4 p-6 bg-white rounded-lg border border-gray-200">
        <div className="flex gap-3 items-center mb-4">
          <div
            className={`flex justify-center items-center w-12 h-12 text-xl font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400 rounded-full`}
          ></div>
          {/* <div>
            <div className="text-lg font-semibold text-gray-900">Agent name</div>
            <div className="text-2xl font-bold text-gray-900">{agent?.name}</div>
          </div> */}
        </div>
        <div className="flex flex-col gap-2 p-4 text-sm rounded-lg border border-gray-200">
          <div className="text-sm font-semibold text-gray-500">Agent Profile</div>
          <div className="flex gap-2">
            <div className="w-40">Name:</div>
            <div>{agent?.name}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="w-40">Role:</div>
            <div>{agent?.config?.role ?? '-'}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="w-40">Specialties:</div>
            <div>{agent?.config?.specialties || '-'}</div>
          </div>
          <div className="flex items-center text-sm text-gray-700">
            <div className="w-40">Skills:</div>
            <div>{agent?.config?.skills || '-'}</div>
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
