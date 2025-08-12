import React, { useEffect, useRef } from 'react';
import type { LogUpdate } from '@/hooks/useVariableUpdates';

interface LogViewerProps {
  logs: LogUpdate[];
  className?: string;
  showTimestamps?: boolean;
  autoScroll?: boolean;
  maxHeight?: string;
}

const LogViewer: React.FC<LogViewerProps> = ({
  logs,
  className = '',
  showTimestamps = false,
  autoScroll = true,
  maxHeight = '300px',
}) => {
  const logContainerRef = useRef<HTMLDivElement>(null);

  // Auto scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  const getLogLevelColor = (level: string) => {
    switch (level.toLowerCase()) {
      case 'error':
        return 'text-red-600 dark:text-red-400';
      case 'warning':
      case 'warn':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'debug':
        return 'text-blue-600 dark:text-blue-400';
      case 'info':
      default:
        return 'text-gray-700 dark:text-gray-300';
    }
  };

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  };

  if (logs.length === 0) {
    return (
      <div
        className={`flex items-center justify-center h-16 text-gray-500 dark:text-gray-400 text-sm ${className}`}
      >
        No logs yet...
      </div>
    );
  }

  return (
    <div
      className={`bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg ${className}`}
    >
      <div className="px-3 py-2 bg-gray-100 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600 text-xs font-medium text-gray-600 dark:text-gray-300 rounded-t-lg">
        Agent Logs ({logs.length})
      </div>
      <div
        ref={logContainerRef}
        className="p-3 overflow-y-auto font-mono text-xs bg-gray-50 dark:bg-gray-800"
        style={{ maxHeight }}
      >
        {logs.map((log) => (
          <div key={log.id} className="mb-1 flex items-start gap-2">
            {showTimestamps && (
              <span className="text-gray-400 dark:text-gray-500 shrink-0 text-[10px]">
                {formatTimestamp(log.timestamp)}
              </span>
            )}
            <span
              className={`shrink-0 uppercase text-[10px] font-medium ${getLogLevelColor(log.level)}`}
            >
              {log.level}:
            </span>
            <span className="text-gray-800 dark:text-gray-200 break-words min-w-0">
              {log.message}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LogViewer;
