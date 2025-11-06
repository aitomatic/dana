import { useEffect, useRef } from 'react';

// WebSocket message types
interface WebSocketMessage {
  type: 'question_generation' | 'structuring';
  knowledge_id: string;
  timestamp: number;
  message: {
    tool_name: string;
    content: string;
    status: 'init' | 'in_progress' | 'finish' | 'error';
    progression?: number;
    path_parts?: string[];
  };
}

// Convert path_parts array to nodePath string (excluding root)
const convertPathPartsToNodePath = (pathParts: string[]): string => {
  // Remove first element (root) and join with " - "
  return pathParts.slice(1).join(' - ');
};

// Get WebSocket URL from environment
const getWebSocketUrl = (knowledgeId: number): string => {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';
  const wsBaseUrl = apiBaseUrl.replace(/^http/, 'ws');
  return `${wsBaseUrl}/api/v2/knowledge/ws/${knowledgeId}`;
};

// Map WebSocket status to node status
const mapWebSocketStatusToNodeStatus = (
  toolName: string,
  status: string
): string | null => {
  if (toolName === 'generate_question_bank') {
    switch (status) {
      case 'init':
      case 'in_progress':
        return 'generating';
      case 'finish':
        return 'question_generated';
      case 'error':
        return 'failed';
      default:
        return null;
    }
  }
  return null;
};

/**
 * Custom hook to manage WebSocket connection for knowledge pack status updates
 * 
 * @param knowledgePackId - The knowledge pack ID to subscribe to
 * @param onStatusUpdate - Callback when a node status is updated (nodePath, status)
 */
export const useKnowledgePackWebSocket = (
  knowledgePackId: number | null,
  onStatusUpdate: (nodePath: string, status: string) => void
) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // Start at 1 second

  const connect = (knowledgeId: number) => {
    try {
      const wsUrl = getWebSocketUrl(knowledgeId);
      console.log('🔌 [KP WebSocket] Connecting to:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('✅ [KP WebSocket] Connected successfully');
        reconnectAttemptsRef.current = 0; // Reset reconnect attempts on success
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          console.log('📨 [KP WebSocket] Message received:', data);

          // Only process question_generation type messages
          if (data.type === 'question_generation' && data.message.path_parts) {
            const { tool_name, status, path_parts } = data.message;

            // Convert path_parts to nodePath
            const nodePath = convertPathPartsToNodePath(path_parts);

            // Map WebSocket status to node status
            const nodeStatus = mapWebSocketStatusToNodeStatus(tool_name, status);

            if (nodeStatus && nodePath) {
              console.log('🔄 [KP WebSocket] Updating node status:', {
                nodePath,
                nodeStatus,
                path_parts,
              });
              onStatusUpdate(nodePath, nodeStatus);
            }
          }
        } catch (error) {
          console.error('❌ [KP WebSocket] Error parsing message:', error);
        }
      };

      ws.onerror = (error) => {
        console.error('❌ [KP WebSocket] Error:', error);
      };

      ws.onclose = (event) => {
        console.log('🔌 [KP WebSocket] Connection closed:', event.code, event.reason);

        // Attempt reconnection with exponential backoff
        if (reconnectAttemptsRef.current < maxReconnectAttempts) {
          const delay = baseReconnectDelay * Math.pow(2, reconnectAttemptsRef.current);
          console.log(
            `🔄 [KP WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})...`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttemptsRef.current += 1;
            connect(knowledgeId);
          }, delay);
        } else {
          console.log('❌ [KP WebSocket] Max reconnection attempts reached');
        }
      };
    } catch (error) {
      console.error('❌ [KP WebSocket] Connection error:', error);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      console.log('🔌 [KP WebSocket] Disconnecting...');
      wsRef.current.close();
      wsRef.current = null;
    }
  };

  useEffect(() => {
    if (knowledgePackId) {
      connect(knowledgePackId);
    }

    // Cleanup on unmount or when knowledgePackId changes
    return () => {
      disconnect();
    };
  }, [knowledgePackId]);

  return {
    disconnect,
  };
};
