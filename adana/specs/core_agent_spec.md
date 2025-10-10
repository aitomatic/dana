# Core Agent Class Specification

## Overview

The core Agent class is the foundation of the agentic architecture, providing state management, conversational loop, and coordination between Resources and Workflows.

## Class Definition

```python
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
import uuid
import json
from adana.common.llm import LLM
from adana.common.llm.types import LLMMessage

class Agent:
    """
    Core agent class providing state management and conversational interface.
    
    The agent maintains all state in a .state dictionary and coordinates
    between Resources and Workflows through a conversational loop pattern.
    Uses the existing adana/common/llm implementation for LLM interactions.
    """
    
    def __init__(self, 
                 agent_type: str, 
                 llm_provider: str | None = None,
                 model: str | None = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent.
        
        Args:
            agent_type: Type of agent (e.g., 'coding', 'financial_analyst')
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai')
            model: Model name to use (defaults to provider's default)
            config: Optional configuration dictionary
        """
        self.agent_type = agent_type
        self.config = config or {}
        
        # Initialize LLM using existing implementation
        self.llm = LLM(provider=llm_provider, model=model)
        
        # Initialize core components
        self.prompt_engineer = PromptEngineer(agent_type, self.config.get('prompt_config', {}))
        
        # Resource and workflow registries
        self.resources: Dict[str, 'Resource'] = {}
        self.workflows: Dict[str, 'Workflow'] = {}
        
        # Initialize state
        self.state = self._initialize_state()
        
        # Execution tracking
        self.execution_history = []
        self.performance_metrics = {}
```

## State Management

### State Structure

```python
def _initialize_state(self) -> Dict[str, Any]:
    """Initialize the agent state structure."""
    return {
        'conversation_history': [],
        'current_context': {
            'active_task': None,
            'working_directory': None,
            'focus_area': None,
            'priority': 'medium',
            'constraints': []
        },
        'session_metadata': {
            'session_id': str(uuid.uuid4()),
            'start_time': datetime.now().isoformat(),
            'agent_type': self.agent_type,
            'agent_version': self.config.get('version', '1.0.0'),
            'user_id': self.config.get('user_id'),
            'environment': self.config.get('environment', 'development')
        },
        'user_preferences': {
            'verbosity': 'normal',
            'auto_save': True,
            'confirmation_required': False,
            'language': 'en',
            'timezone': 'UTC'
        },
        'task_state': {
            'current_workflow': None,
            'workflow_step': 0,
            'intermediate_results': {},
            'pending_actions': [],
            'completed_actions': [],
            'error_history': []
        },
        'resource_usage': {
            'resource_calls': {},
            'resource_errors': {},
            'resource_performance': {}
        },
        'workflow_execution': {
            'active_workflows': [],
            'completed_workflows': [],
            'workflow_errors': {},
            'workflow_performance': {}
        }
    }
```

### State Management Methods

```python
def update_state(self, updates: Dict[str, Any], merge: bool = True) -> None:
    """
    Update agent state with new values.
    
    Args:
        updates: Dictionary of state updates
        merge: If True, merge with existing state; if False, replace
    """
    if merge:
        self._deep_merge(self.state, updates)
    else:
        self.state.update(updates)
    
    # Trigger state change hooks
    self._on_state_change(updates)

def get_state(self, path: str = None) -> Any:
    """
    Get state value by path (dot notation supported).
    
    Args:
        path: Dot-separated path to state value (e.g., 'current_context.active_task')
    
    Returns:
        State value or None if path not found
    """
    if path is None:
        return self.state
    
    keys = path.split('.')
    value = self.state
    
    for key in keys:
        if isinstance(value, dict) and key in value:
            value = value[key]
        else:
            return None
    
    return value

def reset_state(self, preserve_session: bool = True) -> None:
    """
    Reset agent state.
    
    Args:
        preserve_session: If True, preserve session metadata
    """
    if preserve_session:
        session_meta = self.state['session_metadata']
        self.state = self._initialize_state()
        self.state['session_metadata'] = session_meta
    else:
        self.state = self._initialize_state()
```

## Resource Management

```python
def register_resource(self, name: str, resource: 'Resource') -> None:
    """
    Register a resource with the agent.
    
    Args:
        name: Name to register the resource under
        resource: Resource instance
    """
    if not isinstance(resource, Resource):
        raise TypeError(f"Expected Resource instance, got {type(resource)}")
    
    self.resources[name] = resource
    self.state['resource_usage']['resource_calls'][name] = 0
    self.state['resource_usage']['resource_errors'][name] = []
    self.state['resource_usage']['resource_performance'][name] = {}

def query_resource(self, 
                  resource_name: str, 
                  method: str, 
                  params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Query a resource with given method and parameters.
    
    Args:
        resource_name: Name of the registered resource
        method: Method to call on the resource
        params: Parameters for the method
    
    Returns:
        Resource response dictionary
    """
    if resource_name not in self.resources:
        raise ValueError(f"Resource '{resource_name}' not registered")
    
    resource = self.resources[resource_name]
    start_time = datetime.now()
    
    try:
        # Update usage tracking
        self.state['resource_usage']['resource_calls'][resource_name] += 1
        
        # Execute resource query
        result = resource.query(method, params)
        
        # Update performance metrics
        execution_time = (datetime.now() - start_time).total_seconds()
        self.state['resource_usage']['resource_performance'][resource_name][method] = {
            'last_execution_time': execution_time,
            'total_calls': self.state['resource_usage']['resource_calls'][resource_name],
            'success_rate': self._calculate_success_rate(resource_name)
        }
        
        return result
        
    except Exception as e:
        # Track errors
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'method': method,
            'params': params,
            'error': str(e)
        }
        self.state['resource_usage']['resource_errors'][resource_name].append(error_info)
        raise
```

## Workflow Management

```python
def register_workflow(self, name: str, workflow: 'Workflow') -> None:
    """
    Register a workflow with the agent.
    
    Args:
        name: Name to register the workflow under
        workflow: Workflow instance
    """
    if not isinstance(workflow, Workflow):
        raise TypeError(f"Expected Workflow instance, got {type(workflow)}")
    
    self.workflows[name] = workflow
    self.state['workflow_execution']['workflow_errors'][name] = []
    self.state['workflow_execution']['workflow_performance'][name] = {}

def execute_workflow(self, 
                    workflow_name: str, 
                    params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a workflow with given parameters.
    
    Args:
        workflow_name: Name of the registered workflow
        params: Parameters for the workflow
    
    Returns:
        Workflow execution result
    """
    if workflow_name not in self.workflows:
        raise ValueError(f"Workflow '{workflow_name}' not registered")
    
    workflow = self.workflows[workflow_name]
    start_time = datetime.now()
    
    try:
        # Update task state
        self.state['task_state']['current_workflow'] = workflow_name
        self.state['task_state']['workflow_step'] = 0
        self.state['workflow_execution']['active_workflows'].append(workflow_name)
        
        # Execute workflow
        result = workflow.execute(params, self.state)
        
        # Update execution tracking
        execution_time = (datetime.now() - start_time).total_seconds()
        self.state['workflow_execution']['completed_workflows'].append({
            'name': workflow_name,
            'start_time': start_time.isoformat(),
            'execution_time': execution_time,
            'params': params,
            'result': result
        })
        
        # Update performance metrics
        self.state['workflow_execution']['workflow_performance'][workflow_name] = {
            'last_execution_time': execution_time,
            'total_executions': len(self.state['workflow_execution']['completed_workflows']),
            'success_rate': self._calculate_workflow_success_rate(workflow_name)
        }
        
        return result
        
    except Exception as e:
        # Track errors
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'params': params,
            'error': str(e)
        }
        self.state['workflow_execution']['workflow_errors'][workflow_name].append(error_info)
        raise
    finally:
        # Clean up active workflow
        if workflow_name in self.state['workflow_execution']['active_workflows']:
            self.state['workflow_execution']['active_workflows'].remove(workflow_name)
```

## Prompt Management

### Prompt Storage Convention

Prompts are maintained separately in the same file as the agent source file, as a class with the same name as the agent with "Prompts" appended (e.g., "FinanceAgentPrompts"). This class should derive from a base `BasePrompts` class.

```python
# Example: adana/lib/agents/finance_agent.py
from adana.frameworks.prteng import BaseAgentPrompts

class FinanceAgentPrompts(BaseAgentPrompts):
    """Prompts for the Finance Agent."""
    
    @property
    def system_prompt(self) -> str:
        """Main system prompt for the Finance Agent."""
        return """
You are a Financial Analyst agent following the OODA loop pattern internally:

OBSERVE: Analyze financial data, market conditions, and user requests
ORIENT: Consider available financial resources, market data, and analysis tools
DECIDE: Choose the best analytical approach or recommendation
ACT: Execute analysis, generate reports, or provide recommendations

SPECIALIZED CAPABILITIES:
- Financial data analysis and interpretation
- Market trend analysis and forecasting
- Risk assessment and portfolio optimization
- Financial report generation and presentation

RESOURCES:
{resources}

AGENT COMMUNICATION:
You can communicate with other specialized agents:
- interact_with_agent(agent_id, message) - Send a message to another agent
- discover_agents() - Find available agents
- find_agent_by_capability(capability) - Find agents with specific skills

AVAILABLE AGENTS:
{agents}

Current state: {state}
Be precise and data-driven in your financial analysis.
"""

    @property
    def agent_communication_prompt(self) -> str:
        """Prompt for agent-to-agent communication."""
        return """
You are receiving a message from another agent (ID: {from_agent_id}).

Please respond as a Financial Analyst agent. Be helpful and collaborative.
Your response will be sent back to the other agent.
"""

    def resource_call_prompt(self, resource_name: str) -> str:
        """Prompt for calling specific resources."""
        return f"""
You are about to call the {resource_name} resource.
Please provide the necessary parameters for this resource call.
"""

class FinanceAgent(Agent):
    """Financial Analyst Agent implementation."""
    
    def __init__(self, **kwargs):
        super().__init__(agent_type="financial_analyst", **kwargs)
        self.prompts = FinanceAgentPrompts()
    
    def _create_ooda_system_prompt(self) -> str:
        """Create OODA system prompt using the prompts class."""
        return self.prompts.system_prompt.format(
            resources=self._format_resources(),
            agents=self._format_available_agents(),
            state=self.state
        )
```

### Base Prompts Class

```python
# adana/core/agent/base_prompts.py
from abc import ABC, abstractmethod
from typing import Dict, Any

class BasePrompts(ABC):
    """Base class for agent prompts with common functionality."""
    
    @property
    @abstractmethod
    def system_prompt(self) -> str:
        """Main system prompt for the agent."""
        pass
    
    @property
    def agent_communication_prompt(self) -> str:
        """Default agent-to-agent communication prompt."""
        return """
You are receiving a message from another agent (ID: {from_agent_id}).

Please respond as if you are having a conversation with another AI agent. 
Be helpful and collaborative. Your response will be sent back to the other agent.
"""
    
    def resource_call_prompt(self, resource_name: str) -> str:
        """Default prompt for calling resources."""
        return f"""
You are about to call the {resource_name} resource.
Please provide the necessary parameters for this resource call.
"""
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """Format a prompt template with provided variables."""
        return template.format(**kwargs)
```

## Conversational Loop (OODA Pattern)

```python
async def chat(self, user_input: str) -> str:
    """
    Main conversational interface following OODA loop pattern.
    
    OODA Loop: Observe → Orient → Decide → Act
    
    Args:
        user_input: User's input message
    
    Returns:
        Agent's response
    """
    # OBSERVE: Add user input to timeline
    self.timeline.add_entry(
        TimelineEntry(timestamp=datetime.now(), entry_type="user_input", content=user_input)
    )
    
    # ORIENT + DECIDE + ACT: Generate response with resource/agent calls
    system_prompt = self._create_ooda_system_prompt()
    messages = [LLMMessage(role="system", content=system_prompt)] + self.timeline.get_context()
    
    response = await self.llm.chat(messages)
    
    # Add response to timeline
    self.timeline.add_entry(
        TimelineEntry(timestamp=datetime.now(), entry_type="my_response", content=response)
    )
    
    # Handle resource/agent execution loop (ACT phase)
    while self._has_calls(response):
        call_results = await self._execute_calls(response)
        
        # Add results to timeline
        for call_result in call_results:
            self.timeline.add_entry(
                TimelineEntry(
                    timestamp=datetime.now(),
                    entry_type="resource_call" if call_result['type'] == 'resource' else "agent_interaction",
                    content=call_result['result'],
                    correspondent=call_result.get('target')
                )
            )
        
        # Continue OODA loop with results
        messages = [LLMMessage(role="system", content=system_prompt)] + self.timeline.get_context()
        response = await self.llm.chat(messages)
        
        # Add response to timeline
        self.timeline.add_entry(
            TimelineEntry(timestamp=datetime.now(), entry_type="my_response", content=response)
        )
    
    return response

def _create_ooda_system_prompt(self) -> str:
    """Create system prompt that guides LLM to follow OODA thinking."""
    return f"""
You are an AI agent following the OODA loop pattern internally:

OBSERVE: Analyze the user input and current context
ORIENT: Consider available resources, capabilities, and constraints  
DECIDE: Choose the best course of action
ACT: Execute your decision

For each response, think through these phases internally:
1. What am I observing? (user input, context, state)
2. How should I orient myself? (what resources/agents are available?)
3. What should I decide to do? (what's the best action?)
4. How will I act? (execute the decision)

RESOURCES:
{self._format_resources()}

AGENT COMMUNICATION:
You can communicate with other specialized agents:
- interact_with_agent(agent_id, message) - Send a message to another agent
- discover_agents() - Find available agents
- find_agent_by_capability(capability) - Find agents with specific skills

AVAILABLE AGENTS:
{self._format_available_agents()}

Current state: {self.state}
Be concise and direct in your responses.
"""

def _execute_calls(self, response: str) -> List[Dict[str, Any]]:
    """
    Execute resource calls and agent interactions from LLM response.
    
    Args:
        response: LLM response containing calls
    
    Returns:
        List of call execution results
    """
    calls = self._extract_calls(response)
    results = []
    
    for call in calls:
        try:
            if call['type'] == 'resource':
                result = await self.call_resource(call['name'], call['args'])
            elif call['type'] == 'agent':
                result = await self.interact_with_agent(call['agent_id'], call['message'])
            else:
                result = {'error': f"Unknown call type: {call['type']}"}
            
            results.append({
                'type': call['type'],
                'target': call.get('name') or call.get('agent_id'),
                'result': result,
                'success': True
            })
            
        except Exception as e:
            results.append({
                'type': call['type'],
                'target': call.get('name') or call.get('agent_id'),
                'result': {'error': str(e)},
                'success': False
            })
    
    return results
```

## Utility Methods

```python
def _add_to_conversation_history(self, role: str, content: str) -> None:
    """Add message to conversation history."""
    # Add to agent state
    self.state['conversation_history'].append({
        'role': role,
        'content': content,
        'timestamp': datetime.now().isoformat()
    })
    
    # Also add to LLM conversation history if not already there
    llm_history = self.llm.get_conversation_history()
    if not llm_history or llm_history[-1].content != content:
        # Message not in LLM history, add it
        if role == 'user':
            # This will be handled by the chat method
            pass
        elif role == 'assistant':
            # Add to LLM history
            self.llm.conversation_history.append(LLMMessage(role=role, content=content))

def _get_available_tools(self) -> List[Dict[str, Any]]:
    """Get list of available tools for LLM."""
    tools = []
    
    # Add resource tools
    for name, resource in self.resources.items():
        for method_name, method_info in resource.methods.items():
            tools.append({
                'type': 'function',
                'function': {
                    'name': f"{name}_{method_name}",
                    'description': method_info.docstring,
                    'parameters': method_info.parameters
                }
            })
    
    # Add workflow tools
    for name, workflow in self.workflows.items():
        tools.append({
            'type': 'function',
            'function': {
                'name': name,
                'description': workflow.description,
                'parameters': workflow.get_parameters_schema()
            }
        })
    
    return tools

def _deep_merge(self, target: Dict, source: Dict) -> None:
    """Deep merge source into target dictionary."""
    for key, value in source.items():
        if key in target and isinstance(target[key], dict) and isinstance(value, dict):
            self._deep_merge(target[key], value)
        else:
            target[key] = value

def _on_state_change(self, changes: Dict[str, Any]) -> None:
    """Handle state change events."""
    # Override in subclasses for custom behavior
    pass

def _calculate_success_rate(self, resource_name: str) -> float:
    """Calculate success rate for a resource."""
    errors = len(self.state['resource_usage']['resource_errors'][resource_name])
    calls = self.state['resource_usage']['resource_calls'][resource_name]
    return (calls - errors) / calls if calls > 0 else 1.0

def _calculate_workflow_success_rate(self, workflow_name: str) -> float:
    """Calculate success rate for a workflow."""
    errors = len(self.state['workflow_execution']['workflow_errors'][workflow_name])
    completed = len(self.state['workflow_execution']['completed_workflows'])
    return (completed - errors) / completed if completed > 0 else 1.0
```

## Configuration

```python
# Example configuration
config = {
    'version': '1.0.0',
    'user_id': 'user123',
    'environment': 'production',
    'prompt_config': {
        'max_context_length': 4000,
        'temperature': 0.7,
        'system_prompt_template': 'custom_template'
    },
    'state_persistence': {
        'enabled': True,
        'file_path': '/tmp/agent_state.json'
    }
}

# LLM configuration is handled by adana/config.json and environment variables
# Example usage:
agent = Agent(
    agent_type='coding',
    llm_provider='anthropic',  # Uses existing LLM provider system
    model='claude-3-sonnet',   # Optional, defaults to provider default
    config=config
)

# Provider switching
agent.llm.switch_provider('openai', model='gpt-4')

# Check available providers
from adana.common.llm import LLM
available_providers = LLM.get_available_providers()
is_available = LLM.is_provider_available('anthropic')
models = LLM.get_provider_models('openai')
```

## Error Handling

```python
class AgentError(Exception):
    """Base exception for agent errors."""
    pass

class ResourceError(AgentError):
    """Exception raised when resource operations fail."""
    pass

class WorkflowError(AgentError):
    """Exception raised when workflow operations fail."""
    pass

class StateError(AgentError):
    """Exception raised when state operations fail."""
    pass
```

## Performance Monitoring

```python
def get_performance_metrics(self) -> Dict[str, Any]:
    """Get comprehensive performance metrics."""
    return {
        'session_duration': self._get_session_duration(),
        'conversation_length': len(self.state['conversation_history']),
        'resource_usage': self.state['resource_usage'],
        'workflow_execution': self.state['workflow_execution'],
        'error_rates': self._calculate_error_rates(),
        'average_response_time': self._calculate_average_response_time()
    }

def export_state(self, file_path: str) -> None:
    """Export agent state to file."""
    with open(file_path, 'w') as f:
        json.dump(self.state, f, indent=2, default=str)

def import_state(self, file_path: str) -> None:
    """Import agent state from file."""
    with open(file_path, 'r') as f:
        self.state = json.load(f)
```
