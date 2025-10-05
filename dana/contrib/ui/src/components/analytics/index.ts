/**
 * Analytics Module Index
 * 
 * This file provides a centralized export for all analytics-related
 * functionality in the Dana Agent Studio UI.
 */

// Core analytics functionality
export { analytics } from '@/lib/analytics';
export { GA_CONFIG } from '@/lib/constants';

// React hooks for analytics
export { useAnalytics, useDanaAnalytics } from '@/hooks/useAnalytics';

// Analytics documentation and guides
export const ANALYTICS_DOCS = {
  tracking: '/src/components/analytics/ANALYTICS_TRACKING.md',
  pmGuide: '/src/components/analytics/PM_INSIGHTS_GUIDE.md',
  enhancementPlan: '/src/components/analytics/ANALYTICS_ENHANCEMENT_PLAN.md',
  examples: '/src/components/analytics/examples/',
};

// Analytics event types for TypeScript
export interface AnalyticsEvent {
  action: string;
  category: string;
  label?: string;
  value?: number;
}

export interface UserProperties {
  user_id?: string;
  custom_map?: Record<string, string>;
}

export interface SessionContext {
  session_id: string;
  session_duration: number;
  entry_point: string;
  action_count: number;
  user_id: string;
}

// Common event categories
export const ANALYTICS_CATEGORIES = {
  AGENT_MANAGEMENT: 'agent_management',
  LIBRARY: 'library',
  CHAT: 'chat',
  NAVIGATION: 'navigation',
  PERFORMANCE: 'performance',
  ERROR: 'error',
  LIFECYCLE: 'lifecycle',
  CONVERSION: 'conversion',
  ENGAGEMENT: 'engagement',
  ADOPTION: 'adoption',
  BUSINESS_METRICS: 'business_metrics',
  FEATURE_USAGE: 'feature_usage',
  USER_ONBOARDING: 'user_onboarding',
  CHAT_INTERACTION: 'chat_interaction',
  DOCUMENT_PROCESSING: 'document_processing',
  AGENT_WORKFLOW: 'agent_workflow',
  AGENT_DEVELOPMENT: 'agent_development',
  EXPERIMENTS: 'experiments',
  DASHBOARD: 'dashboard',
  KPI: 'kpi',
} as const;

// Common event actions
export const ANALYTICS_ACTIONS = {
  // Agent lifecycle
  CREATE_AGENT: 'create_agent',
  EDIT_AGENT: 'edit_agent',
  DELETE_AGENT: 'delete_agent',
  IMPORT_AGENT: 'import_agent',
  
  // File operations
  UPLOAD_FILE: 'upload_file',
  DOWNLOAD_FILE: 'download_file',
  EXTRACT_FILE: 'extract_file',
  ASSOCIATE_DOCUMENT: 'associate_document',
  
  // Chat interactions
  SEND_MESSAGE: 'send_message',
  RECEIVE_MESSAGE: 'receive_message',
  CHAT_SESSION_START: 'chat_session_start',
  CHAT_SESSION_END: 'chat_session_end',
  
  // Navigation
  PAGE_VIEW: 'page_view',
  TAB_NAVIGATION: 'tab_navigation',
  
  // User lifecycle
  USER_FIRST_AGENT: 'user_first_agent',
  USER_FIRST_CHAT: 'user_first_chat',
  FEATURE_FIRST_USE: 'feature_first_use',
  
  // Performance
  TIMING: 'timing',
  ERROR: 'error',
  
  // Conversion
  FUNNEL_START: 'funnel_start',
  FUNNEL_STEP: 'funnel_step',
  FUNNEL_COMPLETE: 'funnel_complete',
  FUNNEL_ABANDON: 'funnel_abandon',
} as const;

// Analytics configuration
export const ANALYTICS_CONFIG = {
  // Event naming conventions
  NAMING_CONVENTIONS: {
    ACTION_FORMAT: 'snake_case',
    CATEGORY_FORMAT: 'snake_case',
    LABEL_FORMAT: 'snake_case_with_context',
  },
  
  // Value guidelines
  VALUE_GUIDELINES: {
    TIMING_UNIT: 'milliseconds',
    COUNT_UNIT: 'number',
    SCORE_UNIT: 'percentage_or_rating',
  },
  
  // Privacy settings
  PRIVACY: {
    ANONYMIZE_IP: true,
    RESPECT_DNT: true,
    DATA_RETENTION_DAYS: 26,
  },
  
  // Performance settings
  PERFORMANCE: {
    BATCH_SIZE: 10,
    FLUSH_INTERVAL: 5000, // 5 seconds
    MAX_RETRIES: 3,
  },
} as const;

// Utility functions for analytics
export const AnalyticsUtils = {
  /**
   * Generate a unique session ID
   */
  generateSessionId: (): string => {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  },

  /**
   * Format event label with context
   */
  formatLabel: (base: string, context?: string): string => {
    return context ? `${base}_${context}` : base;
  },

  /**
   * Validate event data
   */
  validateEvent: (event: AnalyticsEvent): boolean => {
    return !!(event.action && event.category);
  },

  /**
   * Get current timestamp
   */
  getTimestamp: (): number => {
    return Date.now();
  },

  /**
   * Calculate duration between timestamps
   */
  calculateDuration: (startTime: number, endTime?: number): number => {
    return (endTime || Date.now()) - startTime;
  },

  /**
   * Check if user is in development mode
   */
  isDevelopment: (): boolean => {
    return process.env.NODE_ENV === 'development';
  },

  /**
   * Sanitize sensitive data
   */
  sanitizeData: (data: any): any => {
    if (typeof data !== 'object' || data === null) return data;
    
    const sanitized = { ...data };
    const sensitiveKeys = ['password', 'token', 'key', 'secret', 'email'];
    
    sensitiveKeys.forEach(key => {
      if (sanitized[key]) {
        sanitized[key] = '[REDACTED]';
      }
    });
    
    return sanitized;
  },
};

// Analytics constants for common values
export const ANALYTICS_CONSTANTS = {
  // Timing thresholds (in milliseconds)
  TIMING_THRESHOLDS: {
    FAST: 1000,      // < 1 second
    MODERATE: 3000,  // < 3 seconds
    SLOW: 10000,     // < 10 seconds
    VERY_SLOW: 30000, // < 30 seconds
  },
  
  // Error severity levels
  ERROR_SEVERITY: {
    LOW: 'low',
    MEDIUM: 'medium',
    HIGH: 'high',
    CRITICAL: 'critical',
  },
  
  // User types
  USER_TYPES: {
    ANONYMOUS: 'anonymous',
    FREE: 'free',
    PRO: 'pro',
    ENTERPRISE: 'enterprise',
  },
  
  // Feature tiers
  FEATURE_TIERS: {
    BASIC: 'basic',
    ADVANCED: 'advanced',
    PREMIUM: 'premium',
    ENTERPRISE: 'enterprise',
  },
} as const;

// Export all analytics-related types and utilities
export type {
  AnalyticsEvent,
  UserProperties,
  SessionContext,
};

// Re-export from examples for easy access
export * from './examples/basic-usage';
export * from './examples/advanced-tracking';
export * from './examples/custom-events';
