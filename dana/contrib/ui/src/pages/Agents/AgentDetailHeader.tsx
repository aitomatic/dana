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
    className="flex justify-between items-center px-8 py-4 bg-white border-b"
    style={{ minHeight: 64 }}
  >
    <div className="flex gap-2 items-center cursor-pointer" onClick={onBack}>
      <ArrowLeft className="w-4 h-4" />
      <div className="font-semibold text-gray-700">{title}</div>
    </div>
    <div className="flex gap-4 items-center">
      <div className="text-sm text-gray-500 cursor-pointer" onClick={onCancel}>
        Cancel
      </div>
      <Button size="sm" onClick={onDeploy}>
        Save
      </Button>
    </div>
  </div>
);
