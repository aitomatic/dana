[Project Overview](../README.md) | [Main Documentation](../docs/README.md)

# Dana Examples

This directory contains examples demonstrating different aspects of the Dana framework.

## Directory Structure

```text
examples/
├── getting_started/      # Basic examples for new users
├── core_concepts/        # Examples of core DXA features
├── advanced_topics/      # Complex patterns and integrations
└── real_world_applications/  # Real-world use cases
```

## Getting Started

The `getting_started/` directory contains basic examples that demonstrate fundamental Dana concepts:

1. `01_introduction_to_dxa.ipynb` - Introduction to Dana
2. `02_simple_plans.ipynb` - Creating and running basic plans
3. `03_agent_configuration.ipynb` - Configuring agents with different settings

## Core Concepts

The `core_concepts/` directory contains examples that demonstrate core Dana features:

1. `01_planning_layer.ipynb` - Understanding the planning layer
2. `02_reasoning_layer.ipynb` - Understanding the reasoning layer
3. `03_execution_context.ipynb` - Managing execution context and resources
4. `04_capabilities.ipynb` - Working with agent capabilities
5. `05_resources.ipynb` - Managing and using resources
6. `06_tool_calling.ipynb` - Making resource methods callable
7. `07_mcp_resource.ipynb` - Working with MCP resources
8. `08_smart_resource_selection.ipynb` - Smart resource selection strategies

## Advanced Topics

The `advanced_topics/` directory contains complex examples and patterns:

1. `01_custom_agents.ipynb` - Creating custom agents
2. `02_advanced_planning.ipynb` - Advanced planning strategies
3. `03_advanced_reasoning.ipynb` - Advanced reasoning strategies

## Real-World Applications

The `real_world_applications/` directory contains examples of Dana in real-world scenarios:

1. `01_semiconductor_manufacturing.ipynb` - Semiconductor manufacturing applications
2. `02_general_manufacturing.ipynb` - General manufacturing applications
3. `03_financial_applications.ipynb` - Financial applications

## Prerequisites

Before running any examples:

1. Install Dana and its dependencies:

   ```bash
   pip install -e .
   ```

2. Set up your environment variables:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. Configure logging (optional):

   ```python
   from dana.common import DANA_LOGGER
   DANA_LOGGER.configure(
       level=DANA_LOGGER.DEBUG,
       console=True,
       log_data=True
   )
   ```

## Running Examples

Each example can be run directly with Python:

```bash
# Run a specific example
python examples/getting_started/01_introduction_to_dxa.py

# Run all examples in a directory
python -m pytest examples/getting_started/
```

## Learning Path

1. Start with the getting_started examples to understand basic concepts
2. Move to core_concepts to learn about DXA's 2-layer architecture
3. Explore advanced_topics for complex patterns
4. Study real_world_applications for practical use cases

## Troubleshooting

Common issues and solutions:

1. **LLM Connection Issues**
   - Verify your API key is set correctly in .env
   - Check your network connection
   - Ensure you have sufficient API credits

2. **Planning Layer Issues**
   - Check the plan structure is valid
   - Verify all required steps are present
   - Ensure proper resource selection
   - Validate planning strategy configuration

3. **Reasoning Layer Issues**
   - Verify reasoning strategy is properly configured
   - Check resource availability
   - Ensure proper execution context
   - Validate reasoning results

4. **Context Management**
   - Verify execution context is properly initialized
   - Check resource availability
   - Ensure proper cleanup
   - Validate resource configuration

## Contributing

When adding new examples:

1. Follow the existing directory structure
2. Include clear documentation
3. Add proper error handling
4. Include prerequisites and dependencies
5. Add cross-references to related examples
6. Update this README with new example information

## 📁 Available Examples

Each example includes:
- **Runnable Dana script** (`.dana` file)
- **Documentation** explaining the use case
- **Sample data** when applicable
- **Expected outputs** for verification

## MCP Integration Examples (NEW)

### `mcp-websearch/`
**Object Method Calls with MCP WebSearch**
```python
# Connect to MCP WebSearch service
websearch = use("mcp", url="http://localhost:8880/websearch")

# Call methods on the websearch object
tools = websearch.list_tools()
log.info(f"Available tools: {tools}")

# Perform searches with method calls
search_results = websearch.search("Dana programming language")
if len(search_results) > 0:
    log.info(f"Found {len(search_results)} results")
    
    # Process results
    for result in search_results:
        analysis = reason("Summarize this search result", context=result)
        log.info(f"Summary: {analysis}")
```

### `mcp-database/`
**Database Operations with Object Methods**
```python
# Scoped database connection
with use("mcp.database", "https://db.company.com") as database:
    # Call database methods
    users = database.query("SELECT * FROM users WHERE active = true")
    count = database.count_records("users")
    
    log.info(f"Processing {count} active users")
    
    # Process users and update
    for user in users:
        activity = database.get_user_activity(user.id)
        analysis = reason("Analyze user engagement", context=activity)
        
        if "low_engagement" in analysis:
            database.update_user_status(user.id, "needs_attention")
```

### `a2a-agents/`  
**Agent-to-Agent Communication**
```python
# Connect to specialized agents
research_agent = use("a2a.research-agent", "https://agents.company.com")
planning_agent = use("a2a.workflow-coordinator")

# Async method calls handled automatically
market_data = research_agent.collect_data("technology sector")
analysis = research_agent.analyze_trends(market_data)

# Pass results between agents
workflow = planning_agent.create_action_plan(analysis)
execution_status = planning_agent.execute_workflow(workflow)

log.info(f"Workflow status: {execution_status}")
```

---

## Traditional Dana Examples

---
<!-- AI Assistants: documentation markdowns should have this logo at the bottom -->
---
<p align="center">
Copyright © 2025 Aitomatic, Inc. Licensed under the <a href="../LICENSE.md">MIT License</a>.
<br/>
<a href="https://aitomatic.com">https://aitomatic.com</a>
</p>
