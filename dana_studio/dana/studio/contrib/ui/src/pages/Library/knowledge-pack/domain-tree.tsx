/* eslint-disable react-hooks/exhaustive-deps */
/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect, useRef, useCallback } from 'react';
import ReactFlow, { Controls, Position, MarkerType } from 'reactflow';
import type { Node as FlowNode, Edge, ReactFlowInstance } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import CustomNode from '@/components/knowledge-tree/CustomNode';
import { apiService } from '@/lib/api';
import { useKnowledgePackStore } from '@/stores';
import { useKnowledgePackWebSocket } from '@/hooks/useKnowledgePackWebSocket';
import type { DomainKnowledgeResponse, DomainNode } from '@/types/domainKnowledge';
import type {
  KnowledgeTopicStatus,
  KnowledgeStatusResponse,
  BackgroundTaskResponse,
} from '@/lib/api';
import KnowledgeSidebar from '@/components/knowledge-tree/KnowledgeSidebar';
import { Search, Collapse, Expand, Xmark, LightBulb, ThumbsUp, SystemRestart, Check } from 'iconoir-react';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

// Single transition definition for consistency
const TRANSITION_DURATION = '0.5s';
const TRANSITION_EASING = 'cubic-bezier(.43,.08,.45,.97)';
const TRANSITION_ALL = `all ${TRANSITION_DURATION} ${TRANSITION_EASING}`;

// Add CSS animations for smooth transitions (optimized for zoom performance)
const animationStyles = `
  .react-flow__node {
    /* Only transition opacity and non-transform properties to avoid zoom lag */
    transition: opacity ${TRANSITION_DURATION} ${TRANSITION_EASING} !important;
  }

  .react-flow__node-enter {
    opacity: 0;
    transform: scale(0.8) translateY(10px);
  }

  .react-flow__node-enter-active {
    opacity: 1;
    transform: scale(1) translateY(0);
  }

  .react-flow__node-exit {
    opacity: 1;
    transform: scale(1) translateY(0);
  }

  .react-flow__node-exit-active {
    opacity: 0;
    transform: scale(0.8) translateY(-10px);
  }

  /* Edge animations - optimized for performance */
  .react-flow__edge {
    /* Only transition opacity to avoid interfering with zoom */
    transition: opacity ${TRANSITION_DURATION} ${TRANSITION_EASING} !important;
  }

  .react-flow__edge-path {
    /* Don't transition edge paths during zoom operations */
  }

  /* Animate edges when they appear - using data attributes for better targeting */
  .react-flow__edge[data-edge-new="true"],
  .react-flow__edges g[data-edge-new="true"] {
    opacity: 0 !important;
    animation: edgeAppear 0.8s cubic-bezier(.43,.08,.45,.97) forwards !important;
  }

  .react-flow__edge[data-edge-new="true"] .react-flow__edge-path,
  .react-flow__edges g[data-edge-new="true"] .react-flow__edge-path {
    stroke-dasharray: 1000 !important;
    stroke-dashoffset: 1000 !important;
    animation: edgePathAppear 0.8s cubic-bezier(.43,.08,.45,.97) forwards !important;
  }

  /* Also target edge paths directly with data attribute */
  .react-flow__edge-path[data-edge-new="true"] {
    stroke-dasharray: 1000 !important;
    stroke-dashoffset: 1000 !important;
    animation: edgePathAppear 0.8s cubic-bezier(.43,.08,.45,.97) forwards !important;
  }

  /* Additional targeting for ReactFlow's edge structure */
  .react-flow__edges g[data-edge-new="true"] .react-flow__edge-path {
    stroke-dasharray: 1000 !important;
    stroke-dashoffset: 1000 !important;
    animation: edgePathAppear 0.8s cubic-bezier(.43,.08,.45,.97) forwards !important;
  }

  /* Keyframe animations for edges */
  @keyframes edgeAppear {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  @keyframes edgePathAppear {
    from {
      stroke-dashoffset: 1000;
    }
    to {
      stroke-dashoffset: 0;
    }
  }

  /* Ensure edges are visible during transitions */
  .react-flow__edge.selected .react-flow__edge-path {
    stroke-width: 3;
  }

  .react-flow__edge:hover .react-flow__edge-path {
    stroke-width: 2;
  }

  /* Smooth viewport transitions */
  .react-flow {
    transition: ${TRANSITION_ALL} !important;
  }

  .react-flow__viewport {
    /* No transitions on viewport to avoid zoom lag */
  }

  /* Remove transitions from zoom-sensitive elements to improve performance */
  .react-flow__transformationpane {
    /* No transitions on transformation pane to avoid zoom lag */
  }
`;

// Inject styles
if (typeof document !== 'undefined') {
  const styleElement = document.createElement('style');
  styleElement.textContent = animationStyles;
  document.head.appendChild(styleElement);
}

const initialNodes: FlowNode[] = [
  {
    id: '1',
    type: 'custom',
    data: { label: 'Finance' },
    position: { x: 0, y: 0 }, // dummy, will be overwritten
  },
  {
    id: '2',
    type: 'custom',
    data: { label: 'Market Analysis' },
    position: { x: 0, y: 0 },
  },
  {
    id: '3',
    type: 'custom',
    data: { label: 'Investment Strategy' },
    position: { x: 0, y: 0 },
  },
  {
    id: '4',
    type: 'custom',
    data: { label: 'Risk Management' },
    position: { x: 0, y: 0 },
  },
  {
    id: '5',
    type: 'custom',
    data: { label: 'Financial Planning' },
    position: { x: 0, y: 0 },
  },
  {
    id: '6',
    type: 'custom',
    data: { label: 'Corporate' },
    position: { x: 0, y: 0 },
  },
  {
    id: '7',
    type: 'custom',
    data: { label: 'Compliance' },
    position: { x: 0, y: 0 },
  },
];

const initialEdges: Edge[] = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'default',
    style: {
      stroke: '#6b7280',
      strokeWidth: 1,
      transition: TRANSITION_ALL,
      opacity: 1,
    },
    animated: false,
  },
  {
    id: 'e2-3',
    source: '2',
    target: '3',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'default',
    style: {
      stroke: '#6b7280',
      strokeWidth: 1,
      transition: TRANSITION_ALL,
      opacity: 1,
    },
    animated: false,
  },
  {
    id: 'e3-4',
    source: '3',
    target: '4',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'default',
    style: {
      stroke: '#6b7280',
      strokeWidth: 1,
      transition: TRANSITION_ALL,
      opacity: 1,
    },
    animated: false,
  },
  {
    id: 'e1-5',
    source: '1',
    target: '5',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'default',
    style: {
      stroke: '#6b7280',
      strokeWidth: 1,
      transition: TRANSITION_ALL,
      opacity: 1,
    },
    animated: false,
  },
  {
    id: 'e1-6',
    source: '1',
    target: '6',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'default',
    style: {
      stroke: '#6b7280',
      strokeWidth: 1,
      transition: TRANSITION_ALL,
      opacity: 1,
    },
    animated: false,
  },
  {
    id: 'e1-7',
    source: '1',
    target: '7',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'default',
    style: {
      stroke: '#6b7280',
      strokeWidth: 1,
      transition: TRANSITION_ALL,
      opacity: 1,
    },
    animated: false,
  },
];

const nodeWidth = 220; // Keep width for horizontal layout
const nodeHeight = 80; // Keep height for horizontal layout

function getLayoutedElements(nodes: FlowNode[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 60, // more separation for horizontal
    ranksep: 120, // more separation for horizontal
  });

  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    node.position = {
      x: nodeWithPosition.x - nodeWidth / 2,
      y: nodeWithPosition.y - nodeHeight / 2,
    };
    node.targetPosition = direction === 'LR' ? Position.Left : Position.Top;
    node.sourcePosition = direction === 'LR' ? Position.Right : Position.Bottom;
    return node;
  });
}

interface DomainKnowledgeTreeProps {
  knowledgePackId?: string | number;
  knowledgePackMetadata?: {
    domain?: string;
    role?: string;
  };
}

// KnowledgeIntroBox Component
interface KnowledgeIntroBoxProps {
  isVisible: boolean;
  hasNewKnowledge: boolean;
  onDismiss: () => void;
  knowledgePackMetadata?: {
    domain?: string;
    role?: string;
  };
}

const KnowledgeIntroBox: React.FC<KnowledgeIntroBoxProps> = ({
  isVisible,
  hasNewKnowledge,
  onDismiss,
  knowledgePackMetadata,
}) => {
  if (!isVisible) return null;

  const isSuccess = hasNewKnowledge;
  const hasMetadata = knowledgePackMetadata?.domain && knowledgePackMetadata?.role;
  const title = hasMetadata
    ? `Knowledge Pack for ${knowledgePackMetadata.domain}`
    : 'Knowledge Pack Domain Structure';

  return (
    <div
      className={`mb-6 mx-4 p-4 rounded-lg border border-dashed transition-all duration-300 ${
        isSuccess ? 'bg-green-50 border-green-200' : 'bg-white border-gray-200'
      }`}
    >
      <div className="flex gap-4 justify-between items-start">
        <div className="flex flex-1 gap-3">
          {/* Icon */}
          <div
            className={`flex justify-center items-center flex-shrink-0 w-8 h-8 rounded-full ${
              isSuccess ? 'bg-green-600' : 'bg-gray-600'
            }`}
          >
            {isSuccess ? (
              <ThumbsUp width={20} height={20} strokeWidth={2} className="text-white" />
            ) : (
              <LightBulb width={20} height={20} strokeWidth={2} className="text-white" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1">
            <h3
              className={`text-md font-semibold mb-2 ${isSuccess ? 'text-green-800' : 'text-gray-800'}`}
            >
              {isSuccess ? 'Nice! You have added a new knowledge topic.' : title}
            </h3>
            <p className={`text-sm ${isSuccess ? 'text-green-700' : 'text-gray-700'}`}>
              {isSuccess
                ? 'Keep going to build your knowledge pack.'
                : 'Each node represents a knowledge topic. Chat with Dana to expand and refine your knowledge pack.'}
            </p>
          </div>
        </div>

        {/* Dismiss button */}
        <button
          onClick={onDismiss}
          className={`p-1 rounded-full transition-colors ${
            isSuccess
              ? 'text-green-600 hover:text-green-700'
              : 'text-gray-600 hover:bg-gray-100 hover:text-gray-700'
          }`}
        >
          <Xmark width={16} height={16} />
        </button>
      </div>
    </div>
  );
};

// Static empty status data (shared across all instances to prevent re-renders)
const EMPTY_STATUS_DATA: KnowledgeStatusResponse = { topics: [] };

const DomainKnowledgeTree: React.FC<DomainKnowledgeTreeProps> = ({
  knowledgePackId,
  knowledgePackMetadata,
}) => {
  // Use knowledge pack store
  const {
    domainKnowledge: domainTree,
    isLoadingTree: initialLoading,
    treeError: storeError,
    knowledgeStatus: statusData,
    fetchKnowledgeStatus,
    createdKnowledgePack,
    setIsGeneratingKnowledge,
    updateNodeStatus,
  } = useKnowledgePackStore();

  const generatingNodes = new Set<string>();

  // Background task status state
  const [backgroundTaskStatus, setBackgroundTaskStatus] = useState<BackgroundTaskResponse | null>(
    null,
  );

  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [loading] = useState(false); // Keep for local loading states if needed
  const [error, setError] = useState<string | null>(null);

  // Update error when store error changes
  useEffect(() => {
    setError(storeError);
  }, [storeError]);

  // Store fetchKnowledgeStatus in ref to avoid dependency issues and infinite loops
  const fetchKnowledgeStatusRef = useRef(fetchKnowledgeStatus);
  useEffect(() => {
    fetchKnowledgeStatusRef.current = fetchKnowledgeStatus;
  }, [fetchKnowledgeStatus]);

  // Fetch knowledge status when component mounts or knowledgePackId changes
  // Use ref to prevent multiple calls and avoid infinite loops
  const hasInitializedStatusRef = useRef(false);
  const currentKpIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!knowledgePackId) {
      // Reset refs when no KP
      hasInitializedStatusRef.current = false;
      currentKpIdRef.current = null;
      return;
    }

    const kpId = typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : knowledgePackId;

    // Only fetch if KP ID changed or not initialized yet
    if (currentKpIdRef.current !== kpId || !hasInitializedStatusRef.current) {
      console.log('🎯 Fetching knowledge status (initial or kpId changed):', kpId);
      currentKpIdRef.current = kpId;
      hasInitializedStatusRef.current = true;
      fetchKnowledgeStatusRef.current(kpId); // Use ref to avoid re-triggering effect
    } else {
      console.log('⏭️ Skipping knowledge status fetch (already fetched for this KP):', kpId);
    }
  }, [knowledgePackId]); // Only depend on knowledgePackId

  // Expose refresh function globally for chat sidebar and other components to call
  useEffect(() => {
    if (knowledgePackId) {
      const kpId =
        typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : knowledgePackId;
      (window as any).refreshKnowledgePackStatus = () =>
        fetchKnowledgeStatusRef.current(kpId, true);
    }

    return () => {
      if ((window as any).refreshKnowledgePackStatus) {
        delete (window as any).refreshKnowledgePackStatus;
      }
    };
  }, [knowledgePackId]); // Only depend on knowledgePackId

  const isCheckingTaskRef = useRef(false);

  // Stable function to check task status - no dependencies to avoid loops
  const checkBackgroundTaskStatus = useCallback(async (taskId: number, kpId: number) => {
    if (isCheckingTaskRef.current) {
      console.log('⏭️ Skipping task check (already checking)');
      return;
    }

    isCheckingTaskRef.current = true;
    try {
      console.log('🔍 Checking background task status once:', { kpId, taskId });
      const taskStatus = await apiService.getGenerationStatus(kpId, taskId);
      console.log('✅ Task status loaded:', taskStatus);
      setBackgroundTaskStatus(taskStatus);

      // Update generation flag based on task status
      if (taskStatus.status === 'completed') {
        console.log('🔄 Task completed, refreshing knowledge status once...');
        await fetchKnowledgeStatusRef.current(kpId, true);
        // Reset generation flag when completed
        setIsGeneratingKnowledge(false);
      } else if (taskStatus.status === 'failed') {
        console.log('❌ Task failed');
        toast.error(taskStatus.error || 'Knowledge generation failed');
        // Reset generation flag when failed
        setIsGeneratingKnowledge(false);
      } else if (taskStatus.status === 'running' || taskStatus.status === 'pending') {
        console.log('ℹ️ Task is running/pending, setting generation flag');
        // Set generation flag if task is still running
        setIsGeneratingKnowledge(true);
      } else {
        console.log('ℹ️ Task status:', taskStatus.status);
      }
    } catch (error) {
      console.error('❌ Failed to check background task status:', error);
      setBackgroundTaskStatus(null);
    } finally {
      isCheckingTaskRef.current = false;
    }
  }, []); // No dependencies - stable function

  // Get generation_task_id from store
  const generationTaskId = createdKnowledgePack?.generation_task_id;

  // Debug log for generation task ID
  useEffect(() => {
    console.log('🔍 Generation Task ID from store:', {
      generationTaskId,
      createdKnowledgePack,
      status: createdKnowledgePack?.status,
    });
  }, [generationTaskId, createdKnowledgePack]);

  // Check background task status once when opening KP (if task exists)
  const hasCheckedTaskRef = useRef(false);
  const lastCheckedTaskIdRef = useRef<number | null>(null);

  useEffect(() => {
    if (!generationTaskId || !knowledgePackId) {
      console.log('⏭️ No task to check');
      setBackgroundTaskStatus(null);
      hasCheckedTaskRef.current = false;
      lastCheckedTaskIdRef.current = null;
      // Reset generation flag if no task exists
      setIsGeneratingKnowledge(false);
      return;
    }

    const kpId = typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : knowledgePackId;

    // Only check once per task
    if (lastCheckedTaskIdRef.current === generationTaskId && hasCheckedTaskRef.current) {
      console.log('⏭️ Task status already checked for this task:', generationTaskId);
      return;
    }

    console.log('🔍 Checking background task status once:', generationTaskId);
    hasCheckedTaskRef.current = true;
    lastCheckedTaskIdRef.current = generationTaskId;
    checkBackgroundTaskStatus(generationTaskId, kpId);
  }, [generationTaskId, knowledgePackId]); // Stable function, no need to depend on it
  // const [generating, setGenerating] = useState(false);
  // const [, setGenerateMsg] = useState<string | null>(null);
  const [topicStatus] = useState<{ [id: string]: string }>({});
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarTopicPath, setSidebarTopicPath] = useState<string>('');
  const [sidebarContent, setSidebarContent] = useState<any>(null);
  const [sidebarLoading, setSidebarLoading] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);
  // New UX improvement states
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isTransitioning, setIsTransitioning] = useState(false);

  // Knowledge intro box states
  const [showKnowledgeIntro, setShowKnowledgeIntro] = useState<boolean>(true);
  const [hasNewKnowledge, setHasNewKnowledge] = useState<boolean>(false);
  const [previousKnowledgeCount, setPreviousKnowledgeCount] = useState<number>(0);

  // Delete confirmation states
  const [showDeleteDialog, setShowDeleteDialog] = useState<boolean>(false);
  const [nodeToDelete, setNodeToDelete] = useState<{
    id: string;
    path: string;
    label: string;
  } | null>(null);
  const [isDeleting, setIsDeleting] = useState<boolean>(false);

  // Generate knowledge state
  const [isGenerating, setIsGenerating] = useState<boolean>(false);

  // Initial state management - always show intro box
  useEffect(() => {
    // Always show intro box when component mounts or knowledge pack changes
    setShowKnowledgeIntro(true);
  }, [knowledgePackId]);

  const containerRef = useRef<HTMLDivElement>(null);
  const expandedNodesRef = useRef<Set<string>>(new Set());
  const pendingExpandedNodesRef = useRef<Set<string> | null>(null); // For pending expansion state changes
  const previousKnowledgePackIdRef = useRef<string | number | undefined>(undefined);
  const reactFlowInstanceRef = useRef<ReactFlowInstance | null>(null);
  const nodesRef = useRef<FlowNode[]>([]);
  const previousEdgesRef = useRef<Set<string>>(new Set());
  
  // Store pending expansion state in window to persist across remounts
  // Key format: `pendingExpansion_${knowledgePackId}`
  const getPendingExpansionKey = useCallback(() => {
    const kpId = knowledgePackId ? String(knowledgePackId) : 'unknown';
    return `pendingExpansion_${kpId}`;
  }, [knowledgePackId]);

  // Refs to track timeouts for cleanup
  const timeoutRefs = useRef<Set<ReturnType<typeof setTimeout>>>(new Set());

  // Helper function to safely add timeout and track for cleanup
  const addTimeout = useCallback((callback: () => void, delay: number) => {
    const timeoutId = setTimeout(() => {
      callback();
      timeoutRefs.current.delete(timeoutId);
    }, delay);
    timeoutRefs.current.add(timeoutId);
    return timeoutId;
  }, []);

  // Cleanup all timeouts on unmount or KP change
  useEffect(() => {
    return () => {
      console.log('🧹 Cleaning up all timeouts');
      timeoutRefs.current.forEach((timeoutId) => clearTimeout(timeoutId));
      timeoutRefs.current.clear();
    };
  }, [knowledgePackId]);

  // Stabilize the WebSocket callback to prevent reconnections on re-renders
  const handleWebSocketStatusUpdate = useCallback((nodePath: string, status: string) => {
    console.log('🔄 [DomainKnowledgeTree] WebSocket status update:', { nodePath, status });
    updateNodeStatus(nodePath, status as KnowledgeTopicStatus['status']);
    
    // Auto-expand the path to the updated node
    if (domainTree?.root) {
      const rootTopic = domainTree.root.topic;
      // nodePath format: "Parent - Child - Grandchild" (without root)
      // Split into parts and build full path with root
      const pathParts = nodePath.split(' - ').filter(part => part.trim() !== '');
      const fullPath = [rootTopic, ...pathParts];
      
      // Build node IDs for all parent levels
      const nodeIdsToExpand = new Set(expandedNodes);
      let currentPath = '';
      
      for (let i = 0; i < fullPath.length - 1; i++) { // -1 because we don't need to expand the leaf node itself
        if (i === 0) {
          currentPath = fullPath[i];
        } else {
          currentPath = currentPath + '/' + fullPath[i];
        }
        nodeIdsToExpand.add(currentPath);
      }
      
      // Update expanded nodes if we added any new ones
      if (nodeIdsToExpand.size > expandedNodes.size) {
        console.log('🔓 [DomainKnowledgeTree] Auto-expanding path to updated node:', {
          nodePath,
          expandedNodeIds: Array.from(nodeIdsToExpand),
        });
        setExpandedNodes(nodeIdsToExpand);
        // Note: Tree will regenerate automatically when statusData changes (from updateNodeStatus above)
      }
    }
  }, [updateNodeStatus, domainTree, expandedNodes]);

  // Set up WebSocket connection for real-time status updates
  useKnowledgePackWebSocket(
    knowledgePackId ? (typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : knowledgePackId) : null,
    handleWebSocketStatusUpdate
  );

  // Function to center the view after nodes are expanded - optimized for performance
  const centerView = useCallback(() => {
    if (reactFlowInstanceRef.current && nodesRef.current.length > 0) {
      // Use setTimeout to ensure the nodes are rendered before centering
      addTimeout(() => {
        const instance = reactFlowInstanceRef.current;
        if (!instance) return;

        // Use ReactFlow's fitView method with consistent zoom limits
        instance.fitView({
          padding: 0.2,
          includeHiddenNodes: false,
          minZoom: 0.1,
          maxZoom: 2,
          duration: 300, // Shorter duration for better performance
        });
      }, 100);
    }
  }, [addTimeout]);

  // Function to handle smooth transitions when expanding/collapsing
  const handleSmoothTransition = useCallback(
    (newNodes: FlowNode[], newEdges: Edge[]) => {
      setIsTransitioning(true);

      // Add a small delay to allow the transition to start
      addTimeout(() => {
        setNodes(newNodes);
        setEdges(newEdges);

        // Center view and end transition after animation completes
        addTimeout(() => {
          centerView();
          setIsTransitioning(false);
        }, 300);
      }, 50);
    },
    [centerView, addTimeout],
  );

  // Keep nodes ref in sync
  useEffect(() => {
    nodesRef.current = nodes;
  }, [nodes]);

  // Center view when nodes change
  useEffect(() => {
    if (nodes.length > 0) {
      centerView();
    }
  }, [nodes, centerView]);

  // Handle edge animations for new edges
  useEffect(() => {
    if (edges.length > 0) {
      const currentEdgeIds = new Set(edges.map((edge) => edge.id));
      const previousEdgeIds = previousEdgesRef.current;

      // Find new edges
      const newEdgeIds = [...currentEdgeIds].filter((id) => !previousEdgeIds.has(id));

      if (newEdgeIds.length > 0) {
        // Add animation to new edges with a delay to ensure ReactFlow has rendered them
        addTimeout(() => {
          newEdgeIds.forEach((edgeId) => {
            // Simplified edge detection - look for the edge element directly
            let edgeElement: Element | null = null;

            // Strategy 1: Look for edge by data-id attribute in the edges container
            const edgeContainer = document.querySelector('.react-flow__edges');
            if (edgeContainer) {
              // ReactFlow renders edges as SVG g elements with data-id
              edgeElement = edgeContainer.querySelector(`g[data-id="${edgeId}"]`);
            }

            // Strategy 2: If not found, try looking for any element with the edge ID
            if (!edgeElement) {
              edgeElement = document.querySelector(`[data-id="${edgeId}"]`);
            }

            // Strategy 3: Look for edge by checking all g elements in the edges container
            if (!edgeElement && edgeContainer) {
              const allEdgeElements = edgeContainer.querySelectorAll('g');
              for (const edgeEl of allEdgeElements) {
                const id = edgeEl.getAttribute('data-id');
                if (id === edgeId) {
                  edgeElement = edgeEl;
                  break;
                }
              }
            }

            // If edge element is found, add animation
            if (edgeElement) {
              // Add data attribute for animation
              edgeElement.setAttribute('data-edge-new', 'true');

              // Also add data attribute to the edge path if it exists
              const edgePath = edgeElement.querySelector('.react-flow__edge-path') as Element;
              if (edgePath) {
                edgePath.setAttribute('data-edge-new', 'true');
              }

              // Remove animation attributes after animation completes
              addTimeout(() => {
                edgeElement?.removeAttribute('data-edge-new');
                if (edgePath) {
                  edgePath.removeAttribute('data-edge-new');
                }
              }, 800); // Match the animation duration
            } else {
              // Retry mechanism - if edge not found initially, try again after a short delay
              addTimeout(() => {
                const retryEdgeElement =
                  document.querySelector(`[data-id="${edgeId}"]`) ||
                  document
                    .querySelector('.react-flow__edges')
                    ?.querySelector(`g[data-id="${edgeId}"]`);

                if (retryEdgeElement) {
                  retryEdgeElement.setAttribute('data-edge-new', 'true');

                  const retryEdgePath = retryEdgeElement.querySelector(
                    '.react-flow__edge-path',
                  ) as Element;
                  if (retryEdgePath) {
                    retryEdgePath.setAttribute('data-edge-new', 'true');
                  }

                  addTimeout(() => {
                    retryEdgeElement.removeAttribute('data-edge-new');
                    if (retryEdgePath) {
                      retryEdgePath.removeAttribute('data-edge-new');
                    }
                  }, 800);
                }
              }, 200);
            }
          });
        }, 150); // Slightly increased delay for better reliability
      }

      // Update previous edges
      previousEdgesRef.current = currentEdgeIds;
    }
  }, [edges, addTimeout]);

  // Keep the ref in sync with the state
  useEffect(() => {
    expandedNodesRef.current = expandedNodes;
  }, [expandedNodes]);

  // Reset expansion state only when switching to a different knowledge pack
  useEffect(() => {
    if (knowledgePackId && knowledgePackId !== previousKnowledgePackIdRef.current) {
      setExpandedNodes(new Set());
      expandedNodesRef.current = new Set();
      previousKnowledgePackIdRef.current = knowledgePackId;
    } else if (knowledgePackId) {
      previousKnowledgePackIdRef.current = knowledgePackId;
    }
  }, [knowledgePackId]);

  const nodeTypes = {
    custom: (nodeProps: any) => (
      <CustomNode
        {...nodeProps}
        isSelected={selectedNodeId === nodeProps.id}
        isGenerating={generatingNodes.has(nodeProps.data.label)}
        onNodeClick={(event: React.MouseEvent) => onNodeClick(event, nodeProps)}
        onDeleteNode={handleDeleteNode}
      >
        {renderStatusIcon(getNodeStatus(nodeProps))}
      </CustomNode>
    ),
  };

  // Helper function to check if a node matches search query
  const matchesSearch = (nodeLabel: string, searchQuery: string): boolean => {
    if (!searchQuery.trim()) return true;
    return nodeLabel.toLowerCase().includes(searchQuery.toLowerCase().trim());
  };

  // Helper function to check if any child matches search
  const hasMatchingDescendant = (node: DomainNode, searchQuery: string): boolean => {
    if (matchesSearch(node.topic, searchQuery)) return true;
    if (node.children) {
      return node.children.some((child) => hasMatchingDescendant(child, searchQuery));
    }
    return false;
  };

  // Convert domain knowledge tree to flow nodes and edges
  const convertDomainToFlow = (
    domainTree: DomainKnowledgeResponse,
    statusData?: KnowledgeStatusResponse,
    expandedNodeIds?: Set<string>,
    searchQuery?: string,
  ): { nodes: FlowNode[]; edges: Edge[] } => {
    const nodes: FlowNode[] = [];
    const edges: Edge[] = [];

    // Helper function to get knowledge status for a node path
    const getKnowledgeStatusForPath = (nodePath: string): KnowledgeTopicStatus | null => {
      if (!statusData || !statusData.topics) return null;

      // Debug logging
      console.log('🔍 Looking for knowledge status for nodePath:', nodePath);
      console.log(
        '📋 Available status topics:',
        statusData.topics.map((t) => ({ path: t.path, status: t.status })),
      );

      // Find the status entry that matches this node's path
      // First try exact match
      const match = statusData.topics.find((topic) => topic.path === nodePath);
      if (match) {
        console.log('✅ Found exact match for:', nodePath);
        return match;
      }

      // If no exact match, try to find a partial match for leaf nodes
      // This handles cases where the domain tree structure differs from knowledge status paths
      const pathParts = nodePath.split(' - ');

      // Try different matching strategies
      for (const topic of statusData.topics) {
        const topicParts = topic.path.split(' - ');

        // Strategy 1: Check if this could be a match by comparing the last part (leaf node name)
        if (pathParts.length > 0 && topicParts.length > 0) {
          const lastPathPart = pathParts[pathParts.length - 1];
          const lastTopicPart = topicParts[topicParts.length - 1];

          // If the leaf node names match and the topic path is a subset of the node path
          if (
            lastPathPart === lastTopicPart &&
            topicParts.every((part) => pathParts.includes(part))
          ) {
            console.log('✅ Found match with Strategy 1 for:', nodePath, '->', topic.path);
            return topic;
          }
        }

        // Strategy 2: Check if the node path is a subset of the topic path
        // This handles cases where the UI shows a shorter path but the status has a longer path
        if (pathParts.length > 0 && topicParts.length >= pathParts.length) {
          const nodePathString = pathParts.join(' - ');
          if (topic.path.includes(nodePathString)) {
            console.log('✅ Found match with Strategy 2 for:', nodePath, '->', topic.path);
            return topic;
          }
        }

        // Strategy 3: Check if the topic path is a subset of the node path
        // This handles cases where the UI shows a longer path but the status has a shorter path
        if (topicParts.length > 0 && pathParts.length >= topicParts.length) {
          const topicPathString = topicParts.join(' - ');
          if (nodePath.includes(topicPathString)) {
            console.log('✅ Found match with Strategy 3 for:', nodePath, '->', topic.path);
            return topic;
          }
        }

        // Strategy 4: Check if any part of the node path matches any part of the topic path
        // This is a fallback for complex cases
        const nodePathLower = nodePath.toLowerCase();
        const topicPathLower = topic.path.toLowerCase();
        if (nodePathLower === topicPathLower) {
          console.log('✅ Found match with Strategy 4 for:', nodePath, '->', topic.path);
          return topic;
        }
      }

      console.log('❌ No match found for:', nodePath);
      return null;
    };

    const traverse = (
      domainNode: DomainNode,
      parentId?: string,
      pathParts: string[] = [],
      depth: number = 0,
    ) => {
      const currentPath = [...pathParts, domainNode.topic];
      const nodeId = currentPath.join('/'); // Unique path-based ID

      // Create nodePath excluding the root level for knowledge status matching
      // For root node, use just the topic name; for others, exclude the root from the path
      const nodePathParts = depth === 0 ? [domainNode.topic] : currentPath.slice(1);
      const nodePath = nodePathParts.join(' - '); // Path format used in knowledge status

      // Get knowledge status for this node (only leaf nodes will have status)
      const isLeafNode = !domainNode.children || domainNode.children.length === 0;
      const hasChildren = domainNode.children && domainNode.children.length > 0;
      const knowledgeStatusInfo = isLeafNode ? getKnowledgeStatusForPath(nodePath) : null;

      // Only show the node if:
      // 1. It's the root node (depth 0)
      // 2. Its parent is expanded
      // 3. We don't have expansion state yet (show all - fallback behavior)
      // 4. If there's a search query, the node or its descendants match
      const shouldShowNode = (() => {
        const baseCondition =
          depth === 0 || !parentId || !expandedNodeIds || expandedNodeIds.has(parentId);

        if (!searchQuery || !searchQuery.trim()) {
          return baseCondition;
        }

        // For search: show if current node matches OR has matching descendants
        const nodeMatches = matchesSearch(domainNode.topic, searchQuery);
        const hasMatchingChild = hasMatchingDescendant(domainNode, searchQuery);

        return baseCondition && (nodeMatches || hasMatchingChild);
      })();

      if (shouldShowNode) {
        // Create flow node with knowledge status information
        const flowNode = {
          id: nodeId,
          type: 'custom',
          data: {
            label: domainNode.topic,
            knowledgeStatus: knowledgeStatusInfo,
            isLeafNode,
            hasChildren,
            nodePath,
            isExpanded: expandedNodeIds?.has(nodeId) || false,
            isRootNode: depth === 0,
          },
          position: { x: 0, y: 0 }, // Will be set by dagre layout
        };

        nodes.push(flowNode);

        // Create edge from parent if exists
        if (parentId) {
          edges.push({
            id: `e${parentId}-${nodeId}`,
            source: parentId,
            target: nodeId,
            markerEnd: { type: MarkerType.ArrowClosed },
            type: 'default',
            style: {
              stroke: '#6b7280',
              strokeWidth: 1,
              transition: TRANSITION_ALL,
              opacity: 1, // Ensure opacity is set for animations
            },
            animated: false, // We'll handle animation with CSS
            data: {
              // Add data for animation tracking
              isNew: true,
            },
          });
        }
      }

      // Recursively process children if node should be shown
      if (shouldShowNode && domainNode.children) {
        domainNode.children.forEach((child) => traverse(child, nodeId, currentPath, depth + 1));
      }

      return nodeId;
    };

    if (domainTree.root) {
      traverse(domainTree.root);
    }

    return { nodes, edges };
  };

  // Initialize with default nodes if no knowledge pack ID
  useEffect(() => {
    if (!knowledgePackId) {
      // Show default nodes if no knowledge pack ID
      const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
      setNodes(layouted);
      setEdges(initialEdges);
      return;
    }
  }, [knowledgePackId]);

  // Process domain knowledge and status data from store
  useEffect(() => {
    console.log('🔄 [TREE-REGEN] domainTree useEffect triggered');
    console.log('📊 [TREE-REGEN] Current expandedNodesRef:', Array.from(expandedNodesRef.current));
    console.log('📊 [TREE-REGEN] Current expandedNodes state:', Array.from(expandedNodes));
    console.log('📊 [TREE-REGEN] Pending expansion state:', pendingExpandedNodesRef.current ? Array.from(pendingExpandedNodesRef.current) : 'none');
    
    const effectiveStatusData = statusData || EMPTY_STATUS_DATA;

    if (!domainTree) {
      if (!knowledgePackId) {
        // Show default nodes if no knowledge pack ID
        const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
        setNodes(layouted);
        setEdges(initialEdges);
      }
      console.log('⏭️ [TREE-REGEN] No domainTree, returning early');
      return;
    }

    if (domainTree.message) {
      // No domain knowledge found, show empty state
      setNodes([]);
      setEdges([]);
      setError(domainTree.message);
      console.log('⚠️ [TREE-REGEN] Domain tree has error message:', domainTree.message);
    } else if (domainTree.root) {
      // Check for pending expansion state changes (e.g., from node deletion)
      // Check both ref and window storage (for persistence across remounts)
      let currentExpanded: Set<string>;
      
      // First check ref (for same render cycle)
      let pendingState: Set<string> | null = pendingExpandedNodesRef.current;
      
      // If ref is null, check window storage (for persistence across remounts)
      if (!pendingState && knowledgePackId) {
        const storedPending = (window as any)[getPendingExpansionKey()];
        if (storedPending && Array.isArray(storedPending)) {
          pendingState = new Set(storedPending);
          console.log('💾 [TREE-REGEN] Restored pending expansion state from window storage:', Array.from(pendingState));
          // Clear window storage
          delete (window as any)[getPendingExpansionKey()];
        }
      }
      
      if (pendingState !== null) {
        console.log('🔓 [TREE-REGEN] Applying pending expansion state:', Array.from(pendingState));
        currentExpanded = pendingState;
        expandedNodesRef.current = pendingState;
        setExpandedNodes(pendingState);
        pendingExpandedNodesRef.current = null; // Clear pending state
        // Persist current expansion state in window storage for subsequent effects
        if (knowledgePackId) {
          (window as any)[`currentExpansion_${knowledgePackId}`] = Array.from(pendingState);
          console.log('💾 [TREE-REGEN] Persisted current expansion state to window storage');
        }
      } else if (expandedNodesRef.current.size > 0) {
        console.log('🌳 [TREE-REGEN] Using existing expansion state from ref');
        currentExpanded = expandedNodesRef.current;
        // Also persist it in case of remount
        if (knowledgePackId) {
          (window as any)[`currentExpansion_${knowledgePackId}`] = Array.from(currentExpanded);
        }
      } else {
        // Check window storage for current expansion state (for remounts)
        if (knowledgePackId) {
          const storedCurrent = (window as any)[`currentExpansion_${knowledgePackId}`];
          if (storedCurrent && Array.isArray(storedCurrent) && storedCurrent.length > 0) {
            currentExpanded = new Set(storedCurrent);
            expandedNodesRef.current = currentExpanded;
            setExpandedNodes(currentExpanded);
            console.log('💾 [TREE-REGEN] Restored current expansion state from window storage:', Array.from(currentExpanded));
          } else {
            console.log('🌱 [TREE-REGEN] Initializing with root node only');
            currentExpanded = new Set([domainTree.root.topic]);
            expandedNodesRef.current = currentExpanded;
            setExpandedNodes(currentExpanded);
          }
        } else {
          console.log('🌱 [TREE-REGEN] Initializing with root node only');
          currentExpanded = new Set([domainTree.root.topic]);
          expandedNodesRef.current = currentExpanded;
          setExpandedNodes(currentExpanded);
        }
      }

      console.log('🌳 [TREE-REGEN] Final expansion state to use:', Array.from(currentExpanded));

      // Convert domain knowledge to flow format (now with status information)
      const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
        domainTree,
        effectiveStatusData,
        currentExpanded,
        searchQuery,
      );
      console.log('✨ [TREE-REGEN] Generated', flowNodes.length, 'nodes with IDs:', flowNodes.map(n => n.id));
      
      const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
      setNodes(layoutedNodes);
      setEdges(flowEdges);
      setError(null);
      console.log('✅ [TREE-REGEN] Tree regeneration complete');
    }
  }, [domainTree, statusData, searchQuery]);

  // Real-time status updates - React to knowledgeStatus changes
  // Note: This is for agents only, not for knowledge packs
  useEffect(() => {
    const effectiveStatusData = statusData || EMPTY_STATUS_DATA;

    // Skip this effect for knowledge packs (they don't have real-time status updates)
    if (!statusData || statusData === EMPTY_STATUS_DATA) return;

    if (!domainTree || !domainTree.root) return;

    console.log('[DomainKnowledgeTree] Status data updated, refreshing nodes');
    console.log('📊 [STATUS-UPDATE] Current expandedNodesRef:', Array.from(expandedNodesRef.current));
    console.log('📊 [STATUS-UPDATE] Pending expansion state:', pendingExpandedNodesRef.current ? Array.from(pendingExpandedNodesRef.current) : 'none');

    // Preserve current expansion state - check both ref and window storage (same as main effect)
    let currentExpanded: Set<string>;
    
    // First check ref (for same render cycle)
    let pendingState: Set<string> | null = pendingExpandedNodesRef.current;
    
    // If ref is null, check window storage (for persistence across remounts)
    if (!pendingState && knowledgePackId) {
      const storedPending = (window as any)[getPendingExpansionKey()];
      if (storedPending && Array.isArray(storedPending)) {
        pendingState = new Set(storedPending);
        console.log('💾 [STATUS-UPDATE] Restored pending expansion state from window storage:', Array.from(pendingState));
        // Clear window storage
        delete (window as any)[getPendingExpansionKey()];
      }
    }
    
    if (pendingState !== null) {
      console.log('🔓 [STATUS-UPDATE] Applying pending expansion state:', Array.from(pendingState));
      currentExpanded = pendingState;
      expandedNodesRef.current = pendingState;
      setExpandedNodes(pendingState);
      pendingExpandedNodesRef.current = null; // Clear pending state
      // Persist current expansion state in window storage for subsequent effects
      if (knowledgePackId) {
        (window as any)[`currentExpansion_${knowledgePackId}`] = Array.from(pendingState);
        console.log('💾 [STATUS-UPDATE] Persisted current expansion state to window storage');
      }
    } else if (expandedNodesRef.current.size > 0) {
      console.log('🌳 [STATUS-UPDATE] Using existing expansion state from ref');
      currentExpanded = expandedNodesRef.current;
      // Also persist it in case of remount
      if (knowledgePackId) {
        (window as any)[`currentExpansion_${knowledgePackId}`] = Array.from(currentExpanded);
      }
    } else {
      // Check window storage for current expansion state (for remounts)
      if (knowledgePackId) {
        const storedCurrent = (window as any)[`currentExpansion_${knowledgePackId}`];
        if (storedCurrent && Array.isArray(storedCurrent) && storedCurrent.length > 0) {
          currentExpanded = new Set(storedCurrent);
          expandedNodesRef.current = currentExpanded;
          setExpandedNodes(currentExpanded);
          console.log('💾 [STATUS-UPDATE] Restored current expansion state from window storage:', Array.from(currentExpanded));
        } else {
          console.log('🌱 [STATUS-UPDATE] Initializing with root node only');
          currentExpanded = new Set([domainTree.root.topic]);
          expandedNodesRef.current = currentExpanded;
          setExpandedNodes(currentExpanded);
        }
      } else {
        console.log('🌱 [STATUS-UPDATE] Initializing with root node only');
        currentExpanded = new Set([domainTree.root.topic]);
        expandedNodesRef.current = currentExpanded;
        setExpandedNodes(currentExpanded);
      }
    }

    console.log('🌳 [STATUS-UPDATE] Final expansion state to use:', Array.from(currentExpanded));

    // Convert domain knowledge to flow format with updated status
    const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
      domainTree,
      effectiveStatusData,
      currentExpanded,
      searchQuery,
    );
    console.log('✨ [STATUS-UPDATE] Generated', flowNodes.length, 'nodes with IDs:', flowNodes.map(n => n.id));
    const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');

    // Knowledge detection logic - only detect transitions if intro box is visible
    const currentKnowledgeCount = flowNodes.length;
    if (showKnowledgeIntro) {
      if (previousKnowledgeCount > 0 && currentKnowledgeCount > previousKnowledgeCount) {
        // New knowledge topic detected - show celebration transition
        setHasNewKnowledge(true);
      } else if (previousKnowledgeCount === 0 && currentKnowledgeCount >= 0) {
        // Initial state when intro first becomes visible
        setHasNewKnowledge(false);
      }
    }
    setPreviousKnowledgeCount(currentKnowledgeCount);

    setNodes(layoutedNodes);
    setEdges(flowEdges);
  }, [statusData, showKnowledgeIntro]);

  // Hide popup when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setSelectedNodeId(null);
      }
    }
    if (selectedNodeId) {
      document.addEventListener('mousedown', handleClickOutside);
    } else {
      document.removeEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [selectedNodeId]);

  // Handle node click - toggle expansion for parent nodes, show sidebar for leaf nodes
  const onNodeClick = async (event: React.MouseEvent, node: FlowNode) => {
    // Prevent the click from triggering focus events that might interfere
    event.stopPropagation();

    const nodeData = node.data;

    // Set the selected node for highlighting
    setSelectedNodeId(node.id);

    // If it's a leaf node, show the knowledge sidebar
    if (nodeData.isLeafNode) {
      const topicPath = nodeData.nodePath;

      // For knowledge packs, always attempt to fetch content
      // The knowledge.json files exist regardless of status data
      // Status data loads asynchronously and may not be available on first click
      const shouldFetchContent = true;

      console.log('🔍 Node click - shouldFetchContent decision:', {
        nodePath: topicPath,
        status: nodeData.knowledgeStatus?.status,
        shouldFetchContent,
        hasStatusData: !!statusData,
        note: 'Always fetching for knowledge packs',
      });

      if (shouldFetchContent) {
        // Open sidebar and fetch content
        setSidebarOpen(true);
        setSidebarTopicPath(topicPath);
        setSidebarLoading(true);
        setSidebarError(null);
        setSidebarContent(null);

        try {
          // Convert topicPath (string) to path_parts (array)
          // topicPath format: "Parent - Child - Grandchild" (without root)
          let pathParts: string[] = topicPath
            .split(' - ')
            .filter((part: string) => part.trim() !== '');

          // Add root node to path if not already present (needed for API)
          // The nodePath excludes the root, but the API expects the full path including root
          if (domainTree && domainTree.root) {
            const rootTopic = domainTree.root.topic;
            if (pathParts[0] !== rootTopic) {
              pathParts = [rootTopic, ...pathParts];
            }
          }

          console.log('📋 Fetching knowledge preview with path_parts:', pathParts);

          const response = await apiService.getKnowledgeNodePreview(
            parseInt(knowledgePackId!.toString()),
            pathParts,
          );

          console.log('📦 Knowledge preview response:', {
            success: response.success,
            hasData: !!response.data,
            hasContent: !!response.content,
            dataKeys: response.data ? Object.keys(response.data) : [],
            hasKnowledges: response.data && 'knowledges' in response.data,
          });

          if (response.success) {
            // Extract data from the response - the API returns { success, data: {...} }
            const content = response.data || response.content;
            console.log('✅ Setting sidebar content:', {
              hasKnowledges: content && 'knowledges' in content,
              knowledgesCount: content?.knowledges?.length,
              totalQuestions: content?.total_questions,
            });
            setSidebarContent(content);
          } else {
            setSidebarError(response.message || 'Failed to load knowledge content');
          }
        } catch (error: any) {
          console.error('Error fetching knowledge content:', error);
          setSidebarError(error.message || 'Failed to load knowledge content');
        } finally {
          setSidebarLoading(false);
        }
      } else {
        // Show drawer with message and CTA for nodes without knowledge content
        const status = nodeData.knowledgeStatus?.status || 'pending';
        let title = '';
        let description = '';
        let showGenerateButton = false;

        switch (status) {
          case 'pending':
            title = 'Knowledge Not Generated Yet';
            description = `Content for "${nodeData.label}" will be shown here once knowledge generation is complete. Click the button below to start generating knowledge for this topic.`;
            showGenerateButton = true;
            break;
          case 'in_progress':
            title = 'Generating Knowledge';
            description = `Knowledge for "${nodeData.label}" is currently being generated. This process may take several minutes. Please wait while we analyze and extract insights from your uploaded documents.`;
            showGenerateButton = false;
            break;
          case 'failed':
            title = 'Knowledge Generation Failed';
            description = `We encountered an issue while generating knowledge for "${nodeData.label}". Please try regenerating the knowledge. If the problem persists, check your uploaded documents and try again.`;
            showGenerateButton = true;
            break;
          default:
            title = 'Knowledge Not Available';
            description = `Knowledge for "${nodeData.label}" is not available yet. Click the button below to start the knowledge generation process.`;
            showGenerateButton = true;
        }

        // Open sidebar with message and CTA
        setSidebarOpen(true);
        setSidebarTopicPath(topicPath);
        setSidebarLoading(false);
        setSidebarError(null);
        setSidebarContent({
          message: '', // Keep for backwards compatibility
          title,
          description,
          showGenerateButton,
          topicPath,
          nodeLabel: nodeData.label,
          status,
        });
      }

      return;
    }

    // If the node has children, toggle its expansion
    if (nodeData.hasChildren) {
      const newExpandedNodes = new Set(expandedNodes);

      if (expandedNodes.has(node.id)) {
        // Collapse: remove this node and all its descendants from expanded set
        const removeDescendants = (nodeId: string) => {
          newExpandedNodes.delete(nodeId);
          // Find and remove all descendant nodes
          nodes.forEach((n) => {
            if (n.id !== nodeId && n.id.startsWith(nodeId + '/')) {
              removeDescendants(n.id);
            }
          });
        };
        removeDescendants(node.id);
      } else {
        // Expand: add this node to expanded set
        newExpandedNodes.add(node.id);
      }

      setExpandedNodes(newExpandedNodes);

      // Regenerate the flow with new expansion state
      if (domainTree) {
        const effectiveStatusData = statusData || EMPTY_STATUS_DATA;
        const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
          domainTree,
          effectiveStatusData,
          newExpandedNodes,
          searchQuery,
        );
        const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');

        // Use smooth transition function
        handleSmoothTransition(layoutedNodes, flowEdges);
      }
    }
  };

  // Optionally, handle pane click to clear selection
  const onPaneClick = () => {
    // Only clear selection if sidebar is not open
    if (!sidebarOpen) {
      setSelectedNodeId(null);
    }
  };

  // Handle search query changes
  const handleSearchChange = (query: string) => {
    setSearchQuery(query);

    // Auto-expand nodes when searching to show results
    if (query.trim() && domainTree) {
      const autoExpandForSearch = new Set<string>();

      // Expand all parent nodes that contain matching children
      const expandParentsWithMatches = (
        node: DomainNode,
        pathParts: string[] = [],
        depth: number = 0,
      ) => {
        const currentPath = [...pathParts, node.topic];
        const nodeId = currentPath.join('/');

        if (hasMatchingDescendant(node, query)) {
          autoExpandForSearch.add(nodeId);
          if (node.children) {
            node.children.forEach((child) =>
              expandParentsWithMatches(child, currentPath, depth + 1),
            );
          }
        }
      };

      if (domainTree.root) {
        expandParentsWithMatches(domainTree.root);
        setExpandedNodes(new Set([...expandedNodes, ...autoExpandForSearch]));
      }
    }

    // Regenerate tree with search filter
    if (domainTree) {
      const effectiveStatusData = statusData || EMPTY_STATUS_DATA;
      const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
        domainTree,
        effectiveStatusData,
        expandedNodesRef.current,
        query,
      );
      const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
      setNodes(layoutedNodes);
      setEdges(flowEdges);
    }
  };

  // Tree control functions
  const handleExpandAll = () => {
    if (!domainTree || !domainTree.root) return;

    const allNodeIds = new Set<string>();

    const collectAllNodes = (node: DomainNode, pathParts: string[] = []) => {
      const currentPath = [...pathParts, node.topic];
      const nodeId = currentPath.join('/');
      allNodeIds.add(nodeId);

      if (node.children) {
        node.children.forEach((child) => collectAllNodes(child, currentPath));
      }
    };

    collectAllNodes(domainTree.root);
    setExpandedNodes(allNodeIds);

    // Regenerate tree
    const effectiveStatusData = statusData || EMPTY_STATUS_DATA;
    const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
      domainTree,
      effectiveStatusData,
      allNodeIds,
      searchQuery,
    );
    const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
    setNodes(layoutedNodes);
    setEdges(flowEdges);
  };

  const handleCollapseAll = () => {
    if (!domainTree || !domainTree.root) return;

    // Only keep root expanded
    const rootOnly = new Set([domainTree.root.topic]);
    setExpandedNodes(rootOnly);

    // Regenerate tree
    const effectiveStatusData = statusData || EMPTY_STATUS_DATA;
    const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
      domainTree,
      effectiveStatusData,
      rootOnly,
      searchQuery,
    );
    const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
    setNodes(layoutedNodes);
    setEdges(flowEdges);
  };

  // Handle intro box dismissal
  const handleDismissIntro = () => {
    // Hide intro for current session only (will show again on reload)
    setShowKnowledgeIntro(false);

    // Reset hasNewKnowledge state
    setHasNewKnowledge(false);
  };

  // Handle delete node request
  const handleDeleteNode = (nodeId: string, nodePath: string) => {
    // Find the node to get its label - try both by ID and by nodePath
    let node = nodes.find((n) => n.id === nodeId);
    if (!node) {
      // If not found by ID, try to find by nodePath in the data
      node = nodes.find((n) => n.data?.nodePath === nodePath);
    }

    if (node) {
      setNodeToDelete({
        id: nodeId,
        path: nodePath,
        label: node.data.label,
      });
      setShowDeleteDialog(true);
    }
  };

  // Confirm delete - Knowledge Pack node deletion
  const confirmDelete = async () => {
    if (!nodeToDelete || !knowledgePackId) return;

    setIsDeleting(true);
    try {
      // Parse the node path to get topic parts
      let topicParts = nodeToDelete.path.split(' - ');

      // Get the root node from knowledge pack metadata (domain)
      const rootNode = knowledgePackMetadata?.domain || 'General Purpose';

      // If the first part is not the root node, add it as the root
      if (topicParts[0] !== rootNode) {
        topicParts = [rootNode, ...topicParts];
      }

      console.log('🗑️ Deleting knowledge pack node with topic_parts:', topicParts);

      // Use knowledge pack specific delete endpoint
      const response = await apiService.deleteKnowledgePackNode(
        typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : knowledgePackId,
        topicParts,
      );

      console.log('📋 Delete response:', response);

      // Check for success
      if (response.success || response.message?.includes('deleted successfully')) {
        console.log('✅ [DELETE] Delete successful, closing dialog and refreshing tree');
        console.log('📊 [DELETE] BEFORE cleanup - expandedNodes:', Array.from(expandedNodes));
        console.log('📊 [DELETE] BEFORE cleanup - expandedNodesRef:', Array.from(expandedNodesRef.current));
        console.log('🗑️ [DELETE] Deleting node ID:', nodeToDelete.id, 'with path:', nodeToDelete.path);

        // CRITICAL: Find the actual node to get the correct ID format (uses '/' not ' - ')
        // The nodeToDelete.id might be in the wrong format if it fell back to nodePath
        let deletedNodeId = nodeToDelete.id;
        
        // Check if the ID is in the wrong format (contains ' - ' instead of '/')
        if (deletedNodeId.includes(' - ')) {
          // Convert nodePath format to node ID format
          // nodePath format: "Process Technician - Documentation & Regulatory Compliance - Managing Material Safety Data Sheets (MSDS)"
          // node ID format: "Manufacturing Operations/Process Technician/Documentation & Regulatory Compliance/Managing Material Safety Data Sheets (MSDS)"
          const pathParts = nodeToDelete.path.split(' - ');
          const fullPath = [rootNode, ...pathParts];
          deletedNodeId = fullPath.join('/');
          console.log('🔄 [DELETE] Converted nodePath to node ID format:', deletedNodeId);
        }
        
        // Also try to find the node in the current nodes array to get the exact ID
        const actualNode = nodes.find((n) => {
          // Try exact match first
          if (n.id === deletedNodeId) return true;
          // Try matching by nodePath in data
          if (n.data?.nodePath === nodeToDelete.path) return true;
          // Try matching by label
          if (n.data?.label === nodeToDelete.label) return true;
          return false;
        });
        
        if (actualNode) {
          deletedNodeId = actualNode.id;
          console.log('✅ [DELETE] Found actual node, using ID:', deletedNodeId);
        } else {
          console.warn('⚠️ [DELETE] Could not find node in nodes array, using calculated ID:', deletedNodeId);
        }

        const newExpandedNodes = new Set(expandedNodes);
        
        // First, explicitly preserve all parent nodes by extracting parent paths
        const parentPaths: string[] = [];
        const idParts = deletedNodeId.split('/');
        for (let i = 1; i < idParts.length; i++) {
          const parentPath = idParts.slice(0, i).join('/');
          if (parentPath) {
            parentPaths.push(parentPath);
          }
        }
        console.log('👪 [DELETE] Parent paths to preserve:', parentPaths);
        
        // Remove the deleted node itself
        newExpandedNodes.delete(deletedNodeId);
        console.log('🧹 [DELETE] Removed deleted node:', deletedNodeId);
        
        // Remove all descendant nodes (nodes whose ID starts with deletedNodeId + '/')
        expandedNodes.forEach(nodeId => {
          if (nodeId.startsWith(deletedNodeId + '/')) {
            newExpandedNodes.delete(nodeId);
            console.log('🧹 [DELETE] Removing deleted descendant from expansion:', nodeId);
          }
        });
        
        // Explicitly re-add parent paths to ensure they stay expanded
        parentPaths.forEach(parentPath => {
          newExpandedNodes.add(parentPath);
          console.log('✅ [DELETE] Ensured parent path is expanded:', parentPath);
        });
        
        console.log('📊 [DELETE] AFTER cleanup - newExpandedNodes:', Array.from(newExpandedNodes));
        
        // Store the cleaned expansion state in both ref and window storage
        // Ref for immediate use, window storage for persistence across remounts
        pendingExpandedNodesRef.current = newExpandedNodes;
        if (knowledgePackId) {
          (window as any)[getPendingExpansionKey()] = Array.from(newExpandedNodes);
          console.log('💾 [DELETE] Stored expansion state in window storage with key:', getPendingExpansionKey());
        }
        console.log('🔓 [DELETE] Stored expansion state in pendingExpandedNodesRef');
        console.log('📊 [DELETE] Pending expansion state:', Array.from(pendingExpandedNodesRef.current));

        // Show success toast
        toast.success('Node deleted successfully');

        // Close dialog
        setShowDeleteDialog(false);
        setNodeToDelete(null);

        // Refresh the knowledge pack tree to show updated structure
        if (window.refreshKnowledgePackTree) {
          console.log('🔄 [DELETE] Calling refreshKnowledgePackTree()');
          window.refreshKnowledgePackTree();
        } else {
          console.warn('⚠️ [DELETE] refreshKnowledgePackTree function not available');
        }
      } else {
        console.error('Delete failed:', response.message);
        toast.error('Failed to delete node');
      }
    } catch (error) {
      console.error('Error deleting node:', error);
      toast.error('Failed to delete node');
    } finally {
      setIsDeleting(false);
    }
  };

  // Cancel delete
  const cancelDelete = () => {
    setShowDeleteDialog(false);
    setNodeToDelete(null);
  };

  // Handle generate knowledge
  const handleGenerateKnowledge = async () => {
    if (!knowledgePackId || isGenerating) return;

    // Prevent starting a new generation if there's already one in progress
    if (backgroundTaskStatus?.status === 'running' || backgroundTaskStatus?.status === 'pending') {
      toast.info('Knowledge generation is already in progress. Please wait for it to complete.');
      return;
    }

    setIsGenerating(true);
    try {
      const kpId =
        typeof knowledgePackId === 'string' ? parseInt(knowledgePackId) : knowledgePackId;

      const response = await apiService.generateKnowledgePackKnowledge(kpId);

      if (response.success) {
        // Show success message with information about background processing
        toast.success(
          'Knowledge generation started! This process runs in the background. You can safely leave this page and come back later to check the results.',
          {
            duration: 6000, // Show for 6 seconds
          },
        );

        // Set background task status to 'running' immediately to keep button disabled
        if (response.task_id) {
          setBackgroundTaskStatus({
            id: response.task_id,
            status: 'running',
            progress: 0,
            error: undefined,
          });
        }

        // Set generation flag in store to disable chat input
        setIsGeneratingKnowledge(true);

        // Don't set isGenerating to false - keep button disabled
        return;
      } else {
        toast.error(response.message || 'Failed to start knowledge generation');
        setIsGenerating(false);
      }
    } catch (error: any) {
      console.error('Error generating knowledge:', error);
      toast.error(error?.message || 'Failed to start knowledge generation');
      setIsGenerating(false);
    }
  };

  // Calculate progress statistics
  const getProgressStats = () => {
    if (!statusData || !statusData.topics)
      return { total: 0, completed: 0, inProgress: 0, failed: 0, pending: 0 };

    const total = statusData.topics.length;
    const completed = statusData.topics.filter((topic: any) => topic.status === 'success').length;
    const inProgress = statusData.topics.filter(
      (topic: any) => topic.status === 'in_progress',
    ).length;
    const failed = statusData.topics.filter((topic: any) => topic.status === 'failed').length;
    const pending = statusData.topics.filter((topic: any) => topic.status === 'pending').length;

    return { total, completed, inProgress, failed, pending };
  };

  // Helper to get status for a node
  const getNodeStatus = (node: FlowNode) => {
    // Try both path and topic_id (UUID)
    return topicStatus[node.id] || topicStatus[node.data?.path] || topicStatus[node.data?.topic_id];
  };

  // Render a status icon for a node
  const renderStatusIcon = (status: string | undefined) => {
    if (status === 'in_progress') {
      return (
        <span title="Generating..." className="ml-2 animate-spin">
          ⏳
        </span>
      );
    }
    if (status === 'success') {
      return (
        <span title="Done" className="ml-2 text-green-600">
          ✔️
        </span>
      );
    }
    if (status === 'failed') {
      return (
        <span title="Failed" className="ml-2 text-red-600">
          ❌
        </span>
      );
    }
    return null;
  };

  // No more full page loading replacement - all loading states handled within main component

  return (
    <>
      <div
        className="flex flex-col gap-4 w-full h-full bg-white"
        style={{ position: 'relative' }}
        ref={containerRef}
      >
        {/* Smooth loading indicator that slides down from top */}
        {(initialLoading || loading) && (
          <div
            className="absolute top-0 right-0 left-0 z-30 transform"
            style={{ transition: TRANSITION_ALL }}
          >
            <div className="flex justify-center items-center py-2 bg-blue-50 border-b border-blue-200 shadow-sm animate-pulse">
              <div className="flex gap-2 items-center text-blue-700">
                <div className="w-4 h-4 rounded-full border-2 border-blue-300 animate-spin border-t-blue-600"></div>
                <span className="text-sm font-medium">
                  {initialLoading ? 'Refreshing knowledge tree...' : 'Updating knowledge tree...'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Enhanced Control Bar */}
        {knowledgePackId && (
          <div className={`px-4 ${initialLoading || loading ? 'top-16' : 'top-4'}`}>
            <div className="flex gap-3 justify-between items-center pt-4">
              {/* Left side - Search and Tree Controls */}
              <div className="flex flex-1 gap-3 items-center">
                {/* Search Input */}
                <div className="relative flex-1 max-w-md">
                  <div className="absolute left-3 top-1/2 text-gray-400 transform -translate-y-1/2">
                    <Search width={16} height={16} />
                  </div>
                  <input
                    type="text"
                    placeholder="Search topic"
                    value={searchQuery}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    className="py-2 pr-3 pl-10 w-full text-sm rounded-md border border-gray-300 focus:outline-none focus:ring-1"
                  />
                  {searchQuery && (
                    <button
                      onClick={() => handleSearchChange('')}
                      className="absolute right-2 top-1/2 text-gray-400 transform -translate-y-1/2 hover:text-gray-600"
                    >
                      ✕
                    </button>
                  )}
                </div>
              </div>

              {/* Right side - Total count and Tree Controls */}
              <div className="flex gap-3 items-center">
                {/* Total Items Count */}
                {statusData && statusData.topics && statusData.topics.length > 0 && (
                  <div className="text-sm font-medium text-gray-500">
                    {getProgressStats().total} items
                  </div>
                )}

                {/* Tree Toggle Control */}
                {(() => {
                  // Calculate if we should show "Expand All" or "Collapse All"
                  // If we have more than just the root expanded, show "Collapse All"
                  const shouldShowCollapse = expandedNodes.size > 1;

                  return (
                    <button
                      onClick={shouldShowCollapse ? handleCollapseAll : handleExpandAll}
                      disabled={!domainTree}
                      className="flex gap-1 items-center px-3 py-2 text-xs text-gray-600 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                      style={{ transition: TRANSITION_ALL }}
                      title={shouldShowCollapse ? 'Collapse All' : 'Expand All'}
                    >
                      {/* Icon for visual indication */}
                      {shouldShowCollapse ? (
                        <Collapse className="w-4 h-4" />
                      ) : (
                        <Expand className="w-4 h-4" />
                      )}
                      {shouldShowCollapse ? 'Collapse All' : 'Expand All'}
                    </button>
                  );
                })()}

                {/* Generate Knowledge Button - MOVED TO CHAT SIDEBAR */}
                {false && (
                  <Button
                    onClick={handleGenerateKnowledge}
                    disabled={
                      isGenerating ||
                      initialLoading ||
                      loading ||
                      backgroundTaskStatus?.status === 'running' ||
                      backgroundTaskStatus?.status === 'pending' ||
                      backgroundTaskStatus?.status === 'completed'
                    }
                    variant="default"
                    size="sm"
                    className="gap-2"
                    title={
                      backgroundTaskStatus?.status === 'running' || isGenerating
                        ? 'Knowledge generation is in progress'
                        : backgroundTaskStatus?.status === 'completed'
                          ? 'Knowledge generation completed'
                          : 'Start generating knowledge for all topics'
                    }
                  >
                    {backgroundTaskStatus?.status === 'running' || isGenerating ? (
                      <>
                        <SystemRestart className="w-4 h-4 animate-spin" />
                        <span>Generating...</span>
                      </>
                    ) : backgroundTaskStatus?.status === 'pending' ? (
                      <>
                        <SystemRestart className="w-4 h-4 animate-spin" />
                        <span>Pending...</span>
                      </>
                    ) : backgroundTaskStatus?.status === 'completed' ? (
                      <>
                        <Check className="w-4 h-4" />
                        <span>Knowledge generated</span>
                      </>
                    ) : (
                      <>
                        <LightBulb className="w-4 h-4" />
                        <span>Generate Knowledge</span>
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Knowledge Intro Box */}
        <KnowledgeIntroBox
          isVisible={showKnowledgeIntro}
          hasNewKnowledge={hasNewKnowledge}
          onDismiss={handleDismissIntro}
          knowledgePackMetadata={knowledgePackMetadata}
        />

        {/* Tree View Container with smooth margin adjustment */}
        <div
          className={`h-full ${knowledgePackId ? (initialLoading || loading ? 'pt-32' : 'pt-0') : ''}`}
          style={{ transition: TRANSITION_ALL }}
        >
          {nodes.length > 0 ? (
            <div className="h-full rounded-lg">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                fitViewOptions={{
                  padding: 0.2,
                  includeHiddenNodes: false,
                  minZoom: 0.1,
                  maxZoom: 2,
                }}
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                proOptions={{ hideAttribution: true }}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
                onInit={(reactFlowInstance) => {
                  reactFlowInstanceRef.current = reactFlowInstance;
                }}
                // Performance optimized properties
                defaultViewport={{ x: 0, y: 0, zoom: 1 }}
                minZoom={0.1}
                maxZoom={2}
                zoomOnScroll={true}
                panOnScroll={false}
                zoomOnPinch={true}
                panOnDrag={true}
                // Performance optimizations
                attributionPosition="bottom-left"
                snapToGrid={false}
                deleteKeyCode={null}
                selectionKeyCode={null}
                className={`${isTransitioning ? 'opacity-95' : 'opacity-100'}`}
              >
                <Controls />
              </ReactFlow>
            </div>
          ) : (
            /* Empty/Error State - Doesn't replace tree, shows as overlay */
            <div
              className="flex flex-col gap-4 justify-center items-center h-full"
              style={{ transition: TRANSITION_ALL }}
            >
              {initialLoading ? (
                /* Show loading state when first loading */
                <div className="text-center text-gray-500">
                  <div className="text-lg font-medium">Initializing Domain Knowledge</div>
                  <div className="text-sm">
                    Please wait while we load your agent's knowledge structure...
                  </div>
                </div>
              ) : error ? (
                /* Show error state */
                <>
                  <div className="text-center text-gray-500">
                    <div className="text-lg font-medium">No Domain Knowledge</div>
                    <div className="text-sm">{error}</div>
                  </div>
                  <div className="max-w-md text-xs text-center text-gray-400">
                    Chat with Dana to add missing knowledge
                  </div>
                </>
              ) : (
                /* Show empty state when no nodes but no error */
                <>
                  <div className="flex flex-col text-center item-center">
                    <div className="flex justify-center items-center pb-4 text-gray-400">
                      <Search className="w-10 h-10" />
                    </div>
                    <div className="text-lg font-semibold text-gray-500">Keyword not found</div>
                    <div className="text-sm text-gray-500">
                      Chat with Dana to add missing knowledge
                    </div>
                  </div>
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Knowledge Sidebar */}
      <KnowledgeSidebar
        isOpen={sidebarOpen}
        onClose={() => {
          setSidebarOpen(false);
          setSelectedNodeId(null); // Clear selection when sidebar closes
        }}
        topicPath={sidebarTopicPath}
        content={sidebarContent}
        loading={sidebarLoading}
        error={sidebarError}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex gap-3 items-center">Delete knowledge node?</DialogTitle>
          </DialogHeader>

          <div className="mt-2">
            <p className="text-sm text-gray-700">
              You’re about to remove <strong>"{nodeToDelete?.label}"</strong>. This will remove the
              node and <em>all its sub-nodes and associated knowledge content.</em>
            </p>
          </div>

          <DialogFooter className="flex gap-2 sm:flex-row">
            <Button
              onClick={cancelDelete}
              disabled={isDeleting}
              variant="outline"
              className="w-full sm:w-auto"
            >
              Cancel
            </Button>
            <Button
              onClick={confirmDelete}
              disabled={isDeleting}
              variant="destructive"
              className="w-full sm:w-auto"
            >
              {isDeleting ? (
                <div className="flex items-center">
                  <div className="mr-2 w-4 h-4 rounded-full border-2 border-white animate-spin border-t-transparent"></div>
                  Deleting...
                </div>
              ) : (
                'Delete'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
};

export default DomainKnowledgeTree;
