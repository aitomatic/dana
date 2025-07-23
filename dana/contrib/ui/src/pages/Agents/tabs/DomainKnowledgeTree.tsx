import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Controls, Position, MarkerType } from 'reactflow';
import type { Node as FlowNode, Edge } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';
import { apiService } from '@/lib/api';
import type { DomainKnowledgeResponse, DomainNode } from '@/types/domainKnowledge';

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

const DomainKnowledgeTree: React.FC<DomainKnowledgeTreeProps> = ({ agentId }) => {
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const nodeTypes = {
    custom: (nodeProps: any) => (
      <CustomNode
        {...nodeProps}
        isSelected={selectedNodeId === nodeProps.id}
        onNodeClick={() => setSelectedNodeId(nodeProps.id)}
      />
    ),
  };

  // Convert domain knowledge tree to flow nodes and edges
  const convertDomainToFlow = (domainTree: DomainKnowledgeResponse): { nodes: FlowNode[], edges: Edge[] } => {
    const nodes: FlowNode[] = [];
    const edges: Edge[] = [];

    const traverse = (domainNode: DomainNode, parentId?: string, path: string = '') => {
      const nodeId = path ? `${path}/${domainNode.topic}` : domainNode.topic; // Unique path-based ID

      // Create flow node
      nodes.push({
        id: nodeId,
        type: 'custom',
        data: { label: domainNode.topic },
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
      domainNode.children?.forEach(child => traverse(child, nodeId, nodeId));

      return nodeId;
    };

    if (domainTree.root) {
      traverse(domainTree.root);
    }

    return { nodes, edges };
  };

  // Fetch domain knowledge data
  useEffect(() => {
    if (!agentId) {
      // Show default nodes if no agent ID
      const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
      setNodes(layouted);
      setEdges(initialEdges);
      return;
    }

    const fetchDomainKnowledge = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await apiService.getDomainKnowledge(agentId);

        if (response.message) {
          // No domain knowledge found, show empty state
          setNodes([]);
          setEdges([]);
          setError(response.message);
        } else if (response.root) {
          // Convert domain knowledge to flow format
          const { nodes: flowNodes, edges: flowEdges } = convertDomainToFlow(response);
          const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'LR');
          setNodes(layoutedNodes);
          setEdges(flowEdges);
        }
      } catch (err) {
        console.error('Error fetching domain knowledge:', err);
        setError('Failed to load domain knowledge');
        // Fall back to default nodes
        const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
        setNodes(layouted);
        setEdges(initialEdges);
      } finally {
        setLoading(false);
      }
    };

    fetchDomainKnowledge();
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
      </div>
    );
  }

  return (
    <div className='h-full w-full bg-white' style={{ position: 'relative' }} ref={containerRef}>
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
  );
};

export default DomainKnowledgeTree; 