import { useCallback, useEffect, useRef } from 'react';
import { useUIStore } from '@/stores/ui-store';
import { useKnowledgeStore } from '@/stores/knowledge-store';

interface KnowledgeUpdateMessage {
  type: 'knowledge_update';
  agent_id: string;
  update_type: string;
  timestamp: string;
  data: Record<string, any>;
}

export const useUniversalKnowledgeUpdates = () => {
  const {
    setAgentDetailActiveTab,
    setKnowledgeBaseActiveSubTab,
    agentDetailActiveTab,
    knowledgeBaseActiveSubTab
  } = useUIStore();

  // Track user activity to prevent unwanted switches
  const lastUserActivityRef = useRef<number>(Date.now());
  const isUserActiveRef = useRef<boolean>(false);
  const websocketRef = useRef<WebSocket | null>(null);
  const agentIdRef = useRef<string | null>(null);

  // Track mouse and keyboard activity
  useEffect(() => {
    const updateActivity = () => {
      lastUserActivityRef.current = Date.now();
      isUserActiveRef.current = true;

      // Reset activity flag after 2 seconds of inactivity
      setTimeout(() => {
        isUserActiveRef.current = false;
      }, 2000);
    };

    const events = ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'];

    events.forEach(event => {
      document.addEventListener(event, updateActivity, { passive: true });
    });

    return () => {
      events.forEach(event => {
        document.removeEventListener(event, updateActivity);
      });
    };
  }, []);

  const handleKnowledgeUpdate = useCallback((message: KnowledgeUpdateMessage) => {
    const now = Date.now();
    const timeSinceLastActivity = now - lastUserActivityRef.current;

    console.log('[UniversalKnowledgeUpdates] Received update:', message);

    // Don't switch if user was active in the last 3 seconds
    if (isUserActiveRef.current || timeSinceLastActivity < 3000) {
      console.log('[UniversalKnowledgeUpdates] Skipping tab switch - user is active');
      return;
    }

    // Don't switch if already on Domain Knowledge tab
    if (agentDetailActiveTab === 'Resources' && knowledgeBaseActiveSubTab === 'Domain Knowledge') {
      console.log('[UniversalKnowledgeUpdates] Already on Domain Knowledge tab');
      return;
    }

    console.log('[UniversalKnowledgeUpdates] Switching to Domain Knowledge tab for agent:', message.agent_id);

    // Add a small delay to make the switch feel natural
    setTimeout(() => {
      setAgentDetailActiveTab('Resources');
      setKnowledgeBaseActiveSubTab('Domain Knowledge');
    }, 500);

    // Trigger knowledge store refresh
    const knowledgeStore = useKnowledgeStore.getState();
    knowledgeStore.fetchKnowledgeData(message.agent_id, true);
  }, [
    agentDetailActiveTab,
    knowledgeBaseActiveSubTab,
    setAgentDetailActiveTab,
    setKnowledgeBaseActiveSubTab
  ]);

  const connectWebSocket = useCallback((agentId: string) => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    agentIdRef.current = agentId;
    
    // Connect to universal knowledge updates WebSocket
    const wsUrl = `ws://localhost:8080/ws/universal-knowledge-updates/${agentId}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('[UniversalKnowledgeUpdates] WebSocket connected for agent:', agentId);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data) as KnowledgeUpdateMessage;
        if (message.type === 'knowledge_update') {
          handleKnowledgeUpdate(message);
        }
      } catch (error) {
        console.error('[UniversalKnowledgeUpdates] Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = () => {
      console.log('[UniversalKnowledgeUpdates] WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('[UniversalKnowledgeUpdates] WebSocket error:', error);
    };

    websocketRef.current = ws;
  }, [handleKnowledgeUpdate]);

  const disconnectWebSocket = useCallback(() => {
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }
    agentIdRef.current = null;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectWebSocket();
    };
  }, [disconnectWebSocket]);

  return {
    connectWebSocket,
    disconnectWebSocket,
    handleKnowledgeUpdate,
    isUserActive: isUserActiveRef.current,
    lastActivityTime: lastUserActivityRef.current
  };
};
