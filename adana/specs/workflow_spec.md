# Workflow Composition System Specification

## Overview

Workflows are composed functions that pipe execution from one to another, carrying state through data flow. They enable complex multi-step operations by chaining together simpler functions, with each step transforming data and passing it to the next step.

## Core Workflow Class

```python
from typing import Dict, List, Any, Optional, Callable, Union, Tuple
from datetime import datetime
import json
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow."""
    name: str
    function: Callable
    input_mapping: Dict[str, str]  # Maps workflow data to function parameters
    output_mapping: Dict[str, str]  # Maps function output to workflow data
    error_handler: Optional[Callable] = None
    retry_count: int = 0
    timeout: Optional[float] = None
    condition: Optional[Callable] = None  # Optional condition for step execution

class Workflow:
    """
    Workflow composition system for data flow between functions.
    
    Workflows are stateless - they operate on data passed through the pipeline.
    State is maintained in the agent's .state dictionary and passed to each step.
    """
    
    def __init__(self, 
                 name: str, 
                 description: str = "",
                 steps: Optional[List[WorkflowStep]] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the workflow.
        
        Args:
            name: Unique name for the workflow
            description: Human-readable description
            steps: List of workflow steps
            config: Optional configuration dictionary
        """
        self.name = name
        self.description = description
        self.steps = steps or []
        self.config = config or {}
        
        # Workflow metadata
        self.metadata = {
            'created_at': datetime.now().isoformat(),
            'version': '1.0.0',
            'execution_stats': {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'average_execution_time': 0
            },
            'step_performance': {},
            'error_patterns': {},
            'dependencies': []
        }
        
        # Validation
        self._validate_workflow()
    
    def execute(self, 
                initial_data: Dict[str, Any], 
                agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow with data flow through steps.
        
        Args:
            initial_data: Initial data for the workflow
            agent_state: Current agent state
        
        Returns:
            Final workflow result
        """
        start_time = datetime.now()
        execution_id = f"{self.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Initialize execution context
        execution_context = {
            'execution_id': execution_id,
            'start_time': start_time,
            'current_data': initial_data.copy(),
            'step_results': {},
            'errors': [],
            'agent_state': agent_state
        }
        
        try:
            # Execute each step in sequence
            for i, step in enumerate(self.steps):
                step_start = datetime.now()
                
                # Check if step should be executed
                if step.condition and not step.condition(execution_context['current_data']):
                    continue
                
                # Execute step
                step_result = self._execute_step(step, execution_context)
                
                # Update execution context
                execution_context['step_results'][step.name] = step_result
                execution_context['current_data'].update(step_result)
                
                # Update step performance
                step_time = (datetime.now() - step_start).total_seconds()
                self._update_step_performance(step.name, step_time, True)
            
            # Update workflow statistics
            total_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(True, total_time)
            
            return {
                'success': True,
                'execution_id': execution_id,
                'final_data': execution_context['current_data'],
                'step_results': execution_context['step_results'],
                'execution_time': total_time,
                'steps_executed': len(execution_context['step_results'])
            }
            
        except Exception as e:
            # Handle workflow failure
            total_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(False, total_time)
            
            return {
                'success': False,
                'execution_id': execution_id,
                'error': str(e),
                'execution_time': total_time,
                'step_results': execution_context['step_results'],
                'errors': execution_context['errors']
            }
    
    def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            # Map input data to function parameters
            function_params = self._map_input_data(step.input_mapping, context['current_data'])
            
            # Execute function with retry logic
            result = self._execute_with_retry(step, function_params)
            
            # Map function output to workflow data
            mapped_result = self._map_output_data(step.output_mapping, result)
            
            return mapped_result
            
        except Exception as e:
            # Handle step error
            if step.error_handler:
                return step.error_handler(e, context)
            else:
                raise
    
    def _execute_with_retry(self, step: WorkflowStep, params: Dict[str, Any]) -> Any:
        """Execute step function with retry logic."""
        last_error = None
        
        for attempt in range(step.retry_count + 1):
            try:
                if step.timeout:
                    # Execute with timeout
                    return asyncio.run(self._execute_with_timeout(step.function, params, step.timeout))
                else:
                    # Execute normally
                    if asyncio.iscoroutinefunction(step.function):
                        return asyncio.run(step.function(**params))
                    else:
                        return step.function(**params)
                        
            except Exception as e:
                last_error = e
                if attempt < step.retry_count:
                    # Wait before retry
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise last_error
    
    async def _execute_with_timeout(self, func: Callable, params: Dict[str, Any], timeout: float) -> Any:
        """Execute function with timeout."""
        if asyncio.iscoroutinefunction(func):
            return await asyncio.wait_for(func(**params), timeout=timeout)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, lambda: func(**params)),
                timeout=timeout
            )
    
    def _map_input_data(self, input_mapping: Dict[str, str], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map workflow data to function parameters."""
        mapped_params = {}
        
        for param_name, data_key in input_mapping.items():
            if data_key in current_data:
                mapped_params[param_name] = current_data[data_key]
            else:
                # Try to get from nested data
                keys = data_key.split('.')
                value = current_data
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                
                if value is not None:
                    mapped_params[param_name] = value
        
        return mapped_params
    
    def _map_output_data(self, output_mapping: Dict[str, str], function_result: Any) -> Dict[str, Any]:
        """Map function output to workflow data."""
        mapped_output = {}
        
        if isinstance(function_result, dict):
            for output_key, result_key in output_mapping.items():
                if result_key in function_result:
                    mapped_output[output_key] = function_result[result_key]
                else:
                    # Try to get from nested result
                    keys = result_key.split('.')
                    value = function_result
                    for key in keys:
                        if isinstance(value, dict) and key in value:
                            value = value[key]
                        else:
                            value = None
                            break
                    
                    if value is not None:
                        mapped_output[output_key] = value
        else:
            # If result is not a dict, map to default key
            mapped_output[output_mapping.get('result', 'output')] = function_result
        
        return mapped_output
    
    def add_step(self, 
                 name: str,
                 function: Callable,
                 input_mapping: Dict[str, str],
                 output_mapping: Dict[str, str],
                 error_handler: Optional[Callable] = None,
                 retry_count: int = 0,
                 timeout: Optional[float] = None,
                 condition: Optional[Callable] = None) -> None:
        """Add a step to the workflow."""
        step = WorkflowStep(
            name=name,
            function=function,
            input_mapping=input_mapping,
            output_mapping=output_mapping,
            error_handler=error_handler,
            retry_count=retry_count,
            timeout=timeout,
            condition=condition
        )
        
        self.steps.append(step)
        self._validate_workflow()
    
    def remove_step(self, name: str) -> bool:
        """Remove a step from the workflow."""
        for i, step in enumerate(self.steps):
            if step.name == name:
                del self.steps[i]
                return True
        return False
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """Get parameter schema for the workflow."""
        # Analyze first step to determine input parameters
        if not self.steps:
            return {'type': 'object', 'properties': {}}
        
        first_step = self.steps[0]
        schema = {
            'type': 'object',
            'properties': {},
            'required': []
        }
        
        # Map input parameters from first step
        for param_name, data_key in first_step.input_mapping.items():
            schema['properties'][data_key] = {
                'type': 'string',  # Default type
                'description': f"Input for {param_name}"
            }
            schema['required'].append(data_key)
        
        return schema
    
    def _validate_workflow(self) -> None:
        """Validate workflow structure."""
        if not self.steps:
            raise ValueError("Workflow must have at least one step")
        
        # Check for duplicate step names
        step_names = [step.name for step in self.steps]
        if len(step_names) != len(set(step_names)):
            raise ValueError("Duplicate step names found")
        
        # Validate step dependencies
        self._validate_dependencies()
    
    def _validate_dependencies(self) -> None:
        """Validate step dependencies."""
        # This would check if all required data is available
        # for each step based on previous steps' outputs
        pass
    
    def _update_step_performance(self, step_name: str, execution_time: float, success: bool) -> None:
        """Update performance metrics for a step."""
        if step_name not in self.metadata['step_performance']:
            self.metadata['step_performance'][step_name] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_time': 0,
                'average_time': 0
            }
        
        step_stats = self.metadata['step_performance'][step_name]
        step_stats['total_executions'] += 1
        step_stats['total_time'] += execution_time
        step_stats['average_time'] = step_stats['total_time'] / step_stats['total_executions']
        
        if success:
            step_stats['successful_executions'] += 1
        else:
            step_stats['failed_executions'] += 1
    
    def _update_execution_stats(self, success: bool, execution_time: float) -> None:
        """Update overall workflow execution statistics."""
        stats = self.metadata['execution_stats']
        stats['total_executions'] += 1
        
        if success:
            stats['successful_executions'] += 1
        else:
            stats['failed_executions'] += 1
        
        # Update average execution time
        total_time = stats['average_execution_time'] * (stats['total_executions'] - 1)
        stats['average_execution_time'] = (total_time + execution_time) / stats['total_executions']
```

## Concrete Workflow Implementations

### Debug Code Workflow

```python
class DebugCodeWorkflow(Workflow):
    """Workflow for debugging code issues."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        steps = [
            WorkflowStep(
                name='analyze_error',
                function=analyze_error_message,
                input_mapping={'error_message': 'error_message', 'code': 'code'},
                output_mapping={'error_type': 'error_type', 'suggestions': 'suggestions'}
            ),
            WorkflowStep(
                name='search_solutions',
                function=search_error_solutions,
                input_mapping={'error_type': 'error_type', 'language': 'language'},
                output_mapping={'solutions': 'solutions'}
            ),
            WorkflowStep(
                name='test_fix',
                function=test_code_fix,
                input_mapping={'code': 'code', 'suggestions': 'suggestions'},
                output_mapping={'fixed_code': 'fixed_code', 'test_results': 'test_results'}
            )
        ]
        
        super().__init__(
            name='debug_code',
            description='Debug code by analyzing errors and applying fixes',
            steps=steps,
            config=config
        )

def analyze_error_message(error_message: str, code: str) -> Dict[str, Any]:
    """Analyze error message to determine error type and suggestions."""
    # This would use NLP or pattern matching
    return {
        'error_type': 'syntax_error',
        'suggestions': ['Check indentation', 'Verify variable names']
    }

def search_error_solutions(error_type: str, language: str) -> List[Dict[str, Any]]:
    """Search for solutions to the error type."""
    # This would search documentation or knowledge base
    return [
        {'solution': 'Fix indentation', 'confidence': 0.9},
        {'solution': 'Check variable scope', 'confidence': 0.7}
    ]

def test_code_fix(code: str, suggestions: List[str]) -> Dict[str, Any]:
    """Test the code fix and return results."""
    # This would execute the code and check for errors
    return {
        'fixed_code': code,  # Modified code
        'test_results': {'passed': True, 'errors': []}
    }
```

### Refactor Code Workflow

```python
class RefactorCodeWorkflow(Workflow):
    """Workflow for refactoring code."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        steps = [
            WorkflowStep(
                name='analyze_code',
                function=analyze_code_structure,
                input_mapping={'code': 'code', 'refactor_type': 'refactor_type'},
                output_mapping={'analysis': 'analysis', 'refactor_points': 'refactor_points'}
            ),
            WorkflowStep(
                name='generate_refactored_code',
                function=generate_refactored_code,
                input_mapping={'code': 'code', 'refactor_points': 'refactor_points'},
                output_mapping={'refactored_code': 'refactored_code'}
            ),
            WorkflowStep(
                name='validate_refactoring',
                function=validate_refactored_code,
                input_mapping={'original_code': 'code', 'refactored_code': 'refactored_code'},
                output_mapping={'validation_results': 'validation_results'}
            )
        ]
        
        super().__init__(
            name='refactor_code',
            description='Refactor code to improve structure and maintainability',
            steps=steps,
            config=config
        )

def analyze_code_structure(code: str, refactor_type: str) -> Dict[str, Any]:
    """Analyze code structure for refactoring opportunities."""
    return {
        'analysis': 'Code has long functions and duplicate code',
        'refactor_points': ['extract_method', 'remove_duplication']
    }

def generate_refactored_code(code: str, refactor_points: List[str]) -> str:
    """Generate refactored version of the code."""
    # This would use AI or static analysis to refactor
    return code  # Refactored version

def validate_refactored_code(original_code: str, refactored_code: str) -> Dict[str, Any]:
    """Validate that refactored code maintains functionality."""
    return {
        'functionality_preserved': True,
        'improvements': ['Reduced complexity', 'Better readability']
    }
```

### Financial Analysis Workflow

```python
class AnalyzeStockWorkflow(Workflow):
    """Workflow for analyzing stock performance."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        steps = [
            WorkflowStep(
                name='fetch_market_data',
                function=fetch_stock_data,
                input_mapping={'symbol': 'symbol', 'period': 'period'},
                output_mapping={'price_data': 'price_data', 'volume_data': 'volume_data'}
            ),
            WorkflowStep(
                name='calculate_metrics',
                function=calculate_financial_metrics,
                input_mapping={'price_data': 'price_data', 'volume_data': 'volume_data'},
                output_mapping={'metrics': 'metrics'}
            ),
            WorkflowStep(
                name='generate_analysis',
                function=generate_stock_analysis,
                input_mapping={'metrics': 'metrics', 'symbol': 'symbol'},
                output_mapping={'analysis': 'analysis', 'recommendation': 'recommendation'}
            )
        ]
        
        super().__init__(
            name='analyze_stock',
            description='Analyze stock performance and generate recommendations',
            steps=steps,
            config=config
        )

def fetch_stock_data(symbol: str, period: str) -> Dict[str, Any]:
    """Fetch stock market data."""
    # This would call market data API
    return {
        'price_data': [100, 102, 98, 105],
        'volume_data': [1000, 1200, 800, 1500]
    }

def calculate_financial_metrics(price_data: List[float], volume_data: List[int]) -> Dict[str, Any]:
    """Calculate financial metrics from price and volume data."""
    return {
        'average_price': sum(price_data) / len(price_data),
        'price_change': price_data[-1] - price_data[0],
        'volume_trend': 'increasing'
    }

def generate_stock_analysis(metrics: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    """Generate stock analysis and recommendation."""
    return {
        'analysis': f"Stock {symbol} shows positive trend",
        'recommendation': 'BUY'
    }
```

## Workflow Registry

```python
class WorkflowRegistry:
    """Registry for managing workflows."""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.execution_history: List[Dict[str, Any]] = []
    
    def register(self, workflow: Workflow) -> None:
        """Register a workflow."""
        self.workflows[workflow.name] = workflow
    
    def get(self, name: str) -> Optional[Workflow]:
        """Get a workflow by name."""
        return self.workflows.get(name)
    
    def list_workflows(self) -> List[str]:
        """List all registered workflow names."""
        return list(self.workflows.keys())
    
    def execute(self, name: str, params: Dict[str, Any], agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow."""
        if name not in self.workflows:
            raise ValueError(f"Workflow '{name}' not found")
        
        workflow = self.workflows[name]
        result = workflow.execute(params, agent_state)
        
        # Record execution
        self.execution_history.append({
            'workflow_name': name,
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'result': result
        })
        
        return result
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics for all workflows."""
        stats = {}
        
        for name, workflow in self.workflows.items():
            stats[name] = workflow.metadata['execution_stats']
        
        return stats
```

## Workflow Composition Utilities

```python
class WorkflowComposer:
    """Utilities for composing complex workflows."""
    
    @staticmethod
    def create_conditional_workflow(name: str, condition: Callable, 
                                  true_workflow: Workflow, false_workflow: Workflow) -> Workflow:
        """Create a workflow that branches based on condition."""
        def conditional_executor(data: Dict[str, Any], agent_state: Dict[str, Any]) -> Dict[str, Any]:
            if condition(data):
                return true_workflow.execute(data, agent_state)
            else:
                return false_workflow.execute(data, agent_state)
        
        return Workflow(
            name=name,
            description=f"Conditional workflow: {true_workflow.name} or {false_workflow.name}",
            steps=[WorkflowStep(
                name='conditional_execution',
                function=conditional_executor,
                input_mapping={'data': 'data'},
                output_mapping={'result': 'result'}
            )]
        )
    
    @staticmethod
    def create_parallel_workflow(name: str, workflows: List[Workflow]) -> Workflow:
        """Create a workflow that executes multiple workflows in parallel."""
        def parallel_executor(data: Dict[str, Any], agent_state: Dict[str, Any]) -> Dict[str, Any]:
            import asyncio
            
            async def run_parallel():
                tasks = []
                for workflow in workflows:
                    task = asyncio.create_task(
                        asyncio.to_thread(workflow.execute, data, agent_state)
                    )
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                return {'parallel_results': results}
            
            return asyncio.run(run_parallel())
        
        return Workflow(
            name=name,
            description=f"Parallel execution of {len(workflows)} workflows",
            steps=[WorkflowStep(
                name='parallel_execution',
                function=parallel_executor,
                input_mapping={'data': 'data'},
                output_mapping={'results': 'results'}
            )]
        )
    
    @staticmethod
    def create_loop_workflow(name: str, workflow: Workflow, 
                           max_iterations: int = 10) -> Workflow:
        """Create a workflow that loops until condition is met."""
        def loop_executor(data: Dict[str, Any], agent_state: Dict[str, Any]) -> Dict[str, Any]:
            results = []
            
            for i in range(max_iterations):
                result = workflow.execute(data, agent_state)
                results.append(result)
                
                # Check if we should continue looping
                if result.get('success') and result.get('continue_loop', False):
                    data.update(result.get('final_data', {}))
                else:
                    break
            
            return {
                'loop_results': results,
                'iterations': len(results)
            }
        
        return Workflow(
            name=name,
            description=f"Loop workflow: {workflow.name} (max {max_iterations} iterations)",
            steps=[WorkflowStep(
                name='loop_execution',
                function=loop_executor,
                input_mapping={'data': 'data'},
                output_mapping={'results': 'results'}
            )]
        )
```

## Error Handling

```python
class WorkflowError(Exception):
    """Base exception for workflow errors."""
    pass

class StepExecutionError(WorkflowError):
    """Exception raised when a step execution fails."""
    pass

class WorkflowValidationError(WorkflowError):
    """Exception raised when workflow validation fails."""
    pass

class WorkflowTimeoutError(WorkflowError):
    """Exception raised when workflow execution times out."""
    pass

# Default error handlers
def default_error_handler(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Default error handler for workflow steps."""
    return {
        'error': str(error),
        'error_type': type(error).__name__,
        'step_failed': True
    }

def retry_error_handler(error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
    """Error handler that implements retry logic."""
    retry_count = context.get('retry_count', 0)
    max_retries = context.get('max_retries', 3)
    
    if retry_count < max_retries:
        context['retry_count'] = retry_count + 1
        return {'retry': True, 'retry_count': retry_count + 1}
    else:
        return {
            'error': str(error),
            'error_type': type(error).__name__,
            'step_failed': True,
            'max_retries_exceeded': True
        }
```

## Configuration Examples

```python
# Debug Code Workflow Configuration
debug_config = {
    'max_retries': 3,
    'timeout': 30,
    'error_threshold': 0.1,
    'enable_logging': True
}

# Financial Analysis Workflow Configuration
financial_config = {
    'data_sources': ['yahoo', 'alpha_vantage'],
    'analysis_period': '1y',
    'confidence_threshold': 0.7,
    'enable_backtesting': True
}

# Workflow Registry Configuration
registry_config = {
    'max_execution_history': 1000,
    'enable_performance_tracking': True,
    'cleanup_interval': 3600  # 1 hour
}
```
