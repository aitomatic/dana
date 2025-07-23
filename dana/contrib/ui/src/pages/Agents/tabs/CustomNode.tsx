import React, { useRef, useEffect, useState } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import PortalPopup from './PortalPopup';
import FileIcon from '@/components/file-icon';
import type { KnowledgeTopicStatus } from '@/lib/api';

interface CustomNodeProps extends NodeProps {
  isSelected: boolean;
  onNodeClick: (event: React.MouseEvent) => void;
}

interface NodeData {
  label: string;
  knowledgeStatus?: KnowledgeTopicStatus | null;
  isLeafNode?: boolean;
  nodePath?: string;
}

// Helper functions for status styling
const getStatusColor = (status?: string) => {
  switch (status) {
    case 'pending': return '#F97316'; // Orange
    case 'in_progress': return '#3B82F6'; // Blue
    case 'success': return '#10B981'; // Green
    case 'failed': return '#EF4444'; // Red
    default: return '#6B7280'; // Gray
  }
};

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'pending': return '⏳';
    case 'in_progress': return '🔄';
    case 'success': return '✅';
    case 'failed': return '❌';
    default: return '';
  }
};

const getStatusText = (status?: string) => {
  switch (status) {
    case 'pending': return 'Knowledge generation pending';
    case 'in_progress': return 'Generating knowledge...';
    case 'success': return 'Knowledge generated successfully';
    case 'failed': return 'Knowledge generation failed';
    default: return 'No knowledge status';
  }
};

const FilePopup = ({ 
  x, 
  y, 
  knowledgeStatus, 
  isLeafNode, 
  nodePath 
}: { 
  x: number; 
  y: number; 
  knowledgeStatus?: KnowledgeTopicStatus | null;
  isLeafNode?: boolean;
  nodePath?: string;
}) => (
  <PortalPopup style={{
    position: 'absolute',
    left: x,
    top: y,
    zIndex: 9999,
    background: 'white',
    borderRadius: 8,
    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
    minWidth: 200,
    maxWidth: 300,
    border: '1px solid #E0E0E0'
  }}>
    <div className='text-sm px-3 py-2 border-b border-gray-200 font-semibold text-gray-700'>
      {nodePath || 'Node Information'}
    </div>
    {isLeafNode ? (
      <div className='flex flex-col p-3 gap-2'>
        <div className='flex items-center gap-2 text-sm'>
          <span className='font-medium'>Status:</span>
          <span style={{ color: getStatusColor(knowledgeStatus?.status) }}>
            {getStatusIcon(knowledgeStatus?.status)} {getStatusText(knowledgeStatus?.status)}
          </span>
        </div>
        {knowledgeStatus?.last_generated && (
          <div className='text-xs text-gray-500'>
            Generated: {new Date(knowledgeStatus.last_generated).toLocaleString()}
          </div>
        )}
        {knowledgeStatus?.error && (
          <div className='text-xs text-red-600 bg-red-50 p-2 rounded'>
            Error: {knowledgeStatus.error}
          </div>
        )}
        {knowledgeStatus?.status === 'success' && (
          <div className='flex items-center gap-2 text-xs text-green-600'>
            <FileIcon ext={'json'} />
            {knowledgeStatus.file}
          </div>
        )}
      </div>
    ) : (
      <div className='px-3 py-2 text-sm text-gray-600'>
        This is a parent node. Knowledge is generated for leaf nodes only.
      </div>
    )}
  </PortalPopup>
);

const CustomNode: React.FC<CustomNodeProps> = ({ data, isSelected, onNodeClick }) => {
  const nodeRef = useRef<HTMLDivElement>(null);
  const [popupPos, setPopupPos] = useState<{ x: number; y: number } | null>(null);
  
  const nodeData = data as NodeData;
  const knowledgeStatus = nodeData.knowledgeStatus;
  const isLeafNode = nodeData.isLeafNode;

  useEffect(() => {
    if (isSelected && nodeRef.current) {
      const rect = nodeRef.current.getBoundingClientRect();
      setPopupPos({ x: rect.left, y: rect.bottom + 5 });
    }
  }, [isSelected]);

  // Get node styling based on knowledge status
  const getNodeStyling = () => {
    const baseStyle = {
      padding: 16,
      borderRadius: 8,
      minWidth: 120,
      maxWidth: 220,
      width: 220,
      textAlign: 'center' as const,
      wordBreak: 'break-word' as const,
      whiteSpace: 'pre-line' as const,
      overflowWrap: 'break-word' as const,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      position: 'relative' as const,
    };

    if (!isLeafNode) {
      // Parent nodes - default styling
      return {
        ...baseStyle,
        background: '#F6FAFF',
        border: '2px solid #E0E0E0',
      };
    }

    // Leaf nodes - status-based styling
    switch (knowledgeStatus?.status) {
      case 'pending':
        return {
          ...baseStyle,
          background: '#FEF3C7', // Light yellow
          border: '2px solid #F97316', // Orange border
        };
      case 'in_progress':
        return {
          ...baseStyle,
          background: '#DBEAFE', // Light blue
          border: '2px solid #3B82F6', // Blue border
        };
      case 'success':
        return {
          ...baseStyle,
          background: '#D1FAE5', // Light green
          border: '2px solid #10B981', // Green border
        };
      case 'failed':
        return {
          ...baseStyle,
          background: '#FEE2E2', // Light red
          border: '2px solid #EF4444', // Red border
        };
      default:
        return {
          ...baseStyle,
          background: '#F3F4F6', // Light gray
          border: '2px solid #9CA3AF', // Gray border
        };
    }
  };

  return (
    <div
      ref={nodeRef}
      className='relative'
      style={getNodeStyling()}
      onClick={onNodeClick}
    >
      <div style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
        <span>{nodeData.label}</span>
        {isLeafNode && knowledgeStatus && (
          <span style={{ fontSize: '16px' }}>
            {getStatusIcon(knowledgeStatus.status)}
          </span>
        )}
      </div>
      {/* Handles can be hidden or removed if not needed */}
      <Handle type="target" position={Position.Left} style={{ background: '#F6FAFF', border: '1px solid #E0E0E0' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#F6FAFF', border: '1px solid #E0E0E0' }} />
      {isSelected && popupPos && (
        <FilePopup 
          x={popupPos.x} 
          y={popupPos.y} 
          knowledgeStatus={knowledgeStatus}
          isLeafNode={isLeafNode}
          nodePath={nodeData.nodePath}
        />
      )}
    </div>
  )
};

export default CustomNode; 