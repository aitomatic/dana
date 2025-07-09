import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { PoetConfigRequest, PoetConfigResponse, DomainsResponse, ApiError } from '@/lib/api';

export interface PoetState {
  // POET Configuration
  currentConfig: PoetConfigResponse | null;
  availableDomains: string[];
  selectedDomain: string | null;

  // Loading States
  isLoadingConfig: boolean;
  isLoadingDomains: boolean;
  isConfiguring: boolean;

  // Error States
  error: ApiError | null;

  // Actions
  configurePoet: (config: PoetConfigRequest) => Promise<void>;
  getDomains: () => Promise<void>;
  setSelectedDomain: (domain: string | null) => void;
  clearError: () => void;
  reset: () => void;
}

export const usePoetStore = create<PoetState>((set, get) => ({
  // Initial State
  currentConfig: null,
  availableDomains: [],
  selectedDomain: null,
  isLoadingConfig: false,
  isLoadingDomains: false,
  isConfiguring: false,
  error: null,

  // Actions
  configurePoet: async (config: PoetConfigRequest) => {
    set({ isConfiguring: true, error: null });

    try {
      const response = await apiService.configurePoet(config);

      set({
        currentConfig: response,
        isConfiguring: false,
      });
    } catch (error) {
      const apiError = error as ApiError;
      set({
        currentConfig: null,
        isConfiguring: false,
        error: apiError,
      });
    }
  },

  getDomains: async () => {
    set({ isLoadingDomains: true, error: null });

    try {
      const response = await apiService.getPoetDomains();

      set({
        availableDomains: response.domains,
        isLoadingDomains: false,
      });
    } catch (error) {
      const apiError = error as ApiError;
      set({
        availableDomains: [],
        isLoadingDomains: false,
        error: apiError,
      });
    }
  },

  setSelectedDomain: (domain: string | null) => {
    set({ selectedDomain: domain });
  },

  clearError: () => {
    set({ error: null });
  },

  reset: () => {
    set({
      currentConfig: null,
      availableDomains: [],
      selectedDomain: null,
      isLoadingConfig: false,
      isLoadingDomains: false,
      isConfiguring: false,
      error: null,
    });
  },
})); 