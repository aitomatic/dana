import { create } from 'zustand';
import { apiService } from '@/lib/api';
import type { DomainKnowledgeResponse } from '@/types/domainKnowledge';
import type { KnowledgeStatusResponse } from '@/lib/api';

interface KnowledgeState {
  // Data
  domainKnowledge: DomainKnowledgeResponse | null;
  knowledgeStatus: KnowledgeStatusResponse | null;

  // Loading states
  isLoading: boolean;
  error: string | null;

  // Current agent being tracked
  currentAgentId: string | number | null;

  // WebSocket connection
  websocket: WebSocket | null;
  lastFetchTime: number;

  // Actions
  fetchKnowledgeData: (agentId: string | number, force?: boolean) => Promise<void>;
  clearKnowledgeData: () => void;
  setCurrentAgent: (agentId: string | number | null) => void;
  connectWebSocket: (agentId: string | number) => void;
  disconnectWebSocket: () => void;
}

// Debounce delay for API calls (in milliseconds)
const DEBOUNCE_DELAY = 500;

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  // Initial state
  domainKnowledge: null,
  knowledgeStatus: null,
  isLoading: false,
  error: null,
  currentAgentId: null,
  websocket: null,
  lastFetchTime: 0,

  fetchKnowledgeData: async (agentId: string | number, force = false) => {
    const state = get();
    const now = Date.now();

    // Debouncing: if we fetched recently and it's the same agent, skip unless forced
    if (
      !force &&
      state.currentAgentId === agentId &&
      state.domainKnowledge &&
      state.knowledgeStatus &&
      now - state.lastFetchTime < DEBOUNCE_DELAY
    ) {
      console.log('[KnowledgeStore] Skipping fetch due to debouncing');
      return;
    }

    set({ isLoading: true, error: null, lastFetchTime: now });

    try {
      console.log('[KnowledgeStore] Fetching knowledge data for agent:', agentId);

      // Fetch both domain knowledge and knowledge status in parallel
      const [domainResponse, statusResponse] = await Promise.all([
        apiService.getDomainKnowledge(agentId),
        apiService.getKnowledgeStatus(agentId).catch(() => ({ topics: [] })),
      ]);

      set({
        domainKnowledge: domainResponse,
        knowledgeStatus: statusResponse as KnowledgeStatusResponse,
        currentAgentId: agentId,
        isLoading: false,
        error: null,
      });

      console.log('[KnowledgeStore] Successfully fetched knowledge data');
    } catch (error) {
      console.error('[KnowledgeStore] Error fetching knowledge data:', error);
      set({
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to fetch knowledge data',
      });
    }
  },

  clearKnowledgeData: () => {
    console.log('[KnowledgeStore] Clearing knowledge data');
    set({
      domainKnowledge: null,
      knowledgeStatus: null,
      currentAgentId: null,
      error: null,
      lastFetchTime: 0,
    });
  },

  setCurrentAgent: (agentId: string | number | null) => {
    const state = get();

    if (state.currentAgentId !== agentId) {
      console.log('[KnowledgeStore] Setting current agent:', agentId);

      // Clear data when switching agents
      if (agentId === null) {
        get().clearKnowledgeData();
        get().disconnectWebSocket();
      } else {
        set({ currentAgentId: agentId });

        // Fetch data for new agent
        get().fetchKnowledgeData(agentId);

        // Connect WebSocket for new agent
        get().connectWebSocket(agentId);
      }
    }
  },

  connectWebSocket: (agentId: string | number) => {
    const state = get();

    // Disconnect existing WebSocket if any
    if (state.websocket) {
      state.websocket.close();
    }

    console.log('[KnowledgeStore] Connecting WebSocket for agent:', agentId);

    try {
      const ws = new WebSocket('ws://localhost:8080/ws/knowledge-status');

      ws.onopen = () => {
        console.log('[KnowledgeStore] WebSocket connected');
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);
          if (msg.type === 'knowledge_status_update') {
            console.log('[KnowledgeStore] Received knowledge status update, refreshing data');

            // Use a small delay to debounce rapid updates
            setTimeout(() => {
              const currentState = get();
              if (currentState.currentAgentId === agentId) {
                get().fetchKnowledgeData(agentId, true); // Force refresh
              }
            }, 100);
          }
        } catch (error) {
          console.warn('[KnowledgeStore] Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log('[KnowledgeStore] WebSocket closed:', event.code, event.reason);

        // Attempt to reconnect after a delay if not intentionally closed
        if (event.code !== 1000 && get().currentAgentId === agentId) {
          setTimeout(() => {
            const currentState = get();
            if (currentState.currentAgentId === agentId) {
              console.log('[KnowledgeStore] Attempting to reconnect WebSocket');
              get().connectWebSocket(agentId);
            }
          }, 3000);
        }
      };

      ws.onerror = (error) => {
        console.error('[KnowledgeStore] WebSocket error:', error);
      };

      set({ websocket: ws });
    } catch (error) {
      console.error('[KnowledgeStore] Failed to create WebSocket:', error);
    }
  },

  disconnectWebSocket: () => {
    const state = get();

    if (state.websocket) {
      console.log('[KnowledgeStore] Disconnecting WebSocket');
      state.websocket.close(1000, 'Intentional disconnect');
      set({ websocket: null });
    }
  },
}));
