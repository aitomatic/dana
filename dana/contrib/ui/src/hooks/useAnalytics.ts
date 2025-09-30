import { useEffect, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { analytics, type GAEvent, type GAPageView, type GAUserProperties } from '@/lib/analytics';
import { GA_CONFIG } from '@/lib/constants';

/**
 * Hook for Google Analytics functionality
 */
export const useAnalytics = () => {
  const location = useLocation();

  // Track page views on route changes
  useEffect(() => {
    if (GA_CONFIG.ENABLED) {
      analytics.trackPageView({
        page_title: document.title,
        page_location: window.location.href,
        page_path: location.pathname,
      });
    }
  }, [location]);

  // Track custom events
  const trackEvent = useCallback((event: GAEvent) => {
    analytics.trackEvent(event);
  }, []);

  // Track page view manually
  const trackPageView = useCallback((pageView?: GAPageView) => {
    analytics.trackPageView(pageView);
  }, []);

  // Set user properties
  const setUserProperties = useCallback((properties: GAUserProperties) => {
    analytics.setUserProperties(properties);
  }, []);

  // Track timing
  const trackTiming = useCallback(
    (name: string, value: number, category?: string, label?: string) => {
      analytics.trackTiming(name, value, category, label);
    },
    [],
  );

  return {
    trackEvent,
    trackPageView,
    setUserProperties,
    trackTiming,
    isEnabled: GA_CONFIG.ENABLED,
  };
};

/**
 * Hook for tracking specific user actions in the Dana UI
 */
export const useDanaAnalytics = () => {
  const { trackEvent, trackTiming } = useAnalytics();

  // Track agent creation
  const trackAgentCreation = useCallback(
    (agentName: string, domain?: string) => {
      trackEvent({
        action: 'create_agent',
        category: 'agent_management',
        label: agentName,
      });

      if (domain) {
        trackEvent({
          action: 'create_agent_domain',
          category: 'agent_management',
          label: domain,
        });
      }
    },
    [trackEvent],
  );

  // Track agent editing
  const trackAgentEdit = useCallback(
    (agentId: string, field: string) => {
      trackEvent({
        action: 'edit_agent',
        category: 'agent_management',
        label: `${agentId}_${field}`,
      });
    },
    [trackEvent],
  );

  // Track agent deletion
  const trackAgentDeletion = useCallback(
    (agentId: string) => {
      trackEvent({
        action: 'delete_agent',
        category: 'agent_management',
        label: agentId,
      });
    },
    [trackEvent],
  );

  // Track library file upload
  const trackFileUpload = useCallback(
    (fileType: string, fileSize?: number) => {
      trackEvent({
        action: 'upload_file',
        category: 'library',
        label: fileType,
        value: fileSize,
      });
    },
    [trackEvent],
  );

  // Track library file download
  const trackFileDownload = useCallback(
    (fileType: string, fileName: string) => {
      trackEvent({
        action: 'download_file',
        category: 'library',
        label: `${fileType}_${fileName}`,
      });
    },
    [trackEvent],
  );

  // Track library folder creation
  const trackFolderCreation = useCallback(
    (folderName: string) => {
      trackEvent({
        action: 'create_folder',
        category: 'library',
        label: folderName,
      });
    },
    [trackEvent],
  );

  // Track code generation
  const trackCodeGeneration = useCallback(
    (agentId: string, duration: number) => {
      trackEvent({
        action: 'generate_code',
        category: 'agent_development',
        label: agentId,
        value: duration,
      });

      trackTiming('code_generation', duration, 'agent_development', agentId);
    },
    [trackEvent, trackTiming],
  );

  // Track chat interaction
  const trackChatMessage = useCallback(
    (agentId: string, messageType: 'user' | 'agent') => {
      trackEvent({
        action: 'chat_message',
        category: 'agent_interaction',
        label: `${agentId}_${messageType}`,
      });
    },
    [trackEvent],
  );

  // Track API connection
  const trackApiConnection = useCallback(
    (status: 'success' | 'error', endpoint?: string) => {
      console.log('trackApiConnection', status, endpoint);
      trackEvent({
        action: 'api_connection',
        category: 'system',
        label: endpoint || 'unknown',
      });
    },
    [trackEvent],
  );

  // Track error
  const trackError = useCallback(
    (errorType: string, errorMessage: string, context?: string) => {
      console.log('trackError', errorType, errorMessage, context);
      trackEvent({
        action: 'error',
        category: 'system',
        label: `${errorType}_${context || 'unknown'}`,
      });
    },
    [trackEvent],
  );

  return {
    trackAgentCreation,
    trackAgentEdit,
    trackAgentDeletion,
    trackFileUpload,
    trackFileDownload,
    trackFolderCreation,
    trackCodeGeneration,
    trackChatMessage,
    trackApiConnection,
    trackError,
  };
};
