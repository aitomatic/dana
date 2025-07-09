import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { HealthResponse, RootResponse, ApiError } from '@/lib/api';

export interface ApiState {
  // API Health & Status
  isHealthy: boolean;
  isApiAvailable: boolean;
  healthData: HealthResponse | null;
  rootInfo: RootResponse | null;

  // Loading States
  isLoadingHealth: boolean;
  isLoadingRootInfo: boolean;

  // Error States
  error: ApiError | null;

  // Actions
  checkHealth: () => Promise<void>;
  getRootInfo: () => Promise<void>;
  checkApiAvailability: () => Promise<void>;
  clearError: () => void;
  reset: () => void;
}

export const useApiStore = create<ApiState>((set, get) => ({
  // Initial State
  isHealthy: false,
  isApiAvailable: false,
  healthData: null,
  rootInfo: null,
  isLoadingHealth: false,
  isLoadingRootInfo: false,
  error: null,

  // Actions
  checkHealth: async () => {
    set({ isLoadingHealth: true, error: null });

    try {
      const healthData = await apiService.checkHealth();
      const isHealthy = healthData.status === 'healthy';

      set({
        isHealthy,
        healthData,
        isLoadingHealth: false,
      });
    } catch (error) {
      const apiError = error as ApiError;
      set({
        isHealthy: false,
        healthData: null,
        isLoadingHealth: false,
        error: apiError,
      });
    }
  },

  getRootInfo: async () => {
    set({ isLoadingRootInfo: true, error: null });

    try {
      const rootInfo = await apiService.getRootInfo();

      set({
        rootInfo,
        isLoadingRootInfo: false,
      });
    } catch (error) {
      const apiError = error as ApiError;
      set({
        rootInfo: null,
        isLoadingRootInfo: false,
        error: apiError,
      });
    }
  },

  checkApiAvailability: async () => {
    try {
      const isAvailable = await apiService.isApiAvailable();
      set({ isApiAvailable: isAvailable });
    } catch (error) {
      set({ isApiAvailable: false });
    }
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      isHealthy: false,
      isApiAvailable: false,
      healthData: null,
      rootInfo: null,
      isLoadingHealth: false,
      isLoadingRootInfo: false,
      error: null,
    });
  },
})); 