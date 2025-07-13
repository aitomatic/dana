import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { useDanaAgentForm } from '../use-dana-agent-form';
import { toast } from 'sonner';

// Mock dependencies
vi.mock('react-router-dom', () => ({
  useNavigate: () => vi.fn(),
}));

vi.mock('sonner', () => ({
  toast: {
    error: vi.fn(),
    success: vi.fn(),
  },
}));

const mockCreateAgent = vi.fn();

vi.mock('@/stores/agent-store', () => ({
  useAgentStore: () => ({
    createAgent: mockCreateAgent,
    isCreating: false,
    error: null,
  }),
}));

vi.mock('@/constants/dana-code', () => ({
  DEFAULT_DANA_AGENT_CODE: 'default dana code',
}));

describe('useDanaAgentForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateAgent.mockResolvedValue({ name: 'Test Agent' });
  });

  it('should initialize form with default values', () => {
    const { result } = renderHook(() => useDanaAgentForm());

    expect(result.current.form.getValues()).toEqual({
      name: '',
      description: '',
      avatar: expect.stringMatching(/\/agent-avatar-\d+\.svg$/),
      general_agent_config: {
        dana_code: 'default dana code',
      },
      selectedKnowledge: {
        topics: [],
        documents: [],
      },
      step: 'general',
    });
  });

  it('should generate random avatar on initialization', () => {
    const { result } = renderHook(() => useDanaAgentForm());
    const avatar = result.current.form.getValues().avatar;

    expect(avatar).toMatch(/\/agent-avatar-\d+\.svg$/);
    const avatarNumber = parseInt(avatar.match(/\d+/)?.[0] || '0', 10);
    expect(avatarNumber).toBeGreaterThanOrEqual(1);
    expect(avatarNumber).toBeLessThanOrEqual(20);
  });

  it('should validate required fields on first step', async () => {
    const { result } = renderHook(() => useDanaAgentForm());

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(toast.error).toHaveBeenCalledWith('Agent name is required');
  });

  it('should validate dana code on first step', async () => {
    const { result } = renderHook(() => useDanaAgentForm());

    // Set name but not dana code
    act(() => {
      result.current.form.setValue('name', 'Test Agent');
      result.current.form.setValue('general_agent_config.dana_code', '');
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(toast.error).toHaveBeenCalledWith('Agent configuration (DANA code) is required');
  });

  it('should proceed to knowledge selection step when validation passes', async () => {
    const { result } = renderHook(() => useDanaAgentForm());

    // Set required fields
    act(() => {
      result.current.form.setValue('name', 'Test Agent');
      result.current.form.setValue('general_agent_config.dana_code', 'test dana code');
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(result.current.form.getValues().step).toBe('select-knowledge');
    expect(toast.error).not.toHaveBeenCalled();
  });

  it('should create agent when on knowledge selection step', async () => {
    const { result } = renderHook(() => useDanaAgentForm());

    // Set all required fields and move to knowledge step
    act(() => {
      result.current.form.setValue('name', 'Test Agent');
      result.current.form.setValue('description', 'Test Description');
      result.current.form.setValue('general_agent_config.dana_code', 'test dana code');
      result.current.form.setValue('step', 'select-knowledge');
      result.current.form.setValue('selectedKnowledge', {
        topics: [1],
        documents: [1],
      });
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(toast.success).toHaveBeenCalledWith('Agent "Test Agent" created successfully!');
  });

  it('should handle agent creation error', async () => {
    mockCreateAgent.mockRejectedValueOnce(new Error('Creation failed'));

    const { result } = renderHook(() => useDanaAgentForm());

    // Set all required fields and move to knowledge step
    act(() => {
      result.current.form.setValue('name', 'Test Agent');
      result.current.form.setValue('description', 'Test Description');
      result.current.form.setValue('general_agent_config.dana_code', 'test dana code');
      result.current.form.setValue('step', 'select-knowledge');
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(toast.error).toHaveBeenCalledWith('Creation failed');
  });

  it('should handle unknown error during agent creation', async () => {
    mockCreateAgent.mockRejectedValueOnce('Unknown error');

    const { result } = renderHook(() => useDanaAgentForm());

    // Set all required fields and move to knowledge step
    act(() => {
      result.current.form.setValue('name', 'Test Agent');
      result.current.form.setValue('description', 'Test Description');
      result.current.form.setValue('general_agent_config.dana_code', 'test dana code');
      result.current.form.setValue('step', 'select-knowledge');
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(toast.error).toHaveBeenCalledWith('Failed to create agent');
  });

  it('should return form, onCreateAgent, isCreating, and error', () => {
    const { result } = renderHook(() => useDanaAgentForm());

    expect(result.current.form).toBeDefined();
    expect(typeof result.current.onCreateAgent).toBe('function');
    expect(result.current.isCreating).toBe(false);
    expect(result.current.error).toBe(null);
  });

  it('should trim whitespace from name and description', async () => {
    mockCreateAgent.mockResolvedValueOnce({ name: 'Test Agent' });

    const { result } = renderHook(() => useDanaAgentForm());

    // Set fields with whitespace
    act(() => {
      result.current.form.setValue('name', '  Test Agent  ');
      result.current.form.setValue('description', '  Test Description  ');
      result.current.form.setValue('general_agent_config.dana_code', 'test dana code');
      result.current.form.setValue('step', 'select-knowledge');
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(mockCreateAgent).toHaveBeenCalledWith({
      name: 'Test Agent',
      description: 'Test Description',
      config: {
        avatar: expect.any(String),
        dana_code: 'test dana code',
        selectedKnowledge: {
          topics: [],
          documents: [],
        },
      },
    });
  });

  it('should use empty string for description when not provided', async () => {
    mockCreateAgent.mockResolvedValueOnce({ name: 'Test Agent' });

    const { result } = renderHook(() => useDanaAgentForm());

    // Set only required fields
    act(() => {
      result.current.form.setValue('name', 'Test Agent');
      result.current.form.setValue('general_agent_config.dana_code', 'test dana code');
      result.current.form.setValue('step', 'select-knowledge');
    });

    await act(async () => {
      await result.current.onCreateAgent();
    });

    expect(mockCreateAgent).toHaveBeenCalledWith({
      name: 'Test Agent',
      description: '',
      config: {
        avatar: expect.any(String),
        dana_code: 'test dana code',
        selectedKnowledge: {
          topics: [],
          documents: [],
        },
      },
    });
  });
});
