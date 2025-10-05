/* eslint-disable @typescript-eslint/no-explicit-any */
import { GA_CONFIG } from './constants';

// Google Analytics event types
export interface GAEvent {
  action: string;
  category: string;
  label?: string;
  value?: number;
}

// Google Analytics page view parameters
export interface GAPageView {
  page_title?: string;
  page_location?: string;
  page_path?: string;
}

// Google Analytics user properties
export interface GAUserProperties {
  user_id?: string;
  custom_map?: Record<string, string>;
}

/**
 * Google Analytics utility class
 */
export class Analytics {
  private static instance: Analytics;
  private initialized = false;

  private constructor() {}

  public static getInstance(): Analytics {
    if (!Analytics.instance) {
      Analytics.instance = new Analytics();
    }
    return Analytics.instance;
  }

  /**
   * Initialize Google Analytics
   */
  public initialize(): void {
    if (!GA_CONFIG.ENABLED || this.initialized) {
      return;
    }

    try {
      // Check if Google Analytics is already loaded from HTML
      if (typeof window.gtag === 'function') {
        this.initialized = true;

        // Send initial page view
        window.gtag('event', 'page_view', {
          page_title: document.title,
          page_location: window.location.href,
          page_path: window.location.pathname,
        });

        return;
      }

      // Fallback: Load Google Analytics script dynamically
      // Load Google Analytics script
      const script = document.createElement('script');
      script.async = true;
      script.src = `https://www.googletagmanager.com/gtag/js?id=${GA_CONFIG.TRACKING_ID}`;
      document.head.appendChild(script);

      // Initialize gtag
      window.dataLayer = window.dataLayer || [];
      function gtag(...args: any[]) {
        window.dataLayer.push(args);
      }
      window.gtag = gtag;

      gtag('js', new Date());
      gtag('config', GA_CONFIG.TRACKING_ID, {
        page_title: document.title,
        page_location: window.location.href,
        debug_mode: GA_CONFIG.DEBUG,
      });

      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize Google Analytics:', error);
    }
  }

  /**
   * Track page view
   */
  public trackPageView(pageView?: GAPageView): void {
    if (!GA_CONFIG.ENABLED || !this.initialized) {
      return;
    }

    try {
      const pageData = {
        page_title: pageView?.page_title || document.title,
        page_location: pageView?.page_location || window.location.href,
        page_path: pageView?.page_path || window.location.pathname,
      };

      // Use GA4 page_view event instead of config
      window.gtag('event', 'page_view', pageData);
    } catch (error) {
      console.error('Failed to track page view:', error);
    }
  }

  /**
   * Track custom event
   */
  public trackEvent(event: GAEvent): void {
    if (!GA_CONFIG.ENABLED || !this.initialized) {
      return;
    }

    try {
      window.gtag('event', event.action, {
        event_category: event.category,
        event_label: event.label,
        value: event.value,
      });
    } catch (error) {
      console.error('Failed to track event:', error);
    }
  }

  /**
   * Set user properties (enhanced for PM insights)
   */
  public setUserProperties(properties: GAUserProperties): void {
    if (!GA_CONFIG.ENABLED || !this.initialized) {
      return;
    }

    try {
      if (properties.user_id) {
        window.gtag('config', GA_CONFIG.TRACKING_ID, {
          user_id: properties.user_id,
        });
        
        // Store in sessionStorage for consistent user tracking
        sessionStorage.setItem('analytics_user_id', properties.user_id);
      }

      if (properties.custom_map) {
        window.gtag('set', properties.custom_map);
        
        // Store user properties for context in future events
        Object.entries(properties.custom_map).forEach(([key, value]) => {
          sessionStorage.setItem(`analytics_user_${key}`, String(value));
        });
      }
    } catch (error) {
      console.error('Failed to set user properties:', error);
    }
  }

  /**
   * Initialize session tracking
   */
  public initializeSession(): string {
    const sessionId = sessionStorage.getItem('analytics_session_id');
    const sessionStart = sessionStorage.getItem('analytics_session_start');
    
    if (!sessionId || !sessionStart) {
      // New session
      const newSessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      const startTime = Date.now().toString();
      
      sessionStorage.setItem('analytics_session_id', newSessionId);
      sessionStorage.setItem('analytics_session_start', startTime);
      sessionStorage.setItem('analytics_entry_point', window.location.pathname);
      sessionStorage.setItem('analytics_action_count', '0');
      
      // Track session start
      window.gtag('event', 'session_start', {
        session_id: newSessionId,
        entry_point: window.location.pathname,
      });
      
      return newSessionId;
    }
    
    return sessionId;
  }

  /**
   * Get current session context
   */
  public getSessionContext(): Record<string, any> {
    const sessionId = sessionStorage.getItem('analytics_session_id') || 'unknown';
    const sessionStart = sessionStorage.getItem('analytics_session_start') || '0';
    const entryPoint = sessionStorage.getItem('analytics_entry_point') || 'unknown';
    const actionCount = parseInt(sessionStorage.getItem('analytics_action_count') || '0');
    const userId = sessionStorage.getItem('analytics_user_id') || 'anonymous';
    
    const sessionDuration = Date.now() - parseInt(sessionStart);
    
    return {
      session_id: sessionId,
      session_duration: sessionDuration,
      entry_point: entryPoint,
      action_count: actionCount,
      user_id: userId,
    };
  }

  /**
   * Increment action count (for engagement tracking)
   */
  public incrementActionCount(): void {
    const count = parseInt(sessionStorage.getItem('analytics_action_count') || '0');
    sessionStorage.setItem('analytics_action_count', (count + 1).toString());
  }

  /**
   * Track timing
   */
  public trackTiming(name: string, value: number, category?: string, label?: string): void {
    if (!GA_CONFIG.ENABLED || !this.initialized) {
      return;
    }

    try {
      window.gtag('event', 'timing_complete', {
        name,
        value,
        event_category: category || 'timing',
        event_label: label,
      });
    } catch (error) {
      console.error('Failed to track timing:', error);
    }
  }
}

// Global type declarations for gtag
declare global {
  interface Window {
    dataLayer: any[];
    gtag: (...args: any[]) => void;
  }
}

// Export singleton instance
export const analytics = Analytics.getInstance();
