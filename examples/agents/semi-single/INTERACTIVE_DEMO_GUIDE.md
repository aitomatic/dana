# Interactive Semiconductor Yield Analysis Demo

## Quick Start

```bash
python run_interactive_demo.py
```

This starts an interactive conversation with an AI semiconductor yield analyst.

## What You Can Do

### Ask for Analysis
- "Analyze failures for wafer W12345"
- "Run a Pareto analysis"
- "Give me a complete yield analysis"

### Ask Questions
- "What are the top failure bins?"
- "Is BIN_1 systematic or random?"
- "What's the difference between systematic and random defects?"
- "Which failure should I fix first?"

### Request Evidence
- "Show me evidence that BIN_1 is systematic"
- "What statistical tests support this conclusion?"
- "Compare BIN_1 with historical patterns"
- "Give me the spatial defect distribution"

### Get Recommendations
- "What's the ROI for fixing BIN_1?"
- "Help me prioritize which failure to fix first"
- "What process changes might have caused this?"
- "What actions should I take to improve yield?"

## Available Data

The agent has access to:
- **Wafer W12345**: 68.5% yield, 315 failures
- **Spatial defect maps**: Where failures occur on the wafer
- **Statistical tools**: Moran's I test, hot spot analysis
- **Historical database**: Known systematic defect patterns
- **Process history**: Recent process changes

## How It Works

### ULTIMATE Deterministic Autonomy Pattern

The agent uses three levels of intelligence:

1. **Main Agent** (you talk to this)
   - Decides which workflows to run based on your questions
   - Autonomous, goal-directed

2. **Workflows** (execute systematically)
   - YieldParetoWorkflow - identifies top failure bins
   - FailureCorrelationWorkflow - finds root causes
   - ROIPrioritizationWorkflow - ranks fixes by revenue impact
   - Each workflow executes ALL steps (can't skip)

3. **WorkflowStepAgent** (autonomous intelligence at each step)
   - Equipped with Resources (WaferMap, Statistical, Historical)
   - Equipped with Workflows (Clustering, StatisticalTest)
   - Autonomously uses tools to gather evidence
   - Synthesizes multi-source results

### Example Conversation Flow

```
You: Analyze failures for wafer W12345

Agent: [Decides to run Pareto workflow]
       [Pareto workflow executes all steps:]
         → Collects test data
         → Sorts failure bins
         → Calculates Pareto (80% rule)
         → WorkflowStepAgent classifies patterns:
           • Gets spatial data from WaferMapResource
           • Runs statistical tests via StatisticalTestWorkflow
           • Checks historical patterns
           • Synthesizes evidence: BIN_1 is SYSTEMATIC (confidence 0.95)

Agent: I found 2 critical failure bins representing 80% of failures:
       - BIN_1: SRAM bit failures (180 dies, SYSTEMATIC with 95% confidence)
       - BIN_2: Timing violations (75 dies, RANDOM)

       Evidence for BIN_1 being systematic:
       • Spatial clustering: Center density 0.82 vs edge 0.05 (16:1 ratio)
       • Moran's I = 0.87, p < 0.001 (strong autocorrelation)
       • Hot spot in center region (Gi* = 3.85, p < 0.001)
       • 91% match to historical systematic case CASE_2024_045

You: What's the ROI for fixing BIN_1?

Agent: [Decides to run ROI workflow]
       [ROI workflow calculates revenue impact, fix difficulty]

Agent: BIN_1 has the highest ROI:
       • Revenue impact: $3.24B/year
       • Fix difficulty: MEDIUM (10-20 days)
       • ROI score: $4.86B

       Recommended actions:
       1. Detailed failure analysis (SEM, TEM)
       2. Process characterization split lots
       3. Correlation with metrology data
```

## Key Features

### 🎯 Deterministic Quality
- All workflow steps are executed (can't skip)
- Systematic, repeatable results
- Quality assurance guaranteed

### 🧠 Autonomous Intelligence
- Agent decides which workflows to run
- WorkflowStepAgent decides which tools to use
- Multi-source evidence synthesis
- Adapts to your questions

### 📊 Evidence-Based
- Not just LLM opinions
- Statistical significance tests (p-values)
- Historical pattern matching
- Spatial analysis with metrics

### 💬 Natural Conversation
- Ask questions in plain English
- Get explanations and guidance
- Iterative exploration
- Educational responses

## Comparison with Automated Demos

| Feature | Automated Demos (A/B/C) | Interactive Demo |
|---------|------------------------|------------------|
| **Interface** | Fixed script, no input | Natural conversation |
| **Flexibility** | Pre-defined sequence | You guide the analysis |
| **Exploration** | Limited | Unlimited questions |
| **Learning** | Observe outputs | Ask "why" and "how" |
| **Use Case** | Demonstrations | Real analysis sessions |

## Example Questions to Try

### Beginner
- "What is Pareto analysis?"
- "Explain systematic vs random defects"
- "Help me analyze wafer W12345"

### Intermediate
- "Is BIN_1 systematic or random? Show evidence."
- "What correlates with these failures?"
- "Calculate ROI for fixing each bin"

### Advanced
- "Compare BIN_1 spatial pattern with historical case CASE_2024_045"
- "Run Moran's I test on BIN_1 and interpret results"
- "What's the statistical significance of the center clustering?"
- "Use multiple workflows to build a comprehensive yield improvement plan"

## Tips for Best Results

1. **Be specific**: "Analyze BIN_1" is better than "tell me about failures"
2. **Ask for evidence**: "Show me why" gets statistical backing
3. **Iterate**: Start broad, then drill into details
4. **Request workflows**: "Run Pareto analysis" directly invokes workflows
5. **Compare**: "Compare BIN_1 vs BIN_2" leverages multiple analyses

## Exit Commands

- Type `quit`, `exit`, or `bye` to end the conversation
- Type `help` for available commands

## Technical Details

**Agent**: YieldAnalysisAgent (STARAgent)
- LLM: Claude 3.5 Sonnet
- Pattern: ULTIMATE Deterministic Autonomy
- Resources: 6 (TestData, WaferMap, Statistical, Historical, Conversation, ToDo)
- Workflows: 3 (Pareto, Correlation, ROI)

**Architecture**:
```
User ←→ YieldAnalysisAgent
         ├─ Resources (data access)
         │  ├─ WaferMapResource
         │  ├─ StatisticalAnalysisResource
         │  └─ HistoricalPatternResource
         │
         └─ Workflows (analysis)
            ├─ YieldParetoWorkflow
            │  └─ WorkflowStepAgent (with Resources + Workflows)
            ├─ FailureCorrelationWorkflow
            └─ ROIPrioritizationWorkflow
```

This is **the most powerful agent pattern** - conversational interface with deterministic quality and autonomous intelligence.
