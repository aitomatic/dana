# Prompt Engineering System Specification

## Overview

The Adana prompt engineering system provides a structured approach to generating system prompts for agents, incorporating resource descriptions and agent descriptions. The system follows the coding_agent.py pattern for consistency and effectiveness.

## Architecture

### Core Components

1. **PromptEngineer** - Central orchestrator for prompt generation
2. **BasePrompts** - Common prompt utilities and formatting
3. **BaseAgentPrompts** - Agent-specific prompt management
4. **BaseResourcePrompts** - Resource-specific prompt management
5. **BaseAgent** - Agent base class with prompt integration

## Design Principles

### 1. Single Source of Truth
- Each agent's prompts come from its `AgentPrompts` class
- Each resource's prompts come from its `ResourcePrompts` class
- No duplication of prompt content across classes

### 2. Coding Agent Pattern Compliance
- System prompts follow the exact structure and style of `coding_agent.py`
- Concise, direct communication with minimal token usage
- Clear examples, capabilities, and limitations

### 3. Modular Composition
- System prompts are composed from multiple sources
- Agent self-description + available resources + available agents
- Dynamic content based on current context

## Component Specifications

### PromptEngineer Class

**Location**: `adana/frameworks/prteng/prompt_engineer.py`

**Responsibilities**:
1. Generate complete system prompts for agents
2. Compose resource descriptions for inclusion in system prompts
3. Compose agent descriptions for inclusion in system prompts
4. Follow coding_agent.py pattern and structure

**Key Methods**:
```python
class PromptEngineer:
    def create_agent_system_prompt(
        self,
        agent: BaseAgent,
        available_resources: list[BaseResource] = None,
        available_agents: list[BaseAgent] = None,
        context: dict[str, Any] = None
    ) -> str:
        """Create complete system prompt for an agent."""
        
    def create_resource_description(self, resource: BaseResource) -> str:
        """Create resource description for inclusion in system prompts."""
        
    def create_agent_description(self, agent: BaseAgent) -> str:
        """Create agent description for inclusion in other agents' system prompts."""
        
    def _apply_coding_agent_pattern(self, content: str) -> str:
        """Apply coding_agent.py structure and formatting."""
```

### BaseAgentPrompts Enhancements

**New Required Methods**:
```python
class BaseAgentPrompts:
    @property
    def agent_self_description(self) -> str:
        """Self-description for inclusion in own system prompt."""
        
    @property
    def agent_description(self) -> str:
        """Description for inclusion in other agents' system prompts."""
        
    @property
    def system_prompt(self) -> str:
        """Main system prompt (delegates to PromptEngineer)."""
```

**Note**: Agent-to-agent communication is handled through the standard system prompt and timeline system, not through separate communication prompts.

### BaseResourcePrompts Enhancements

**New Required Methods**:
```python
class BaseResourcePrompts:
    @property
    def resource_description(self) -> str:
        """Detailed resource description for LLM understanding."""
        
    @property
    def resource_usage_examples(self) -> str:
        """Concrete usage examples for the resource."""
        
    def get_method_description(self, method_name: str) -> str:
        """Get description for specific resource method."""
```

## System Prompt Structure

Following the coding_agent.py pattern:

```
You are a [AGENT_TYPE] that [PURPOSE]. Use the instructions below to assist users.

IMPORTANT: [KEY_CONSTRAINTS]

# Tone and style
[COMMUNICATION_GUIDELINES]

## Examples
[CONCRETE_EXAMPLES]

# Capabilities
[AGENT_CAPABILITIES]

# Limitations
[AGENT_LIMITATIONS]

# Available Resources
[RESOURCE_DESCRIPTIONS]

# Available Agents
[AGENT_DESCRIPTIONS]

[ADDITIONAL_SECTIONS]
```

**Note**: Agent-to-agent communication is handled through the standard system prompt and timeline system. Agents communicate by sending messages through the `interact_with_agent()` method, and the receiving agent processes these messages using its normal system prompt.

## Implementation Details

### 1. Agent Self-Description

**Purpose**: Describes the agent's own capabilities, limitations, and behavior for its own system prompt.

**Content**:
- Role and purpose
- Core capabilities
- Communication style
- Behavioral guidelines
- Limitations and constraints

**Example**:
```python
@property
def agent_self_description(self) -> str:
    return """You are a Financial Analyst agent specializing in market analysis and investment recommendations.

CORE CAPABILITIES:
- Financial data analysis and interpretation
- Market trend analysis and forecasting
- Risk assessment and portfolio optimization
- Financial report generation

COMMUNICATION STYLE:
- Data-driven and analytical
- Precise with numbers and metrics
- Professional and objective
- Clear explanations of complex financial concepts

LIMITATIONS:
- Cannot provide personal financial advice
- Limited to publicly available data
- Cannot guarantee investment outcomes
- Focused on analysis, not execution"""
```

### 2. Agent Description (for others)

**Purpose**: Describes the agent for inclusion in other agents' system prompts.

**Content**:
- Agent type and specialization
- Key capabilities
- When to contact this agent
- How to interact with this agent

**Example**:
```python
@property
def agent_description(self) -> str:
    return """FINANCIAL ANALYST AGENT
- Specializes in financial data analysis and market research
- Contact for: investment analysis, market trends, risk assessment
- Interaction: Provide specific financial data or questions
- Response style: Data-driven analysis with clear recommendations"""
```

### 3. Resource Description

**Purpose**: Describes resources for inclusion in agent system prompts.

**Content**:
- Resource name and purpose
- Available methods and capabilities
- Usage examples
- Parameters and return values

**Example**:
```python
@property
def resource_description(self) -> str:
    return """DATABASE RESOURCE
- Purpose: Access and manipulate database data
- Methods: query(sql), insert(table, data), update(table, data, where)
- Usage: call_resource('database', 'query', {'sql': 'SELECT * FROM users'})
- Returns: Query results or operation status"""
```

## Integration Points

### 1. Agent System Prompt Generation

```python
# In BaseAgent
def get_system_prompt(self) -> str:
    prompt_engineer = PromptEngineer()
    return prompt_engineer.create_agent_system_prompt(
        agent=self,
        available_resources=self.get_available_resources(),
        available_agents=self.get_available_agents(),
        context=self.get_context()
    )
```

### 2. Dynamic Resource Integration

```python
# In PromptEngineer
def create_agent_system_prompt(self, agent, available_resources, available_agents, context):
    base_prompt = agent.prompts.agent_self_description
    
    # Add resource descriptions
    if available_resources:
        resource_section = self._create_resource_section(available_resources)
        base_prompt += f"\n\n# Available Resources\n{resource_section}"
    
    # Add agent descriptions
    if available_agents:
        agent_section = self._create_agent_section(available_agents)
        base_prompt += f"\n\n# Available Agents\n{agent_section}"
    
    return self._apply_coding_agent_pattern(base_prompt)
```

## File Structure

```
adana/frameworks/prteng/
├── __init__.py
├── base_prompts.py              # Common prompt utilities
├── base_agent_prompts.py        # Agent prompt base class
├── base_resource_prompts.py     # Resource prompt base class
├── prompt_engineer.py           # Central prompt orchestrator
└── examples/
    ├── example_agent_prompts.py
    └── example_resource_prompts.py
```

## Benefits

1. **Consistency**: All prompts follow coding_agent.py pattern
2. **Modularity**: Easy to add new agents and resources
3. **Maintainability**: Single source of truth for each component
4. **Flexibility**: Dynamic composition based on context
5. **Reusability**: Agent descriptions can be shared across agents

## Migration Path

1. Create `PromptEngineer` class
2. Enhance `BaseAgentPrompts` with new methods
3. Enhance `BaseResourcePrompts` with new methods
4. Update `BaseAgent` to use `PromptEngineer`
5. Update existing agents to implement new methods
6. Test with `ExampleAgent` and `ExampleResource`

## Example Usage

```python
# Agent gets its system prompt
agent = FinancialAnalystAgent()
system_prompt = agent.get_system_prompt()

# System prompt includes:
# - Agent's own description
# - Available resource descriptions
# - Available agent descriptions
# - All formatted in coding_agent.py style
```

This design provides a comprehensive, maintainable, and consistent approach to prompt engineering across the entire Adana system.
