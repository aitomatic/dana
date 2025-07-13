import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useApiStore } from '../api-store';
import type { HealthResponse, RootResponse, ApiError } from '@/lib/api';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    checkHealth: vi.fn(),
    getRootInfo: vi.fn(),
    isApiAvailable: vi.fn(),
  },
}));

import { apiService } from '@/lib/api';

describe('API Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the store state
    useApiStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = useApiStore.getState();

      expect(state.isHealthy).toBe(false);
      expect(state.isApiAvailable).toBe(false);
      expect(state.healthData).toBeNull();
      expect(state.rootInfo).toBeNull();
      expect(state.isLoadingHealth).toBe(false);
      expect(state.isLoadingRootInfo).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('checkHealth', () => {
    it('should check health successfully', async () => {
      const mockHealthData: HealthResponse = {
        status: 'healthy',
        service: 'Dana API',
      };

      (apiService.checkHealth as any).mockResolvedValue(mockHealthData);

      await useApiStore.getState().checkHealth();

      expect(apiService.checkHealth).toHaveBeenCalled();
      expect(useApiStore.getState().isHealthy).toBe(true);
      expect(useApiStore.getState().healthData).toEqual(mockHealthData);
      expect(useApiStore.getState().isLoadingHealth).toBe(false);
      expect(useApiStore.getState().error).toBeNull();
    });

    it('should handle unhealthy status', async () => {
      const mockHealthData: HealthResponse = {
        status: 'unhealthy',
        service: 'Dana API',
      };

      (apiService.checkHealth as any).mockResolvedValue(mockHealthData);

      await useApiStore.getState().checkHealth();

      expect(useApiStore.getState().isHealthy).toBe(false);
      expect(useApiStore.getState().healthData).toEqual(mockHealthData);
      expect(useApiStore.getState().isLoadingHealth).toBe(false);
      expect(useApiStore.getState().error).toBeNull();
    });

    it('should handle health check error', async () => {
      const error = new Error('Health check failed') as ApiError;
      (apiService.checkHealth as any).mockRejectedValue(error);

      await useApiStore.getState().checkHealth();

      expect(useApiStore.getState().isHealthy).toBe(false);
      expect(useApiStore.getState().healthData).toBeNull();
      expect(useApiStore.getState().isLoadingHealth).toBe(false);
      expect(useApiStore.getState().error).toBe(error);
    });

    it('should set loading state during health check', async () => {
      const mockHealthData: HealthResponse = {
        status: 'healthy',
        service: 'Dana API',
      };

      let resolvePromise: (value: HealthResponse) => void;
      const healthPromise = new Promise<HealthResponse>((resolve) => {
        resolvePromise = resolve;
      });

      (apiService.checkHealth as any).mockImplementation(() => healthPromise);

      // Start health check
      const healthCheckPromise = useApiStore.getState().checkHealth();

      // Check loading state immediately after starting
      expect(useApiStore.getState().isLoadingHealth).toBe(true);

      // Resolve the promise
      resolvePromise!(mockHealthData);

      // Wait for completion
      await healthCheckPromise;

      expect(useApiStore.getState().isLoadingHealth).toBe(false);
    });
  });

  describe('getRootInfo', () => {
    it('should get root info successfully', async () => {
      const mockRootInfo: RootResponse = {
        service: 'Dana API',
        version: '1.0.0',
        status: 'healthy',
        endpoints: {
          '/health': 'Health check endpoint',
          '/agents': 'Agent management endpoint',
          '/conversations': 'Conversation management endpoint',
        },
      };

      (apiService.getRootInfo as any).mockResolvedValue(mockRootInfo);

      await useApiStore.getState().getRootInfo();

      expect(apiService.getRootInfo).toHaveBeenCalled();
      expect(useApiStore.getState().rootInfo).toEqual(mockRootInfo);
      expect(useApiStore.getState().isLoadingRootInfo).toBe(false);
      expect(useApiStore.getState().error).toBeNull();
    });

    it('should handle root info error', async () => {
      const error = new Error('Failed to get root info') as ApiError;
      (apiService.getRootInfo as any).mockRejectedValue(error);

      await useApiStore.getState().getRootInfo();

      expect(useApiStore.getState().rootInfo).toBeNull();
      expect(useApiStore.getState().isLoadingRootInfo).toBe(false);
      expect(useApiStore.getState().error).toBe(error);
    });

    it('should set loading state during root info fetch', async () => {
      const mockRootInfo: RootResponse = {
        service: 'Dana API',
        version: '1.0.0',
        status: 'healthy',
        endpoints: {
          '/health': 'Health check endpoint',
          '/agents': 'Agent management endpoint',
          '/conversations': 'Conversation management endpoint',
        },
      };

      let resolvePromise: (value: RootResponse) => void;
      const rootInfoPromise = new Promise<RootResponse>((resolve) => {
        resolvePromise = resolve;
      });

      (apiService.getRootInfo as any).mockImplementation(() => rootInfoPromise);

      // Start root info fetch
      const fetchPromise = useApiStore.getState().getRootInfo();

      // Check loading state immediately after starting
      expect(useApiStore.getState().isLoadingRootInfo).toBe(true);

      // Resolve the promise
      resolvePromise!(mockRootInfo);

      // Wait for completion
      await fetchPromise;

      expect(useApiStore.getState().isLoadingRootInfo).toBe(false);
    });
  });

  describe('checkApiAvailability', () => {
    it('should check API availability successfully', async () => {
      (apiService.isApiAvailable as any).mockResolvedValue(true);

      await useApiStore.getState().checkApiAvailability();

      expect(apiService.isApiAvailable).toHaveBeenCalled();
      expect(useApiStore.getState().isApiAvailable).toBe(true);
    });

    it('should handle API unavailable', async () => {
      (apiService.isApiAvailable as any).mockResolvedValue(false);

      await useApiStore.getState().checkApiAvailability();

      expect(useApiStore.getState().isApiAvailable).toBe(false);
    });

    it('should handle API availability check error', async () => {
      (apiService.isApiAvailable as any).mockRejectedValue(new Error('Network error'));

      await useApiStore.getState().checkApiAvailability();

      expect(useApiStore.getState().isApiAvailable).toBe(false);
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      // Set an error first using the store's setState method
      useApiStore.setState({ error: new Error('Test error') as ApiError });

      expect(useApiStore.getState().error).toBeTruthy();

      // Clear the error
      useApiStore.getState().clearError();

      expect(useApiStore.getState().error).toBeNull();
    });
  });

  describe('reset', () => {
    it('should reset store to initial state', () => {
      // Modify state using the store's setState method
      useApiStore.setState({
        isHealthy: true,
        isApiAvailable: true,
        healthData: { status: 'healthy', service: 'Dana API' },
        rootInfo: {
          service: 'Test',
          version: '1.0.0',
          status: 'healthy',
          endpoints: {},
        },
        isLoadingHealth: true,
        isLoadingRootInfo: true,
        error: new Error('Test error') as ApiError,
      });

      // Reset
      useApiStore.getState().reset();

      expect(useApiStore.getState().isHealthy).toBe(false);
      expect(useApiStore.getState().isApiAvailable).toBe(false);
      expect(useApiStore.getState().healthData).toBeNull();
      expect(useApiStore.getState().rootInfo).toBeNull();
      expect(useApiStore.getState().isLoadingHealth).toBe(false);
      expect(useApiStore.getState().isLoadingRootInfo).toBe(false);
      expect(useApiStore.getState().error).toBeNull();
    });
  });

  describe('Integration Tests', () => {
    it('should handle multiple API calls correctly', async () => {
      const mockHealthData: HealthResponse = {
        status: 'healthy',
        service: 'Dana API',
      };

      const mockRootInfo: RootResponse = {
        service: 'Dana API',
        version: '1.0.0',
        status: 'healthy',
        endpoints: {
          '/health': 'Health check endpoint',
          '/agents': 'Agent management endpoint',
          '/conversations': 'Conversation management endpoint',
        },
      };

      (apiService.checkHealth as any).mockResolvedValue(mockHealthData);
      (apiService.getRootInfo as any).mockResolvedValue(mockRootInfo);
      (apiService.isApiAvailable as any).mockResolvedValue(true);

      await Promise.all([
        useApiStore.getState().checkHealth(),
        useApiStore.getState().getRootInfo(),
        useApiStore.getState().checkApiAvailability(),
      ]);

      expect(useApiStore.getState().isHealthy).toBe(true);
      expect(useApiStore.getState().isApiAvailable).toBe(true);
      expect(useApiStore.getState().healthData).toEqual(mockHealthData);
      expect(useApiStore.getState().rootInfo).toEqual(mockRootInfo);
      expect(useApiStore.getState().isLoadingHealth).toBe(false);
      expect(useApiStore.getState().isLoadingRootInfo).toBe(false);
      expect(useApiStore.getState().error).toBeNull();
    });

    it('should handle concurrent error states', async () => {
      const healthError = new Error('Health check failed') as ApiError;
      const rootInfoError = new Error('Root info failed') as ApiError;

      (apiService.checkHealth as any).mockRejectedValue(healthError);
      (apiService.getRootInfo as any).mockRejectedValue(rootInfoError);
      (apiService.isApiAvailable as any).mockRejectedValue(new Error('Availability check failed'));

      await Promise.all([
        useApiStore.getState().checkHealth(),
        useApiStore.getState().getRootInfo(),
        useApiStore.getState().checkApiAvailability(),
      ]);

      expect(useApiStore.getState().isHealthy).toBe(false);
      expect(useApiStore.getState().isApiAvailable).toBe(false);
      expect(useApiStore.getState().healthData).toBeNull();
      expect(useApiStore.getState().rootInfo).toBeNull();
      expect(useApiStore.getState().error).toBe(rootInfoError); // Last error should be set
    });
  });
});
