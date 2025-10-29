import React, { useRef, useEffect, useState } from 'react';
import { Handle, Position } from 'reactflow';
import type { NodeProps } from 'reactflow';
import PortalPopup from './PortalPopup';
import FileIcon from '@/components/file-icon';
import type { KnowledgeTopicStatus } from '@/lib/api';
import { SystemRestart, Xmark, NavArrowRight, Clock, Trash } from 'iconoir-react';

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

  }

  @keyframes selectedPulse {
    0%, 100% {
      box-shadow: 0 0 0 1px #333, 0 4px 12px rgba(107, 79, 255, 0.1);
    }
    50% {
      box-shadow: 0 0 0 1px #333, 0 4px 16px rgba(107, 79, 255, 0.1);
    }
  }

  @keyframes generatingPulse {
    0%, 100% {
      box-shadow: 0 0 0 2px rgb(107, 79, 255), 0 0 0 4px rgba(107, 79, 255, 0.2);
    }
    50% {
      box-shadow: 0 0 0 2px rgb(107, 79, 255), 0 0 0 8px rgba(107, 79, 255, 0.1);
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
    case 'draft':
    case 'pending': // Map pending to draft (combined status)
      return 'rgb(209, 213, 219)'; // Gray-300
    case 'generating':
    case 'in_progress': // Backward compatibility
      return 'rgb(79, 204, 255)'; // Cyan-400 - Primary cyan accent
    case 'question_generated':
      return 'rgb(192, 132, 252)'; // Purple-400
    case 'completed':
    case 'success': // Backward compatibility
      return 'rgb(16, 185, 129)'; // Success-500
    case 'failed':
      return 'rgb(255, 79, 79)'; // Error-500 - Ctrl.xyz error red
    default:
      return 'rgb(107, 108, 116)'; // Gray-500 - Ctrl.xyz tertiary text
  }
};

const getStatusIcon = (status?: string) => {
  console.log('🧠 status: ', status);
  switch (status) {
    case 'draft':
    case 'pending': // Map pending to draft (combined status)
      return null; // Draft/Not Started has no icon
    case 'generating':
    case 'in_progress': // Backward compatibility
      return <SystemRestart className="text-cyan-400 animate-spin" />;
    case 'question_generated':
      return <Clock className="text-purple-400" />; // Purple clock for intermediate state
    case 'completed':
    case 'success': // Backward compatibility
      return null;
    case 'failed':
      return <Xmark className="text-error-500" />;
    default:
      return null;
  }
};

const getStatusText = (status?: string) => {
  switch (status) {
    case 'draft':
    case 'pending': // Map pending to draft (combined status)
      return 'Not started';
    case 'generating':
    case 'in_progress': // Backward compatibility
      return 'Generating knowledge...';
    case 'question_generated':
      return 'Questions generated - ready for content';
    case 'completed':
    case 'success': // Backward compatibility
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
        {(knowledgeStatus?.status === 'success' || knowledgeStatus?.status === 'completed') && (
          <div className="flex items-center gap-2 text-xs text-gray-600 max-w-[200px] overflow-eclipse truncate">
            <FileIcon ext={'json'} />
            {knowledgeStatus.file}
          </div>
        )}
      </div>
    ) : null}
  </PortalPopup>
);

const CustomNode: React.FC<CustomNodeProps> = ({
  data,
  isSelected,
  isGenerating = false,
  onNodeClick,
  onDeleteNode,
}) => {
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
        background: 'rgb(207, 250, 254)', // Cyan-100 - Light cyan
        border: '1px solid rgb(79, 204, 255)', // Cyan-400 - Primary cyan accent
        boxShadow: '0 0 0 1px rgb(79, 204, 255)',
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
      case 'draft':
      case 'pending': // Map pending to draft (combined status)
        return {
          ...baseStyle,
          ...selectionStyle,
          background: 'rgb(249, 250, 251)', // Gray-50 - Very light
          border: '1px solid rgb(209, 213, 219)', // Gray-300
          opacity: 0.7, // Slightly faded
        };
      case 'generating':
      case 'in_progress': // Backward compatibility
        return {
          ...baseStyle,
          ...selectionStyle,
          background: 'rgb(207, 250, 254)', // Cyan-100 - Light cyan
          border: '1px solid rgb(79, 204, 255)', // Cyan-400 - Primary cyan accent
          boxShadow: '0 0 0 1px rgb(79, 204, 255)',
        };
      case 'question_generated':
        return {
          ...baseStyle,
          ...selectionStyle,
          background: 'rgb(243, 232, 255)', // Purple-50 - Light purple
          border: '1px solid rgb(192, 132, 252)', // Purple-400
          opacity: 0.9,
        };
      case 'completed':
      case 'success': // Backward compatibility
        return {
          ...baseStyle,
          ...selectionStyle,
          background: 'rgb(236, 253, 245)', // Success-100 - Light green
          border: '1px solid rgb(16, 185, 129)', // Success-500
        };
      case 'failed':
        return {
          ...baseStyle,
          ...selectionStyle,
          background: 'rgb(254, 226, 226)', // Error-100 - Light red
          border: '1px solid rgb(255, 79, 79)', // Error-500 - Ctrl.xyz error red
        };
      default:
        return {
          ...baseStyle,
          ...selectionStyle,
          background: 'rgb(243, 244, 246)', // Gray-100 - Light gray
          border: '1px solid rgb(107, 108, 116)', // Gray-500 - Ctrl.xyz tertiary text
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
              <SystemRestart className="text-cyan-500 animate-spin" />
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
            className="h-2 bg-cyan-400 rounded-full transition-all duration-300 animate-pulse"
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
    </div>
  );
};

export default CustomNode;
