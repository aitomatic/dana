import { useEffect, useRef } from 'react';

// WebSocket message types
interface WebSocketMessage {
  type: 'question_generation' | 'structuring';
  knowledge_id: string;
  timestamp: number;
  message: {
    tool_name: string;
    content: string;
    status: 'init' | 'in_progress' | 'finish' | 'error' | 'completed' | 'question_generated' | 'generating';
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
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080/api';
  const wsBaseUrl = apiBaseUrl.replace(/^http/, 'ws');
  return `${wsBaseUrl}/v2/knowledge/ws/${knowledgeId}`;
};

// Map WebSocket status to node status
const mapWebSocketStatusToNodeStatus = (
  toolName: string,
  status: string
): string | null => {
  // Support both naming conventions for question bank generation
  if (toolName === 'generate_question_bank' || toolName === 'question_bank_generation') {
    switch (status) {
      case 'init':
      case 'in_progress':
        return 'generating';
      case 'generating':  // Map directly (backend sends this during generation)
        return 'generating';
      case 'question_generated':  // Map directly (current backend format)
        return 'question_generated';
      case 'completed':  // Knowledge generation complete - maps to "completed" (green)
        return 'completed';
      case 'finish':  // Backward compatibility
        return 'question_generated';
      case 'error':
        return 'failed';
      default:
        return null;
    }
  }
  
  // Handle knowledge generation tool
  if (toolName === 'generate_knowledge') {
    switch (status) {
      case 'init':
      case 'in_progress':
      case 'generating':
        return 'generating';
      case 'completed':
      case 'success':
        return 'completed';
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
 * @param onStatusUpdate - Callback when a node status is updated (nodePath, status, type)
 */
export const useKnowledgePackWebSocket = (
  knowledgePackId: number | null,
  onStatusUpdate: (nodePath: string, status: string, type: string) => void
) => {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const currentKnowledgeIdRef = useRef<number | null>(null);
  const maxReconnectAttempts = 5;
  const baseReconnectDelay = 1000; // Start at 1 second
  
  // Use ref for callback to avoid reconnection on callback changes
  const onStatusUpdateRef = useRef(onStatusUpdate);
  
  // Keep ref up to date
  useEffect(() => {
    onStatusUpdateRef.current = onStatusUpdate;
  }, [onStatusUpdate]);

  const connect = (knowledgeId: number) => {
    try {
      // Prevent duplicate connections to the same knowledge pack
      if (wsRef.current && currentKnowledgeIdRef.current === knowledgeId) {
        console.log('⚠️ [KP WebSocket] Connection already exists for:', knowledgeId);
        
        // Check if existing connection is still open
        if (wsRef.current.readyState === WebSocket.OPEN || 
            wsRef.current.readyState === WebSocket.CONNECTING) {
          console.log('✅ [KP WebSocket] Using existing connection');
          return;
        } else {
          console.log('🔄 [KP WebSocket] Existing connection closed, reconnecting...');
        }
      }

      // Close any existing connection before creating a new one
      if (wsRef.current) {
        console.log('🔌 [KP WebSocket] Closing previous connection');
        wsRef.current.close();
        wsRef.current = null;
      }

      const wsUrl = getWebSocketUrl(knowledgeId);
      console.log('🔌 [KP WebSocket] Connecting to:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      currentKnowledgeIdRef.current = knowledgeId;

      ws.onopen = () => {
        console.log('✅ [KP WebSocket] Connected successfully');
        reconnectAttemptsRef.current = 0; // Reset reconnect attempts on success
      };

      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          console.log('📨 [KP WebSocket] Message received:', data);

          // ✅ VALIDATION: Check if message is for this KP
          const messageKpId = parseInt(data.knowledge_id);
          if (messageKpId !== knowledgeId) {
            console.warn('⚠️ [KP WebSocket] Ignoring message for different KP:', {
              messageKpId,
              subscribedKpId: knowledgeId,
              messageType: data.type,
            });
            return; // Ignore messages for other KPs
          }

          // Process messages with path_parts (both question_generation and knowledge_generation)
          if (data.message.path_parts) {
            const { tool_name, status, path_parts } = data.message;

            // Convert path_parts to nodePath
            const nodePath = convertPathPartsToNodePath(path_parts);

            // Map WebSocket status to node status
            const nodeStatus = mapWebSocketStatusToNodeStatus(tool_name, status);

            console.log('🔄 [KP WebSocket] Processing message:', {
              type: data.type,
              tool_name,
              originalStatus: status,
              mappedStatus: nodeStatus,
              path_parts,
              convertedNodePath: nodePath,
              kpId: knowledgeId,
            });

            if (nodeStatus && nodePath) {
              console.log('✅ [KP WebSocket] Calling status update callback for KP:', knowledgeId);
              onStatusUpdateRef.current(nodePath, nodeStatus, data.type);
            } else {
              console.warn('⚠️ [KP WebSocket] Skipping update:', {
                hasNodeStatus: !!nodeStatus,
                hasNodePath: !!nodePath,
              });
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
      currentKnowledgeIdRef.current = null;
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
