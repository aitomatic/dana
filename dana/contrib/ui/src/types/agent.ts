export interface Agent {
  id: string;
  name: string;
  description?: string;
  avatar: string;
  general_agent_config: {
    dana_code: string;
  };
}

export interface DanaAgentForm {
  name: string;
  description?: string;
  avatar: string;
  general_agent_config: {
    dana_code: string;
  };
}
