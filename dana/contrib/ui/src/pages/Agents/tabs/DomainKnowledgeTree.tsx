import React, { useState, useEffect, useRef } from 'react';
import ReactFlow, { Controls, Position, MarkerType } from 'reactflow';
import type { Node as FlowNode, Edge } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import CustomNode from './CustomNode';

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

const nodeWidth = 180;
const nodeHeight = 60;

function getLayoutedElements(nodes: FlowNode[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction });

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

const DomainKnowledgeTree: React.FC = () => {
  const [nodes, setNodes] = useState<FlowNode[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
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

  useEffect(() => {
    const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
    setNodes(layouted);
    setEdges(initialEdges);
  }, []);

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