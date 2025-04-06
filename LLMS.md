# OpenDXA (Domain-Expert Agent Framework) - AI Coder Guide

## Core Philosophy
OpenDXA is a framework for building intelligent agents with domain expertise using LLMs. It follows a three-layer architecture that maps business workflows to concrete plans to reasoning patterns:
- Workflows (WHY): Define what agents can do
- Plans (WHAT): Break down workflows into executable steps
- Reasoning (HOW): Execute steps using thinking patterns

## Key Design Principles
1. Progressive Complexity: Start simple, scale to complex tasks
2. Composable Architecture: Mix and match capabilities
3. Domain Expertise Integration: Built-in system for expert knowledge
4. Clean Separation of Concerns: Three-layer architecture
5. Resource Management: Standardized integration of external tools via MCP

## Core Components
1. Agent System
   - Capability System: Defines agent abilities
   - Resource System: Integrates external tools
   - IO System: Handles input/output
   - State System: Manages agent state

2. Execution System
   - Workflow Layer: High-level task definition
   - Planning Layer: Step breakdown and dependencies
   - Reasoning Layer: Execution strategies
   - Pipeline Layer: Orchestration and flow

## Resource Integration
- Uses Model Context Protocol (MCP) for standardized tool integration
- Supports both STDIO and HTTP transport types
- Built-in tool discovery and schema validation
- Robust error handling and type safety

## Best Practices for AI Coders
1. Follow the three-layer architecture when adding new features
2. Use MCP for external tool integration
3. Implement proper error handling and type validation
4. Keep components focused and single-purpose
5. Document interfaces and schemas clearly

## Common Patterns
1. Workflow Creation:
   ```python
   workflow = Workflow(objective="Task description")
   workflow.add_node(ExecutionNode(
       node_id="TASK_ID",
       node_type=NodeType.TASK,
       objective="Step description"
   ))
   ```

2. Resource Integration:
   ```python
   mcp_resource = McpResource(
       name="resource_name",
       transport_params=StdioTransportParams(
           server_script="path/to/server.py"
       )
   )
   ```

## Extension Points
1. Custom Workflows: Extend Workflow class
2. New Capabilities: Add to capability system
3. Custom Resources: Implement MCP protocol
4. Reasoning Patterns: Add to reasoning layer 
