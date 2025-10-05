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

  // Track agent creation with context
  const trackAgentCreation = useCallback(
    (agentName: string, domain?: string) => {
      analytics.incrementActionCount();
      const context = analytics.getSessionContext();
      
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
      
      // Check if this is user's first agent
      const firstAgent = !sessionStorage.getItem('analytics_first_agent_created');
      if (firstAgent) {
        sessionStorage.setItem('analytics_first_agent_created', 'true');
        trackEvent({
          action: 'user_first_agent',
          category: 'lifecycle',
          label: agentName,
        });
        
        // Calculate time to first agent (activation metric)
        if (context.session_duration) {
          trackTiming('time_to_first_agent', context.session_duration, 'activation', 'first_agent');
        }
      }
    },
    [trackEvent, trackTiming],
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

  // Track chat interaction with first-time detection
  const trackChatMessage = useCallback(
    (agentId: string, messageType: 'user' | 'agent') => {
      analytics.incrementActionCount();
      const context = analytics.getSessionContext();
      
      trackEvent({
        action: 'chat_message',
        category: 'agent_interaction',
        label: `${agentId}_${messageType}`,
      });
      
      // Check if this is user's first chat (aha moment!)
      if (messageType === 'user') {
        const firstChat = !sessionStorage.getItem('analytics_first_chat_sent');
        if (firstChat) {
          sessionStorage.setItem('analytics_first_chat_sent', 'true');
          trackEvent({
            action: 'user_first_chat',
            category: 'lifecycle',
            label: agentId,
          });
          
          // Calculate time to first chat (engagement metric)
          if (context.session_duration) {
            trackTiming('time_to_first_chat', context.session_duration, 'activation', 'first_chat');
          }
        }
      }
    },
    [trackEvent, trackTiming],
  );

  // Track tab navigation
  const trackTabNavigation = useCallback(
    (tabName: string, context: 'agent_detail' | 'main_page') => {
      trackEvent({
        action: 'tab_navigation',
        category: 'navigation',
        label: `${context}_${tabName}`,
      });
    },
    [trackEvent],
  );

  // Track agent import
  const trackAgentImport = useCallback(
    (prebuiltKey: string, success: boolean) => {
      trackEvent({
        action: success ? 'import_agent_success' : 'import_agent_failed',
        category: 'agent_management',
        label: prebuiltKey,
      });
    },
    [trackEvent],
  );

  // Track document association
  const trackDocumentAssociation = useCallback(
    (agentId: string, documentCount: number) => {
      trackEvent({
        action: 'associate_documents',
        category: 'agent_management',
        label: agentId,
        value: documentCount,
      });
    },
    [trackEvent],
  );

  // Track file extraction with first-time detection
  const trackFileExtraction = useCallback(
    (fileType: string, extractionType: 'basic' | 'deep', success: boolean) => {
      analytics.incrementActionCount();
      
      trackEvent({
        action: success ? 'file_extraction_success' : 'file_extraction_failed',
        category: 'library',
        label: `${fileType}_${extractionType}`,
      });
      
      // Track first-time deep extraction usage (feature discovery)
      if (extractionType === 'deep' && success) {
        const firstDeepExtraction = !sessionStorage.getItem('analytics_first_deep_extraction');
        if (firstDeepExtraction) {
          sessionStorage.setItem('analytics_first_deep_extraction', 'true');
          trackEvent({
            action: 'feature_first_use',
            category: 'discovery',
            label: 'deep_extraction',
          });
        }
      }
    },
    [trackEvent],
  );

  // Track PDF viewing
  const trackPdfView = useCallback(
    (fileName: string) => {
      trackEvent({
        action: 'view_pdf',
        category: 'library',
        label: fileName,
      });
    },
    [trackEvent],
  );

  // Track API connection
  const trackApiConnection = useCallback(
    (status: 'success' | 'error', endpoint?: string) => {
      trackEvent({
        action: 'api_connection',
        category: 'system',
        label: `${status}_${endpoint || 'unknown'}`,
      });
    },
    [trackEvent],
  );

  // Track error
  const trackError = useCallback(
    (errorType: string, _errorMessage: string, context?: string) => {
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
    trackAgentImport,
    trackDocumentAssociation,
    trackFileUpload,
    trackFileDownload,
    trackFolderCreation,
    trackFileExtraction,
    trackPdfView,
    trackCodeGeneration,
    trackChatMessage,
    trackTabNavigation,
    trackApiConnection,
    trackError,
  };
};
