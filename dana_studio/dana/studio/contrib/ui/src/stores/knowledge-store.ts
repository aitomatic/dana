/* eslint-disable @typescript-eslint/no-explicit-any */
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

  // Tree update callback
  onTreeUpdate?: (agentId: string | number) => void;

  // Real-time generation tracking
  generatingNodes: Set<string>;

  // Actions
  fetchKnowledgeData: (agentId: string | number, force?: boolean) => Promise<void>;
  clearKnowledgeData: () => void;
  setCurrentAgent: (agentId: string | number | null) => void;
  setTreeUpdateCallback: (callback: (agentId: string | number) => void) => void;
  connectWebSocket: (agentId: string | number) => void;
  disconnectWebSocket: () => void;
  updateTopicStatus: (topicPath: string, status: string, progression?: number) => void;
  updateGeneratingNodes: (nodeNames: string[], isGenerating: boolean) => void;
  handleChatUpdateMessage: (message: any) => void;
}

// Debounce delay for API calls (in milliseconds)
const DEBOUNCE_DELAY = 500;

// Utility function to parse node names from processing messages
const parseNodeNameFromMessage = (message: string): string | null => {
  const match = message.match(/Processing \d+\/\d+: (.+)$/);
  return match ? match[1].trim() : null;
};

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  // Initial state
  domainKnowledge: null,
  knowledgeStatus: null,
  isLoading: false,
  error: null,
  currentAgentId: null,
  websocket: null,
  lastFetchTime: 0,
  onTreeUpdate: undefined,
  generatingNodes: new Set(),

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

      // Trigger tree update callback if available
      const currentState = get();
      if (currentState.onTreeUpdate) {
        console.log('[KnowledgeStore] Triggering tree update callback for agent:', agentId);
        currentState.onTreeUpdate(agentId);
      }
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
      generatingNodes: new Set(),
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

  setTreeUpdateCallback: (callback: (agentId: string | number) => void) => {
    console.log('[KnowledgeStore] Setting tree update callback');
    set({ onTreeUpdate: callback });
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
          console.log('[KnowledgeStore] Received WebSocket message:', msg);

          if (msg.type === 'knowledge_status_update') {
            console.log('🔄 [DEBUG] Generation Completes - knowledge_status_update received:', {
              path: msg.path,
              status: msg.status,
              progression: msg.progression,
              fullMessage: msg,
            });

            // Handle specific topic updates
            if (msg.path && msg.status) {
              console.log('[KnowledgeStore] Updating specific topic:', msg.path, msg.status);
              console.log('🔄 [DEBUG] About to call updateTopicStatus with:', {
                topicPath: msg.path,
                status: msg.status,
                progression: msg.progression,
              });
              get().updateTopicStatus(msg.path, msg.status, msg.progression);
            } else {
              // Fallback to full refresh for general updates
              console.log('[KnowledgeStore] General knowledge status update, refreshing data');
              setTimeout(() => {
                const currentState = get();
                if (currentState.currentAgentId === agentId) {
                  get().fetchKnowledgeData(agentId, true); // Force refresh
                }
              }, 100);
            }
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

  updateTopicStatus: (topicPath: string, status: string, progression?: number) => {
    const state = get();

    if (!state.knowledgeStatus) {
      console.warn('[KnowledgeStore] Cannot update topic status - no knowledge status data');
      return;
    }

    console.log('[KnowledgeStore] Updating topic status:', { topicPath, status, progression });
    console.log('🔄 [DEBUG] updateTopicStatus called with:', {
      topicPath,
      status,
      progression,
      currentGeneratingNodes: Array.from(state.generatingNodes),
    });

    const updatedTopics = state.knowledgeStatus.topics.map((topic) => {
      if (topic.path === topicPath) {
        return {
          ...topic,
          status: status as 'pending' | 'in_progress' | 'success' | 'failed',
          last_generated: status === 'success' ? new Date().toISOString() : topic.last_generated,
        };
      }
      return topic;
    });

    // Clear the node from generatingNodes Set when generation completes (success or failed)
    let updatedGeneratingNodes = state.generatingNodes;
    if (status === 'success' || status === 'failed') {
      // Extract node name from topic path (last part after ' - ')
      const nodeName = topicPath.split(' - ').pop();
      console.log('🔄 [DEBUG] Attempting to clear generating node:', {
        topicPath,
        extractedNodeName: nodeName,
        currentGeneratingNodes: Array.from(state.generatingNodes),
        willClear: nodeName && state.generatingNodes.has(nodeName),
      });

      if (nodeName) {
        const newSet = new Set(state.generatingNodes);
        const wasPresent = newSet.has(nodeName);
        newSet.delete(nodeName);
        updatedGeneratingNodes = newSet;
        console.log(
          '[KnowledgeStore] Cleared generating node:',
          nodeName,
          'due to status:',
          status,
          'wasPresent:',
          wasPresent,
        );
        console.log(
          '🔄 [DEBUG] After clearing - generating nodes:',
          Array.from(updatedGeneratingNodes),
        );
      } else {
        console.log('🔄 [DEBUG] No node name extracted from topicPath:', topicPath);
      }
    }

    set({
      knowledgeStatus: {
        ...state.knowledgeStatus,
        topics: updatedTopics,
      },
      generatingNodes: updatedGeneratingNodes,
    });

    // Trigger tree update callback if available
    if (state.onTreeUpdate && state.currentAgentId) {
      console.log('[KnowledgeStore] Triggering tree update callback for topic status change');
      state.onTreeUpdate(state.currentAgentId);
    }
  },

  updateGeneratingNodes: (nodeNames: string[], isGenerating: boolean) => {
    const state = get();

    set((prevState) => {
      const newSet = new Set(prevState.generatingNodes);
      if (isGenerating) {
        nodeNames.forEach((name) => newSet.add(name));
      } else {
        nodeNames.forEach((name) => newSet.delete(name));
      }

      console.log('[KnowledgeStore] Updated generating nodes:', {
        nodeNames,
        isGenerating,
        totalGenerating: newSet.size,
      });

      return { generatingNodes: newSet };
    });

    // Trigger tree update callback if available
    if (state.onTreeUpdate && state.currentAgentId) {
      console.log('[KnowledgeStore] Triggering tree update callback for generating nodes change');
      state.onTreeUpdate(state.currentAgentId);
    }
  },

  handleChatUpdateMessage: (message: any) => {
    console.log('🔄 [DEBUG] handleChatUpdateMessage received:', {
      tool_name: message.tool_name,
      status: message.status,
      content: message.content,
      fullMessage: message,
    });

    // Handle generation messages from chat WebSocket
    if (message.tool_name === 'generate_knowledge' && message.status === 'in_progress') {
      const nodeName = parseNodeNameFromMessage(message.content);
      console.log('🔄 [DEBUG] Parsed node name from in_progress message:', {
        originalContent: message.content,
        parsedNodeName: nodeName,
      });
      if (nodeName) {
        console.log('[KnowledgeStore] Node generation started:', nodeName);
        get().updateGeneratingNodes([nodeName], true);
      }
    } else if (message.tool_name === 'generate_knowledge' && message.status === 'finish') {
      const nodeName = parseNodeNameFromMessage(message.content);
      console.log('🔄 [DEBUG] Parsed node name from finish message:', {
        originalContent: message.content,
        parsedNodeName: nodeName,
      });
      if (nodeName) {
        console.log('[KnowledgeStore] Node generation finished:', nodeName);
        get().updateGeneratingNodes([nodeName], false);
      }
    }
  },
}));
