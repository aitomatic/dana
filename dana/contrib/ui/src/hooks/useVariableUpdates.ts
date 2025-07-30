import { useState, useCallback, useRef, useEffect } from 'react';
import useWebSocketLib from 'react-use-websocket';

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

export function useVariableUpdates(websocketId: string, options: UseVariableUpdatesOptions = {}) {
  const { maxUpdates = 100, autoConnect = true } = options;
  const [updates, setUpdates] = useState<VariableUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const updateIdCounter = useRef(0);

  // WebSocket URL for variable updates
  const wsUrl = `ws://localhost:8080/api/agent-test/ws/${websocketId}`;

  const handleMessage = useCallback(
    (message: string) => {
      try {
        const data = JSON.parse(message);

        if (data.type === 'variable_change' && data.variable === 'step') {
          const updateMessage = data as VariableUpdateMessage;

          const newUpdate: VariableUpdate = {
            id: `update-${++updateIdCounter.current}`,
            scope: updateMessage.scope,
            variable: updateMessage.variable,
            oldValue: updateMessage.old_value,
            newValue: updateMessage.new_value,
            timestamp: new Date(updateMessage.timestamp * 1000), // Convert from Unix timestamp
          };

          setUpdates((prev) => {
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
    },
    [maxUpdates],
  );

  const { sendMessage, readyState, getWebSocket } = useWebSocketLib(wsUrl, {
    onMessage: (event) => {
      handleMessage(event.data);
    },
    shouldReconnect: (closeEvent) => {
      // Reconnect on any close event (unless explicitly closed)
      return closeEvent.code !== 1000;
    },
    reconnectAttempts: 5,
    reconnectInterval: (attemptNumber) => {
      // Exponential backoff: 1000ms * 2^attemptNumber, max 30 seconds
      return Math.min(1000 * Math.pow(2, attemptNumber), 30000);
    },
  });

  // Clear all updates
  const clearUpdates = useCallback(() => {
    setUpdates([]);
  }, []);

  // Get updates by scope
  const getUpdatesByScope = useCallback(
    (scope: string) => {
      return updates.filter((update) => update.scope === scope);
    },
    [updates],
  );

  // Get updates by variable
  const getUpdatesByVariable = useCallback(
    (variable: string) => {
      return updates.filter((update) => update.variable === variable);
    },
    [updates],
  );

  // Get latest update for a specific variable
  const getLatestUpdateForVariable = useCallback(
    (scope: string, variable: string) => {
      return (
        updates
          .filter((update) => update.scope === scope && update.variable === variable)
          .slice(-1)[0] || null
      );
    },
    [updates],
  );

  // Send message function
  const send = useCallback(
    (message: string) => {
      if (readyState === 1) {
        // WebSocket.OPEN = 1
        sendMessage(message);
      }
    },
    [sendMessage, readyState],
  );

  // Connect to WebSocket (if not auto-connecting)
  const connect = useCallback(() => {
    if (!autoConnect) {
      // Manual connection logic would go here
      // The react-use-websocket hook handles connection automatically
    }
  }, [autoConnect]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    const ws = getWebSocket();
    if (ws) {
      ws.close(1000, 'Manual disconnect');
    }
    setIsConnected(false);
  }, [getWebSocket]);

  // Update connection status based on readyState
  useEffect(() => {
    setIsConnected(readyState === 1); // WebSocket.OPEN = 1
  }, [readyState]);

  // Send initial connection message when connected
  useEffect(() => {
    if (autoConnect && readyState === 1) {
      // WebSocket.OPEN = 1
      // Send a ping to confirm connection
      sendMessage(JSON.stringify({ type: 'ping', websocket_id: websocketId }));
    }
  }, [sendMessage, websocketId, autoConnect, readyState]);

  return {
    updates,
    isConnected,
    clearUpdates,
    getUpdatesByScope,
    getUpdatesByVariable,
    getLatestUpdateForVariable,
    connect,
    disconnect,
    send,
    readyState,
  };
}
