import { describe, it, expect, beforeEach, vi } from 'vitest';
import { usePoetStore } from '../poet-store';
import type { PoetConfigRequest, PoetConfigResponse, DomainsResponse, ApiError } from '@/lib/api';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    configurePoet: vi.fn(),
    getPoetDomains: vi.fn(),
  },
}));

import { apiService } from '@/lib/api';

describe('Poet Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    usePoetStore.getState().reset();
  });

  describe('Initial State', () => {
    it('should have correct initial state', () => {
      const state = usePoetStore.getState();
      expect(state.currentConfig).toBeNull();
      expect(state.availableDomains).toEqual([]);
      expect(state.selectedDomain).toBeNull();
      expect(state.isLoadingConfig).toBe(false);
      expect(state.isLoadingDomains).toBe(false);
      expect(state.isConfiguring).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe('configurePoet', () => {
    it('should configure poet successfully', async () => {
      const mockConfig: PoetConfigRequest = {
        domain: 'healthcare',
        retries: 3,
        enable_training: true,
      };
      const mockResponse: PoetConfigResponse = {
        message: 'POET configured successfully',
        config: {
          domain: 'healthcare',
          retries: 3,
          enable_training: true,
        },
      };
      (apiService.configurePoet as any).mockResolvedValue(mockResponse);
      await usePoetStore.getState().configurePoet(mockConfig);
      expect(apiService.configurePoet).toHaveBeenCalledWith(mockConfig);
      expect(usePoetStore.getState().currentConfig).toEqual(mockResponse);
      expect(usePoetStore.getState().isConfiguring).toBe(false);
      expect(usePoetStore.getState().error).toBeNull();
    });
    it('should handle configure poet error', async () => {
      const error = new Error('Failed to configure') as ApiError;
      (apiService.configurePoet as any).mockRejectedValue(error);
      await usePoetStore
        .getState()
        .configurePoet({ domain: 'fail', retries: 1, enable_training: false });
      expect(usePoetStore.getState().isConfiguring).toBe(false);
      expect(usePoetStore.getState().error).toBe(error);
    });
    it('should set loading state during configuration', async () => {
      const mockConfig: PoetConfigRequest = {
        domain: 'healthcare',
        retries: 3,
        enable_training: true,
      };
      const mockResponse: PoetConfigResponse = {
        message: 'POET configured successfully',
        config: {
          domain: 'healthcare',
          retries: 3,
          enable_training: true,
        },
      };
      let resolvePromise: (value: PoetConfigResponse) => void;
      const configPromise = new Promise<PoetConfigResponse>((resolve) => {
        resolvePromise = resolve;
      });
      (apiService.configurePoet as any).mockImplementation(() => configPromise);
      const configurePromise = usePoetStore.getState().configurePoet(mockConfig);
      expect(usePoetStore.getState().isConfiguring).toBe(true);
      resolvePromise!(mockResponse);
      await configurePromise;
      expect(usePoetStore.getState().isConfiguring).toBe(false);
    });
  });

  describe('getDomains', () => {
    it('should get domains successfully', async () => {
      const mockResponse: DomainsResponse = {
        domains: ['healthcare', 'finance', 'education', 'manufacturing'],
      };
      (apiService.getPoetDomains as any).mockResolvedValue(mockResponse);
      await usePoetStore.getState().getDomains();
      expect(apiService.getPoetDomains).toHaveBeenCalled();
      expect(usePoetStore.getState().availableDomains).toEqual(mockResponse.domains);
      expect(usePoetStore.getState().isLoadingDomains).toBe(false);
      expect(usePoetStore.getState().error).toBeNull();
    });
    it('should handle get domains error', async () => {
      const error = new Error('Failed to get domains') as ApiError;
      (apiService.getPoetDomains as any).mockRejectedValue(error);
      await usePoetStore.getState().getDomains();
      expect(usePoetStore.getState().availableDomains).toEqual([]);
      expect(usePoetStore.getState().isLoadingDomains).toBe(false);
      expect(usePoetStore.getState().error).toBe(error);
    });
    it('should set loading state during domains fetch', async () => {
      const mockResponse: DomainsResponse = {
        domains: ['healthcare', 'finance', 'education'],
      };
      let resolvePromise: (value: DomainsResponse) => void;
      const domainsPromise = new Promise<DomainsResponse>((resolve) => {
        resolvePromise = resolve;
      });
      (apiService.getPoetDomains as any).mockImplementation(() => domainsPromise);
      const fetchPromise = usePoetStore.getState().getDomains();
      expect(usePoetStore.getState().isLoadingDomains).toBe(true);
      resolvePromise!(mockResponse);
      await fetchPromise;
      expect(usePoetStore.getState().isLoadingDomains).toBe(false);
    });
  });

  describe('setSelectedDomain', () => {
    it('should set selected domain', () => {
      expect(usePoetStore.getState().selectedDomain).toBeNull();
      usePoetStore.getState().setSelectedDomain('healthcare');
      expect(usePoetStore.getState().selectedDomain).toBe('healthcare');
    });
    it('should clear selected domain', () => {
      usePoetStore.setState({ selectedDomain: 'healthcare' });
      expect(usePoetStore.getState().selectedDomain).toBe('healthcare');
      usePoetStore.getState().setSelectedDomain(null);
      expect(usePoetStore.getState().selectedDomain).toBeNull();
    });
    it('should update selected domain', () => {
      usePoetStore.getState().setSelectedDomain('finance');
      expect(usePoetStore.getState().selectedDomain).toBe('finance');
      usePoetStore.getState().setSelectedDomain('education');
      expect(usePoetStore.getState().selectedDomain).toBe('education');
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      usePoetStore.setState({ error: new Error('Test error') as ApiError });
      expect(usePoetStore.getState().error).toBeTruthy();
      usePoetStore.getState().clearError();
      expect(usePoetStore.getState().error).toBeNull();
    });
  });

  describe('Reset', () => {
    it('should reset store to initial state', () => {
      usePoetStore.setState({
        currentConfig: {
          message: 'POET configured successfully',
          config: {
            domain: 'healthcare',
            retries: 3,
            enable_training: true,
          },
        },
        availableDomains: ['healthcare', 'finance'],
        selectedDomain: 'healthcare',
        isLoadingConfig: true,
        isLoadingDomains: true,
        isConfiguring: true,
        error: new Error('Test error') as ApiError,
      });
      usePoetStore.getState().reset();
      expect(usePoetStore.getState().currentConfig).toBeNull();
      expect(usePoetStore.getState().availableDomains).toEqual([]);
      expect(usePoetStore.getState().selectedDomain).toBeNull();
      expect(usePoetStore.getState().isLoadingConfig).toBe(false);
      expect(usePoetStore.getState().isLoadingDomains).toBe(false);
      expect(usePoetStore.getState().isConfiguring).toBe(false);
      expect(usePoetStore.getState().error).toBeNull();
    });
  });

  describe('Integration Tests', () => {
    it('should handle complete poet workflow', async () => {
      const mockConfig: PoetConfigRequest = {
        domain: 'healthcare',
        retries: 3,
        enable_training: true,
      };
      const mockResponse: PoetConfigResponse = {
        message: 'POET configured successfully',
        config: {
          domain: 'healthcare',
          retries: 3,
          enable_training: true,
        },
      };
      const mockDomains: DomainsResponse = {
        domains: ['healthcare', 'finance'],
      };
      (apiService.configurePoet as any).mockResolvedValue(mockResponse);
      (apiService.getPoetDomains as any).mockResolvedValue(mockDomains);
      await usePoetStore.getState().configurePoet(mockConfig);
      await usePoetStore.getState().getDomains();
      usePoetStore.getState().setSelectedDomain('finance');
      expect(usePoetStore.getState().currentConfig).toEqual(mockResponse);
      expect(usePoetStore.getState().availableDomains).toEqual(mockDomains.domains);
      expect(usePoetStore.getState().selectedDomain).toBe('finance');
    });
    it('should handle concurrent operations', async () => {
      const mockConfig: PoetConfigRequest = {
        domain: 'healthcare',
        retries: 3,
        enable_training: true,
      };
      const mockResponse: PoetConfigResponse = {
        message: 'POET configured successfully',
        config: {
          domain: 'healthcare',
          retries: 3,
          enable_training: true,
        },
      };
      const mockDomains: DomainsResponse = {
        domains: ['healthcare', 'finance'],
      };
      (apiService.configurePoet as any).mockResolvedValue(mockResponse);
      (apiService.getPoetDomains as any).mockResolvedValue(mockDomains);
      await Promise.all([
        usePoetStore.getState().configurePoet(mockConfig),
        usePoetStore.getState().getDomains(),
      ]);
      expect(usePoetStore.getState().currentConfig).toEqual(mockResponse);
      expect(usePoetStore.getState().availableDomains).toEqual(mockDomains.domains);
    });
    it('should handle error states correctly', async () => {
      const error = new Error('Failed to get domains') as ApiError;
      (apiService.getPoetDomains as any).mockRejectedValue(error);
      await usePoetStore.getState().getDomains();
      expect(usePoetStore.getState().availableDomains).toEqual([]);
      expect(usePoetStore.getState().error).toBe(error);
    });
  });
});
