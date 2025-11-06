import axios from 'axios';
import type { Environment, AgentPlan, Feedback, LearningAnalysis } from '@/types/hvac';

const API_BASE = '/api/hvac'; // Will be proxied by Vite

export const hvacApi = {
  async generateEnvironment(): Promise<Environment> {
    const { data } = await axios.post(`${API_BASE}/environment`);
    return data;
  },

  async createPlan(environment: Environment): Promise<AgentPlan> {
    const { data } = await axios.post(`${API_BASE}/plan`, { environment });
    return data;
  },

  async validatePlan(environment: Environment, plan: AgentPlan): Promise<Feedback> {
    const { data } = await axios.post(`${API_BASE}/validate`, { environment, plan });
    return data;
  },

  async getPolicies(): Promise<{ policies: string[]; count: number }> {
    const { data } = await axios.get(`${API_BASE}/policies`);
    return data;
  },

  async analyzeFeedback(
    environment: Environment,
    plan: AgentPlan,
    feedback: Feedback,
  ): Promise<LearningAnalysis> {
    const { data } = await axios.post(`${API_BASE}/analyze`, {
      environment,
      agent_plan: plan,
      feedback,
    });
    return data;
  },

  async deletePolicies(
    policies: string[],
  ): Promise<{ success: boolean; deleted_count: number; message: string }> {
    const { data } = await axios.post(`${API_BASE}/policies/delete`, { policies });
    return data;
  },
};
