import { useCallback, useEffect } from 'react';
import { useHVACStore } from '@/stores/hvac-store';
import { hvacApi } from '@/lib/hvac-api';
import type { AgentPlan, Feedback } from '@/types/hvac';

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
    setComparisonResults,
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
      // Clear previous run's data to hide cards immediately
      setAgentPlan(null);
      setFeedback(null);
      setCurrentExecutionLearning(null);
      setComparisonResults(null);
      
      setLoading(true);
      setError(null);

      const sessionId = currentSession?.session_id || 'hvac-agent-session-001';

      // Step 1: Generate environment (once, used for both runs in comparison mode)
      setExecutionStep('environment');
      const env = await hvacApi.generateEnvironment();
      setEnvironment(env);
      await new Promise((resolve) => setTimeout(resolve, 800));

      if (store.comparisonMode) {
        // Comparison Mode: Run twice sequentially
        console.log('[COMPARISON MODE] Starting comparison mode execution');
        console.log('[COMPARISON MODE] Environment:', env);
        const previousLearningsCount = store.acquisitiveLearnings.length;
        console.log('[COMPARISON MODE] Previous learnings count:', previousLearningsCount);
        
        const comparisonResults: {
          withoutLearning: { plan: AgentPlan | null; feedback: Feedback | null };
          withLearning: { plan: AgentPlan | null; feedback: Feedback | null };
        } = {
          withoutLearning: { plan: null, feedback: null },
          withLearning: { plan: null, feedback: null },
        };

        // First run: WITHOUT learning
        console.log('[COMPARISON MODE] ===== FIRST RUN: WITHOUT LEARNING =====');
        console.log('[COMPARISON MODE] Calling createPlan with with_learner=false');
        console.log('[COMPARISON MODE] Ensuring clean state for WITHOUT learning run');
        setExecutionStep('planning');
        const planWithoutLearning = await hvacApi.createPlan(env, sessionId, false);
        console.log('[COMPARISON MODE] Received plan WITHOUT learning:', planWithoutLearning);
        comparisonResults.withoutLearning.plan = planWithoutLearning;
        await new Promise((resolve) => setTimeout(resolve, 800));

        setExecutionStep('validation');
        console.log('[COMPARISON MODE] Validating plan WITHOUT learning');
        const feedbackWithoutLearning = await hvacApi.validatePlan(env, planWithoutLearning);
        console.log('[COMPARISON MODE] Received feedback WITHOUT learning:', feedbackWithoutLearning);
        comparisonResults.withoutLearning.feedback = feedbackWithoutLearning;
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Second run: WITH learning (using same environment)
        console.log('[COMPARISON MODE] ===== SECOND RUN: WITH LEARNING =====');
        console.log('[COMPARISON MODE] Calling createPlan with with_learner=true');
        setExecutionStep('planning');
        const planWithLearning = await hvacApi.createPlan(env, sessionId, true);
        console.log('[COMPARISON MODE] Received plan WITH learning:', planWithLearning);
        console.log('[COMPARISON MODE] Plans are identical?', JSON.stringify(planWithoutLearning) === JSON.stringify(planWithLearning));
        comparisonResults.withLearning.plan = planWithLearning;
        await new Promise((resolve) => setTimeout(resolve, 800));

        setExecutionStep('validation');
        console.log('[COMPARISON MODE] Validating plan WITH learning');
        const feedbackWithLearning = await hvacApi.validatePlan(env, planWithLearning);
        console.log('[COMPARISON MODE] Received feedback WITH learning:', feedbackWithLearning);
        console.log('[COMPARISON MODE] Feedbacks are identical?', JSON.stringify(feedbackWithoutLearning) === JSON.stringify(feedbackWithLearning));
        
        // Store feedback in comparison results
        comparisonResults.withLearning.feedback = feedbackWithLearning;
        console.log('[COMPARISON MODE] Stored feedback in comparisonResults.withLearning.feedback');

        // Save feedback for the WITH learning run
        try {
          await hvacApi.saveFeedback(JSON.stringify(feedbackWithLearning, null, 2), sessionId);
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

        // Store comparison results
        console.log('[COMPARISON MODE] Storing comparison results');
        console.log('[COMPARISON MODE] Final comparison results:', comparisonResults);
        setComparisonResults(comparisonResults);
        setExecutionStep('complete');
        console.log('[COMPARISON MODE] Comparison mode execution complete');
      } else {
        // Normal Mode: Single run with learning enabled
        console.log('[NORMAL MODE] Starting normal mode execution with learning enabled');
        setExecutionStep('planning');
        const previousLearningsCount = store.acquisitiveLearnings.length;
        console.log('[NORMAL MODE] Previous learnings count:', previousLearningsCount);
        console.log('[NORMAL MODE] Calling createPlan with with_learner=true');
        const plan = await hvacApi.createPlan(env, sessionId, true);
        console.log('[NORMAL MODE] Received plan:', plan);
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
      }
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
    setComparisonResults,
    currentSession,
    store.acquisitiveLearnings.length,
    store.comparisonMode,
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
