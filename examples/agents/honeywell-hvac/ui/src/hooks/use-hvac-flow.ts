import { useCallback, useEffect } from 'react';
import { useHVACStore } from '@/stores/hvac-store';
import { hvacApi } from '@/lib/hvac-api';

export function useHVACFlow() {
  const {
    setLoading,
    setError,
    setExecutionStep,
    setEnvironment,
    setAgentPlan,
    setFeedback,
    setCurrentSession,
    setAcquisitiveLearnings,
    setEpisodicLearning,
    setLearningMetrics,
    setCurrentExecutionLearning,
    currentSession,
    reset: storeReset,
    ...store
  } = useHVACStore();

  // Initialize session on mount
  useEffect(() => {
    const initializeSession = async () => {
      if (!currentSession) {
        try {
          const session = await hvacApi.createSession('hvac-agent-session-001');
          setCurrentSession(session);
          await loadLearnings(session.session_id);
        } catch (error) {
          console.error('Failed to initialize session:', error);
        }
      }
    };
    initializeSession();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadLearnings = useCallback(
    async (sessionId: string) => {
      try {
        // Load acquisitive learnings
        const { learnings } = await hvacApi.getAcquisitiveLearnings(sessionId);
        setAcquisitiveLearnings(learnings);

        // Load episodic learning
        const episodicLearning = await hvacApi.getEpisodicLearning(sessionId);
        if (episodicLearning.content) {
          setEpisodicLearning(episodicLearning);
        }

        // Load learning metrics
        const metrics = await hvacApi.getLearningMetrics(sessionId);
        setLearningMetrics(metrics);
      } catch (error) {
        console.error('Failed to load learnings:', error);
      }
    },
    [setAcquisitiveLearnings, setEpisodicLearning, setLearningMetrics],
  );

  const runFlow = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const sessionId = currentSession?.session_id || 'hvac-agent-session-001';

      // Step 1: Generate environment
      setExecutionStep('environment');
      const env = await hvacApi.generateEnvironment();
      setEnvironment(env);
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Step 2: Get agent plan (this triggers acquisitive learning automatically)
      setExecutionStep('planning');
      const previousLearningsCount = store.acquisitiveLearnings.length;
      const plan = await hvacApi.createPlan(env, sessionId);
      setAgentPlan(plan);
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Step 3: Validate plan
      setExecutionStep('validation');
      const feedback = await hvacApi.validatePlan(env, plan);
      setFeedback(feedback);

      // Save feedback
      try {
        await hvacApi.saveFeedback(JSON.stringify(feedback, null, 2), sessionId);
      } catch (error) {
        console.error('Failed to save feedback:', error);
      }

      await new Promise((resolve) => setTimeout(resolve, 500));

      // Step 4: Load acquisitive learning (highlight new learning)
      setExecutionStep('learning');
      try {
        // Reload learnings to get the latest one
        const { learnings } = await hvacApi.getAcquisitiveLearnings(sessionId);
        setAcquisitiveLearnings(learnings);

        // Highlight the newest learning if a new one was created
        if (learnings.length > previousLearningsCount && learnings.length > 0) {
          const newestLearning = learnings[0]; // Sorted newest first
          setCurrentExecutionLearning(newestLearning);
        }

        // Update learning metrics
        const metrics = await hvacApi.getLearningMetrics(sessionId);
        setLearningMetrics(metrics);
      } catch (error) {
        console.error('Failed to load learnings:', error);
      }
      await new Promise((resolve) => setTimeout(resolve, 800));

      setExecutionStep('complete');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
      setExecutionStep('idle');
    } finally {
      setLoading(false);
    }
  }, [
    setLoading,
    setError,
    setExecutionStep,
    setEnvironment,
    setAgentPlan,
    setFeedback,
    setAcquisitiveLearnings,
    setCurrentExecutionLearning,
    setLearningMetrics,
    currentSession,
    store.acquisitiveLearnings.length,
  ]);

  const loadLearningsForSession = useCallback(
    async (sessionId: string) => {
      await loadLearnings(sessionId);
    },
    [loadLearnings],
  );

  const reset = useCallback(() => {
    storeReset();
    setCurrentExecutionLearning(null);
  }, [storeReset, setCurrentExecutionLearning]);

  return {
    runFlow,
    loadLearnings: loadLearningsForSession,
    reset,
    ...store,
  };
}
