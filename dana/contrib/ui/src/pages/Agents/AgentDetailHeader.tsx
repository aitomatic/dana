import React from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'iconoir-react';

interface AgentDetailHeaderProps {
  onBack: () => void;
  title: string;
  onDeploy?: () => void;
  onCancel?: () => void;
}

export const AgentDetailHeader: React.FC<AgentDetailHeaderProps> = ({
  onBack,
  title,
  onDeploy,
  onCancel,
}) => (
  <div
    className="flex justify-between items-center px-6 py-4 bg-white border-b"
    style={{ minHeight: 64 }}
  >
    <div className="flex gap-1 items-center cursor-pointer" onClick={onBack}>
      <div className="flex justify-center items-center w-8 h-8 rounded-full transition-colors hover:bg-gray-100">
        <ArrowLeft className="w-4 h-4" />
      </div>
      <div className="font-semibold text-gray-700">{title}</div>
    </div>
    <div className="flex items-center">
      <Button
        variant="ghost"
        className="px-4 py-1 text-sm font-medium text-gray-500 cursor-pointer"
        onClick={onCancel}
      >
        Cancel
      </Button>
      <Button variant="default" className="px-4 py-1 font-medium" onClick={onDeploy}>
        Save
      </Button>
    </div>
  </div>
);
