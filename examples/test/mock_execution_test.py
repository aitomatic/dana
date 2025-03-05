"""
Example demonstrating a simple workflow-plan-reasoning execution with a mock LLM.
This tests our refactored code without external dependencies.
"""

import asyncio
import logging
from typing import Dict, Any

from dxa.execution import WorkflowFactory, WorkflowExecutor, PlanExecutor, ReasoningExecutor
from dxa.execution import ExecutionContext
from dxa.execution.execution_types import Objective
from dxa.common.utils.logging import DXA_LOGGER

# Mock LLM implementation
class MockLLM:
    """A mock LLM that returns predefined responses."""
    
    async def initialize(self):
        """Initialize the LLM."""
        pass
        
    async def cleanup(self):
        """Clean up resources."""
        pass
        
    async def query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Return a mock response."""
        prompt = request.get("prompt", "")
        return {
            "content": f"Response to: {prompt}\nThis is a mock response for testing."
        }

async def main():
    """Run the test with our refactored code."""
    # Set up logging
    DXA_LOGGER.configure(level=DXA_LOGGER.DEBUG)
    
    # Create a mock LLM
    llm = MockLLM()
    await llm.initialize()
    
    # Create an execution context with the mock LLM
    context = ExecutionContext(
        reasoning_llm=llm,
        planning_llm=llm,
        workflow_llm=llm
    )
    
    # Create a simple workflow
    objective = "Test the refactored W-P-R stack"
    workflow = WorkflowFactory.create_minimal_workflow(Objective(objective))
    
    print(f"Created workflow with {len(workflow.nodes)} nodes")
    
    # Set up executors
    reasoning_executor = ReasoningExecutor()
    plan_executor = PlanExecutor(reasoning_executor=reasoning_executor)
    workflow_executor = WorkflowExecutor(plan_executor=plan_executor)
    
    # Execute workflow
    print("\nExecuting workflow...\n")
    try:
        signals = await workflow_executor.execute_workflow(workflow, context)
        
        # Print results
        print("\nWorkflow execution complete. Results:")
        for signal in signals:
            if hasattr(signal, 'content') and 'result' in signal.content:
                print(f"\n--- {signal.content.get('node', 'Unknown')} ---")
                result = signal.content['result']
                if isinstance(result, dict) and 'content' in result:
                    print(result['content'])
                else:
                    print(result)
        
        print("\nExecution completed successfully!")
        return True
    except Exception as e:
        print(f"\nError during execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await llm.cleanup()

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)