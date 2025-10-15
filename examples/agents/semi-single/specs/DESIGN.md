# Semi-Single: Yield Pareto Analysis Agent

## Overview

**Use Case:** Yield Pareto Analysis for semiconductor wafer test data

**Domain:** Semiconductor manufacturing - Final test yield optimization

**Objective:** Demonstrate the difference between automation, probabilistic autonomy, and deterministic autonomy in a single-agent, high-stakes technical task.

## Business Context

### The Problem

In semiconductor manufacturing, every chip that fails final test represents lost revenue. A typical fab produces millions of chips per month, and even a 1% yield improvement can generate $10M+ in annual revenue.

**Yield Pareto Analysis** is the standard process for identifying and prioritizing yield loss opportunities:

1. Collect test failure data from all chips
2. Categorize failures by bin (functional test failures)
3. Perform Pareto analysis (80/20 rule: which bins cause most loss?)
4. Prioritize top failing bins for engineering investigation
5. Generate actionable recommendations with ROI analysis

### Why This is High-Stakes

- **Financial:** 1% yield improvement = $10M+ annual revenue
- **Time-critical:** Yield issues compound daily (every day of delay = lost revenue)
- **Technical complexity:** Requires understanding electrical test data, failure modes, design architecture
- **Strategic:** Prioritization matters (which failures to fix first?)

### Why This Demonstrates the Three Modes

**Automation (Rule-based):**
- Can generate basic Pareto charts
- ❌ Can't interpret novel failure patterns
- ❌ Can't prioritize based on business context
- ❌ Can't generate actionable recommendations

**Probabilistic Autonomy (LLM-only):**
- Can reason about failure patterns intelligently
- ❌ Might skip critical analysis steps
- ❌ Inconsistent prioritization
- ❌ No guarantee of systematic investigation

**Deterministic Autonomy (Workflows + LLM):**
- ✅ Systematic analysis (can't skip steps)
- ✅ Intelligent reasoning (pattern recognition, prioritization)
- ✅ Consistent quality
- ✅ Verifiable recommendations

## Use Case Scenario

### Input Data
```python
wafer_test_results = {
    "wafer_id": "W12345",
    "product": "CPU_7nm_A53",
    "total_dies": 1000,
    "good_dies": 720,
    "yield": 0.72,
    "failure_bins": {
        "BIN_1": {"count": 150, "description": "SRAM fail"},
        "BIN_2": {"count": 80, "description": "Logic timing fail"},
        "BIN_3": {"count": 30, "description": "I/O fail"},
        "BIN_4": {"count": 20, "description": "Voltage regulator fail"},
        # ... more bins
    },
    "test_date": "2025-01-15",
    "product_context": {
        "asp": 150,  # Average selling price per die
        "volume": "10K wafers/month",
        "customer": "Tier-1 datacenter"
    }
}
```

### Expected Analysis

The agent must:
1. ✅ Calculate Pareto (cumulative % of failures)
2. ✅ Identify top failing bins (80% rule)
3. ✅ Analyze failure patterns (systematic vs random)
4. ✅ Correlate with historical data
5. ✅ Estimate revenue impact per bin
6. ✅ Prioritize by ROI (easiest to fix + highest revenue impact)
7. ✅ Generate actionable recommendations

## Architecture

### Single Agent: YieldParetoAnalysisAgent

**Deterministic Mode (with workflows):**
```python
class YieldParetoAnalysisAgent(STARAgent):
    """
    Systematic yield analysis with deterministic workflows.

    Workflows ensure:
    - Complete analysis (can't skip steps)
    - Consistent prioritization
    - Verifiable recommendations
    """

    def __init__(self):
        super().__init__(
            agent_type="yield-pareto-analysis",
            agent_id="yield-analyst-001",
            llm_provider="anthropic",
            model="claude-3-5-sonnet-20241022"
        )

        # Compose workflows
        self.with_workflows(
            YieldParetoWorkflow(workflow_id="pareto-analysis"),
            FailureCorrelationWorkflow(workflow_id="failure-correlation"),
            ROIPrioritizationWorkflow(workflow_id="roi-prioritization"),
        )

        # Compose resources
        self.with_resources(
            TestDataResource(resource_id="test-data"),
            HistoricalYieldResource(resource_id="historical-yield"),
            ConversationResource(resource_id="llm-reasoning"),
        )
```

**Probabilistic Mode (LLM-only):**
```python
class ProbabilisticYieldAgent(STARAgent):
    """
    LLM-only yield analysis - no workflow orchestration.

    LLM decides:
    - Which analysis steps to perform
    - How to prioritize
    - What recommendations to make

    Problem: Inconsistent, might skip steps
    """

    def __init__(self):
        super().__init__(
            agent_type="probabilistic-yield-analysis",
            llm_provider="anthropic",
            model="claude-3-5-sonnet-20241022"
        )

        # Resources available, but no workflow orchestration
        self.with_resources(
            TestDataResource(resource_id="test-data"),
            HistoricalYieldResource(resource_id="historical-yield"),
            ConversationResource(resource_id="llm-reasoning"),
        )

        # NO WORKFLOWS - LLM decides what to do
```

**Automation Mode (Rule-based):**
```python
class AutomatedYieldAnalysis:
    """
    Traditional rule-based Pareto analysis.

    Rigid rules:
    - Sort bins by count
    - Calculate cumulative %
    - Flag top 80%

    Problem: No intelligent reasoning, brittle
    """

    def analyze(self, test_data):
        # Sort by failure count
        sorted_bins = sorted(test_data["failure_bins"].items(),
                           key=lambda x: x[1]["count"], reverse=True)

        # Calculate cumulative %
        total_fails = sum(b["count"] for b in test_data["failure_bins"].values())
        cumulative = 0
        pareto_bins = []

        for bin_id, data in sorted_bins:
            cumulative += data["count"] / total_fails
            pareto_bins.append({
                "bin": bin_id,
                "count": data["count"],
                "cumulative": cumulative
            })
            if cumulative >= 0.8:
                break

        # Rigid output - no intelligent recommendations
        return {
            "top_bins": pareto_bins,
            "recommendation": "Investigate top bins in order"
        }
```

## Workflows

### 1. YieldParetoWorkflow

**Purpose:** Systematic Pareto analysis

**Steps:**
1. **Data Collection** - Gather test results, product context
2. **Bin Sorting** - Sort failure bins by count
3. **Pareto Calculation** - Calculate cumulative % failures
4. **Top Bin Identification** - Identify bins representing 80% of failures
5. **Pattern Recognition** (LLM) - Identify systematic vs random patterns
6. **Output** - Structured Pareto with classifications

**LLM Intelligence:**
- Pattern recognition: "BIN_1 (SRAM fail) shows spatial clustering → systematic"
- Failure mode understanding: "SRAM failures often process-related"

**Workflow Enforcement:**
- Can't skip Pareto calculation
- Must identify top bins
- Must classify patterns

### 2. FailureCorrelationWorkflow

**Purpose:** Correlate failures with historical data and process changes

**Steps:**
1. **Historical Lookup** - Get similar products/wafers
2. **Trend Analysis** - Is this failure rate increasing/decreasing?
3. **Process Correlation** (LLM) - Recent process changes?
4. **Root Cause Hypothesis** (LLM) - Generate initial hypotheses
5. **Output** - Correlation findings with confidence

**LLM Intelligence:**
- Correlation reasoning: "SRAM failures increased after etch recipe change 2 weeks ago"
- Hypothesis generation: "Likely etch-induced damage to SRAM cells"

**Workflow Enforcement:**
- Must check historical data
- Must identify trends
- Must generate hypotheses

### 3. ROIPrioritizationWorkflow

**Purpose:** Prioritize failures by ROI (revenue impact + fix difficulty)

**Steps:**
1. **Revenue Impact** - Calculate per-bin revenue loss (count × ASP)
2. **Fix Difficulty** (LLM) - Assess engineering effort (easy/medium/hard)
3. **ROI Scoring** - Score each bin: revenue_impact / fix_difficulty
4. **Prioritization** - Rank bins by ROI score
5. **Action Plan** (LLM) - Generate specific recommendations
6. **Output** - Prioritized action plan with ROI justification

**LLM Intelligence:**
- Fix difficulty assessment: "I/O failures typically circuit design fix (hard), SRAM failures often process tuning (medium)"
- Action plan generation: "Recommend immediate process DOE for SRAM, defer I/O to next design rev"

**Workflow Enforcement:**
- Must calculate revenue impact for all top bins
- Must assess fix difficulty
- Must prioritize systematically
- Can't skip ROI analysis

## Resources

### 1. TestDataResource

```python
class TestDataResource(BaseResource):
    """Access wafer test data."""

    def get_test_results(self, wafer_id):
        """Fetch test results for a wafer."""

    def get_bin_details(self, bin_id):
        """Get detailed bin description and test conditions."""
```

### 2. HistoricalYieldResource

```python
class HistoricalYieldResource(BaseResource):
    """Access historical yield data for trend analysis."""

    def get_product_yield_trend(self, product, weeks=12):
        """Get yield trend for product over time."""

    def get_similar_failures(self, bin_id, product):
        """Find historical similar failure patterns."""
```

### 3. ConversationResource (from library)

Standard LLM reasoning resource for intelligent analysis.

## Demo Scripts

### Mode 1: demo_automation.py

Shows rule-based Pareto analysis (brittle, no intelligence)

### Mode 2: demo_probabilistic.py

Shows LLM-only analysis (flexible but inconsistent)

### Mode 3: demo_deterministic.py

Shows workflow-orchestrated analysis (systematic + intelligent)

### Mode Comparison: demo_comparison.py

Runs all three modes side-by-side on same data to show differences.

## Success Metrics

The demo should clearly show:

1. **Automation:**
   - ✅ Generates basic Pareto chart
   - ❌ No pattern recognition
   - ❌ No intelligent prioritization
   - ❌ Brittle recommendations

2. **Probabilistic:**
   - ✅ Intelligent pattern recognition
   - ✅ Context-aware recommendations
   - ❌ Inconsistent (might skip ROI analysis)
   - ❌ Unreliable for production

3. **Deterministic:**
   - ✅ Systematic analysis (all steps executed)
   - ✅ Intelligent reasoning (pattern recognition, ROI)
   - ✅ Consistent quality
   - ✅ Verifiable recommendations
   - ✅ **Production-ready**

## Value Proposition

**"In semiconductor yield optimization, you can't afford probabilistic behavior. Deterministic autonomy ensures systematic analysis while leveraging LLM intelligence for pattern recognition and prioritization."**

**Financial Impact:**
- Systematic analysis finds 20% more optimization opportunities
- Intelligent prioritization focuses effort on highest ROI fixes
- Consistent quality prevents missed opportunities
- Result: Millions in additional revenue from yield improvement
