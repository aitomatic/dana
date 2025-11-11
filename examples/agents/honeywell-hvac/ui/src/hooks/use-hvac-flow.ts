import { useCallback, useEffect } from 'react';
import { useHVACStore } from '@/stores/hvac-store';
import { hvacApi, DEFAULT_SESSION_ID } from '@/lib/hvac-api';
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
    setComparisonResults,
    setIsFadingOut,
    currentSession,
    reset: storeReset,
    ...store
  } = useHVACStore();

  // Initialize session on mount
  useEffect(() => {
    const initializeSession = async () => {
      if (!currentSession) {
        try {
          const session = await hvacApi.createSession(DEFAULT_SESSION_ID);
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

  // Extract WITHOUT learning path
  const runWithoutLearningPath = useCallback(
    async (env: any, sessionId: string): Promise<{ plan: AgentPlan | null; feedback: Feedback | null }> => {
      try {
        const suffixedSessionId = `${sessionId}-False`;
        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Starting path');
        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Original sessionId:', sessionId);
        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Using suffixed sessionId:', suffixedSessionId);
        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Calling createPlan with with_learner=false');
        const plan = await hvacApi.createPlan(env, suffixedSessionId, false);
        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Received plan:', plan);
        await new Promise((resolve) => setTimeout(resolve, 800));

        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Validating plan');
        const feedback = await hvacApi.validatePlan(env, plan, suffixedSessionId, false);
        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Received feedback:', feedback);
        await new Promise((resolve) => setTimeout(resolve, 500));

        console.log('[COMPARISON MODE] [WITHOUT LEARNING] Path completed');
        return { plan, feedback };
      } catch (error) {
        console.error('[COMPARISON MODE] [WITHOUT LEARNING] Path failed:', error);
        return { plan: null, feedback: null };
      }
    },
    [],
  );

  // Extract WITH learning path (excluding learning steps)
  const runWithLearningPath = useCallback(
    async (env: any, sessionId: string): Promise<{ plan: AgentPlan | null; feedback: Feedback | null }> => {
      try {
        const suffixedSessionId = `${sessionId}-True`;
        console.log('[COMPARISON MODE] [WITH LEARNING] Starting path');
        console.log('[COMPARISON MODE] [WITH LEARNING] Original sessionId:', sessionId);
        console.log('[COMPARISON MODE] [WITH LEARNING] Using suffixed sessionId:', suffixedSessionId);
        console.log('[COMPARISON MODE] [WITH LEARNING] Calling createPlan with with_learner=true');
        const plan = await hvacApi.createPlan(env, suffixedSessionId, true);
        console.log('[COMPARISON MODE] [WITH LEARNING] Received plan:', plan);
        await new Promise((resolve) => setTimeout(resolve, 800));

        console.log('[COMPARISON MODE] [WITH LEARNING] Validating plan');
        const feedback = await hvacApi.validatePlan(env, plan, suffixedSessionId, true);
        console.log('[COMPARISON MODE] [WITH LEARNING] Received feedback:', feedback);

        // Save feedback for the WITH learning run (using suffixed sessionId to match the path)
        try {
          await hvacApi.saveFeedback(JSON.stringify(feedback, null, 2), suffixedSessionId);
          console.log('[COMPARISON MODE] [WITH LEARNING] Saved feedback with suffixed sessionId:', suffixedSessionId);
        } catch (error) {
          console.error('[COMPARISON MODE] [WITH LEARNING] Failed to save feedback:', error);
        }

        await new Promise((resolve) => setTimeout(resolve, 500));
        console.log('[COMPARISON MODE] [WITH LEARNING] Path completed');
        return { plan, feedback };
      } catch (error) {
        console.error('[COMPARISON MODE] [WITH LEARNING] Path failed:', error);
        return { plan: null, feedback: null };
      }
    },
    [],
  );

  const runFlow = useCallback(async () => {
    try {
      // Clear previous run's data to hide cards immediately
      setAgentPlan(null);
      setFeedback(null);
      setEpisodicLearning(null);
      setComparisonResults(null);
      
      setLoading(true);
      setError(null);

      const sessionId = currentSession?.session_id || DEFAULT_SESSION_ID;

      // Step 1: Use existing environment from store (or fallback to default)
      setExecutionStep('environment');
      const env = store.environment;
      if (!env) {
        setError('No environment data available. Please fetch environment data first.');
        setLoading(false);
        setExecutionStep('idle');
        return;
      }
      // Skip delay since we're using existing environment

      if (store.comparisonMode) {
        // Comparison Mode: Run both paths in parallel
        console.log('[COMPARISON MODE] Starting parallel comparison mode execution');
        console.log('[COMPARISON MODE] Environment:', env);
        
        // Track episodic learning content for the "with learning" session BEFORE the run starts
        // This will be used to detect if episodic learning was updated during this run
        const withLearningSessionId = `${sessionId}-True`;
        let previousEpisodicContent = '';
        try {
          const previousEpisodic = await hvacApi.getEpisodicLearning(withLearningSessionId);
          previousEpisodicContent = previousEpisodic?.content || '';
          console.log('[COMPARISON MODE] Previous episodic learning content length:', previousEpisodicContent.length);
        } catch (error) {
          console.error('[COMPARISON MODE] Failed to load previous episodic learning:', error);
          // If we can't load, assume empty (no previous learning)
          previousEpisodicContent = '';
        }
        
        const comparisonResults: {
          withoutLearning: { plan: AgentPlan | null; feedback: Feedback | null };
          withLearning: { plan: AgentPlan | null; feedback: Feedback | null };
        } = {
          withoutLearning: { plan: null, feedback: null },
          withLearning: { plan: null, feedback: null },
        };

        // Execute both paths in parallel
        setExecutionStep('planning');
        console.log('[COMPARISON MODE] Executing both paths in parallel...');
        
        const [resultWithoutLearning, resultWithLearning] = await Promise.all([
          runWithoutLearningPath(env, sessionId),
          runWithLearningPath(env, sessionId),
        ]);

        // Update comparison results with parallel execution results
        comparisonResults.withoutLearning = resultWithoutLearning;
        comparisonResults.withLearning = resultWithLearning;

        console.log('[COMPARISON MODE] Both paths completed');
        console.log('[COMPARISON MODE] Plans are identical?', JSON.stringify(resultWithoutLearning.plan) === JSON.stringify(resultWithLearning.plan));
        console.log('[COMPARISON MODE] Feedbacks are identical?', JSON.stringify(resultWithoutLearning.feedback) === JSON.stringify(resultWithLearning.feedback));

        // Store comparison results immediately so components render as soon as they're ready
        // This enables incremental rendering - plans and feedbacks appear immediately when available
        setComparisonResults(comparisonResults);

        // Both paths have completed validation
        setExecutionStep('validation');
        await new Promise((resolve) => setTimeout(resolve, 500));

        // Step 4: Trigger episodic learning and load all learnings (after both paths complete)
        // Use suffixed sessionId for WITH learning path (already defined above)
        setExecutionStep('learning');
        try {
          // Trigger episodic learning
          try {
            await hvacApi.triggerEpisodicLearning(withLearningSessionId);
            console.log('[COMPARISON MODE] Triggered episodic learning with suffixed sessionId:', withLearningSessionId);
          } catch (error) {
            console.error('Failed to trigger episodic learning:', error);
          }

          // Reload acquisitive learnings (still needed for other parts of UI)
          const { learnings } = await hvacApi.getAcquisitiveLearnings(withLearningSessionId);
          setAcquisitiveLearnings(learnings);

          // Reload episodic learning after triggering
          try {
            const episodicLearning = await hvacApi.getEpisodicLearning(withLearningSessionId);
            if (episodicLearning.content) {
              // Only update if content has changed (new learning detected)
              if (episodicLearning.content !== previousEpisodicContent) {
                setEpisodicLearning(episodicLearning);
                console.log('[COMPARISON MODE] New episodic learning detected, content changed');
              } else {
                console.log('[COMPARISON MODE] Episodic learning unchanged');
              }
            }
          } catch (error) {
            console.error('Failed to load episodic learning:', error);
          }

          // Update learning metrics
          const metrics = await hvacApi.getLearningMetrics(withLearningSessionId);
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
        console.log('[COMPARISON MODE] Parallel comparison mode execution complete');
      } else {
        // Normal Mode: Single run with learning enabled
        console.log('[NORMAL MODE] Starting normal mode execution with learning enabled');
        setExecutionStep('planning');
        
        // Track episodic learning content BEFORE the run starts
        // This will be used to detect if episodic learning was updated during this run
        let previousEpisodicContent = '';
        try {
          const previousEpisodic = await hvacApi.getEpisodicLearning(sessionId);
          previousEpisodicContent = previousEpisodic?.content || '';
          console.log('[NORMAL MODE] Previous episodic learning content length:', previousEpisodicContent.length);
        } catch (error) {
          console.error('[NORMAL MODE] Failed to load previous episodic learning:', error);
          previousEpisodicContent = '';
        }
        console.log('[NORMAL MODE] Calling createPlan with with_learner=true');
        const plan = await hvacApi.createPlan(env, sessionId, true);
        console.log('[NORMAL MODE] Received plan:', plan);
        setAgentPlan(plan);
        await new Promise((resolve) => setTimeout(resolve, 800));

        // Step 3: Validate plan
        setExecutionStep('validation');
        const feedback = await hvacApi.validatePlan(env, plan, sessionId, true);
        setFeedback(feedback);

        // Save feedback
        try {
          await hvacApi.saveFeedback(JSON.stringify(feedback, null, 2), sessionId);
        } catch (error) {
          console.error('Failed to save feedback:', error);
        }

        await new Promise((resolve) => setTimeout(resolve, 500));

        // Step 4: Trigger episodic learning and load all learnings
        setExecutionStep('learning');
        try {
          // Trigger episodic learning
          try {
            await hvacApi.triggerEpisodicLearning(sessionId);
            console.log('[NORMAL MODE] Triggered episodic learning');
          } catch (error) {
            console.error('Failed to trigger episodic learning:', error);
          }

          // Reload acquisitive learnings (still needed for other parts of UI)
          const { learnings } = await hvacApi.getAcquisitiveLearnings(sessionId);
          setAcquisitiveLearnings(learnings);

          // Reload episodic learning after triggering
          try {
            const episodicLearning = await hvacApi.getEpisodicLearning(sessionId);
            if (episodicLearning.content) {
              // Only update if content has changed (new learning detected)
              if (episodicLearning.content !== previousEpisodicContent) {
                setEpisodicLearning(episodicLearning);
                console.log('[NORMAL MODE] New episodic learning detected, content changed');
              } else {
                console.log('[NORMAL MODE] Episodic learning unchanged');
              }
            }
          } catch (error) {
            console.error('Failed to load episodic learning:', error);
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
    setLearningMetrics,
    setComparisonResults,
    setEpisodicLearning,
    currentSession,
    store.comparisonMode,
    store.environment,
    runWithoutLearningPath,
    runWithLearningPath,
  ]);

  const fetchEnvironment = useCallback(async () => {
    try {
      setError(null);
      // Start fade-out animation
      setIsFadingOut(true);
      
      // Wait for fade-out animation to complete (500ms)
      await new Promise((resolve) => setTimeout(resolve, 500));
      
      // Clear agent plan, feedback, and learning data after animation
      setAgentPlan(null);
      setFeedback(null);
      setEpisodicLearning(null);
      setComparisonResults(null);
      setIsFadingOut(false);
      
      const env = await hvacApi.generateEnvironment();
      setEnvironment(env);
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch environment';
      setError(errorMessage);
      setIsFadingOut(false);
      console.error('Failed to fetch environment:', error);
    }
  }, [setEnvironment, setError, setAgentPlan, setFeedback, setEpisodicLearning, setComparisonResults, setIsFadingOut]);

  const loadLearningsForSession = useCallback(
    async (sessionId: string) => {
      await loadLearnings(sessionId);
    },
    [loadLearnings],
  );

  const reset = useCallback(() => {
    storeReset();
    setEpisodicLearning(null);
  }, [storeReset, setEpisodicLearning]);

  return {
    runFlow,
    fetchEnvironment,
    loadLearnings: loadLearningsForSession,
    reset,
    ...store,
  };
}
