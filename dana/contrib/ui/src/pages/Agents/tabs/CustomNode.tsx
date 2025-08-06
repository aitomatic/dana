import React, { useRef, useEffect, useState } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import PortalPopup from './PortalPopup';
import FileIcon from '@/components/file-icon';
import type { KnowledgeTopicStatus } from '@/lib/api';
import { CheckIcon, Loader2Icon, XIcon, ChevronRight, ChevronDown } from 'lucide-react';

// Add CSS styles for node selection
const nodeStyles = `
  .custom-node {
    transition: all 0.2s ease;
  }

  .custom-node.selected {

    transform: scale(1.02) !important;
    z-index: 10 !important;
    animation: selectedPulse 2s ease-in-out infinite;
  }


  @keyframes selectedPulse {
    0%, 100% {
      box-shadow: 0 0 0 1px #333, 0 4px 12px rgba(59, 130, 246, 0.3);
    }
    50% {
      box-shadow: 0 0 0 1px #333, 0 4px 16px rgba(59, 130, 246, 0.4);
    }
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = nodeStyles;
  document.head.appendChild(styleElement);
}

interface CustomNodeProps extends NodeProps {
  isSelected: boolean;
  onNodeClick: (event: React.MouseEvent) => void;
}

interface NodeData {
  label: string;
  knowledgeStatus?: KnowledgeTopicStatus | null;
  isLeafNode?: boolean;
  hasChildren?: boolean;
  isExpanded?: boolean;
  nodePath?: string;
}

// Helper functions for status styling
const getStatusColor = (status?: string) => {
  switch (status) {
    // case 'pending': return '#F97316'; // Orange
    case 'in_progress':
      return '#3B82F6'; // Blue
    case 'success':
      return '#10B981'; // Green
    case 'failed':
      return '#EF4444'; // Red
    default:
      return '#6B7280'; // Gray
  }
};

const getStatusIcon = (status?: string) => {
  switch (status) {
    case 'in_progress':
      return <Loader2Icon className="animate-spin" />;
    case 'success':
      return <CheckIcon />;
    case 'failed':
      return <XIcon />;
    default:
      return '';
  }
};

const getStatusText = (status?: string) => {
  switch (status) {
    // case 'pending': return 'Knowledge generation pending';
    case 'in_progress':
      return 'Generating knowledge...';
    case 'success':
      return 'Knowledge generated successfully';
    case 'failed':
      return 'Knowledge generation failed';
    default:
      return 'No knowledge status';
  }
};

const FilePopup = ({
  x,
  y,
  knowledgeStatus,
  isLeafNode,
  nodePath,
}: {
  x: number;
  y: number;
  knowledgeStatus?: KnowledgeTopicStatus | null;
  isLeafNode?: boolean;
  nodePath?: string;
}) => (
  <PortalPopup
    style={{
      position: 'absolute',
      display: 'none',
      left: x,
      top: y,
      zIndex: 9999,
      background: 'white',
      borderRadius: 8,
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      minWidth: 200,
      maxWidth: 300,
      border: '1px solid #E0E0E0',
    }}
  >
    <div className="px-3 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
      {nodePath || 'Node Information'}
    </div>
    {isLeafNode ? (
      <div className="flex flex-col gap-2 p-3">
        <div className="flex gap-2 items-center text-sm">
          <div className="font-medium">Status:</div>
          <div
            className="flex gap-2 items-center"
            style={{ color: getStatusColor(knowledgeStatus?.status) }}
          >
            <div>{getStatusIcon(knowledgeStatus?.status)}</div>
            <div>{getStatusText(knowledgeStatus?.status)}</div>
          </div>
        </div>
        {knowledgeStatus?.last_generated && (
          <div className="text-xs text-gray-500">
            Generated: {new Date(knowledgeStatus.last_generated).toLocaleString()}
          </div>
        )}
        {knowledgeStatus?.error && (
          <div className="p-2 text-xs text-red-600 bg-red-50 rounded">
            Error: {knowledgeStatus.error}
          </div>
        )}
        {knowledgeStatus?.status === 'success' && (
          <div className="flex items-center gap-2 text-xs text-green-600 max-w-[200px] truncate">
            <FileIcon ext={'json'} />
            {knowledgeStatus.file}
          </div>
        )}
      </div>
    ) : (
      <div className="px-3 py-2 text-sm text-gray-600">
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
  const hasChildren = nodeData.hasChildren;
  const isExpanded = nodeData.isExpanded;

  useEffect(() => {
    if (isSelected && nodeRef.current) {
      const rect = nodeRef.current.getBoundingClientRect();
      setPopupPos({ x: rect.left, y: rect.bottom + 5 });
    }
  }, [isSelected]);

  // Get CSS classes for the node
  const getNodeClasses = () => {
    const baseClasses = ['custom-node'];
    if (isSelected) baseClasses.push('selected');
    return baseClasses.join(' ');
  };

  // Render selection indicator
  // const renderSelectionIndicator = () => {
  //   if (!isSelected) return null;

  //   return (
  //     <div className="absolute -top-1 -right-1 w-5 h-5 bg-blue-600 rounded-full flex items-center justify-center shadow-lg animate-pulse">
  //       {/* <CheckIcon size={14} className="text-white" /> */}
  //     </div>
  //   );
  // };

  // Get node styling based on knowledge status and node type
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
      cursor: hasChildren ? 'pointer' : 'default',
      transition: 'all 0.2s ease', // Add smooth transitions
    };

    // Add selection highlighting
    const selectionStyle = isSelected
      ? {
          // boxShadow: '0 0 0 1px #3B82F6, 0 4px 12px rgba(59, 130, 246, 0.3)',
          border: 'none',
          transform: 'scale(1.02)',
          zIndex: 10,
        }
      : {};

    if (!isLeafNode) {
      // Parent nodes - different styling based on expansion state
      return {
        ...baseStyle,
        ...selectionStyle,
        background: hasChildren ? (isExpanded ? '#EBF8FF' : '#F6FAFF') : '#F6FAFF',
        border: hasChildren
          ? isExpanded
            ? '2px solid #3B82F6'
            : '2px solid #93C5FD'
          : '2px solid #E0E0E0',
        fontWeight: hasChildren ? 'bold' : 'normal',
      };
    }

    // Leaf nodes - status-based styling
    switch (knowledgeStatus?.status) {
      // case 'pending':
      //   return {
      //     ...baseStyle,
      //     background: '#FEF3C7', // Light yellow
      //     border: '2px solid #F97316', // Orange border
      //   };
      case 'in_progress':
        return {
          ...baseStyle,
          ...selectionStyle,
          background: '#DBEAFE', // Light blue
          border: '2px solid #3B82F6', // Blue border
        };
      case 'success':
        return {
          ...baseStyle,
          ...selectionStyle,
          background: '#D1FAE5', // Light green
          border: '2px solid #10B981', // Green border
        };
      case 'failed':
        return {
          ...baseStyle,
          ...selectionStyle,
          background: '#FEE2E2', // Light red
          border: '2px solid #EF4444', // Red border
        };
      default:
        return {
          ...baseStyle,
          ...selectionStyle,
          background: '#F3F4F6', // Light gray
          border: '2px solid #9CA3AF', // Gray border
        };
    }
  };

  return (
    <div ref={nodeRef} className={getNodeClasses()} style={getNodeStyling()} onClick={onNodeClick}>
      <div
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
        }}
      >
        {/* Show expand/collapse icon for nodes with children */}
        {hasChildren && (
          <span style={{ fontSize: '16px', marginRight: 8 }}>
            {isExpanded ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          </span>
        )}
        <span>{nodeData.label}</span>
        {isLeafNode && knowledgeStatus && (
          <span style={{ fontSize: '16px', marginLeft: 8 }}>
            {getStatusIcon(knowledgeStatus.status)}
          </span>
        )}
      </div>

      {/* Handles can be hidden or removed if not needed */}
      <Handle
        type="target"
        position={Position.Left}
        style={{ background: '#F6FAFF', border: '1px solid #E0E0E0' }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ background: '#F6FAFF', border: '1px solid #E0E0E0' }}
      />
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
  );
};

export default CustomNode;
