// Agent Types matching the API schemas
export interface AgentBase {
  name: string;
  description: string;
  config: Record<string, any>;
}

export interface AgentCreate extends AgentBase {
  // Same as AgentBase for creation
}

export interface AgentRead extends AgentBase {
  id: number;
}

// Agent API Response Types
export interface AgentListResponse {
  agents: AgentRead[];
  total: number;
  skip: number;
  limit: number;
}

export interface AgentCreateResponse {
  agent: AgentRead;
  message: string;
}

export interface AgentUpdateResponse {
  agent: AgentRead;
  message: string;
}

export interface AgentDeleteResponse {
  message: string;
}

// Agent Filter Types
export interface AgentFilters {
  search?: string;
  skip?: number;
  limit?: number;
}

// Agent Store State
export interface AgentState {
  agents: AgentRead[];
  selectedAgent: AgentRead | null;
  isLoading: boolean;
  isCreating: boolean;
  isUpdating: boolean;
  isDeleting: boolean;
  error: string | null;
  total: number;
  skip: number;
  limit: number;
  isCreateAgentDialogOpen: boolean;
  isEditAgentDialogOpen: boolean;
  isDeleteAgentDialogOpen: boolean;

  // Actions
  fetchAgents: (filters?: AgentFilters) => Promise<void>;
  fetchAgent: (agentId: number) => Promise<AgentRead>;
  createAgent: (agent: AgentCreate) => Promise<AgentRead>;
  updateAgent: (agentId: number, agent: AgentCreate) => Promise<AgentRead>;
  deleteAgent: (agentId: number) => Promise<void>;
  setSelectedAgent: (agent: AgentRead | null) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

// Legacy types for backward compatibility
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
