/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useCallback, useState } from 'react';

export interface ChatUpdateMessage {
  tool_name: string;
  content: string;
  status: 'init' | 'in_progress' | 'finish' | 'error';
  progression?: number;
}

export interface WebSocketMessage {
  type: 'chat_update' | 'echo';
  message?: ChatUpdateMessage;
  data?: any;
  timestamp?: number;
}

interface UseSmartChatWebSocketOptions {
  agentId: string;
  onChatUpdate?: (message: ChatUpdateMessage) => void;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
  enabled?: boolean; // Allow enabling/disabling the connection
}

export const useSmartChatWebSocket = ({
  agentId,
  onChatUpdate,
  onConnect,
  onDisconnect,
  onError,
  enabled = true,
}: UseSmartChatWebSocketOptions) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const callbacksRef = useRef({ onChatUpdate, onConnect, onDisconnect, onError });
  const [isConnected, setIsConnected] = useState(false);
  const [connectionState, setConnectionState] = useState<
    'disconnected' | 'connecting' | 'connected' | 'reconnecting'
  >('disconnected');

  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000;

  // Update callbacks ref when they change (without triggering reconnection)
  useEffect(() => {
    callbacksRef.current = { onChatUpdate, onConnect, onDisconnect, onError };
  }, [onChatUpdate, onConnect, onDisconnect, onError]);

  const cleanupConnection = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      // Remove event listeners to prevent callbacks during cleanup
      wsRef.current.onopen = null;
      wsRef.current.onclose = null;
      wsRef.current.onmessage = null;
      wsRef.current.onerror = null;

      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      wsRef.current = null;
    }

    setIsConnected(false);
    setConnectionState('disconnected');
  }, []);

  const connect = useCallback(() => {
    // Don't connect if already connected or connecting
    if (
      wsRef.current?.readyState === WebSocket.OPEN ||
      wsRef.current?.readyState === WebSocket.CONNECTING ||
      !enabled ||
      !agentId
    ) {
      return;
    }

    try {
      setConnectionState(reconnectAttemptsRef.current > 0 ? 'reconnecting' : 'connecting');

      // Get WebSocket URL from environment or construct from current location
      const wsUrl = `http://localhost:8080/api/agents/ws/dana-chat/${agentId}`;

      console.log(
        `${reconnectAttemptsRef.current > 0 ? 'Reconnecting' : 'Connecting'} WebSocket for agent ${agentId}...`,
      );

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log(`✅ WebSocket connected for agent ${agentId}`);
        reconnectAttemptsRef.current = 0;
        setIsConnected(true);
        setConnectionState('connected');
        callbacksRef.current.onConnect?.();
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);

          if (data.type === 'chat_update' && data.message) {
            callbacksRef.current.onChatUpdate?.(data.message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      ws.onclose = (event) => {
        console.log(`🔌 WebSocket disconnected for agent ${agentId}`, {
          code: event.code,
          reason: event.reason,
        });

        wsRef.current = null;
        setIsConnected(false);
        setConnectionState('disconnected');
        callbacksRef.current.onDisconnect?.();

        // Only attempt to reconnect if it wasn't a clean close and we haven't exceeded max attempts
        const shouldReconnect =
          enabled &&
          event.code !== 1000 && // 1000 = normal closure
          reconnectAttemptsRef.current < maxReconnectAttempts;

        if (shouldReconnect) {
          reconnectAttemptsRef.current++;
          console.log(
            `🔄 Scheduling reconnect attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${reconnectDelay}ms`,
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            if (enabled && agentId) {
              // Double-check conditions before reconnecting
              connect();
            }
          }, reconnectDelay);
        } else {
          console.log(
            `❌ Not reconnecting: enabled=${enabled}, code=${event.code}, attempts=${reconnectAttemptsRef.current}/${maxReconnectAttempts}`,
          );
        }
      };

      ws.onerror = (error) => {
        console.error(`❌ WebSocket error for agent ${agentId}:`, error);
        callbacksRef.current.onError?.(error);
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      setConnectionState('disconnected');
      callbacksRef.current.onError?.(error as Event);
    }
  }, [agentId, enabled]);

  const disconnect = useCallback(() => {
    console.log(`🔌 Manually disconnecting WebSocket for agent ${agentId}`);
    cleanupConnection();
  }, [agentId, cleanupConnection]);

  const sendMessage = useCallback((message: any) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
      return true;
    }
    console.warn('Cannot send message: WebSocket not connected');
    return false;
  }, []);

  // Main connection effect - only depends on agentId and enabled
  useEffect(() => {
    if (enabled && agentId) {
      connect();
    } else {
      cleanupConnection();
    }

    return () => {
      cleanupConnection();
    };
  }, [agentId, enabled]); // Intentionally minimal deps to prevent reconnections

  // Reset reconnection attempts when agentId changes
  useEffect(() => {
    reconnectAttemptsRef.current = 0;
  }, [agentId]);

  return {
    isConnected,
    connectionState,
    connect,
    disconnect,
    sendMessage,
    reconnectAttempts: reconnectAttemptsRef.current,
    maxReconnectAttempts,
  };
};
