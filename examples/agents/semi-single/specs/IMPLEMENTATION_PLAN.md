# Semi-Single Implementation Plan & Tracker

## Project: Yield Pareto Analysis Agent - Three Modes Demo

## Objectives

1. Implement YieldParetoAnalysisAgent (deterministic mode with workflows)
2. Implement ProbabilisticYieldAgent (probabilistic mode, LLM-only)
3. Implement AutomatedYieldAnalysis (traditional automation, rule-based)
4. Create compelling demo comparing all three modes
5. Show clear value proposition for deterministic autonomy

## Implementation Phases

### Phase 1: Foundation - Resources

**Purpose:** Create data access and mock test data

#### Tasks

- [ ] **1.1 Create TestDataResource**
  - File: `resources/test_data_resource.py`
  - Methods:
    - `get_test_results(wafer_id)` - Returns mock wafer test data
    - `get_bin_details(bin_id)` - Returns bin description
  - Mock data: Realistic semiconductor test results with ~10 failure bins
  - Estimated: 1 hour

- [ ] **1.2 Create HistoricalYieldResource**
  - File: `resources/historical_yield_resource.py`
  - Methods:
    - `get_product_yield_trend(product, weeks)` - Returns yield trend data
    - `get_similar_failures(bin_id, product)` - Returns historical similar patterns
  - Mock data: Historical yield trends, previous failure cases
  - Estimated: 1 hour

- [ ] **1.3 Create mock test dataset**
  - File: `resources/mock_data.py`
  - Realistic failure bins with interesting patterns:
    - SRAM failures (systematic - process issue)
    - Logic timing (random - design margin)
    - I/O failures (systematic - package issue)
  - Include product context (ASP, volume, customer tier)
  - Estimated: 30 min

**Phase 1 Deliverables:**
- Working resources with realistic mock data
- Ready for agent integration

---

### Phase 2: Workflows (Deterministic Mode)

**Purpose:** Create systematic workflows for yield analysis

#### Tasks

- [ ] **2.1 Create YieldParetoWorkflow**
  - File: `workflows/yield_pareto_workflow.py`
  - Steps:
    1. Data collection and validation
    2. Bin sorting by failure count
    3. Pareto calculation (cumulative %)
    4. Top bin identification (80% rule)
    5. Pattern classification (LLM: systematic vs random)
  - Broadcasts: Progress at each step
  - Validation: Ensure all bins properly classified
  - Estimated: 2 hours

- [ ] **2.2 Create FailureCorrelationWorkflow**
  - File: `workflows/failure_correlation_workflow.py`
  - Steps:
    1. Historical data lookup
    2. Trend analysis (improving/degrading/stable)
    3. Process correlation (LLM reasoning)
    4. Root cause hypothesis generation (LLM)
  - Broadcasts: Correlation findings
  - Output: Structured correlation with confidence
  - Estimated: 2 hours

- [ ] **2.3 Create ROIPrioritizationWorkflow**
  - File: `workflows/roi_prioritization_workflow.py`
  - Steps:
    1. Revenue impact calculation (count × ASP)
    2. Fix difficulty assessment (LLM: easy/medium/hard)
    3. ROI scoring (revenue / difficulty)
    4. Prioritization ranking
    5. Action plan generation (LLM: specific recommendations)
  - Broadcasts: ROI calculations and prioritization
  - Output: Prioritized action plan with justification
  - Estimated: 2 hours

**Phase 2 Deliverables:**
- Three working workflows
- Systematic, verifiable yield analysis process

---

### Phase 3: Agents (Three Modes)

**Purpose:** Implement agents for all three autonomy modes

#### Tasks

- [ ] **3.1 Create YieldParetoAnalysisAgent (Deterministic)**
  - File: `agents/yield_pareto_analysis_agent.py`
  - Compose: All three workflows + resources
  - Prompt: Mandate workflow usage for systematic analysis
  - Expected behavior: Always runs all workflows in sequence
  - Estimated: 1 hour

- [ ] **3.2 Create ProbabilisticYieldAgent (Probabilistic)**
  - File: `agents/probabilistic_yield_agent.py`
  - Compose: Resources only (NO workflows)
  - Prompt: Allow LLM to decide analysis approach
  - Expected behavior: Inconsistent - sometimes thorough, sometimes superficial
  - Estimated: 30 min

- [ ] **3.3 Create AutomatedYieldAnalysis (Automation)**
  - File: `agents/automated_yield_analysis.py`
  - Pure Python class (no STARAgent, no LLM)
  - Rule-based Pareto calculation
  - Expected behavior: Rigid, no intelligence, brittle
  - Estimated: 30 min

**Phase 3 Deliverables:**
- Three agents representing three autonomy modes
- Ready for demo comparison

---

### Phase 4: Demo Scripts

**Purpose:** Create compelling demonstrations of all three modes

#### Tasks

- [ ] **4.1 Create demo_automation.py**
  - Shows: Rule-based Pareto (automation mode)
  - Highlights:
    - ✅ Basic Pareto chart generation
    - ❌ No pattern recognition
    - ❌ No intelligent prioritization
    - ❌ Rigid recommendations
  - Estimated: 1 hour

- [ ] **4.2 Create demo_probabilistic.py**
  - Shows: LLM-only analysis (probabilistic mode)
  - Run multiple times to show inconsistency
  - Highlights:
    - ✅ Intelligent pattern recognition
    - ✅ Context-aware reasoning
    - ❌ Inconsistent behavior (might skip steps)
    - ❌ Not production-ready
  - Estimated: 1 hour

- [ ] **4.3 Create demo_deterministic.py**
  - Shows: Workflow-orchestrated analysis (deterministic mode)
  - Include ThoughtLogger for visible workflow progress
  - Highlights:
    - ✅ Systematic (all steps executed)
    - ✅ Intelligent (LLM reasoning)
    - ✅ Consistent quality
    - ✅ Verifiable recommendations
  - Estimated: 1 hour

- [ ] **4.4 Create demo_comparison.py**
  - Side-by-side comparison of all three modes
  - Same input data for fair comparison
  - Clear output showing differences
  - Summary: Why deterministic is superior
  - Estimated: 2 hours

- [ ] **4.5 Create README.md**
  - Overview of the demo
  - How to run each mode
  - Expected output and key insights
  - Business value proposition
  - Estimated: 1 hour

**Phase 4 Deliverables:**
- Complete demo suite
- Clear demonstration of value proposition

---

## Testing & Validation

### Test Cases

- [ ] **Automation Mode:**
  - Generates correct Pareto chart
  - Identifies top bins (80% rule)
  - Shows brittleness on edge cases

- [ ] **Probabilistic Mode:**
  - Run 5 times, verify inconsistent behavior
  - Show: Sometimes thorough, sometimes skips steps
  - Document variance in quality

- [ ] **Deterministic Mode:**
  - Run 5 times, verify consistent workflow execution
  - All workflows execute in sequence
  - All steps broadcast progress
  - Output quality consistent

- [ ] **Comparison Demo:**
  - All three modes run on same data
  - Clear differences highlighted
  - Value proposition evident

---

## Timeline Estimates

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1: Resources | 3 tasks | 2.5 hours |
| Phase 2: Workflows | 3 tasks | 6 hours |
| Phase 3: Agents | 3 tasks | 2 hours |
| Phase 4: Demos | 5 tasks | 6 hours |
| **Total** | **14 tasks** | **16.5 hours** |

---

## Success Criteria

✅ All three modes working and demonstrable
✅ Clear behavioral differences shown
✅ Deterministic mode shows superior reliability
✅ Probabilistic mode shows inconsistency
✅ Automation mode shows brittleness
✅ Business value proposition clear
✅ Production-ready code quality
✅ Comprehensive documentation

---

## Implementation Status

**Overall Progress:** 0/14 tasks completed (0%)

### Phase 1: Resources (0/3)
- [ ] TestDataResource
- [ ] HistoricalYieldResource
- [ ] Mock test dataset

### Phase 2: Workflows (0/3)
- [ ] YieldParetoWorkflow
- [ ] FailureCorrelationWorkflow
- [ ] ROIPrioritizationWorkflow

### Phase 3: Agents (0/3)
- [ ] YieldParetoAnalysisAgent (Deterministic)
- [ ] ProbabilisticYieldAgent (Probabilistic)
- [ ] AutomatedYieldAnalysis (Automation)

### Phase 4: Demos (0/5)
- [ ] demo_automation.py
- [ ] demo_probabilistic.py
- [ ] demo_deterministic.py
- [ ] demo_comparison.py
- [ ] README.md

---

## Notes

- Focus on clarity of value proposition
- Make differences between modes obvious
- Use realistic semiconductor data
- Show financial impact ($10M yield improvement)
- Include visible thinking (ThoughtLogger) for deterministic mode
- Run probabilistic multiple times to show variance
