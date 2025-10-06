import React, { useRef, useEffect, useState } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import PortalPopup from './PortalPopup';
import FileIcon from '@/components/file-icon';
import type { KnowledgeTopicStatus } from '@/lib/api';
import {
  SystemRestart,
  Xmark,
  NavArrowRight,
  Clock,
  CheckCircle,
  QuestionMark,
  Trash,
} from 'iconoir-react';
// import { XCircle } from 'lucide-react';

// Single transition definition for consistency (matching DomainKnowledgeTree)
const TRANSITION_DURATION = '0.5s';
const TRANSITION_EASING = 'cubic-bezier(.43,.08,.45,.97)';
const TRANSITION_ALL = `all ${TRANSITION_DURATION} ${TRANSITION_EASING}`;

// Add CSS styles for node selection and generation
const nodeStyles = `
  .custom-node {
    transition: ${TRANSITION_ALL};
  }

  .custom-node.selected {
    transform: scale(1.02) !important;
    z-index: 10 !important;
    animation: selectedPulse 2s ease-in-out infinite;
  }

  .custom-node.generating {
    animation: generatingPulse 2s ease-in-out infinite;
  }

  @keyframes selectedPulse {
    0%, 100% {
      box-shadow: 0 0 0 1px #333, 0 4px 12px rgba(59, 130, 246, 0.1);
    }
    50% {
      box-shadow: 0 0 0 1px #333, 0 4px 16px rgba(59, 130, 246, 0.1);
    }
  }

  @keyframes generatingPulse {
    0%, 100% {
      box-shadow: 0 0 0 2px #3B82F6, 0 0 0 4px rgba(59, 130, 246, 0.2);
    }
    50% {
      box-shadow: 0 0 0 2px #3B82F6, 0 0 0 8px rgba(59, 130, 246, 0.1);
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
  isGenerating?: boolean;
  onNodeClick: (event: React.MouseEvent) => void;
  onDeleteNode?: (nodeId: string, nodePath: string) => void;
}

interface NodeData {
  label: string;
  knowledgeStatus?: KnowledgeTopicStatus | null;
  isLeafNode?: boolean;
  hasChildren?: boolean;
  isExpanded?: boolean;
  nodePath?: string;
  isRootNode?: boolean;
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
  console.log('🧠 status: ', status);
  switch (status) {
    case 'pending':
      return <Clock className="text-amber-500" />;
    case 'in_progress':
      return <SystemRestart className="text-blue-500 animate-spin" />;
    case 'success':
      return <CheckCircle className="text-green-500" />;
    case 'failed':
      return <Xmark className="text-red-500" />;
    default:
      return <QuestionMark className="text-gray-400" />;
  }
};

const getStatusText = (status?: string) => {
  switch (status) {
    case 'pending':
      return 'Knowledge generation pending';
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

export const FilePopup = ({
  knowledgeStatus,
  isLeafNode,
  x,
  y,
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
    {/* <div className="px-3 py-2 text-sm font-semibold text-gray-700 border-b border-gray-200">
      {nodePath || 'Node Information'}
    </div> */}
    {isLeafNode ? (
      <div className="flex flex-col gap-2 p-3">
        <div className="flex gap-2 items-center text-xs">
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
            Last modified: {new Date(knowledgeStatus.last_generated).toLocaleString()}
          </div>
        )}
        {knowledgeStatus?.error && (
          <div className="p-2 text-xs text-red-600 bg-red-50 rounded">
            Error: {knowledgeStatus.error}
          </div>
        )}
        {knowledgeStatus?.status === 'success' && (
          <div className="flex items-center gap-2 text-xs text-gray-600 max-w-[200px] overflow-eclipse truncate">
            <FileIcon ext={'json'} />
            {knowledgeStatus.file}
          </div>
        )}
      </div>
    ) : null}
  </PortalPopup>
);

const CustomNode: React.FC<CustomNodeProps> = ({ data, isSelected, isGenerating = false, onNodeClick, onDeleteNode }) => {
  const nodeRef = useRef<HTMLDivElement>(null);
  const [, setPopupPos] = useState<{ x: number; y: number } | null>(null);
  const [isHovered, setIsHovered] = useState(false);

  const nodeData = data as NodeData;
  const knowledgeStatus = nodeData.knowledgeStatus;
  const isLeafNode = nodeData.isLeafNode;
  const hasChildren = nodeData.hasChildren;
  const isExpanded = nodeData.isExpanded;
  const isRootNode = nodeData.isRootNode;

  // Handle delete button click
  const handleDeleteClick = (event: React.MouseEvent) => {
    // Use nodePath as fallback ID if data.id is undefined
    const nodeId = data.id || nodeData.nodePath;
    event.stopPropagation(); // Prevent node click
    if (onDeleteNode && nodeData.nodePath) {
      onDeleteNode(nodeId, nodeData.nodePath);
    }
  };

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
    if (isGenerating) baseClasses.push('generating');
    return baseClasses.join(' ');
  };

  // Render selection indicator
  // const renderSelectionIndicator = () => {
  //   if (!isSelected) return null;

  //   return (
  //     <div className="flex absolute -top-1 -right-1 justify-center items-center w-5 h-5 bg-blue-600 rounded-full shadow-lg animate-pulse">
  //       {/* <CheckIcon size={14} className="text-white" /> */}
  //     </div>
  //   );
  // };

  // Get node styling based on knowledge status and node type
  const getNodeStyling = () => {
    const baseStyle = {
      padding: 16,
      borderRadius: 8,
      width: 280,
      textAlign: 'left' as const,
      wordBreak: 'break-word' as const,
      whiteSpace: 'pre-line' as const,
      overflowWrap: 'break-word' as const,
      display: 'flex',
      position: 'relative' as const,
      cursor: hasChildren ? 'pointer' : 'default',
      transition: TRANSITION_ALL, // Enhanced smooth transitions
      transform: 'scale(1)',
      opacity: 1,
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

    // Add generation styling (prioritize over other states)
    if (isGenerating) {
      return {
        ...baseStyle,
        ...selectionStyle,
        background: '#DBEAFE', // Light blue (same as in_progress)
        border: '2px solid #3B82F6', // Blue border
        boxShadow: '0 0 0 2px #3B82F6, 0 0 0 4px rgba(59, 130, 246, 0.2)',
      };
    }

    if (!isLeafNode) {
      // Parent nodes - different styling based on expansion state
      return {
        ...baseStyle,
        ...selectionStyle,
        background: hasChildren ? (isExpanded ? '#F6FAFF' : '#F6FAFF') : '#F6FAFF',
        border: hasChildren
          ? isExpanded
            ? '1px solid #aac5e6'
            : '1px solid #aac5e6'
          : '1px solid #aac5e6',
        fontWeight: hasChildren ? 'bold' : 'normal',
      };
    }

    // Leaf nodes - status-based styling
    switch (knowledgeStatus?.status) {
      case 'pending':
        return {
          ...baseStyle,
          ...selectionStyle,
          background: '#FEF3C7', // Light yellow/amber
          border: '2px solid #F59E0B', // Amber border
          opacity: 0.8, // Slightly faded
        };
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
          opacity: 0.6, // More faded for unknown status
        };
    }
  };

  return (
    <div
      ref={nodeRef}
      className={getNodeClasses()}
      style={getNodeStyling()}
      onClick={onNodeClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        style={{
          width: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <span style={{ textAlign: 'left', flex: 1 }}>{nodeData.label}</span>
        {/* Icons positioned on the right edge */}
        <div style={{ display: 'flex', alignItems: 'center', marginLeft: 8, gap: 4 }}>
          {/* Delete button - only show on hover and if onDeleteNode is provided, but not on root nodes */}
          {isHovered && onDeleteNode && !isRootNode && (
            <button
              onClick={handleDeleteClick}
              style={{
                position: 'absolute',
                right: 0,
                top: '0%',
                transform: 'translate(25%,-40%)',
                border: '1px solid rgba(166, 166, 166, 0.3)',
                background: 'rgba(255, 255, 255, 1)',
                borderRadius: '99px',
                padding: '10px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s ease',
                zIndex: 1000,
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.background = '#f1f1f1';
                e.currentTarget.style.borderColor = 'rgba(166, 166, 166, 0.5)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = '#f1f1f1';
                e.currentTarget.style.borderColor = 'rgba(166, 166, 166, 0.3)';
              }}
              title="Delete node"
            >
              <Trash width={20} height={20} style={{ color: '#7d7d7d' }} />
            </button>
          )}
          {hasChildren && (
            <span style={{ fontSize: '16px' }}>{isExpanded ? '' : <NavArrowRight />}</span>
          )}
          {/* Generating indicator - show spinning icon when generating */}
          {isGenerating && (
            <span style={{ fontSize: '16px' }}>
              <SystemRestart className="text-blue-500 animate-spin" />
            </span>
          )}
          {/* Status icon - only show if not generating */}
          {isLeafNode && knowledgeStatus && !isGenerating && (
            <span style={{ fontSize: '16px' }}>{getStatusIcon(knowledgeStatus.status)}</span>
          )}
        </div>
      </div>

      {/* Progress bar for in-progress knowledge generation */}
      {isLeafNode && knowledgeStatus?.status === 'in_progress' && (
        <div className="mt-2 w-full h-2 bg-gray-200 rounded-full">
          <div
            className="h-2 bg-blue-500 rounded-full transition-all duration-300 animate-pulse"
            style={{ width: '100%' }}
          ></div>
        </div>
      )}

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
      {/* {isSelected && popupPos && (
        <FilePopup
          x={popupPos.x}
          y={popupPos.y}
          knowledgeStatus={knowledgeStatus}
          isLeafNode={isLeafNode}
          nodePath={nodeData.nodePath}
        />
      )} */}
    </div>
  );
};

export default CustomNode;
