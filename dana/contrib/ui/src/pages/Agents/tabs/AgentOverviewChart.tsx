import React, { useMemo, useEffect } from 'react';
import ReactFlow, { Controls, MarkerType } from 'reactflow';
import type { Node as FlowNode, Edge } from 'reactflow';
import dagre from 'dagre';
import 'reactflow/dist/style.css';
import AgentChartNode from './AgentChartNode';
import type { AgentOverviewChartProps, AgentChartData } from './types/agent-chart';
import { useKnowledgeStore } from '@/stores/knowledge-store';
import { useDocumentStore } from '@/stores/document-store';

const nodeWidth = 250;
const nodeHeight = 100;
const mainNodeSize = 96;

function getLayoutedElements(nodes: FlowNode[], edges: Edge[], direction: 'TB' | 'LR' = 'TB') {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({
    rankdir: direction,
    nodesep: 90, // Horizontal separation between nodes on same rank
    ranksep: 80, // Reduced vertical separation between ranks
    marginx: 60, // Margin on x-axis
    marginy: 40, // Reduced top/bottom margin
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

    // Custom positioning for proper layout
    if (node.id === 'ai-model') {
      const topRowY = 74; // Fixed Y position for top row
      node.position = {
        x: nodeWithPosition.x - width / 2 - 320, // Move further left
        y: topRowY,
      };
    } else if (node.id === 'agent') {
      // Agent should be centered between Knowledge Base and Tools
      const agentRowY = 50; // Same row as AI Model
      node.position = {
        x: nodeWithPosition.x - width / 2, // Center position
        y: agentRowY,
      };
    } else if (node.id === 'knowledge-base') {
      node.position = {
        x: nodeWithPosition.x - width / 2 - 150, // Position left of center
        y: nodeWithPosition.y - height / 2 - 60, // Move closer to Agent
      };
    } else if (node.id === 'tools') {
      node.position = {
        x: nodeWithPosition.x - width / 2 + 150, // Position right of center
        y: nodeWithPosition.y - height / 2 - 60, // Move closer to Agent
      };
    } else {
      node.position = {
        x: nodeWithPosition.x - width / 2,
        y: nodeWithPosition.y - height / 2,
      };
    }
    return node;
  });
}

const AgentOverviewChart: React.FC<AgentOverviewChartProps> = ({ agent, className = '' }) => {
  // Use centralized knowledge store
  const { domainKnowledge, knowledgeStatus, setCurrentAgent } = useKnowledgeStore();

  // Use centralized document store
  const { documents, isLoading: documentsLoading, fetchDocuments } = useDocumentStore();

  // Update current agent when component mounts or agent changes
  useEffect(() => {
    if (agent?.id) {
      setCurrentAgent(agent.id);
    } else {
      setCurrentAgent(null);
    }
  }, [agent?.id, setCurrentAgent]);

  // Fetch agent-specific documents when agent changes
  useEffect(() => {
    if (agent?.id) {
      fetchDocuments({ agent_id: parseInt(agent.id.toString()) });
    }
  }, [agent?.id, fetchDocuments]);

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

    // Count domain knowledge items from knowledge status (same as DomainKnowledgeTree)
    const domainKnowledgeCount = knowledgeStatus?.topics?.length || 0;

    // Check if knowledge is currently being generated for Domain Knowledge status
    const inProgressCount =
      knowledgeStatus?.topics?.filter((topic) => topic.status === 'in_progress').length || 0;
    const isGeneratingKnowledge = inProgressCount > 0;

    // Count documents from store (filtered for current agent)
    const agentDocuments = documents.filter(
      (doc) => doc.agent_id?.toString() === agent.id.toString(),
    );
    const documentsCount = agentDocuments.length;

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
            status: isGeneratingKnowledge
              ? 'loading'
              : domainKnowledgeCount > 0
                ? 'active'
                : 'empty',
          },
          documents: {
            count: documentsCount,
            status: documentsLoading ? 'loading' : documentsCount > 0 ? 'active' : 'empty',
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
  }, [agent, domainKnowledge, knowledgeStatus, documents, documentsLoading]);

  const { nodes, edges } = useMemo(() => {
    const flowNodes: FlowNode[] = [];
    const flowEdges: Edge[] = [];

    // Get in-progress count for Knowledge Base loading status
    const inProgressCount =
      knowledgeStatus?.topics?.filter((topic) => topic.status === 'in_progress').length || 0;
    const isGeneratingKnowledge = inProgressCount > 0;
    const isKnowledgeBaseLoading = isGeneratingKnowledge || documentsLoading;

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
        isMain: false, // Same level as agent
      },
      position: { x: 0, y: 0 },
    });

    // Knowledge Base node
    flowNodes.push({
      id: 'knowledge-base',
      type: 'agentChart',
      data: {
        label: 'Knowledge Base',
        status: isKnowledgeBaseLoading ? 'loading' : 'active',
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
        description: `${chartData.components.knowledgeBase.domainKnowledge.count} items`,
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
        description: `${chartData.components.knowledgeBase.documents.count} ${chartData.components.knowledgeBase.documents.count === 1 ? 'document' : 'documents'}`,
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

    // Right to left connection: AI Model to Agent
    flowEdges.push({
      id: 'e-ai-model-agent',
      source: 'ai-model',
      target: 'agent',
      sourceHandle: 'right',
      targetHandle: 'left',
      style: {
        stroke: '#6b7280',
        strokeWidth: 2,
      },
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
  }, [chartData, agent?.id, knowledgeStatus, documentsLoading]);

  const nodeTypes = useMemo(
    () => ({
      agentChart: AgentChartNode,
    }),
    [],
  );

  if (!agent) {
    return (
      <div
        className={`flex justify-center items-center h-64 bg-gray-50 rounded-lg border border-gray-200 ${className}`}
      >
        <div className="text-gray-500">No agent selected</div>
      </div>
    );
  }

  return (
    <div className={`h-[100%] min-h-140 w-full ${className}`}>
      <style>
        {`
          /* Hide ONLY the connection handles (black dots) - keep edges/lines visible */
          .agent-overview-flow .react-flow__handle {
            opacity: 0 !important;
            pointer-events: none !important;
          }
        `}
      </style>
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
        className="bg-gray-50 agent-overview-flow"
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      >
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default AgentOverviewChart;
