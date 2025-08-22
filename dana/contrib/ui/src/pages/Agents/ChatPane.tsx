import React, { useState, useRef, useEffect, useCallback } from 'react';
import {
  ArrowUp,
  NavArrowDown,
  NavArrowUp,
  Xmark,
  Table2Columns,
  Download,
  Page,
} from 'iconoir-react';
import { SidebarExpand } from 'iconoir-react';
import { useParams } from 'react-router-dom';
import { apiService } from '@/lib/api';
import type {
  BulkEvaluationRequest,
  BulkEvaluationQuestion,
  BulkEvaluationResult,
} from '@/lib/api';
import { MarkdownViewerSmall } from './chat/markdown-viewer';
import { useVariableUpdates } from '@/hooks/useVariableUpdates';
import { getAgentAvatarSync } from '@/utils/avatar';
import LogViewer from '@/components/LogViewer';
import { Button } from '@/components/ui/button';

// Constants for resize functionality
const MIN_WIDTH = 380;
const MAX_WIDTH = 800;
const DEFAULT_WIDTH = 420;
const RESIZE_HANDLE_WIDTH = 2;

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'agent';
  timestamp: Date;
}

// CSV-related interfaces
interface CSVRow {
  question: string;
  expected_answer?: string;
  category?: string;
  context?: string;
}

interface ParsedCSV {
  data: CSVRow[];
  headers: string[];
  preview: CSVRow[];
}

interface BulkEvaluationState {
  isRunning: boolean;
  results: BulkEvaluationResult[];
  progress: {
    current: number;
    total: number;
    successful: number;
    failed: number;
    progress: number;
    estimatedTimeRemaining: number;
  };
}

type EvaluationMode = 'individual' | 'bulk';

interface ChatPaneProps {
  agentName?: string;
  onClose: () => void;
  isVisible: boolean;
}

// Resize handle component for ChatPane
const ChatResizeHandle: React.FC<{
  onResize: (width: number) => void;
  isResizing: boolean;
  setIsResizing: (resizing: boolean) => void;
}> = ({ onResize, isResizing, setIsResizing }) => {
  const handleRef = useRef<HTMLDivElement>(null);
  const startXRef = useRef<number>(0);
  const startWidthRef = useRef<number>(0);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();

      if (!handleRef.current) return;

      setIsResizing(true);
      startXRef.current = e.clientX;
      startWidthRef.current = handleRef.current.parentElement?.offsetWidth || DEFAULT_WIDTH;

      // Add global mouse event listeners
      const handleMouseMove = (e: MouseEvent) => {
        const deltaX = startXRef.current - e.clientX; // Inverted for left-side resize
        const newWidth = Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, startWidthRef.current + deltaX));
        onResize(newWidth);
      };

      const handleMouseUp = () => {
        setIsResizing(false);
        document.removeEventListener('mousemove', handleMouseMove);
        document.removeEventListener('mouseup', handleMouseUp);
      };

      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    },
    [onResize, setIsResizing],
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (isResizing) {
        setIsResizing(false);
      }
    };
  }, [isResizing, setIsResizing]);

  return (
    <div
      ref={handleRef}
      className={`
        absolute top-0 left-0 h-full z-50
        hover:bg-gray-200 hover:shadow-sm transition-all duration-200
        ${isResizing ? 'bg-primary' : 'hover:bg-gray-200'}
        group
      `}
      onMouseDown={handleMouseDown}
      style={{
        width: `${RESIZE_HANDLE_WIDTH}px`,
        cursor: 'col-resize',
      }}
      title="Drag to resize chat panel"
    >
      {/* Visual indicator line */}
      <div
        className={`
          absolute top-1/2 left-1/2 transform -translate-x-2/3 -translate-y-1/2
          w-2 h-8 rounded-full transition-all duration-200 border border-gray-300
          ${isResizing ? 'shadow-sm bg-primary' : 'bg-white shadow-sm group-hover:bg-primary'}
        `}
        style={{
          zIndex: 60,
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};

export const ChatPane: React.FC<ChatPaneProps> = ({ agentName = 'Agent', onClose, isVisible }) => {
  const { agent_id } = useParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [showLogs, setShowLogs] = useState(false);
  const [hideLogs, setHideLogs] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Bulk evaluation state
  const [evaluationMode, setEvaluationMode] = useState<EvaluationMode>('individual');
  const [, setCsvFile] = useState<File | null>(null);
  const [parsedCSV, setParsedCSV] = useState<ParsedCSV | null>(null);
  const [csvError, setCsvError] = useState<string>('');
  const [batchSize, setBatchSize] = useState(5);
  const [bulkEvaluationState, setBulkEvaluationState] = useState<BulkEvaluationState>({
    isRunning: false,
    results: [],
    progress: {
      current: 0,
      total: 0,
      successful: 0,
      failed: 0,
      progress: 0,
      estimatedTimeRemaining: 0,
    },
  });
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Resize state management
  const [chatWidth, setChatWidth] = useState(() => {
    // Try to get saved width from localStorage
    const savedWidth = localStorage.getItem('chat-pane-width');
    if (savedWidth) {
      const width = parseInt(savedWidth, 10);
      return Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, width));
    }
    return DEFAULT_WIDTH;
  });
  const [isResizing, setIsResizing] = useState(false);

  // Save width to localStorage when it changes
  useEffect(() => {
    localStorage.setItem('chat-pane-width', chatWidth.toString());
  }, [chatWidth]);

  const handleResize = useCallback((newWidth: number) => {
    setChatWidth(newWidth);
  }, []);

  // Generate unique WebSocket ID for this chat session
  const [websocketId] = useState(
    () => `chatpane-${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
  );

  // WebSocket for variable updates and log streaming
  const {
    updates,
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

  // Handle variable updates - show step changes as thinking messages
  useEffect(() => {
    if (updates.length > 0) {
      const latestUpdate = updates[updates.length - 1];
      // Update current step for thinking message
      if (latestUpdate.variable === 'step') {
        // Try both property names to be safe
        const stepValue = latestUpdate.newValue || '';

        if (stepValue) {
          try {
            // Parse the stringified object
            console.log('==============================================');
            console.log('stepValue', stepValue);
            const stepObject = JSON.parse(stepValue.replaceAll("'", '"'));
            console.log('stepObject', stepObject);
            const action = stepObject.action || stepObject.description || stepObject.name || '';
            console.log('==============================================');
            setCurrentStep(action);
          } catch (error) {
            // If parsing fails, use the raw value
            console.log(`📝 Failed to parse step object, using raw value: "${stepValue}"`);
            setCurrentStep(stepValue);
          }
        }
      }
    }
  }, [updates]);

  // Handle bulk evaluation progress updates
  useEffect(() => {
    if (bulkEvaluationProgress) {
      setBulkEvaluationState((prev) => ({
        ...prev,
        progress: {
          current: bulkEvaluationProgress.current_question,
          total: bulkEvaluationProgress.total_questions,
          successful: bulkEvaluationProgress.successful_count,
          failed: bulkEvaluationProgress.failed_count,
          progress: bulkEvaluationProgress.progress,
          estimatedTimeRemaining: bulkEvaluationProgress.estimated_time_remaining,
        },
      }));
    }
  }, [bulkEvaluationProgress]);

  // Handle bulk evaluation result updates
  useEffect(() => {
    if (bulkEvaluationResults.length > 0) {
      const latestResults = bulkEvaluationResults.map((result) => ({
        question: result.question,
        response: result.response,
        response_time: result.response_time,
        status: result.status,
        error: result.error,
        expected_answer: undefined,
        question_index: result.question_index,
      }));

      setBulkEvaluationState((prev) => ({
        ...prev,
        results: latestResults,
      }));
    }
  }, [bulkEvaluationResults]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load chat history when component mounts or agent_id changes
  useEffect(() => {
    const loadChatHistory = async () => {
      if (!agent_id || !isVisible) return;

      setIsLoadingHistory(true);
      try {
        // Try to load chat history (test_chat + smart_chat)
        const chatHistory = await apiService.getTestChatHistory(agent_id);

        if (chatHistory && chatHistory.length > 0) {
          // Convert API response to Message format and sort by timestamp
          const historyMessages: Message[] = chatHistory
            .map((chat: any, index: number) => ({
              id: `history-${index}`,
              text: chat.text,
              sender: chat.sender as 'user' | 'agent',
              timestamp: new Date(chat.created_at),
            }))
            .sort((a: any, b: any) => a.timestamp.getTime() - b.timestamp.getTime());

          setMessages(historyMessages);
        } else {
          // No history found, show welcome message
          setMessages([]);
          setMessages([
            {
              id: 'welcome',
              text: `Hello! I'm ${agentName}. How can I help you today?`,
              sender: 'agent',
              timestamp: new Date(),
            },
          ]);
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
        // On error, show welcome message
        setMessages([
          {
            id: 'welcome',
            text: `Hello! I'm ${agentName}. How can I help you today?`,
            sender: 'agent',
            timestamp: new Date(),
          },
        ]);
      } finally {
        setIsLoadingHistory(false);
      }
    };

    loadChatHistory();
  }, [agent_id, agentName, isVisible]);

  // CSV parsing function
  const parseCSV = (content: string): ParsedCSV => {
    const lines = content.trim().split('\n');
    if (lines.length < 2) {
      throw new Error('CSV must have at least a header row and one data row');
    }

    const headers = lines[0].split(',').map((h) => h.trim().replace(/^"|"$/g, ''));
    const questionIndex = headers.findIndex((h) => h.toLowerCase().includes('question'));
    if (questionIndex === -1) {
      throw new Error('CSV must have a column with "question" in the header');
    }

    const data: CSVRow[] = [];
    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map((v) => v.trim().replace(/^"|"$/g, ''));
      if (values.length !== headers.length) continue;

      const row: CSVRow = {
        question: values[questionIndex] || '',
        expected_answer:
          values[headers.findIndex((h) => h.toLowerCase().includes('expected'))] || undefined,
        category:
          values[headers.findIndex((h) => h.toLowerCase().includes('category'))] || undefined,
        context: values[headers.findIndex((h) => h.toLowerCase().includes('context'))] || undefined,
      };

      if (row.question.trim()) {
        data.push(row);
      }
    }

    if (data.length === 0) {
      throw new Error('No valid questions found in CSV');
    }

    return {
      data,
      headers,
      preview: data.slice(0, 5),
    };
  };

  // Handle CSV file selection
  const handleCSVUpload = async (file: File) => {
    setCsvError('');
    setCsvFile(file);

    try {
      const content = await file.text();
      const parsed = parseCSV(content);
      setParsedCSV(parsed);
    } catch (error) {
      setCsvError(error instanceof Error ? error.message : 'Failed to parse CSV');
      setParsedCSV(null);
    }
  };

  // Handle file drop
  const handleFileDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files);
    const csvFile = files.find((f) => f.name.toLowerCase().endsWith('.csv'));
    if (csvFile) {
      handleCSVUpload(csvFile);
    }
  };

  // Handle file input change
  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleCSVUpload(file);
    }
  };

  // Export results to CSV
  const exportResultsToCSV = () => {
    if (bulkEvaluationState.results.length === 0) return;

    const headers = ['question', 'response', 'status', 'response_time_ms', 'error'];
    const csvContent = [
      headers.join(','),
      ...bulkEvaluationState.results.map((result) =>
        [
          `"${result.question.replace(/"/g, '""')}"`,
          `"${result.response.replace(/"/g, '""')}"`,
          result.status,
          result.response_time.toFixed(2),
          result.error ? `"${result.error.replace(/"/g, '""')}"` : '',
        ].join(','),
      ),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bulk-evaluation-results-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Download sample CSV file
  const downloadSampleCSV = () => {
    const sampleData = [
      ['question', 'expected_answer', 'category'],
      ['What is 2+2?', '4', 'Math'],
      ['What is the capital of France?', 'Paris', 'Geography'],
      ['Who wrote Romeo and Juliet?', 'William Shakespeare', 'Literature'],
      ['What is the largest planet in our solar system?', 'Jupiter', 'Astronomy'],
      ['What is the chemical symbol for water?', 'H2O', 'Chemistry'],
    ];

    const csvContent = sampleData
      .map((row) => row.map((field) => `"${field}"`).join(','))
      .join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'sample-questions.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  // Start bulk evaluation
  const startBulkEvaluation = async () => {
    if (!parsedCSV || !agent_id || bulkEvaluationState.isRunning) return;

    setBulkEvaluationState((prev) => ({
      ...prev,
      isRunning: true,
      results: [],
      progress: {
        current: 0,
        total: parsedCSV.data.length,
        successful: 0,
        failed: 0,
        progress: 0,
        estimatedTimeRemaining: 0,
      },
    }));

    clearLogUpdates();
    clearBulkEvaluationData();
    setHideLogs(false);

    try {
      const questions: BulkEvaluationQuestion[] = parsedCSV.data.map((row) => ({
        question: row.question,
        expected_answer: row.expected_answer,
        context: row.context,
        category: row.category,
      }));

      // Get agent data first
      const agentData = await apiService.getAgent(parseInt(agent_id));

      const request: BulkEvaluationRequest = {
        agent_code: '', // Backend will handle agent code loading via folder_path
        questions,
        agent_name: agentName,
        context: { user_id: 'bulk_evaluation_user', session_id: `bulk_${Date.now()}` },
        websocket_id: websocketId,
        batch_size: batchSize,
        folder_path: agentData.folder_path,
      };

      const response = await apiService.bulkEvaluateAgent(request);

      // Update final state
      setBulkEvaluationState((prev) => ({
        ...prev,
        isRunning: false,
        results: response.results,
        progress: {
          ...prev.progress,
          current: response.total_questions,
          successful: response.successful_count,
          failed: response.failed_count,
          progress: 100,
          estimatedTimeRemaining: 0,
        },
      }));

      // Add summary message to chat
      const summaryMessage: Message = {
        id: Date.now().toString(),
        text: `**Bulk Evaluation Complete**\n\n- Total Questions: ${response.total_questions}\n- Successful: ${response.successful_count}\n- Failed: ${response.failed_count}\n- Total Time: ${response.total_time.toFixed(2)}s\n- Average Response Time: ${response.average_response_time.toFixed(2)}ms`,
        sender: 'agent',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, summaryMessage]);
    } catch (error: any) {
      console.error('Bulk evaluation error:', error);
      setBulkEvaluationState((prev) => ({
        ...prev,
        isRunning: false,
      }));

      const errorMessage: Message = {
        id: Date.now().toString(),
        text: `**Bulk Evaluation Failed**\n\nError: ${error.message || 'Unknown error occurred'}`,
        sender: 'agent',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  // Clean up WebSocket when component becomes invisible or unmounts
  useEffect(() => {
    if (!isVisible) {
      disconnect();
    }
    // Clean up on unmount
    return () => {
      disconnect();
    };
  }, [isVisible, disconnect]);

  const handleSendMessage = async () => {
    if (!inputText.trim() || isLoading || !agent_id || bulkEvaluationState.isRunning) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText.trim(),
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setCurrentStep(''); // Reset current step when starting new request
    clearLogUpdates(); // Clear previous logs when starting new request
    setHideLogs(false); // Show logs section when starting new request

    try {
      // Call the new agent test API using apiService with WebSocket ID
      const data = await apiService.testAgentById(
        agent_id,
        userMessage.text,
        { user_id: 'chat_pane_user', session_id: `chatpane_${Date.now()}` },
        websocketId,
      );

      const agentMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: data.success
          ? data.agent_response
          : `Error: ${data.error || 'Unknown error occurred'}`,
        sender: 'agent',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (error: any) {
      console.error('Error testing agent:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: `Sorry, I encountered an error while processing your message: ${error.message || 'Please try again.'}`,
        sender: 'agent',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setCurrentStep(''); // Clear step when done
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div
      className={`relative bg-white max-h-[calc(100vh-64px)] border-l border-gray-200 overflow-visible flex flex-col transform transition-transform duration-300 ease-in-out z-50 ${
        isVisible ? 'translate-x-0' : 'translate-x-full'
      }`}
      style={{
        width: `${chatWidth}px`,
        minWidth: `${MIN_WIDTH}px`,
        maxWidth: `${MAX_WIDTH}px`,
      }}
    >
      <ChatResizeHandle
        onResize={handleResize}
        isResizing={isResizing}
        setIsResizing={setIsResizing}
      />
      {/* Header */}
      <div className="border-b border-gray-200">
        <div className="flex justify-between items-center p-4 h-14">
          <div className="flex gap-3 items-center">
            <div className="flex overflow-hidden justify-center items-center w-8 h-8 rounded-full">
              <img
                src={getAgentAvatarSync(agent_id || '0')}
                alt={`${agentName} avatar`}
                className="object-cover w-full h-full"
                onError={(e) => {
                  // Fallback to colored circle if image fails to load
                  const target = e.target as HTMLImageElement;
                  target.style.display = 'none';
                  //const parent = target.parentElement;
                  // if (parent) {
                  //   parent.innerHTML = `<div class="flex justify-center items-center w-full h-full text-sm font-bold text-white bg-gradient-to-br from-pink-400 to-purple-400">${agentName?.[0] || 'A'}</div>`;
                  // }
                }}
              />
            </div>
            <h3 className="font-semibold text-gray-900">{agentName}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 transition-colors cursor-pointer hover:text-gray-600"
          >
            <SidebarExpand width={20} height={20} />
          </button>
        </div>

        {/* Mode Toggle */}
        <div className="px-4 pb-4">
          <div className="flex p-1 bg-gray-100 rounded-lg">
            <button
              onClick={() => setEvaluationMode('individual')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                evaluationMode === 'individual'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Chat
            </button>
            <button
              onClick={() => setEvaluationMode('bulk')}
              className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-colors ${
                evaluationMode === 'bulk'
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              Bulk Evaluation
            </button>
          </div>
        </div>
      </div>

      {/* Content Area */}
      <div className="flex overflow-y-auto flex-col flex-1 custom-scrollbar">
        {evaluationMode === 'individual' ? (
          /* Individual Chat Messages */
          <div className="flex overflow-y-auto flex-col flex-1 p-4 space-y-4 custom-scrollbar">
            {isLoadingHistory ? (
              <div className="flex justify-center items-center h-full">
                <div className="grid grid-cols-[max-content_1fr] gap-2 items-center">
                  <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                  <div className="text-sm text-gray-700">
                    <span className="font-medium">Loading chat history...</span>
                  </div>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
                  >
                    <div
                      className={` px-4 py-2 rounded-lg ${
                        message.sender === 'user'
                          ? 'bg-gray-50 text-gray-900 border border-gray-100'
                          : 'text-gray-900'
                      }`}
                    >
                      <MarkdownViewerSmall>{message.text ?? 'Empty message'}</MarkdownViewerSmall>
                      <p className="mt-1 text-xs opacity-70">
                        {message.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                ))}
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="grid grid-cols-[max-content_1fr] gap-2 items-center">
                      <div className="w-4 h-4 rounded-full border-2 border-gray-600 animate-spin border-t-transparent"></div>
                      <div className="text-sm text-gray-700">
                        <span className="font-medium">Thinking...</span>
                        {currentStep && (
                          <div className="mt-1 text-xs italic text-blue-600">{currentStep}</div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </>
            )}
            <div ref={messagesEndRef} />
          </div>
        ) : (
          /* Bulk Evaluation UI */
          <div className="flex flex-col flex-1 p-4 space-y-4 custom-scrollbar">
            {!parsedCSV ? (
              /* CSV Upload */
              <div className="flex flex-col flex-1 justify-center items-center p-8 rounded-lg border-2 border-gray-300 border-dashed">
                <div
                  className="text-center cursor-pointer"
                  onClick={() => fileInputRef.current?.click()}
                  onDrop={handleFileDrop}
                  onDragOver={(e) => e.preventDefault()}
                >
                  <Table2Columns className="mx-auto mb-4 w-12 h-12 text-gray-400" />
                  <h3 className="mb-2 text-lg font-medium text-gray-900">
                    Add Evaluation File (.csv)
                  </h3>
                  <p className="mb-4 text-sm text-gray-600">
                    Drop your CSV file here or click to browse.
                  </p>
                  <p className="mb-4 text-xs text-gray-500">
                    Required: 'question' column. Optional: 'expected_answer', 'category', 'context'
                  </p>

                  {/* Sample CSV Download Link */}
                  <Button
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadSampleCSV();
                    }}
                    className="inline-flex gap-2 items-center px-3 py-2 text-sm text-blue-600 rounded-md transition-colors hover:text-blue-800 hover:bg-blue-50"
                  >
                    <Page className="w-4 h-4" />
                    Get Sample CSV
                  </Button>

                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv"
                    onChange={handleFileInputChange}
                    className="hidden"
                  />
                </div>
                {csvError && (
                  <div className="p-3 mt-4 bg-red-50 rounded-md border border-red-200">
                    <p className="text-sm text-red-600">{csvError}</p>
                  </div>
                )}
              </div>
            ) : (
              /* CSV Preview and Configuration */
              <div className="space-y-4">
                <div className="p-4 bg-green-50 rounded-md border border-green-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-green-800">✓ CSV Loaded Successfully</h4>
                      <p className="mt-1 text-sm text-green-600">
                        {parsedCSV.data.length} questions found
                      </p>
                    </div>
                    <button
                      onClick={() => {
                        setCsvFile(null);
                        setParsedCSV(null);
                        setCsvError('');
                      }}
                      className="text-green-600 hover:text-green-800"
                    >
                      <Xmark className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* CSV Preview */}
                <div className="rounded-lg border border-gray-200">
                  <div className="px-4 py-3 bg-gray-50 border-b border-gray-200">
                    <h4 className="font-medium text-gray-900">Preview (First 5 rows)</h4>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead className="bg-gray-50">
                        <tr>
                          {parsedCSV.headers.map((header, index) => (
                            <th
                              key={index}
                              className="px-4 py-2 text-xs font-medium tracking-wider text-left text-gray-500 uppercase"
                            >
                              {header}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-200">
                        {parsedCSV.preview.map((row, index) => (
                          <tr key={index} className="hover:bg-gray-50">
                            <td className="px-4 py-3 max-w-xs text-sm text-gray-900 truncate">
                              {row.question}
                            </td>
                            {row.expected_answer !== undefined && (
                              <td className="px-4 py-3 max-w-xs text-sm text-gray-900 truncate">
                                {row.expected_answer}
                              </td>
                            )}
                            {row.category !== undefined && (
                              <td className="px-4 py-3 text-sm text-gray-900">{row.category}</td>
                            )}
                            {row.context !== undefined && (
                              <td className="px-4 py-3 max-w-xs text-sm text-gray-900 truncate">
                                {row.context}
                              </td>
                            )}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                {/* Configuration */}
                <div className="p-4 rounded-lg border border-gray-200">
                  <h4 className="mb-3 font-medium text-gray-900">Configuration</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-700">
                        Batch Size
                      </label>
                      <select
                        value={batchSize}
                        onChange={(e) => setBatchSize(parseInt(e.target.value))}
                        className="px-3 py-2 w-full rounded-md border border-gray-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      >
                        <option value={1}>1 (Sequential)</option>
                        <option value={3}>3</option>
                        <option value={5}>5 (Recommended)</option>
                        <option value={10}>10</option>
                        <option value={20}>20</option>
                      </select>
                    </div>
                    <div>
                      <label className="block mb-2 text-sm font-medium text-gray-700">
                        Total Questions
                      </label>
                      <p className="px-3 py-2 text-gray-900 bg-gray-50 rounded-md border border-gray-300">
                        {parsedCSV.data.length}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Start Button */}
                <button
                  onClick={startBulkEvaluation}
                  disabled={bulkEvaluationState.isRunning}
                  className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                    bulkEvaluationState.isRunning
                      ? 'bg-gray-400 text-gray-600 cursor-not-allowed'
                      : 'bg-blue-600 text-white hover:bg-blue-700'
                  }`}
                >
                  {bulkEvaluationState.isRunning
                    ? 'Running Evaluation...'
                    : 'Start Bulk Evaluation'}
                </button>

                {/* Progress */}
                {bulkEvaluationState.isRunning && (
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-sm font-medium text-blue-800">Progress</span>
                      <span className="text-sm text-blue-600">
                        {bulkEvaluationState.progress.current} /{' '}
                        {bulkEvaluationState.progress.total}
                      </span>
                    </div>
                    <div className="mb-3 w-full h-2 bg-blue-200 rounded-full">
                      <div
                        className="h-2 bg-blue-600 rounded-full transition-all duration-300"
                        style={{ width: `${bulkEvaluationState.progress.progress}%` }}
                      ></div>
                    </div>
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-green-600">
                          ✓ {bulkEvaluationState.progress.successful}
                        </span>
                        <span className="ml-1 text-gray-600">successful</span>
                      </div>
                      <div>
                        <span className="font-medium text-red-600">
                          ✗ {bulkEvaluationState.progress.failed}
                        </span>
                        <span className="ml-1 text-gray-600">failed</span>
                      </div>
                      <div>
                        <span className="font-medium text-blue-600">
                          {Math.ceil(bulkEvaluationState.progress.estimatedTimeRemaining)}s
                        </span>
                        <span className="ml-1 text-gray-600">remaining</span>
                      </div>
                    </div>
                  </div>
                )}

                {/* Results */}
                {bulkEvaluationState.results.length > 0 && (
                  <div className="rounded-lg border border-gray-200">
                    <div className="flex justify-between items-center px-4 py-3 bg-gray-50 border-b border-gray-200">
                      <h4 className="font-medium text-gray-900">
                        Results ({bulkEvaluationState.results.length})
                      </h4>
                      <button
                        onClick={exportResultsToCSV}
                        className="flex gap-2 items-center px-3 py-1 text-sm text-white bg-green-600 rounded-md transition-colors hover:bg-green-700"
                      >
                        <Download className="w-4 h-4" />
                        Export CSV
                      </button>
                    </div>
                    <div className="overflow-y-auto max-h-96 custom-scrollbar">
                      {bulkEvaluationState.results.map((result, index) => (
                        <div
                          key={index}
                          className={`p-4 border-b border-gray-200 last:border-b-0 ${
                            result.status === 'error' ? 'bg-red-50' : 'bg-white'
                          }`}
                        >
                          <div className="flex justify-between items-start mb-2">
                            <h5 className="text-sm font-medium text-gray-900">
                              Q{index + 1}: {result.question}
                            </h5>
                            <span
                              className={`text-xs px-2 py-1 rounded-full ${
                                result.status === 'success'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-red-100 text-red-800'
                              }`}
                            >
                              {result.status} ({result.response_time.toFixed(0)}ms)
                            </span>
                          </div>
                          {result.status === 'success' ? (
                            <div className="text-sm text-gray-700">
                              <MarkdownViewerSmall>{result.response}</MarkdownViewerSmall>
                            </div>
                          ) : (
                            <div className="text-sm text-red-600">
                              Error: {result.error || 'Unknown error'}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Collapsible Live Logs Section */}
      {(isLoading || logUpdates.length > 0) && !hideLogs && (
        <div className="border-t border-gray-200 dark:border-gray-700">
          {/* Toggle Button */}
          <div className="flex justify-between items-center px-4 py-3 transition-colors hover:bg-gray-50 dark:hover:bg-gray-800">
            <div
              className="flex flex-1 gap-2 items-center cursor-pointer"
              onClick={() => setShowLogs(!showLogs)}
            >
              <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                Backend Logs
              </span>
              {isLoading && (
                <div className="flex gap-1 items-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                  <span className="text-xs text-blue-600 dark:text-blue-400">Live</span>
                </div>
              )}
              {logUpdates.length > 0 && (
                <span className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 text-xs px-2 py-0.5 rounded-full font-medium">
                  {logUpdates.length}
                </span>
              )}
              {showLogs ? (
                <NavArrowUp className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              ) : (
                <NavArrowDown className="w-4 h-4 text-gray-400 dark:text-gray-500" />
              )}
            </div>

            {/* Close button */}
            {!isLoading && (
              <button
                onClick={() => {
                  setHideLogs(true);
                  setShowLogs(false);
                }}
                className="p-1 rounded transition-colors hover:bg-gray-200 dark:hover:bg-gray-700"
                title="Hide logs"
              >
                <Xmark className="w-3 h-3 text-gray-400 dark:text-gray-500" />
              </button>
            )}
          </div>

          {/* Logs Content - Only show when expanded */}
          {showLogs && (
            <div className="px-4 pb-3">
              <LogViewer
                logs={logUpdates}
                showTimestamps={true}
                autoScroll={true}
                maxHeight="150px"
              />
            </div>
          )}
        </div>
      )}

      {/* Input - Only show for individual mode */}
      {evaluationMode === 'individual' && (
        <div className="p-4">
          <div className="flex relative">
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Type your message"
              className="w-full min-h-[100px] max-h-[120px] pl-3 pr-12 py-3 text-sm rounded-lg bg-gray-100 border-gray-300
                focus:outline-none focus:ring-1 focus:ring-gray-500 focus:border-transparent resize-none overflow-y-auto custom-scrollbar"
              rows={2}
              disabled={isLoading || bulkEvaluationState.isRunning}
            />
            {inputText.trim() && (
              <button
                onClick={handleSendMessage}
                className="absolute bottom-3 right-4 p-2 text-white bg-gray-700 rounded-full transition-colors hover:text-blue-600"
                title="Send message"
                disabled={isLoading || bulkEvaluationState.isRunning}
              >
                <ArrowUp className="w-4 h-4" strokeWidth={1.5} />
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
