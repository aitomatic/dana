# Demo Output Example

This document shows what the `demo_deterministic.py` output looks like when run with an Anthropic API key.

## Console Output Structure

### 1. Introduction
```
================================================================================
  DETERMINISTIC YIELD ANALYSIS DEMO
================================================================================

This demo demonstrates DETERMINISTIC AUTONOMY for semiconductor yield analysis.

The agent will execute three systematic workflows:
  1. Pareto Analysis     - Identify top failing bins (80/20 rule)
  2. Correlation Analysis - Connect to historical data and process changes
  3. ROI Prioritization   - Rank by revenue impact vs fix difficulty

Watch the workflow progress in real-time below...

Setting up agent and logger...
✓ Agent and logger ready
```

### 2. Workflow Progress (Real-time in Gray)
```
================================================================================
  EXECUTING DETERMINISTIC ANALYSIS
================================================================================

(Workflow progress shown below in gray...)

👁️  SEE    [yield-pareto-agent] Received: Analyze yield
🧠 THINK   [yield-pareto-agent] Phase 1/3: Running Pareto analysis...
⚙️  WORKFLOW [pareto-analysis] Collecting wafer test data...
⚙️  WORKFLOW [pareto-analysis] Sorting failure bins by count...
⚙️  WORKFLOW [pareto-analysis] Calculating Pareto cumulative percentages...
🤖 WORKFLOW [pareto-analysis] Analyzing failure patterns with LLM...
✅ WORKFLOW [pareto-analysis] Pareto analysis complete: 3 top bins identified (80% rule)

🧠 THINK   [yield-pareto-agent] Phase 2/3: Correlating 3 top bins with historical data...
⚙️  WORKFLOW [failure-correlation] Retrieving 12 weeks of yield history...
⚙️  WORKFLOW [failure-correlation] Searching for historical similar failure patterns...
🤖 WORKFLOW [failure-correlation] Analyzing process change correlations...
🤖 WORKFLOW [failure-correlation] Generating root cause hypotheses...
✅ WORKFLOW [failure-correlation] Correlation analysis complete: 2 hypotheses generated

🧠 THINK   [yield-pareto-agent] Phase 3/3: Calculating ROI and prioritizing actions...
⚙️  WORKFLOW [roi-prioritization] Calculating revenue impact per bin...
🤖 WORKFLOW [roi-prioritization] Assessing fix difficulty with LLM...
⚙️  WORKFLOW [roi-prioritization] Calculating ROI scores...
⚙️  WORKFLOW [roi-prioritization] Ranking bins by ROI score...
🤖 WORKFLOW [roi-prioritization] Generating actionable recommendations with LLM...
✅ WORKFLOW [roi-prioritization] ROI prioritization complete: $564,000,000 annual opportunity

✅ WORKFLOW [yield-pareto-agent] Analysis complete: $564,000,000 opportunity identified across 3 bins

✅ Analysis completed successfully!
```

### 3. Executive Summary
```
================================================================================
  EXECUTIVE SUMMARY
================================================================================

Wafer ID:          W12345-789
Product:           CPU_7nm_A53_HiPerf
Current Yield:     68.5%
Yield Trend:       FLAT (-1.0%)
Total Failures:    315

Pareto Bins:       3 bins represent 80% of failures
Revenue at Risk:   $564,000,000 annually

Top Priority:      BIN_1
  Impact:          $324,000,000/year

Likely Root Cause: Similar to historical case: Metal etch over-etch causing SRAM cell damage
  Confidence:      HIGH
```

### 4. Pareto Analysis Table
```
================================================================================
  PARETO ANALYSIS (Top Bins - 80% Rule)
================================================================================

Rank   Bin ID       Description                    Count    %      Cum%   Pattern
--------------------------------------------------------------------------------
1      BIN_1        SRAM bit failures              180      57.1   57.1   clustered
2      BIN_2        Logic path timing violations    75      23.8   81.0   random
3      BIN_3        I/O buffer failures             35      11.1   92.1   systematic
```

**Analysis:**
- **BIN_1 (57.1%)**: SRAM failures with clustered pattern → Likely process issue (fixable!)
- **BIN_2 (23.8%)**: Timing violations with random pattern → Design margin issue (harder to fix)
- **BIN_3 (11.1%)**: I/O failures with systematic pattern → Package/assembly issue

These 3 bins represent 92.1% of all failures, exceeding the 80% Pareto threshold.

### 5. Root Cause Hypotheses
```
================================================================================
  ROOT CAUSE HYPOTHESES (Evidence-Based)
================================================================================

Hypothesis #1: Similar to historical case: Metal etch over-etch causing SRAM cell damage
  Confidence: HIGH
  Evidence:
    • Very similar failure pattern (similarity: 0.92)
    • Historical case: YLD-2023-087
    • Previous resolution: Reduced etch RF power by 8%, adjusted etch time
  Next Steps: Apply similar resolution approach: Reduced etch RF power by 8%, adjusted etch time

Hypothesis #2: Process change impact: Suspected cause of SRAM yield loss - more aggressive etch may damage cell structures
  Confidence: MEDIUM-HIGH
  Evidence:
    • Process change: Metal etch recipe: Increased RF power 5% for throughput improvement
    • Timing correlation: 2024-W50
    • Yield degradation coincides with change
  Next Steps: Run DOE to test process parameter sensitivity
```

**Key Insight:**
Both hypotheses point to the same root cause: **metal etch process change** in Week 50. The increased RF power (for throughput) is likely damaging SRAM cell structures. HIGH confidence because we have a 92% similar historical case with known resolution.

### 6. Prioritized Action Plan
```
================================================================================
  PRIORITIZED ACTION PLAN (ROI-Ranked)
================================================================================

#1 - BIN_1: SRAM bit failures
  Revenue Impact:  $324,000,000/year
  Fix Difficulty:  MEDIUM
  ROI Score:       486,000,000
  Priority:        HIGH PRIORITY: Significant revenue impact ($324,000,000/year) with moderate fix difficulty. Good ROI.
  Timeline:        10-20 days
  Actions:
    • Immediate DOE on process parameters
    • Check recent process recipe changes
    • Compare with historical similar cases

#2 - BIN_2: Logic path timing violations
  Revenue Impact:  $135,000,000/year
  Fix Difficulty:  HARD
  ROI Score:       67,500,000
  Priority:        STRATEGIC: Large revenue impact ($135,000,000/year) but hard to fix. Long-term investment.
  Timeline:        60-90 days (design rev)
  Actions:
    • Deep root cause investigation
    • Design for manufacturability review
    • Long-term process development

#3 - BIN_3: I/O buffer failures
  Revenue Impact:  $63,000,000/year
  Fix Difficulty:  MEDIUM
  ROI Score:       94,500,000
  Priority:        HIGH PRIORITY: Significant revenue impact ($63,000,000/year) with moderate fix difficulty. Good ROI.
  Timeline:        15-30 days
  Actions:
    • Detailed failure analysis (SEM, TEM)
    • Process characterization split lots
    • Correlation with metrology data
```

**Action Priority Explanation:**
1. **BIN_1 (ROI: 486M)**: Highest priority - large impact, fixable in 10-20 days
2. **BIN_3 (ROI: 94.5M)**: Second priority - good ROI, moderate difficulty
3. **BIN_2 (ROI: 67.5M)**: Strategic - large impact but hard to fix (60-90 days)

ROI Score formula: `Annual Revenue Impact × Difficulty Multiplier`
- EASY fix = 3x multiplier
- MEDIUM fix = 1.5x multiplier
- HARD fix = 0.5x multiplier

### 7. Value Demonstration
```
================================================================================
  VALUE OF DETERMINISTIC AUTONOMY
================================================================================

✓ SYSTEMATIC: Executed 3 workflows
  - Can't skip steps (engineering rigor)
  - Every bin analyzed (comprehensive)
  - Pareto, correlation, ROI always performed

✓ INTELLIGENT: LLM applied at key decision points
  - Pattern classification (systematic vs random)
  - Process correlation reasoning
  - Root cause hypothesis generation
  - Actionable recommendation synthesis

✓ ACTIONABLE: Clear prioritized plan
  - $564,000,000 annual revenue opportunity identified
  - 3 bins prioritized by ROI
  - Specific next steps with timelines
  - Evidence-based root cause hypotheses

✓ CONSISTENT: Same analysis every time
  - Deterministic workflow sequence
  - Reproducible results
  - Explainable reasoning
  - Engineer trust

Compare this to:
  × Automation: No AI intelligence, can't handle novel patterns
  × Probabilistic: Might skip steps, inconsistent analysis, hard to trust

================================================================================
  DEMO COMPLETE
================================================================================

This demo showed how DETERMINISTIC AUTONOMY combines:
  • Systematic engineering workflows (structure)
  • LLM intelligence (reasoning)
  → Reliable, comprehensive, actionable yield analysis

The workflows are visible, explainable, and trustworthy - perfect for
high-stakes semiconductor manufacturing where mistakes cost millions.
```

## Key Takeaways

### Business Impact
- **$564M** annual revenue opportunity identified
- **$324M/year** from top priority (BIN_1) alone
- **10-20 days** to fix top priority (fast ROI)
- **92% similarity** to historical case (high confidence in solution)

### Technical Excellence
- **Comprehensive**: All 3 workflows executed (Pareto, Correlation, ROI)
- **Systematic**: Can't skip critical analysis steps
- **Intelligent**: LLM reasoning at 4 key decision points
- **Reproducible**: Same analysis every time
- **Explainable**: Clear reasoning trail for engineer trust

### Autonomy Mode Comparison

| Feature | Automation | Probabilistic | **Deterministic** |
|---------|-----------|---------------|-------------------|
| Structure | ✅ Rigid rules | ❌ LLM decides | ✅ Workflows enforce |
| Intelligence | ❌ None | ✅ Full AI | ✅ LLM at decision points |
| Consistency | ✅ Perfect | ❌ Varies | ✅ Reproducible |
| Novel patterns | ❌ Fails | ✅ Handles | ✅ Handles |
| Completeness | ✅ All steps | ❌ Might skip | ✅ All steps |
| Explainability | ✅ Simple | ❌ Black box | ✅ Clear reasoning |
| **Use Case** | Simple tasks | Exploration | **High-stakes industrial** |

**Winner for Semiconductor Yield Analysis: Deterministic Autonomy** ⭐

It combines the best of both worlds:
- Structure and completeness of automation
- Intelligence and adaptability of probabilistic AI
- Reproducibility and explainability for engineer trust
- Perfect for high-stakes decisions where mistakes cost millions

## Running the Demo Yourself

To see this output for yourself:

```bash
# Set your Anthropic API key
export ANTHROPIC_API_KEY='your-key-here'

# Run the demo
cd examples/agents/semi-single
python demo_deterministic.py
```

The demo takes about 60-90 seconds to complete (3 workflows × 3-4 LLM calls each).
