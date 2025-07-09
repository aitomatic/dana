export interface Agent {
  id: string;
  name: string;
  description?: string;
  avatar: string;
  general_agent_config: {
    dana_code: string;
  };
}

export type AgentSteps = 'general' | 'select-knowledge';

export interface DanaAgentForm {
  name: string;
  description?: string;
  avatar: string;
  general_agent_config: {
    dana_code: string;
  };
  step?: AgentSteps;
}
