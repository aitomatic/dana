# Context Keys Reference

This document provides a comprehensive reference for all the context dictionary keys expected by each template in the Context Engineering Framework.

## Template Overview

The framework provides 4 main templates, each optimized for different use cases:

1. **General Template** - Fallback template for unspecified use cases
2. **Conversation Template** - Optimized for conversational interactions
3. **Analysis Template** - Optimized for data analysis and research
4. **Problem Solving Template** - Rich context for complex problem solving

## 1. General Template (`XMLGeneralTemplate`)

**Purpose**: Generic template that accepts any context keys

### Required Keys
- `query` - The main query/problem (required)

### Optional Keys
- Any other keys - Will be included as-is if they have values

### Example Context
```python
context = {
    "query": "What is the weather like?",
    "user_location": "San Francisco",
    "time_of_day": "morning",
    "preferences": "metric units"
}
```

### Output Structure
```xml
<context>
  <query>What is the weather like?</query>
  <user_location>San Francisco</user_location>
  <time_of_day>morning</time_of_day>
  <preferences>metric units</preferences>
</context>
```

## 2. Conversation Template (`XMLConversationTemplate`)

**Purpose**: Optimized for ongoing conversations and chat interactions

### Required Keys
- `query` - The current user message (required)

### Optional Keys
- `conversation_history` - Summary of previous conversation turns
- `recent_events` - List of recent events or actions

### Example Context
```python
context = {
    "query": "Tell me more about that",
    "conversation_history": "User: What is Python?\nAgent: Python is a programming language...",
    "recent_events": ["User asked about Python", "Agent provided basic explanation"]
}
```

### Output Structure
```xml
<conversation>
  <message>Tell me more about that</message>
  <history>
    <summary>User: What is Python?\nAgent: Python is a programming language...</summary>
  </history>
  <recent_events>
    <event>User asked about Python</event>
    <event>Agent provided basic explanation</event>
  </recent_events>
</conversation>
```

## 3. Analysis Template (`XMLAnalysisTemplate`)

**Purpose**: Optimized for data analysis, research, and examination tasks

### Required Keys
- `query` - The analysis query or research question (required)

### Optional Keys
- `data_context` - Description of the data being analyzed
- `analysis_params` - Dictionary of analysis parameters

### Example Context
```python
context = {
    "query": "Analyze sales performance for Q4",
    "data_context": "Sales data from CRM system, 10,000 records, Jan-Dec 2024",
    "analysis_params": {
        "time_range": "Q4 2024",
        "metrics": ["revenue", "conversions", "customer_satisfaction"],
        "group_by": "region"
    }
}
```

### Output Structure
```xml
<analysis>
  <query>Analyze sales performance for Q4</query>
  <data_context>
    <description>Sales data from CRM system, 10,000 records, Jan-Dec 2024</description>
  </data_context>
  <analysis_params>
    <param name="time_range">Q4 2024</param>
    <param name="metrics">revenue, conversions, customer_satisfaction</param>
    <param name="group_by">region</param>
  </analysis_params>
</analysis>
```

## 4. Problem Solving Template (`XMLProblemSolvingTemplate`)

**Purpose**: Rich context for complex problem solving, planning, and execution

### Required Keys
- `query` - The problem to be solved (required)

### Optional Keys

#### Problem Context
- `problem_statement` - Detailed problem description
- `objective` - What needs to be accomplished
- `current_depth` - Current recursion depth (for recursive strategies)
- `constraints` - Dictionary of problem constraints
- `assumptions` - List of assumptions about the problem

#### Workflow Context
- `workflow_current_workflow` - Name/ID of current workflow
- `workflow_workflow_state` - Current state of the workflow

#### Execution Context
- `conversation_history` - Summary of previous conversation turns
- `recent_events` - List of recent execution events
- `additional_context` - Any other relevant context data

### Example Context
```python
context = {
    "query": "Calculate 2 + 2",
    "problem_statement": "Simple arithmetic problem",
    "objective": "Solve: Calculate 2 + 2",
    "current_depth": 0,
    "constraints": {
        "conversation_history": "User: Calculate 2 + 2\nAgent: No result"
    },
    "assumptions": ["Basic arithmetic", "No special constraints"],
    "workflow_current_workflow": "RecursiveWorkflow_1234",
    "workflow_workflow_state": "planning",
    "conversation_history": "User: Calculate 2 + 2\nAgent: No result",
    "recent_events": ["Workflow started", "Strategy selected: RecursiveStrategy"],
    "additional_context": {
        "user_preference": "show_work",
        "complexity_level": "basic"
    }
}
```

### Output Structure
```xml
<context>
  <query>Calculate 2 + 2</query>
  <problem_context>
    <objective>Solve: Calculate 2 + 2</objective>
    <current_depth>0</current_depth>
    <constraints>
      <constraint type="conversation_history">User: Calculate 2 + 2\nAgent: No result</constraint>
    </constraints>
    <assumptions>
      <assumption>Basic arithmetic</assumption>
      <assumption>No special constraints</assumption>
    </assumptions>
  </problem_context>
  <workflow_context>
    <current_workflow>RecursiveWorkflow_1234</current_workflow>
    <workflow_state>planning</workflow_state>
  </workflow_context>
  <conversation_history>
    <summary>User: Calculate 2 + 2\nAgent: No result</summary>
  </conversation_history>
  <recent_events>
    <event>Workflow started</event>
    <event>Strategy selected: RecursiveStrategy</event>
  </recent_events>
  <additional_context>
    <user_preference>show_work</user_preference>
    <complexity_level>basic</complexity_level>
  </additional_context>
</context>
```

## Template Selection Guidelines

### When to Use Each Template

1. **General Template**: When you don't know what template to use or need maximum flexibility
2. **Conversation Template**: For ongoing conversations, chat interactions, and discussion-based tasks
3. **Analysis Template**: For data analysis, research, examination, and analytical tasks
4. **Problem Solving Template**: For complex problem solving, planning, execution, and recursive strategies

### Fallback Behavior

- If a requested template is not found, the system automatically falls back to the "general" template
- This ensures the system always has a working template
- Logs a warning when fallback occurs

### Context Key Best Practices

1. **Always provide `query`** - This is the only truly required key across all templates
2. **Use template-specific keys** - Each template is optimized for certain context keys
3. **Provide rich context** - More context leads to better LLM understanding
4. **Follow naming conventions** - Use the exact key names documented above
5. **Handle missing keys gracefully** - Templates work with minimal context but provide richer output with more context

## Adding New Templates

To add a new template:

1. Create a new template class inheriting from `XMLTemplate` or `TextTemplate`
2. Implement the `assemble()` method with your template's logic
3. Document the expected context keys in the class docstring
4. Add the template to `TemplateManager._load_templates()`
5. Update this reference document

## Example Usage

```python
from dana.frameworks.ctxeng import ContextEngine

# Create context engine
ctx = ContextEngine.from_agent(agent)

# Assemble prompt with problem-solving template
prompt = ctx.assemble(
    query="Calculate 2 + 2",
    template="problem_solving",
    context={
        "objective": "Solve: Calculate 2 + 2",
        "current_depth": 0,
        "constraints": {"conversation_history": "Previous context..."}
    }
)
```
