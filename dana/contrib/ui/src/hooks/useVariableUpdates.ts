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

export interface LogMessage {
  type: 'log_message';
  level: string;
  message: string;
  timestamp: number;
}

export interface BulkEvaluationProgressMessage {
  type: 'bulk_evaluation_progress';
  progress: number;
  current_question: number;
  total_questions: number;
  successful_count: number;
  failed_count: number;
  estimated_time_remaining: number;
  timestamp: number;
}

export interface BulkEvaluationResultMessage {
  type: 'bulk_evaluation_result';
  question_index: number;
  question: string;
  response: string;
  response_time: number;
  status: string;
  error?: string;
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

export interface LogUpdate {
  id: string;
  level: string;
  message: string;
  timestamp: Date;
}

export interface BulkEvaluationProgress {
  progress: number;
  current_question: number;
  total_questions: number;
  successful_count: number;
  failed_count: number;
  estimated_time_remaining: number;
  timestamp: Date;
}

export interface BulkEvaluationResult {
  id: string;
  question_index: number;
  question: string;
  response: string;
  response_time: number;
  status: 'success' | 'error';
  error?: string;
  timestamp: Date;
}

interface UseVariableUpdatesOptions {
  maxUpdates?: number; // Maximum number of updates to keep in memory
  autoConnect?: boolean; // Whether to connect automatically
}

export function useVariableUpdates(websocketId: string, options: UseVariableUpdatesOptions = {}) {
  const { maxUpdates = 100, autoConnect = true } = options;
  const [updates, setUpdates] = useState<VariableUpdate[]>([]);
  const [logUpdates, setLogUpdates] = useState<LogUpdate[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [bulkEvaluationProgress, setBulkEvaluationProgress] =
    useState<BulkEvaluationProgress | null>(null);
  const [bulkEvaluationResults, setBulkEvaluationResults] = useState<BulkEvaluationResult[]>([]);
  const updateIdCounter = useRef(0);
  const logIdCounter = useRef(0);
  const bulkResultIdCounter = useRef(0);

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
        } else if (data.type === 'log_message') {
          const logMessage = data as LogMessage;

          const newLogUpdate: LogUpdate = {
            id: `log-${++logIdCounter.current}`,
            level: logMessage.level,
            message: logMessage.message,
            timestamp: new Date(logMessage.timestamp * 1000), // Convert from Unix timestamp
          };

          setLogUpdates((prev) => {
            const newLogUpdates = [...prev, newLogUpdate];
            // Keep only the most recent log updates
            if (newLogUpdates.length > maxUpdates) {
              return newLogUpdates.slice(-maxUpdates);
            }
            return newLogUpdates;
          });
        } else if (data.type === 'bulk_evaluation_progress') {
          const progressMessage = data as BulkEvaluationProgressMessage;

          setBulkEvaluationProgress({
            progress: progressMessage.progress,
            current_question: progressMessage.current_question,
            total_questions: progressMessage.total_questions,
            successful_count: progressMessage.successful_count,
            failed_count: progressMessage.failed_count,
            estimated_time_remaining: progressMessage.estimated_time_remaining,
            timestamp: new Date(progressMessage.timestamp * 1000),
          });
        } else if (data.type === 'bulk_evaluation_result') {
          const resultMessage = data as BulkEvaluationResultMessage;

          const newResult: BulkEvaluationResult = {
            id: `bulk-result-${++bulkResultIdCounter.current}`,
            question_index: resultMessage.question_index,
            question: resultMessage.question,
            response: resultMessage.response,
            response_time: resultMessage.response_time,
            status: resultMessage.status as 'success' | 'error',
            error: resultMessage.error,
            timestamp: new Date(resultMessage.timestamp * 1000),
          };

          setBulkEvaluationResults((prev) => {
            const newResults = [...prev, newResult];
            // Keep only the most recent results
            if (newResults.length > maxUpdates) {
              return newResults.slice(-maxUpdates);
            }
            return newResults;
          });
        } else if (data.type === 'echo') {
          console.log('WebSocket connection confirmed:', data.message);
          setIsConnected(true);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
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

  // Clear all log updates
  const clearLogUpdates = useCallback(() => {
    setLogUpdates([]);
  }, []);

  // Clear bulk evaluation data
  const clearBulkEvaluationData = useCallback(() => {
    setBulkEvaluationProgress(null);
    setBulkEvaluationResults([]);
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
    logUpdates,
    bulkEvaluationProgress,
    bulkEvaluationResults,
    isConnected,
    clearUpdates,
    clearLogUpdates,
    clearBulkEvaluationData,
    getUpdatesByScope,
    getUpdatesByVariable,
    getLatestUpdateForVariable,
    connect,
    disconnect,
    send,
    readyState,
  };
}
