import React from 'react';
import { Button } from '@/components/ui/button';

export const AgentDetailSidebar: React.FC<{ children?: React.ReactNode }> = ({ children }) => (
  <div className="w-[320px] min-w-[280px] bg-white border-r border-gray-200 flex flex-col p-6 h-full">
    <div className="flex items-center gap-3 mb-4">
      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-400 to-purple-400 flex items-center justify-center text-white text-lg font-bold">D</div>
      <div>
        <div className="font-semibold text-gray-900">Dana</div>
        <div className="text-xs text-gray-500">Agent builder assistant</div>
      </div>
    </div>
    <div className="bg-gray-50 rounded-lg p-4 text-gray-700 text-sm mb-4">
      Great choice on the Finance Specialist <b>Georgia</b>!<br /><br />
      Feel free to review Georgia's setup in the summary panel, then let me know if you need any customization.<br /><br />
      Here are the next steps I'd recommend to make Georgia specifically brilliant for your company:
    </div>
    <div className="flex flex-col gap-2 mb-4">
      <Button variant="outline" className="w-full">Add company financial documents</Button>
      <Button variant="outline" className="w-full">Review and customize workflows</Button>
    </div>
    <div className="mt-auto">
      <textarea className="w-full border rounded-lg p-2 text-sm text-gray-700" placeholder="Chat with Dana to build up your agent" rows={2} />
    </div>
    {children}
  </div>
); 