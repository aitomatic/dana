# Comparing Three Patterns: Automation, Probabilistic Autonomy, Deterministic Autonomy

This directory contains three demos showing fundamentally different approaches to the same task:
**"Analyze yield failures for wafer W12345"**

## Quick Comparison

| Pattern | Intelligence | Flexibility | Completeness | Reliability |
|---------|-------------|-------------|--------------|-------------|
| **(A) Automation** | ❌ None | ❌ Fixed sequence | ✅ All steps run | ⚠️ Might do unnecessary work |
| **(B) Probabilistic Autonomy** | ✅ Agent decides | ✅ Adapts to data | ❌ Might skip steps | ⚠️ Inconsistent results |
| **(C) Deterministic Autonomy** | ✅ Agent decides | ✅ Adapts to data | ✅ All steps guaranteed | ✅ Systematic quality |

## (A) Automation - `run_a_automation_demo.py`

### What it is:
Pure automation with no intelligence. Like a traditional script or cron job.

### How it works:
```
1. Run Pareto workflow (always)
2. Run Correlation workflow (always)
3. Run ROI workflow (always)
4. Print report (always)
```

### Characteristics:
- ❌ **No intelligence** - Just executes fixed steps
- ❌ **No adaptation** - Always runs same sequence
- ✅ **Predictable** - Always does the same thing
- ⚠️ **Might waste time** - Runs all steps even if not needed

### When to use:
- Process is well-defined and never changes
- Speed is critical (no LLM calls for decisions)
- You want 100% predictability

### Example output:
```
STEP 1: Running Pareto Analysis (fixed step)
✓ Pareto complete: 4 top bins identified

STEP 2: Running Failure Correlation (fixed step)
✓ Correlation complete: 2 hypotheses generated

STEP 3: Running ROI Prioritization (fixed step)
✓ ROI complete: 4 actions prioritized
```

---

## (B) Probabilistic Autonomy - `run_b_probabilistic_autonomy_demo.py`

### What it is:
Agent makes decisions about what to analyze, but might skip important steps.

### How it works:
```
Agent: "Should I run Pareto?" → Decides YES
  [Runs Pareto]

Agent: "Do I need correlation?" → Might decide NO (skip!)
  [Skips correlation - missing data!]

Agent: "Should I calculate ROI?" → Might decide NO (skip!)
  [Makes quick recommendation without ROI analysis]
```

### Characteristics:
- ✅ **Intelligent** - Agent makes decisions
- ✅ **Flexible** - Adapts to data
- ❌ **Might skip steps** - Decisions are probabilistic
- ❌ **Incomplete results** - Missing data affects quality
- ⚠️ **Hard to guarantee quality** - Results vary by agent's choices

### When to use:
- You need flexibility over consistency
- Quick results acceptable, even if incomplete
- You can tolerate missing analysis

### Example output:
```
AGENT REASONING: Should I run correlation analysis?
Agent reasoning: Hmm, patterns look random...
→ Agent decision: SKIP correlation analysis (probably not needed)
  ⚠️  RISK: Might be missing important historical context!

Root cause analysis: SKIPPED ⚠️
ROI prioritization: SKIPPED ⚠️
```

---

## (C) Deterministic Autonomy - `run_c_deterministic_autonomy_demo.py` ⭐ **STRONGEST**

### What it is:
Agent decides which workflows to run, but workflows guarantee ALL steps are completed.

### How it works:
```
Agent: "I need to understand failure distribution first"
  → Runs Pareto workflow (DETERMINISTIC)
      ✓ Data collection (can't skip)
      ✓ Bin sorting (can't skip)
      ✓ Pareto calculation (can't skip)
      ✓ Pattern classification via WorkflowStepAgent (can't skip)
      ✓ Output generation (can't skip)

Agent reviews COMPLETE Pareto data: "I see systematic patterns"
  → Runs Correlation workflow (DETERMINISTIC)
      ✓ Historical lookup (can't skip)
      ✓ Similar cases search (can't skip)
      ✓ Process correlation via WorkflowStepAgent (can't skip)
      ✓ Hypothesis generation via WorkflowStepAgent (can't skip)
      ✓ Output generation (can't skip)

Agent reviews COMPLETE correlation data: "I need to prioritize by ROI"
  → Runs ROI workflow (DETERMINISTIC)
      ✓ Revenue calculation (can't skip)
      ✓ Fix difficulty assessment (can't skip)
      ✓ ROI scoring (can't skip)
      ✓ Ranking (can't skip)
      ✓ Recommendations via WorkflowStepAgent (can't skip)
      ✓ Output generation (can't skip)

Agent generates comprehensive report with ALL data points
```

### Characteristics:
- ✅ **Intelligent** - Agent makes decisions
- ✅ **Flexible** - Adapts to data
- ✅ **Complete** - Workflows guarantee all steps executed
- ✅ **Systematic** - Structured, reliable results
- ✅ **STRONGEST** - Combines intelligence with quality assurance

### Key Architecture:
1. **Calling agent decides** which workflows to run (autonomous, goal-directed)
2. **Workflows execute deterministically** (can't skip steps within workflow)
3. **Workflows use WorkflowStepAgent** for intelligence at decision points
4. **Agent gets complete data** to make next decision

### When to use:
- You need both intelligence AND reliability
- Quality assurance is critical
- You want comprehensive, systematic results
- **This is the recommended pattern for production systems**

### Example output:
```
AGENT REASONING: What workflow should I run first?
Agent decision: I need to understand failure distribution first.
→ Running Pareto workflow (deterministic - ALL steps executed)

✓ Pareto workflow complete (all steps executed)
  - Data collected: 10000 dies
  - Bins sorted: 8 bins
  - Pareto calculated: 4 top bins (80% rule)
  - Patterns classified: 4 bins analyzed
  - Yield: 85.4%

AGENT REASONING: Based on complete Pareto data, what next?
Agent reviews structured data:
  - Systematic patterns detected: True
  - Top bins: 4

Agent decision: I need historical context to understand root causes.
→ Running Correlation workflow (deterministic - ALL steps executed)

✓ Correlation workflow complete (all steps executed)
  - Historical data retrieved: 87.2% yield
  - Similar cases found: 2
  - Process correlations analyzed: True
  - Hypotheses generated: 2

[... continues with complete, systematic analysis ...]
```

---

## Running the Demos

```bash
# (A) Automation - Fixed sequence, no intelligence
python run_a_automation_demo.py

# (B) Probabilistic Autonomy - Agent decides, might skip steps
python run_b_probabilistic_autonomy_demo.py

# (C) Deterministic Autonomy - Agent decides, workflows guarantee completeness ⭐
python run_c_deterministic_autonomy_demo.py
```

## Key Insight: Why (C) is STRONGEST

**Deterministic Autonomy combines the best of both worlds:**

| Aspect | How (C) Achieves It |
|--------|-------------------|
| **Intelligence** | Agent (LLM) makes goal-directed decisions |
| **Flexibility** | Agent adapts based on data from each workflow |
| **Completeness** | Workflows execute ALL steps (can't skip) |
| **Quality** | Workflows use WorkflowStepAgent for systematic intelligence |
| **Reliability** | Agent gets complete, structured data to make informed decisions |

### The Magic:
- **Agent level**: Flexible, autonomous, goal-directed (can skip workflows)
- **Workflow level**: Deterministic, complete, systematic (can't skip steps)
- **Intelligence**: Injected via WorkflowStepAgent at workflow decision points

This architecture ensures you get both **AI intelligence** AND **systematic quality assurance**.

---

## Visual Comparison

### (A) Automation:
```
START → Pareto → Correlation → ROI → END
        (fixed)  (fixed)       (fixed)
```

### (B) Probabilistic Autonomy:
```
START → [Agent decides] → Maybe Pareto → [Agent decides] → Maybe Correlation? → END
                         (might be incomplete)            (might skip!)
```

### (C) Deterministic Autonomy: ⭐
```
START → [Agent decides] → Pareto (ALL STEPS ✓) → [Agent decides] → Correlation (ALL STEPS ✓) → [Agent decides] → ROI (ALL STEPS ✓) → END
        "Need distribution"   ├─ Collect            "Need root cause"    ├─ Historical           "Need priorities"   ├─ Revenue calc
                              ├─ Sort                                     ├─ Similar cases                           ├─ Fix difficulty
                              ├─ Calculate                                ├─ Process correlations                    ├─ ROI score
                              ├─ Classify (WorkflowStepAgent)            ├─ Hypotheses (WorkflowStepAgent)         ├─ Rank
                              └─ Output (complete!)                       └─ Output (complete!)                      └─ Recommendations (WorkflowStepAgent)
                                                                                                                      └─ Output (complete!)
```

## Summary

Choose based on your needs:
- **(A) Automation**: Need speed and predictability, no intelligence required
- **(B) Probabilistic Autonomy**: Need flexibility, can accept incomplete results
- **(C) Deterministic Autonomy**: Need intelligence AND reliability ⭐ **RECOMMENDED**
