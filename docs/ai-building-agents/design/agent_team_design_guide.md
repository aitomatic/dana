# STARAgent Team Design Methodology

## Overview

This guide provides a systematic methodology for designing STARAgent specialist teams to solve complex domain problems. The methodology emphasizes composition, specialization, and deterministic workflow orchestration to create maintainable, performant, and focused agent systems.

## Core Principles

### 1. Compositional Hierarchy

```
Agent (Prompt-driven behavior)
  ├─> Sub-Agents (Specialists)
  ├─> Workflows (Deterministic orchestration)
  └─> Resources (Domain-agnostic capabilities)

Workflow (Deterministic logic)
  ├─> Other Workflows (Composition)
  └─> Resources (External capabilities)

Resource (Stateless capability)
  └─> Other Resources (Internal composition)
```

**Key Rule**: Maintain this hierarchy to preserve order while affording complexity.

### 2. Domain Expertise Layering

- **Agents**: Domain-specific identity, roles, and decision-making
- **Workflows**: Domain-specific orchestration, business logic, and determinism
- **Resources**: Domain-agnostic capabilities (mostly reusable across domains)

**Why This Matters**:
- Resources can be broadly reused (e.g., `ConversationResource` works for interviews, support, analysis)
- Workflows encode domain logic and can be composed for new use cases
- Agents provide the specialized interface and behavior for specific problems

### 3. Determinism Through Workflows

Pure LLM-based approaches lack the determinism required for production systems. Workflows provide:
- **Predictable execution paths**: Known steps, known order
- **Reliable error handling**: Explicit fallbacks and validation
- **Testable logic**: Each workflow step can be verified independently
- **Observable behavior**: Clear progression through defined phases

### 4. Specialization and Load Distribution

Multi-agent systems offer:
- **Focus**: Each agent has a narrow, well-defined responsibility
- **Performance**: Smaller, focused prompts perform better than monolithic ones
- **Parallelism**: Independent agents can work concurrently
- **Maintainability**: Changes to one specialist don't affect others
- **Load Distribution**: Avoid overly large system prompts that degrade performance

## Design Process

### Phase 1: Problem Analysis

#### 1.1 Define the Problem Domain

Start by clearly articulating:
- **What problem needs to be solved?**
- **Who are the users/stakeholders?**
- **What are the success criteria?**
- **What are the constraints?** (latency, accuracy, cost, safety)

**Example: Data Analysis Agent**
- Problem: Analysts need to reason through data analysis tasks and execute them in Python
- Users: Data scientists, analysts, researchers
- Success: Correct analysis, clear reasoning, reproducible code
- Constraints: Must explain reasoning, code must be safe, handle pandas/numpy/matplotlib

**Example: Maritime Navigation Agent**
- Problem: Ship captains need real-time navigation assistance in varying conditions
- Users: Ship captains, navigation officers
- Success: Safe route planning, regulatory compliance, weather adaptation
- Constraints: Real-time decision making, regulatory adherence, safety-critical

#### 1.2 Identify Core Capabilities Required

Break down the problem into capabilities:
- What external systems need to be accessed? (APIs, databases, sensors)
- What cognitive tasks are needed? (analysis, reasoning, classification)
- What workflows/processes need orchestration?
- What domain knowledge is required?

**Example: Data Analysis Agent**
- Reasoning about analysis approach
- Python code generation
- Code execution in safe environment
- Pandas/numpy operations
- Data visualization
- Result interpretation

**Example: Maritime Navigation Agent**
- Weather data access
- Navigation charts and routes
- Maritime law/regulation knowledge
- Route optimization
- Risk assessment
- Communication protocols

### Phase 2: Component Identification

#### 2.1 Identify Reusable Resources

Look for domain-agnostic capabilities in the existing resource library:

**Ask yourself:**
- Is this a general capability that could work across domains?
- Does a similar resource already exist?
- Could this resource be useful for other agents?

**Common Reusable Resources:**
- `ConversationResource`: Topic extraction, intent detection, summarization
- `SearchResource`: Web search, ranking, filtering
- `LLMResource`: General LLM capabilities for reasoning
- `FileResource`: File operations
- `DatabaseResource`: Data storage and retrieval

**Example: Data Analysis Agent**
- **Reuse**: `ConversationResource` (for understanding user intent)
- **Create**: `PythonExecutionResource` (safe code execution)
- **Create**: `DataFrameResource` (pandas operations, schema inference)

**Example: Maritime Navigation Agent**
- **Reuse**: `SearchResource` (for regulation lookups)
- **Create**: `WeatherDataResource` (weather APIs)
- **Create**: `NavigationChartResource` (chart data, routes)
- **Create**: `MaritimeRegulationResource` (compliance checking)

#### 2.2 Identify Required Workflows

Workflows encode domain-specific orchestration logic:

**Ask yourself:**
- What multi-step processes need to happen?
- Where is determinism critical?
- What are the decision points?
- What can be parallelized vs must be sequential?

**Workflow Design Triggers:**
- Multiple steps with clear dependencies
- Need for error handling and fallbacks
- Parallel operations for performance
- Complex data flow between operations
- Domain-specific business logic

**Example: Data Analysis Agent**
- **Create**: `AnalysisReasoningWorkflow` (reason about approach before coding)
- **Create**: `PythonAnalysisWorkflow` (write code → validate → execute → interpret)
- **Create**: `DataValidationWorkflow` (validate data quality before analysis)

**Example: Maritime Navigation Agent**
- **Create**: `RouteplanningWorkflow` (analyze conditions → plan route → validate compliance)
- **Create**: `WeatherAssessmentWorkflow` (fetch data → analyze risk → recommend actions)
- **Create**: `ComplianceCheckWorkflow` (check regulations → flag violations → suggest corrections)

#### 2.3 Identify Required Agents

Agents provide specialized interfaces and behaviors:

**Ask yourself:**
- Are there distinct roles or specializations needed?
- Is there a coordination role vs specialist roles?
- Would multiple agents enable parallel work?
- Does the problem benefit from peer collaboration?

**Agent Architecture Patterns:**

**Single Specialist**: One agent with focused workflows/resources
```
DataAnalysisAgent
  └─> AnalysisReasoningWorkflow
  └─> PythonAnalysisWorkflow
  └─> PythonExecutionResource
  └─> DataFrameResource
```

**Peer Collaboration**: Multiple specialists working together
```
NavigationPlanningAgent (route planning)
WeatherAnalysisAgent (weather assessment)
ComplianceAgent (regulatory checking)
```

**Hierarchical**: Coordinator + specialists
```
MaritimeNavigationCoordinator
  ├─> NavigationPlanningAgent
  ├─> WeatherAnalysisAgent
  └─> ComplianceAgent
```

### Phase 3: Specialization Decomposition

#### 3.1 Define Agent Identities

Each agent needs two forms of identity:

**PUBLIC_DESCRIPTION**: How the agent appears to other agents and users
- What the agent does
- When to use this agent
- What problems it solves
- Key capabilities

**IDENTITY**: How the agent sees itself and behaves
- Role and personality
- Decision-making approach
- Constraints and boundaries
- Operating principles

**Example: DataAnalysisAgent**
```
<PUBLIC_DESCRIPTION>
Data Analysis Agent specializes in reasoning through data analysis tasks
and executing them in Python. Use this agent for:
- Exploratory data analysis
- Statistical analysis
- Data visualization
- Pandas/numpy operations
The agent explains its reasoning before generating code.
</PUBLIC_DESCRIPTION>

<IDENTITY>
You are a data analysis specialist who thinks carefully before coding.
You always:
- Reason through the analysis approach first
- Explain your analytical strategy
- Write clean, well-commented Python code
- Validate data before analysis
- Interpret results clearly
You are methodical, thorough, and pedagogical.
</IDENTITY>
```

#### 3.2 Define Agent Scope

For each agent, clearly define:

**Responsibilities**: What the agent IS responsible for
**Non-responsibilities**: What the agent is NOT responsible for (equally important!)
**Dependencies**: What the agent depends on (data, other agents, resources)
**Outputs**: What the agent produces

**Example: WeatherAnalysisAgent**
```
Responsibilities:
- Fetch current weather data for maritime routes
- Assess weather-related risks (storms, fog, waves)
- Recommend routing adjustments based on weather
- Track weather changes during voyage

Non-responsibilities:
- Does NOT make final route decisions (that's NavigationPlanningAgent)
- Does NOT check regulatory compliance (that's ComplianceAgent)
- Does NOT execute navigation commands

Dependencies:
- WeatherDataResource for API access
- Current vessel position and route
- Risk tolerance parameters

Outputs:
- Weather assessment report
- Risk score (low/medium/high/critical)
- Recommended route adjustments
- Weather monitoring alerts
```

### Phase 4: Composition Strategy

#### 4.1 Workflow Orchestration Patterns

Choose the right pattern for each workflow:

**Sequential Pattern**: Steps must happen in order
```python
workflow = (
    Step1_Workflow()
    | Step2_Workflow()  # Waits for Step1
    | Step3_Workflow()  # Waits for Step2
)
```

**Use when**: Each step depends on previous results

**Parallel Pattern**: Independent operations
```python
async def parallel_phase():
    results = await asyncio.gather(
        operation1(),
        operation2(),
        operation3()
    )
    return results
```

**Use when**: Operations are independent, want speed

**Phased Pattern**: Parallel → Sequential
```python
# Phase 1: Parallel gathering
async def phase1():
    return await asyncio.gather(
        gather_data1(),
        gather_data2(),
    )

data1, data2 = asyncio.run(phase1())

# Phase 2: Sequential processing
result = (
    ProcessWorkflow()
    | AnalyzeWorkflow()
    | SynthesizeWorkflow()
).execute(data1=data1, data2=data2)
```

**Use when**: Need speed for independent operations, then ordered processing

#### 4.2 Agent Composition

Build agents through composition:

```python
class DataAnalysisAgent(STARAgent):
    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="data-analyst",
            agent_id=agent_id or "data-analyst",
            **kwargs
        )

        self.with_workflows(
            AnalysisReasoningWorkflow(workflow_id="analysis-reasoning"),
            PythonAnalysisWorkflow(workflow_id="python-analysis"),
            DataValidationWorkflow(workflow_id="data-validation"),
        ).with_resources(
            PythonExecutionResource(resource_id="python-executor"),
            DataFrameResource(resource_id="dataframe-ops"),
            ConversationResource(resource_id="conversation"),
        )
```

**Key Points:**
- Keep agent code minimal (mostly configuration)
- Compose existing capabilities
- Clear, focused identity
- Explicit resource and workflow registration

#### 4.3 Multi-Agent Coordination

For multi-agent systems, choose a coordination pattern:

**Pattern 1: Peer Collaboration (No Coordinator)**
- Agents communicate directly
- Each agent knows about relevant peers
- Suitable for simple collaboration

```python
class NavigationPlanningAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="navigation-planner", **kwargs)

        self.with_agents(
            WeatherAnalysisAgent(),  # Can call for weather info
            ComplianceAgent(),       # Can call for compliance check
        )
```

**Pattern 2: Hierarchical (Coordinator + Specialists)**
- Coordinator agent manages specialists
- Specialists focus on their domain
- Coordinator handles routing and synthesis

```python
class MaritimeNavigationCoordinator(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="maritime-coordinator", **kwargs)

        self.with_agents(
            NavigationPlanningAgent(),
            WeatherAnalysisAgent(),
            ComplianceAgent(),
        )
    # Coordinator's prompt instructs it to delegate to specialists
```

### Phase 5: Validation and Refinement

#### 5.1 Design Validation Checklist

Before implementation, validate your design:

**Component Reusability**
- [ ] Are resources domain-agnostic where possible?
- [ ] Could workflows be reused for similar problems?
- [ ] Is the agent specialized enough to be focused but general enough to be useful?

**Composition Clarity**
- [ ] Is the hierarchy clear (Agent → Workflow → Resource)?
- [ ] Are dependencies explicit?
- [ ] Can components be tested independently?

**Specialization**
- [ ] Does each agent have a clear, focused role?
- [ ] Are responsibilities and non-responsibilities well-defined?
- [ ] Is the scope appropriate (not too broad, not too narrow)?

**Determinism**
- [ ] Are critical paths deterministic (using workflows)?
- [ ] Is error handling explicit?
- [ ] Are validation points clear?

**Performance**
- [ ] Are parallel operations identified?
- [ ] Are system prompts appropriately sized?
- [ ] Is load distributed across agents?

#### 5.2 Common Design Pitfalls

**Pitfall 1: Overly Broad Agent Scope**
- **Problem**: Agent tries to do too much, resulting in bloated prompts and poor performance
- **Solution**: Decompose into multiple specialized agents

**Pitfall 2: Domain-Specific Resources**
- **Problem**: Creating resources that are too specific to reuse
- **Solution**: Extract the domain-agnostic capability; put domain logic in workflows

**Pitfall 3: Insufficient Determinism**
- **Problem**: Relying on LLM for critical decision paths that need reliability
- **Solution**: Use workflows for deterministic logic; use LLM for reasoning and generation

**Pitfall 4: Unclear Agent Boundaries**
- **Problem**: Multiple agents with overlapping responsibilities
- **Solution**: Clearly define responsibilities and non-responsibilities for each agent

**Pitfall 5: Over-Engineering**
- **Problem**: Creating too many components for simple problems
- **Solution**: Start simple; add specialization as complexity demands

## Design Templates

### Template 1: Single Specialist Agent

**Use when**: Problem has focused scope, single domain, no need for multiple perspectives

**Structure**:
```
SpecialistAgent
  ├─> Domain-specific Workflows (2-4)
  ├─> Domain-specific Resources (1-3)
  └─> Reused Resources (1-3)
```

**Example**: DataAnalysisAgent, WebResearchAgent

### Template 2: Multi-Agent Peer Collaboration

**Use when**: Problem requires multiple perspectives, agents can work independently, need parallelism

**Structure**:
```
SpecialistAgent1 ← → SpecialistAgent2 ← → SpecialistAgent3
(Each agent can call others directly)
```

**Example**: Research + Analysis + Verification agents working on investigation

### Template 3: Hierarchical Coordination

**Use when**: Problem requires orchestration, synthesis of multiple specialist outputs, complex routing

**Structure**:
```
CoordinatorAgent
  ├─> SpecialistAgent1
  ├─> SpecialistAgent2
  └─> SpecialistAgent3
```

**Example**: DanaAgent (coordinator) managing domain specialists

### Template 4: Workflow-Heavy Application

**Use when**: Problem is deterministic with clear steps, minimal agent-to-agent communication needed

**Structure**:
```
OrchestrationWorkflow
  ├─> Phase1: Parallel resource calls
  ├─> Phase2: Sequential processing
  └─> Phase3: Synthesis
```

**Example**: Expert Interview Application (minimal agent coordination, heavy workflow orchestration)

## Key Success Patterns

### Pattern 1: Composition Over Creation
- **Principle**: Reuse existing resources and workflows whenever possible
- **Evidence**: Expert Interview achieved 90% code reduction by composing existing components
- **Application**: Always check the library before creating new components

### Pattern 2: Domain-Agnostic Resources
- **Principle**: Resources should be capability-focused, not domain-focused
- **Evidence**: ConversationResource works across interviews, support, analysis, etc.
- **Application**: Extract the general capability; leave domain logic to workflows

### Pattern 3: Phased Orchestration
- **Principle**: Combine parallel gathering with sequential processing
- **Evidence**: Expert Interview workflow parallelizes topic extraction + insight analysis, then sequences gap detection + question generation
- **Application**: Identify independent operations (parallelize) and dependent operations (sequence)

### Pattern 4: Minimal Agent Code
- **Principle**: Agents should be mostly configuration and composition
- **Evidence**: All successful agents are 15-40 lines of code
- **Application**: If agent code is >100 lines, extract logic into workflows or resources

### Pattern 5: Clear Identity Definition
- **Principle**: Both PUBLIC_DESCRIPTION and IDENTITY are essential
- **Evidence**: All successful agents have both forms clearly defined
- **Application**: Write both before implementing the agent

## Common Pitfalls to Avoid

### 1. Wrong Entry Point (No Autonomy)
**Problem**: Using hardcoded methods that bypass the STAR loop, resulting in no agent autonomy.

**❌ Anti-pattern**:
```python
# Bypasses STAR loop - no autonomy
result = agent.research_companies(provinces=["Đắk Lắk"])
```

**✅ Solution**:
```python
# Uses STAR loop - full autonomy
result = agent.query(caller_message="research companies in Đắk Lắk")
agent.converse(initial_message="research companies in Đắk Lắk")
agent.research_coffee_companies()  # Magic function
```

**Why This Matters**: The STAR loop is what makes agents autonomous. Bypassing it removes all reasoning and adaptation capability.

### 2. Composition vs. Programmatic Confusion
**Problem**: Assuming `with_workflows()` gives programmatic access to workflows.

**❌ Anti-pattern**:
```python
# This doesn't work - composition is for LLM tool selection
result = self.execute_workflow("my-workflow", params)
```

**✅ Solution**:
```python
# For LLM tool selection (composition)
self.with_workflows(MyWorkflow(workflow_id="my-workflow"))

# For programmatic use (direct instantiation)
workflow = MyWorkflow()
result = workflow.execute(params)
```

**Why This Matters**: Composition is for LLM tool selection, not programmatic access. Use direct instantiation for code.

### 3. Missing Intuitive Interface
**Problem**: Complex `query(caller_message="...")` syntax is not user-friendly.

**❌ Anti-pattern**:
```python
# Complex, not intuitive
result = agent.query(caller_message="research coffee companies in Đắk Lắk")
```

**✅ Solution**:
```python
# Implement magic function for intuitive interface
def __getattr__(self, name: str):
    def magic_method(*args, **kwargs):
        natural_language = name.replace("_", " ").strip()
        return self.converse(initial_message=natural_language)
    return magic_method

# Now this works naturally:
agent.research_coffee_companies()  # -> converse("research coffee companies")
```

**Why This Matters**: Intuitive interfaces make agents accessible and user-friendly.

### 4. Hardcoded Provider Selection
**Problem**: Hardcoding specific LLM providers instead of using auto-selection.

**❌ Anti-pattern**:
```python
# Hardcoded provider
llm = LLM(provider="anthropic")
```

**✅ Solution**:
```python
# Auto-select by priority
llm = LLM()  # Uses config priority order
```

**Why This Matters**: Auto-selection provides flexibility and follows configuration priorities.

### 5. Async Event Loop Conflicts
**Problem**: Calling `asyncio.run()` within an existing event loop.

**❌ Anti-pattern**:
```python
# This causes "Event loop is closed" errors
result = asyncio.run(some_async_function())
```

**✅ Solution**:
```python
# Use await in async context
result = await some_async_function()

# Or use mock data for demos
result = generate_mock_data()
```

**Why This Matters**: Event loop conflicts cause hangs and errors in production.

## Next Steps

After completing the design:

1. **Review** the design with stakeholders
2. **Prototype** one workflow/resource to validate approach
3. **Iterate** on the design based on prototype learnings
4. **Implement** incrementally (resources → workflows → agents)
5. **Test** each component independently
6. **Integrate** and test the full system
7. **Monitor** and refine based on real usage

## Related Documents

- [Agent Design Patterns](./agent_design_patterns.md) - Practical patterns from successful agents
- [Workflow Design Patterns](./workflow_design_patterns.md) - Workflow orchestration techniques
- [Resource Design Patterns](./resource_design_patterns.md) - Resource design best practices
- [Implementation Pitfalls](./implementation_pitfalls.md) - Common mistakes and fixes from real implementations
- [Examples](./examples/) - Worked examples applying this methodology
