import { create } from 'zustand';
import type { Environment, AgentPlan, Feedback, ExecutionStep } from '@/types/hvac';

interface HVACState {
  environment: Environment | null;
  agentPlan: AgentPlan | null;
  feedback: Feedback | null;
  executionStep: ExecutionStep;
  policies: string[];
  isLoading: boolean;
  error: string | null;
  
  setEnvironment: (env: Environment) => void;
  setAgentPlan: (plan: AgentPlan) => void;
  setFeedback: (feedback: Feedback) => void;
  setExecutionStep: (step: ExecutionStep) => void;
  setPolicies: (policies: string[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  reset: () => void;
}

export const useHVACStore = create<HVACState>((set) => ({
  environment: null,
  agentPlan: null,
  feedback: null,
  executionStep: 'idle',
  policies: [],
  isLoading: false,
  error: null,
  
  setEnvironment: (environment) => set({ environment }),
  setAgentPlan: (agentPlan) => set({ agentPlan }),
  setFeedback: (feedback) => set({ feedback }),
  setExecutionStep: (executionStep) => set({ executionStep }),
  setPolicies: (policies) => set({ policies }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  reset: () => set({
    environment: null,
    agentPlan: null,
    feedback: null,
    executionStep: 'idle',
    error: null
  }),
}));

