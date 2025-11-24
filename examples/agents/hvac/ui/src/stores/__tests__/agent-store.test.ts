import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useAgentStore } from '../agent-store';
import type { AgentCreate, AgentRead } from '@/types/agent';

// Mock the API service
vi.mock('@/lib/api', () => ({
  apiService: {
    getAgents: vi.fn(),
    getAgent: vi.fn(),
    createAgent: vi.fn(),
    updateAgent: vi.fn(),
    deleteAgent: vi.fn(),
  },
}));

import { apiService } from '@/lib/api';

describe('Agent Store', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset the store state
    useAgentStore.getState().reset();
  });

  describe('fetchAgents', () => {
    it('should fetch agents successfully', async () => {
      const mockAgents: AgentRead[] = [
        {
          id: 1,
          name: 'Test Agent',
          description: 'A test agent',
          config: {},
        },
      ];

      (apiService.getAgents as any).mockResolvedValue(mockAgents);

      const { result } = renderHook(() => useAgentStore());

      await act(async () => {
        await result.current.fetchAgents();
      });

      expect(apiService.getAgents).toHaveBeenCalledWith(undefined);
      expect(result.current.agents).toEqual(mockAgents);
      expect(result.current.isLoading).toBe(false);
      expect(result.current.error).toBe(null);
    });

    it('should handle fetch agents error', async () => {
      const error = new Error('Failed to fetch agents');
      (apiService.getAgents as any).mockRejectedValue(error);

      const { result } = renderHook(() => useAgentStore());

      await act(async () => {
        await result.current.fetchAgents();
      });

      expect(result.current.error).toBe('Failed to fetch agents');
      expect(result.current.isLoading).toBe(false);
    });
  });

  describe('createAgent', () => {
    it('should create agent successfully', async () => {
      const newAgent: AgentCreate = {
        name: 'New Agent',
        description: 'A new agent',
        config: {},
      };

      const createdAgent: AgentRead = {
        id: 2,
        ...newAgent,
      };

      (apiService.createAgent as any).mockResolvedValue(createdAgent);

      const { result } = renderHook(() => useAgentStore());

      // Set initial agents
      act(() => {
        result.current.agents = [
          {
            id: 1,
            name: 'Existing Agent',
            description: 'An existing agent',
            config: {},
          },
        ];
      });

      let response;
      await act(async () => {
        response = await result.current.createAgent(newAgent);
      });

      expect(apiService.createAgent).toHaveBeenCalledWith(newAgent);
      expect(result.current.agents).toHaveLength(2);
      expect(result.current.agents).toContainEqual(createdAgent);
      expect(response).toEqual(createdAgent);
      expect(result.current.error).toBe(null);
    });

    it('should handle create agent error', async () => {
      const newAgent: AgentCreate = {
        name: 'New Agent',
        description: 'A new agent',
        config: {},
      };

      const error = new Error('Failed to create agent');
      (apiService.createAgent as any).mockRejectedValue(error);

      const { result } = renderHook(() => useAgentStore());

      await act(async () => {
        await expect(result.current.createAgent(newAgent)).rejects.toThrow(
          'Failed to create agent',
        );
      });
      expect(result.current.error).toBe('Failed to create agent');
    });
  });

  describe('updateAgent', () => {
    it('should update agent successfully', async () => {
      const agentId = 1;
      const updateData: AgentCreate = {
        name: 'Updated Agent',
        description: 'An updated agent',
        config: {},
      };

      const updatedAgent: AgentRead = {
        id: agentId,
        ...updateData,
      };

      (apiService.updateAgent as any).mockResolvedValue(updatedAgent);

      const { result } = renderHook(() => useAgentStore());

      // Set initial agents
      act(() => {
        result.current.agents = [
          {
            id: agentId,
            name: 'Original Agent',
            description: 'Original description',
            config: {},
          },
        ];
      });

      let response;
      await act(async () => {
        response = await result.current.updateAgent(agentId, updateData);
      });

      expect(apiService.updateAgent).toHaveBeenCalledWith(agentId, updateData);
      expect(result.current.agents[0]).toEqual(updatedAgent);
      expect(response).toEqual(updatedAgent);
      expect(result.current.error).toBe(null);
    });

    it('should handle update agent error', async () => {
      const agentId = 1;
      const updateData: AgentCreate = {
        name: 'Updated Agent',
        description: 'An updated agent',
        config: {},
      };

      const error = new Error('Failed to update agent');
      (apiService.updateAgent as any).mockRejectedValue(error);

      const { result } = renderHook(() => useAgentStore());

      await act(async () => {
        await expect(result.current.updateAgent(agentId, updateData)).rejects.toThrow(
          'Failed to update agent',
        );
      });
      expect(result.current.error).toBe('Failed to update agent');
    });
  });

  describe('deleteAgent', () => {
    it('should delete agent successfully', async () => {
      const agentId = 1;

      (apiService.deleteAgent as any).mockResolvedValue({ message: 'Agent deleted' });

      const { result } = renderHook(() => useAgentStore());

      // Set initial agents
      act(() => {
        result.current.agents = [
          {
            id: agentId,
            name: 'Agent to Delete',
            description: 'Will be deleted',
            config: {},
          },
          {
            id: 2,
            name: 'Agent to Keep',
            description: 'Will remain',
            config: {},
          },
        ];
      });

      await act(async () => {
        await result.current.deleteAgent(agentId);
      });

      expect(apiService.deleteAgent).toHaveBeenCalledWith(agentId);
      expect(result.current.agents).toHaveLength(1);
      expect(result.current.agents[0].id).toBe(2);
      expect(result.current.error).toBe(null);
    });

    it('should handle delete agent error', async () => {
      const agentId = 1;

      const error = new Error('Failed to delete agent');
      (apiService.deleteAgent as any).mockRejectedValue(error);

      const { result } = renderHook(() => useAgentStore());

      await act(async () => {
        await expect(result.current.deleteAgent(agentId)).rejects.toThrow('Failed to delete agent');
      });
      expect(result.current.error).toBe('Failed to delete agent');
    });
  });

  describe('setSelectedAgent', () => {
    it('should set selected agent', () => {
      const { result } = renderHook(() => useAgentStore());
      const agent: AgentRead = {
        id: 1,
        name: 'Test Agent',
        description: 'A test agent',
        config: {},
      };

      act(() => {
        result.current.setSelectedAgent(agent);
      });
      expect(result.current.selectedAgent).toEqual(agent);
    });

    it('should clear selected agent', () => {
      const { result } = renderHook(() => useAgentStore());

      act(() => {
        result.current.setSelectedAgent(null);
      });
      expect(result.current.selectedAgent).toBe(null);
    });
  });

  describe('clearError', () => {
    it('should clear error state', () => {
      const { result } = renderHook(() => useAgentStore());

      act(() => {
        result.current.setError('Some error');
        result.current.clearError();
      });
      expect(result.current.error).toBe(null);
    });
  });

  describe('reset', () => {
    it('should reset store to initial state', () => {
      const { result } = renderHook(() => useAgentStore());

      // Set some state
      act(() => {
        result.current.agents = [{ id: 1, name: 'Test', description: 'Test', config: {} }];
        result.current.selectedAgent = { id: 1, name: 'Test', description: 'Test', config: {} };
        result.current.error = 'Some error';
      });

      act(() => {
        result.current.reset();
      });

      expect(result.current.agents).toEqual([]);
      expect(result.current.selectedAgent).toBe(null);
      expect(result.current.error).toBe(null);
      expect(result.current.isLoading).toBe(false);
    });
  });
});
