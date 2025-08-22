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
           description: `${steps.join(' → ')}`,
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
                     <div key={index} className="p-6 bg-gradient-to-br from-white to-gray-50 rounded-xl border border-gray-200 shadow-sm hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1">
             <div className="flex justify-between items-start mb-6">
               <div>
                 <h4 className="text-xl font-bold text-gray-900 mb-2">{workflow.name}</h4>
                 {workflow.description && (
                   <p className="text-sm text-gray-600 bg-white px-3 py-2 rounded-lg border border-gray-100 inline-block">
                     {workflow.description}
                   </p>
                 )}
               </div>
               <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-semibold bg-gradient-to-r from-blue-500 to-blue-600 text-white shadow-sm">
                 Workflow
               </span>
             </div>

                         {/* Enhanced Pipeline Visualization */}
             <div className="mb-6">
               <h5 className="text-sm font-medium text-gray-700 mb-4 flex items-center">
                 <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                   <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                 </svg>
                 Workflow Steps
               </h5>
               <div className="relative">
                 {workflow.steps.map((step, stepIndex) => (
                   <div key={stepIndex} className="relative">
                     {/* Step Card */}
                     <div className="flex items-center mb-4">
                       {/* Enhanced Step Number Circle */}
                       <div className="flex-shrink-0 w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-full flex items-center justify-center mr-5 z-10 relative shadow-lg">
                         <span className="text-sm font-bold text-white">{stepIndex + 1}</span>
                         {/* Glow effect */}
                         <div className="absolute inset-0 bg-blue-400 rounded-full opacity-20 animate-pulse"></div>
                       </div>
                       
                       {/* Enhanced Step Content */}
                       <div className="flex-1 bg-gradient-to-r from-gray-50 to-white border border-gray-200 rounded-xl px-5 py-4 shadow-sm hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
                         <div className="flex items-center justify-between">
                           <span className="text-sm font-semibold text-gray-800 font-mono">{step}</span>
                           {/* Step type indicator */}
                           <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                             stepIndex === 0 ? 'bg-green-100 text-green-800' :
                             stepIndex === workflow.steps.length - 1 ? 'bg-purple-100 text-purple-800' :
                             'bg-blue-100 text-blue-800'
                           }`}>
                             {stepIndex === 0 ? 'Input' : 
                              stepIndex === workflow.steps.length - 1 ? 'Output' : 'Process'}
                           </span>
                         </div>
                         {/* Step description placeholder */}
                         <p className="text-xs text-gray-500 mt-1">
                           {stepIndex === 0 ? 'Initial data processing' :
                            stepIndex === workflow.steps.length - 1 ? 'Final result generation' :
                            'Data transformation step'}
                         </p>
                       </div>
                     </div>
                     
                     {/* Curved Connector Line */}
                     {stepIndex < workflow.steps.length - 1 && (
                       <div className="absolute left-5 top-10 w-0.5 h-8 bg-gradient-to-b from-blue-400 to-blue-200"></div>
                     )}
                   </div>
                 ))}
                 
                 {/* Workflow Flow Indicator */}
                 <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-600 via-blue-400 to-blue-200 opacity-30"></div>
               </div>
             </div>

            {/* Raw Pipeline */}
            <div className="p-3 bg-gray-50 rounded-md">
                           <h5 className="mb-2 text-xs font-medium tracking-wide text-gray-500 uppercase">
               Code
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
