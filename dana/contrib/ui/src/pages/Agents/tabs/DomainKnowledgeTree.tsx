import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Controls, Position, MarkerType } from 'reactflow';
import type { Node as FlowNode, Edge } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import { apiService } from '@/lib/api';
import type { DomainKnowledgeResponse, DomainNode } from '@/types/domainKnowledge';
import type { KnowledgeStatusResponse, KnowledgeTopicStatus } from '@/lib/api';
import { toast } from 'sonner';
import KnowledgeSidebar from './KnowledgeSidebar';
import { Search } from 'iconoir-react';

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
    type: 'smoothstep',
  },
  {
    id: 'e2-3',
    source: '2',
    target: '3',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'smoothstep',
  },
  {
    id: 'e3-4',
    source: '3',
    target: '4',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'smoothstep',
  },
  {
    id: 'e1-5',
    source: '1',
    target: '5',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'smoothstep',
  },
  {
    id: 'e1-6',
    source: '1',
    target: '6',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'smoothstep',
  },
  {
    id: 'e1-7',
    source: '1',
    target: '7',
    markerEnd: { type: MarkerType.ArrowClosed },
    type: 'smoothstep',
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
  agentId?: string | number;
}

// Add this function to call the API
async function triggerGenerateKnowledge(agentId: string | number) {
  const response = await apiService.generateKnowledge(agentId);
  toast.success(response.message);
  return response;
}

// Use backend URL for WebSocket
const wsUrl = `ws://localhost:8080/ws/knowledge-status`;

const DomainKnowledgeTree: React.FC<DomainKnowledgeTreeProps> = ({ agentId }) => {
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [, setGenerateMsg] = useState<string | null>(null);
  const [topicStatus] = useState<{ [id: string]: string }>({});
  const [domainTree, setDomainTree] = useState<DomainKnowledgeResponse | null>(null);
  const [statusData, setStatusData] = useState<KnowledgeStatusResponse | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarTopicPath, setSidebarTopicPath] = useState<string>('');
  const [sidebarContent, setSidebarContent] = useState<any>(null);
  const [sidebarLoading, setSidebarLoading] = useState(false);
  const [sidebarError, setSidebarError] = useState<string | null>(null);
  // New UX improvement states
  const [searchQuery, setSearchQuery] = useState<string>('');
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const expandedNodesRef = useRef<Set<string>>(new Set());
  const previousAgentIdRef = useRef<string | number | undefined>(undefined);

  // Keep the ref in sync with the state
  useEffect(() => {
    expandedNodesRef.current = expandedNodes;
  }, [expandedNodes]);

  // Reset expansion state only when switching to a different agent
  useEffect(() => {
    if (agentId && agentId !== previousAgentIdRef.current) {
      setExpandedNodes(new Set());
      expandedNodesRef.current = new Set();
      previousAgentIdRef.current = agentId;
    } else if (agentId) {
      previousAgentIdRef.current = agentId;
    }
  }, [agentId]);

  // WebSocket for real-time status updates
  useEffect(() => {
    if (!agentId) return;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;
    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'knowledge_status_update') {
          // Debug: log the message
          console.log('[WebSocket] Received knowledge_status_update:', msg);
          // Update by path
          // --- NEW: Refetch domain knowledge and status on update ---
          if (agentId) {
            (async () => {
              try {
                setLoading(true);
                const [domainResponse, statusResponse] = await Promise.all([
                  apiService.getDomainKnowledge(agentId),
                  apiService.getKnowledgeStatus(agentId).catch(() => ({ topics: [] })),
                ]);
                if (domainResponse.message) {
                  setNodes([]);
                  setEdges([]);
                  setError(domainResponse.message);
                } else if (domainResponse.root) {
                  // Store the domain tree and status data
                  setDomainTree(domainResponse);
                  setStatusData(statusResponse);

                  const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
                    domainResponse,
                    statusResponse,
                    expandedNodesRef.current,
                    searchQuery,
                  );
                  const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
                  setNodes(layoutedNodes);
                  setEdges(flowEdges);
                  setError(null);
                }
              } catch (err) {
                setError('Failed to refresh domain knowledge');
              } finally {
                setLoading(false);
              }
            })();
          }
        }
      } catch (e) {
        // Ignore malformed messages
      }
    };
    ws.onclose = () => {
      // Optionally, try to reconnect
    };
    return () => {
      ws.close();
    };
  }, [agentId]);

  const nodeTypes = {
    custom: (nodeProps: any) => (
      <CustomNode
        {...nodeProps}
        isSelected={selectedNodeId === nodeProps.id}
        onNodeClick={(event: React.MouseEvent) => onNodeClick(event, nodeProps)}
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

      // Find the status entry that matches this node's path
      // First try exact match
      let match = statusData.topics.find((topic) => topic.path === nodePath);
      if (match) return match;

      // If no exact match, try to find a partial match for leaf nodes
      // This handles cases where the domain tree structure differs from knowledge status paths
      const pathParts = nodePath.split(' - ');
      for (const topic of statusData.topics) {
        const topicParts = topic.path.split(' - ');

        // Check if this could be a match by comparing the last part (leaf node name)
        if (pathParts.length > 0 && topicParts.length > 0) {
          const lastPathPart = pathParts[pathParts.length - 1];
          const lastTopicPart = topicParts[topicParts.length - 1];

          // If the leaf node names match and the topic path is a subset of the node path
          if (
            lastPathPart === lastTopicPart &&
            topicParts.every((part) => pathParts.includes(part))
          ) {
            return topic;
          }
        }
      }

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
        nodes.push({
          id: nodeId,
          type: 'custom',
          data: {
            label: domainNode.topic,
            knowledgeStatus: knowledgeStatusInfo,
            isLeafNode,
            hasChildren,
            nodePath,
            isExpanded: expandedNodeIds?.has(nodeId) || false,
          },
          position: { x: 0, y: 0 }, // Will be set by dagre layout
        });

        // Create edge from parent if exists
        if (parentId) {
          edges.push({
            id: `e${parentId}-${nodeId}`,
            source: parentId,
            target: nodeId,
            markerEnd: { type: MarkerType.ArrowClosed },
            type: 'smoothstep',
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

  // Fetch domain knowledge data and knowledge status
  useEffect(() => {
    if (!agentId) {
      // Show default nodes if no agent ID
      const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
      setNodes(layouted);
      setEdges(initialEdges);
      return;
    }

    const fetchData = async () => {
      setInitialLoading(true);
      setError(null);

      try {
        // Fetch both domain knowledge and knowledge status in parallel
        const [domainResponse, statusResponse] = await Promise.all([
          apiService.getDomainKnowledge(agentId),
          apiService.getKnowledgeStatus(agentId).catch(() => ({ topics: [] })), // Fallback to empty if status fails
        ]);

        if (domainResponse.message) {
          // No domain knowledge found, show empty state
          setNodes([]);
          setEdges([]);
          setError(domainResponse.message);
        } else if (domainResponse.root) {
          // Store the domain tree and status data
          setDomainTree(domainResponse);
          setStatusData(statusResponse);

          // Preserve existing expansion state or initialize with just the root
          const currentExpanded =
            expandedNodesRef.current.size > 0
              ? expandedNodesRef.current
              : new Set([domainResponse.root.topic]);

          // Only set expanded nodes if we don't have any yet
          if (expandedNodesRef.current.size === 0) {
            setExpandedNodes(currentExpanded);
          }

          // Convert domain knowledge to flow format (now with status information)
          const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
            domainResponse,
            statusResponse,
            currentExpanded,
            searchQuery,
          );
          const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
          setNodes(layoutedNodes);
          setEdges(flowEdges);
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load domain knowledge');
        // Fall back to default nodes
        const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
        setNodes(layouted);
        setEdges(initialEdges);
      } finally {
        setInitialLoading(false);
      }
    };

    fetchData();
  }, [agentId]);

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

      // Check if knowledge is generated
      if (nodeData.knowledgeStatus && nodeData.knowledgeStatus.status === 'success') {
        // Open sidebar and fetch content
        setSidebarOpen(true);
        setSidebarTopicPath(topicPath);
        setSidebarLoading(true);
        setSidebarError(null);
        setSidebarContent(null);

        try {
          const response = await apiService.getTopicKnowledgeContent(agentId!, topicPath);

          if (response.success) {
            setSidebarContent(response.content);
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
        // Show toast that knowledge is not generated yet
        const status = nodeData.knowledgeStatus?.status || 'pending';
        let message = '';

        switch (status) {
          case 'pending':
            message = `Knowledge for "${nodeData.label}" is not generated yet. Click "Generate Contextual Knowledge" to start generation.`;
            break;
          case 'in_progress':
            message = `Knowledge for "${nodeData.label}" is currently being generated. Please wait...`;
            break;
          case 'failed':
            message = `Knowledge generation failed for "${nodeData.label}". Please try regenerating.`;
            break;
          default:
            message = `Knowledge for "${nodeData.label}" is not available yet.`;
        }

        toast.info(message, {
          duration: 5000,
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
      if (domainTree && statusData) {
        const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
          domainTree,
          statusData,
          newExpandedNodes,
          searchQuery,
        );
        const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
        setNodes(layoutedNodes);
        setEdges(flowEdges);
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

  // Handler for the button
  const handleGenerateKnowledge = async () => {
    if (!agentId) return;
    setGenerating(true);
    setGenerateMsg(null);
    try {
      const result = await triggerGenerateKnowledge(agentId);
      setGenerateMsg(result.message || 'Generation started!');
    } catch (err) {
      setGenerateMsg('Failed to start generation');
    } finally {
      setGenerating(false);
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
    if (domainTree && statusData) {
      const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
        domainTree,
        statusData,
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
    const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
      domainTree,
      statusData!,
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
    const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(
      domainTree,
      statusData!,
      rootOnly,
      searchQuery,
    );
    const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
    setNodes(layoutedNodes);
    setEdges(flowEdges);
  };

  // Calculate progress statistics
  const getProgressStats = () => {
    if (!statusData || !statusData.topics)
      return { total: 0, completed: 0, inProgress: 0, failed: 0, pending: 0 };

    const total = statusData.topics.length;
    const completed = statusData.topics.filter((topic) => topic.status === 'success').length;
    const inProgress = statusData.topics.filter((topic) => topic.status === 'in_progress').length;
    const failed = statusData.topics.filter((topic) => topic.status === 'failed').length;
    const pending = statusData.topics.filter((topic) => topic.status === 'pending').length;

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
          <div className="absolute top-0 right-0 left-0 z-30 transition-all duration-300 ease-in-out transform">
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
        {agentId && (
          <div
            className={`absolute left-4 right-4 z-20 transition-all duration-300 ease-in-out ${
              initialLoading || loading ? 'top-16' : 'top-4'
            }`}
          >
            <div className="flex gap-3 justify-between items-center">
              {/* Left side - Search and Tree Controls */}
              <div className="flex flex-1 gap-3 items-center">
                {/* Search Input */}
                <div className="relative flex-1 max-w-md">
                  <div className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400">
                    <Search width={16} height={16} />
                  </div>
                  <input
                    type="text"
                    placeholder="Search topic"
                    value={searchQuery}
                    onChange={(e) => handleSearchChange(e.target.value)}
                    className="pl-10 pr-3 py-2 w-full text-sm rounded-md border border-gray-300 focus:outline-none focus:ring-1"
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

                {/* Tree Controls */}
                <div className="flex gap-2">
                  <button
                    onClick={handleExpandAll}
                    disabled={!domainTree}
                    className="px-3 py-2 text-xs text-gray-600 bg-gray-50 rounded-md border border-gray-200 transition-colors hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Expand All"
                  >
                    Expand All
                  </button>
                  <button
                    onClick={handleCollapseAll}
                    disabled={!domainTree}
                    className="px-3 py-2 text-xs text-gray-600 bg-gray-50 rounded-md border border-gray-200 transition-colors hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                    title="Collapse All"
                  >
                    Collapse All
                  </button>
                </div>
              </div>

              {/* Right side - Total count and Generate Button */}
              <div className="flex gap-3 items-center">
                {/* Total Items Count */}
                {statusData && statusData.topics && statusData.topics.length > 0 && (
                  <div className="text-xs font-medium text-gray-500">
                    {getProgressStats().total} items
                  </div>
                )}

                {/* Generate Knowledge Button */}
                <button
                  onClick={handleGenerateKnowledge}
                  disabled={generating || initialLoading || loading}
                  className={`px-4 py-2 text-sm rounded-md border transition-all duration-200 shadow-sm ${
                    generating || initialLoading || loading
                      ? 'text-gray-400 bg-gray-100 border-gray-200 cursor-not-allowed opacity-75'
                      : 'text-gray-700 bg-white border-gray-300 hover:bg-gray-50 hover:text-gray-900 hover:shadow-md'
                  }`}
                >
                  {generating ? (
                    <div className="flex gap-2 items-center">
                      <div className="w-4 h-4 rounded-full border-2 border-gray-300 animate-spin border-t-blue-500"></div>
                      <span>Generating...</span>
                    </div>
                  ) : (
                    <span className="text-sm font-medium text-gray-700">Generate Knowledge</span>
                  )}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tree View Container with smooth margin adjustment */}
        <div
          className={`transition-all duration-300 ease-in-out h-full ${
            agentId ? (initialLoading || loading ? 'pt-32' : 'pt-20') : ''
          }`}
        >
          {nodes.length > 0 ? (
            <div className="h-full rounded-lg">
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                fitView
                nodesDraggable={false}
                nodesConnectable={false}
                elementsSelectable={false}
                proOptions={{ hideAttribution: true }}
                onNodeClick={onNodeClick}
                onPaneClick={onPaneClick}
              >
                <Controls />
              </ReactFlow>
            </div>
          ) : (
            /* Empty/Error State - Doesn't replace tree, shows as overlay */
            <div className="flex flex-col gap-4 justify-center items-center h-full transition-opacity duration-500 ease-in-out">
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
                  <div className="text-center flex item-center flex-col ">
                    <div className="flex items-center pb-4 justify-center text-gray-400">
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
    </>
  );
};

export default DomainKnowledgeTree;
