# Agent Design Patterns

## Overview

This document catalogs proven agent design patterns extracted from successful implementations in the Dana framework. Each pattern includes the problem it solves, the structure it uses, real examples, and guidance on when to apply it.

## Pattern Catalog

### Pattern 1: Single Specialist Agent

**Intent**: Create a focused agent for a specific domain task

**Problem**: Need an agent that excels at one particular type of task without the complexity of multi-agent coordination

**Structure**:
```python
class SpecialistAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="specialist-type",
            agent_id="specialist-id",
            **kwargs
        )

        self.with_workflows(
            DomainWorkflow1(),
            DomainWorkflow2(),
        ).with_resources(
            DomainResource1(),
            GenericResource1(),
        )
```

**Characteristics**:
- Single, focused responsibility
- 2-5 workflows for domain tasks
- 2-5 resources (mix of domain-specific and reusable)
- Minimal code (~30-50 lines)
- Clear identity in prompt file

**Real Example**: WebResearchAgent (`dana/lib/agents/web_research.py`)

```python
class WebResearchAgent(STARAgent):
    """
    Prompt-driven agent for web research and information synthesis.
    """

    def __init__(self, agent_id: str | None = None, **kwargs):
        super().__init__(
            agent_type="web-researcher",
            agent_id=agent_id or "web-researcher",
            **kwargs
        )

        self.with_workflows(
            GoogleLookupWorkflow(workflow_id="google-lookup"),
            FactFindingWorkflow(workflow_id="fact-finding"),
        ).with_resources(
            SearchResource(resource_id="web-search"),
            WorkflowSelectorResource(resource_id="workflow-selector"),
        )
```

**When to Use**:
- Problem has clear, focused scope
- Single domain expertise required
- No need for multi-agent coordination
- Task can be solved with 2-5 workflows

**Anti-patterns**:
- Agent trying to do too many different things
- Workflows from completely different domains
- Agent code exceeding 100 lines

---

## Entry Point Patterns

### Pattern: Autonomous Entry Points (Recommended)

**Intent**: Provide intuitive interfaces that leverage agent autonomy through STAR loop

**Problem**: Need natural, intuitive ways to interact with agents while maintaining full autonomy

**Structure**:
```python
# ✅ Good - Full autonomy through STAR loop
result = agent.query(caller_message="research companies")
agent.converse(initial_message="research companies")
agent.research_companies()  # Magic function

# ❌ Bad - No autonomy, hardcoded workflow
result = agent.research_companies()  # Direct method call
```

**Characteristics**:
- Uses STAR loop for reasoning and tool selection
- Agent can adapt strategy based on results
- LLM chooses which workflows/resources to use
- Natural language interface

**When to Use**:
- User-facing interfaces
- Interactive applications
- When you want agent autonomy
- Complex, adaptive tasks

**Anti-patterns**:
- Hardcoded workflow execution
- Bypassing STAR loop
- No LLM reasoning
- Inflexible interfaces

---

### Pattern: Magic Function Interface

**Intent**: Convert method calls to natural language for intuitive agent interaction

**Problem**: Complex `query(caller_message="...")` syntax is not user-friendly

**Structure**:
```python
def __getattr__(self, name: str):
    """
    Magic function: Convert unknown method calls to natural language and call converse.

    Examples:
        agent.hi_how_are_you() -> converse("hi how are you")
        agent.research_coffee_companies() -> converse("research coffee companies")
        agent.find_exporters_in_dak_lak() -> converse("find exporters in dak lak")
    """
    def magic_method(*args, **kwargs):
        # Convert method name to natural language
        natural_language = name.replace("_", " ").strip()

        # Add any positional arguments as additional context
        if args:
            args_str = " ".join(str(arg) for arg in args)
            natural_language += f" {args_str}"

        # Add any keyword arguments as additional context
        if kwargs:
            kwargs_str = " ".join(f"{k}={v}" for k, v in kwargs.items())
            natural_language += f" {kwargs_str}"

        # Call converse with the natural language message
        return self.converse(initial_message=natural_language)

    return magic_method
```

**Characteristics**:
- Intuitive method names: `agent.research_coffee_companies()`
- Natural language conversion: `research_coffee_companies` → `"research coffee companies"`
- Argument support: `agent.find_exporters_in("Đắk Lắk")` → `"find exporters in Đắk Lắk"`
- Interactive conversation: Calls `converse()` for user interaction

**When to Use**:
- User-facing agent interfaces
- Interactive applications
- When you want natural method names
- Educational or demo purposes

**Examples**:
```python
# All of these work and start interactive conversations:
agent.hi_how_are_you()                    # -> converse("hi how are you")
agent.research_coffee_companies()         # -> converse("research coffee companies")
agent.find_exporters_in_dak_lak()         # -> converse("find exporters in dak lak")
agent.search_companies_in_province("Gia Lai") # -> converse("search companies in province Gia Lai")
```

**Anti-patterns**:
- Not implementing `__getattr__`
- Complex method signatures
- Non-intuitive naming
- Bypassing conversation interface

---

### Pattern 2: Hierarchical Coordinator

**Intent**: Orchestrate multiple specialist agents through a coordinator

**Problem**: Complex task requires multiple specialist perspectives with centralized decision-making and routing

**Structure**:
```python
class CoordinatorAgent(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(
            agent_type="coordinator",
            agent_id="coordinator-id",
            **kwargs
        )

        self.with_agents(
            SpecialistAgent1(),
            SpecialistAgent2(),
            SpecialistAgent3(),
        ).with_workflows(
            CoordinationWorkflow(),
        ).with_resources(
            GenericResource1(),
        )
```

**Characteristics**:
- Contains 2-5 specialist agents
- Minimal workflows (coordination logic)
- Prompt focuses on delegation and synthesis
- Routes user requests to appropriate specialists
- Synthesizes results from multiple specialists

**Real Example**: DanaAgent (`dana/apps/dana/dana_agent.py`)

```python
class DanaAgent(STARAgent):
    def __init__(self, thought_logger: ThoughtLogger, **kwargs):
        """Initialize Dana agent."""
        super().__init__(
            agent_id="dana_agent",
            agent_type="dana_agent",
            **kwargs
        )

        self.with_agents(
            WebResearchAgent(),
        ).with_workflows(
            GoogleLookupWorkflow(),
        ).with_resources(
            SearchResource(),
        ).with_notifiable(
            thought_logger,
        )
```

**Prompt Pattern** (`DanaAgent.xml`):
```
<PUBLIC_DESCRIPTION>
Dana is a conversational coordinator for multi-agent systems. Dana helps users:
- Discuss goals and translate them into structured actions
- Create, configure, and manage specialized agents
- Invoke resources and workflows to perform tasks
- Orchestrate multi-step, cross-agent operations
</PUBLIC_DESCRIPTION>

<IDENTITY>
You are Dana, a conversational coordinator for multi-agent systems. You help users
navigate complex tasks by breaking them down, delegating to appropriate agents,
and orchestrating the results into coherent outcomes.
</IDENTITY>

<THINKING_RULES>
You operate according to the STAR loop:
- SEE: Understand the user's request and current context
- THINK: Plan the approach and identify required agents/resources
- ACT: Execute the plan through structured tool calls
- REFLECT: Summarize outcomes and suggest next steps
</THINKING_RULES>
```

**When to Use**:
- Multiple specialists with distinct domains
- Need centralized routing and synthesis
- User shouldn't need to know which specialist to use
- Complex multi-step operations spanning specialists

**Anti-patterns**:
- Coordinator doing specialist work itself
- Too many specialists (>5-7 becomes hard to manage)
- Specialists that could work peer-to-peer

---

### Pattern 3: Peer Collaboration

**Intent**: Enable direct communication between specialist agents

**Problem**: Specialists need to work together without central coordination overhead

**Structure**:
```python
class SpecialistA(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="specialist-a", **kwargs)

        self.with_agents(
            SpecialistB(),  # Can call B directly
            SpecialistC(),  # Can call C directly
        ).with_workflows(
            SpecialistAWorkflow(),
        )

class SpecialistB(STARAgent):
    def __init__(self, **kwargs):
        super().__init__(agent_type="specialist-b", **kwargs)

        self.with_agents(
            SpecialistA(),  # Can call A directly
            SpecialistC(),  # Can call C directly
        ).with_workflows(
            SpecialistBWorkflow(),
        )
```

**Characteristics**:
- Agents reference each other as sub-agents
- Each agent knows who to call for what
- Direct communication (no coordinator)
- Suitable for 2-4 peer agents

**Real Example**: Test Multi-Agent Collaboration (`tests/live/agent/test_multi_agent_live.py`)

```python
class ResearchAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Research-focused STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <IDENTITY>
    You are a research agent for testing multi-agent scenarios.
    You focus on gathering and analyzing information.
    You are thorough and analytical.
    </IDENTITY>
    """
    ...

class AnalysisAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Analysis-focused STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <IDENTITY>
    You are an analysis agent for testing multi-agent scenarios.
    You focus on interpreting data and providing insights.
    You are analytical and strategic.
    </IDENTITY>
    """
    ...

class CoordinatorAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Coordinator STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <IDENTITY>
    You are a coordinator agent for testing multi-agent scenarios.
    You focus on managing and orchestrating multiple agents.
    You are organized and strategic.
    </IDENTITY>
    """
    ...
```

**When to Use**:
- Small number of specialists (2-4)
- Clear, simple interaction patterns
- No need for complex routing logic
- Agents have peer relationships

**Anti-patterns**:
- Too many peers (becomes spaghetti)
- Unclear responsibility boundaries
- Circular dependencies that cause confusion

---

### Pattern 4: Workflow-Heavy Application

**Intent**: Solve structured problems through workflow orchestration with minimal agent complexity

**Problem**: Problem is well-defined with clear steps; agent intelligence needed primarily for decision-making within workflow

**Structure**:
```python
# Minimal agent - mostly workflow orchestration
class ApplicationWorkflow(BaseWorkflow):
    """Main orchestration workflow"""

    def __init__(self, **kwargs):
        super().__init__(workflow_id="app-workflow", **kwargs)
        self.resource1 = Resource1()
        self.resource2 = Resource2()

    def _do_execute(self, **kwargs):
        # Phase 1: Parallel operations
        async def phase1():
            return await asyncio.gather(
                self.resource1.method1(**kwargs),
                self.resource2.method1(**kwargs),
            )

        result1, result2 = asyncio.run(phase1())

        # Phase 2: Sequential processing
        processed = self.resource1.method2(result1, result2)
        final = self.resource2.method2(processed)

        return final
```

**Characteristics**:
- Heavy workflow orchestration
- Minimal agent-to-agent communication
- Clear, deterministic steps
- Resources do the work; workflows orchestrate

**Real Example**: Expert Interview Application (`contrib/expert_interview/`)

The Expert Interview demonstrates this pattern beautifully:

```python
class ExpertInterviewWorkflow(BaseWorkflow):
    def __init__(self, reference_materials=None, expert_profile=None, **kwargs):
        super().__init__(workflow_id="expert-interview", **kwargs)

        # Initialize resources
        self.conversation = ConversationResource()
        self.insight_analyzer = ExpertInsightAnalyzer()
        self.gap_detector = KnowledgeGapDetector()

    def _do_execute(self, **kwargs):
        expert_message = kwargs["expert_message"]
        conversation_history = kwargs.get("conversation_history", [])

        # PHASE 1: Parallel information gathering
        async def phase1():
            """Extract topics and insights in parallel"""
            topic_task = asyncio.create_task(
                self.conversation._extract_topics(
                    message=expert_message,
                    conversation_history=conversation_history,
                    preserve_terminology=True
                )
            )

            insight_task = asyncio.create_task(
                self.insight_analyzer._analyze_insights(
                    message=expert_message,
                    conversation_history=conversation_history,
                    expert_profile=self.expert_profile
                )
            )

            return await asyncio.gather(topic_task, insight_task)

        topics, insights = asyncio.run(phase1())

        # PHASE 2: Gap detection and next question
        gaps = {}
        if self.reference_materials:
            gaps = self.gap_detector.detect_gaps(
                source1_content=insights.get("expert_insights_original", []),
                source2_content=self.reference_materials,
                source1_label="Expert Knowledge",
                source2_label="Reference Materials",
                topic_context=topics,
            )

        next_question = self._generate_next_question(topics, insights, gaps, conversation_history)

        return {
            "topics": topics,
            "insights": insights,
            "gaps": gaps,
            "next_question": next_question,
        }
```

**Key Success Metrics**:
- 90% code reduction vs custom implementation (10,000 LOC → 800 LOC)
- Domain-agnostic (works across all domains)
- Highly reusable resources
- Clear, testable workflow steps

**When to Use**:
- Problem has well-defined structure
- Steps are largely deterministic
- Little need for agent-to-agent communication
- Focus on orchestration, not decision-making

**Anti-patterns**:
- Trying to make workflows handle too much decision logic
- Not extracting reusable resources
- Building domain-specific workflows that can't be reused

---

## Agent Identity Patterns

### Identity Pattern: Dual Description

**All successful agents use dual identity definition:**

**PUBLIC_DESCRIPTION**:
- Describes the agent from an external perspective
- What the agent does
- When to use the agent
- What problems it solves
- Key capabilities

**IDENTITY**:
- Describes how the agent should think and behave
- Agent's role and personality
- Decision-making approach
- Operating principles
- Constraints

**Example from Test Agents**:
```python
class ResearchAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Research-focused STARAgent for testing multi-agent scenarios.
    </PUBLIC_DESCRIPTION>

    <IDENTITY>
    You are a research agent for testing multi-agent scenarios.
    You focus on gathering and analyzing information.
    You are thorough and analytical.
    </IDENTITY>
    """
```

**Why Both Are Needed**:
- PUBLIC: Enables other agents and users to know when to use this agent
- PRIVATE: Guides the agent's behavior and decision-making
- Separation enables clear multi-agent communication

---

## Composition Patterns

### Composition Pattern: Fluent Builder

All agents use the fluent builder pattern for composition:

```python
self.with_agents(
    SubAgent1(),
    SubAgent2(),
).with_workflows(
    Workflow1(),
    Workflow2(),
).with_resources(
    Resource1(),
    Resource2(),
).with_notifiable(
    observer,
)
```

**Benefits**:
- Clear, readable composition
- Chainable methods
- Explicit dependencies
- Easy to modify

---

### Composition Pattern: Module-Level Resource Instantiation

When workflows need to share resources, instantiate at module level:

```python
# web_research.py
from dana.lib.resources.web_research import SearchResource, FetchResource

# Module-level instantiation
_searcher = SearchResource()
_fetcher = FetchResource()

class SearchWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _searcher.search_web(**kwargs)

class FetchWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        return _fetcher.fetch_url(**kwargs)
```

**Benefits**:
- Avoid duplicate resource instantiation
- Share resource state if needed
- Cleaner workflow code
- Better performance

---

## Agent Sizing Guidelines

Based on successful implementations:

**Code Size**:
- Single Specialist: 30-50 lines
- Coordinator: 30-60 lines
- Complex Multi-Agent: 60-100 lines
- **If exceeding 100 lines**: Extract logic into workflows/resources

**Prompt Size**:
- Single Specialist: 200-500 words
- Coordinator: 300-800 words
- **If exceeding 1000 words**: Agent scope is too broad

**Component Counts**:
- Workflows: 2-5 per agent
- Resources: 2-5 per agent
- Sub-agents: 0-5 per coordinator
- **If exceeding these**: Consider decomposition

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: God Agent

**Problem**: Single agent trying to do everything

**Symptoms**:
- Agent has >10 workflows
- Agent has >10 resources
- Prompt exceeds 2000 words
- Agent handles multiple unrelated domains

**Solution**: Decompose into multiple specialists with optional coordinator

---

### Anti-Pattern 2: Thin Wrapper Agent

**Problem**: Agent that just wraps a single workflow with no added value

**Symptoms**:
- Agent has 1 workflow and no other capabilities
- Agent prompt is identical to workflow description
- No decision-making or routing logic

**Solution**: Either enrich the agent with more capabilities or just use the workflow directly

---

### Anti-Pattern 3: Circular Dependencies

**Problem**: Agents reference each other in circular fashion

**Symptoms**:
```python
class AgentA(STARAgent):
    def __init__(self):
        self.with_agents(AgentB())

class AgentB(STARAgent):
    def __init__(self):
        self.with_agents(AgentA())  # Circular!
```

**Solution**: Introduce coordinator or redesign collaboration pattern

---

### Anti-Pattern 4: Unclear Boundaries

**Problem**: Multiple agents with overlapping responsibilities

**Symptoms**:
- Can't clearly state what each agent does vs others
- Agents calling each other for same task
- Duplicate workflows across agents

**Solution**: Clearly define responsibilities and non-responsibilities; consolidate if needed

---

## Quick Reference: Pattern Selection

| Scenario | Recommended Pattern |
|----------|-------------------|
| Single domain, focused task | Single Specialist |
| Multiple domains, need synthesis | Hierarchical Coordinator |
| 2-4 specialists, simple interaction | Peer Collaboration |
| Structured problem, clear steps | Workflow-Heavy Application |
| User-facing, multi-domain | Hierarchical Coordinator (like DanaAgent) |
| Research/analysis task | Single Specialist (like WebResearchAgent) |
| Interview/structured capture | Workflow-Heavy (like Expert Interview) |

---

## Examples Reference

- **WebResearchAgent**: Single Specialist pattern
- **DanaAgent**: Hierarchical Coordinator pattern
- **Expert Interview**: Workflow-Heavy Application pattern
- **Test Multi-Agent**: Peer Collaboration pattern

See the `examples/` directory for detailed worked examples applying these patterns.
