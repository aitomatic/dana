/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Play, Workflow, Layers, Clock, CheckCircle, XCircle, Pause, Loader } from 'lucide-react';
import { apiService } from '@/lib/api';
import type { WorkflowExecutionRequest, WorkflowExecutionControl } from '@/lib/api';
import { cn } from '@/lib/utils';

// Execution status enum matching Dana's ExecutionStatus
const ExecutionStatus = {
  IDLE: 'idle',
  RUNNING: 'running',
  COMPLETED: 'completed',
  FAILED: 'failed',
  PAUSED: 'paused',
  CANCELLED: 'cancelled',
} as const;

type ExecutionStatus = (typeof ExecutionStatus)[keyof typeof ExecutionStatus];

interface WorkflowDefinition {
  name: string;
  steps: string[];
  pipeline: string;
  description?: string;
  executionStatus?: ExecutionStatus;
  currentStep?: number;
  startTime?: Date;
  endTime?: Date;
  executionTime?: number;
  errorMessage?: string;
}

interface WorkflowExecution {
  workflowId: string;
  status: ExecutionStatus;
  currentStep: number;
  totalSteps: number;
  startTime: Date;
  lastUpdateTime: Date;
  executionTime: number;
  endTime?: Date;
  stepResults: StepResult[];
  errorMessage?: string;
  execution_metadata?: {
    execution_time?: number;
    memory_usage?: number;
    steps_executed?: number;
    errors?: string[];
  };
  result?: any;
  error?: string;
}

interface StepResult {
  stepIndex: number;
  stepName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  startTime?: Date;
  endTime?: Date;
  executionTime?: number;
  result?: any; // Add result property to match backend
  errorMessage?: string;
  input?: any;
  error?: string;
}

interface ParsedWorkflow {
  workflow_definitions: WorkflowDefinition[];
  function_definitions: Record<string, unknown>[];
  has_pipeline_workflows: boolean;
  total_workflows: number;
}

/**
 * WorkflowsTab Component - AI Engineer Workflow Execution Dashboard
 *
 * This component provides a comprehensive view of Dana workflow execution with:
 *
 * 🔄 INPUT/OUTPUT FLOW:
 * 1. INPUT: Query, context, transaction data sent to workflow
 * 2. PROCESSING: Step-by-step execution with real-time status updates
 * 3. OUTPUT: Structured results, insights, and recommendations
 *
 * 📊 EXECUTION TRACKING:
 * - Real-time status updates every second
 * - Step-by-step progress visualization
 * - Input/output data for each step
 * - Execution metrics and timing
 *
 * 🎯 AI ENGINEER FEATURES:
 * - View workflow code and structure
 * - Monitor execution in real-time
 * - Debug step-by-step data flow
 * - Analyze input/output transformations
 * - Track performance metrics
 */
const WorkflowsTab: React.FC = () => {
  const { agent_id: agentId } = useParams<{ agent_id: string }>();
  const [workflows, setWorkflows] = useState<ParsedWorkflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [executingWorkflows, setExecutingWorkflows] = useState<Map<string, WorkflowExecution>>(
    new Map(),
  );
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowDefinition | null>(null);
  const [customTestQuery, setCustomTestQuery] = useState<string>('');

  // Real-time execution updates from Dana runtime
  useEffect(() => {
    const updateExecutions = async () => {
      setExecutingWorkflows((prevExecutions) => {
        const updated = new Map(prevExecutions);

        for (const [executionId, execution] of updated.entries()) {
          if (execution.status === ExecutionStatus.RUNNING) {
            // Use a promise to get the status, but don't await it here
            // to avoid blocking the UI updates
            apiService
              .getWorkflowExecutionStatus(executionId)
              .then((status) => {
                console.log(`Updating execution ${executionId}:`, status);

                // Update execution with real data
                execution.status = status.status as ExecutionStatus;
                execution.currentStep = status.current_step;
                execution.executionTime = status.execution_time;
                execution.stepResults = status.step_results.map((step) => ({
                  stepIndex: step.step_index,
                  stepName: step.step_name,
                  status: step.status,
                  startTime: step.start_time ? new Date(step.start_time) : undefined,
                  endTime: step.end_time ? new Date(step.end_time) : undefined,
                  executionTime: step.execution_time,
                  result: step.result,
                  errorMessage: step.error,
                }));

                // Check if execution completed
                if (status.status === ExecutionStatus.COMPLETED) {
                  execution.endTime = new Date();
                }

                console.log(`Updated execution ${executionId}:`, execution);
                console.log(
                  `📊 Step ${execution.currentStep + 1} completed with result:`,
                  execution.stepResults[execution.currentStep]?.result,
                );

                // Force a re-render by updating the state
                setExecutingWorkflows(new Map(updated));
              })
              .catch((error) => {
                console.error(`Failed to get status for execution ${executionId}:`, error);
              });
          }
        }

        return updated;
      });
    };

    const interval = setInterval(updateExecutions, 1000); // Update every second
    return () => clearInterval(interval);
  }, []); // Remove dependency to prevent infinite loop

  const fetchWorkflows = async (id: number) => {
    try {
      setLoading(true);
      setError(null);

      // Get workflows.na file content
      const fileContent = await apiService.getAgentFileContent(id, 'workflows.na');

      // Parse the workflow content (simple parsing for now)
      const parsed = parseWorkflowContent(fileContent.content);
      setWorkflows(parsed);
    } catch (err) {
      console.error('Error fetching workflows:', err);
      setError('Failed to load workflows');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log({ agentId });
    if (agentId) {
      fetchWorkflows(parseInt(agentId));
    }
  }, [agentId]);

  const parseWorkflowContent = (content: string): ParsedWorkflow => {
    const lines = content
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line && !line.startsWith('#'));

    const workflow_definitions: WorkflowDefinition[] = [];
    console.log({ content });

    for (const line of lines) {
      // Parse imports
      console.log({ line });

      // Parse workflow definitions - look for "def workflow_name(params) = step1 | step2 | step3"
      if (line.startsWith('def ') && line.includes(' = ') && line.includes('|')) {
        // Extract function name from "def workflow_name(params)"
        const funcDef = line.substring(4); // Remove "def "
        const openParen = funcDef.indexOf('(');
        if (openParen > 0) {
          const workflowName = funcDef.substring(0, openParen).trim();
          const pipeline = line.substring(line.indexOf(' = ') + 3); // Get everything after " = "
          const steps = pipeline.split('|').map((step) => step.trim());

          workflow_definitions.push({
            name: workflowName,
            steps,
            pipeline: pipeline.trim(),
            description: `${steps.join(' → ')}`,
            executionStatus: ExecutionStatus.IDLE,
          });
        }
      }
    }

    return {
      workflow_definitions,
      function_definitions: [],
      has_pipeline_workflows: workflow_definitions.length > 0,
      total_workflows: workflow_definitions.length,
    };
  };

  const generateAgentSpecificTestData = (
    agentId: number,
    workflowName: string,
    customQuery?: string,
  ) => {
    // Generate context-aware test data based on agent type and workflow
    const baseData = {
      query: customQuery || 'How can I help you today?',
      context: 'General inquiry',
      timestamp: new Date().toISOString(),
      user_id: 'user_123',
      session_id: `session_${Date.now()}`,
    };

    // Agent-specific data based on common agent types
    switch (agentId) {
      case 1: // Agent 1 - Nova (likely general purpose)
        return {
          ...baseData,
          query: customQuery || 'What can you help me with today?',
          context: 'General assistance request',
          agent_type: 'general_purpose',
          capabilities: ['information_retrieval', 'task_execution', 'problem_solving'],
        };

      case 2: // Agent 2 - Likely specialized
        return {
          ...baseData,
          query: customQuery || 'I need help with my specific domain',
          context: 'Domain-specific inquiry',
          agent_type: 'specialized',
          domain: 'business_operations',
          priority: 'medium',
        };

      case 3: // Agent 3 - Sofia (likely customer service)
        return {
          ...baseData,
          query: customQuery || 'I have a customer service question',
          context: 'Customer support inquiry',
          agent_type: 'customer_service',
          customer_tier: 'premium',
          issue_category: 'general_support',
        };

      default:
        // Generic data for unknown agents
        return {
          ...baseData,
          query: customQuery || 'How can I assist you?',
          context: 'Standard inquiry',
          agent_type: 'unknown',
          workflow_name: workflowName,
        };
    }
  };

  const startWorkflowExecution = async (workflow: WorkflowDefinition) => {
    try {
      // Generate agent-specific test data
      const testData = generateAgentSpecificTestData(
        parseInt(agentId || '0'),
        workflow.name,
        customTestQuery,
      );

      // Start workflow execution using Dana runtime
      const request: WorkflowExecutionRequest = {
        agent_id: parseInt(agentId || '0'),
        workflow_name: workflow.name,
        input_data: testData,
        execution_mode: 'step-by-step',
      };

      console.log(
        `🚀 Starting workflow '${workflow.name}' with agent-specific input:`,
        request.input_data,
      );

      const response = await apiService.startWorkflowExecution(request);

      if (!response.success) {
        console.error('Failed to start workflow execution:', response.error);
        return;
      }

      // Create execution tracking object
      const execution: WorkflowExecution = {
        workflowId: workflow.name, // Use workflow name for display purposes
        status: ExecutionStatus.RUNNING,
        currentStep: response.current_step,
        totalSteps: response.total_steps,
        startTime: new Date(),
        lastUpdateTime: new Date(),
        executionTime: response.execution_time,
        stepResults: response.step_results.map((step) => ({
          stepIndex: step.step_index,
          stepName: step.step_name,
          status: step.status,
          startTime: undefined,
          endTime: undefined,
          executionTime: step.execution_time,
          errorMessage: step.error,
          input: step.input, // Preserve input data from backend
          result: step.result, // Preserve result data from backend
        })),
      };

      // Mark first step as running
      if (execution.stepResults.length > 0) {
        execution.stepResults[0].status = 'running';
      }

      // Store execution with execution_id as the key
      setExecutingWorkflows((prev) => new Map(prev).set(response.execution_id, execution));

      // Update workflow status
      setWorkflows((prev) => {
        if (!prev) return prev;
        return {
          ...prev,
          workflow_definitions: prev.workflow_definitions.map((w) =>
            w.name === workflow.name
              ? { ...w, executionStatus: ExecutionStatus.RUNNING, startTime: new Date() }
              : w,
          ),
        };
      });

      console.log(`✅ Started workflow execution: ${response.execution_id}`);
      console.log(`📊 Initial execution state:`, execution);
    } catch (error) {
      console.error('Failed to start workflow execution:', error);
    }
  };

  const stopWorkflowExecution = async (executionId: string) => {
    try {
      // Stop workflow execution using Dana runtime
      const control: WorkflowExecutionControl = {
        execution_id: executionId,
        action: 'stop',
      };

      const response = await apiService.controlWorkflowExecution(control);

      if (!response.success) {
        console.error('Failed to stop workflow execution:', response.error);
        return;
      }

      setExecutingWorkflows((prev) => {
        const updated = new Map(prev);
        const execution = updated.get(executionId);
        if (execution) {
          execution.status = ExecutionStatus.CANCELLED;
          execution.endTime = new Date();
        }
        return updated;
      });

      console.log(`Stopped workflow execution: ${executionId}`);
    } catch (error) {
      console.error('Failed to stop workflow execution:', error);
    }
  };

  const getExecutionStatusIcon = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.RUNNING:
        return <Loader className="w-4 h-4 text-blue-600 animate-spin" />;
      case ExecutionStatus.COMPLETED:
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case ExecutionStatus.FAILED:
        return <XCircle className="w-4 h-4 text-red-600" />;
      case ExecutionStatus.PAUSED:
        return <Pause className="w-4 h-4 text-yellow-600" />;
      case ExecutionStatus.CANCELLED:
        return <XCircle className="w-4 h-4 text-gray-600" />;
      default:
        return <Clock className="w-4 h-4 text-gray-400" />;
    }
  };

  const getExecutionStatusColor = (status: ExecutionStatus) => {
    switch (status) {
      case ExecutionStatus.RUNNING:
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case ExecutionStatus.COMPLETED:
        return 'bg-green-100 text-green-800 border-green-200';
      case ExecutionStatus.FAILED:
        return 'bg-red-100 text-red-800 border-red-200';
      case ExecutionStatus.PAUSED:
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case ExecutionStatus.CANCELLED:
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-600 border-gray-200';
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="w-8 h-8 rounded-full border-b-2 border-blue-600 animate-spin"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="p-4 bg-red-50 rounded-lg border border-red-200">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="w-5 h-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error loading workflows</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!workflows || workflows.workflow_definitions.length === 0) {
    return (
      <div className="p-8">
        <div className="text-center">
          <Workflow className="mx-auto w-12 h-12 text-gray-400" />
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows found</h3>
          <p className="mt-1 text-sm text-gray-500">
            This agent doesn't have any workflow definitions yet.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-6 pb-6">
      {/* Workflow Execution Dashboard */}
      <div className="mb-6">
        <div className="flex gap-3 items-center m-4">
          <h2 className="text-2xl font-bold text-gray-900">Workflow</h2>
          <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">
            Coming Soon
          </span>
        </div>

        {/* AI Engineer Test Configuration */}
        <div className="p-6 mb-6 hidden  via-blue-50 to-indigo-50 rounded-xl border shadow-sm from-slate-50 border-slate-200">
          <div className="flex justify-between items-center mb-4">
            <div className="flex items-center space-x-3">
              <div>
                <h3 className="text-xl font-semibold text-slate-800">AI Engineer Test Suite</h3>
                <p className="text-sm text-slate-600">
                  Configure test parameters for workflow validation
                </p>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Test Query Configuration */}
            <div className="lg:col-span-2">
              <div className="p-4 bg-white rounded-lg border shadow-sm border-slate-200">
                <label className="block mb-3 text-sm font-semibold text-slate-700">
                  <span className="flex items-center space-x-2">
                    <svg
                      className="w-4 h-4 text-blue-500"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                    <span>Test Query Input</span>
                  </span>
                </label>
                <textarea
                  value={customTestQuery}
                  onChange={(e) => setCustomTestQuery(e.target.value)}
                  placeholder="Enter custom test query or leave empty for agent-specific defaults..."
                  rows={3}
                  className="px-4 py-3 w-full font-mono text-sm rounded-lg border resize-none border-slate-300 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <div className="flex justify-between items-center mt-2">
                  <p className="text-xs text-slate-500">
                    💡 <span className="font-medium">Pro tip:</span> Use specific queries to test
                    edge cases and workflow robustness
                  </p>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => setCustomTestQuery('')}
                      className="px-3 py-1.5 bg-slate-100 text-slate-700 text-xs font-medium rounded-md hover:bg-slate-200 transition-colors flex items-center space-x-1"
                    >
                      <svg
                        className="w-3 h-3"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                      <span>Reset</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Test Configuration Options */}
            <div className="space-y-4">
              <div className="p-4 bg-white rounded-lg border shadow-sm border-slate-200">
                <h4 className="flex items-center mb-3 space-x-2 text-sm font-semibold text-slate-700">
                  <svg
                    className="w-4 h-4 text-indigo-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <span>Test Configuration</span>
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">Execution Mode:</span>
                    <span className="px-2 py-1 text-xs font-medium text-blue-800 bg-blue-100 rounded">
                      Step-by-Step
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">Runtime:</span>
                    <span className="px-2 py-1 text-xs font-medium text-green-800 bg-green-100 rounded">
                      Dana Engine
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-600">Validation:</span>
                    <span className="px-2 py-1 text-xs font-medium text-purple-800 bg-purple-100 rounded">
                      Real-time
                    </span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-white rounded-lg border shadow-sm border-slate-200">
                <h4 className="flex items-center mb-3 space-x-2 text-sm font-semibold text-slate-700">
                  <svg
                    className="w-4 h-4 text-emerald-500"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span>Quick Actions</span>
                </h4>
                <div className="space-y-2">
                  <button
                    onClick={() => setCustomTestQuery('Test edge case with empty input')}
                    className="px-3 py-2 w-full text-xs font-medium text-left text-gray-600 bg-gray-50 rounded-md transition-colors hover:bg-emerald-100"
                  >
                    Edge Case Test
                  </button>
                  <button
                    onClick={() => setCustomTestQuery('Performance test with complex query')}
                    className="px-3 py-2 w-full text-xs font-medium text-left text-gray-600 bg-gray-50 rounded-md transition-colors hover:bg-blue-100"
                  >
                    Performance Test
                  </button>
                  <button
                    onClick={() => setCustomTestQuery('Integration test with external data')}
                    className="px-3 py-2 w-full text-xs font-medium text-left text-gray-600 bg-gray-50 rounded-md transition-colors hover:bg-purple-100"
                  >
                    Integration Test
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Execution Overview */}
      <div className="grid hidden grid-cols-1 gap-4 mb-6 md:grid-cols-4">
        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Workflow className="w-5 h-5 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Total Workflows</p>
              <p className="text-2xl font-bold text-gray-900">{workflows.total_workflows}</p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Completed</p>
              <p className="text-2xl font-bold text-gray-900">
                {
                  Array.from(executingWorkflows.values()).filter(
                    (w) => w.status === ExecutionStatus.COMPLETED,
                  ).length
                }
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Loader className="w-5 h-5 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Running</p>
              <p className="text-2xl font-bold text-gray-900">
                {
                  Array.from(executingWorkflows.values()).filter(
                    (w) => w.status === ExecutionStatus.RUNNING,
                  ).length
                }
              </p>
            </div>
          </div>
        </div>

        <div className="p-4 bg-white rounded-lg border border-gray-200 shadow-sm">
          <div className="flex items-center">
            <div className="p-2 bg-red-100 rounded-lg">
              <XCircle className="w-5 h-5 text-red-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-600">Failed</p>
              <p className="text-2xl font-bold text-gray-900">
                {
                  Array.from(executingWorkflows.values()).filter(
                    (w) => w.status === ExecutionStatus.FAILED,
                  ).length
                }
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Workflow Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {workflows.workflow_definitions.map((workflow) => {
          // Find execution by workflow name (for now, we'll use the first execution found)
          // In a real implementation, you might want to track workflow name to execution ID mapping
          const execution = Array.from(executingWorkflows.values()).find(
            (exec) =>
              exec.workflowId === workflow.name || exec.workflowId.startsWith(workflow.name),
          );

          console.log(`Workflow ${workflow.name}:`, {
            execution,
            executingWorkflowsSize: executingWorkflows.size,
            allExecutions: Array.from(executingWorkflows.entries()),
          });

          const isExecuting = execution && execution.status === ExecutionStatus.RUNNING;

          return (
            <div
              key={workflow.name}
              className={cn(
                'p-6 bg-gradient-to-br  to-gray-50 rounded-xl border border-gray-200  duration-300 transform ',
                isExecuting ? 'ring-2 ring-blue-500' : '',
              )}
            >
              {/* Workflow Header */}
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="mb-2 text-xl font-bold text-gray-900">{workflow.name}</h3>
                  <div className="inline-block px-3 py-2 rounded-lg border border-gray-100">
                    <span className="text-sm text-gray-600">{workflow.description}</span>
                  </div>
                </div>

                {/* Execution Status Badge */}
                <div
                  className={`inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold border ${getExecutionStatusColor(execution?.status || ExecutionStatus.IDLE)}`}
                >
                  {getExecutionStatusIcon(execution?.status || ExecutionStatus.IDLE)}
            
                </div>
              </div>

              {/* Execution Progress */}
              {execution && (
                <div className="p-4 mb-4 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-gray-700">Execution Progress</span>
                    <span className="text-sm text-gray-500">
                      Step {Math.min(execution.currentStep + 1, execution.totalSteps)} of{' '}
                      {execution.totalSteps}
                    </span>
                  </div>

                  {/* Progress Bar Container */}
                  <div className="overflow-hidden w-full h-2 bg-gray-200 rounded-full">
                    <div
                      className="h-2 bg-blue-600 rounded-full transition-all duration-300"
                      style={{
                        width: `${Math.min(100, Math.max(0, ((execution.currentStep + 1) / execution.totalSteps) * 100))}%`,
                      }}
                    ></div>
                  </div>

                  {/* Execution Time */}
                  <div className="flex items-center mt-2 text-sm text-gray-500">
                    <Clock className="mr-1 w-4 h-4" />
                    {execution.executionTime > 0
                      ? `${Math.round(execution.executionTime)}s`
                      : 'Starting...'}
                  </div>

                  {/* Real-time Data Flow from Dana Runtime */}
                  <div className="p-3 mt-3 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                    <div className="flex items-center mb-2 text-xs font-medium text-blue-800">
                      <span className="mr-1">🔄</span> Real-time Data Flow
                    </div>

                    {/* Execution Status */}
                    <div className="p-2 mb-2 bg-white rounded border border-blue-100">
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        <div>
                          <span className="font-medium text-blue-600">Status:</span>
                          <span
                            className={`ml-1 px-1 py-0.5 text-xs rounded ${
                              execution.status === ExecutionStatus.COMPLETED
                                ? 'bg-green-100 text-green-700'
                                : execution.status === ExecutionStatus.RUNNING
                                  ? 'bg-blue-100 text-blue-700'
                                  : execution.status === ExecutionStatus.FAILED
                                    ? 'bg-red-100 text-red-700'
                                    : 'bg-gray-100 text-gray-700'
                            }`}
                          >
                            {execution.status}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-blue-600">Runtime:</span>
                          <span className="ml-1 text-blue-700">
                            {execution.executionTime > 0
                              ? `${Math.round(execution.executionTime)}s`
                              : 'Starting...'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Input/Output Data */}
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="font-medium text-blue-600">📥 Input:</span>
                        <div className="p-1 mt-1 text-blue-700 truncate bg-blue-100 rounded border border-blue-200">
                          {execution.stepResults[0]?.input
                            ? typeof execution.stepResults[0].input === 'object'
                              ? JSON.stringify(execution.stepResults[0].input).substring(0, 60) +
                                '...'
                              : String(execution.stepResults[0].input).substring(0, 60) + '...'
                            : 'No input data'}
                        </div>
                      </div>
                      <div>
                        <span className="font-medium text-green-600">📤 Output:</span>
                        <div className="p-1 mt-1 text-green-700 truncate bg-green-100 rounded border border-green-200">
                          {execution.stepResults[execution.stepResults.length - 1]?.result
                            ? typeof execution.stepResults[execution.stepResults.length - 1]
                                .result === 'object'
                              ? JSON.stringify(
                                  execution.stepResults[execution.stepResults.length - 1].result,
                                ).substring(0, 60) + '...'
                              : String(
                                  execution.stepResults[execution.stepResults.length - 1].result,
                                ).substring(0, 60) + '...'
                            : 'No output data'}
                        </div>
                      </div>
                    </div>

                    {/* Execution Metadata */}
                    {execution.execution_metadata &&
                      Object.keys(execution.execution_metadata).length > 0 && (
                        <div className="p-2 mt-2 bg-white rounded border border-blue-100">
                          <div className="mb-1 text-xs font-medium text-blue-600">
                            ⚡ Runtime Metrics
                          </div>
                          <div className="grid grid-cols-2 gap-1 text-xs">
                            <div>
                              <span className="text-gray-600">Memory:</span>
                              <span className="ml-1 text-gray-700">
                                {execution.execution_metadata.memory_usage
                                  ? `${execution.execution_metadata.memory_usage}MB`
                                  : 'N/A'}
                              </span>
                            </div>
                            <div>
                              <span className="text-gray-600">Steps:</span>
                              <span className="ml-1 text-gray-700">
                                {execution.execution_metadata.steps_executed || 0}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}

                    {/* View Details Button */}
                    <button
                      onClick={() => setSelectedWorkflow(workflow)}
                      className="px-2 py-1 mt-2 w-full text-xs text-blue-800 bg-blue-100 rounded transition-colors hover:bg-blue-200"
                    >
                      🔍 View Full Execution Details
                    </button>
                  </div>
                </div>
              )}

              {/* Workflow Steps */}
              <div className="mb-6">
                <h5 className="flex items-center mb-4 text-sm font-medium text-gray-700">
                  <Layers className="mr-2 w-4 h-4" />
                  Workflow Steps
                </h5>
                <div className="relative">
                  {workflow.steps.map((step, stepIndex) => {
                    const stepExecution = execution?.stepResults[stepIndex];
                    const stepStatus = stepExecution?.status || 'pending';

                    return (
                      <div key={stepIndex} className="relative">
                        {/* Step Card */}
                        <div className="flex items-center mb-3">
                          {/* Step Number Circle */}
                          <div
                            className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center mr-4 z-10 relative ${
                              stepStatus === 'completed'
                                ? 'bg-gradient-to-br from-green-500 to-green-600'
                                : stepStatus === 'running'
                                  ? 'bg-gradient-to-br from-blue-500 to-blue-600 animate-pulse'
                                  : stepStatus === 'failed'
                                    ? 'bg-gradient-to-br from-red-500 to-red-600'
                                    : 'bg-gradient-to-br from-gray-400 to-gray-500'
                            } shadow-lg`}
                          >
                            {stepStatus === 'running' ? (
                              <Loader className="w-5 h-5 text-white animate-spin" />
                            ) : stepStatus === 'completed' ? (
                              <CheckCircle className="w-5 h-5 text-white" />
                            ) : stepStatus === 'failed' ? (
                              <XCircle className="w-5 h-5 text-white" />
                            ) : (
                              <span className="text-sm font-bold text-white">{stepIndex + 1}</span>
                            )}
                          </div>

                          {/* Step Content */}
                          <div className="flex-1 px-5 py-4 bg-gradient-to-r from-gray-50 to-white rounded-xl border border-gray-200 shadow-sm transition-all duration-300 transform">
                            <div className="flex justify-between items-center mb-2">
                              <span className="font-mono text-sm font-medium text-gray-800">
                                {step}
                              </span>
                              <span
                                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  stepStatus === 'completed'
                                    ? 'bg-green-100 text-green-800'
                                    : stepStatus === 'running'
                                      ? 'bg-blue-100 text-blue-800'
                                      : stepStatus === 'failed'
                                        ? 'bg-red-100 text-red-800'
                                        : 'bg-gray-100 text-gray-600'
                                }`}
                              >
                                {stepStatus === 'completed'
                                  ? 'Completed'
                                  : stepStatus === 'running'
                                    ? 'Running'
                                    : stepStatus === 'failed'
                                      ? 'Failed'
                                      : 'Pending'}
                              </span>
                            </div>

                            {/* Step Type Indicator */}
                            <div className="flex items-center">
                              <span
                                className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                                  stepIndex === 0
                                    ? 'bg-green-100 text-green-800'
                                    : stepIndex === workflow.steps.length - 1
                                      ? 'bg-purple-100 text-purple-800'
                                      : 'bg-blue-100 text-blue-800'
                                }`}
                              >
                                {stepIndex === 0
                                  ? 'Input'
                                  : stepIndex === workflow.steps.length - 1
                                    ? 'Output'
                                    : 'Process'}
                              </span>
                              <span className="ml-2 text-xs text-gray-500">
                                {stepIndex === 0
                                  ? 'Initial data processing'
                                  : stepIndex === workflow.steps.length - 1
                                    ? 'Final result generation'
                                    : 'Data transformation step'}
                              </span>
                            </div>
                          </div>
                        </div>

                        {/* Connector Line */}
                        {stepIndex < workflow.steps.length - 1 && (
                          <div className="absolute left-5 top-10 w-0.5 h-8 bg-gradient-to-b from-blue-400 to-blue-200"></div>
                        )}
                      </div>
                    );
                  })}

                  {/* Overall Workflow Flow Indicator */}
                  <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-600 via-blue-400 to-blue-200 opacity-30"></div>
                </div>
              </div>

              {/* Execution Controls */}
              <div className="flex hidden space-x-3">
                {!execution ||
                execution.status === ExecutionStatus.IDLE ||
                execution.status === ExecutionStatus.COMPLETED ||
                execution.status === ExecutionStatus.FAILED ? (
                  <button
                    onClick={() => startWorkflowExecution(workflow)}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md border border-transparent transition-colors hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                  >
                    <Play className="mr-2 w-4 h-4" />
                    Execute Workflow
                  </button>
                ) : execution.status === ExecutionStatus.RUNNING ? (
                  <button
                    onClick={() => stopWorkflowExecution(execution.workflowId)}
                    className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md border border-transparent transition-colors hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
                  >
                    <XCircle className="mr-2 w-4 h-4" />
                    Stop Execution
                  </button>
                ) : null}

                <button
                  onClick={() => setSelectedWorkflow(workflow)}
                  className="inline-flex items-center px-4 py-2 text-sm font-medium text-gray-700 bg-white rounded-md border border-gray-300 transition-colors hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <Layers className="mr-2 w-4 h-4" />
                  View Details
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Workflow Details Modal */}
      {selectedWorkflow && (
        <div className="overflow-y-auto fixed inset-0 z-50 w-full h-full bg-gray-600 bg-opacity-50">
          <div className="relative top-20 p-5 mx-auto w-11/12 bg-white rounded-md border shadow-lg md:w-3/4 lg:w-1/2">
            <div className="mt-3">
              <h3 className="mb-4 text-lg font-medium text-gray-900">
                Workflow Details: {selectedWorkflow.name}
              </h3>

              {/* Execution Summary (if available) */}
              {(() => {
                const execution = Array.from(executingWorkflows.values()).find(
                  (exec) => exec.workflowId === selectedWorkflow.name,
                );

                if (execution) {
                  return (
                    <div className="p-4 mb-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h4 className="mb-2 text-sm font-medium text-blue-800">Execution Summary</h4>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="font-medium text-blue-600">Status:</span>
                          <span
                            className={`ml-2 px-2 py-1 text-xs rounded-full ${
                              execution.status === ExecutionStatus.COMPLETED
                                ? 'bg-green-100 text-green-800'
                                : execution.status === ExecutionStatus.RUNNING
                                  ? 'bg-blue-100 text-blue-800'
                                  : execution.status === ExecutionStatus.FAILED
                                    ? 'bg-red-100 text-red-800'
                                    : 'bg-gray-100 text-gray-800'
                            }`}
                          >
                            {execution.status}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-blue-600">Progress:</span>
                          <span className="ml-2 text-blue-700">
                            {execution.currentStep + 1} / {execution.totalSteps}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-blue-600">Execution Time:</span>
                          <span className="ml-2 text-blue-700">
                            {execution.executionTime
                              ? `${Math.round(execution.executionTime)}s`
                              : 'Starting...'}
                          </span>
                        </div>
                        <div>
                          <span className="font-medium text-blue-600">Started:</span>
                          <span className="ml-2 text-blue-700">
                            {execution.startTime
                              ? execution.startTime.toLocaleTimeString()
                              : 'Unknown'}
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                }

                return null;
              })()}

              <div className="space-y-4">
                <div>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">Code</h4>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <code className="font-mono text-sm text-gray-800">
                      {selectedWorkflow.pipeline}
                    </code>
                  </div>
                </div>

                {/* Workflow Input Data */}
                <div>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">Input Data</h4>
                  <div className="p-3 bg-gray-50 rounded-lg">
                    <div className="text-sm text-gray-800">
                      {(() => {
                        // Get the actual execution data if available
                        const execution = Array.from(executingWorkflows.values()).find(
                          (exec) => exec.workflowId === selectedWorkflow.name,
                        );

                        if (execution && execution.stepResults.length > 0) {
                          // Show actual input data from the first step
                          const firstStep = execution.stepResults[0];
                          if (firstStep && firstStep.input) {
                            return (
                              <>
                                <div className="mb-2">
                                  <span className="font-medium">Query:</span> "
                                  {firstStep.input.query || 'N/A'}"
                                </div>
                                <div className="mb-2">
                                  <span className="font-medium">Context:</span>{' '}
                                  {firstStep.input.context || 'N/A'}
                                </div>
                                {firstStep.input.agent_type && (
                                  <div className="mb-2">
                                    <span className="font-medium">Agent Type:</span>{' '}
                                    {firstStep.input.agent_type}
                                  </div>
                                )}
                                {firstStep.input.capabilities && (
                                  <div className="mb-2">
                                    <span className="font-medium">Capabilities:</span>
                                    <div className="ml-4 text-gray-600">
                                      {firstStep.input.capabilities.map(
                                        (cap: string, idx: number) => (
                                          <div key={idx}>• {cap}</div>
                                        ),
                                      )}
                                    </div>
                                  </div>
                                )}
                                {firstStep.input.customer_tier && (
                                  <div className="mb-2">
                                    <span className="font-medium">Customer Tier:</span>{' '}
                                    {firstStep.input.customer_tier}
                                  </div>
                                )}
                                {firstStep.input.domain && (
                                  <div className="mb-2">
                                    <span className="font-medium">Domain:</span>{' '}
                                    {firstStep.input.domain}
                                  </div>
                                )}
                                <div className="mb-2">
                                  <span className="font-medium">Timestamp:</span>{' '}
                                  {firstStep.input.timestamp
                                    ? new Date(firstStep.input.timestamp).toLocaleString()
                                    : new Date().toLocaleString()}
                                </div>
                              </>
                            );
                          }
                        }

                        // Fallback: Show the test data that would be used
                        const testData = generateAgentSpecificTestData(
                          parseInt(agentId || '0'),
                          selectedWorkflow.name,
                          customTestQuery,
                        );

                        return (
                          <>
                            <div className="mb-2">
                              <span className="font-medium">Query:</span> "{testData.query}"
                            </div>
                            <div className="mb-2">
                              <span className="font-medium">Context:</span> {testData.context}
                            </div>
                            {testData.agent_type && (
                              <div className="mb-2">
                                <span className="font-medium">Agent Type:</span>{' '}
                                {testData.agent_type}
                              </div>
                            )}
                            {'capabilities' in testData && testData.capabilities && (
                              <div className="mb-2">
                                <span className="font-medium">Capabilities:</span>
                                <div className="ml-4 text-gray-600">
                                  {testData.capabilities.map((cap: string, idx: number) => (
                                    <div key={idx}>• {cap}</div>
                                  ))}
                                </div>
                              </div>
                            )}
                            {'customer_tier' in testData && testData.customer_tier && (
                              <div className="mb-2">
                                <span className="font-medium">Customer Tier:</span>{' '}
                                {testData.customer_tier}
                              </div>
                            )}
                            {'domain' in testData && testData.domain && (
                              <div className="mb-2">
                                <span className="font-medium">Domain:</span> {testData.domain}
                              </div>
                            )}
                            <div className="mb-2">
                              <span className="font-medium">Timestamp:</span>{' '}
                              {testData.timestamp
                                ? new Date(testData.timestamp).toLocaleString()
                                : new Date().toLocaleString()}
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  </div>
                </div>

                <div>
                  <h4 className="mb-2 text-sm font-medium text-gray-700">Steps</h4>
                  <div className="space-y-2">
                    {selectedWorkflow.steps.map((step, index) => (
                      <div key={index} className="flex items-center space-x-3">
                        <div className="flex justify-center items-center w-6 h-6 bg-blue-100 rounded-full">
                          <span className="text-xs font-medium text-blue-600">{index + 1}</span>
                        </div>
                        <span className="font-mono text-sm text-gray-800">{step}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Execution Data (if available) */}
                {(() => {
                  const execution = Array.from(executingWorkflows.values()).find(
                    (exec) => exec.workflowId === selectedWorkflow.name,
                  );

                  if (execution && execution.stepResults.length > 0) {
                    return (
                      <div>
                        <h4 className="mb-2 text-sm font-medium text-gray-700">Execution Data</h4>

                        {/* Real-time Execution Status */}
                        <div className="p-3 mb-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200">
                          <div className="flex justify-between items-center mb-2">
                            <span className="text-sm font-medium text-blue-800">
                              🔄 Real-time Execution
                            </span>
                            <span
                              className={`px-2 py-1 text-xs rounded-full ${
                                execution.status === ExecutionStatus.COMPLETED
                                  ? 'bg-green-100 text-green-800'
                                  : execution.status === ExecutionStatus.RUNNING
                                    ? 'bg-blue-100 text-blue-800'
                                    : execution.status === ExecutionStatus.FAILED
                                      ? 'bg-red-100 text-red-800'
                                      : 'bg-gray-100 text-gray-800'
                              }`}
                            >
                              {execution.status}
                            </span>
                          </div>

                          {/* Execution Metadata */}
                          {execution.execution_metadata &&
                            Object.keys(execution.execution_metadata).length > 0 && (
                              <div className="grid grid-cols-2 gap-2 text-xs">
                                <div>
                                  <span className="font-medium text-blue-600">Runtime:</span>
                                  <span className="ml-1 text-blue-700">
                                    {execution.execution_metadata.execution_time
                                      ? `${execution.execution_metadata.execution_time.toFixed(2)}s`
                                      : 'N/A'}
                                  </span>
                                </div>
                                <div>
                                  <span className="font-medium text-blue-600">Memory:</span>
                                  <span className="ml-1 text-blue-700">
                                    {execution.execution_metadata.memory_usage
                                      ? `${execution.execution_metadata.memory_usage}MB`
                                      : 'N/A'}
                                  </span>
                                </div>
                                <div>
                                  <span className="font-medium text-blue-600">Steps:</span>
                                  <span className="ml-1 text-blue-700">
                                    {execution.execution_metadata.steps_executed || 0}
                                  </span>
                                </div>
                                <div>
                                  <span className="font-medium text-blue-600">Errors:</span>
                                  <span className="ml-1 text-blue-700">
                                    {execution.execution_metadata.errors
                                      ? execution.execution_metadata.errors.length
                                      : 0}
                                  </span>
                                </div>
                              </div>
                            )}
                        </div>

                        {/* Step-by-Step Execution Results */}
                        <div className="space-y-3">
                          {execution.stepResults.map((stepResult, index) => (
                            <div
                              key={index}
                              className="p-3 rounded-lg border border-gray-200 "
                            >
                              {/* Step Header */}
                              <div className="flex justify-between items-center mb-3">
                                <div className="flex items-center space-x-2">
                                  <div className="flex justify-center items-center w-6 h-6 bg-blue-100 rounded-full">
                                    <span className="text-xs font-medium text-blue-600">
                                      {index + 1}
                                    </span>
                                  </div>
                                  <span className="text-sm font-medium text-gray-800">
                                    {stepResult.stepName}
                                  </span>
                                </div>
                                <div className="flex items-center space-x-2">
                                  <span
                                    className={`px-2 py-1 text-xs rounded-full ${
                                      stepResult.status === 'completed'
                                        ? 'bg-green-100 text-green-800'
                                        : stepResult.status === 'running'
                                          ? 'bg-blue-100 text-blue-800'
                                          : stepResult.status === 'failed'
                                            ? 'bg-red-100 text-red-800'
                                            : 'bg-gray-100 text-gray-800'
                                    }`}
                                  >
                                    {stepResult.status}
                                  </span>
                                  {stepResult.executionTime && (
                                    <span className="px-2 py-1 text-xs text-gray-500 bg-gray-100 rounded">
                                      {stepResult.executionTime.toFixed(2)}s
                                    </span>
                                  )}
                                </div>
                              </div>

                              {/* Step Input/Output Data from Dana Runtime */}
                              <div className="space-y-3">
                                {/* Input Data */}
                                {stepResult.input ? (
                                  <div>
                                    <span className="text-xs font-medium text-gray-600">
                                      📥 Input:
                                    </span>
                                    <div className="overflow-y-auto p-2 mt-1 max-h-32 font-mono text-xs text-blue-700 bg-blue-50 rounded border border-blue-200">
                                      {typeof stepResult.input === 'object'
                                        ? JSON.stringify(stepResult.input, null, 2)
                                        : String(stepResult.input)}
                                    </div>
                                  </div>
                                ) : (
                                  <div>
                                    <span className="text-xs font-medium text-gray-600">
                                      📥 Input:
                                    </span>
                                    <div className="p-2 mt-1 font-mono text-xs text-gray-500 bg-gray-50 rounded border border-gray-200">
                                      No input data available for this step
                                    </div>
                                  </div>
                                )}

                                {/* Output Data */}
                                {stepResult.result ? (
                                  <div>
                                    <span className="text-xs font-medium text-gray-600">
                                      📤 Output:
                                    </span>
                                    <div className="overflow-y-auto p-2 mt-1 max-h-32 font-mono text-xs text-green-700 bg-green-50 rounded border border-green-200">
                                      {typeof stepResult.result === 'object'
                                        ? JSON.stringify(stepResult.result, null, 2)
                                        : String(stepResult.result)}
                                    </div>
                                  </div>
                                ) : (
                                  <div>
                                    <span className="text-xs font-medium text-gray-600">
                                      📤 Output:
                                    </span>
                                    <div className="p-2 mt-1 font-mono text-xs text-gray-500 bg-gray-50 rounded border border-gray-200">
                                      No output data available for this step
                                    </div>
                                  </div>
                                )}

                                {/* Real-time Step Status */}
                                <div className="flex justify-between items-center text-xs">
                                  <span className="text-gray-600">Step Status:</span>
                                  <span
                                    className={`px-2 py-1 rounded ${
                                      stepResult.status === 'completed'
                                        ? 'bg-green-100 text-green-700'
                                        : stepResult.status === 'running'
                                          ? 'bg-blue-100 text-blue-700'
                                          : stepResult.status === 'failed'
                                            ? 'bg-red-100 text-red-700'
                                            : 'bg-gray-100 text-gray-600'
                                    }`}
                                  >
                                    {stepResult.status}
                                  </span>
                                </div>

                                {/* Step Execution Time */}
                                {stepResult.executionTime && stepResult.executionTime > 0 && (
                                  <div className="px-2 py-1 text-xs text-gray-500 bg-gray-100 rounded">
                                    ⏱️ Execution time: {stepResult.executionTime.toFixed(3)}s
                                  </div>
                                )}

                                {/* Error Information */}
                                {stepResult.error && (
                                  <div>
                                    <span className="text-xs font-medium text-red-600">
                                      ❌ Error:
                                    </span>
                                    <div className="overflow-y-auto p-2 mt-1 max-h-32 font-mono text-xs text-red-700 bg-red-50 rounded border border-red-200">
                                      {stepResult.error}
                                    </div>
                                  </div>
                                )}

                                {/* Step Timing */}
                                {stepResult.startTime && stepResult.endTime && (
                                  <div className="flex justify-between items-center text-xs text-gray-500">
                                    <span>
                                      Started: {stepResult.startTime.toLocaleTimeString()}
                                    </span>
                                    <span>Ended: {stepResult.endTime.toLocaleTimeString()}</span>
                                  </div>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>

                        {/* Final Result */}
                        {execution.result && (
                          <div className="p-3 mt-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg border border-green-200">
                            <h5 className="mb-2 text-sm font-medium text-green-800">
                              🎯 Final Result
                            </h5>
                            <div className="overflow-y-auto p-2 max-h-32 font-mono text-xs text-green-800 bg-green-100 rounded">
                              {typeof execution.result === 'object'
                                ? JSON.stringify(execution.result, null, 2)
                                : String(execution.result)}
                            </div>
                          </div>
                        )}

                        {/* Execution Errors */}
                        {execution.error && (
                          <div className="p-3 mt-4 bg-gradient-to-r from-red-50 to-pink-50 rounded-lg border border-red-200">
                            <h5 className="mb-2 text-sm font-medium text-red-800">
                              ❌ Execution Error
                            </h5>
                            <div className="overflow-y-auto p-2 max-h-32 font-mono text-xs text-red-800 bg-red-100 rounded">
                              {execution.error}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  }

                  return (
                    <div className="py-8 text-center text-gray-500">
                      <div className="mb-2 text-4xl">🚀</div>
                      <p className="text-sm">No execution data available yet.</p>
                      <p className="mt-1 text-xs text-gray-400">
                        Execute the workflow to see real-time data flow!
                      </p>
                    </div>
                  );
                })()}
              </div>

              <div className="flex justify-end mt-6 space-x-3">
                <button
                  onClick={() => setSelectedWorkflow(null)}
                  className="px-4 py-2 text-sm font-medium text-gray-700 bg-white rounded-md border border-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WorkflowsTab;
