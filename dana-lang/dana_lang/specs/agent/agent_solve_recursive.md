# Recursive Strategy Implementation

## Overview

This document details the implementation of the **Recursive Strategy** for the `agent.solve()` system. This strategy implements the core architecture defined in `agent_solve.md` by providing a recursive, LLM-driven problem-solving approach that leverages the comprehensive context engineering system.

**Note**: This document assumes familiarity with the core architecture outlined in `agent_solve.md`, particularly the Context Engineering section. Please refer to that document for the overall system design, interfaces, and general patterns.

## Strategy Overview

The **Recursive Strategy** is a concrete implementation of the `BaseStrategy` interface that:

1. **Breaks down complex problems** into sub-problems using LLM analysis
2. **Generates Dana code** that the LLM believes will solve the problem
3. **Compiles and executes** the generated code within a workflow
4. **Supports recursion** by allowing the generated code to call `agent.solve()` again
5. **Prevents infinite loops** through depth limits and logical analysis
6. **Leverages rich context** from the Context Engineering Framework (`dana.frameworks.ctxeng`) for optimal LLM reasoning

## Implementation Details

### 1. Strategy Class Structure

```python
class RecursiveStrategy(BaseStrategy):
    """Recursive problem-solving strategy using LLM-generated Dana code."""
    
    def __init__(self, llm_client: LLMClient, max_depth: int = 10):
        self.llm_client = llm_client
        self.max_depth = max_depth
        self.prompt_templates = self._load_prompt_templates()
        self.computable_context = ComputableContext()
    
    def can_handle(self, problem: str, context: ProblemContext) -> bool:
        """Determine if this strategy can handle the problem."""
        # Recursive strategy can handle most problems
        # but check for obvious infinite loops
        return not self._detect_obvious_loop(problem, context)
    
    def create_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
        """Create a workflow instance using LLM-generated Dana code."""
        # Implementation details below
```

### 2. Core Workflow Creation

```python
def create_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
    """Create a workflow instance for the problem."""
    
    # 1. Check recursion depth limits
    if not self._check_depth_limits(context):
        return self._create_base_case_workflow(problem, context)
    
    # 2. Generate LLM prompt with rich computable context
    prompt = self._build_enhanced_analysis_prompt(problem, context)
    
    # 3. Get LLM response (Dana code)
    dana_code = self._get_llm_response(prompt)
    
    # 4. Validate and compile Dana code
    compiled_function = self._compile_dana_code(dana_code, context)
    
    # 5. Create WorkflowInstance with parent reference
    return self._create_workflow_instance(problem, context, compiled_function)
```

### 3. Enhanced LLM Prompt Generation

The strategy generates comprehensive prompts using the Context Engineering Framework:

```python
def _build_enhanced_analysis_prompt(self, problem: str, context: ProblemContext) -> str:
    """Build the LLM analysis prompt with rich computable context."""
    
    # Get the workflow instance from context
    workflow_instance = context.workflow_instance
    
    # Compute rich context from execution data
    complexity_indicators = self.computable_context.get_complexity_indicators(context, workflow_instance._global_event_history)
    constraint_violations = self.computable_context.get_constraint_violations(context, workflow_instance._global_event_history)
    successful_patterns = self.computable_context.get_successful_patterns(context, workflow_instance._global_event_history)
    
    # Get recent events from global history
    recent_events = workflow_instance._global_event_history.get_events_by_type("workflow_start")[-5:]
    
    # Get parent context if available
    parent_context = ""
    if workflow_instance._parent_workflow:
        parent_context = f"""
PARENT CONTEXT:
- Problem: {workflow_instance._parent_workflow._problem_statement}
- Objective: {workflow_instance._parent_workflow._objective}
- Depth: {workflow_instance._parent_workflow._problem_context.depth}
- Success Patterns: {', '.join(self.computable_context.get_successful_patterns(workflow_instance._parent_workflow._problem_context, workflow_instance._parent_workflow._global_event_history))}
"""
    
    # Use Context Engineering Framework for optimal prompt generation
    from dana.frameworks.ctxeng import ContextEngine
    
    context_engine = ContextEngine.from_agent(workflow_instance._agent_instance)
    
    # Assemble rich context using ctxeng framework
    rich_prompt = context_engine.assemble(
        problem,
        context={
            "complexity_indicators": complexity_indicators,
            "constraint_violations": constraint_violations,
            "successful_patterns": successful_patterns,
            "recent_events": recent_events,
            "parent_context": parent_context
        },
        template="problem_solving"
    )
    
    # rich_prompt now contains structured XML with optimized context
    return rich_prompt
```

### 4. Context Engineering Framework Integration

The Recursive Strategy integrates with the Context Engineering Framework to provide:

#### **Enhanced Prompt Generation**
- **Structured XML Output**: LLM receives well-structured, parseable prompts
- **Relevance Optimization**: Only relevant context pieces are included
- **Token Efficiency**: Automatic length optimization reduces token usage
- **Template Consistency**: Standardized prompt structure across all recursive calls

#### **Integration Benefits**
- **Better LLM Performance**: Structured prompts improve problem decomposition
- **Context Relevance**: Multi-factor relevance scoring ensures optimal context
- **Recursive Context**: Rich context flows through recursive `agent.solve()` calls
- **Template Management**: Problem-solving template automatically selected
- **Zero Configuration**: Auto-discovery of agent resources and workflows

#### **Context Flow in Recursion**
```
Level 0: agent.solve("Plan trip to Mexico")
  ↓ Uses ctxeng framework for rich context
  ↓ LLM generates Dana code with agent.solve() calls
  
Level 1: agent.solve("Research destinations")
  ↓ Inherits context from parent + adds new context
  ↓ Uses ctxeng framework for enhanced context
  ↓ LLM continues with rich context
  
Level 2: agent.solve("Find safety information")
  ↓ Builds on full context chain
  ↓ ctxeng optimizes context for current depth
  ↓ Maximum context relevance maintained
```

PROBLEM: {problem}
OBJECTIVE: {context.objective}
DEPTH: {context.depth}

COMPUTED CONTEXT:
- Sub-problems attempted: {complexity_indicators['sub_problem_count']}
- Total execution time: {complexity_indicators['execution_time_total']:.2f}s
- Error rate: {complexity_indicators['error_rate']:.1%}
- Max depth reached: {complexity_indicators['max_depth_reached']}

CONSTRAINTS: {', '.join(context.constraints.get('hard', []))}
ASSUMPTIONS: {', '.join(context.assumptions[:3])}

LEARNING FROM EXECUTION:
- Constraint violations: {', '.join(constraint_violations[:2])}
- Successful patterns: {', '.join(successful_patterns)}
- Recent events: {self._format_recent_events(recent_events)}

{parent_context}

AVAILABLE FUNCTIONS:
- agent.output(result): Specify final result when problem is solved
- agent.solve(sub_problem, objective): Solve a sub-problem recursively
- agent.input(prompt): Get user input during problem solving
- agent.reason(thought): Express natural language reasoning

RECURSION RULES:
- You can call agent.solve() for sub-problems
- Pass the workflow_instance in kwargs
- Each recursive call increases depth by 1
- Maximum depth is {self.max_depth}

STRATEGY GUIDANCE:
Based on the computed context above, consider:
1. What patterns have been successful so far?
2. What constraints have been violated?
3. How complex is this problem becoming?
4. What can we learn from recent actions?

Generate Dana code that solves: {problem}
"""
    
    return prompt
```

### 4. Dana Code Compilation

The strategy compiles LLM-generated Dana code into executable functions:

```python
def _compile_dana_code(self, dana_code: str, context: ProblemContext) -> ComposedFunction:
    """Compile Dana code to a ComposedFunction."""
    
    try:
        # 1. Clean and validate the code
        cleaned_code = self._clean_dana_code(dana_code)
        
        # 2. Parse the Dana code
        ast = self._parse_dana_code(cleaned_code)
        
        # 3. Validate function calls
        self._validate_function_calls(ast, context)
        
        # 4. Compile to ComposedFunction
        compiled_function = self._compile_ast_to_function(ast, context)
        
        # 5. Validate the compiled function
        self._validate_compiled_function(compiled_function, context)
        
        return compiled_function
        
    except Exception as e:
        # Fallback to a simple output function
        return self._create_fallback_function(problem, context, str(e))
```

### 5. Workflow Instance Creation

```python
def _create_workflow_instance(
    self, 
    problem: str, 
    context: ProblemContext, 
    compiled_function: ComposedFunction
) -> WorkflowInstance:
    """Create a WorkflowInstance with the compiled function."""
    
    # Get parent workflow if this is a recursive call
    parent_workflow = context.workflow_instance
    
    # Create workflow type
    workflow_type = self._create_workflow_type(problem)
    
    # Create workflow instance with minimal state carriers
    workflow = WorkflowInstance(
        struct_type=workflow_type,
        values={
            "composed_function": compiled_function,
            "problem_statement": problem,
            "objective": context.objective,
            "problem_context": context,
            "action_history": context.workflow_instance._global_action_history
        },
        parent_workflow=parent_workflow
    )
    
    return workflow
```

## LLM-Generated Dana Code Patterns

### 1. Direct Solution (No Recursion)

```dana
# Simple problem that can be solved directly
agent.reason("This is a straightforward calculation problem")

result = 42 * 2 + 10
agent.output(result)
```

### 2. Problem Decomposition (With Recursion)

```dana
# Break into sub-problems
agent.reason("I need to solve this in three steps: gather data, analyze, and synthesize")

# Step 1: Gather data
agent.reason("First, I need to collect the necessary data")
data = agent.solve(
    "Collect user data from database", 
    "Retrieve user profiles and preferences",
    workflow_instance=workflow_instance
)

# Step 2: Analyze data
agent.reason("Now I'll analyze the collected data")
analysis = agent.solve(
    "Analyze user behavior patterns", 
    "Identify patterns and insights from user data",
    workflow_instance=workflow_instance
)

# Step 3: Synthesize results
agent.reason("Finally, I'll combine the analysis into a solution")
final_result = {
    "insights": analysis["patterns"],
    "recommendations": analysis["recommendations"],
    "confidence": analysis["confidence_score"]
}

agent.output(final_result)
```

### 3. User Input Integration

```dana
# Need user input to proceed
agent.reason("I need to know the user's preferences to continue")

preferences = agent.input("What are your preferences for this solution? (e.g., speed vs accuracy)")

# Use input to solve
agent.reason(f"Now I can solve the problem with user preferences: {preferences}")

result = agent.solve(
    "Solve based on user preferences", 
    "Optimize solution according to user preferences",
    workflow_instance=workflow_instance
)

agent.output(result)
```

### 4. Complex Multi-Step Problem

```dana
# Complex problem requiring multiple recursive calls
agent.reason("This is a complex optimization problem that requires multiple approaches")

# Phase 1: Initial analysis
agent.reason("First, I'll analyze the problem structure")
problem_structure = agent.solve(
    "Analyze problem structure and identify components",
    "Break down the problem into manageable components",
    workflow_instance=workflow_instance
)

# Phase 2: Parallel sub-problem solving
agent.reason("Now I'll solve the main components in parallel")

component_a = agent.solve(
    "Solve component A optimization",
    "Optimize component A according to constraints",
    workflow_instance=workflow_instance
)

component_b = agent.solve(
    "Solve component B optimization", 
    "Optimize component B according to constraints",
    workflow_instance=workflow_instance
)

# Phase 3: Integration
agent.reason("Finally, I'll integrate the component solutions")
integrated_solution = agent.solve(
    "Integrate component solutions into final result",
    "Combine optimized components into final solution",
    workflow_instance=workflow_instance
)

agent.output(integrated_solution)
```

## Recursion Control Mechanisms

### 1. Depth Limit Enforcement

```python
def _check_depth_limits(self, context: ProblemContext) -> bool:
    """Check if recursion depth limits have been reached."""
    
    # Check absolute depth limit
    if context.depth >= self.max_depth:
        return False
    
    # Check for rapid depth increases
    if self._detect_rapid_depth_increase(context):
        return False
    
    return True
```

### 2. Logical Loop Detection

```python
def _detect_logical_loop(self, problem: str, context: ProblemContext) -> bool:
    """Detect logical loops in problem solving."""
    
    # Check for identical problem statements
    if self._is_identical_problem(problem, context):
        return True
    
    # Check for circular problem patterns
    if self._has_circular_pattern(problem, context):
        return True
    
    # Check for repetitive action patterns using computable context
    workflow_instance = context.workflow_instance
    if workflow_instance:
        action_history = workflow_instance._global_action_history
        recent_actions = action_history.get_recent_actions(10)
        
        # Check for repetitive patterns in recent actions
        if self._has_repetitive_actions(recent_actions):
            return True
    
    return False
```

### 3. Base Case Handling

```python
def _create_base_case_workflow(self, problem: str, context: ProblemContext) -> WorkflowInstance:
    """Create a workflow for base cases (max depth reached)."""
    
    # Create a simple output function
    base_function = self._create_base_case_function(problem, context)
    
    # Create workflow instance
    workflow = WorkflowInstance(
        struct_type=self._create_workflow_type(problem),
        values={
            "composed_function": base_function,
            "problem_statement": f"Base case: {problem}",
            "objective": context.objective,
            "problem_context": context,
            "action_history": context.workflow_instance._global_action_history
        },
        parent_workflow=context.workflow_instance._parent_workflow
    )
    
    return workflow
```

## Error Handling and Recovery

### 1. LLM Response Validation

```python
def _validate_llm_response(self, response: str) -> bool:
    """Validate that the LLM response contains valid Dana code."""
    
    # Check for basic structure
    if not response or len(response.strip()) < 10:
        return False
    
    # Check for required function calls
    required_functions = ['agent.output', 'agent.solve', 'agent.input', 'agent.reason']
    has_required_function = any(func in response for func in required_functions)
    
    if not has_required_function:
        return False
    
    # Check for basic syntax patterns
    if not self._has_valid_syntax_patterns(response):
        return False
    
    return True
```

### 2. Compilation Error Recovery

```python
def _handle_compilation_error(self, error: Exception, problem: str, context: ProblemContext) -> ComposedFunction:
    """Handle compilation errors by creating a fallback function."""
    
    # Log the compilation error
    self._log_compilation_error(error, problem, context)
    
    # Create a simple fallback function
    fallback_code = f"""
agent.reason("Failed to compile complex solution, using fallback approach")
agent.output("Unable to solve {problem} due to compilation error: {str(error)}")
"""
    
    try:
        return self._compile_dana_code(fallback_code, context)
    except Exception:
        # Ultimate fallback
        return self._create_ultimate_fallback_function(problem, context)
```

### 3. Runtime Error Handling

```python
def _handle_runtime_error(self, error: Exception, context: ProblemContext) -> Any:
    """Handle runtime errors during workflow execution."""
    
    # Log the runtime error
    self._log_runtime_error(error, context)
    
    # Check if we can retry with a simpler approach
    if self._can_retry_with_simpler_approach(error, context):
        return self._retry_with_simpler_approach(context)
    
    # Check if we can fall back to a different strategy
    if self._can_fallback_to_different_strategy(error, context):
        return self._fallback_to_different_strategy(context)
    
    # Re-raise the error if no recovery is possible
    raise error
```

## Performance Optimizations

### 1. Prompt Caching

```python
class PromptCache:
    """Cache for LLM prompts to avoid redundant calls."""
    
    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, str] = {}
        self._max_size = max_size
    
    def get_cached_response(self, problem: str, context: ProblemContext) -> str | None:
        """Get cached response for similar problems."""
        cache_key = self._generate_cache_key(problem, context)
        return self._cache.get(cache_key)
    
    def cache_response(self, problem: str, context: ProblemContext, response: str) -> None:
        """Cache a response for future use."""
        cache_key = self._generate_cache_key(problem, context)
        
        if len(self._cache) >= self._max_size:
            self._evict_oldest()
        
        self._cache[cache_key] = response
```

### 2. Parallel Sub-Problem Execution

```python
def _execute_parallel_sub_problems(self, sub_problems: list[tuple[str, str]], context: ProblemContext) -> list[Any]:
    """Execute independent sub-problems in parallel."""
    
    # Create tasks for parallel execution
    tasks = []
    for sub_problem, objective in sub_problems:
        task = asyncio.create_task(
            self._execute_sub_problem(sub_problem, objective, context)
        )
        tasks.append(task)
    
    # Execute all tasks in parallel
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            # Log and create fallback result
            self._log_parallel_execution_error(result, sub_problems[i], context)
            results[i] = self._create_fallback_result(sub_problems[i], context)
    
    return results
```

## Testing Strategy

### 1. Unit Tests

```python
class TestRecursiveStrategy:
    def test_can_handle(self):
        """Test strategy selection logic."""
        
    def test_create_workflow(self):
        """Test workflow creation process."""
        
    def test_enhanced_llm_prompt_generation(self):
        """Test enhanced LLM prompt building with computable context."""
        
    def test_dana_code_compilation(self):
        """Test Dana code compilation."""
        
    def test_recursion_control(self):
        """Test recursion depth limits."""
        
    def test_loop_detection(self):
        """Test infinite loop detection."""
        
    def test_context_integration(self):
        """Test integration with context engineering system."""
```

### 2. Integration Tests

```python
class TestRecursiveStrategyIntegration:
    def test_end_to_end_recursive_solving(self):
        """Test complete recursive problem solving."""
        
    def test_context_propagation(self):
        """Test context propagation through recursion."""
        
    def test_error_recovery(self):
        """Test error handling and recovery."""
        
    def test_performance_optimizations(self):
        """Test caching and parallel execution."""
        
    def test_context_effectiveness(self):
        """Test that rich context improves LLM reasoning."""
```

### 3. Mock LLM Testing

```python
class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, responses: dict[str, str]):
        self.responses = responses
        self.call_count = 0
    
    async def generate(self, prompt: str) -> str:
        """Generate a mock response."""
        self.call_count += 1
        
        # Find the best matching response
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return response
        
        # Default response
        return "agent.output('Mock solution')"
```

## Configuration

### 1. Strategy-Specific Configuration

```python
@dataclass
class RecursiveStrategyConfig:
    max_depth: int = 10
    enable_loop_detection: bool = True
    enable_prompt_caching: bool = True
    enable_parallel_execution: bool = True
    compilation_timeout: int = 30
    llm_timeout: int = 60
    fallback_strategy: str = "iterative"
    enable_enhanced_context: bool = True  # Use Context Engineering Framework
```

### 2. Environment Variables

```bash
# Recursive Strategy Configuration
DANA_RECURSIVE_MAX_DEPTH=10
DANA_RECURSIVE_ENABLE_LOOP_DETECTION=true
DANA_RECURSIVE_ENABLE_PROMPT_CACHING=true
DANA_RECURSIVE_ENABLE_PARALLEL_EXECUTION=true
DANA_RECURSIVE_COMPILATION_TIMEOUT=30
DANA_RECURSIVE_LLM_TIMEOUT=60
DANA_RECURSIVE_ENABLE_ENHANCED_CONTEXT=true  # Use Context Engineering Framework
```

## Conclusion

The **Recursive Strategy** provides a powerful, flexible approach to problem-solving that leverages LLM capabilities while maintaining control through recursion limits and state management. By implementing the core architecture defined in `agent_solve.md` and leveraging the Context Engineering Framework (`dana.frameworks.ctxeng`), this strategy enables agents to:

- **Break down complex problems** into manageable sub-problems
- **Generate executable code** using LLM reasoning enhanced with rich context
- **Maintain context** throughout recursive problem decomposition
- **Prevent infinite loops** through multiple detection mechanisms
- **Recover from errors** with fallback strategies and error handling
- **Learn from execution** using computable context and pattern recognition

The strategy balances complexity with usability, providing agents with the tools they need to solve complex problems while preventing infinite loops and maintaining context throughout the problem-solving process. The integration with the Context Engineering Framework ensures that the LLM receives optimal information for reasoning, leading to better problem decomposition and more effective recursive solutions.
