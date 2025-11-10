import axios from 'axios';
import type {
  Environment,
  AgentPlan,
  Feedback,
  AcquisitiveLearning,
  EpisodicLearning,
  Session,
  LearningMetrics,
  StoredFeedback,
} from '@/types/hvac';

const API_BASE = '/api/hvac'; // Will be proxied by Vite

export const hvacApi = {
  async generateEnvironment(): Promise<Environment> {
    const { data } = await axios.post(`${API_BASE}/environment`);
    return data;
  },

  async createPlan(
    environment: Environment,
    sessionId?: string,
    withLearner?: boolean,
  ): Promise<AgentPlan> {
    const { data } = await axios.post(`${API_BASE}/plan`, {
      environment,
      session_id: sessionId,
      with_learner: withLearner,
    });
    return data;
  },

  async validatePlan(environment: Environment, plan: AgentPlan): Promise<Feedback> {
    const { data } = await axios.post(`${API_BASE}/validate`, { environment, plan });
    return data;
  },

  // Session management
  async createSession(sessionId?: string): Promise<Session> {
    const { data } = await axios.post(`${API_BASE}/sessions`, {
      session_id: sessionId,
    });
    return data;
  },

  async listSessions(): Promise<{ sessions: Session[] }> {
    const { data } = await axios.get(`${API_BASE}/sessions`);
    return data;
  },

  // Learning endpoints
  async getAcquisitiveLearnings(
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<{ learnings: AcquisitiveLearning[]; count: number }> {
    const { data } = await axios.get(`${API_BASE}/learnings/acquisitive`, {
      params: { session_id: sessionId },
    });
    return data;
  },

  async deleteAcquisitiveLearning(
    loopId: string,
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<{ success: boolean; message: string }> {
    const { data } = await axios.delete(`${API_BASE}/learnings/acquisitive/${loopId}`, {
      params: { session_id: sessionId },
    });
    return data;
  },

  async getEpisodicLearning(
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<EpisodicLearning> {
    const { data } = await axios.get(`${API_BASE}/learnings/episodic`, {
      params: { session_id: sessionId },
    });
    return data;
  },

  async triggerEpisodicLearning(
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<{ success: boolean; content: string; timestamp: string; session_id: string }> {
    const { data } = await axios.post(`${API_BASE}/learnings/episodic`, null, {
      params: { session_id: sessionId },
    });
    return data;
  },

  async getStoredFeedback(
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<StoredFeedback> {
    const { data } = await axios.get(`${API_BASE}/feedback`, {
      params: { session_id: sessionId },
    });
    return data;
  },

  async saveFeedback(
    feedback: string,
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<{ success: boolean; timestamp: string; session_id: string }> {
    const { data } = await axios.post(`${API_BASE}/feedback`, {
      feedback,
      session_id: sessionId,
    });
    return data;
  },

  async getLearningMetrics(
    sessionId: string = 'hvac-agent-session-001',
  ): Promise<LearningMetrics> {
    const { data } = await axios.get(`${API_BASE}/learnings/metrics`, {
      params: { session_id: sessionId },
    });
    return data;
  },
};
