import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { apiService } from '@/lib/api';

interface WorkflowDefinition {
  name: string;
  steps: string[];
  pipeline: string;
  description?: string;
}

interface ParsedWorkflow {
  workflow_definitions: WorkflowDefinition[];
  function_definitions: Record<string, unknown>[];
  has_pipeline_workflows: boolean;
  total_workflows: number;
}

const WorkflowsTab: React.FC = () => {
  const { agent_id: agentId } = useParams<{ agent_id: string }>();
  const [workflows, setWorkflows] = useState<ParsedWorkflow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

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

      // Parse workflow definitions
      if (line.includes(' = ') && line.includes('|')) {
        const [name, pipeline] = line.split(' = ', 2);
        const steps = pipeline.split('|').map((step) => step.trim());

        workflow_definitions.push({
          name: name.trim(),
          steps,
          pipeline: pipeline.trim(),
          description: `Pipeline: ${steps.join(' → ')}`,
        });
      }
    }

    return {
      workflow_definitions,
      function_definitions: [],
      has_pipeline_workflows: workflow_definitions.length > 0,
      total_workflows: workflow_definitions.length,
    };
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
              <h3 className="text-sm font-medium text-red-800">Error Loading Workflows</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!workflows || workflows.total_workflows === 0) {
    return (
      <div className="p-8">
        <div className="text-center">
          <svg
            className="mx-auto w-12 h-12 text-gray-400"
            stroke="currentColor"
            fill="none"
            viewBox="0 0 48 48"
          >
            <path
              d="M34 40h10v-4a6 6 0 00-10.712-3.714M34 40H14m20 0v-4a9.971 9.971 0 00-.712-3.714M14 40H4v-4a6 6 0 0110.713-3.714M14 40v-4c0-1.313.253-2.566.713-3.714m0 0A9.971 9.971 0 0124 24c4.21 0 7.813 2.602 9.288 6.286"
              strokeWidth={2}
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No workflows found</h3>
          <p className="mt-1 text-sm text-gray-500">
            This agent doesn't have any workflows defined in workflows.na
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="px-6 pb-6">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Agent Workflows</h2>
        <p className="mt-1 text-sm text-gray-600">
          {workflows.total_workflows} workflow{workflows.total_workflows !== 1 ? 's' : ''} defined
        </p>
      </div>

      {/* Workflows Section */}
      <div className="space-y-6">
        <h3 className="text-base font-medium text-gray-800">Workflow Definitions</h3>
        {workflows.workflow_definitions.map((workflow, index) => (
          <div key={index} className="p-6 bg-white rounded-lg border border-gray-200 shadow-sm">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h4 className="text-lg font-semibold text-gray-900">{workflow.name}</h4>
                {workflow.description && (
                  <p className="mt-1 text-sm text-gray-600">{workflow.description}</p>
                )}
              </div>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                Pipeline
              </span>
            </div>

            {/* Pipeline Visualization */}
            <div className="mb-4">
              <div className="flex overflow-x-auto items-center pb-2 space-x-3">
                {workflow.steps.map((step, stepIndex) => (
                  <React.Fragment key={stepIndex}>
                    <div className="flex-shrink-0 px-4 py-2 min-w-max bg-blue-50 rounded-lg border border-blue-200">
                      <span className="text-sm font-medium text-blue-800">{step}</span>
                    </div>
                    {stepIndex < workflow.steps.length - 1 && (
                      <div className="flex-shrink-0 text-gray-400">
                        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      </div>
                    )}
                  </React.Fragment>
                ))}
              </div>
            </div>

            {/* Raw Pipeline */}
            <div className="p-3 bg-gray-50 rounded-md">
              <h5 className="mb-2 text-xs font-medium tracking-wide text-gray-500 uppercase">
                Pipeline Code
              </h5>
              <code className="font-mono text-sm text-gray-800 break-all">
                {workflow.name} = {workflow.pipeline}
              </code>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default WorkflowsTab;
