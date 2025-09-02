# Agent Strategy Prompt Management

This directory contains the agent strategy system with a new prompt management approach that separates prompt templates from strategy logic for easier maintenance and editing.

## Structure

```
dana/builtin_types/agent/strategy/
├── __init__.py                 # Strategy registry and selection
├── base.py                     # Base strategy interface
├── common_prompts.py           # Shared prompt elements and utilities
├── recursive/
│   ├── __init__.py
│   ├── recursive_strategy.py   # Recursive strategy implementation
│   └── prompts.py             # Recursive strategy prompts
├── iterative/
│   ├── __init__.py
│   ├── iterative_strategy.py   # Iterative strategy implementation
│   └── prompts.py             # Iterative strategy prompts
└── README.md                   # This file
```

## Prompt Management

### Why Extract Prompts?

1. **Easier Editing**: Prompts can be modified without touching strategy logic
2. **Version Control**: Prompt changes are clearly tracked in git
3. **Reusability**: Common prompt elements can be shared between strategies
4. **Maintenance**: Non-developers can edit prompts without code knowledge
5. **Testing**: Prompts can be tested independently of strategy logic

### How It Works

Each strategy now imports its prompts from a dedicated `prompts.py` file:

```python
# In recursive_strategy.py
from .prompts import build_basic_prompt, build_enhanced_prompt, SYSTEM_MESSAGE

def _build_basic_prompt(self, problem: str, context: ProblemContext) -> str:
    return build_basic_prompt(problem, context)
```

### Common Prompt Elements

The `common_prompts.py` file contains shared elements:

- **Common Functions**: Basic agent functions used by all strategies
- **Decision Framework**: Standard decision-making structure
- **Formatting Utilities**: Functions for consistent prompt formatting
- **Base Builder**: Function to build common prompt bases

### Strategy-Specific Prompts

Each strategy has its own `prompts.py` file containing:

- **Strategy Description**: How the strategy works
- **Strategy Functions**: Functions specific to that strategy
- **Strategy Guidance**: Specific instructions for the strategy
- **Prompt Templates**: Complete prompt templates
- **Building Functions**: Functions to construct prompts with context

## Adding New Strategies

To add a new strategy with prompt management:

1. **Create the strategy directory**:
   ```
   mkdir dana/builtin_types/agent/strategy/new_strategy/
   ```

2. **Create `prompts.py`**:
   ```python
   # new_strategy/prompts.py
   from ..common_prompts import build_common_prompt_base
   
   STRATEGY_DESCRIPTION = " using new approach"
   NEW_STRATEGY_FUNCTIONS = """
   - agent.new_function(): Do something new
   """
   
   def build_new_strategy_prompt(problem: str, context) -> str:
       return build_common_prompt_base(
           problem, context, 
           STRATEGY_DESCRIPTION, 
           NEW_STRATEGY_FUNCTIONS
       )
   ```

3. **Create the strategy class**:
   ```python
   # new_strategy/new_strategy.py
   from .prompts import build_new_strategy_prompt
   
   def _build_prompt(self, problem: str, context) -> str:
       return build_new_strategy_prompt(problem, context)
   ```

4. **Register in `__init__.py`**:
   ```python
   from .new_strategy.new_strategy import NewStrategy
   
   STRATEGY_TEMPLATES = {
       "recursive": RecursiveStrategy,
       "iterative": IterativeStrategy,
       "new_strategy": NewStrategy,  # Add this line
   }
   ```

## Editing Prompts

### Simple Changes

To modify a prompt, edit the appropriate `prompts.py` file:

```python
# In recursive/prompts.py
BASIC_PROMPT_TEMPLATE = """
You are an AI agent solving problems using Dana code.
... your modified prompt here ...
"""
```

### Adding New Prompt Types

To add new prompt types:

1. **Add the template** to the appropriate `prompts.py` file
2. **Add a building function** that uses the template
3. **Update the strategy** to use the new prompt type

### Testing Prompt Changes

After modifying prompts:

1. **Run tests** to ensure strategies still work
2. **Test with real problems** to verify prompt effectiveness
3. **Check for consistency** across different strategies

## Best Practices

### Prompt Design

1. **Be Clear**: Use simple, unambiguous language
2. **Be Specific**: Give clear examples and instructions
3. **Be Consistent**: Use consistent formatting and structure
4. **Be Flexible**: Allow for different problem types and complexities

### Code Organization

1. **Keep prompts separate** from strategy logic
2. **Use constants** for repeated text
3. **Use functions** for dynamic prompt building
4. **Document changes** in commit messages

### Maintenance

1. **Review prompts regularly** for clarity and effectiveness
2. **Update prompts** when adding new agent functions
3. **Test prompts** with various problem types
4. **Version control** all prompt changes

## Example: Modifying a Prompt

Let's say you want to change how the recursive strategy explains recursion:

1. **Edit the prompt template**:
   ```python
   # In recursive/prompts.py
   RECURSION_RULES = """
   RECURSION APPROACH:
   - Break complex problems into smaller, similar sub-problems
   - Solve each sub-problem using the same approach
   - Combine results to solve the original problem
   - Use agent.solve() for sub-problems with increased depth tracking
   """
   ```

2. **Update the enhanced prompt template** to use the new rules
3. **Test the change** with a complex problem
4. **Commit the change** with a clear description

This approach makes prompt management much more maintainable and allows for rapid iteration on prompt quality without touching core strategy logic.
