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
   * Set user properties
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
      }

      if (properties.custom_map) {
        window.gtag('set', properties.custom_map);
      }
    } catch (error) {
      console.error('Failed to set user properties:', error);
    }
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
