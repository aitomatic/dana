import useWebSocketLib from 'react-use-websocket';
import { useCallback } from 'react';

interface UseWebSocketOptions {
  maxRetries?: number;
  retryDelay?: number; // initial delay in ms
}

export function useWebSocket(
  url: string,
  onMessage: (msg: string) => void,
  options: UseWebSocketOptions = {}
) {
  const maxRetries = options.maxRetries ?? 5;
  const initialDelay = options.retryDelay ?? 1000;

  const {
    sendMessage,
    lastMessage,
    readyState,
    getWebSocket
  } = useWebSocketLib(url, {
    onMessage: (event) => {
      onMessage(event.data);
    },
    shouldReconnect: (closeEvent) => {
      // Reconnect on any close event (unless explicitly closed)
      return closeEvent.code !== 1000;
    },
    reconnectAttempts: maxRetries,
    reconnectInterval: (attemptNumber) => {
      // Exponential backoff: initialDelay * 2^attemptNumber
      return Math.min(initialDelay * Math.pow(2, attemptNumber), 30000);
    },
  });

  const send = useCallback((msg: string) => {
    sendMessage(msg);
  }, [sendMessage]);

  const close = useCallback(() => {
    const ws = getWebSocket();
    if (ws) {
      ws.close(1000, 'Manual close');
    }
  }, [getWebSocket]);

  return { 
    send, 
    close, 
    ws: getWebSocket(),
    readyState,
    lastMessage
  };
} 