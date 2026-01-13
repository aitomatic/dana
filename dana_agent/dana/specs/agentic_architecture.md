# Agentic Architecture Design Specifications

## Overview

This document outlines the design specifications for a flexible, LLM-agnostic agentic architecture that uses Resources, Workflows, and a PromptEngineer to create specialized agents for different domains.

## Core Principles

- **LLM Agnostic**: No dependency on specific LLM libraries (LangChain, etc.)
- **Resource-Based**: Capabilities exposed through Resources with adaptive metadata
- **Workflow Composition**: Data flow through composed functions
- **State-Driven**: All agent state maintained in `.state` dict
- **Prompt-Centric**: PromptEngineer handles all prompt complexity
- **Conversational Loop**: Maintains conversation pattern with tool execution

## Architecture Components

### 1. Core Agent Class

```python
from common.llm import LLM
from common.llm.types import LLMMessage

class Agent:
    def __init__(self, agent_type: str, llm_provider: str | None = None, model: str | None = None, config: dict = None):
        self.agent_type = agent_type
        self.config = config or {}

        # Use existing LLM implementation
        self.llm = LLM(provider=llm_provider, model=model)

        # Initialize core components
        self.prompt_engineer = PromptEngineer(agent_type, self.config.get('prompt_config', {}))
        self.resources = {}  # Resource registry
        self.workflows = {}  # Workflow registry
        self.state = {
            'conversation_history': [],
            'current_context': {},
            'session_metadata': {},
            'user_preferences': {},
            'task_state': {}
        }

    def register_resource(self, name: str, resource: Resource):
        """Register a resource with the agent"""

    def register_workflow(self, name: str, workflow: Workflow):
        """Register a workflow with the agent"""

    async def chat(self, user_input: str) -> str:
        """Main conversational interface with tool execution"""

    def execute_workflow(self, workflow_name: str, params: dict) -> dict:
        """Execute a workflow with given parameters"""

    def query_resource(self, resource_name: str, method: str, params: dict) -> dict:
        """Query a resource with given method and parameters"""
```

### 2. Resource Abstraction

```python
class Resource:
    def __init__(self, name: str, description: str, methods: dict):
        self.name = name
        self.description = description
        self.methods = methods  # {method_name: MethodInfo}
        self.metadata = {
            'adaptive_docstrings': {},
            'usage_stats': {},
            'performance_metrics': {}
        }

    def query(self, method: str, params: dict) -> dict:
        """Primary query method - delegates to specific method"""

    def get_method_docstring(self, method: str) -> str:
        """Get adaptive docstring for method"""

    def update_metadata(self, feedback: dict):
        """Update adaptive metadata based on feedback"""

class MethodInfo:
    def __init__(self, name: str, docstring: str, parameters: dict, handler: callable):
        self.name = name
        self.docstring = docstring
        self.parameters = parameters
        self.handler = handler
```

### 3. Workflow Composition

```python
class Workflow:
    def __init__(self, name: str, steps: list, description: str = ""):
        self.name = name
        self.steps = steps  # List of (function, input_mapping, output_mapping)
        self.description = description
        self.metadata = {
            'execution_stats': {},
            'error_handling': {},
            'dependencies': []
        }

    def execute(self, initial_data: dict, agent_state: dict) -> dict:
        """Execute workflow with data flow through steps"""

    def add_step(self, function: callable, input_mapping: dict, output_mapping: dict):
        """Add a step to the workflow"""

    def validate_dependencies(self) -> bool:
        """Validate that all dependencies are available"""

class WorkflowStep:
    def __init__(self, function: callable, input_mapping: dict, output_mapping: dict):
        self.function = function
        self.input_mapping = input_mapping  # Maps workflow data to function params
        self.output_mapping = output_mapping  # Maps function output to workflow data
```

### 4. PromptEngineer Class

```python
class PromptEngineer:
    def __init__(self, agent_type: str):
        self.agent_type = agent_type
        self.prompt_templates = {}
        self.adaptive_prompts = {}
        self.feedback_history = []
        self.performance_metrics = {}

    def create_system_prompt(self, agent_state: dict, available_resources: dict,
                           available_workflows: dict) -> str:
        """Create system prompt incorporating state and capabilities"""

    def create_user_prompt(self, user_input: str, context: dict) -> str:
        """Create user prompt with context"""

    def create_tool_prompt(self, tool_name: str, tool_info: dict) -> str:
        """Create prompt for tool execution"""

    def combine_prompts(self, prompt_parts: list, strategy: str = "concatenate") -> str:
        """Combine multiple prompt parts using specified strategy"""

    def evolve_prompt(self, prompt_type: str, feedback: dict, performance_data: dict):
        """Evolve prompts based on feedback and performance"""

    def adapt_to_context(self, base_prompt: str, context: dict) -> str:
        """Adapt prompt based on current context"""

    def get_prompt_variants(self, prompt_type: str, count: int = 3) -> list:
        """Generate multiple prompt variants for A/B testing"""
```

### 5. LLM Abstraction Layer

```python
class LLMProvider:
    def __init__(self, provider_type: str, config: dict):
        self.provider_type = provider_type
        self.config = config
        self.client = self._initialize_client()

    def generate(self, messages: list, tools: list = None, **kwargs) -> dict:
        """Generate response from LLM"""

    def stream_generate(self, messages: list, tools: list = None, **kwargs):
        """Stream response from LLM"""

    def get_available_models(self) -> list:
        """Get list of available models"""

    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text"""

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation"""

class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""

class OllamaProvider(LLMProvider):
    """Ollama local provider implementation"""
```

## Use Case Implementations

### 1. CodingAgent

```python
class CodingAgent(Agent):
    def __init__(self, llm_provider: LLMProvider, config: dict = None):
        super().__init__("coding", llm_provider, config)
        self._setup_coding_resources()
        self._setup_coding_workflows()

    def _setup_coding_resources(self):
        """Register coding-specific resources"""
        self.register_resource("file_system", FileSystemResource())
        self.register_resource("git", GitResource())
        self.register_resource("terminal", TerminalResource())
        self.register_resource("web_search", WebSearchResource())
        self.register_resource("code_analysis", CodeAnalysisResource())

    def _setup_coding_workflows(self):
        """Register coding-specific workflows"""
        self.register_workflow("debug_code", DebugCodeWorkflow())
        self.register_workflow("refactor_code", RefactorCodeWorkflow())
        self.register_workflow("add_feature", AddFeatureWorkflow())
        self.register_workflow("write_tests", WriteTestsWorkflow())
```

### 2. FinancialAnalyst

```python
class FinancialAnalyst(Agent):
    def __init__(self, llm_provider: LLMProvider, config: dict = None):
        super().__init__("financial_analyst", llm_provider, config)
        self._setup_financial_resources()
        self._setup_financial_workflows()

    def _setup_financial_resources(self):
        """Register financial-specific resources"""
        self.register_resource("market_data", MarketDataResource())
        self.register_resource("financial_news", FinancialNewsResource())
        self.register_resource("company_data", CompanyDataResource())
        self.register_resource("economic_indicators", EconomicIndicatorsResource())
        self.register_resource("portfolio_data", PortfolioDataResource())

    def _setup_financial_workflows(self):
        """Register financial-specific workflows"""
        self.register_workflow("analyze_stock", AnalyzeStockWorkflow())
        self.register_workflow("portfolio_optimization", PortfolioOptimizationWorkflow())
        self.register_workflow("risk_assessment", RiskAssessmentWorkflow())
        self.register_workflow("market_research", MarketResearchWorkflow())
```

## State Management

### State Structure

```python
state = {
    'conversation_history': [
        {'role': 'user', 'content': '...', 'timestamp': '...'},
        {'role': 'assistant', 'content': '...', 'timestamp': '...'}
    ],
    'current_context': {
        'active_task': 'debug_python_code',
        'working_directory': '/path/to/project',
        'focus_area': 'authentication',
        'priority': 'high'
    },
    'session_metadata': {
        'session_id': 'uuid',
        'start_time': 'timestamp',
        'user_id': 'user123',
        'agent_version': '1.0.0'
    },
    'user_preferences': {
        'code_style': 'pep8',
        'language': 'python',
        'verbosity': 'concise',
        'auto_save': True
    },
    'task_state': {
        'current_workflow': 'debug_code',
        'workflow_step': 3,
        'intermediate_results': {...},
        'pending_actions': [...]
    }
}
```

## Conversational Loop Pattern

```python
async def chat(self, user_input: str) -> str:
    """Main conversational interface with tool execution loop"""

    # 1. Update state with user input
    self._add_to_conversation_history('user', user_input)

    # 2. Create system prompt using PromptEngineer
    system_prompt = self.prompt_engineer.create_system_prompt(
        self.state, self.resources, self.workflows
    )

    # 3. Set system prompt if not already set
    if not self.llm.get_system_messages():
        self.llm.set_system_prompt(system_prompt)

    # 4. Generate initial response using existing LLM interface
    response = await self.llm.chat(user_input)

    # 5. Handle tool execution loop
    while self._has_tool_calls(response):
        tool_results = await self._execute_tools(response)

        # Add tool results to conversation
        for tool_result in tool_results:
            await self.llm.chat(tool_result, role="assistant")

        # Get next response
        response = await self.llm.chat("Continue with the tool results above.")

    # 6. Update state and return response
    self._add_to_conversation_history('assistant', response)
    return response
```

## Adaptive Learning System

### Prompt Evolution

```python
class PromptEvolution:
    def __init__(self, prompt_engineer: PromptEngineer):
        self.prompt_engineer = prompt_engineer
        self.feedback_analyzer = FeedbackAnalyzer()
        self.performance_tracker = PerformanceTracker()

    def evolve_prompts(self, feedback_data: list, performance_data: dict):
        """Evolve prompts based on feedback and performance"""

    def generate_prompt_variants(self, base_prompt: str, mutation_rate: float = 0.1) -> list:
        """Generate mutated variants of prompts"""

    def evaluate_prompt_performance(self, prompt: str, test_cases: list) -> float:
        """Evaluate prompt performance on test cases"""
```

### Resource Metadata Adaptation

```python
class ResourceMetadataAdapter:
    def __init__(self, resource: Resource):
        self.resource = resource
        self.usage_patterns = {}
        self.feedback_history = []

    def adapt_docstrings(self, usage_feedback: dict):
        """Adapt resource docstrings based on usage feedback"""

    def optimize_parameters(self, performance_data: dict):
        """Optimize resource parameters based on performance"""

    def update_capabilities(self, new_capabilities: dict):
        """Update resource capabilities based on discovered usage patterns"""
```

## Implementation Phases

### Phase 1: Core Infrastructure
- [ ] Base Agent class with state management
- [ ] Resource abstraction with adaptive metadata
- [ ] Workflow composition system
- [ ] Basic PromptEngineer
- [ ] LLM abstraction layer

### Phase 2: Use Case Implementations
- [ ] CodingAgent with file system, git, terminal resources
- [ ] FinancialAnalyst with market data, news, analysis resources
- [ ] Basic workflows for each agent type

### Phase 3: Advanced Features
- [ ] Adaptive learning system
- [ ] Prompt evolution mechanisms
- [ ] Resource metadata adaptation
- [ ] Performance optimization

### Phase 4: Production Features
- [ ] State persistence
- [ ] Multi-agent coordination
- [ ] Advanced workflow orchestration
- [ ] Monitoring and observability

## File Structure

```
adana/
├── specs/
│   ├── agentic_architecture.md
│   ├── resource_specs.md
│   ├── workflow_specs.md
│   ├── prompt_engineer_specs.md
│   └── llm_abstraction_spec.md
├── core/
│   ├── agent/
│   │   ├── base_agent.py
│   │   ├── state_manager.py
│   │   ├── conversational_loop.py
│   │   ├── llm_integration.py
│   │   └── tool_execution.py
│   ├── resource/
│   │   ├── base_resource.py
│   │   ├── method_info.py
│   │   └── metadata_adapter.py
│   ├── workflow/
│   │   ├── base_workflow.py
│   │   ├── workflow_step.py
│   │   └── workflow_registry.py
│   └── prompt_engineer/
│       ├── prompt_engineer.py
│       ├── template_manager.py
│       └── evolution_engine.py
├── common/                            # Existing shared components
│   ├── llm/                          # Existing LLM infrastructure
│   │   ├── llm.py
│   │   ├── types.py
│   │   ├── providers/
│   │   │   ├── factory.py
│   │   │   ├── anthropic.py
│   │   │   ├── openai.py
│   │   │   ├── ollama.py
│   │   │   └── [other providers]
│   │   └── tests/
│   └── config.py                     # Existing configuration management
├── lib/
│   ├── agents/
│   │   ├── coding_agent.py
│   │   └── financial_analyst.py
│   ├── resources/
│   │   ├── file_system.py
│   │   ├── git.py
│   │   ├── market_data.py
│   │   └── web_search.py
│   └── workflows/
│       ├── coding_workflows.py
│       └── financial_workflows.py
├── examples/
│   ├── coding_agent_demo.py
│   └── financial_analyst_demo.py
└── config.json                       # Existing LLM configuration
```
