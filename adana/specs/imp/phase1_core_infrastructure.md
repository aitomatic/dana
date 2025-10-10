# Phase 1: Core Infrastructure Implementation Plan

## Overview
Phase 1 focuses on implementing the core framework components that will support the agentic architecture. This includes the base Agent class, Resource system, Workflow composition, LLM abstraction layer, and PromptEngineer framework.

## Week 1: Core Agent and Resource Framework

### Day 1-2: Base Agent Implementation

**File**: `core/agent/base_agent.py`
```python
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
import json
from abc import ABC, abstractmethod

class Agent:
    """Base agent class with state management and conversational interface."""
    
    def __init__(self, agent_type: str, llm_provider: 'LLMProvider', config: Optional[Dict[str, Any]] = None):
        self.agent_type = agent_type
        self.llm_provider = llm_provider
        self.config = config or {}
        self.resources: Dict[str, 'Resource'] = {}
        self.workflows: Dict[str, 'Workflow'] = {}
        self.state = self._initialize_state()
        self.prompt_engineer = None  # Will be set in Week 3
    
    def _initialize_state(self) -> Dict[str, Any]:
        """Initialize the agent state structure."""
        return {
            'conversation_history': [],
            'current_context': {
                'active_task': None,
                'working_directory': None,
                'focus_area': None,
                'priority': 'medium'
            },
            'session_metadata': {
                'session_id': str(uuid.uuid4()),
                'start_time': datetime.now().isoformat(),
                'agent_type': self.agent_type
            },
            'user_preferences': {
                'verbosity': 'normal',
                'auto_save': True
            },
            'task_state': {
                'current_workflow': None,
                'workflow_step': 0,
                'intermediate_results': {},
                'pending_actions': []
            }
        }
    
    def register_resource(self, name: str, resource: 'Resource') -> None:
        """Register a resource with the agent."""
        self.resources[name] = resource
    
    def register_workflow(self, name: str, workflow: 'Workflow') -> None:
        """Register a workflow with the agent."""
        self.workflows[name] = workflow
    
    def query_resource(self, resource_name: str, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query a resource with given method and parameters."""
        if resource_name not in self.resources:
            raise ValueError(f"Resource '{resource_name}' not registered")
        
        resource = self.resources[resource_name]
        return resource.query(method, params)
    
    def execute_workflow(self, workflow_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a workflow with given parameters."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not registered")
        
        workflow = self.workflows[workflow_name]
        return workflow.execute(params, self.state)
    
    def chat(self, user_input: str) -> str:
        """Main conversational interface."""
        # Add user input to conversation history
        self.state['conversation_history'].append({
            'role': 'user',
            'content': user_input,
            'timestamp': datetime.now().isoformat()
        })
        
        # For MVP, simple echo response
        # Will be enhanced in Week 3 with PromptEngineer
        response = f"Agent {self.agent_type} received: {user_input}"
        
        # Add response to conversation history
        self.state['conversation_history'].append({
            'role': 'assistant',
            'content': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return response
```

**File**: `core/agent/state_manager.py`
```python
from typing import Dict, Any, Optional
import json
from datetime import datetime

class StateManager:
    """Manages agent state operations."""
    
    @staticmethod
    def update_state(state: Dict[str, Any], updates: Dict[str, Any], merge: bool = True) -> None:
        """Update agent state with new values."""
        if merge:
            StateManager._deep_merge(state, updates)
        else:
            state.update(updates)
    
    @staticmethod
    def get_state(state: Dict[str, Any], path: str = None) -> Any:
        """Get state value by path (dot notation supported)."""
        if path is None:
            return state
        
        keys = path.split('.')
        value = state
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    @staticmethod
    def _deep_merge(target: Dict, source: Dict) -> None:
        """Deep merge source into target dictionary."""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                StateManager._deep_merge(target[key], value)
            else:
                target[key] = value
```

**File**: `tests/unit/test_agent.py`
```python
import pytest
from unittest.mock import Mock, MagicMock
from core.agent.base import Agent
from core.agent.state_manager import StateManager

class TestAgent:
    def test_agent_initialization(self):
        """Test agent initialization with basic configuration."""
        mock_llm = Mock()
        agent = Agent('test_agent', mock_llm, {'test_config': 'value'})
        
        assert agent.agent_type == 'test_agent'
        assert agent.llm_provider == mock_llm
        assert agent.config['test_config'] == 'value'
        assert 'session_metadata' in agent.state
        assert agent.state['session_metadata']['agent_type'] == 'test_agent'
    
    def test_resource_registration(self):
        """Test resource registration and querying."""
        mock_llm = Mock()
        agent = Agent('test_agent', mock_llm)
        
        mock_resource = Mock()
        mock_resource.query.return_value = {'result': 'test'}
        
        agent.register_resource('test_resource', mock_resource)
        assert 'test_resource' in agent.resources
        
        result = agent.query_resource('test_resource', 'test_method', {'param': 'value'})
        assert result == {'result': 'test'}
        mock_resource.query.assert_called_once_with('test_method', {'param': 'value'})
    
    def test_workflow_registration(self):
        """Test workflow registration and execution."""
        mock_llm = Mock()
        agent = Agent('test_agent', mock_llm)
        
        mock_workflow = Mock()
        mock_workflow.execute.return_value = {'result': 'workflow_test'}
        
        agent.register_workflow('test_workflow', mock_workflow)
        assert 'test_workflow' in agent.workflows
        
        result = agent.execute_workflow('test_workflow', {'param': 'value'})
        assert result == {'result': 'workflow_test'}
        mock_workflow.execute.assert_called_once_with({'param': 'value'}, agent.state)
    
    def test_chat_functionality(self):
        """Test basic chat functionality."""
        mock_llm = Mock()
        agent = Agent('test_agent', mock_llm)
        
        response = agent.chat("Hello, world!")
        
        assert "Hello, world!" in response
        assert len(agent.state['conversation_history']) == 2
        assert agent.state['conversation_history'][0]['role'] == 'user'
        assert agent.state['conversation_history'][1]['role'] == 'assistant'

class TestStateManager:
    def test_state_update(self):
        """Test state update functionality."""
        state = {'test': {'nested': 'value'}}
        updates = {'test': {'new_key': 'new_value'}}
        
        StateManager.update_state(state, updates, merge=True)
        
        assert state['test']['nested'] == 'value'
        assert state['test']['new_key'] == 'new_value'
    
    def test_state_get(self):
        """Test state retrieval by path."""
        state = {'test': {'nested': {'deep': 'value'}}}
        
        result = StateManager.get_state(state, 'test.nested.deep')
        assert result == 'value'
        
        result = StateManager.get_state(state, 'nonexistent.path')
        assert result is None
```

### Day 3-4: Base Resource Implementation

**File**: `core/resource/base_resource.py`
```python
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from abc import ABC, abstractmethod

class MethodInfo:
    """Information about a resource method."""
    
    def __init__(self, name: str, docstring: str, parameters: Dict[str, Any], handler: Callable):
        self.name = name
        self.docstring = docstring
        self.parameters = parameters
        self.handler = handler
        self.last_called = None
        self.call_count = 0

class Resource(ABC):
    """Abstract base class for all resources."""
    
    def __init__(self, name: str, description: str, methods: Dict[str, MethodInfo], config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.description = description
        self.methods = methods
        self.config = config or {}
        
        # Adaptive metadata system
        self.metadata = {
            'adaptive_docstrings': {method: info.docstring for method, info in methods.items()},
            'usage_stats': {method: {'calls': 0, 'successes': 0, 'errors': 0} for method in methods},
            'performance_metrics': {method: {'avg_time': 0, 'last_time': 0} for method in methods}
        }
    
    @abstractmethod
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Primary query method - delegates to specific method."""
        pass
    
    def get_method_docstring(self, method: str) -> str:
        """Get adaptive docstring for method."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        return self.metadata['adaptive_docstrings'].get(method, self.methods[method].docstring)
    
    def _update_performance_metrics(self, method: str, execution_time: float) -> None:
        """Update performance metrics for a method."""
        if method in self.metadata['performance_metrics']:
            metrics = self.metadata['performance_metrics'][method]
            metrics['last_time'] = execution_time
            metrics['avg_time'] = (metrics['avg_time'] + execution_time) / 2
```

**File**: `core/resource/method_info.py`
```python
from typing import Dict, Any, Callable
from dataclasses import dataclass

@dataclass
class MethodInfo:
    """Information about a resource method."""
    name: str
    docstring: str
    parameters: Dict[str, Any]
    handler: Callable
    return_type: str = 'dict'
    is_async: bool = False
    rate_limit: Optional[int] = None
    last_called: Optional[datetime] = None
    call_count: int = 0
```

**File**: `tests/unit/test_resource.py`
```python
import pytest
from unittest.mock import Mock
from core.resource.base_resource import Resource, MethodInfo

class MockResource(Resource):
    """Mock resource for testing."""
    
    def __init__(self, name: str, description: str, methods: Dict[str, MethodInfo], config: Dict[str, Any] = None):
        super().__init__(name, description, methods, config)
    
    def query(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Mock query implementation."""
        if method not in self.methods:
            raise ValueError(f"Method '{method}' not found")
        
        method_info = self.methods[method]
        self.metadata['usage_stats'][method]['calls'] += 1
        
        try:
            result = method_info.handler(params)
            self.metadata['usage_stats'][method]['successes'] += 1
            return {'success': True, 'result': result}
        except Exception as e:
            self.metadata['usage_stats'][method]['errors'] += 1
            return {'success': False, 'error': str(e)}

class TestResource:
    def test_resource_initialization(self):
        """Test resource initialization."""
        methods = {
            'test_method': MethodInfo(
                name='test_method',
                docstring='Test method',
                parameters={'param': {'type': 'string'}},
                handler=lambda params: f"Hello {params.get('param', 'world')}"
            )
        }
        
        resource = MockResource('test_resource', 'Test resource', methods)
        
        assert resource.name == 'test_resource'
        assert resource.description == 'Test resource'
        assert 'test_method' in resource.methods
        assert 'test_method' in resource.metadata['usage_stats']
    
    def test_method_query_success(self):
        """Test successful method query."""
        methods = {
            'test_method': MethodInfo(
                name='test_method',
                docstring='Test method',
                parameters={'param': {'type': 'string'}},
                handler=lambda params: f"Hello {params.get('param', 'world')}"
            )
        }
        
        resource = MockResource('test_resource', 'Test resource', methods)
        result = resource.query('test_method', {'param': 'test'})
        
        assert result['success'] is True
        assert 'Hello test' in result['result']
        assert resource.metadata['usage_stats']['test_method']['calls'] == 1
        assert resource.metadata['usage_stats']['test_method']['successes'] == 1
    
    def test_method_query_error(self):
        """Test method query with error."""
        methods = {
            'error_method': MethodInfo(
                name='error_method',
                docstring='Error method',
                parameters={},
                handler=lambda params: (_ for _ in ()).throw(Exception("Test error"))
            )
        }
        
        resource = MockResource('test_resource', 'Test resource', methods)
        result = resource.query('error_method', {})
        
        assert result['success'] is False
        assert 'Test error' in result['error']
        assert resource.metadata['usage_stats']['error_method']['calls'] == 1
        assert resource.metadata['usage_stats']['error_method']['errors'] == 1
    
    def test_get_method_docstring(self):
        """Test getting method docstring."""
        methods = {
            'test_method': MethodInfo(
                name='test_method',
                docstring='Test method docstring',
                parameters={},
                handler=lambda params: None
            )
        }
        
        resource = MockResource('test_resource', 'Test resource', methods)
        docstring = resource.get_method_docstring('test_method')
        
        assert docstring == 'Test method docstring'
```

### Day 5: Resource Metadata Adapter

**File**: `core/resource/metadata_adapter.py`
```python
from typing import Dict, Any, List
from datetime import datetime

class ResourceMetadataAdapter:
    """Handles adaptive learning for resource metadata."""
    
    def __init__(self, resource: 'Resource'):
        self.resource = resource
        self.feedback_history = []
    
    def adapt_docstrings(self, usage_feedback: Dict[str, Any]) -> None:
        """Adapt resource docstrings based on usage feedback."""
        for method, feedback in usage_feedback.items():
            if method in self.resource.metadata['adaptive_docstrings']:
                # Simple adaptation for MVP
                current_docstring = self.resource.metadata['adaptive_docstrings'][method]
                if 'improvements' in feedback:
                    improved = current_docstring + "\n\nNote: " + "; ".join(feedback['improvements'])
                    self.resource.metadata['adaptive_docstrings'][method] = improved
    
    def optimize_parameters(self, performance_data: Dict[str, Any]) -> None:
        """Optimize resource parameters based on performance data."""
        # MVP implementation - basic parameter optimization
        for method, data in performance_data.items():
            if method in self.resource.methods:
                if data.get('avg_time', 0) > 5.0:  # If average time > 5 seconds
                    # Add rate limiting suggestion
                    if hasattr(self.resource.methods[method], 'rate_limit'):
                        self.resource.methods[method].rate_limit = max(1, int(60 / data['avg_time']))
    
    def discover_capabilities(self, usage_patterns: Dict[str, Any]) -> List[str]:
        """Discover new capabilities based on usage patterns."""
        discovered = []
        for pattern, frequency in usage_patterns.items():
            if frequency > 0.8 and pattern not in self.resource.methods:
                discovered.append(pattern)
        return discovered
```

## Week 2: Workflow Framework and LLM Abstraction

### Day 6-7: Workflow Framework

**File**: `core/workflow/base_workflow.py`
```python
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
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

class Workflow:
    """Workflow composition system for data flow between functions."""
    
    def __init__(self, name: str, description: str = "", steps: Optional[List[WorkflowStep]] = None, config: Optional[Dict[str, Any]] = None):
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
            }
        }
    
    def execute(self, initial_data: Dict[str, Any], agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with data flow through steps."""
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
            for step in self.steps:
                step_result = self._execute_step(step, execution_context)
                execution_context['step_results'][step.name] = step_result
                execution_context['current_data'].update(step_result)
            
            # Update workflow statistics
            total_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(True, total_time)
            
            return {
                'success': True,
                'execution_id': execution_id,
                'final_data': execution_context['current_data'],
                'step_results': execution_context['step_results'],
                'execution_time': total_time
            }
            
        except Exception as e:
            total_time = (datetime.now() - start_time).total_seconds()
            self._update_execution_stats(False, total_time)
            
            return {
                'success': False,
                'execution_id': execution_id,
                'error': str(e),
                'execution_time': total_time,
                'step_results': execution_context['step_results']
            }
    
    def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single workflow step."""
        try:
            # Map input data to function parameters
            function_params = self._map_input_data(step.input_mapping, context['current_data'])
            
            # Execute function
            result = step.function(**function_params)
            
            # Map function output to workflow data
            mapped_result = self._map_output_data(step.output_mapping, result)
            
            return mapped_result
            
        except Exception as e:
            if step.error_handler:
                return step.error_handler(e, context)
            else:
                raise
    
    def _map_input_data(self, input_mapping: Dict[str, str], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map workflow data to function parameters."""
        mapped_params = {}
        for param_name, data_key in input_mapping.items():
            if data_key in current_data:
                mapped_params[param_name] = current_data[data_key]
        return mapped_params
    
    def _map_output_data(self, output_mapping: Dict[str, str], function_result: Any) -> Dict[str, Any]:
        """Map function output to workflow data."""
        mapped_output = {}
        if isinstance(function_result, dict):
            for output_key, result_key in output_mapping.items():
                if result_key in function_result:
                    mapped_output[output_key] = function_result[result_key]
        else:
            mapped_output[output_mapping.get('result', 'output')] = function_result
        return mapped_output
    
    def _update_execution_stats(self, success: bool, execution_time: float) -> None:
        """Update workflow execution statistics."""
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

**File**: `tests/unit/test_workflow.py`
```python
import pytest
from unittest.mock import Mock
from core.workflow.base_workflow import Workflow, WorkflowStep

def test_function(data):
    """Test function for workflow."""
    return {'processed': data['input'] * 2}

def error_function(data):
    """Function that raises an error."""
    raise ValueError("Test error")

def error_handler(error, context):
    """Error handler for workflow steps."""
    return {'error': str(error), 'handled': True}

class TestWorkflow:
    def test_workflow_initialization(self):
        """Test workflow initialization."""
        workflow = Workflow('test_workflow', 'Test workflow description')
        
        assert workflow.name == 'test_workflow'
        assert workflow.description == 'Test workflow description'
        assert workflow.steps == []
        assert 'execution_stats' in workflow.metadata
    
    def test_workflow_execution_success(self):
        """Test successful workflow execution."""
        step = WorkflowStep(
            name='test_step',
            function=test_function,
            input_mapping={'data': 'input'},
            output_mapping={'result': 'processed'}
        )
        
        workflow = Workflow('test_workflow', steps=[step])
        initial_data = {'input': 5}
        agent_state = {}
        
        result = workflow.execute(initial_data, agent_state)
        
        assert result['success'] is True
        assert result['final_data']['result'] == 10
        assert 'test_step' in result['step_results']
        assert workflow.metadata['execution_stats']['total_executions'] == 1
        assert workflow.metadata['execution_stats']['successful_executions'] == 1
    
    def test_workflow_execution_error(self):
        """Test workflow execution with error."""
        step = WorkflowStep(
            name='error_step',
            function=error_function,
            input_mapping={'data': 'input'},
            output_mapping={'result': 'processed'},
            error_handler=error_handler
        )
        
        workflow = Workflow('test_workflow', steps=[step])
        initial_data = {'input': 5}
        agent_state = {}
        
        result = workflow.execute(initial_data, agent_state)
        
        assert result['success'] is False
        assert 'Test error' in result['error']
        assert workflow.metadata['execution_stats']['failed_executions'] == 1
    
    def test_workflow_data_mapping(self):
        """Test data mapping in workflow steps."""
        def mapping_function(input_data, multiplier):
            return {'result': input_data * multiplier}
        
        step = WorkflowStep(
            name='mapping_step',
            function=mapping_function,
            input_mapping={'input_data': 'value', 'multiplier': 'factor'},
            output_mapping={'output': 'result'}
        )
        
        workflow = Workflow('test_workflow', steps=[step])
        initial_data = {'value': 3, 'factor': 4}
        agent_state = {}
        
        result = workflow.execute(initial_data, agent_state)
        
        assert result['success'] is True
        assert result['final_data']['output'] == 12
```

### Day 8-10: LLM Abstraction Layer

**File**: `core/llm/base_provider.py`
```python
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

class LLMProviderType(Enum):
    """Supported LLM provider types."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    OLLAMA = "ollama"

@dataclass
class LLMResponse:
    """Standardized response from LLM providers."""
    content: str
    model: str
    provider: str
    usage: Dict[str, Any]
    metadata: Dict[str, Any]
    response_time: float
    timestamp: datetime

@dataclass
class LLMRequest:
    """Standardized request to LLM providers."""
    messages: List[Dict[str, str]]
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    tools: Optional[List[Dict[str, Any]]] = None
    stream: bool = False

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.provider_type = self._get_provider_type()
        self.client = self._initialize_client()
        self.available_models = self._get_available_models()
        self.default_model = self._get_default_model()
    
    @abstractmethod
    def _get_provider_type(self) -> LLMProviderType:
        """Get the provider type."""
        pass
    
    @abstractmethod
    def _initialize_client(self) -> Any:
        """Initialize the provider client."""
        pass
    
    @abstractmethod
    def _get_available_models(self) -> List[str]:
        """Get list of available models."""
        pass
    
    @abstractmethod
    def _get_default_model(self) -> str:
        """Get the default model for this provider."""
        pass
    
    @abstractmethod
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return len(text.split()) * 1.3  # Rough estimation
```

**File**: `core/llm/anthropic_provider.py`
```python
import anthropic
from typing import Dict, List, Any, Optional
from datetime import datetime
from .base_provider import LLMProvider, LLMProviderType, LLMRequest, LLMResponse

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""
    
    def _get_provider_type(self) -> LLMProviderType:
        return LLMProviderType.ANTHROPIC
    
    def _initialize_client(self) -> anthropic.Anthropic:
        """Initialize Anthropic client."""
        api_key = self.config.get('api_key')
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        return anthropic.Anthropic(api_key=api_key)
    
    def _get_available_models(self) -> List[str]:
        """Get available Anthropic models."""
        return [
            'claude-3-5-sonnet-20241022',
            'claude-3-5-haiku-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307'
        ]
    
    def _get_default_model(self) -> str:
        return 'claude-3-5-sonnet-20241022'
    
    def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic Claude."""
        start_time = datetime.now()
        
        try:
            # Prepare messages for Anthropic
            messages = self._prepare_messages(request.messages)
            
            # Make API call
            response = self.client.messages.create(
                model=request.model or self.default_model,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature or 0.7,
                messages=messages
            )
            
            # Extract content
            content = response.content[0].text if response.content else ""
            
            # Calculate response time
            response_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare usage information
            usage = {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            }
            
            # Prepare metadata
            metadata = {
                'model': response.model,
                'stop_reason': response.stop_reason
            }
            
            return LLMResponse(
                content=content,
                model=response.model,
                provider=self.provider_type.value,
                usage=usage,
                metadata=metadata,
                response_time=response_time,
                timestamp=datetime.now()
            )
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Prepare messages for Anthropic API."""
        # Anthropic uses different message format
        prepared = []
        for msg in messages:
            if msg['role'] == 'system':
                # Anthropic doesn't have system messages, prepend to first user message
                if prepared and prepared[-1]['role'] == 'user':
                    prepared[-1]['content'] = f"System: {msg['content']}\n\nUser: {prepared[-1]['content']}"
                else:
                    prepared.append({'role': 'user', 'content': f"System: {msg['content']}"})
            else:
                prepared.append(msg)
        
        return prepared
```

**File**: `tests/unit/test_llm_providers.py`
```python
import pytest
from unittest.mock import Mock, patch
from core.llm.anthropic_provider import AnthropicProvider
from core.llm.base_provider import LLMRequest, LLMResponse

class TestAnthropicProvider:
    def test_provider_initialization(self):
        """Test Anthropic provider initialization."""
        config = {'api_key': 'test_key'}
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            provider = AnthropicProvider(config)
            
            assert provider.provider_type.value == 'anthropic'
            assert 'claude-3-5-sonnet-20241022' in provider.available_models
            assert provider.default_model == 'claude-3-5-sonnet-20241022'
    
    def test_generate_response(self):
        """Test response generation."""
        config = {'api_key': 'test_key'}
        
        with patch('anthropic.Anthropic') as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.return_value = mock_client
            
            # Mock API response
            mock_response = Mock()
            mock_response.content = [Mock(text="Test response")]
            mock_response.usage.input_tokens = 10
            mock_response.usage.output_tokens = 5
            mock_response.model = "claude-3-5-sonnet-20241022"
            mock_response.stop_reason = "end_turn"
            
            mock_client.messages.create.return_value = mock_response
            
            provider = AnthropicProvider(config)
            
            request = LLMRequest(
                messages=[{'role': 'user', 'content': 'Hello'}],
                model='claude-3-5-sonnet-20241022'
            )
            
            response = provider.generate(request)
            
            assert isinstance(response, LLMResponse)
            assert response.content == "Test response"
            assert response.model == "claude-3-5-sonnet-20241022"
            assert response.provider == "anthropic"
            assert response.usage['input_tokens'] == 10
            assert response.usage['output_tokens'] == 5
```

## Week 3: PromptEngineer Framework

### Day 11-12: Basic PromptEngineer

**File**: `core/prompt_engineer/prompt_engineer.py`
```python
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

class PromptType(Enum):
    """Types of prompts in the system."""
    SYSTEM = "system"
    USER = "user"
    TOOL = "tool"
    WORKFLOW = "workflow"

class PromptEngineer:
    """Handles all prompt creation, combination, and evolution."""
    
    def __init__(self, agent_type: str, config: Optional[Dict[str, Any]] = None):
        self.agent_type = agent_type
        self.config = config or {}
        self.prompt_templates = {}
        self.adaptive_prompts = {}
        self._initialize_default_templates()
    
    def create_system_prompt(self, agent_state: Dict[str, Any], available_resources: Dict[str, Any], available_workflows: Dict[str, Any]) -> str:
        """Create system prompt incorporating state and capabilities."""
        # Get base system template
        base_template = self._get_template('system_base')
        
        # Extract context elements
        context_elements = self._extract_context_elements(agent_state)
        resource_elements = self._extract_resource_elements(available_resources)
        workflow_elements = self._extract_workflow_elements(available_workflows)
        
        # Generate prompt using template
        system_prompt = self._generate_from_template(
            base_template,
            {
                'agent_type': self.agent_type,
                'context': context_elements,
                'resources': self._format_resources(available_resources),
                'workflows': self._format_workflows(available_workflows),
                'user_preferences': agent_state.get('user_preferences', {}),
                'current_task': agent_state.get('current_context', {}).get('active_task')
            }
        )
        
        return system_prompt
    
    def create_user_prompt(self, user_input: str, context: Dict[str, Any]) -> str:
        """Create user prompt with context."""
        base_template = self._get_template('user_base')
        
        relevant_context = self._extract_relevant_context(context, user_input)
        
        user_prompt = self._generate_from_template(
            base_template,
            {
                'user_input': user_input,
                'context': relevant_context,
                'timestamp': datetime.now().isoformat()
            }
        )
        
        return user_prompt
    
    def _initialize_default_templates(self):
        """Initialize default prompt templates."""
        self.prompt_templates = {
            'system_base': """You are a {agent_type} agent specialized in {agent_type} tasks.

## Current Context
{context}

## Available Resources
{resources}

## Available Workflows
{workflows}

## User Preferences
{user_preferences}

## Current Task
{current_task}

## Instructions
- Use the available resources and workflows to complete tasks
- Provide clear, actionable responses
- Follow best practices for {agent_type} tasks
- Ask for clarification when needed""",
            
            'user_base': """User Input: {user_input}

Context: {context}
Timestamp: {timestamp}"""
        }
    
    def _get_template(self, name: str) -> str:
        """Get a template by name."""
        return self.prompt_templates.get(name, "")
    
    def _extract_context_elements(self, agent_state: Dict[str, Any]) -> str:
        """Extract context elements from agent state."""
        context = agent_state.get('current_context', {})
        elements = []
        
        if context.get('active_task'):
            elements.append(f"Active task: {context['active_task']}")
        if context.get('working_directory'):
            elements.append(f"Working directory: {context['working_directory']}")
        if context.get('focus_area'):
            elements.append(f"Focus area: {context['focus_area']}")
        
        return "\n".join(elements) if elements else "No specific context"
    
    def _extract_resource_elements(self, available_resources: Dict[str, Any]) -> str:
        """Extract resource elements."""
        if not available_resources:
            return "No resources available"
        
        resource_list = []
        for name, resource in available_resources.items():
            resource_list.append(f"- {name}: {resource.description}")
        
        return "\n".join(resource_list)
    
    def _extract_workflow_elements(self, available_workflows: Dict[str, Any]) -> str:
        """Extract workflow elements."""
        if not available_workflows:
            return "No workflows available"
        
        workflow_list = []
        for name, workflow in available_workflows.items():
            workflow_list.append(f"- {name}: {workflow.description}")
        
        return "\n".join(workflow_list)
    
    def _format_resources(self, available_resources: Dict[str, Any]) -> str:
        """Format resources for prompt."""
        return self._extract_resource_elements(available_resources)
    
    def _format_workflows(self, available_workflows: Dict[str, Any]) -> str:
        """Format workflows for prompt."""
        return self._extract_workflow_elements(available_workflows)
    
    def _extract_relevant_context(self, context: Dict[str, Any], user_input: str) -> str:
        """Extract relevant context for user input."""
        # Simple implementation - return basic context
        return f"Agent type: {self.agent_type}"
    
    def _generate_from_template(self, template: str, variables: Dict[str, Any]) -> str:
        """Generate prompt from template with variables."""
        try:
            return template.format(**variables)
        except KeyError as e:
            # Handle missing variables gracefully
            return template.replace(f"{{{e.args[0]}}}", f"[MISSING: {e.args[0]}]")
```

**File**: `tests/unit/test_prompt_engineer.py`
```python
import pytest
from core.prompt_engineer.prompt_engineer import PromptEngineer

class TestPromptEngineer:
    def test_initialization(self):
        """Test PromptEngineer initialization."""
        engineer = PromptEngineer('coding', {'test_config': 'value'})
        
        assert engineer.agent_type == 'coding'
        assert engineer.config['test_config'] == 'value'
        assert 'system_base' in engineer.prompt_templates
        assert 'user_base' in engineer.prompt_templates
    
    def test_create_system_prompt(self):
        """Test system prompt creation."""
        engineer = PromptEngineer('coding')
        
        agent_state = {
            'current_context': {
                'active_task': 'debug_code',
                'working_directory': '/home/user/project'
            },
            'user_preferences': {
                'verbosity': 'normal'
            }
        }
        
        resources = {
            'file_system': Mock(description='File system operations'),
            'git': Mock(description='Git operations')
        }
        
        workflows = {
            'debug_code': Mock(description='Debug code workflow')
        }
        
        prompt = engineer.create_system_prompt(agent_state, resources, workflows)
        
        assert 'coding agent' in prompt.lower()
        assert 'debug_code' in prompt
        assert 'File system operations' in prompt
        assert 'Debug code workflow' in prompt
    
    def test_create_user_prompt(self):
        """Test user prompt creation."""
        engineer = PromptEngineer('coding')
        
        user_input = "Help me debug this Python code"
        context = {'test': 'value'}
        
        prompt = engineer.create_user_prompt(user_input, context)
        
        assert 'Help me debug this Python code' in prompt
        assert 'coding' in prompt.lower()
        assert 'Timestamp:' in prompt
```

## Testing Strategy for Phase 1

### Unit Testing Requirements
- **Coverage Target**: >90% for all core components
- **Test Framework**: pytest
- **Mock Strategy**: Extensive use of mocks for external dependencies
- **Test Data**: Comprehensive test fixtures and data

### Integration Testing
- **Agent-Resource Integration**: Test resource registration and querying
- **Agent-Workflow Integration**: Test workflow registration and execution
- **LLM Integration**: Test with mock LLM providers
- **State Management**: Test state updates and persistence

### Performance Testing
- **Response Time**: <100ms for basic operations
- **Memory Usage**: <50MB for basic agent instance
- **Concurrent Operations**: Test multiple agents running simultaneously

## Acceptance Criteria for Phase 1

### Core Agent
- [ ] Agent can be instantiated with LLM provider
- [ ] State management works correctly
- [ ] Resources can be registered and queried
- [ ] Workflows can be registered and executed
- [ ] Basic chat functionality works

### Resource System
- [ ] Resources can be created with methods
- [ ] Method queries work with error handling
- [ ] Metadata tracking functions correctly
- [ ] Adaptive learning system works (basic level)

### Workflow System
- [ ] Workflows can be created with steps
- [ ] Data flows correctly between steps
- [ ] Error handling and retry logic work
- [ ] Workflow statistics are tracked

### LLM Abstraction
- [ ] Anthropic provider works correctly
- [ ] OpenAI provider works correctly (if implemented)
- [ ] Unified interface functions properly
- [ ] Error handling is robust

### PromptEngineer
- [ ] System prompts can be generated
- [ ] User prompts can be generated
- [ ] Template system works correctly
- [ ] Context extraction functions properly

### Testing
- [ ] All unit tests pass with >90% coverage
- [ ] Integration tests pass
- [ ] Performance requirements met
- [ ] Documentation is complete

This completes Phase 1 implementation plan with detailed code examples, test cases, and clear acceptance criteria.
