import React, { useState, useEffect } from 'react';
import ReactFlow, { Controls, Position, MarkerType } from 'reactflow';
import type { Node, Edge } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';

const initialNodes: Node[] = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Finance' },
    position: { x: 0, y: 0 }, // dummy, will be overwritten
  },
  {
    id: '2',
    data: { label: 'Market Analysis' },
    position: { x: 0, y: 0 },
  },
  {
    id: '3',
    data: { label: 'Investment Strategy' },
    position: { x: 0, y: 0 },
  },
  {
    id: '4',
    data: { label: 'Risk Management' },
    position: { x: 0, y: 0 },
  },
  {
    id: '5',
    data: { label: 'Financial Planning' },
    position: { x: 0, y: 0 },
  },
  {
    id: '6',
    data: { label: 'Corporate' },
    position: { x: 0, y: 0 },
  },
  {
    id: '7',
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

function getLayoutedElements(nodes: Node[], edges: Edge[], direction: 'LR' | 'TB' = 'LR') {
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
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  useEffect(() => {
    const layouted = getLayoutedElements(initialNodes, initialEdges, 'LR');
    setNodes(layouted);
    setEdges(initialEdges);
  }, []);

  return (
    <div style={{ width: '100%', height: '600px', background: 'white' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        fitView
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
      >
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default DomainKnowledgeTree; 