import React, { useRef, useEffect, useState } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import PortalPopup from './PortalPopup';
import FileIcon from '@/components/file-icon';

interface CustomNodeProps extends NodeProps {
  isSelected: boolean;
  onNodeClick: (event: React.MouseEvent) => void;
}

const FilePopup = ({ x, y }: { x: number; y: number }) => (
  <PortalPopup style={{
    position: 'absolute',
    left: x,
    top: y,
    zIndex: 9999,
    background: 'white',
    borderRadius: 8,
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    minWidth: 160,
    border: '1px solid #E0E0E0'
  }}>
    <div className='text-sm px-3 py-2 border-b border-gray-200 font-semibold text-gray-500'>2 documents</div>
    <div className='flex flex-col'>
      <div className='flex items-center px-3 py-2 gap-2 border-b border-gray-200'> <FileIcon ext={'pdf'} /> Industry.pdf</div>
      <div className='flex items-center px-3 py-2 gap-2'> <FileIcon ext={'pdf'} /> case 1.pdf</div>
    </div>
  </PortalPopup>
);

const CustomNode: React.FC<CustomNodeProps> = ({ data, isSelected, onNodeClick }) => {
  const nodeRef = useRef<HTMLDivElement>(null);
  const [popupPos, setPopupPos] = useState<{ x: number; y: number } | null>(null);

  useEffect(() => {
    if (isSelected && nodeRef.current) {
      const rect = nodeRef.current.getBoundingClientRect();
      setPopupPos({ x: rect.left, y: rect.bottom + 5 });
    }
  }, [isSelected]);

  return (
    <div
      ref={nodeRef}
      className='relative'
      style={{
        padding: 16,
        background: '#F6FAFF',
        borderRadius: 8,
        minWidth: 120,
        maxWidth: 220,
        width: 220,
        textAlign: 'center',
        wordBreak: 'break-word',
        whiteSpace: 'pre-line',
        overflowWrap: 'break-word',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
      }}
      onClick={onNodeClick}
    >
      <div style={{ width: '100%' }}>{data.label}</div>
      {/* Handles can be hidden or removed if not needed */}
      <Handle type="target" position={Position.Left} style={{ background: '#F6FAFF', border: '1px solid #E0E0E0' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#F6FAFF', border: '1px solid #E0E0E0' }} />
      {isSelected && popupPos && <FilePopup x={popupPos.x} y={popupPos.y} />}
    </div>
  )
};

export default CustomNode; 