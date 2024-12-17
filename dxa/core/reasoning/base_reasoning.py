"""Base reasoning system with integrated planning and execution.

The DXA reasoning system implements a two-layer architecture that separates strategic
planning from tactical execution. This separation allows the system to maintain
high-level objectives and adapt plans while efficiently executing individual steps.
Like a general commanding an army, the strategic layer makes high-level decisions
and adjusts plans, while the tactical layer handles the immediate execution and
reports back critical information.

Consider these scenarios and their implementations:

1. Simple Question-Answering:
   User: "What is quantum computing?"
   Implementation:
   - DirectReasoning subclass handles simple queries
   - Bypasses complex planning by creating single-step plan
   - Uses template-based prompting for consistent LLM interaction
   - Minimal state tracking and resource management
   ```python
   class DirectReasoning(BaseReasoning):
       async def _create_plan(self, objective):
           return Plan(steps=[{
               "action": "query",
               "prompt": self._create_prompt(objective)
           }])
   ```

2. Research Assistant:
   User: "Research recent breakthroughs in fusion energy"
   Implementation:
   - ChainOfThoughtReasoning manages multi-step research
   - Planning layer decomposes task into research steps
   - Each step can refine objective based on findings
   - Resources (search, analysis) managed tactically
   ```python
   class ResearchReasoning(BaseReasoning):
       async def _execute_step(self, step, context):
           if step.action == "search":
               results = await context.search.find(step.query)
               # Signal interesting findings back to planning
               if self._is_significant(results):
                   self._signal_discovery(results)
   ```

3. System Monitoring:
   User: "Monitor system health and respond to issues"
   Implementation:
   - OODAReasoning provides continuous observation loop
   - Planning maintains alert policies and thresholds
   - Tactical layer handles sensor reading and basic responses
   - Signals trigger plan updates for complex issues
   ```python
   class MonitorReasoning(BaseReasoning):
       async def _create_objective(self, task):
           return Objective(
               original=task,
               current=task,
               success_criteria=self._create_health_criteria(task)
           )
           
       async def _review_plan(self, result):
           if self._needs_escalation(result):
               return ReviewResult(
                   needs_update=True,
                   updated_item=self._create_response_plan(result)
               )
   ```

4. Code Generation:
   User: "Optimize this database query"
   Implementation:
   - DANAReasoning combines neural search with symbolic execution
   - Planning layer manages optimization strategy
   - Neural components find similar patterns
   - Symbolic components handle code generation and validation
   ```python
   class DANAReasoning(BaseReasoning):
       async def _create_plan(self, objective):
           similar_cases = await self._neural_search(objective)
           return Plan(steps=[
               {"action": "analyze", "target": objective.current},
               {"action": "synthesize", "patterns": similar_cases},
               {"action": "validate", "criteria": objective.constraints}
           ])
   ```

The architecture supports this spectrum through careful separation of concerns:
- BaseReasoning provides the core loop and state management
- Subclasses implement specific reasoning patterns
- Planning layer handles strategy and adaptation
- Tactical layer manages execution and resources
- Clear interfaces allow mixing and matching components

System Architecture
-----------------
1. Strategic Layer (Planning)
   Purpose: High-level control and adaptation
   
   Components:
   - Objective Manager
     * Interprets user intent
     * Refines objectives
     * Tracks success criteria
   
   - Plan Manager
     * Selects execution pattern
     * Creates/updates plans
     * Monitors overall progress
   
   - Resource Coordinator
     * Allocates resources
     * Manages capabilities
     * Ensures availability

2. Tactical Layer (Reasoning)
   Purpose: Direct execution and monitoring
   
   Components:
   - Executor
     * Runs reasoning steps
     * Manages resources
     * Reports progress
   
   - Monitor
     * Tracks execution
     * Detects issues
     * Signals updates

Objective Evolution
-----------------
1. Structure
   - Original intent
   - Current understanding
   - Success criteria
   - Constraints
   - Evolution history

2. Update Triggers
   From Planning:
   - User feedback
   - Strategic realignment
   - Resource constraints
   - Success criteria changes

   From Reasoning:
   - New discoveries
   - Technical blockers
   - Opportunity detection
   - Context changes

3. Evolution Process
   a. Signal Generation
      - Source identifies need
      - Packages evidence
      - Assigns priority
   
   b. Strategic Review
      - Evaluate significance
      - Check feasibility
      - Validate consistency
   
   c. Update Application
      - Record rationale
      - Update objective
      - Adjust criteria
      - Notify stakeholders

Plan Evolution
------------
1. Structure
   - Step sequence
   - Resource requirements
   - Progress metrics
   - Update history

2. Update Triggers
   From Planning:
   - Objective changes
   - Strategy shifts
   - Resource availability
   - Priority changes

   From Reasoning:
   - Step failures
   - Performance data
   - Resource issues
   - New approaches

3. Evolution Process
   a. Evaluation
      - Current validity
      - Performance review
      - Resource check
      - Alternative analysis
   
   b. Update Mechanism
      - Preserve progress
      - Update steps
      - Adjust resources
      - Record rationale

4. Consistency Management
   - Objective alignment
   - Resource validation
   - Progress preservation
   - History tracking

Extension Points
--------------
1. Custom Patterns
   - New reasoning strategies
   - Specialized workflows
   - Domain-specific handlers

2. Resource Integration
   - Tool integration
   - Custom capabilities
   - I/O handlers

Implementation Notes
------------------
1. Simple cases remain simple:
   - Direct reasoning is just one LLM call
   - Basic workflows are natural language → steps
   - Interactive modes use simple patterns

2. Complex cases are possible:
   - Full planning/reasoning cycle
   - Neural-symbolic integration
   - Multi-stage execution

3. User-Defined Workflows:
   - Natural language specifications
   - Runtime translation to plans
   - Flexible execution patterns

Core Concepts
------------
1. Reasoning Patterns (How to Think)
   Purpose: Define the cognitive approach
   
   Pure Patterns:
   - Direct: Single LLM query → response
   - Chain-of-Thought: Structured step-by-step thinking
   - OODA: Observe-Orient-Decide-Act loop
   - DANA: Neural search → symbolic execution
   
   Example:
   ```python
   # Pure reasoning pattern
   class OODAReasoning(ReasoningPattern):
       async def reason_about_step(self, step, context):
           observation = await self.observe(step.targets)
           orientation = await self.orient(observation)
           decision = await self.decide(orientation)
           action = await self.plan_action(decision)
           return action
   ```

2. Execution Strategies (How to Act)
   Purpose: Define the execution flow
   
   Pure Strategies:
   - Single-Shot: One request → one response
   - Iterative: Repeated try-evaluate-adjust
   - Continuous: Ongoing operation
   - Interactive: User-in-loop operation
   
   Example:
   ```python
   # Pure execution strategy
   class ContinuousStrategy(ExecutionStrategy):
       async def execute(self, reasoning, objective):
           while await self.should_continue(objective):
               step = await self.next_step()
               result = await reasoning.reason_about_step(step)
               yield result
   ```

3. Workflows (What to Do)
   Purpose: Define the task structure
   
   Pure Workflows:
   - Linear: Sequential steps
   - Branching: Decision-based paths
   - State Machine: Complex state transitions
   - Event-Driven: Response patterns
   
   Example:
   ```python
   # Pure workflow definition
   monitoring_workflow = Workflow({
       "type": "state_machine",
       "states": {
           "monitoring": {
               "actions": ["check_metrics"],
               "transitions": {
                   "alert_triggered": "responding",
                   "normal": "monitoring"
               }
           },
           "responding": {
               "actions": ["evaluate", "act"],
               "transitions": {
                   "resolved": "monitoring",
                   "escalate": "alerting"
               }
           }
       }
   })
   ```

Integration Model
---------------
1. Composition (not Inheritance)
   - Agents combine patterns, strategies, and workflows
   - Each component remains pure and focused
   - Mix and match based on needs

2. Example Combinations:
   a. System Monitoring
      - Pattern: OODA Reasoning (how to think)
      - Strategy: Continuous Execution (how to act)
      - Workflow: State Machine (what to do)
   
   b. Research Assistant
      - Pattern: Chain-of-Thought Reasoning
      - Strategy: Iterative Execution
      - Workflow: Branching Tasks
   
   c. Chat Bot
      - Pattern: Direct Reasoning
      - Strategy: Interactive Execution
      - Workflow: Event-Driven
"""