import { useState, useCallback, useRef, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { apiService } from '@/lib/api';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import {
  Send,
  Loader2,
  Trash2,
  ChevronDown,
  ChevronUp,
  X,
  MessageSquare,
  FileSpreadsheet,
  Upload,
  FileText,
  Settings,
  BarChart3,
  Download,
} from 'lucide-react';
import { HybridRenderer } from '@/pages/Agents/chat/hybrid-renderer';
import { useVariableUpdates } from '@/hooks/useVariableUpdates';
import LogViewer from '@/components/LogViewer';

// Message interface for the test chat
interface TestChatMessage {
  id: string;
  role: 'user' | 'agent' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    questionIndex?: number;
    responseTime?: number;
    status?: 'success' | 'error';
    expectedAnswer?: string;
    isBulkEvaluation?: boolean;
  };
}

interface AgentTestChatProps {
  agentCode: string;
  agentName: string;
  agentDescription: string;
  className?: string;
  currentFolder?: string;
}

type ChatMode = 'individual' | 'bulk';

interface CSVRow {
  question: string;
  expected_answer?: string;
  context?: string;
  category?: string;
  [key: string]: string | undefined;
}

interface ParsedCSV {
  headers: string[];
  rows: CSVRow[];
  questionColumn: string;
  isValid: boolean;
  errors: string[];
}

interface BulkEvaluationResult {
  question: string;
  response: string;
  responseTime: number;
  status: 'success' | 'error';
  error?: string;
  expectedAnswer?: string;
  rowIndex: number;
}

interface BulkEvaluationState {
  isRunning: boolean;
  isPaused: boolean;
  progress: number;
  totalQuestions: number;
  currentQuestionIndex: number;
  results: BulkEvaluationResult[];
  startTime: Date | null;
  estimatedTimeRemaining: number;
}

const AgentTestChat = ({
  agentCode,
  agentName,
  agentDescription,
  className,
  currentFolder,
}: AgentTestChatProps) => {
  const [messages, setMessages] = useState<TestChatMessage[]>([
    {
      id: '1',
      role: 'agent',
      content: "Hi, I'm Georgia! How can I help you today?",
      timestamp: new Date(),
    },
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTesting, setIsTesting] = useState(false);
  const [showLogs, setShowLogs] = useState(false);
  const [hideLogs, setHideLogs] = useState(false);

  // Chat mode state
  const [chatMode, setChatMode] = useState<ChatMode>('individual');

  // Bulk evaluation state
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [parsedCSV, setParsedCSV] = useState<ParsedCSV | null>(null);
  const [isParsingCSV, setIsParsingCSV] = useState(false);

  // Bulk evaluation configuration
  const [batchSize, setBatchSize] = useState(5);
  const [showConfig, setShowConfig] = useState(false);

  // Bulk evaluation state
  const [bulkEvaluation, setBulkEvaluation] = useState<BulkEvaluationState>({
    isRunning: false,
    isPaused: false,
    progress: 0,
    totalQuestions: 0,
    currentQuestionIndex: 0,
    results: [],
    startTime: null,
    estimatedTimeRemaining: 0,
  });

  // Generate unique WebSocket ID for this test session
  const [websocketId] = useState(
    () => `agenttest-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
  );

  // WebSocket for variable updates and log streaming
  const {
    logUpdates,
    bulkEvaluationProgress,
    bulkEvaluationResults,
    disconnect,
    clearLogUpdates,
    clearBulkEvaluationData,
  } = useVariableUpdates(websocketId, {
    maxUpdates: 50,
    autoConnect: true,
  });

  // Ref for the messages container to enable auto-scroll
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when messages change
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  // Scroll to bottom whenever messages change
  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Clean up WebSocket on component unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  // Update bulk evaluation state from WebSocket progress updates
  useEffect(() => {
    if (bulkEvaluationProgress && bulkEvaluation.isRunning) {
      setBulkEvaluation((prev) => ({
        ...prev,
        progress: bulkEvaluationProgress.progress,
        currentQuestionIndex: bulkEvaluationProgress.current_question,
        estimatedTimeRemaining: bulkEvaluationProgress.estimated_time_remaining,
      }));
    }
  }, [bulkEvaluationProgress, bulkEvaluation.isRunning]);

  // Add individual question results to messages as they come in
  useEffect(() => {
    if (bulkEvaluationResults.length > 0 && bulkEvaluation.isRunning) {
      const latestResult = bulkEvaluationResults[bulkEvaluationResults.length - 1];

      // Add question message
      const questionMessage: TestChatMessage = {
        id: `q-${latestResult.id}`,
        role: 'user',
        content: latestResult.question,
        timestamp: new Date(),
        metadata: {
          questionIndex: latestResult.question_index,
          isBulkEvaluation: true,
        },
      };

      // Add response message
      const responseMessage: TestChatMessage = {
        id: `r-${latestResult.id}`,
        role: 'agent',
        content:
          latestResult.response ||
          (latestResult.error ? `Error: ${latestResult.error}` : 'No response'),
        timestamp: new Date(),
        metadata: {
          questionIndex: latestResult.question_index,
          responseTime: latestResult.response_time,
          status: latestResult.status,
          isBulkEvaluation: true,
        },
      };

      setMessages((prev) => [...prev, questionMessage, responseMessage]);
    }
  }, [bulkEvaluationResults, bulkEvaluation.isRunning]);

  // Clear messages function
  const handleClearMessages = useCallback(() => {
    setMessages([
      {
        id: '1',
        role: 'agent',
        content: "Hi, I'm Georgia! How can I help you today?",
        timestamp: new Date(),
      },
    ]);
    clearLogUpdates(); // Also clear logs when clearing messages
    clearBulkEvaluationData(); // Clear bulk evaluation data
    setBulkEvaluation({
      isRunning: false,
      isPaused: false,
      progress: 0,
      totalQuestions: 0,
      currentQuestionIndex: 0,
      results: [],
      startTime: null,
      estimatedTimeRemaining: 0,
    });
    setHideLogs(false); // Reset hide logs state
  }, [clearLogUpdates, clearBulkEvaluationData]);

  const handleSendMessage = useCallback(async () => {
    if (!inputMessage.trim() || isTesting) return;

    const userMessage: TestChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date(),
    };

    // Add user message immediately
    setMessages((prev) => [...prev, userMessage]);
    setInputMessage('');
    setIsTesting(true);
    clearLogUpdates(); // Clear previous logs when starting new request
    setHideLogs(false); // Show logs section when starting new request

    try {
      // Test the agent directly with the new API including WebSocket ID for log streaming
      const response = await apiService.testAgent({
        agent_code: agentCode,
        message: userMessage.content,
        agent_name: agentName || 'Test Agent',
        agent_description: agentDescription || 'A test agent',
        context: { user_id: 1, test_mode: true },
        folder_path: currentFolder,
        websocket_id: websocketId, // Pass WebSocket ID for real-time log streaming
      });

      if (response.success) {
        // Add agent response
        const agentMessage: TestChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'agent',
          content: response.agent_response,
          timestamp: new Date(),
        };

        setMessages((prev) => [...prev, agentMessage]);
      } else {
        throw new Error(response.error || 'Failed to get agent response');
      }
    } catch (error) {
      console.error('Failed to test agent:', error);

      // Add error message
      const errorMessage: TestChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'agent',
        content: `Sorry, I encountered an error while testing: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your agent code and try again.`,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
      toast.error('Failed to test agent. Please check your code.');
    } finally {
      setIsTesting(false);
    }
  }, [inputMessage, isTesting, agentCode, agentName, agentDescription, currentFolder]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage],
  );

  const canSend = inputMessage.trim().length > 0 && !isTesting;

  // CSV file upload handlers
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setCsvFile(file);
      } else {
        toast.error('Please upload a CSV file');
      }
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type === 'text/csv' || file.name.endsWith('.csv')) {
        setCsvFile(file);
      } else {
        toast.error('Please upload a CSV file');
      }
    }
  }, []);

  const removeCSVFile = useCallback(() => {
    setCsvFile(null);
    setParsedCSV(null);
  }, []);

  // CSV parsing function
  const parseCSV = useCallback(async (file: File): Promise<ParsedCSV> => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const text = e.target?.result as string;
          const lines = text.split('\n').filter((line) => line.trim());

          if (lines.length < 2) {
            resolve({
              headers: [],
              rows: [],
              questionColumn: '',
              isValid: false,
              errors: ['CSV must have at least 2 lines (header + 1 data row)'],
            });
            return;
          }

          // Parse headers
          const headers = lines[0].split(',').map((h) => h.trim().replace(/"/g, ''));

          // Find question column
          const questionColumn = headers.find(
            (h) =>
              h.toLowerCase().includes('question') ||
              h.toLowerCase() === 'q' ||
              h.toLowerCase() === 'query',
          );

          const errors: string[] = [];
          if (!questionColumn) {
            errors.push(
              'No "question" column found. Please include a column with "question" in the name.',
            );
          }

          // Parse rows
          const rows: CSVRow[] = [];
          for (let i = 1; i < lines.length && i <= 1000; i++) {
            // Limit to 1000 questions
            const values = lines[i].split(',').map((v) => v.trim().replace(/"/g, ''));
            const row: CSVRow = { question: '' };

            headers.forEach((header, index) => {
              const value = values[index] || '';
              if (header === questionColumn) {
                row.question = value;
              } else if (
                header.toLowerCase().includes('expected') ||
                header.toLowerCase().includes('answer')
              ) {
                row.expected_answer = value;
              } else if (header.toLowerCase().includes('context')) {
                row.context = value;
              } else if (header.toLowerCase().includes('category')) {
                row.category = value;
              } else {
                row[header] = value;
              }
            });

            if (row.question.trim()) {
              rows.push(row);
            }
          }

          if (rows.length === 0) {
            errors.push('No valid question rows found');
          }

          if (lines.length > 1001) {
            errors.push(`File has ${lines.length - 1} rows. Maximum 1000 questions supported.`);
          }

          resolve({
            headers,
            rows,
            questionColumn: questionColumn || '',
            isValid: errors.length === 0,
            errors,
          });
        } catch (error) {
          resolve({
            headers: [],
            rows: [],
            questionColumn: '',
            isValid: false,
            errors: [
              `Failed to parse CSV: ${error instanceof Error ? error.message : 'Unknown error'}`,
            ],
          });
        }
      };
      reader.readAsText(file);
    });
  }, []);

  // Parse CSV when file is selected
  useEffect(() => {
    if (csvFile) {
      setIsParsingCSV(true);
      parseCSV(csvFile).then((parsed) => {
        setParsedCSV(parsed);
        if (!parsed.isValid) {
          toast.error(parsed.errors[0]);
        }
        setIsParsingCSV(false);
      });
    }
  }, [csvFile, parseCSV]);

  // Bulk evaluation control functions
  const startBulkEvaluation = useCallback(async () => {
    if (!parsedCSV?.isValid) return;

    setBulkEvaluation({
      isRunning: true,
      isPaused: false,
      progress: 0,
      totalQuestions: parsedCSV.rows.length,
      currentQuestionIndex: 0,
      results: [],
      startTime: new Date(),
      estimatedTimeRemaining: parsedCSV.rows.length * 3, // Rough estimate: 3 seconds per question
    });

    setIsTesting(true);
    clearLogUpdates();
    setHideLogs(false);

    // Add system message to start bulk evaluation
    const startMessage: TestChatMessage = {
      id: Date.now().toString(),
      role: 'system',
      content: `🚀 Starting bulk evaluation of ${parsedCSV.rows.length} questions...\n\n**Configuration:**\n- Batch size: ${batchSize} questions\n- Total batches: ${Math.ceil(parsedCSV.rows.length / batchSize)}\n- Estimated time: ~${Math.ceil((parsedCSV.rows.length / batchSize) * 3)} seconds`,
      timestamp: new Date(),
      metadata: { isBulkEvaluation: true },
    };
    setMessages((prev) => [...prev, startMessage]);

    try {
      // Call bulk evaluation API
      const response = await apiService.bulkEvaluateAgent({
        agent_code: agentCode,
        questions: parsedCSV.rows.map((row) => ({
          question: row.question,
          expected_answer: row.expected_answer,
          context: row.context,
          category: row.category,
        })),
        agent_name: agentName,
        agent_description: agentDescription,
        context: { user_id: 1, test_mode: true },
        folder_path: currentFolder,
        websocket_id: websocketId,
        batch_size: batchSize,
      });

      if (response.success) {
        // Update bulk evaluation state with results
        setBulkEvaluation((prev) => ({
          ...prev,
          isRunning: false,
          progress: 100,
          currentQuestionIndex: response.total_questions,
          results: response.results.map((result) => ({
            question: result.question,
            response: result.response,
            responseTime: result.response_time,
            status: result.status as 'success' | 'error',
            error: result.error,
            expectedAnswer: result.expected_answer,
            rowIndex: result.question_index,
          })),
        }));

        // Add completion message
        const completeMessage: TestChatMessage = {
          id: (Date.now() + 1).toString(),
          role: 'system',
          content: `✅ Bulk evaluation completed!\n\n**Results:**\n- Total questions: ${response.total_questions}\n- Successful: ${response.successful_count}\n- Failed: ${response.failed_count}\n- Average response time: ${response.average_response_time.toFixed(0)}ms\n- Total time: ${response.total_time.toFixed(1)}s`,
          timestamp: new Date(),
          metadata: { isBulkEvaluation: true },
        };
        setMessages((prev) => [...prev, completeMessage]);

        toast.success(
          `Bulk evaluation completed! ${response.successful_count}/${response.total_questions} successful`,
        );
      } else {
        throw new Error(response.error || 'Bulk evaluation failed');
      }
    } catch (error) {
      console.error('Failed to start bulk evaluation:', error);

      // Add error message
      const errorMessage: TestChatMessage = {
        id: (Date.now() + 1).toString(),
        role: 'system',
        content: `❌ Bulk evaluation failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
        timestamp: new Date(),
        metadata: { isBulkEvaluation: true },
      };
      setMessages((prev) => [...prev, errorMessage]);

      setBulkEvaluation((prev) => ({ ...prev, isRunning: false }));
      toast.error('Failed to start bulk evaluation. Please check your agent configuration.');
    } finally {
      setIsTesting(false);
    }
  }, [
    parsedCSV,
    batchSize,
    clearLogUpdates,
    agentCode,
    agentName,
    agentDescription,
    currentFolder,
    websocketId,
    apiService,
  ]);

  const pauseBulkEvaluation = useCallback(() => {
    setBulkEvaluation((prev) => ({ ...prev, isPaused: true }));
  }, []);

  const resumeBulkEvaluation = useCallback(() => {
    setBulkEvaluation((prev) => ({ ...prev, isPaused: false }));
  }, []);

  const cancelBulkEvaluation = useCallback(() => {
    setBulkEvaluation({
      isRunning: false,
      isPaused: false,
      progress: 0,
      totalQuestions: 0,
      currentQuestionIndex: 0,
      results: [],
      startTime: null,
      estimatedTimeRemaining: 0,
    });
    setIsTesting(false);
  }, []);

  // Calculate bulk evaluation statistics
  const getBulkEvaluationStats = useCallback(() => {
    const { results, startTime } = bulkEvaluation;
    if (results.length === 0) return null;

    const successful = results.filter((r) => r.status === 'success').length;
    const failed = results.filter((r) => r.status === 'error').length;
    const successRate = (successful / results.length) * 100;
    const avgResponseTime = results.reduce((sum, r) => sum + r.responseTime, 0) / results.length;
    const totalTime = startTime ? Date.now() - startTime.getTime() : 0;

    return {
      total: results.length,
      successful,
      failed,
      successRate,
      avgResponseTime: Math.round(avgResponseTime),
      totalTime: Math.round(totalTime / 1000), // Convert to seconds
    };
  }, [bulkEvaluation]);

  // Export bulk evaluation results
  const exportBulkResults = useCallback(
    (format: 'csv' | 'json') => {
      const stats = getBulkEvaluationStats();
      if (!stats || bulkEvaluation.results.length === 0) return;

      if (format === 'csv') {
        const headers = [
          'Question Index',
          'Question',
          'Agent Response',
          'Status',
          'Response Time (ms)',
          'Expected Answer',
        ];
        const rows = bulkEvaluation.results.map((result) => [
          result.rowIndex + 1,
          `"${result.question.replace(/"/g, '""')}"`,
          `"${result.response.replace(/"/g, '""')}"`,
          result.status,
          result.responseTime,
          result.expectedAnswer ? `"${result.expectedAnswer.replace(/"/g, '""')}"` : '',
        ]);

        const csvContent = [headers.join(','), ...rows.map((row) => row.join(','))].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bulk-evaluation-results-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const jsonData = {
          metadata: {
            exportDate: new Date().toISOString(),
            agentName: agentName,
            ...stats,
          },
          results: bulkEvaluation.results,
        };

        const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `bulk-evaluation-results-${new Date().toISOString().split('T')[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
      }

      toast.success(`Results exported as ${format.toUpperCase()}`);
    },
    [bulkEvaluation.results, getBulkEvaluationStats, agentName],
  );

  return (
    <div className={cn('flex flex-col h-full bg-[#EFF4FE]', className)}>
      {/* Header with mode toggle and clear button */}
      <div className="flex justify-between items-center px-3 py-2 bg-gray-50 border-b border-gray-200">
        {/* Mode Toggle */}
        <div className="flex p-1 bg-white rounded-lg border border-gray-200">
          <Button
            onClick={() => setChatMode('individual')}
            variant={chatMode === 'individual' ? 'default' : 'ghost'}
            size="sm"
            className={cn(
              'px-3 py-1 h-8 text-xs font-medium transition-all',
              chatMode === 'individual'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 hover:text-gray-900',
            )}
          >
            <MessageSquare className="mr-1 w-3 h-3" />
            Individual
          </Button>
          <Button
            onClick={() => setChatMode('bulk')}
            variant={chatMode === 'bulk' ? 'default' : 'ghost'}
            size="sm"
            className={cn(
              'px-3 py-1 h-8 text-xs font-medium transition-all',
              chatMode === 'bulk'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-gray-600 hover:text-gray-900',
            )}
          >
            <FileSpreadsheet className="mr-1 w-3 h-3" />
            Bulk
          </Button>
        </div>

        {/* Clear button */}
        <Button
          onClick={handleClearMessages}
          variant="ghost"
          size="sm"
          className="p-0 w-8 h-8 text-gray-400 cursor-pointer hover:text-red-500 hover:bg-red-50"
          title="Clear messages"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Messages */}
      <div className="overflow-y-auto flex-1 p-3 space-y-3">
        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              'flex gap-3',
              message.role === 'user'
                ? 'justify-end'
                : message.role === 'system'
                  ? 'justify-center'
                  : 'justify-start',
            )}
          >
            <div
              className={cn(
                'max-w-[80%] rounded-lg px-3 py-2 text-sm',
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : message.role === 'system'
                    ? 'bg-amber-50 dark:bg-amber-900/20 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-800'
                    : message.metadata?.status === 'error'
                      ? 'bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-200 border border-red-200 dark:border-red-800'
                      : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100',
              )}
            >
              {/* Sender label inside bubble */}
              <div
                className={cn(
                  'text-xs font-medium mb-1 flex items-center justify-between',
                  message.role === 'user'
                    ? 'text-blue-100 opacity-80'
                    : message.role === 'system'
                      ? 'text-amber-600 dark:text-amber-400'
                      : 'text-gray-500 dark:text-gray-400 opacity-80',
                )}
              >
                <span>
                  {message.role === 'user'
                    ? 'User'
                    : message.role === 'system'
                      ? 'System'
                      : agentName || 'Agent'}
                  {message.metadata?.questionIndex !== undefined && (
                    <span className="ml-1 bg-blue-100 dark:bg-blue-800 text-blue-700 dark:text-blue-300 px-1 py-0.5 rounded text-xs">
                      Q{message.metadata.questionIndex + 1}
                    </span>
                  )}
                </span>
                {message.metadata?.responseTime && (
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {message.metadata.responseTime}ms
                  </span>
                )}
              </div>

              {/* Message content */}
              {message.role === 'agent' || message.role === 'system' ? (
                <HybridRenderer content={message.content} backgroundContext="agent" />
              ) : (
                <div className="whitespace-pre-wrap">{message.content}</div>
              )}

              {/* Expected answer comparison for bulk evaluation */}
              {message.metadata?.expectedAnswer && (
                <div className="pt-2 mt-2 border-t border-gray-200 dark:border-gray-600">
                  <div className="mb-1 text-xs text-gray-600 dark:text-gray-400">
                    Expected Answer:
                  </div>
                  <div className="p-2 text-xs bg-gray-50 rounded dark:bg-gray-600">
                    {message.metadata.expectedAnswer}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              <div
                className={cn(
                  'text-xs mt-1',
                  message.role === 'user'
                    ? 'text-blue-100'
                    : message.role === 'system'
                      ? 'text-amber-600 dark:text-amber-400'
                      : 'text-gray-500 dark:text-gray-400',
                )}
              >
                {message.timestamp.toLocaleTimeString()}
              </div>
            </div>
          </div>
        ))}

        {isTesting && (
          <div className="flex gap-3 justify-start">
            <div className="px-3 py-2 text-gray-900 bg-gray-100 rounded-lg">
              <div className="flex gap-2 items-center">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span className="text-sm">Testing agent...</span>
              </div>
            </div>
          </div>
        )}

        {/* Invisible div for auto-scroll target */}
        <div ref={messagesEndRef} />
      </div>

      {/* Bulk Evaluation Summary */}
      {!bulkEvaluation.isRunning &&
        bulkEvaluation.results.length > 0 &&
        (() => {
          const stats = getBulkEvaluationStats();
          return stats ? (
            <div className="mx-3 mb-3">
              <div className="p-4 bg-green-50 rounded-lg border border-green-200 dark:bg-green-900/20 dark:border-green-800">
                <div className="flex justify-between items-center mb-3">
                  <div className="flex gap-2 items-center">
                    <BarChart3 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    <h3 className="text-sm font-medium text-green-800 dark:text-green-200">
                      Evaluation Complete
                    </h3>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      onClick={() => exportBulkResults('csv')}
                      size="sm"
                      variant="outline"
                      className="px-2 h-7 text-xs"
                    >
                      <Download className="mr-1 w-3 h-3" />
                      CSV
                    </Button>
                    <Button
                      onClick={() => exportBulkResults('json')}
                      size="sm"
                      variant="outline"
                      className="px-2 h-7 text-xs"
                    >
                      <Download className="mr-1 w-3 h-3" />
                      JSON
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 text-sm md:grid-cols-4">
                  <div className="text-center">
                    <div className="text-xl font-bold text-green-700 dark:text-green-300">
                      {stats.total}
                    </div>
                    <div className="text-green-600 dark:text-green-400">Total Questions</div>
                  </div>

                  <div className="text-center">
                    <div className="text-xl font-bold text-green-700 dark:text-green-300">
                      {stats.successRate.toFixed(1)}%
                    </div>
                    <div className="text-green-600 dark:text-green-400">Success Rate</div>
                  </div>

                  <div className="text-center">
                    <div className="text-xl font-bold text-green-700 dark:text-green-300">
                      {stats.avgResponseTime}ms
                    </div>
                    <div className="text-green-600 dark:text-green-400">Avg Response</div>
                  </div>

                  <div className="text-center">
                    <div className="text-xl font-bold text-green-700 dark:text-green-300">
                      {stats.totalTime}s
                    </div>
                    <div className="text-green-600 dark:text-green-400">Total Time</div>
                  </div>
                </div>

                {stats.failed > 0 && (
                  <div className="pt-3 mt-3 border-t border-green-200 dark:border-green-800">
                    <div className="text-sm text-amber-700 dark:text-amber-300">
                      <strong>{stats.failed}</strong> questions failed - check individual responses
                      above for details
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : null;
        })()}

      {/* Collapsible Live Logs Section */}
      {(isTesting || logUpdates.length > 0) && !hideLogs && (
        <div className="bg-gray-50 border-t border-gray-200 dark:bg-gray-800 dark:border-gray-700">
          {/* Toggle Button */}
          <div className="flex justify-between items-center px-3 py-2 transition-colors hover:bg-gray-100 dark:hover:bg-gray-700">
            <div
              className="flex flex-1 gap-2 items-center cursor-pointer"
              onClick={() => setShowLogs(!showLogs)}
            >
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                Backend Logs
              </span>
              {isTesting && (
                <div className="flex gap-1 items-center">
                  <Loader2 className="w-3 h-3 text-blue-500 animate-spin" />
                  <span className="text-xs text-blue-600 dark:text-blue-400">Live</span>
                </div>
              )}
              {logUpdates.length > 0 && (
                <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-0.5 rounded-full font-medium">
                  {logUpdates.length}
                </span>
              )}
              {showLogs ? (
                <ChevronUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              ) : (
                <ChevronDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              )}
            </div>

            {/* Close button */}
            {!isTesting && (
              <button
                onClick={() => {
                  setHideLogs(true);
                  setShowLogs(false);
                }}
                className="p-1 rounded transition-colors hover:bg-gray-200 dark:hover:bg-gray-700"
                title="Hide logs"
              >
                <X className="w-3 h-3 text-gray-400 dark:text-gray-500" />
              </button>
            )}
          </div>

          {/* Logs Content - Only show when expanded */}
          {showLogs && (
            <div className="px-3 pb-2">
              <LogViewer
                logs={logUpdates}
                showTimestamps={true}
                autoScroll={true}
                maxHeight="120px"
              />
            </div>
          )}
        </div>
      )}

      {/* Input - Different UI based on chat mode */}
      <div className="p-3 bg-gray-50 border-t border-gray-200 dark:bg-gray-800 dark:border-gray-700">
        {chatMode === 'individual' ? (
          // Individual chat input
          <div className="flex gap-2">
            <div className="relative flex-1">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Chat with agent"
                className="px-3 py-2 w-full text-sm text-gray-900 bg-white rounded-lg border border-gray-300 resize-none dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                rows={2}
                disabled={isTesting}
              />
            </div>
            <Button
              onClick={handleSendMessage}
              disabled={!canSend}
              size="sm"
              className="px-4"
              aria-label="Send message"
            >
              {isTesting ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        ) : (
          // Bulk evaluation CSV upload interface
          <div className="space-y-3">
            {!csvFile ? (
              // CSV Upload Area
              <div
                className={cn(
                  'p-6 rounded-lg border-2 border-dashed transition-colors cursor-pointer',
                  isDragOver
                    ? 'bg-blue-50 border-blue-500 dark:bg-blue-900/20'
                    : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500',
                )}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('csv-file-input')?.click()}
              >
                <div className="flex flex-col items-center text-center">
                  <FileSpreadsheet className="mb-2 w-8 h-8 text-gray-400 dark:text-gray-500" />
                  <p className="mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                    Drop CSV file here or click to browse
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Required: 'question' column | Optional: 'expected_answer'
                  </p>
                </div>
                <input
                  id="csv-file-input"
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </div>
            ) : (
              // CSV File Selected and Preview
              <div className="space-y-3">
                {/* File Info */}
                <div className="p-3 bg-white rounded-lg border border-gray-200 dark:border-gray-600 dark:bg-gray-700">
                  <div className="flex justify-between items-center">
                    <div className="flex gap-2 items-center">
                      <FileText
                        className={cn(
                          'w-4 h-4',
                          isParsingCSV
                            ? 'text-blue-500'
                            : parsedCSV?.isValid
                              ? 'text-green-600'
                              : 'text-red-500',
                        )}
                      />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          {csvFile.name}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {(csvFile.size / 1024).toFixed(1)} KB
                          {isParsingCSV && ' • Parsing...'}
                          {parsedCSV && ` • ${parsedCSV.rows.length} questions`}
                        </p>
                      </div>
                    </div>
                    <Button
                      onClick={removeCSVFile}
                      variant="ghost"
                      size="sm"
                      className="text-gray-400 hover:text-red-500"
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                </div>

                {/* CSV Preview */}
                {parsedCSV && parsedCSV.isValid && (
                  <div className="bg-white rounded-lg border border-gray-200 dark:border-gray-600 dark:bg-gray-700">
                    <div className="p-3 border-b border-gray-200 dark:border-gray-600">
                      <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        Preview ({parsedCSV.rows.length} questions)
                      </h4>
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        Question column: "{parsedCSV.questionColumn}"
                      </p>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-xs">
                        <thead>
                          <tr className="border-b border-gray-200 dark:border-gray-600">
                            {parsedCSV.headers.slice(0, 4).map((header, index) => (
                              <th
                                key={index}
                                className="p-2 font-medium text-left text-gray-700 dark:text-gray-300"
                              >
                                {header}
                                {header === parsedCSV.questionColumn && (
                                  <span className="ml-1 px-1 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-xs">
                                    Q
                                  </span>
                                )}
                              </th>
                            ))}
                            {parsedCSV.headers.length > 4 && (
                              <th className="p-2 font-medium text-left text-gray-500">
                                +{parsedCSV.headers.length - 4} more
                              </th>
                            )}
                          </tr>
                        </thead>
                        <tbody>
                          {parsedCSV.rows.slice(0, 3).map((row, rowIndex) => (
                            <tr
                              key={rowIndex}
                              className="border-b border-gray-100 dark:border-gray-700"
                            >
                              {parsedCSV.headers.slice(0, 4).map((header, colIndex) => (
                                <td
                                  key={colIndex}
                                  className="p-2 text-gray-600 truncate dark:text-gray-400 max-w-32"
                                >
                                  {row[header] || '—'}
                                </td>
                              ))}
                              {parsedCSV.headers.length > 4 && (
                                <td className="p-2 text-gray-500">...</td>
                              )}
                            </tr>
                          ))}
                          {parsedCSV.rows.length > 3 && (
                            <tr>
                              <td
                                colSpan={Math.min(parsedCSV.headers.length, 5)}
                                className="p-2 text-xs text-center text-gray-500"
                              >
                                +{parsedCSV.rows.length - 3} more questions...
                              </td>
                            </tr>
                          )}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Configuration */}
                {parsedCSV && parsedCSV.isValid && (
                  <div className="bg-white rounded-lg border border-gray-200 dark:border-gray-600 dark:bg-gray-700">
                    <div
                      className="flex justify-between items-center p-3 transition-colors cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-600"
                      onClick={() => setShowConfig(!showConfig)}
                    >
                      <div className="flex gap-2 items-center">
                        <Settings className="w-4 h-4 text-gray-500" />
                        <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                          Configuration
                        </span>
                        <span className="text-xs text-gray-500 bg-gray-100 dark:bg-gray-600 px-2 py-0.5 rounded">
                          Batch: {batchSize}
                        </span>
                      </div>
                      {showConfig ? (
                        <ChevronUp className="w-4 h-4 text-gray-400" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-400" />
                      )}
                    </div>

                    {showConfig && (
                      <div className="px-3 pt-3 pb-3 space-y-3 border-t border-gray-200 dark:border-gray-600">
                        <div>
                          <label className="block mb-1 text-sm font-medium text-gray-700 dark:text-gray-300">
                            Batch Size
                          </label>
                          <div className="flex gap-2 items-center">
                            <select
                              value={batchSize}
                              onChange={(e) => setBatchSize(Number(e.target.value))}
                              className="flex-1 px-3 py-2 text-sm text-gray-900 bg-white rounded-md border border-gray-300 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                              <option value={1}>1 question at a time</option>
                              <option value={3}>3 questions at a time</option>
                              <option value={5}>5 questions at a time</option>
                              <option value={10}>10 questions at a time</option>
                              <option value={20}>20 questions at a time</option>
                            </select>
                          </div>
                          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                            Higher batch sizes process faster but use more resources
                          </p>
                        </div>

                        <div className="p-2 bg-blue-50 rounded-lg border border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
                          <p className="text-xs text-blue-700 dark:text-blue-300">
                            <strong>Estimated time:</strong> ~
                            {Math.ceil((parsedCSV.rows.length / batchSize) * 3)} seconds
                            <br />
                            <strong>Total questions:</strong> {parsedCSV.rows.length}
                            <br />
                            <strong>Batches:</strong> {Math.ceil(parsedCSV.rows.length / batchSize)}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Error Display */}
                {parsedCSV && !parsedCSV.isValid && (
                  <div className="p-3 bg-red-50 rounded-lg border border-red-200 dark:border-red-800 dark:bg-red-900/20">
                    <p className="text-sm font-medium text-red-800 dark:text-red-200">
                      CSV Validation Errors:
                    </p>
                    <ul className="mt-1 text-xs list-disc list-inside text-red-600 dark:text-red-300">
                      {parsedCSV.errors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Progress Tracking */}
            {bulkEvaluation.isRunning && (
              <div className="p-4 space-y-3 bg-blue-50 rounded-lg border border-blue-200 dark:border-blue-800 dark:bg-blue-900/20">
                <div className="flex justify-between items-center">
                  <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100">
                    Bulk Evaluation in Progress
                  </h4>
                  <div className="flex gap-1">
                    {bulkEvaluation.isPaused ? (
                      <Button
                        onClick={resumeBulkEvaluation}
                        size="sm"
                        variant="outline"
                        className="px-2 h-7 text-xs"
                      >
                        Resume
                      </Button>
                    ) : (
                      <Button
                        onClick={pauseBulkEvaluation}
                        size="sm"
                        variant="outline"
                        className="px-2 h-7 text-xs"
                      >
                        Pause
                      </Button>
                    )}
                    <Button
                      onClick={cancelBulkEvaluation}
                      size="sm"
                      variant="outline"
                      className="px-2 h-7 text-xs text-red-600 hover:text-red-700"
                    >
                      Cancel
                    </Button>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs text-blue-700 dark:text-blue-300">
                    <span>
                      Question {bulkEvaluation.currentQuestionIndex + 1} of{' '}
                      {bulkEvaluation.totalQuestions}
                    </span>
                    <span>{bulkEvaluation.progress}% complete</span>
                  </div>
                  <div className="w-full h-2 bg-blue-200 rounded-full dark:bg-blue-800">
                    <div
                      className="h-2 bg-blue-600 rounded-full transition-all duration-300 dark:bg-blue-400"
                      style={{ width: `${bulkEvaluation.progress}%` }}
                    />
                  </div>
                  <div className="flex justify-between items-center text-xs text-blue-600 dark:text-blue-400">
                    <span>
                      {bulkEvaluation.results.filter((r) => r.status === 'success').length}{' '}
                      successful,{' '}
                      {bulkEvaluation.results.filter((r) => r.status === 'error').length} failed
                    </span>
                    <span>~{Math.round(bulkEvaluation.estimatedTimeRemaining)}s remaining</span>
                  </div>
                </div>
              </div>
            )}

            {/* Start Evaluation Button */}
            {csvFile && parsedCSV?.isValid && !bulkEvaluation.isRunning && (
              <Button
                onClick={startBulkEvaluation}
                className="w-full"
                disabled={isTesting || isParsingCSV}
              >
                <Upload className="mr-2 w-4 h-4" />
                Start Evaluation ({parsedCSV.rows.length} questions)
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AgentTestChat;
