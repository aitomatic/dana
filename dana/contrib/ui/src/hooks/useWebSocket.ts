import { useEffect, useRef, useCallback } from 'react';

interface UseWebSocketOptions {
  maxRetries?: number;
  retryDelay?: number; // initial delay in ms
}

export function useWebSocket(
  url: string,
  onMessage: (msg: string) => void,
  options: UseWebSocketOptions = {}
) {
  const ws = useRef<WebSocket | null>(null);
  const retryCount = useRef(0);
  const reconnectTimeout = useRef<number | null>(null);
  const maxRetries = options.maxRetries ?? 5;
  const initialDelay = options.retryDelay ?? 1000;

  const connect = useCallback(() => {
    ws.current = new WebSocket(url);

    ws.current.onopen = () => {
      retryCount.current = 0; // Reset on successful connect
    };

    ws.current.onmessage = (event) => {
      onMessage(event.data);
    };

    ws.current.onclose = () => {
      if (retryCount.current < maxRetries) {
        const delay = initialDelay * Math.pow(2, retryCount.current);
        reconnectTimeout.current = window.setTimeout(() => {
          retryCount.current += 1;
          connect();
        }, delay);
      }
    };

    ws.current.onerror = () => {
      ws.current?.close(); // Will trigger onclose and reconnect
    };
  }, [url, onMessage, maxRetries, initialDelay]);

  useEffect(() => {
    connect();
    return () => {
      ws.current?.close();
      if (reconnectTimeout.current) window.clearTimeout(reconnectTimeout.current);
    };
  }, [connect]);

  const send = useCallback((msg: string) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(msg);
    }
  }, []);

  const close = useCallback(() => {
    ws.current?.close();
    if (reconnectTimeout.current) window.clearTimeout(reconnectTimeout.current);
  }, []);

  return { send, close, ws: ws.current };
} 