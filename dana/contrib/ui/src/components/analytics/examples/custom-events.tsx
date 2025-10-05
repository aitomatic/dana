/**
 * Custom Analytics Events Examples
 *
 * This file contains examples of custom event implementations
 * for specific Dana Agent Studio features and workflows.
 */

// Analytics hook available but not used in this example
import { analytics } from '@/lib/analytics';

// ============================================================================
// 1. AGENT WORKFLOW TRACKING
// ============================================================================

export const AgentWorkflowTracking = () => {
  // Analytics hook available but not used in this example

  const trackAgentWorkflowStart = (workflowType: string) => {
    analytics.trackEvent({
      action: 'workflow_start',
      category: 'agent_workflow',
      label: workflowType,
    });
  };

  const trackAgentWorkflowStep = (workflowType: string, step: string, data?: any) => {
    analytics.trackEvent({
      action: 'workflow_step',
      category: 'agent_workflow',
      label: `${workflowType}_${step}`,
      value: data ? Object.keys(data).length : 0,
    });
  };

  const trackAgentWorkflowComplete = (workflowType: string, duration: number, success: boolean) => {
    analytics.trackEvent({
      action: success ? 'workflow_complete' : 'workflow_failed',
      category: 'agent_workflow',
      label: workflowType,
      value: duration,
    });
  };

  const trackAgentIteration = (agentId: string, iterationNumber: number, changes: string[]) => {
    analytics.trackEvent({
      action: 'agent_iteration',
      category: 'agent_development',
      label: agentId,
      value: iterationNumber,
    });

    // Track specific changes
    changes.forEach((change) => {
      analytics.trackEvent({
        action: 'agent_change',
        category: 'agent_development',
        label: `${agentId}_${change}`,
      });
    });
  };

  return {
    trackAgentWorkflowStart,
    trackAgentWorkflowStep,
    trackAgentWorkflowComplete,
    trackAgentIteration,
  };
};

// ============================================================================
// 2. DOCUMENT PROCESSING TRACKING
// ============================================================================

export const DocumentProcessingTracking = () => {
  const trackDocumentUpload = (fileType: string, fileSize: number, source: string) => {
    analytics.trackEvent({
      action: 'document_upload',
      category: 'document_processing',
      label: `${fileType}_${source}`,
      value: fileSize,
    });
  };

  const trackDocumentProcessing = (
    documentId: string,
    processingType: string,
    duration: number,
  ) => {
    analytics.trackEvent({
      action: 'document_processing',
      category: 'document_processing',
      label: `${documentId}_${processingType}`,
      value: duration,
    });
  };

  const trackDocumentQuality = (documentId: string, qualityScore: number, metrics: any) => {
    analytics.trackEvent({
      action: 'document_quality',
      category: 'document_processing',
      label: documentId,
      value: qualityScore,
    });

    // Track quality metrics
    Object.entries(metrics).forEach(([metric, value]) => {
      analytics.trackEvent({
        action: 'document_quality_metric',
        category: 'document_processing',
        label: `${documentId}_${metric}`,
        value: typeof value === 'number' ? value : 0,
      });
    });
  };

  const trackDocumentAssociation = (
    documentId: string,
    agentId: string,
    associationType: string,
  ) => {
    analytics.trackEvent({
      action: 'document_association',
      category: 'document_processing',
      label: `${documentId}_${agentId}_${associationType}`,
    });
  };

  return {
    trackDocumentUpload,
    trackDocumentProcessing,
    trackDocumentQuality,
    trackDocumentAssociation,
  };
};

// ============================================================================
// 3. CHAT INTERACTION DEEP TRACKING
// ============================================================================

export const ChatInteractionTracking = () => {
  const trackChatSessionStart = (agentId: string, sessionType: string) => {
    analytics.trackEvent({
      action: 'chat_session_start',
      category: 'chat_interaction',
      label: `${agentId}_${sessionType}`,
    });
  };

  const trackChatMessage = (
    agentId: string,
    messageType: 'user' | 'agent',
    messageLength: number,
    responseTime?: number,
  ) => {
    analytics.trackEvent({
      action: 'chat_message',
      category: 'chat_interaction',
      label: `${agentId}_${messageType}`,
      value: messageLength,
    });

    if (responseTime) {
      analytics.trackEvent({
        action: 'chat_response_time',
        category: 'chat_interaction',
        label: agentId,
        value: responseTime,
      });
    }
  };

  const trackChatSatisfaction = (
    agentId: string,
    satisfaction: 'positive' | 'negative' | 'neutral',
    feedback?: string,
  ) => {
    analytics.trackEvent({
      action: 'chat_satisfaction',
      category: 'chat_interaction',
      label: `${agentId}_${satisfaction}`,
    });

    if (feedback) {
      analytics.trackEvent({
        action: 'chat_feedback',
        category: 'chat_interaction',
        label: agentId,
      });
    }
  };

  const trackChatSessionEnd = (
    agentId: string,
    duration: number,
    messageCount: number,
    satisfaction?: string,
  ) => {
    analytics.trackEvent({
      action: 'chat_session_end',
      category: 'chat_interaction',
      label: agentId,
      value: duration,
    });

    analytics.trackEvent({
      action: 'chat_session_stats',
      category: 'chat_interaction',
      label: `${agentId}_messages`,
      value: messageCount,
    });

    if (satisfaction) {
      analytics.trackEvent({
        action: 'chat_session_satisfaction',
        category: 'chat_interaction',
        label: `${agentId}_${satisfaction}`,
      });
    }
  };

  return {
    trackChatSessionStart,
    trackChatMessage,
    trackChatSatisfaction,
    trackChatSessionEnd,
  };
};

// ============================================================================
// 4. USER ONBOARDING TRACKING
// ============================================================================

export const OnboardingTracking = () => {
  const trackOnboardingStart = (userId: string, entryPoint: string) => {
    analytics.trackEvent({
      action: 'onboarding_start',
      category: 'user_onboarding',
      label: `${userId}_${entryPoint}`,
    });
  };

  const trackOnboardingStep = (step: string, completed: boolean, timeSpent: number) => {
    analytics.trackEvent({
      action: completed ? 'onboarding_step_complete' : 'onboarding_step_abandon',
      category: 'user_onboarding',
      label: step,
      value: timeSpent,
    });
  };

  const trackOnboardingMilestone = (milestone: string, timeToMilestone: number) => {
    analytics.trackEvent({
      action: 'onboarding_milestone',
      category: 'user_onboarding',
      label: milestone,
      value: timeToMilestone,
    });
  };

  const trackOnboardingComplete = (
    totalTime: number,
    stepsCompleted: number,
    skippedSteps: string[],
  ) => {
    analytics.trackEvent({
      action: 'onboarding_complete',
      category: 'user_onboarding',
      label: 'full_onboarding',
      value: totalTime,
    });

    analytics.trackEvent({
      action: 'onboarding_stats',
      category: 'user_onboarding',
      label: 'steps_completed',
      value: stepsCompleted,
    });

    skippedSteps.forEach((step) => {
      analytics.trackEvent({
        action: 'onboarding_step_skipped',
        category: 'user_onboarding',
        label: step,
      });
    });
  };

  return {
    trackOnboardingStart,
    trackOnboardingStep,
    trackOnboardingMilestone,
    trackOnboardingComplete,
  };
};

// ============================================================================
// 5. FEATURE USAGE ANALYTICS
// ============================================================================

export const FeatureUsageTracking = () => {
  const trackFeatureAccess = (featureName: string, accessMethod: string) => {
    analytics.trackEvent({
      action: 'feature_access',
      category: 'feature_usage',
      label: `${featureName}_${accessMethod}`,
    });
  };

  const trackFeatureUsage = (featureName: string, usageType: string, duration?: number) => {
    analytics.trackEvent({
      action: 'feature_usage',
      category: 'feature_usage',
      label: `${featureName}_${usageType}`,
      value: duration || 0,
    });
  };

  const trackFeatureOutcome = (
    featureName: string,
    outcome: 'success' | 'failure',
    result?: any,
  ) => {
    analytics.trackEvent({
      action: 'feature_outcome',
      category: 'feature_usage',
      label: `${featureName}_${outcome}`,
    });

    if (result) {
      analytics.trackEvent({
        action: 'feature_result',
        category: 'feature_usage',
        label: featureName,
        value: typeof result === 'number' ? result : 0,
      });
    }
  };

  const trackFeatureDiscovery = (featureName: string, discoveryMethod: string) => {
    analytics.trackEvent({
      action: 'feature_discovery',
      category: 'feature_usage',
      label: `${featureName}_${discoveryMethod}`,
    });
  };

  return {
    trackFeatureAccess,
    trackFeatureUsage,
    trackFeatureOutcome,
    trackFeatureDiscovery,
  };
};

// ============================================================================
// 6. PERFORMANCE AND HEALTH TRACKING
// ============================================================================

export const PerformanceTracking = () => {
  const trackPageLoad = (pageName: string, loadTime: number, resourceCount: number) => {
    analytics.trackEvent({
      action: 'page_load',
      category: 'performance',
      label: pageName,
      value: loadTime,
    });

    analytics.trackEvent({
      action: 'page_resources',
      category: 'performance',
      label: pageName,
      value: resourceCount,
    });
  };

  const trackAPICall = (endpoint: string, method: string, duration: number, status: number) => {
    analytics.trackEvent({
      action: 'api_call',
      category: 'performance',
      label: `${method}_${endpoint}`,
      value: duration,
    });

    analytics.trackEvent({
      action: 'api_status',
      category: 'performance',
      label: `${endpoint}_${status}`,
    });
  };

  const trackMemoryUsage = (operation: string, memoryBefore: number, memoryAfter: number) => {
    const memoryDelta = memoryAfter - memoryBefore;

    analytics.trackEvent({
      action: 'memory_usage',
      category: 'performance',
      label: operation,
      value: memoryDelta,
    });

    if (memoryDelta > 10 * 1024 * 1024) {
      // > 10MB
      analytics.trackEvent({
        action: 'high_memory_usage',
        category: 'performance',
        label: operation,
        value: memoryDelta,
      });
    }
  };

  const trackErrorRate = (component: string, errorCount: number, totalActions: number) => {
    const errorRate = (errorCount / totalActions) * 100;

    analytics.trackEvent({
      action: 'error_rate',
      category: 'performance',
      label: component,
      value: errorRate,
    });

    if (errorRate > 5) {
      // > 5% error rate
      analytics.trackEvent({
        action: 'high_error_rate',
        category: 'performance',
        label: component,
        value: errorRate,
      });
    }
  };

  return {
    trackPageLoad,
    trackAPICall,
    trackMemoryUsage,
    trackErrorRate,
  };
};

// ============================================================================
// 7. BUSINESS METRICS TRACKING
// ============================================================================

export const BusinessMetricsTracking = () => {
  const trackUserValue = (userId: string, valueType: string, value: number) => {
    analytics.trackEvent({
      action: 'user_value',
      category: 'business_metrics',
      label: `${userId}_${valueType}`,
      value: value,
    });
  };

  const trackAgentSuccess = (agentId: string, successMetrics: any) => {
    analytics.trackEvent({
      action: 'agent_success',
      category: 'business_metrics',
      label: agentId,
    });

    Object.entries(successMetrics).forEach(([metric, value]) => {
      analytics.trackEvent({
        action: 'agent_success_metric',
        category: 'business_metrics',
        label: `${agentId}_${metric}`,
        value: typeof value === 'number' ? value : 0,
      });
    });
  };

  const trackContentEngagement = (contentId: string, engagementType: string, duration: number) => {
    analytics.trackEvent({
      action: 'content_engagement',
      category: 'business_metrics',
      label: `${contentId}_${engagementType}`,
      value: duration,
    });
  };

  const trackConversion = (conversionType: string, value: number, context: string) => {
    analytics.trackEvent({
      action: 'conversion',
      category: 'business_metrics',
      label: `${conversionType}_${context}`,
      value: value,
    });
  };

  return {
    trackUserValue,
    trackAgentSuccess,
    trackContentEngagement,
    trackConversion,
  };
};

// ============================================================================
// USAGE EXAMPLES
// ============================================================================

export const UsageExamples = () => {
  const agentWorkflow = AgentWorkflowTracking();
  const documentProcessing = DocumentProcessingTracking();
  const chatInteraction = ChatInteractionTracking();
  const onboarding = OnboardingTracking();
  const featureUsage = FeatureUsageTracking();
  const performance = PerformanceTracking();
  const businessMetrics = BusinessMetricsTracking();

  return {
    // Agent workflow example
    startAgentCreation: () => {
      agentWorkflow.trackAgentWorkflowStart('agent_creation');
      agentWorkflow.trackAgentWorkflowStep('agent_creation', 'name_entry');
      agentWorkflow.trackAgentWorkflowStep('agent_creation', 'description_added');
      agentWorkflow.trackAgentWorkflowComplete('agent_creation', 45000, true);
    },

    // Document processing example
    processDocument: () => {
      documentProcessing.trackDocumentUpload('pdf', 2048000, 'library');
      documentProcessing.trackDocumentProcessing('doc_123', 'deep_extraction', 15000);
      documentProcessing.trackDocumentQuality('doc_123', 85, {
        text_quality: 90,
        structure_quality: 80,
        completeness: 85,
      });
    },

    // Chat interaction example
    chatWithAgent: () => {
      chatInteraction.trackChatSessionStart('agent_456', 'support');
      chatInteraction.trackChatMessage('agent_456', 'user', 45, 1200);
      chatInteraction.trackChatMessage('agent_456', 'agent', 120, 800);
      chatInteraction.trackChatSatisfaction('agent_456', 'positive', 'Very helpful!');
      chatInteraction.trackChatSessionEnd('agent_456', 300000, 5, 'positive');
    },

    // Onboarding example
    completeOnboarding: () => {
      onboarding.trackOnboardingStart('user_789', 'homepage');
      onboarding.trackOnboardingStep('welcome', true, 30000);
      onboarding.trackOnboardingStep('first_agent', true, 120000);
      onboarding.trackOnboardingMilestone('first_chat', 180000);
      onboarding.trackOnboardingComplete(300000, 4, ['advanced_features']);
    },

    // Feature usage example
    useFeature: () => {
      featureUsage.trackFeatureDiscovery('deep_extraction', 'tooltip');
      featureUsage.trackFeatureAccess('deep_extraction', 'button_click');
      featureUsage.trackFeatureUsage('deep_extraction', 'file_processing', 30000);
      featureUsage.trackFeatureOutcome('deep_extraction', 'success', { pages_extracted: 5 });
    },

    // Performance example
    trackPerformance: () => {
      performance.trackPageLoad('agent_detail', 1200, 15);
      performance.trackAPICall('/api/agents', 'GET', 800, 200);
      performance.trackMemoryUsage('file_processing', 50000000, 75000000);
      performance.trackErrorRate('agent_creation', 2, 100);
    },

    // Business metrics example
    trackBusinessMetrics: () => {
      businessMetrics.trackUserValue('user_123', 'monthly_revenue', 150);
      businessMetrics.trackAgentSuccess('agent_456', {
        conversations: 25,
        satisfaction_score: 4.2,
        resolution_rate: 0.85,
      });
      businessMetrics.trackContentEngagement('doc_789', 'view', 45000);
      businessMetrics.trackConversion('premium_upgrade', 99, 'feature_usage');
    },
  };
};

// ============================================================================
// NOTES
// ============================================================================

/*
Custom Event Implementation Guidelines:

1. CONSISTENT NAMING
   - Use snake_case for actions
   - Use descriptive category names
   - Include context in labels

2. VALUE TRACKING
   - Use value field for numeric metrics
   - Include timing, counts, scores
   - Avoid storing sensitive data

3. CONTEXT RICHNESS
   - Include relevant identifiers
   - Track user state and flow
   - Add metadata for debugging

4. PERFORMANCE CONSIDERATIONS
   - Don't block UI with tracking
   - Batch events when possible
   - Monitor tracking overhead

5. PRIVACY COMPLIANCE
   - Don't track PII
   - Use anonymized identifiers
   - Follow data retention policies

6. TESTING AND VALIDATION
   - Test events in development
   - Validate data in GA4
   - Monitor for anomalies

Example Event Structure:
{
  action: 'feature_usage',
  category: 'feature_usage',
  label: 'deep_extraction_file_processing',
  value: 30000
}

This creates a clear hierarchy:
- Category: feature_usage
- Action: feature_usage
- Label: deep_extraction_file_processing
- Value: 30000 (duration in ms)
*/
