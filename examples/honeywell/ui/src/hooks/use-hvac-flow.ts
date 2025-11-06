import { useCallback } from 'react';
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
    setPolicies,
    setNewlyLearnedPolicies,
    setLearningAnalysis,
    policies,
    reset: storeReset,
    ...store
  } = useHVACStore();

  const runFlow = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Step 1: Generate environment
      setExecutionStep('environment');
      const env = await hvacApi.generateEnvironment();
      setEnvironment(env);
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Step 2: Get agent plan
      setExecutionStep('planning');
      const plan = await hvacApi.createPlan(env);
      setAgentPlan(plan);
      await new Promise((resolve) => setTimeout(resolve, 800));

      // Step 3: Validate plan
      setExecutionStep('validation');
      const feedback = await hvacApi.validatePlan(env, plan);
      setFeedback(feedback);
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Step 4: Learning Agent Analysis
      setExecutionStep('learning');
      try {
        const learningAnalysis = await hvacApi.analyzeFeedback(env, plan, feedback);
        setLearningAnalysis(learningAnalysis);
        // Reload policies if new ones were learned
        if (learningAnalysis.success && learningAnalysis.policies.length > 0) {
          const previousPolicies = new Set(policies);
          const { policies: updatedPolicies } = await hvacApi.getPolicies();
          setPolicies(updatedPolicies);

          // Identify newly learned policies
          const newlyLearned = updatedPolicies.filter((policy) => !previousPolicies.has(policy));
          setNewlyLearnedPolicies(newlyLearned);
        } else {
          setNewlyLearnedPolicies([]);
        }
      } catch (error) {
        console.error('Learning agent analysis failed:', error);
        // Don't fail the whole flow if learning fails
        setLearningAnalysis({
          success: false,
          insights: '',
          policies: [],
          error: error instanceof Error ? error.message : 'Unknown error',
        });
        setNewlyLearnedPolicies([]);
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
    setLearningAnalysis,
    setPolicies,
    setNewlyLearnedPolicies,
    policies,
  ]);

  const loadPolicies = useCallback(async () => {
    try {
      const { policies } = await hvacApi.getPolicies();
      setPolicies(policies);
    } catch (error) {
      console.error('Failed to load policies:', error);
    }
  }, [setPolicies]);

  const reset = useCallback(() => {
    storeReset();
  }, [storeReset]);

  return { runFlow, loadPolicies, reset, ...store };
}
