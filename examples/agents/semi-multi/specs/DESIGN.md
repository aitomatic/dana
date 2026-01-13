# Semi-Multi: Production Manager + Specialist Team

## Overview

**Use Case:** Novel Defect Pattern Investigation and Resolution

**Domain:** Semiconductor manufacturing - Inline defect detection and response

**Objective:** Demonstrate the difference between automation, probabilistic autonomy, and deterministic autonomy in a **multi-agent coordinator pattern** with human-in-the-loop at strategic decision points.

## Business Context

### The Problem

A defect detection system identifies an **unknown pattern** on wafers during production. The production team must:

1. **Investigate systematically** - What is this defect? Root cause?
2. **Assess risk** - Should we stop production? Hold material?
3. **Take corrective action** - How do we fix it?
4. **Verify effectiveness** - Did the fix work?
5. **Document for compliance** - ISO/IATF requirements

This requires **coordination** across multiple disciplines:
- **Production Manager** - Owns production decisions, customer impact
- **Defect Specialist** - Systematic investigation expertise
- **Process Engineer** - Corrective action execution

### Why This is High-Stakes

- **Financial:** Wafer lot = $500K-$1M, stopping production = $1M/day lost revenue
- **Customer impact:** Shipping defective product = returns, reputation damage
- **Compliance:** ISO/IATF requires documented investigation and corrective action
- **Time-critical:** Every hour counts (defects compound with each wafer)

### Why This Demonstrates Multi-Agent Value

**Single agent limitations:**
- Technical specialist overwhelms user with details
- User (production manager) needs strategic summary, not technical details
- No clear separation: investigation vs decision vs action

**Multi-agent advantages:**
- **Coordinator** (ProductionManagerAgent) interfaces with user at strategic level
- **Specialists** do detailed technical work autonomously
- **Human-in-the-loop** at right level (approve/reject, not micro-decisions)
- **Realistic workflow** mirrors real fab organization

## Use Case Scenario

### Initial Alert

```
Defect Alert - Inline Inspection System
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Wafer Lot: ABC123
Product: CPU_7nm_A53
Defect Type: UNKNOWN (not in library)
Pattern: Circular clusters, ~5μm diameter
Location: Wafer edge, 120° sector, repeating
Frequency: 15% of wafers affected
Process step: Metal etch, Chamber 3
Detected: 2025-01-15 14:30

Status: ⚠️ PRODUCTION CONTINUING
Action: Requires investigation
```

### Required Response

**Investigation → Risk Assessment → Decision → Action → Verification → Closure**

This naturally maps to multi-agent workflow:
1. **ProductionManager** receives alert, delegates to **DefectSpecialist**
2. **DefectSpecialist** systematically investigates
3. **ProductionManager** assesses risk, presents options to **User**
4. **User** approves corrective action
5. **ProcessEngineer** executes fix
6. **ProductionManager** verifies effectiveness, closes loop

## Architecture

### Multi-Agent Hierarchy

```
User (Fab Production Manager)
  ↕ (strategic decisions: approve/reject)
ProductionManagerAgent (Coordinator)
  ↕ (delegates work, monitors, summarizes)
  ├── DefectSpecialistAgent (Technical investigation)
  └── ProcessEngineerAgent (Corrective action execution)
```

### Agent Responsibilities

#### 1. ProductionManagerAgent (Coordinator)

**Role:** User-facing coordinator, strategic decisions, workflow orchestration

**Responsibilities:**
- Receive defect alerts from user
- Assess severity and urgency
- Delegate investigation to DefectSpecialist
- Translate technical findings to business language
- Present options and recommendations to user
- Get user approval for production-impacting actions
- Delegate corrective action to ProcessEngineer
- Verify effectiveness and close loop
- Document per ISO/IATF requirements

**Workflows:**
- `DefectResponseWorkflow` - Orchestrate overall response
- `RiskAssessmentWorkflow` - Assess production and customer risk
- `VerificationWorkflow` - Verify corrective action effectiveness

**Key Behavior:**
- **Human-in-the-loop gates:**
  - Approve/reject holding production
  - Approve/reject corrective action plan
  - Approve/reject releasing held material

#### 2. DefectSpecialistAgent (Technical Expert)

**Role:** Systematic defect investigation, root cause analysis

**Responsibilities:**
- Receive investigation request from ProductionManager
- Execute systematic investigation workflow
- Analyze defect patterns (LLM intelligence)
- Correlate with process/material changes
- Search historical similar patterns
- Generate root cause hypotheses
- Design verification experiments
- Report findings to ProductionManager

**Workflows:**
- `NovelDefectInvestigationWorkflow` - Systematic investigation
- `RootCauseAnalysisWorkflow` - 8D problem solving
- `HistoricalSimilarityWorkflow` - Pattern matching

**Key Behavior:**
- Does NOT interact with user directly
- Reports to ProductionManager
- Broadcasts investigation progress (visible thinking)

#### 3. ProcessEngineerAgent (Action Executor)

**Role:** Execute approved corrective actions

**Responsibilities:**
- Receive corrective action plan from ProductionManager
- Execute process changes (pressure reduction, recipe change, etc.)
- Run verification wafers
- Collect verification results
- Report results to ProductionManager

**Workflows:**
- `CorrectiveActionWorkflow` - Execute process changes
- `MonitorWaferWorkflow` - Run and analyze test wafers

**Key Behavior:**
- Only executes after user approval (via ProductionManager)
- Reports progress and results to ProductionManager

## Demonstrating Three Modes

### MODE 1: AUTOMATION (Rule-Based System)

```python
class AutomatedDefectSystem:
    """Traditional rule-based defect response."""

    def handle_defect(self, defect_alert):
        # Rule-based classification
        if defect_alert["type"] in KNOWN_DEFECTS:
            action = DEFECT_ACTION_LOOKUP[defect_alert["type"]]
            return f"Action: {action}"
        else:
            # Can't handle unknown defects
            return "UNKNOWN_DEFECT - Escalate to engineer"

# Limitations:
# ❌ No investigation for unknown defects
# ❌ Just escalates to human
# ❌ No intelligent reasoning
# ❌ Requires manual rules for every defect type
# ❌ No multi-agent coordination (single system)
```

**User Experience:**
```
User: "Unknown defects on lot ABC123"
System: "UNKNOWN_DEFECT_TYPE. Escalated to engineering queue. Ticket #4582."
❌ No investigation, just waits for human
```

### MODE 2: PROBABILISTIC AUTONOMY (Pure LLM)

```python
# Single LLM agent decides everything

class ProbabilisticDefectManager(STARAgent):
    """LLM decides what to do - no workflows, no specialist delegation."""

    def __init__(self):
        super().__init__(agent_type="probabilistic-defect-manager")
        # Resources available, but NO workflows
        # NO specialist agents
        # LLM decides investigation depth, actions, etc.

# Limitations:
# ❌ Might skip systematic investigation
# ❌ Might not delegate to specialists (tries to do everything)
# ❌ Might skip critical steps (correlation, verification)
# ❌ Inconsistent behavior (run-to-run variance)
# ❌ No guaranteed human-in-the-loop at right points
```

**User Experience (Run 1):**
```
User: "Unknown defects on lot ABC123"
Agent: "Based on circular pattern, this looks like particle contamination.
        I recommend cleaning chamber 3."

❌ Jumped to conclusion without investigation
❌ Didn't delegate to specialist
❌ Didn't verify hypothesis
❌ Might be wrong
```

**User Experience (Run 2):**
```
User: "Unknown defects on lot ABC123"
Agent: "Let me investigate this defect pattern...
        [Does investigation]
        This appears to be resist spray issue.
        Recommend pressure reduction."

⚠️ Better, but INCONSISTENT
⚠️ Didn't do this in Run 1
⚠️ No verification plan
⚠️ Can't rely on thorough investigation
```

### MODE 3: DETERMINISTIC AUTONOMY (Workflows + Multi-Agent)

```python
# Coordinator + Specialists with workflows

class ProductionManagerAgent(STARAgent):
    """Coordinator with user-facing workflows."""

    def __init__(self):
        super().__init__(agent_type="production-manager")

        # Compose specialist agents
        self.with_agents(
            DefectSpecialistAgent(agent_id="defect-specialist-001"),
            ProcessEngineerAgent(agent_id="process-engineer-001"),
        )

        # Compose coordinator workflows
        self.with_workflows(
            DefectResponseWorkflow(workflow_id="defect-response"),
            RiskAssessmentWorkflow(workflow_id="risk-assessment"),
            VerificationWorkflow(workflow_id="verification"),
        )

class DefectSpecialistAgent(STARAgent):
    """Specialist with investigation workflows."""

    def __init__(self):
        super().__init__(agent_type="defect-specialist")

        # Compose specialist workflows
        self.with_workflows(
            NovelDefectInvestigationWorkflow(workflow_id="investigation"),
            RootCauseAnalysisWorkflow(workflow_id="root-cause"),
        )

# Benefits:
# ✅ Systematic investigation (DefectSpecialist workflows)
# ✅ Coordinator orchestrates (ProductionManager workflows)
# ✅ Human-in-the-loop at strategic points (approve/reject)
# ✅ Consistent behavior (workflows enforce structure)
# ✅ Intelligent reasoning (LLM at each step)
# ✅ Mirrors real fab organization
```

**User Experience (EVERY TIME):**
```
User: "Unknown defects on lot ABC123"

ProductionManager: "I'm engaging the defect specialist for systematic investigation.
                    This will take approximately 30 minutes."

[DefectSpecialist runs NovelDefectInvestigationWorkflow]
🔧 WORKFLOW [investigation] Analyzing query to select research strategy...
🔍 WORKFLOW [investigation] Collecting high-resolution defect images...
📊 WORKFLOW [investigation] Characterizing pattern features...
🔗 WORKFLOW [investigation] Correlating with recent process changes...
   Found: Resist spray pressure increased 10 PSI (2 days ago)
🔍 WORKFLOW [investigation] Searching historical similar patterns...
   Found: Similar case 2023 - root cause: nozzle clogging
✅ WORKFLOW [investigation] Investigation complete.

ProductionManager: "Investigation findings:

ROOT CAUSE (MEDIUM confidence):
Resist spray nozzle partially clogged, exacerbated by recent
pressure increase.

EVIDENCE:
• Pattern matches nozzle splatter signature
• Timing correlates with pressure increase (2 days ago)
• Historical case 2023: same pattern, nozzle clogging

RISK ASSESSMENT:
• Customer impact: MEDIUM (15% yield loss)
• Production impact: Can continue with monitoring
• Recommendation: Do NOT hold production

RECOMMENDED ACTION:
1. Reduce spray pressure to baseline (immediate)
2. Run 5 monitor wafers to verify improvement
3. If defects persist: Replace nozzle
4. Update nozzle PM schedule (preventive)

ESTIMATED IMPACT:
• Downtime: 2 hours
• Cost: 5 monitor wafers (~$500)
• Risk if wrong: Low (reversible action)

❓ This requires process intervention. Should I proceed with corrective action?"

User: "Yes, proceed"

ProductionManager: "Delegating to process engineer for execution..."

[ProcessEngineer runs CorrectiveActionWorkflow]
⚙️ WORKFLOW [corrective-action] Reducing spray pressure to baseline...
✅ WORKFLOW [corrective-action] Pressure reduced to 50 PSI
⚙️ WORKFLOW [corrective-action] Running 5 monitor wafers...
   Wafer 1: ✓ No defects
   Wafer 2: ✓ No defects
   Wafer 3: ✓ No defects
   Wafer 4: ✓ No defects
   Wafer 5: ✓ No defects

ProcessEngineer: "Verification complete: Defects cleared with pressure reduction."

ProductionManager: "✅ RESOLUTION VERIFIED

Corrective action successful:
• All 5 monitor wafers passed
• Defect pattern eliminated
• Root cause confirmed: Spray pressure

NEXT STEPS:
• Update process spec: Max pressure = 50 PSI
• Add pressure to SPC monitoring
• Update nozzle PM schedule

Generating compliance documentation (ISO/IATF 8D Report)...
Documentation complete: 8D-2025-001

Case closed. Lot ABC123 released to production."

✅ SYSTEMATIC investigation
✅ COORDINATOR orchestrates specialists
✅ HUMAN approval at strategic points
✅ VERIFIABLE action and results
✅ COMPLIANT documentation
✅ CONSISTENT quality (every time)
```

## Workflows

### Coordinator Level (ProductionManagerAgent)

#### 1. DefectResponseWorkflow

**Purpose:** Orchestrate overall defect response

**Steps:**
1. **Severity Assessment** (LLM) - Assess defect severity and urgency
2. **Delegation Decision** - If HIGH severity → delegate to DefectSpecialist
3. **Monitor Investigation** - Track specialist progress
4. **Risk Assessment** - Assess customer and production risk
5. **User Presentation** - Present findings and options to user
6. **Approval Gate** - Get user approval for action
7. **Delegate Action** - Delegate to ProcessEngineer if approved
8. **Verification** - Verify effectiveness
9. **Documentation** - Generate compliance documentation

**Human-in-the-Loop Gates:**
- Approve/reject holding production
- Approve/reject corrective action
- Approve/reject material release

#### 2. RiskAssessmentWorkflow

**Purpose:** Assess production and customer risk

**Steps:**
1. **Defect Impact** (LLM) - How does this affect chip functionality?
2. **Yield Impact** - Calculate % yield loss
3. **Customer Risk** (LLM) - Risk of shipping defective product
4. **Production Risk** (LLM) - Risk of continuing production
5. **Financial Impact** - Calculate revenue at risk
6. **Recommendation** (LLM) - Hold production or continue with monitoring?

#### 3. VerificationWorkflow

**Purpose:** Verify corrective action effectiveness

**Steps:**
1. **Run Monitor Wafers** - Execute verification test
2. **Analyze Results** - Check for defects
3. **Statistical Validation** - Verify statistically significant improvement
4. **Effectiveness Determination** - Pass/Fail decision
5. **Documentation** - Update 8D report

### Specialist Level (DefectSpecialistAgent)

#### 4. NovelDefectInvestigationWorkflow

**Purpose:** Systematic investigation of unknown defects

**Steps:**
1. **Image Collection** - High-res SEM images
2. **Pattern Characterization** (LLM) - Analyze morphology, distribution
3. **Process Correlation** - Check recent process changes
4. **Material Correlation** - Check material lot changes
5. **Historical Similarity** (LLM) - Search for similar past cases
6. **Hypothesis Generation** (LLM) - Generate root cause hypotheses
7. **Verification Plan** (LLM) - Design verification experiment
8. **Report** - Structured findings to ProductionManager

#### 5. RootCauseAnalysisWorkflow

**Purpose:** 8D problem solving methodology

**Steps:**
1. **Problem Description** - Clear problem statement
2. **Containment** - Immediate containment actions
3. **Root Cause** - 5-Why, fishbone analysis
4. **Corrective Action** - Permanent fix
5. **Verification** - Verify effectiveness
6. **Preventive Action** - Prevent recurrence
7. **Documentation** - 8D report for compliance

### Action Level (ProcessEngineerAgent)

#### 6. CorrectiveActionWorkflow

**Purpose:** Execute approved process changes

**Steps:**
1. **Pre-Check** - Verify equipment ready
2. **Execute Change** - Implement process modification
3. **Run Monitor Wafers** - Execute verification test
4. **Collect Results** - Gather defect inspection data
5. **Report** - Report results to ProductionManager

## Success Criteria

The demo should clearly show:

1. **Automation:**
   - ❌ No investigation for unknown defects
   - ❌ Just escalates to human queue
   - ❌ No multi-agent coordination
   - ❌ User waits for human engineer

2. **Probabilistic:**
   - ⚠️ Sometimes investigates thoroughly
   - ⚠️ Sometimes jumps to conclusions
   - ❌ Inconsistent delegation to specialists
   - ❌ No guaranteed human approval gates
   - ❌ Not production-ready

3. **Deterministic:**
   - ✅ Always systematic investigation (workflows)
   - ✅ Always delegates to appropriate specialist
   - ✅ Always gets user approval at strategic points
   - ✅ Consistent quality across runs
   - ✅ Mirrors real fab organization
   - ✅ **Production-ready**

## Value Proposition

**"In semiconductor manufacturing, multi-agent deterministic autonomy mirrors your organization structure: a coordinator manages specialists, systematic workflows ensure quality, and humans approve strategic decisions. You can't rely on probabilistic agents that might skip investigation or forget to get approval."**

**Business Impact:**
- Faster response to defects (systematic investigation, no waiting for human)
- Consistent quality (every defect gets thorough investigation)
- Right level of human involvement (strategic decisions, not tactical details)
- Compliance ready (documented workflows, audit trail)
- Scalable (add more specialists as needed)
