# Semiconductor Yield Analysis - Deterministic Autonomy Demo

This demo showcases **Deterministic Autonomy** for semiconductor yield analysis using the Dana agent framework.

## What is Deterministic Autonomy?

Deterministic Autonomy combines systematic engineering workflows with LLM intelligence at specific decision points. It sits between two extremes:

| Mode | Structure | Intelligence | Consistency | Use Case |
|------|-----------|--------------|-------------|----------|
| **Automation** | Rigid rules (IF-THEN) | ❌ None | ✅ Perfect | Simple, well-defined tasks |
| **Probabilistic Autonomy** | ❌ LLM decides everything | ✅ Full AI | ❌ Inconsistent | Creative, exploratory tasks |
| **Deterministic Autonomy** | ✅ Workflows enforce steps | ✅ LLM at decision points | ✅ Reproducible | High-stakes industrial applications |

**This demo implements Deterministic Autonomy** - perfect for semiconductor manufacturing where:
- You **cannot skip** critical analysis steps (Pareto, correlation, ROI)
- You **need** AI intelligence for pattern recognition and root cause analysis
- You **must** have consistent, reproducible, explainable results
- Mistakes cost millions in revenue loss

## The Use Case: Wafer Yield Analysis

**Business Context:**
- 7nm CPU manufacturing
- Current yield: 68.5% (target: 75%+)
- Revenue at risk: $10M+ annually from yield loss
- 6 different failure bins with varying patterns

**Analysis Challenge:**
Engineers need to:
1. Identify which failure bins matter most (Pareto analysis)
2. Correlate with historical data and process changes
3. Prioritize fixes by ROI (revenue impact vs difficulty)
4. Generate actionable recommendations with evidence

**Why Deterministic Autonomy Wins:**
- ✅ **Can't skip steps**: Always does Pareto, correlation, ROI (engineering rigor)
- ✅ **Intelligent**: LLM classifies patterns, reasons about correlations, generates hypotheses
- ✅ **Reproducible**: Same analysis every time (engineer trust)
- ✅ **Actionable**: Specific recommendations ranked by ROI

## Architecture

```
YieldParetoAnalysisAgent (STARAgent)
  │
  ├── YieldParetoWorkflow
  │   ├── Data collection (MANDATORY)
  │   ├── Bin sorting (MANDATORY)
  │   ├── Pareto calculation (MANDATORY - 80/20 rule)
  │   ├── Pattern classification (LLM INTELLIGENCE)
  │   └── Output structured results
  │
  ├── FailureCorrelationWorkflow
  │   ├── Historical yield lookup (MANDATORY)
  │   ├── Similar case search (MANDATORY)
  │   ├── Process correlation analysis (LLM INTELLIGENCE)
  │   ├── Root cause hypothesis generation (LLM INTELLIGENCE)
  │   └── Output correlation findings
  │
  └── ROIPrioritizationWorkflow
      ├── Revenue impact calculation (MANDATORY)
      ├── Fix difficulty assessment (LLM INTELLIGENCE)
      ├── ROI scoring (MANDATORY formula)
      ├── Ranking by ROI (MANDATORY)
      ├── Action recommendations (LLM INTELLIGENCE)
      └── Output prioritized plan
```

### Key Design Principles

1. **Workflows Enforce Structure**: Can't skip Pareto, correlation, or ROI steps
2. **LLM Provides Intelligence**: Pattern recognition, root cause reasoning, recommendations
3. **Systematic + Smart**: Engineering rigor + AI insight
4. **Visible + Explainable**: ThoughtLogger shows every step in real-time

## Running the Demo

### Prerequisites

```bash
# Install Dana framework (from repository root)
cd dana_agent
pip install -e .

# Set up Anthropic API key
export ANTHROPIC_API_KEY="your-key-here"
```

### Run the Demo

```bash
cd examples/agents/semi-single
python demo_deterministic.py
```

### What You'll See

The demo will show:

1. **Real-time workflow progress** (via ThoughtLogger in gray):
   ```
   👁️  SEE    [yield-pareto-agent] Received: Analyze yield
   🧠 THINK   [yield-pareto-agent] Planning systematic analysis...
   ⚙️  WORKFLOW [pareto-analysis] Collecting wafer test data...
   ⚙️  WORKFLOW [pareto-analysis] Sorting failure bins by count...
   🤖 WORKFLOW [pareto-analysis] Analyzing failure patterns with LLM...
   ✅ WORKFLOW [pareto-analysis] Pareto analysis complete: 3 top bins identified
   ```

2. **Executive Summary**:
   ```
   Wafer ID:          W12345-789
   Product:           CPU_7nm_A53_HiPerf
   Current Yield:     68.5%
   Yield Trend:       DEGRADING (-4.0%)
   Total Failures:    315

   Pareto Bins:       3 bins represent 80% of failures
   Revenue at Risk:   $564,000,000 annually

   Top Priority:      BIN_1
     Impact:          $324,000,000/year

   Likely Root Cause: Metal etch over-etch causing SRAM cell damage
     Confidence:      HIGH
   ```

3. **Pareto Analysis Table**:
   ```
   Rank   Bin ID       Description                    Count    %      Cum%   Pattern
   ----   ------       -----------                    -----    --     ----   -------
   1      BIN_1        SRAM bit failures              180      57.1   57.1   clustered
   2      BIN_2        Logic path timing violations    75      23.8   81.0   random
   3      BIN_3        I/O buffer failures             35      11.1   92.1   systematic
   ```

4. **Root Cause Hypotheses** (evidence-based):
   ```
   Hypothesis #1: Similar to historical case: Metal etch over-etch causing SRAM cell damage
     Confidence: HIGH
     Evidence:
       • Very similar failure pattern (similarity: 0.92)
       • Historical case: YLD-2023-087
       • Previous resolution: Reduced etch RF power by 8%, adjusted etch time
     Next Steps: Apply similar resolution approach: Reduced etch RF power by 8%, adjusted etch time
   ```

5. **Prioritized Action Plan** (ROI-ranked):
   ```
   #1 - BIN_1: SRAM bit failures
     Revenue Impact:  $324,000,000/year
     Fix Difficulty:  MEDIUM
     ROI Score:       486,000,000
     Priority:        HIGH PRIORITY: Significant revenue impact with moderate fix difficulty. Good ROI.
     Timeline:        10-20 days
     Actions:
       • Immediate DOE on process parameters
       • Check recent process recipe changes
       • Compare with historical similar cases
   ```

## Value Demonstration

This demo shows how Deterministic Autonomy provides:

### ✅ Systematic Coverage (Can't Skip Steps)
- **Always** performs Pareto analysis (80/20 rule)
- **Always** searches historical correlations
- **Always** calculates ROI and prioritizes

Compare to:
- ❌ Automation: Can't handle novel patterns (no AI)
- ❌ Probabilistic: Might skip correlation if LLM "thinks" it's not needed

### ✅ Intelligent Reasoning (LLM at Decision Points)
- Pattern classification (systematic vs random)
- Process correlation reasoning (timing, causality)
- Root cause hypothesis generation (evidence synthesis)
- Actionable recommendation generation

Compare to:
- ❌ Automation: No intelligence, rigid rules only
- ✅ Probabilistic: Has intelligence, but inconsistent application

### ✅ Reproducible Results (Engineering Trust)
- Same workflow sequence every time
- Structured data flow between workflows
- Explainable reasoning at each step
- Audit trail of decisions

Compare to:
- ✅ Automation: Reproducible but dumb
- ❌ Probabilistic: Inconsistent - different analysis each run

### ✅ Actionable Output (Business Value)
- **$564M annual opportunity identified** (yield gap to target)
- **3 high-priority bins** representing 80% of failures
- **Specific actions** with timelines (10-20 days for top priority)
- **Evidence-based** root cause (92% similarity to historical case)

## File Structure

```
semi-single/
├── README.md                           # This file
├── demo_deterministic.py               # Main demo script
│
├── agents/
│   └── yield_pareto_analysis_agent.py  # Deterministic agent (STARAgent)
│
├── workflows/
│   ├── yield_pareto_workflow.py        # Pareto analysis (80/20 rule)
│   ├── failure_correlation_workflow.py # Historical correlation
│   └── roi_prioritization_workflow.py  # ROI-based prioritization
│
├── resources/
│   ├── test_data_resource.py           # Wafer test data access
│   ├── historical_yield_resource.py    # Historical data access
│   └── mock_data.py                    # Realistic semiconductor test data
│
└── specs/
    ├── DESIGN.md                       # Detailed design document
    └── IMPLEMENTATION_PLAN.md          # Task breakdown and estimates
```

## Key Insights

### Why This Matters for Semiconductor Manufacturing

**Real-world impact:**
- Every 1% yield improvement = $10M+ annual revenue
- Wrong root cause analysis = weeks of wasted investigation
- Inconsistent analysis = loss of engineer trust
- Skipped steps = missed critical correlations

**Deterministic Autonomy delivers:**
- ✅ Rigorous engineering methodology (workflows)
- ✅ AI intelligence where it matters (LLM reasoning)
- ✅ Consistent, reproducible, explainable results
- ✅ Actionable recommendations with ROI justification

### When to Use Each Mode

**Use Automation when:**
- Process is fully defined (no ambiguity)
- No intelligence needed (simple rules)
- Zero tolerance for variation

**Use Probabilistic Autonomy when:**
- Creative exploration needed
- Novel problems (no playbook)
- Flexibility > consistency

**Use Deterministic Autonomy when:** ⭐
- High-stakes decisions (millions at risk)
- Engineering rigor required (can't skip steps)
- Need AI intelligence (pattern recognition, reasoning)
- Must be reproducible and explainable

## Next Steps

This demo implements **Deterministic mode only**. To see the full comparison, you could add:

1. **Automation mode** (`demo_automation.py`):
   - Rigid IF-THEN rules
   - No LLM intelligence
   - Shows limitations (can't classify novel patterns)

2. **Probabilistic mode** (`demo_probabilistic.py`):
   - Pure LLM agent (no workflows)
   - Might skip correlation analysis
   - Inconsistent results across runs

3. **Comparison demo** (`demo_comparison.py`):
   - Run all three modes on same data
   - Show differences in coverage, intelligence, consistency
   - Quantify value difference

## Related Demos

See also:
- **`../semi-multi/`** - Multi-agent coordinator pattern (Production Manager + Specialists)
- **`../SEMICONDUCTOR_DEMOS.md`** - Overview of both demos and autonomy modes

## Contact

For questions or feedback on this demo, please reach out to the Dana framework team.
