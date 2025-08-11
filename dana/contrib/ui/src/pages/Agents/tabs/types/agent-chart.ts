export interface AgentChartNode {
  id: string;
  type: 'agent' | 'component' | 'subcomponent';
  data: {
    label: string;
    icon?: React.ReactNode;
    status?: 'active' | 'coming-soon' | 'empty' | 'loading';
    count?: number;
    description?: string;
    isMain?: boolean;
  };
  position: { x: number; y: number };
}

export interface AgentChartData {
  agent: {
    name: string;
    model?: string;
    domain?: string;
    topic?: string;
  };
  components: {
    aiModel: {
      name: string;
      status: 'active' | 'coming-soon';
    };
    knowledgeBase: {
      domainKnowledge: {
        count: number;
        status: 'active' | 'empty' | 'loading';
      };
      documents: {
        count: number;
        status: 'active' | 'empty';
      };
      workflows: {
        status: 'coming-soon';
      };
    };
    tools: {
      status: 'coming-soon';
    };
  };
}

export interface AgentOverviewChartProps {
  agent: any | null;
  className?: string;
}
