import React, { useMemo, useEffect, useState } from 'react';
import ReactFlow, { Controls, Position, MarkerType } from 'reactflow';
import type { Node as FlowNode, Edge } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import AgentChartNode from './AgentChartNode';
import type { AgentOverviewChartProps, AgentChartData } from './types/agent-chart';
import { apiService } from '@/lib/api';
import type { DomainKnowledgeResponse } from '@/types/domainKnowledge';

const nodeWidth = 250;
const nodeHeight = 100;
const mainNodeSize = 96;

function getLayoutedElements(nodes: FlowNode[], edges: Edge[], direction: 'TB' = 'TB') {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 100, // Increased separation between nodes
    ranksep: 150, // Increased separation between ranks
  });

  nodes.forEach((node) => {
    const isMain = node.data?.isMain;
    const width = isMain ? mainNodeSize : nodeWidth;
    const height = isMain ? mainNodeSize : nodeHeight;
    dagreGraph.setNode(node.id, { width, height });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    const isMain = node.data?.isMain;
    const width = isMain ? mainNodeSize : nodeWidth;
    const height = isMain ? mainNodeSize : nodeHeight;

    node.position = {
      x: nodeWithPosition.x - width / 2,
      y: nodeWithPosition.y - height / 2,
    };
    node.targetPosition = Position.Top;
    node.sourcePosition = Position.Bottom;
    return node;
  });
}

// Utility function to count nodes in domain knowledge tree
function countDomainKnowledgeNodes(domainTree: DomainKnowledgeResponse | null): number {
  if (!domainTree || !domainTree.root) return 0;

  let count = 0;

  function traverse(node: any) {
    if (node) {
      count++;
      if (node.children && Array.isArray(node.children)) {
        node.children.forEach(traverse);
      }
    }
  }

  traverse(domainTree.root);
  return count;
}

const AgentOverviewChart: React.FC<AgentOverviewChartProps> = ({ agent, className = '' }) => {
  const [domainKnowledge, setDomainKnowledge] = useState<DomainKnowledgeResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Fetch domain knowledge data
  useEffect(() => {
    if (!agent?.id) {
      setDomainKnowledge(null);
      return;
    }

    const fetchDomainKnowledge = async () => {
      setIsLoading(true);
      try {
        const response = await apiService.getDomainKnowledge(agent.id);
        setDomainKnowledge(response);
      } catch (error) {
        console.error('Failed to fetch domain knowledge:', error);
        setDomainKnowledge(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDomainKnowledge();
  }, [agent?.id]);

  const chartData = useMemo((): AgentChartData => {
    if (!agent) {
      return {
        agent: { name: 'Agent' },
        components: {
          aiModel: { name: 'GPT4o', status: 'active' },
          knowledgeBase: {
            domainKnowledge: { count: 0, status: 'empty' },
            documents: { count: 0, status: 'empty' },
            workflows: { status: 'coming-soon' },
          },
          tools: { status: 'coming-soon' },
        },
      };
    }

    // Count domain knowledge nodes
    const domainKnowledgeCount = countDomainKnowledgeNodes(domainKnowledge);

    // Count documents (from agent.files or other source)
    const documentsCount = agent.files ? agent.files.length : 0;

    return {
      agent: {
        name: agent.name || 'Agent',
        model: agent.config?.model || 'GPT4o',
        domain: agent.config?.domain,
        topic: agent.config?.topic,
      },
      components: {
        aiModel: {
          name: agent.config?.model || 'GPT4o',
          status: 'active',
        },
        knowledgeBase: {
          domainKnowledge: {
            count: domainKnowledgeCount,
            status: domainKnowledgeCount > 0 ? 'active' : 'empty',
          },
          documents: {
            count: documentsCount,
            status: documentsCount > 0 ? 'active' : 'empty',
          },
          workflows: {
            status: 'coming-soon',
          },
        },
        tools: {
          status: 'coming-soon',
        },
      },
    };
  }, [agent, domainKnowledge]);

  const { nodes, edges } = useMemo(() => {
    const flowNodes: FlowNode[] = [];
    const flowEdges: Edge[] = [];

    // Main agent node
    flowNodes.push({
      id: 'agent',
      type: 'agentChart',
      data: {
        label: chartData.agent.name,
        isMain: true,
        agentId: agent?.id,
      },
      position: { x: 0, y: 0 },
    });

    // AI Model node
    flowNodes.push({
      id: 'ai-model',
      type: 'agentChart',
      data: {
        label: 'AI Model',
        description: chartData.components.aiModel.name,
        status: chartData.components.aiModel.status,
      },
      position: { x: 0, y: 0 },
    });

    // Knowledge Base node
    flowNodes.push({
      id: 'knowledge-base',
      type: 'agentChart',
      data: {
        label: 'Knowledge Base',
        status: 'active',
      },
      position: { x: 0, y: 0 },
    });

    // Tools node
    flowNodes.push({
      id: 'tools',
      type: 'agentChart',
      data: {
        label: 'Tools',
        status: chartData.components.tools.status,
      },
      position: { x: 0, y: 0 },
    });

    // Knowledge Base sub-components
    flowNodes.push({
      id: 'domain-knowledge',
      type: 'agentChart',
      data: {
        label: 'Domain Knowledge',
        count: chartData.components.knowledgeBase.domainKnowledge.count,
        status: chartData.components.knowledgeBase.domainKnowledge.status,
        description: `${chartData.components.knowledgeBase.domainKnowledge.count} knowledge packs`,
      },
      position: { x: 0, y: 0 },
    });

    flowNodes.push({
      id: 'documents',
      type: 'agentChart',
      data: {
        label: 'Documents',
        count: chartData.components.knowledgeBase.documents.count,
        status: chartData.components.knowledgeBase.documents.status,
        description: `${chartData.components.knowledgeBase.documents.count} added document`,
      },
      position: { x: 0, y: 0 },
    });

    flowNodes.push({
      id: 'workflows',
      type: 'agentChart',
      data: {
        label: 'Workflows',
        status: chartData.components.knowledgeBase.workflows.status,
      },
      position: { x: 0, y: 0 },
    });

    // Edges
    flowEdges.push({
      id: 'e-agent-ai-model',
      source: 'agent',
      target: 'ai-model',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6b7280', strokeWidth: 2 },
    });

    flowEdges.push({
      id: 'e-agent-knowledge-base',
      source: 'agent',
      target: 'knowledge-base',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6b7280', strokeWidth: 2 },
    });

    flowEdges.push({
      id: 'e-agent-tools',
      source: 'agent',
      target: 'tools',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6b7280', strokeWidth: 2 },
    });

    flowEdges.push({
      id: 'e-knowledge-base-domain-knowledge',
      source: 'knowledge-base',
      target: 'domain-knowledge',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6b7280', strokeWidth: 1 },
    });

    flowEdges.push({
      id: 'e-knowledge-base-documents',
      source: 'knowledge-base',
      target: 'documents',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6b7280', strokeWidth: 1 },
    });

    flowEdges.push({
      id: 'e-knowledge-base-workflows',
      source: 'knowledge-base',
      target: 'workflows',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#6b7280', strokeWidth: 1 },
    });

    const layoutedNodes = getLayoutedElements(flowNodes, flowEdges, 'TB');
    return { nodes: layoutedNodes, edges: flowEdges };
  }, [chartData, agent?.id]);

  const nodeTypes = {
    agentChart: AgentChartNode,
  };

  if (!agent) {
    return (
      <div
        className={`flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200 ${className}`}
      >
        <div className="text-gray-500">No agent selected</div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={`flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-gray-200 ${className}`}
      >
        <div className="text-gray-500">Loading agent overview...</div>
      </div>
    );
  }

  return (
    <div className={`h-[100%] min-h-140 w-full ${className}`}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        proOptions={{ hideAttribution: true }}
        className="bg-gray-50"
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default AgentOverviewChart;
