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
  { id: 'e1-2', source: '1', target: '2', markerEnd: { type: MarkerType.ArrowClosed }, type: 'smoothstep' },
  { id: 'e2-3', source: '2', target: '3', markerEnd: { type: MarkerType.ArrowClosed }, type: 'smoothstep' },
  { id: 'e3-4', source: '3', target: '4', markerEnd: { type: MarkerType.ArrowClosed }, type: 'smoothstep' },
  { id: 'e1-5', source: '1', target: '5', markerEnd: { type: MarkerType.ArrowClosed }, type: 'smoothstep' },
  { id: 'e1-6', source: '1', target: '6', markerEnd: { type: MarkerType.ArrowClosed }, type: 'smoothstep' },
  { id: 'e1-7', source: '1', target: '7', markerEnd: { type: MarkerType.ArrowClosed }, type: 'smoothstep' },
];

const nodeWidth = 220;   // Keep width for horizontal layout
const nodeHeight = 80;  // Keep height for horizontal layout

function getLayoutedElements(nodes: FlowNode[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 60,   // more separation for horizontal
    ranksep: 120,  // more separation for horizontal
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
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const [generateMsg, setGenerateMsg] = useState<string | null>(null);
  const [knowledgeStatus, setKnowledgeStatus] = useState<KnowledgeStatusResponse | null>(null);
  const [topicStatus, setTopicStatus] = useState<{ [id: string]: string }>({});
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);

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
          if (msg.path) {
            setTopicStatus((prev) => {
              console.log('[WebSocket] Updating status for path:', msg.path, msg.status);
              return { ...prev, [msg.path]: msg.status };
            });
          }
          // Update by topic_id (UUID) if present
          if (msg.topic_id) {
            setTopicStatus((prev) => {
              console.log('[WebSocket] Updating status for topic_id:', msg.topic_id, msg.status);
              return { ...prev, [msg.topic_id]: msg.status };
            });
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
        onNodeClick={() => setSelectedNodeId(nodeProps.id)}
      >
        {renderStatusIcon(getNodeStatus(nodeProps))}
      </CustomNode>
    ),
  };

  // Convert domain knowledge tree to flow nodes and edges
  const convertDomainToFlow = (domainTree: DomainKnowledgeResponse, statusData?: KnowledgeStatusResponse): { nodes: FlowNode[], edges: Edge[] } => {
    const nodes: FlowNode[] = [];
    const edges: Edge[] = [];

    // Helper function to get knowledge status for a node path
    const getKnowledgeStatusForPath = (nodePath: string): KnowledgeTopicStatus | null => {
      if (!statusData || !statusData.topics) return null;

      // Find the status entry that matches this node's path
      return statusData.topics.find(topic => topic.path === nodePath) || null;
    };

    const traverse = (domainNode: DomainNode, parentId?: string, pathParts: string[] = []) => {
      const currentPath = [...pathParts, domainNode.topic];
      const nodeId = currentPath.join('/'); // Unique path-based ID
      const nodePath = currentPath.join(' - '); // Path format used in knowledge status

      // Get knowledge status for this node (only leaf nodes will have status)
      const isLeafNode = !domainNode.children || domainNode.children.length === 0;
      const knowledgeStatusInfo = isLeafNode ? getKnowledgeStatusForPath(nodePath) : null;

      // Create flow node with knowledge status information
      nodes.push({
        id: nodeId,
        type: 'custom',
        data: {
          label: domainNode.topic,
          knowledgeStatus: knowledgeStatusInfo,
          isLeafNode,
          nodePath
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

      // Recursively process children
      domainNode.children?.forEach(child => traverse(child, nodeId, currentPath));

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
      setKnowledgeStatus(null);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      setError(null);

      try {
        // Fetch both domain knowledge and knowledge status in parallel
        const [domainResponse, statusResponse] = await Promise.all([
          apiService.getDomainKnowledge(agentId),
          apiService.getKnowledgeStatus(agentId).catch(() => ({ topics: [] })) // Fallback to empty if status fails
        ]);

        // Set knowledge status first so convertDomainToFlow can use it
        setKnowledgeStatus(statusResponse);

        if (domainResponse.message) {
          // No domain knowledge found, show empty state
          setNodes([]);
          setEdges([]);
          setError(domainResponse.message);
        } else if (domainResponse.root) {
          // Convert domain knowledge to flow format (now with status information)
          const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(domainResponse, statusResponse);
          const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
          setNodes(layoutedNodes);
          setEdges(flowEdges);
        }
      } catch (err) {
        console.error('Error fetching data:', err);
        setError('Failed to load domain knowledge');
        setKnowledgeStatus({ topics: [] });
        // Fall back to default nodes
        const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
        setNodes(layouted);
        setEdges(initialEdges);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [agentId]);

  // Hide popup when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
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

  // Handle node click
  const onNodeClick = (_: React.MouseEvent, node: FlowNode) => {
    setSelectedNodeId(node.id);
  };

  // Optionally, handle pane click to clear selection
  const onPaneClick = () => {
    setSelectedNodeId(null);
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

  // Helper to get status for a node
  const getNodeStatus = (node: FlowNode) => {
    // Try both path and topic_id (UUID)
    return topicStatus[node.id] || topicStatus[node.data?.path] || topicStatus[node.data?.topic_id];
  };

  // Render a status icon for a node
  const renderStatusIcon = (status: string | undefined) => {
    if (status === 'in_progress') {
      return <span title="Generating..." className="ml-2 animate-spin">⏳</span>;
    }
    if (status === 'success') {
      return <span title="Done" className="ml-2 text-green-600">✔️</span>;
    }
    if (status === 'failed') {
      return <span title="Failed" className="ml-2 text-red-600">❌</span>;
    }
    return null;
  };

  // Show loading state
  if (loading) {
    return (
      <div className="h-full w-full bg-white flex items-center justify-center">
        <div className="text-gray-500">Loading domain knowledge...</div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="h-full w-full bg-white flex flex-col items-center justify-center gap-4">
        <div className="text-gray-500 text-center">
          <div className="text-lg font-medium">No Domain Knowledge</div>
          <div className="text-sm">{error}</div>
        </div>
        <div className="text-xs text-gray-400 max-w-md text-center">
          Start a conversation with the agent to build domain knowledge automatically,
          or use the smart chat feature to add specific expertise areas.
        </div>
        {agentId && (
          <button
            onClick={handleGenerateKnowledge}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? 'Generating...' : 'Generate Domain Knowledge'}
          </button>
        )}
        {generateMsg && (
          <div className="mt-2 text-xs text-gray-600">{generateMsg}</div>
        )}
      </div>
    );
  }

  // Show empty state if no nodes
  if (nodes.length === 0) {
    return (
      <div className="h-full w-full bg-white flex flex-col items-center justify-center gap-4">
        <div className="text-gray-500 text-center">
          <div className="text-lg font-medium">No Domain Knowledge</div>
          <div className="text-sm">This agent doesn't have any domain knowledge yet</div>
        </div>
        <div className="text-xs text-gray-400 max-w-md text-center">
          Start a conversation with the agent to build domain knowledge automatically,
          or use the smart chat feature to add specific expertise areas.
        </div>
        {agentId && (
          <button
            onClick={handleGenerateKnowledge}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? 'Generating...' : 'Generate Domain Knowledge'}
          </button>
        )}
        {generateMsg && (
          <div className="mt-2 text-xs text-gray-600">{generateMsg}</div>
        )}
      </div>
    );
  }

  return (
    <>
      {agentId && (
        <div style={{}}>
          <button
            onClick={handleGenerateKnowledge}
            disabled={generating}
            className="px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 disabled:opacity-50"
          >
            {generating ? 'Generating...' : 'Generate Domain Knowledge'}
          </button>
        </div>
      )}
      <div className='h-full w-full bg-white flex flex-col gap-4' style={{ position: 'relative' }} ref={containerRef}>
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
    </>
  );
};

export default DomainKnowledgeTree; 