# Design for Agent's Problem-Solving with Expert Workflows

## Overview

The agent problem-solving system provides a unified interface for agents to solve problems by intelligently routing them to specialized workflows contained in existing Dana modules. This design enables agents to leverage domain expertise through importable modules while maintaining a consistent problem-solving interface.

## Key Approach

### Core Philosophy
The primary approach is leveraging **already-existing, importable Dana modules** that contain **WORKFLOWS** performing precise and sophisticated tasks in specific technical domains. These workflows are the building blocks that agents use to solve problems.

### Workflow Characteristics
- **Composed Functions**: Workflows are composed functions that can be readily called
- **Signature Compliance**: They operate on resources and other input arguments that are compliant with their function signatures
- **Domain-Specific Results**: They return helpful intermediate or final results for problems or sub-tasks in their domain
- **Composability**: Workflows can be composed further into greater workflows or included in generated-at-problem-solving-time functions
- **Inspectable**: Workflows should be inspectable in terms of their names and/or metadata for intelligent selection

### Agent Blueprint Structure
```dana
agent_blueprint DomainExpert:
    expertise: list = [module1, module2, module3]  # List of Dana modules containing expert workflows
```

The agent blueprint or agent instance/singleton is declared to have access to certain domain expertise by having its `.expertise` attribute assigned to a list of Dana modules that contain expert workflows.

## Fundamental Building Blocks

### 1. Problem Statement
- **Definition**: A natural-language string task or problem statement
- **Characteristics**:
  - Describes what needs to be solved or accomplished
  - May include implicit or explicit constraints
  - Can be decomposed into sub-problems
- **Example**: "Calculate the liquidity ratios for Company X using their latest financial statements"

### 2. Resources
- **Definition**: Dictionary with string keys where each value is a named queryable resource or input information
- **Characteristics**:
  - Simple dictionary interface: `{'resource_key': resource_object}`
  - Values can be diverse types with no prior constraints
  - **Inspectable**: Resource values should be inspectable in terms of their names and/or metadata
  - This inspectability enables the problem-solving procedure to make informed guesses about what resources to use in which expert workflows
- **Examples**:
  ```python
  {
      "financial_data": database_connection,
      "company_info": api_client,
      "documents": document_store,
      "config": {"currency": "USD", "period": "2023"}
  }
  ```

### 3. Expertise Modules (Agent Capabilities)
- **Definition**: Importable Dana modules containing named workflows (composed functions) with input-output signatures
- **Characteristics**:
  - Self-contained collections of related workflows
  - Well-defined interfaces with function signatures
  - **Inspectable**: Workflows should be inspectable in terms of their names and/or metadata
  - This inspectability enables intelligent workflow selection and resource matching
- **Examples**: `financial_analysis` module with workflows like `calc_liquidity_ratios`, `analyze_financial_health`

## Agent Solve Method Interface

### Method Signature
```python
def solve(
    problem: str,
    resources: dict[str, Any] = None
) -> Any:
    """
    Solve a problem using available resources and expertise modules.

    Args:
        problem: Natural language description of the problem to solve
        resources: Dictionary mapping resource keys to resource objects

    Returns:
        Solution to the problem
    """
```

### Parameters
- **problem**: Natural language string task or problem statement
- **resources**: Dictionary with string keys where each value is a resource or input information

### Resource and Workflow Diversity
- **No Prior Constraints**: Both resource values and workflow function signatures can be diverse with no prior constraints
- **Inspectability Requirement**: Both must be inspectable in terms of names and/or metadata
- **Intelligent Matching**: The problem-solving procedure uses this inspectability to make informed guesses about:
  - Which workflow(s) to utilize
  - What resources to use in which expert workflows

## Problem-Solving Flow

### Phase 1: Problem Analysis
1. **Problem Understanding**: Parse and understand the natural language problem statement
2. **Key Concept Extraction**: Identify key concepts, entities, and required operations
3. **Resource Requirements**: Determine what types of resources might be needed

### Phase 2: Expertise Module Inspection
1. **Module Discovery**: Examine the agent's expertise modules for available workflows
2. **Workflow Inspection**: Analyze workflow names, metadata, and function signatures
3. **Capability Assessment**: Understand what each workflow can do based on its inspectable properties

### Phase 3: Resource Inspection
1. **Resource Discovery**: Examine available resources in the dictionary
2. **Resource Analysis**: Analyze resource names, metadata, and capabilities
3. **Compatibility Assessment**: Determine which resources might be compatible with which workflows

### Phase 4: Intelligent Matching
1. **Workflow Selection**: Use inspectable properties to select appropriate workflows
2. **Resource Matching**: Match resources to workflow input requirements based on inspectable properties
3. **Execution Planning**: Plan how to use selected workflows with available resources

### Phase 5: Solution Execution
1. **Workflow Execution**: Execute selected workflows with matched resources
2. **Result Collection**: Collect intermediate and final results
3. **Error Handling**: Handle any execution errors or missing resources

### Phase 6: Result Synthesis
1. **Solution Assembly**: Combine results from multiple workflows if needed
2. **Problem Resolution**: Ensure the solution addresses the original problem
3. **Response Formatting**: Format the final solution appropriately

## Key Design Principles

### 1. Leverage Existing Code
- **Module Reuse**: Build on existing Dana modules rather than creating new systems
- **Workflow Composition**: Use existing workflows as building blocks
- **Domain Expertise**: Leverage domain-specific knowledge already encoded in workflows

### 2. Inspectability
- **Resource Inspection**: Resources must be inspectable for intelligent matching
- **Workflow Inspection**: Workflows must be inspectable for intelligent selection
- **Metadata Utilization**: Use names, signatures, and metadata for informed decisions

### 3. Flexibility
- **No Type Constraints**: No prior constraints on resource or workflow types
- **Dynamic Matching**: Intelligent matching based on inspectable properties
- **Adaptive Execution**: Adapt to available resources and workflows

### 4. Composability
- **Workflow Composition**: Combine workflows to solve complex problems
- **Generated Solutions**: Create new workflows at problem-solving time if needed
- **Modular Design**: Maintain modularity for maintainability and reusability

## Example Usage

```dana
# Agent blueprint with expertise modules
agent_blueprint FinancialAnalyst:
    expertise: list = [financial_analysis, risk_assessment, reporting]

# Agent instance
analyst = FinancialAnalyst()

# Solve problem using available resources
result = analyst.solve(
    problem="Calculate liquidity ratios for Company X using their latest financial statements",
    resources={
        "financial_data": database_connection,
        "company_info": api_client,
        "analysis_config": {"currency": "USD", "period": "2023"}
    }
)
```

## Implementation Strategy

### Workflow Discovery
```python
def discover_workflows_from_modules(self, expertise_modules: list[ModuleType]) -> None:
    """Discover and register workflows from expertise modules."""
    for module in expertise_modules:
        if hasattr(module, '__all__'):
            workflow_names = module.__all__
            for workflow_name in workflow_names:
                if hasattr(module, workflow_name):
                    workflow_function = getattr(module, workflow_name)
                    # Register workflow with inspectable metadata
                    self.register_workflow(workflow_function, module.__name__)
```

### Intelligent Resource Matching
```python
def match_resources_to_workflow(self, workflow, resources: dict[str, Any]) -> dict[str, Any]:
    """Match available resources to workflow requirements using inspectable properties."""
    matched_resources = {}

    # Use workflow's inspectable properties to determine requirements
    workflow_requirements = self.inspect_workflow_requirements(workflow)

    # Use resource inspectable properties to find matches
    for req_name, req_type in workflow_requirements.items():
        for res_key, res_value in resources.items():
            if self.is_compatible_resource(res_key, res_value, req_name, req_type):
                matched_resources[req_name] = res_value
                break

    return matched_resources
```

## Future Enhancements

### 1. Enhanced Inspection
- **Type System Integration**: Better integration with Dana's type system for inspection
- **Metadata Standards**: Standardized metadata for workflows and resources
- **Semantic Matching**: Semantic understanding of workflow and resource capabilities

### 2. Advanced Composition
- **Dynamic Workflow Generation**: Generate new workflows at problem-solving time
- **Multi-Step Problem Solving**: Chain multiple workflows for complex problems
- **Conditional Execution**: Execute workflows based on intermediate results

### 3. Learning and Adaptation
- **Performance Tracking**: Learn which workflows work best for different problem types
- **Resource Optimization**: Optimize resource usage based on historical performance
- **Workflow Recommendations**: Suggest new workflows based on problem patterns
