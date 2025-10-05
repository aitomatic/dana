/* eslint-disable @typescript-eslint/no-explicit-any */
/**
 * Advanced Analytics Tracking Examples
 *
 * This file contains advanced patterns for analytics tracking including
 * funnel tracking, user segmentation, and performance monitoring.
 */

import { useState } from 'react';
import { useDanaAnalytics } from '@/hooks/useAnalytics';
import { analytics } from '@/lib/analytics';

// ============================================================================
// 1. FUNNEL TRACKING WITH ABANDONMENT
// ============================================================================

export const AgentCreationFunnel = () => {
  const [funnelStep, setFunnelStep] = useState(0);
  const [funnelStartTime, setFunnelStartTime] = useState<number | null>(null);

  const funnelSteps = [
    'funnel_start',
    'step_1_name',
    'step_2_description',
    'step_3_resources',
    'step_4_submit',
    'funnel_complete',
  ];

  const startFunnel = () => {
    setFunnelStartTime(Date.now());
    setFunnelStep(1);

    // Track funnel start
    analytics.trackEvent({
      action: 'funnel_start',
      category: 'conversion',
      label: 'agent_creation',
    });
  };

  const nextStep = () => {
    if (funnelStep < funnelSteps.length - 1) {
      setFunnelStep((prev) => prev + 1);

      // Track step completion
      analytics.trackEvent({
        action: 'funnel_step',
        category: 'conversion',
        label: `agent_creation_${funnelSteps[funnelStep]}`,
        value: funnelStep,
      });
    } else {
      // Complete funnel
      const duration = funnelStartTime ? Date.now() - funnelStartTime : 0;

      analytics.trackEvent({
        action: 'funnel_complete',
        category: 'conversion',
        label: 'agent_creation',
        value: duration,
      });
    }
  };

  const abandonFunnel = () => {
    if (funnelStartTime) {
      const duration = Date.now() - funnelStartTime;

      // Track abandonment with context
      analytics.trackEvent({
        action: 'funnel_abandon',
        category: 'conversion',
        label: `agent_creation_step_${funnelStep}`,
        value: duration,
      });
    }
  };

  return (
    <div>
      <button onClick={startFunnel}>Start Creating Agent</button>
      <button onClick={nextStep}>Next Step</button>
      <button onClick={abandonFunnel}>Cancel</button>
      <p>
        Step {funnelStep} of {funnelSteps.length}
      </p>
    </div>
  );
};

// ============================================================================
// 2. USER SEGMENTATION TRACKING
// ============================================================================

export const UserSegmentationTracking = () => {
  const setUserProperties = (userData: any) => {
    // Set user properties for segmentation
    analytics.setUserProperties({
      user_id: userData.id,
      custom_map: {
        user_type: userData.type, // 'free', 'pro', 'enterprise'
        signup_date: userData.signupDate,
        total_agents: userData.totalAgents.toString(),
        feature_tier: userData.featureTier,
        organization_id: userData.orgId,
        last_active: new Date().toISOString(),
      },
    });
  };

  const trackUserMilestone = (milestone: string, value?: number) => {
    analytics.trackEvent({
      action: 'user_milestone',
      category: 'lifecycle',
      label: milestone,
      value: value,
    });
  };

  const trackPowerUserAction = () => {
    const context = analytics.getSessionContext();

    // Check if this is a power user session (10+ actions)
    if (context.action_count >= 10) {
      analytics.trackEvent({
        action: 'power_user_action',
        category: 'engagement',
        label: 'high_engagement_session',
        value: context.action_count,
      });
    }
  };

  return (
    <div>
      <button
        onClick={() =>
          setUserProperties({
            id: 'user_123',
            type: 'pro',
            signupDate: '2025-01-01',
            totalAgents: 5,
            featureTier: 'advanced',
            orgId: 'org_456',
          })
        }
      >
        Set User Properties
      </button>

      <button onClick={() => trackUserMilestone('first_week_active')}>Track Milestone</button>

      <button onClick={trackPowerUserAction}>Track Power User Action</button>
    </div>
  );
};

// ============================================================================
// 3. PERFORMANCE MONITORING
// ============================================================================

export const PerformanceMonitoring = () => {
  const { trackTiming, trackError } = useDanaAnalytics();

  const trackOperationPerformance = async (
    operationName: string,
    operation: () => Promise<any>,
  ) => {
    const startTime = Date.now();
    const startMemory = (performance as any).memory?.usedJSHeapSize || 0;

    try {
      const result = await operation();
      const duration = Date.now() - startTime;
      const endMemory = (performance as any).memory?.usedJSHeapSize || 0;
      const memoryDelta = endMemory - startMemory;

      // Track successful operation
      analytics.trackEvent({
        action: 'operation_success',
        category: 'performance',
        label: operationName,
        value: duration,
      });

      // Track timing
      trackTiming(`${operationName}_duration`, duration, 'performance', 'success');

      // Track memory usage if significant
      if (memoryDelta > 1024 * 1024) {
        // > 1MB
        analytics.trackEvent({
          action: 'high_memory_usage',
          category: 'performance',
          label: operationName,
          value: memoryDelta,
        });
      }

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;

      // Track failed operation
      analytics.trackEvent({
        action: 'operation_failed',
        category: 'performance',
        label: operationName,
        value: duration,
      });

      trackTiming(`${operationName}_failed_duration`, duration, 'performance', 'error');
      trackError('operation_performance_error', (error as Error).message, operationName);

      throw error;
    }
  };

  const performHeavyOperation = async () => {
    return trackOperationPerformance('heavy_file_processing', async () => {
      // Simulate heavy operation
      await new Promise((resolve) => setTimeout(resolve, 2000));
      return { processed: true };
    });
  };

  return <button onClick={performHeavyOperation}>Perform Heavy Operation</button>;
};

// ============================================================================
// 4. FEATURE ADOPTION TRACKING
// ============================================================================

export const FeatureAdoptionTracking = () => {
  const trackFeatureDiscovery = (featureName: string) => {
    const isFirstTime = !sessionStorage.getItem(`analytics_feature_${featureName}_discovered`);

    if (isFirstTime) {
      sessionStorage.setItem(`analytics_feature_${featureName}_discovered`, 'true');

      analytics.trackEvent({
        action: 'feature_discovery',
        category: 'adoption',
        label: featureName,
      });
    }
  };

  const trackFeatureUsage = (featureName: string, usageCount: number) => {
    analytics.trackEvent({
      action: 'feature_usage',
      category: 'adoption',
      label: featureName,
      value: usageCount,
    });
  };

  const trackFeatureAbandonment = (featureName: string, step: string) => {
    analytics.trackEvent({
      action: 'feature_abandonment',
      category: 'adoption',
      label: `${featureName}_${step}`,
    });
  };

  return (
    <div>
      <button onClick={() => trackFeatureDiscovery('advanced_search')}>
        Discover Advanced Search
      </button>

      <button onClick={() => trackFeatureUsage('deep_extraction', 3)}>
        Use Deep Extraction (3rd time)
      </button>

      <button onClick={() => trackFeatureAbandonment('workflow_builder', 'step_2')}>
        Abandon Workflow Builder
      </button>
    </div>
  );
};

// ============================================================================
// 5. ERROR CONTEXT TRACKING
// ============================================================================

export const ErrorContextTracking = () => {
  const { trackError } = useDanaAnalytics();

  const trackErrorWithRichContext = (
    errorType: string,
    error: Error,
    context: {
      component: string;
      action: string;
      userState: any;
      previousAction?: string;
      timeInFlow?: number;
    },
  ) => {
    const sessionContext = analytics.getSessionContext();

    // Track error with rich context
    trackError(
      errorType,
      error.message,
      JSON.stringify({
        component: context.component,
        action: context.action,
        userState: context.userState,
        previousAction: context.previousAction,
        timeInFlow: context.timeInFlow,
        sessionId: sessionContext.session_id,
        sessionDuration: sessionContext.session_duration,
        actionCount: sessionContext.action_count,
        userAgent: navigator.userAgent,
        url: window.location.href,
        timestamp: new Date().toISOString(),
      }),
    );
  };

  const simulateError = () => {
    try {
      throw new Error('Simulated API error');
    } catch (error) {
      trackErrorWithRichContext('api_error', error as Error, {
        component: 'AgentCreationForm',
        action: 'create_agent',
        userState: { hasAgents: true, isProUser: false },
        previousAction: 'uploaded_documents',
        timeInFlow: 45000, // 45 seconds
      });
    }
  };

  return <button onClick={simulateError}>Simulate Error with Context</button>;
};

// ============================================================================
// 6. A/B TESTING INFRASTRUCTURE
// ============================================================================

export const ABTestingInfrastructure = () => {
  const trackExperiment = (experimentName: string, variant: string, action: string) => {
    analytics.trackEvent({
      action: 'experiment_action',
      category: 'experiments',
      label: `${experimentName}_${variant}_${action}`,
    });
  };

  // Example experiment tracking functions (not used in this component)
  // const trackExperimentConversion = (experimentName: string, variant: string) => {
  //   analytics.trackEvent({
  //     action: 'experiment_conversion',
  //     category: 'experiments',
  //     label: `${experimentName}_${variant}`,
  //   });
  // };

  // const getExperimentVariant = (experimentName: string): string => {
  //   // Simple hash-based variant assignment
  //   const userId = sessionStorage.getItem('analytics_user_id') || 'anonymous';
  //   const hash = userId.split('').reduce((a, b) => {
  //     a = (a << 5) - a + b.charCodeAt(0);
  //     return a & a;
  //   }, 0);

  //   return hash % 2 === 0 ? 'control' : 'treatment';
  // };

  const runExperiment = (experimentName: string) => {
    const variant = 'control'; // Simplified for example

    // Track experiment exposure
    analytics.trackEvent({
      action: 'experiment_exposure',
      category: 'experiments',
      label: `${experimentName}_${variant}`,
    });

    return variant;
  };

  const trackExperimentAction = (experimentName: string, action: string) => {
    const variant = 'control'; // Simplified for example
    trackExperiment(experimentName, variant, action);
  };

  return (
    <div>
      <button
        onClick={() => {
          const variant = runExperiment('onboarding_flow');
          console.log(`Running experiment with variant: ${variant}`);
        }}
      >
        Start Onboarding Experiment
      </button>

      <button onClick={() => trackExperimentAction('onboarding_flow', 'completed')}>
        Track Experiment Completion
      </button>
    </div>
  );
};

// ============================================================================
// 7. CUSTOM DASHBOARD METRICS
// ============================================================================

export const CustomDashboardMetrics = () => {
  const trackCustomMetric = (
    metricName: string,
    value: number,
    dimensions: Record<string, string>,
  ) => {
    analytics.trackEvent({
      action: 'custom_metric',
      category: 'dashboard',
      label: metricName,
      value: value,
    });

    // Also track with dimensions
    Object.entries(dimensions).forEach(([key, value]) => {
      analytics.trackEvent({
        action: 'custom_metric_dimension',
        category: 'dashboard',
        label: `${metricName}_${key}_${value}`,
      });
    });
  };

  const trackBusinessMetric = (metric: string, value: number, context: string) => {
    analytics.trackEvent({
      action: 'business_metric',
      category: 'kpi',
      label: `${metric}_${context}`,
      value: value,
    });
  };

  return (
    <div>
      <button
        onClick={() =>
          trackCustomMetric('agent_quality_score', 85, {
            domain: 'finance',
            complexity: 'high',
            user_type: 'pro',
          })
        }
      >
        Track Agent Quality Score
      </button>

      <button onClick={() => trackBusinessMetric('revenue_per_user', 150, 'monthly')}>
        Track Revenue Per User
      </button>
    </div>
  );
};

// ============================================================================
// USAGE NOTES
// ============================================================================

/*
Advanced Analytics Patterns:

1. FUNNEL TRACKING
   - Track each step of user flows
   - Measure abandonment at each step
   - Calculate conversion rates
   - Identify friction points

2. USER SEGMENTATION
   - Set user properties for cohort analysis
   - Track user milestones and progression
   - Identify power users and churn risks

3. PERFORMANCE MONITORING
   - Track operation timing and memory usage
   - Identify performance bottlenecks
   - Monitor error rates by operation

4. FEATURE ADOPTION
   - Track feature discovery and usage
   - Measure adoption rates
   - Identify abandonment points

5. ERROR CONTEXT
   - Include rich context in error tracking
   - Track user state and flow context
   - Enable better debugging and prioritization

6. A/B TESTING
   - Track experiment exposure and actions
   - Measure conversion by variant
   - Enable data-driven optimization

7. CUSTOM METRICS
   - Track business-specific KPIs
   - Create custom dashboards
   - Measure product success metrics

Best Practices:
- Always include context in tracking
- Use consistent naming conventions
- Track both positive and negative outcomes
- Monitor performance impact of tracking
- Regular review and cleanup of unused events
*/
