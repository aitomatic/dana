# Re-Implementation Plan: Correct Deterministic Autonomy Architecture

## Problem Statement

The current prototype implements a **fixed workflow sequence** where the agent always runs:
```
Pareto → Correlation → ROI (fixed, always in this order)
```

This is **NOT** true deterministic autonomy because:
- ❌ Agent doesn't decide which workflows to run
- ❌ Workflows have embedded LLM calls instead of `agent.query()` callbacks
- ❌ Too rigid - not truly autonomous

## Correct Architecture

**CRITICAL: Workflows lazy-instantiate their own WorkflowStepAgent for intelligence!**

**Deterministic Autonomy should be:**
1. **Calling Agent (LLM)** decides which workflows to invoke (autonomous, goal-directed)
2. **Workflows execute deterministically** (can't skip steps within workflow)
3. **Workflows lazy-instantiate WorkflowStepAgent** for objective-driven intelligence tasks
   - WorkflowStepAgent is a reusable library component (`lib/agents/workflow_step_agent.py`)
   - Each workflow creates its own WorkflowStepAgent instance (lazy, on-demand)
   - WorkflowStepAgent has a system prompt for orchestrating intelligence tasks
   - **Avoids polluting calling agent's conversation timeline**
   - Workflow owns its intelligence context, not the calling agent

**Flow Example (Workflows with WorkflowStepAgent):**
```
YieldAnalysisAgent (calling agent) receives goal: "Analyze yield failures for wafer W12345"
  ↓
Calling Agent decides: "I need to understand failure distribution first"
  ↓
Calling Agent invokes: YieldParetoWorkflow(wafer_id="W12345")
  ↓
ParetoWorkflow executes deterministically:
  - Collect test data (can't skip)
  - Sort bins by count (can't skip)
  - Calculate Pareto 80/20 (can't skip)
  - 🔧 Lazy-instantiate: orchestrator = WorkflowStepAgent(objective="Classify failure bin patterns")
  - ⚡ Call: orchestrator.query("Classify these bin patterns: BIN_1 (clustered), BIN_2 (random)...")
    ↓ WorkflowStepAgent provides classification (using its own conversation context)
  - ⚡ Call: orchestrator.query("Is this Pareto distribution statistically significant?")
    ↓ WorkflowStepAgent validates (continues its conversation)
  - Generate structured output (can't skip)
  ↓
Workflow returns results to Calling Agent (orchestrator context stays in workflow)
  ↓
Calling Agent reviews results, decides: "Clustered patterns detected - need root cause analysis"
  ↓
Calling Agent invokes: FailureCorrelationWorkflow(bins=top_bins, product="CPU_7nm")
  ↓
CorrelationWorkflow executes deterministically:
  - Get historical yield data (can't skip)
  - Search similar cases (can't skip)
  - 🔧 Lazy-instantiate: orchestrator = WorkflowStepAgent(objective="Analyze yield correlations")
  - ⚡ Call: orchestrator.query("Analyze correlations with process changes...")
    ↓ WorkflowStepAgent provides correlation insights (new conversation context)
  - ⚡ Call: orchestrator.query("Generate root cause hypotheses based on evidence...")
    ↓ WorkflowStepAgent generates hypotheses (continues its conversation)
  - Generate correlation findings (can't skip)
  ↓
Workflow returns results to Calling Agent (orchestrator context stays in workflow)
  ↓
Calling Agent reviews all data, decides: "Ready to prioritize by ROI"
  ↓
Calling Agent invokes: ROIPrioritizationWorkflow(bins=top_bins, context=product_context)
  ↓
ROIWorkflow executes deterministically:
  - Calculate revenue impact (can't skip)
  - 🔧 Lazy-instantiate: orchestrator = WorkflowStepAgent(objective="Prioritize corrective actions")
  - ⚡ Call: orchestrator.query("Assess fix difficulty for each bin...")
    ↓ WorkflowStepAgent assesses difficulty (new conversation context)
  - Calculate ROI scores (can't skip)
  - Rank by ROI (can't skip)
  - ⚡ Call: orchestrator.query("Generate actionable recommendations...")
    ↓ WorkflowStepAgent synthesizes recommendations (continues its conversation)
  - Generate prioritized plan (can't skip)
  ↓
Workflow returns results to Calling Agent (orchestrator context stays in workflow)
  ↓
Calling Agent generates final comprehensive report
```

**Key Insights:**
- ✅ **Each workflow owns its intelligence context** via its own WorkflowStepAgent instance
- ✅ **Calling agent timeline stays clean** - no intelligence queries mixed in
- ✅ **WorkflowStepAgent is reusable** - same agent class across all workflows
- ✅ **Lazy instantiation** - only created when workflow needs intelligence
- ✅ **Objective-driven** - WorkflowStepAgent initialized with workflow's objective
- ✅ **Deterministic structure** maintained - workflows still can't skip steps

## Key Changes Required

### 0. NEW: Create WorkflowStepAgent (`dana_agent/dana/lib/agents/workflow_step_agent.py`)

**Purpose:** Reusable library agent for objective-driven intelligence orchestration within workflows.

**Design:**
```python
"""
WorkflowStepAgent - Reusable intelligence orchestrator for workflows.

This agent is designed to be lazy-instantiated by workflows to handle
objective-driven intelligence tasks without polluting the calling agent's
conversation timeline.
"""

from dana.core.agent.star_agent import STARAgent
from dana.lib.resources.conversation import ConversationResource

class WorkflowStepAgent(STARAgent):
    """
    Reusable agent for orchestrating intelligence tasks within workflows.

    Each workflow can instantiate its own WorkflowStepAgent with a specific
    objective, keeping intelligence context separate from the calling agent.

    Usage:
        orchestrator = WorkflowStepAgent(
            objective="Classify failure bin patterns for Pareto analysis"
        )
        result = orchestrator.query("Classify these patterns: ...")
    """

    def __init__(
        self,
        objective: str,
        agent_id: str | None = None,
        llm_provider: str = "anthropic",
        model: str | None = None,
        **kwargs
    ):
        """
        Initialize WorkflowStepAgent with an objective.

        Args:
            objective: The objective this orchestrator should achieve
                      (e.g., "Classify failure patterns", "Generate hypotheses")
            agent_id: Optional agent ID (auto-generated if not provided)
            llm_provider: LLM provider ("anthropic", "openai", etc.)
            model: Model name (defaults to provider default)
        """
        super().__init__(
            agent_id=agent_id or f"orchestrator-{objective[:20]}",
            system_prompt=self._build_system_prompt(objective),
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022",
            **kwargs
        )

        self.objective = objective
        self.conversation = ConversationResource(
            resource_id=f"{self.agent_id}-conversation",
            llm_provider=llm_provider,
            model=model or "claude-3-5-sonnet-20241022"
        )

    def _build_system_prompt(self, objective: str) -> str:
        """Build system prompt for this orchestrator's objective."""
        return f"""You are an WorkflowStepAgent responsible for: {objective}

Your role is to provide intelligent, objective-driven analysis and decision-making
for specific tasks within a systematic workflow.

Guidelines:
- Focus on the objective: {objective}
- Provide clear, structured, actionable responses
- Use domain expertise to analyze data and make recommendations
- Be concise but thorough
- Return structured data when requested (JSON, lists, etc.)
- Reason through complex problems step-by-step
- Acknowledge limitations when uncertain

You are operating within a deterministic workflow that ensures systematic quality.
Your job is to provide intelligence at specific decision points.
"""

    def query(self, question: str, context: dict | None = None) -> dict:
        """
        Query the orchestrator for intelligence on a specific question.

        Args:
            question: The question or task to address
            context: Optional context dictionary with additional data

        Returns:
            dict: Response with 'answer' and optional structured data
        """
        # Build prompt with context
        prompt = question
        if context:
            prompt = f"Context:\n{context}\n\nQuestion:\n{question}"

        # Use conversation resource for multi-turn intelligence
        response = self.conversation.send_message(
            message=prompt,
            conversation_history=[]  # Could maintain history if needed
        )

        return {
            "answer": response.get("response", ""),
            "context": context
        }

    def _do_execute(self, **kwargs) -> dict:
        """
        Execute method for STARAgent compatibility.

        Workflows should use query() directly instead of execute().
        """
        question = kwargs.get("caller_message", "")
        context = kwargs.get("context")
        return self.query(question, context)
```

**Key Features:**
- ✅ Lazy-instantiatable by workflows
- ✅ Objective-driven system prompt
- ✅ Maintains own conversation context
- ✅ Reusable across all workflows
- ✅ Clean separation from calling agent

**System Prompt Design:**
- Focused on specific objective
- Emphasizes structured, actionable responses
- Acknowledges role within deterministic workflow
- Encourages step-by-step reasoning

**Estimated effort:** 2-3 hours (implementation + testing)

### 1. Agent Changes (`agents/yield_pareto_analysis_agent.py`)

**BEFORE (Incorrect):**
```python
def _do_execute(self, **kwargs):
    # Fixed sequence - agent doesn't decide
    pareto_results = self.pareto_workflow.execute(wafer_id=wafer_id)
    correlation_results = self.correlation_workflow.execute(...)
    roi_results = self.roi_workflow.execute(...)
    return combined_results
```

**AFTER (Correct):**
```python
def _do_execute(self, **kwargs):
    # Agent uses LLM to decide workflow sequence
    goal = kwargs.get("caller_message", "Analyze yield")

    # Agent (LLM) decides what to do first
    plan = self.query(f"""
    Goal: {goal}

    You have access to these workflows:
    - YieldParetoWorkflow: Analyze failure distribution (80/20 rule)
    - FailureCorrelationWorkflow: Find historical correlations
    - ROIPrioritizationWorkflow: Prioritize by ROI

    Decide which workflow to run first and why.
    Return: {{"workflow": "workflow_name", "reasoning": "why"}}
    """)

    # Execute workflows based on agent decisions
    results = {}

    if plan["workflow"] == "YieldParetoWorkflow":
        pareto_results = self.pareto_workflow.execute(
            wafer_id=wafer_id,
            agent=self  # Pass agent so workflow can call back
        )
        results["pareto"] = pareto_results

        # Agent decides next step based on results
        next_step = self.query(f"""
        Pareto analysis complete:
        {pareto_results}

        Should I:
        1. Check historical correlations (FailureCorrelationWorkflow)?
        2. Go straight to ROI prioritization (ROIPrioritizationWorkflow)?
        3. Generate report with current data?

        Decide and explain.
        """)

        # Continue based on agent decision...
```

**Key Points:**
- Agent uses `self.query()` to make decisions about which workflows to invoke
- Agent passes `self` to workflows so they can call `agent.query()`
- Agent reviews results between workflows and decides next steps
- NOT a fixed sequence - agent adapts based on findings

### 2. Workflow Changes (All `workflows/*.py`)

**BEFORE (Incorrect):**
```python
class YieldParetoWorkflow(BaseWorkflow):
    def __init__(self, ...):
        # Workflow has its own LLM conversation resource
        self.conversation = ConversationResource(...)

    def _do_execute(self, **kwargs):
        # ... deterministic steps ...

        # Workflow calls its own LLM
        classification = self.conversation.send_message("Classify patterns...")

        # ... more steps ...
```

**AFTER (Correct) - Lazy-instantiate WorkflowStepAgent with Resources/Workflows:**
```python
from dana.lib.agents.workflow_step_agent import WorkflowStepAgent
from dana.lib.resources.conversation import ConversationResource

class YieldParetoWorkflow(BaseWorkflow):
    def __init__(self, ...):
        # NO embedded LLM resource or ConversationResource
        # Will lazy-instantiate WorkflowStepAgent when needed
        self._orchestrator = None

    def _get_orchestrator(self) -> WorkflowStepAgent:
        """Lazy-instantiate orchestrator with resources it needs."""
        if self._orchestrator is None:
            self._orchestrator = WorkflowStepAgent(
                agent_id=f"{self.workflow_id}-orchestrator"
            )

            # Give orchestrator access to resources it needs
            self._orchestrator.with_resources(
                ConversationResource(
                    resource_id=f"{self.workflow_id}-llm",
                    llm_provider="anthropic",
                    model="claude-3-5-sonnet-20241022"
                )
                # Could add other resources: data resources, analysis tools, etc.
            )

        return self._orchestrator

    def _do_execute(self, **kwargs):
        # STEP 1: Collect data (deterministic - can't skip)
        test_data = self.test_data.get_test_results(wafer_id=wafer_id)

        # STEP 2: Sort and calculate (deterministic - can't skip)
        sorted_bins = sorted(test_data['bins'], key=lambda x: x['count'], reverse=True)
        pareto_data = self._calculate_pareto_80_20(sorted_bins)

        # STEP 3: Get orchestrator for intelligence tasks
        orchestrator = self._get_orchestrator()

        # STEP 4: Call orchestrator for pattern classification
        # Orchestrator returns STRUCTURED data (not just text)
        classification_result = orchestrator.execute(
            caller_message=f"""
            Classify these bin patterns and return structured JSON:

            Bins: {self._format_bins_summary(sorted_bins[:5])}

            Return JSON with this exact structure:
            {{
                "classifications": [
                    {{
                        "bin_id": "BIN_1",
                        "pattern_type": "clustered|random|edge|center",
                        "fixability": "high|medium|low",
                        "confidence": 0.0-1.0,
                        "reasoning": "brief explanation"
                    }}
                ]
            }}
            """
        )

        # STEP 5: Parse structured response from orchestrator
        import json
        classifications = json.loads(classification_result.get("content", "{}"))

        # STEP 6: Workflow makes DETERMINISTIC decision based on structured data
        has_clustered = any(
            c["pattern_type"] == "clustered"
            for c in classifications.get("classifications", [])
        )

        # STEP 7: Generate output (can't skip)
        return {
            "success": True,
            "pareto_analysis": pareto_data,
            "pattern_classifications": classifications,
            "has_clustered_patterns": has_clustered,  # Deterministic flag
            "recommendation": "investigate_clustering" if has_clustered else "monitor"
        }
```

**Key Points:**
- ✅ Workflows NO LONGER have embedded `ConversationResource`
- ✅ Workflows lazy-instantiate `WorkflowStepAgent` (only when needed)
- ✅ WorkflowStepAgent is initialized with workflow's objective
- ✅ Orchestrator maintains its own conversation context (doesn't pollute calling agent)
- ✅ Workflow structure remains deterministic (can't skip steps)
- ✅ **Clean separation:** Calling agent decides workflows, workflows handle their own intelligence

### 3. Specific File Changes

#### `agents/yield_pareto_analysis_agent.py`

**Changes needed:**
1. Remove fixed sequence in `_do_execute()`
2. Add agent decision-making using `self.query()` or `self.converse()`
3. Pass `self` to workflow executions so they can callback
4. Agent reviews results between workflows and decides next steps
5. Agent generates final report after all workflows complete

**Estimated effort:** 2-3 hours

#### `workflows/yield_pareto_workflow.py`

**Changes needed:**
1. Remove `self.conversation = ConversationResource(...)`
2. Add `agent = kwargs.get("agent")` in `_do_execute()`
3. Replace `self.conversation.send_message(...)` with `agent.query(...)`
4. Keep all deterministic steps (data collection, sorting, calculation)
5. Update docstrings to explain agent callback mechanism

**Estimated effort:** 1 hour

#### `workflows/failure_correlation_workflow.py`

**Changes needed:**
1. Remove `self.conversation = ConversationResource(...)`
2. Add `agent = kwargs.get("agent")` in `_do_execute()`
3. Replace LLM calls with `agent.query(...)` for:
   - Correlation analysis
   - Root cause hypothesis generation
4. Keep all deterministic steps (historical lookup, case search)

**Estimated effort:** 1 hour

#### `workflows/roi_prioritization_workflow.py`

**Changes needed:**
1. Remove `self.conversation = ConversationResource(...)`
2. Add `agent = kwargs.get("agent")` in `_do_execute()`
3. Replace LLM calls with `agent.query(...)` for:
   - Fix difficulty assessment
   - Recommendation generation
4. Keep all deterministic steps (revenue calc, ROI scoring, ranking)

**Estimated effort:** 1 hour

#### `demo_deterministic.py`

**Changes needed:**
1. Update demo to show agent decision-making
2. Add output showing:
   - "Agent decides: I need Pareto analysis..."
   - "Workflow executing: YieldParetoWorkflow..."
   - "Workflow calls agent: Classify patterns..."
   - "Agent provides: LLM classification..."
   - "Agent decides next: Check correlations..."
3. Make it clear that sequence is NOT fixed

**Estimated effort:** 30 minutes

## Implementation Steps

### Phase 0: Create WorkflowStepAgent (Foundation)
**Time: ~2-3 hours**

1. Create `dana_agent/dana/lib/agents/__init__.py` (if doesn't exist)

2. Create `dana_agent/dana/lib/agents/workflow_step_agent.py`
   - Implement WorkflowStepAgent class (extends STARAgent)
   - Add objective-driven system prompt builder
   - Add query() method for intelligence tasks
   - Add lazy instantiation support

3. Test WorkflowStepAgent standalone
   - Test objective initialization
   - Test query() method
   - Test conversation context isolation

**Milestone:** WorkflowStepAgent ready for use by workflows

### Phase 1: Update Workflows (Intelligence Layer)
**Time: ~4 hours**

1. Update `workflows/yield_pareto_workflow.py`
   - Remove ConversationResource
   - Add _get_orchestrator() lazy instantiation method
   - Replace LLM calls with orchestrator.query()
   - Add objective: "Classify failure bin patterns and validate Pareto analysis"

2. Update `workflows/failure_correlation_workflow.py`
   - Same pattern as above
   - Add objective: "Analyze yield correlations and generate root cause hypotheses"

3. Update `workflows/roi_prioritization_workflow.py`
   - Same pattern as above
   - Add objective: "Assess fix difficulty and prioritize corrective actions"

**Milestone:** Workflows use WorkflowStepAgent for intelligence

### Phase 2: Update Agent (Core Logic)
**Time: ~3 hours**

1. Update `agents/yield_pareto_analysis_agent.py`
   - Remove fixed workflow sequence
   - Add agent decision-making logic
   - Pass `self` to workflows
   - Implement result review and next-step decisions
   - Generate final report

**Milestone:** Agent can decide workflows autonomously

### Phase 3: Update Demo
**Time: ~1 hour**

1. Update `demo_deterministic.py`
   - Show agent decision points
   - Show workflow callbacks
   - Make autonomy visible to user

**Milestone:** Demo clearly shows deterministic autonomy

### Phase 4: Test and Validate
**Time: ~2 hours**

1. Run demo and verify:
   - Agent makes decisions
   - Workflows execute deterministically
   - Workflows call agent for intelligence
   - Output shows collaborative flow

2. Test edge cases:
   - What if agent decides to skip a workflow?
   - What if workflow query fails?
   - Graceful degradation

**Milestone:** System working with correct architecture

## Total Estimated Effort

- **Phase 0 (WorkflowStepAgent):** ~2-3 hours
- **Phase 1 (Workflows):** ~4 hours
- **Phase 2 (Agent):** ~3 hours
- **Phase 3 (Demo):** ~1 hour
- **Phase 4 (Testing):** ~2 hours
- **Documentation:** ~1 hour
- **Total:** ~13-14 hours (2 days)

**Note:** Slightly longer than multi-agent approach due to creating new WorkflowStepAgent library component, but cleaner architecture.

## Success Criteria

✅ Agent (LLM) decides which workflows to run
✅ Workflows execute deterministically (can't skip steps)
✅ Workflows call `agent.query()` for intelligence
✅ Demo clearly shows agent-workflow collaboration
✅ Architecture matches design documentation
✅ System passes same yield analysis test case

## Questions to Resolve

1. **Agent API:** Should workflows use `agent.query()`, `agent.converse()`, or `agent.some_magic_function()`?
   - `agent.query(prompt)` → simple question/answer
   - `agent.converse(message, history)` → multi-turn conversation
   - `agent.some_magic_function()` → ???

2. **Workflow failure:** What if agent.query() fails? Should workflow:
   - Fail completely?
   - Use fallback heuristics?
   - Return partial results?

3. **Agent memory:** Should agent maintain state between workflow invocations?
   - Store results from previous workflows?
   - Build up context as it progresses?

4. **Decision transparency:** How to log/display agent decisions for debugging?
   - Workflow progress broadcasts?
   - Separate agent decision log?

## Next Steps

1. ✅ Design docs updated (SEMICONDUCTOR_DEMOS.md, WHAT_WE_DEMONSTRATED.md)
2. ⏳ Get user confirmation on architecture
3. ⏳ Clarify agent API questions above
4. ⏳ Begin Phase 1: Update workflows
5. ⏳ Begin Phase 2: Update agent
6. ⏳ Begin Phase 3: Update demo
7. ⏳ Phase 4: Test and validate
