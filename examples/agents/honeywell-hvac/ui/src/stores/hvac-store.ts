import { create } from 'zustand';
import type {
  Environment,
  AgentPlan,
  Feedback,
  ExecutionStep,
  AcquisitiveLearning,
  EpisodicLearning,
  Session,
  LearningMetrics,
  ComparisonResults,
} from '@/types/hvac';

interface HVACState {
  environment: Environment | null;
  agentPlan: AgentPlan | null;
  feedback: Feedback | null;
  executionStep: ExecutionStep;
  // Learning state (replaces policies)
  currentSession: Session | null;
  acquisitiveLearnings: AcquisitiveLearning[];
  episodicLearning: EpisodicLearning | null;
  learningMetrics: LearningMetrics | null;
  currentExecutionLearning: AcquisitiveLearning | null;
  isLoading: boolean;
  error: string | null;
  comparisonMode: boolean;
  comparisonResults: ComparisonResults | null;
  isFadingOut: boolean;

  setEnvironment: (env: Environment) => void;
  setAgentPlan: (plan: AgentPlan) => void;
  setFeedback: (feedback: Feedback) => void;
  setExecutionStep: (step: ExecutionStep) => void;
  setCurrentSession: (session: Session | null) => void;
  setAcquisitiveLearnings: (learnings: AcquisitiveLearning[]) => void;
  removeAcquisitiveLearning: (loopId: string) => void;
  setEpisodicLearning: (learning: EpisodicLearning | null) => void;
  setLearningMetrics: (metrics: LearningMetrics | null) => void;
  setCurrentExecutionLearning: (learning: AcquisitiveLearning | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setComparisonMode: (value: boolean) => void;
  setComparisonResults: (results: ComparisonResults | null) => void;
  setIsFadingOut: (value: boolean) => void;
  reset: () => void;
}

export const useHVACStore = create<HVACState>((set) => ({
  environment: null,
  agentPlan: null,
  feedback: null,
  executionStep: 'idle',
  currentSession: null,
  acquisitiveLearnings: [],
  episodicLearning: null,
  learningMetrics: null,
  currentExecutionLearning: null,
  isLoading: false,
  error: null,
  comparisonMode: false,
  comparisonResults: null,
  isFadingOut: false,

  setEnvironment: (environment) => set({ environment }),
  setAgentPlan: (agentPlan) => set({ agentPlan }),
  setFeedback: (feedback) => set({ feedback }),
  setExecutionStep: (executionStep) => set({ executionStep }),
  setCurrentSession: (currentSession) => set({ currentSession }),
  setAcquisitiveLearnings: (acquisitiveLearnings) => set({ acquisitiveLearnings }),
  removeAcquisitiveLearning: (loopId) =>
    set((state) => {
      const filtered = state.acquisitiveLearnings.filter((l) => l.loop_id !== loopId);
      // Also clear currentExecutionLearning if it matches the deleted one
      const clearedCurrent =
        state.currentExecutionLearning?.loop_id === loopId
          ? null
          : state.currentExecutionLearning;
      return {
        acquisitiveLearnings: filtered,
        currentExecutionLearning: clearedCurrent,
      };
    }),
  setEpisodicLearning: (episodicLearning) => set({ episodicLearning }),
  setLearningMetrics: (learningMetrics) => set({ learningMetrics }),
  setCurrentExecutionLearning: (currentExecutionLearning) => set({ currentExecutionLearning }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),
  setComparisonMode: (comparisonMode) => set({ comparisonMode }),
  setComparisonResults: (comparisonResults) => set({ comparisonResults }),
  setIsFadingOut: (isFadingOut) => set({ isFadingOut }),
  reset: () =>
    set({
      environment: null,
      agentPlan: null,
      feedback: null,
      executionStep: 'idle',
      episodicLearning: null,
      currentExecutionLearning: null,
      error: null,
      comparisonResults: null,
    }),
}));
