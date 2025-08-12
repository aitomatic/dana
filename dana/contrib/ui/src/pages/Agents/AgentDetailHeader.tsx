import React from 'react';
import { Button } from '@/components/ui/button';
import { Play } from 'iconoir-react';

interface AgentDetailHeaderProps {
  title: string;
  onDeploy?: () => void;
  onCancel?: () => void;
}

export const AgentDetailHeader: React.FC<AgentDetailHeaderProps> = ({
  title,
  onDeploy,
  onCancel,
}) => (
  <div className="flex justify-between items-center px-6 py-4 bg-white border-b h-[64px]">
    <div className="font-semibold text-gray-700">{title}</div>
    <div className="flex gap-2 items-center">
      <Button
        variant="ghost"
        className="px-4 py-1 text-sm font-medium text-gray-500 cursor-pointer"
        onClick={onCancel}
      >
        Close
      </Button>
      <Button variant="default" className="px-4 py-1 font-semibold" onClick={onDeploy}>
        <Play className="w-4 h-4" strokeWidth={1.5} /> Use Mode
      </Button>
    </div>
  </div>
);
