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
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Step 2: Get agent plan
      setExecutionStep('planning');
      const plan = await hvacApi.createPlan(env);
      setAgentPlan(plan);
      await new Promise(resolve => setTimeout(resolve, 800));
      
      // Step 3: Validate plan
      setExecutionStep('validation');
      const feedback = await hvacApi.validatePlan(env, plan);
      setFeedback(feedback);
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setExecutionStep('complete');
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Unknown error');
      setExecutionStep('idle');
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError, setExecutionStep, setEnvironment, setAgentPlan, setFeedback]);
  
  const loadPolicies = useCallback(async () => {
    try {
      const { policies } = await hvacApi.getPolicies();
      setPolicies(policies);
    } catch (error) {
      console.error('Failed to load policies:', error);
    }
  }, [setPolicies]);
  
  const reset = useCallback(() => {
    store.reset();
  }, [store]);
  
  return { runFlow, loadPolicies, reset, ...store };
}

