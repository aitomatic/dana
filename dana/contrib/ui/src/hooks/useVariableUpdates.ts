import { useState, useCallback, useRef, useEffect } from 'react';
import { useWebSocket } from './useWebSocket';

// Variable update message types
export interface VariableUpdateMessage {
  type: 'variable_change';
  scope: string;
  variable: string;
  old_value: string | null;
  new_value: string | null;
  timestamp: number;
}

export interface VariableUpdate {
  id: string;
  scope: string;
  variable: string;
  oldValue: string | null;
  newValue: string | null;
  timestamp: Date;
}

interface UseVariableUpdatesOptions {
  maxUpdates?: number; // Maximum number of updates to keep in memory
  autoConnect?: boolean; // Whether to connect automatically
}

export function useVariableUpdates(
  websocketId: string,
  options: UseVariableUpdatesOptions = {}
) {
  const { maxUpdates = 100, autoConnect = true } = options;
  const [updates, setUpdates] = useState<VariableUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const updateIdCounter = useRef(0);

  // WebSocket URL for variable updates
  const wsUrl = `ws://localhost:8080/api/agent-test/ws/${websocketId}`;

  const handleMessage = useCallback((message: string) => {
    try {
      const data = JSON.parse(message);
      
      if (data.type === 'variable_change') {
        const updateMessage = data as VariableUpdateMessage;
        
        const newUpdate: VariableUpdate = {
          id: `update-${++updateIdCounter.current}`,
          scope: updateMessage.scope,
          variable: updateMessage.variable,
          oldValue: updateMessage.old_value,
          newValue: updateMessage.new_value,
          timestamp: new Date(updateMessage.timestamp * 1000), // Convert from Unix timestamp
        };

        setUpdates(prev => {
          const newUpdates = [...prev, newUpdate];
          // Keep only the most recent updates
          if (newUpdates.length > maxUpdates) {
            return newUpdates.slice(-maxUpdates);
          }
          return newUpdates;
        });
      } else if (data.type === 'echo') {
        console.log('WebSocket connection confirmed:', data.message);
        setIsConnected(true);
      }
    } catch (error) {
      console.error('Failed to parse variable update message:', error);
    }
  }, [maxUpdates]);

  const { send, close } = useWebSocket(wsUrl, handleMessage, {
    maxRetries: 5,
    retryDelay: 1000,
  });

  // Clear all updates
  const clearUpdates = useCallback(() => {
    setUpdates([]);
  }, []);

  // Get updates by scope
  const getUpdatesByScope = useCallback((scope: string) => {
    return updates.filter(update => update.scope === scope);
  }, [updates]);

  // Get updates by variable
  const getUpdatesByVariable = useCallback((variable: string) => {
    return updates.filter(update => update.variable === variable);
  }, [updates]);

  // Get latest update for a specific variable
  const getLatestUpdateForVariable = useCallback((scope: string, variable: string) => {
    return updates
      .filter(update => update.scope === scope && update.variable === variable)
      .slice(-1)[0] || null;
  }, [updates]);

  // Connect to WebSocket (if not auto-connecting)
  const connect = useCallback(() => {
    if (!autoConnect) {
      // Manual connection logic would go here
      // The useWebSocket hook handles connection automatically
    }
  }, [autoConnect]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    close();
    setIsConnected(false);
  }, [close]);

  // Send initial connection message
  useEffect(() => {
    if (autoConnect && send) {
      // Send a ping to confirm connection
      send(JSON.stringify({ type: 'ping', websocket_id: websocketId }));
    }
  }, [send, websocketId, autoConnect]);

  return {
    updates,
    isConnected,
    clearUpdates,
    getUpdatesByScope,
    getUpdatesByVariable,
    getLatestUpdateForVariable,
    connect,
    disconnect,
  };
}