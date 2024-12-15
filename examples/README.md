<!-- markdownlint-disable MD041 -->
<p align="center">
  ![Aitomatic Logo](https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png){: width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"}
</p>

# DXA Examples

This directory contains examples demonstrating different reasoning patterns and use cases.

## Reasoning Patterns

### 1. Direct Reasoning
Simple task execution:
```python
from dxa.agent import Agent

# Create direct execution agent
agent = Agent("executor").with_reasoning("direct")

# Run simple task
result = await agent.run("Calculate 2+2")
```

### 2. Chain of Thought
Step-by-step problem solving:
```python
# Create CoT agent
agent = Agent("solver").with_reasoning("cot")

# Solve complex problem
result = await agent.run({
    "objective": "Solve quadratic equation",
    "command": "Find roots of x^2 + 5x + 6 = 0"
})
```

### 3. OODA Loop
Adaptive decision making:
```python
# Create OODA agent
agent = Agent("strategist").with_reasoning("ooda")

# Handle dynamic situation
result = await agent.run({
    "objective": "Monitor system health",
    "command": "Check and respond to system metrics"
})
```

### 4. DANA (Neural-Symbolic)
Hybrid computation:
```python
# Create DANA agent
agent = Agent("hybrid").with_reasoning("dana")

# Execute computational task
result = await agent.run({
    "objective": "Optimize function",
    "command": "Find minimum of f(x) = x^2 - 4x + 4"
})
```

## Example Applications

1. `research_assistant.py` - Uses CoT for research tasks
2. `system_monitor.py` - Uses OODA for monitoring
3. `math_solver.py` - Uses DANA for computations
4. `chat_bot.py` - Uses Direct reasoning for simple interactions

Each example includes:
- Full implementation
- Usage instructions
- Sample inputs/outputs
- Best practices

## Running Examples

1. Set up environment:
```bash
source venv/bin/activate
```

2. Run an example:
```bash
python examples/research_assistant.py
```

## Creating Your Own

See the template in `examples/template.py` for creating new examples.

## Support

If you have questions about the examples or need assistance:

- Refer to the official DXA documentation
- Contact Aitomatic support
- Reach out to your Aitomatic representative

## License

These examples are proprietary and confidential to Aitomatic, Inc. All rights reserved.
