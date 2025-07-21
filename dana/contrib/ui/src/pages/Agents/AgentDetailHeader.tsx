import React from 'react';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'iconoir-react';

interface AgentDetailHeaderProps {
  onBack: () => void;
  title: string;
  onDeploy?: () => void;
  onCancel?: () => void;
}

export const AgentDetailHeader: React.FC<AgentDetailHeaderProps> = ({ onBack, title, onDeploy, onCancel }) => (
  <div className="flex items-center justify-between px-8 py-4 border-b bg-white" style={{ minHeight: 64 }}>
    <div className='flex items-center gap-2 cursor-pointer ' onClick={onBack}>
      <ArrowLeft className='w-4 h-4' />
      <div className='font-semibold text-gray-700'>{title}</div>
    </div>
    <div className='flex items-center gap-2'>
      <div className='text-gray-500 text-sm cursor-pointer' onClick={onCancel}>Cancel</div>
      <Button size="sm" onClick={onDeploy}>
        Deploy
      </Button>
    </div>
  </div>
); 