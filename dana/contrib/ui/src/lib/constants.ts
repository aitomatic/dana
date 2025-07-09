// API Configuration
export const API_CONFIG = {
  BASE_URL:
    (typeof import.meta !== "undefined" &&
      import.meta.env?.VITE_API_BASE_URL) ||
    "http://localhost:12345",
  TIMEOUT: 30000, // 30 seconds
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY: 1000, // 1 second
} as const;

// API Endpoints
export const API_ENDPOINTS = {
  HEALTH: "/health",
  ROOT: "/",
  POET: {
    CONFIGURE: "/poet/configure",
    DOMAINS: "/poet/domains",
  },
  TOPICS: {
    LIST: "/topics",
    CREATE: "/topics",
    GET: (id: number) => `/topics/${id}`,
    UPDATE: (id: number) => `/topics/${id}`,
    DELETE: (id: number) => `/topics/${id}`,
  },
  DOCUMENTS: {
    LIST: "/documents",
    CREATE: "/documents",
    GET: (id: number) => `/documents/${id}`,
    UPDATE: (id: number) => `/documents/${id}`,
    DELETE: (id: number) => `/documents/${id}`,
    DOWNLOAD: (id: number) => `/documents/${id}/download`,
  },
} as const;

// POET Domains (available domains for POET configuration)
export const POET_DOMAINS = [
  "healthcare",
  "finance",
  "manufacturing",
  "building_management",
  "text_classification",
  "mathematical_operations",
  "data_processing",
] as const;

// Default POET Configuration
export const DEFAULT_POET_CONFIG = {
  domain: undefined,
  retries: 1,
  timeout: undefined,
  enable_training: true,
} as const;

// UI Constants
export const UI_CONSTANTS = {
  SIDEBAR_WIDTH: {
    MIN: 200,
    MAX: 400,
    DEFAULT: 280,
  },
  NOTIFICATION_DURATION: {
    SHORT: 2000,
    MEDIUM: 5000,
    LONG: 10000,
    PERSISTENT: 0,
  },
  DEBOUNCE_DELAY: 300,
  THROTTLE_DELAY: 100,
} as const;

// Theme Constants
export const THEME = {
  LIGHT: "light",
  DARK: "dark",
  SYSTEM: "system",
} as const;

// Notification Types
export const NOTIFICATION_TYPES = {
  SUCCESS: "success",
  ERROR: "error",
  WARNING: "warning",
  INFO: "info",
} as const;

// Local Storage Keys
export const STORAGE_KEYS = {
  THEME: "opendxa-theme",
  SIDEBAR_COLLAPSED: "opendxa-sidebar-collapsed",
  SIDEBAR_WIDTH: "opendxa-sidebar-width",
  API_CONFIG: "opendxa-api-config",
} as const;

// Error Messages
export const ERROR_MESSAGES = {
  API_UNAVAILABLE:
    "OpenDXA API is not available. Please check if the server is running.",
  NETWORK_ERROR: "Network error occurred. Please check your connection.",
  UNAUTHORIZED: "Unauthorized access. Please check your credentials.",
  FORBIDDEN:
    "Access forbidden. You do not have permission to perform this action.",
  NOT_FOUND: "Resource not found.",
  SERVER_ERROR: "Server error occurred. Please try again later.",
  TIMEOUT: "Request timed out. Please try again.",
  UNKNOWN: "An unexpected error occurred.",
} as const;

// Success Messages
export const SUCCESS_MESSAGES = {
  API_CONNECTED: "Successfully connected to OpenDXA API",
  POET_CONFIGURED: "POET configuration updated successfully",
  DOMAINS_REFRESHED: "Available domains refreshed successfully",
  HEALTH_CHECK_PASSED: "OpenDXA API is running normally",
} as const;

// Loading States
export const LOADING_STATES = {
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  ERROR: "error",
} as const;
