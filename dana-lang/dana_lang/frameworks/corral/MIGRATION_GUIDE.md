# CORRAL Framework - Composition Pattern

## Overview

The CORRAL framework uses the **composition pattern** (like ctxeng) for better modularity, testability, and easier integration.

## Architecture

### Composition Pattern
```python
from dana.frameworks.corral import CORRALEngineer
from dana.core.agent import AgentInstance

class MyAgent(AgentInstance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._corral_engineer = None

    @property
    def corral_engineer(self) -> CORRALEngineer:
        if self._corral_engineer is None:
            self._corral_engineer = CORRALEngineer.from_agent(self)
        return self._corral_engineer
```

## Usage

### 1. Import CORRALEngineer

```python
from dana.frameworks.corral import CORRALEngineer
```

### 2. Define Your Agent

```python
class MyAgent(AgentInstance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._corral_engineer = None

    @property
    def corral_engineer(self) -> CORRALEngineer:
        if self._corral_engineer is None:
            self._corral_engineer = CORRALEngineer.from_agent(self)
        return self._corral_engineer
```

### 3. Use CORRAL Methods

```python
agent.corral_engineer.curate_knowledge(source, context)
agent.corral_engineer.retrieve_knowledge(query)
agent.corral_engineer.execute_corral_cycle(problem)
agent.corral_engineer.get_knowledge_state()
```

## Benefits of the New Pattern

### ✅ Advantages

1. **🎯 Better Modularity**: CORRALEngineer can be used independently
2. **🧪 Easier Testing**: Test CORRALEngineer in isolation
3. **⚡ Lazy Initialization**: Only creates engines when needed
4. **🔧 Simpler Integration**: No complex multiple inheritance
5. **📦 Cleaner Architecture**: Follows composition over inheritance
6. **🔄 Direct Usage**: Use CORRALEngineer directly
7. **🛠️ Better Maintainability**: Clearer separation of concerns


## Usage Examples

### Example 1: Using CORRALEngineer

```python
from dana.frameworks.corral import CORRALEngineer
from dana.core.agent import AgentInstance

class KnowledgeAgent(AgentInstance):
    """Agent with knowledge management capabilities"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._corral_engineer = None

    @property
    def corral_engineer(self) -> CORRALEngineer:
        if self._corral_engineer is None:
            self._corral_engineer = CORRALEngineer.from_agent(self)
        return self._corral_engineer

    def solve_problem(self, problem: str):
        # Use CORRAL cycle for problem solving
        result = self.corral_engineer.execute_corral_cycle(problem)
        return result.action_result.outcomes

# Usage
agent = KnowledgeAgent(agent_type, values)
result = agent.solve_problem("How to optimize database queries?")
```

### Example 2: Using CORRALEngineer Directly

```python
from dana.frameworks.corral import CORRALEngineer
from dana.core.agent import AgentInstance

class CustomAgent(AgentInstance):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._corral_engineer = None

    @property
    def corral_engineer(self) -> CORRALEngineer:
        if self._corral_engineer is None:
            self._corral_engineer = CORRALEngineer.from_agent(self)
        return self._corral_engineer

    def learn_from_interaction(self, user_query: str, response: str, feedback: str):
        # Direct access to CORRAL functionality
        return self.corral_engineer.curate_from_interaction(
            user_query, response, feedback
        )
```

### Example 3: Integration with Context Engineering

```python
from dana.frameworks.corral import CORRALEngineer
from dana.frameworks.ctxeng import ContextEngineer
from dana.core.agent import AgentInstance

class AdvancedAgent(AgentInstance):
    """Agent with both CORRAL and Context Engineering"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._corral_engineer = None
        self._context_engineer = None

    @property
    def corral_engineer(self) -> CORRALEngineer:
        if self._corral_engineer is None:
            self._corral_engineer = CORRALEngineer.from_agent(self)
        return self._corral_engineer

    @property
    def context_engineer(self) -> ContextEngineer:
        if self._context_engineer is None:
            self._context_engineer = ContextEngineer.from_agent(self)
        return self._context_engineer

    def solve_with_context(self, problem: str):
        # Get knowledge from CORRAL
        knowledge_result = self.corral_engineer.retrieve_knowledge(problem)

        # Use knowledge to enhance context
        context_data = {
            "problem": problem,
            "relevant_knowledge": knowledge_result.knowledge_items
        }

        # Generate enhanced prompt
        prompt = self.context_engineer.engineer_context(
            problem, context_data, template="problem_solving"
        )

        return prompt
```

## Performance Considerations

### Memory Usage
- **New Pattern**: Lazy initialization reduces memory footprint
- **Old Pattern**: All engines initialized upfront

### Initialization Time
- **New Pattern**: Faster startup, engines created on-demand
- **Old Pattern**: Slower startup, all engines initialized immediately

### Runtime Performance
- **Both Patterns**: Identical runtime performance
- **New Pattern**: Slight overhead on first access (negligible)

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure to use the correct import path
2. **Method Not Found**: Ensure you're using CORRALEngineer
3. **Configuration Issues**: Configuration is handled internally

### Getting Help

- Check the updated documentation
- Review the examples in this guide
- Test with the new pattern in a development environment first

## Timeline

- **Phase 1**: New composition pattern available (current)
- **Phase 2**: CORRALActorMixin marked as deprecated
- **Phase 3**: CORRALActorMixin removed (future release)

## Conclusion

The new composition pattern provides the same powerful CORRAL functionality with better architecture, easier testing, and cleaner integration. The migration is straightforward and maintains full API compatibility.
