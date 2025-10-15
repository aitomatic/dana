# Autonomy Pattern Demonstrations

This directory contains demos that showcase the difference between **deterministic** and **probabilistic** autonomy patterns in AI agents.

## The Core Difference

### 🔧 Deterministic (Workflow-Orchestrated)
- **Workflows control execution**: You define the sequence of operations
- **Guaranteed behavior**: Same query type → same workflow sequence
- **Transparent**: You can trace exactly what happened
- **Predictable**: Run it 10 times, get consistent execution flow

**Example**: SmartResearchAgent with workflows enabled

### 🎲 Probabilistic (LLM-Only)
- **LLM decides**: AI chooses what to do autonomously
- **Variable behavior**: May or may not use available tools
- **Opaque**: Decision-making happens in the LLM
- **Unpredictable**: Run it 10 times, might get different strategies

**Example**: ProbabilisticResearchAgent with workflows commented out

## Demos

### 1. Deterministic Control Demo
**File**: `demo_deterministic_control.py`

Shows how workflows provide consistent, controlled execution across different query types.

```bash
python examples/autonomy/demo_deterministic_control.py
```

**What to observe:**
- Strategy selection workflow executes first
- Research workflow executes based on strategy
- Consistent workflow sequence every time
- Timeline shows all workflow calls

### 2. Comparison Demo
**File**: `demo_comparison.py`

Side-by-side comparison of the same query through both agents.

```bash
python examples/autonomy/demo_comparison.py
```

**What to observe:**
- Deterministic: Always calls workflows
- Probabilistic: LLM decides (might skip workflows)
- Shows fundamental difference in control vs autonomy

### 2b. Visible Thinking Demo
**File**: `demo_visible_thinking.py`

Demonstrates the ThoughtLogger feature that makes agent thinking transparent.

```bash
python examples/autonomy/demo_visible_thinking.py
```

**What to observe:**
- STAR loop phases shown in real-time (SEE, THINK, ACT, REFLECT)
- Internal reasoning displayed in faded gray
- Comparison with/without ThoughtLogger
- Shows what makes Dana agents transparent vs black-box AI

### 2c. Workflow Thinking Demo
**File**: `demo_workflow_thinking.py`

Shows how workflows broadcast their internal progress step-by-step.

```bash
python examples/autonomy/demo_workflow_thinking.py
```

**What to observe:**
- Workflow phases: START → CLASSIFY → COMPLETE
- Each workflow step visible (extract, themes, gaps, confidence)
- Complete transparency into multi-step processes
- How the Notifiable pattern makes workflows observable

### 2d. Semiconductor Research Demo
**File**: `demo_semiconductor_research.py`

Real-world demonstration using semiconductor technology comparison - shows why deterministic matters for high-stakes technical research.

```bash
python examples/autonomy/demo_semiconductor_research.py
```

**Query**: "Compare TSMC's 3nm vs Intel 18A: yield rates, performance, timeline, positioning"

**What to observe:**
- Deterministic: Always verifies technical claims (yield rates often speculation)
- Deterministic: Always checks recency (semiconductor data outdates quarterly)
- Deterministic: Always identifies gaps (what's verified vs unverified)
- Probabilistic: May cite unverified claims as fact
- Probabilistic: May give overly confident answers on incomplete data
- **Why it matters**: Bad research → bad investment/strategy decisions

### 3. Interactive Sessions
**Files**: `run_deterministic.py`, `run_probabilistic.py`

Interactive conversation sessions with each agent type.

```bash
python examples/autonomy/run_deterministic.py
python examples/autonomy/run_probabilistic.py
```

### 4. Interactive Sessions with Visible Thinking
**Files**: `run_deterministic_with_thinking.py`, `run_probabilistic_with_thinking.py`

Interactive sessions that show the agent's STAR loop in real-time using `ThoughtLogger`.

```bash
python examples/autonomy/run_deterministic_with_thinking.py
python examples/autonomy/run_probabilistic_with_thinking.py
```

**What to observe:**
- 👁️ SEE phase: Agent perceives your query or tool results
- 💭 THINK phase: Agent reasons (shown in faded gray)
- ⚡ ACT phase: Agent executes tools/workflows
- 🔄 REFLECT phase: Agent learns from interaction

The gray text shows internal thinking - making the AI completely transparent!

**Note**: The SEE phase appears both:
- Initially: When receiving the user's query
- After tool execution: When perceiving tool results for the next STAR loop iteration

## Why Semiconductors is a Compelling Demo Domain

Semiconductor technology research is **ideal** for demonstrating deterministic vs probabilistic autonomy because:

### 1. **Verification Critical**
- **Yield rates** are often rumors/speculation (companies don't disclose real numbers)
- **Performance claims** are often marketing vs verified benchmarks
- **Timeline promises** often slip (need to verify against history)
- Deterministic: Always runs verification workflow
- Probabilistic: May cite unverified claims as fact

### 2. **Recency Critical**
- Roadmaps change **quarterly**
- Data from 6+ months ago is **outdated**
- New process nodes, design wins, production updates constantly
- Deterministic: Always checks source dates, searches for recent updates
- Probabilistic: May use outdated information

### 3. **Gap Detection Critical**
- What's **claimed** vs what's **proven** matters enormously
- Knowing **what you don't know** is critical for risk assessment
- Example: "Intel 18A high yields" (claimed) vs "No verified yield data" (reality)
- Deterministic: Always identifies knowledge gaps
- Probabilistic: May give overly confident answers on incomplete data

### 4. **High Stakes**
- Investment decisions worth **billions**
- Strategic decisions (which foundry? which process node?)
- Supply chain risk assessment
- **Bad research → bad decisions → massive losses**

### 5. **Multi-Dimensional**
- Technical (transistor density, power, performance)
- Business (customers, revenue, market share)
- Geopolitical (export controls, supply chain, Taiwan risk)
- Requires **structured analysis** across dimensions

This makes semiconductors a **perfect stress test** for agent reliability.

### Other Compelling Semiconductor Queries

Try these queries to see deterministic vs probabilistic differences:

**1. Geopolitical Supply Chain:**
```
"Analyze China's progress in advanced packaging (chiplets, HBM) to circumvent US export controls"
```
- Challenge: Mix of propaganda and facts
- Deterministic advantage: Source credibility workflow separates claims from verified data

**2. EUV Supply Chain Risk:**
```
"What are the critical dependencies in ASML's EUV lithography supply chain and which chipmakers are most exposed?"
```
- Challenge: Multi-dimensional (technology + business + geopolitics)
- Deterministic advantage: Systematic risk assessment across all dimensions

**3. Process Technology Roadmap:**
```
"Compare roadmaps for GAA (Gate-All-Around) transistor adoption across TSMC, Samsung, Intel"
```
- Challenge: Marketing claims vs reality, timeline verification
- Deterministic advantage: Historical timeline accuracy checking

**4. Market Analysis:**
```
"Should TSMC expand 3nm production in Arizona vs Taiwan? Analyze cost, geopolitical risk, timeline"
```
- Challenge: Multi-criteria decision making
- Deterministic advantage: Structured decision framework, explicit trade-offs

## Key Insights

### When to Use Deterministic (Workflows)
- ✅ You need **predictable** behavior
- ✅ You want **control** over execution flow
- ✅ You need to **trace** what happened
- ✅ Compliance or audit requirements
- ✅ Multi-step processes with dependencies

### When to Use Probabilistic (LLM-Only)
- ✅ You want **flexible** AI reasoning
- ✅ Task is **open-ended** or exploratory
- ✅ You trust the LLM to make good decisions
- ✅ Rapid prototyping without workflow design

### The Hybrid Approach
In practice, you often want **both**:
- Use workflows for critical path operations
- Let LLM decide on exploratory/creative tasks
- Dana framework supports both patterns!

## Technical Implementation

### Deterministic Agent (`SmartResearchAgent`)
```python
# Workflows are composed into the agent
self.with_workflows(
    ResearchStrategyWorkflow(workflow_id="strategy-selection"),
    ParallelGatheringWorkflow(workflow_id="parallel-gather"),
    SynthesisWorkflow(workflow_id="synthesis"),
)

# Prompt mandates workflow usage
**MANDATORY WORKFLOW USAGE:**
For ALL research queries, you MUST follow this workflow sequence...
```

### Probabilistic Agent (`ProbabilisticResearchAgent`)
```python
# Workflows are commented out - only resources available
self.with_resources(
    SearchResource(resource_id="web-search"),
    WebFetcher(resource_id="web-fetch"),
    ConversationResource(resource_id="llm-reasoning"),
)

# Workflows NOT composed
# self.with_workflows(...) # COMMENTED OUT
```

## Visible Thinking with ThoughtLogger

The Dana framework includes `ThoughtLogger` - a notifiable component that makes agent thinking transparent in real-time.

### How It Works

```python
import logging
import structlog
from dana.apps.dana.thought_logger import ThoughtLogger

# Optional: Suppress framework logging to keep output clean
logging.basicConfig(level=logging.ERROR, force=True)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR),
)

# Create agent
agent = SmartResearchAgent()

# Attach ThoughtLogger to show thinking progress
thought_logger = ThoughtLogger(verbose=True, show_tool_calls=True)
agent.with_notifiable(thought_logger)

# Now all STAR loop phases are visible!
agent.converse()
```

### What You'll See

The complete STAR loop becomes visible in faded gray text:

```
👁️  SEE [smart-research-001] Received: What is quantum computing?
💭 THINK [smart-research-001] Analyzing query type... → workflow:strategy-selection
⚡ ACT [smart-research-001] Calling: call_workflow execute
🔧 WORKFLOW [research-strategy] Analyzing query to select research strategy...
🔍 WORKFLOW [research-strategy] Classifying query type with keyword matching...
✅ WORKFLOW [research-strategy] Selected QUICK_FACT strategy (confidence: 0.85)
👁️  SEE [smart-research-001] Perceived 1 tool result(s)
💭 THINK [smart-research-001] Based on strategy, gathering information... → workflow:synthesis
⚡ ACT [smart-research-001] Calling: call_workflow execute
🔧 WORKFLOW [synthesis] Synthesizing findings from 5 sources...
📄 WORKFLOW [synthesis] Extracting key findings from 5 sources...
🏷️  WORKFLOW [synthesis] Identifying common themes...
📝 WORKFLOW [synthesis] Generating synthesis overview...
✅ WORKFLOW [synthesis] Synthesis complete (confidence: 0.75, 5 findings)
👁️  SEE [smart-research-001] Perceived 1 tool result(s)
💭 THINK [smart-research-001] Generating final response based on synthesis...
🔄 REFLECT [smart-research-001] [ACQUISITIVE] Initial learning and trial-level plasticity
```

Notice how:
- **SEE** appears multiple times (initial query, then perceiving each tool result)
- **Workflows** show their internal thinking step-by-step
- Complete transparency into the entire STAR loop iteration process!

### Why This Matters

**Transparency**: You can see exactly what the agent is doing at each step - including what it perceives (SEE), how it thinks (THINK), what it does (ACT), and what it learns (REFLECT)

**Debugging**: Identify where workflows are/aren't being called, and see the complete STAR loop in action

**Understanding**: Learn how the STAR loop works in practice - both the initial perception and subsequent perceptions of tool results

**Trust**: No black box - every decision and perception is visible

### Notifiable Pattern

Under the hood, this uses Dana's **Notifiable** pattern:
- All agents, workflows, and resources inherit from `Notifier`
- They broadcast events after each STAR phase
- `ThoughtLogger` is a `Notifiable` that receives and displays these events
- Events cascade: attach to agent, and sub-agents/workflows/resources notify too

**Workflows can broadcast their own thinking:**

```python
class MyWorkflow(BaseWorkflow):
    def _do_execute(self, **kwargs):
        # Broadcast progress at key steps
        self.broadcast({
            "workflow_progress": {
                "workflow_id": self.workflow_id,
                "phase": "start",
                "message": "Starting complex computation..."
            }
        })

        # Do work...

        self.broadcast({
            "workflow_progress": {
                "workflow_id": self.workflow_id,
                "phase": "complete",
                "message": "Computation complete!"
            }
        })
```

This makes workflows transparent too - you see every step of their reasoning!

You can create your own custom notifiables for logging, monitoring, or UI updates!

## Framework Improvements

This demo also showcases recent Dana framework improvements:

1. **XML Tool Call Parsing**: Handles attributes on `<tool_call>` tags
2. **Synthetic User Messages**: Framework adds continuation prompts after tool execution
3. **Timeline Transparency**: Full visibility into agent execution
4. **LLM Flexibility**: Works with Anthropic Claude, OpenAI, and other providers
5. **Notifiable Pattern**: Real-time visibility into agent thinking and actions

## Running the Demos

All demos use Claude 3.5 Sonnet for consistent comparison. Make sure you have:

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

Then run any demo from the project root:

```bash
cd /path/to/dana-internal/examples/agents/smart-research
python examples/autonomy/demo_deterministic_control.py
python examples/autonomy/demo_comparison.py
```

## Further Reading

- **Design Docs**: `../../docs/ai-building-agents/design/`
- **Agent Implementation**: `../../agents/smart_research_agent.py`
- **Workflow Examples**: `../../workflows/`
