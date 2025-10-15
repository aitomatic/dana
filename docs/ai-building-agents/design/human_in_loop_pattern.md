# Human-in-the-Loop Phased Orchestration Pattern

## Overview

The **Human-in-the-Loop Phased Orchestration** pattern combines deterministic multi-phase workflows with interactive approval gates, enabling collaborative execution between humans and autonomous agents. This pattern is essential for long-running, high-stakes operations where human oversight and iterative refinement are critical.

## Pattern Classification

This is a **hybrid pattern** that extends:
- **Pattern 1: Single Specialist Agent** (with agent autonomy in each phase)
- **Pattern 4: Workflow-Heavy Application** (with strong workflow backbone)
- **Workflow Pattern 3: Phased Orchestration** (parallel + sequential phases)

**New Elements**:
- Interactive approval gates between phases
- State management for reversibility
- Rich command sets for human control
- Agent responsiveness to human commands within gates

---

## Intent

Enable human oversight and control over multi-phase autonomous agent work while maintaining agent flexibility within each phase.

---

## Problem

**Scenario**: You need to execute a long-running, complex task with multiple phases where:
- The task may take hours to complete
- Early phases inform decisions about later phases
- Mistakes in early phases are expensive to fix later
- Quality validation is critical
- Parameters may need adjustment based on results
- Humans want to review progress without micromanaging
- Agent autonomy is valuable within each phase

**Without this pattern**:
- All-or-nothing execution (can't stop midway)
- No opportunity to validate before proceeding
- Wasted time/money on bad early results
- No iterative refinement
- Either too much control (micromanaging) or too little (blind execution)

**With this pattern**:
- Review and approve after each phase
- Abort early if results are unsatisfactory
- Adjust parameters based on actual results
- Agent works autonomously within approved phases
- Human maintains oversight without constant intervention

---

## Structure

```
┌─────────────────────────────────────────────────────────┐
│                 Overall Workflow                        │
│                                                         │
│  Phase 1: Data Gathering                               │
│    - Agent autonomous work (STAR loop)                 │
│    - Resources + Workflows execute                     │
│    - Results stored in session                         │
│                      ↓                                  │
│  📍 GATE 1: Review & Approve Discovery                 │
│    - Human inspects results                            │
│    - Commands: proceed, filter, limit, redo, abort     │
│    - Agent responds to questions/commands              │
│    - Session state updated based on commands           │
│                      ↓                                  │
│  Phase 2: Processing (Batched)                         │
│    - Agent enriches/processes items                    │
│    - Progress tracking                                 │
│    - Quality metrics computed                          │
│                      ↓                                  │
│  📍 GATE 2: Progress Checkpoint (every N batches)      │
│    - Review quality and progress                       │
│    - Commands: continue, pause, show stats, abort      │
│    - Agent provides analysis                           │
│    - Can adjust remaining batches                      │
│                      ↓                                  │
│  Phase 3: Validation & Synthesis                       │
│    - Final processing                                  │
│    - Quality validation                                │
│    - Results preparation                               │
│                      ↓                                  │
│  📍 GATE 3: Final Approval                             │
│    - Review complete results                           │
│    - Commands: approve, export, re-process, redo       │
│    - Agent ready for delivery                          │
│                      ↓                                  │
│  Complete: Export & Deliver                            │
└─────────────────────────────────────────────────────────┘
```

---

## Components

### 1. Session State Manager

Tracks progress and enables reversibility:

```python
@dataclass
class SessionState:
    """
    Maintains state across phases for reversibility and checkpointing.
    """
    # Current position
    current_phase: Literal["discovery", "processing", "validation", "complete"]

    # Configuration (adjustable at gates)
    parameters: dict

    # Results at each phase (for reversibility)
    phase1_results: dict | None = None
    phase2_results: list[dict] = field(default_factory=list)
    phase3_results: dict | None = None

    # Progress tracking
    current_batch: int = 0
    total_batches: int = 0

    # Quality metrics
    quality_stats: dict | None = None

    def can_proceed(self) -> bool:
        """Check if current phase has results to proceed."""
        pass

    def reset_from_phase(self, phase: str):
        """Reset all data after a phase (for redo)."""
        pass

    def get_summary(self) -> dict:
        """Get current session summary for gates."""
        pass
```

### 2. Interactive Gate Handler

Processes human commands at each gate:

```python
class GateHandler:
    """
    Handles interactive commands at approval gates.

    Each gate has a specific command set appropriate to the phase.
    """

    def __init__(self, agent: STARAgent, session: SessionState):
        self.agent = agent
        self.session = session

    def present_gate(self, gate_name: str, data: dict) -> dict:
        """
        Present gate to human with summary and available commands.

        Args:
            gate_name: Name of gate (e.g., "discovery", "progress", "final")
            data: Data to present (companies, stats, etc.)

        Returns:
            Human decision and any adjustments
        """
        print(f"\n📍 GATE: {gate_name.upper()}")
        self._show_summary(data)
        self._show_commands(gate_name)

        while True:
            command = input("\n👤 Command: ").strip().lower()
            result = self._process_command(gate_name, command, data)

            if result.get("action") in ["proceed", "abort", "complete"]:
                return result

    def _show_summary(self, data: dict):
        """Display data summary for this gate."""
        pass

    def _show_commands(self, gate_name: str):
        """Show available commands for this gate."""
        pass

    def _process_command(self, gate_name: str, command: str, data: dict) -> dict:
        """
        Process user command, possibly using agent for complex queries.

        Simple commands (proceed, abort) handled directly.
        Complex commands (show stats, filter) delegated to agent.
        """
        pass
```

### 3. Phased Orchestration Workflow

Main workflow with gate checkpoints:

```python
class HumanInLoopWorkflow(BaseWorkflow):
    """
    Multi-phase workflow with interactive approval gates.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Phase workflows
        self.phase1_workflow = Phase1Workflow()
        self.phase2_workflow = Phase2Workflow()
        self.phase3_workflow = Phase3Workflow()

        # Session and gate handler
        self.session = SessionState()
        self.gate_handler = GateHandler(agent=None, session=self.session)

    def _do_execute(self, **kwargs):
        """
        Execute workflow with gates.

        Unlike normal workflows, this can pause for human input.
        """
        # Phase 1: Discovery/Gathering
        print("\n🔄 Phase 1: Discovery...")
        phase1_result = self.phase1_workflow.execute(**kwargs)
        self.session.phase1_results = phase1_result["result"]

        # Gate 1: Approve discovery
        gate1_decision = self.gate_handler.present_gate(
            "discovery",
            self.session.phase1_results
        )

        if gate1_decision["action"] == "abort":
            return {"success": False, "aborted_at": "gate1"}

        if gate1_decision["action"] == "redo":
            # Recursively restart with adjusted parameters
            return self._do_execute(**gate1_decision.get("adjusted_params", kwargs))

        # Apply any filters/limits from gate
        filtered_items = self._apply_gate_adjustments(
            self.session.phase1_results,
            gate1_decision.get("adjustments", {})
        )

        # Phase 2: Processing (with progress gates)
        print("\n🔄 Phase 2: Processing...")
        batches = self._create_batches(filtered_items, batch_size=15)
        self.session.total_batches = len(batches)

        for i, batch in enumerate(batches):
            # Process batch
            batch_result = self.phase2_workflow.execute(items=batch)
            self.session.phase2_results.extend(batch_result["result"]["items"])
            self.session.current_batch = i + 1

            # Gate 2: Progress checkpoint (every 5 batches)
            if (i + 1) % 5 == 0 or (i + 1) == len(batches):
                gate2_decision = self.gate_handler.present_gate(
                    "progress",
                    {
                        "current_batch": i + 1,
                        "total_batches": len(batches),
                        "results_so_far": self.session.phase2_results,
                        "quality_stats": self._compute_quality_stats()
                    }
                )

                if gate2_decision["action"] == "abort":
                    return {"success": False, "aborted_at": "gate2"}

                if gate2_decision["action"] == "pause":
                    # Export partial results and stop
                    return {
                        "success": True,
                        "paused": True,
                        "results": self.session.phase2_results
                    }

        # Phase 3: Validation
        print("\n🔄 Phase 3: Validation...")
        phase3_result = self.phase3_workflow.execute(
            items=self.session.phase2_results
        )
        self.session.phase3_results = phase3_result["result"]

        # Gate 3: Final approval
        gate3_decision = self.gate_handler.present_gate(
            "final",
            self.session.phase3_results
        )

        if gate3_decision["action"] == "abort":
            return {"success": False, "aborted_at": "gate3"}

        if gate3_decision["action"] == "redo_processing":
            # Re-run phase 2 with same discovery but different parameters
            self.session.reset_from_phase("processing")
            # ... restart from phase 2

        # Complete
        return {
            "success": True,
            "results": self.session.phase3_results,
            "session_summary": self.session.get_summary()
        }

    def _apply_gate_adjustments(self, data: dict, adjustments: dict) -> list:
        """Apply filters, limits, etc. from gate decisions."""
        pass

    def _create_batches(self, items: list, batch_size: int) -> list[list]:
        """Split items into batches."""
        pass

    def _compute_quality_stats(self) -> dict:
        """Compute quality metrics for current results."""
        pass
```

### 4. Agent with Interactive Methods

Agent that can respond to gate commands:

```python
class InteractiveAgent(STARAgent):
    """
    Agent that can work autonomously AND respond to interactive commands.
    """

    def __init__(self, **kwargs):
        super().__init__(
            agent_type="interactive-agent",
            agent_id="interactive-agent",
            **kwargs
        )

        self.session = SessionState()

        self.with_workflows(
            HumanInLoopWorkflow(),
        ).with_resources(
            # ... resources
        )

    def execute_with_gates(self, **kwargs) -> dict:
        """
        Execute the main workflow with interactive gates.

        This is the entry point for human-in-the-loop execution.
        """
        workflow = HumanInLoopWorkflow()
        workflow.gate_handler.agent = self  # Give gate handler access to agent

        return workflow.execute(**kwargs)

    def show_statistics(self, data: dict) -> str:
        """
        Agent analyzes data and returns statistics.
        Called from gate commands like "show stats".
        """
        # Use agent's reasoning to analyze and present stats
        result = self.query(
            caller_message=f"Analyze this data and provide detailed statistics: {data}"
        )
        return result.get("content", "No analysis available")

    def filter_items(self, items: list, filter_criteria: str) -> list:
        """
        Agent filters items based on natural language criteria.
        Called from gate commands like "filter trading companies".
        """
        result = self.query(
            caller_message=f"Filter these items based on: {filter_criteria}. Items: {items}"
        )
        # Parse result and return filtered items
        pass
```

---

## Real Example: Vietnam Coffee Research

See `dana_agent/docs/ai-building-agents/use-cases/vietnam_coffee/` for full implementation.

### Gate 1: Discovery Review

```python
📍 GATE 1: DISCOVERY COMPLETE
✅ Found 247 companies across 3 provinces

Sample Companies:
  1. Công ty TNHH Milano (Đắk Lắk) - Roaster
  2. HTX Ea Tân (Đắk Lắk) - Cooperative
  3. Công ty Intimex (Gia Lai) - Exporter
  ... (showing 10 of 247)

Commands:
  • proceed              - Start enrichment for all 247 companies
  • show more           - View companies 11-30
  • filter <keyword>    - Remove companies (e.g., "filter trading")
  • limit <N>           - Only enrich first N companies
  • add province <name> - Discover in additional province
  • redo                - Restart discovery with different parameters
  • abort               - Cancel research

👤 Command: show more
📋 Companies 11-20: [displays companies 11-20]

👤 Command: filter trading
✅ Removed 12 trading companies (235 remaining)

👤 Command: limit 100
✅ Will enrich first 100 companies only

👤 Command: proceed
🔄 Starting enrichment phase...
```

### Gate 2: Progress Checkpoint

```python
📍 GATE 2: ENRICHMENT PROGRESS
✅ Completed: 50 / 100 companies (5 batches)
⏱️  Time elapsed: 45 minutes
⏱️  Estimated remaining: 40 minutes

Quality Distribution:
  High confidence (>0.8):   38 companies (76%)
  Medium confidence (0.5-0.8): 10 companies (20%)
  Low confidence (<0.5):     2 companies (4%)

Latest Batch (Batch 5):
  1. Công ty TNHH Phương Nam - Revenue: $2.1M (verified)
  2. HTX Chu Prông - Revenue: ~$800K (estimated)
  ...

Commands:
  • continue            - Continue enriching remaining 50 companies
  • show batch          - View full details of latest batch
  • show stats          - Detailed quality breakdown by field
  • show low quality    - View the 2 low-confidence companies
  • pause               - Stop here and export 50 companies
  • abort               - Cancel remaining enrichment

👤 Command: show low quality
📋 Low-confidence companies:
  1. Công ty ABC - Missing: revenue, certifications (confidence: 0.42)
  2. HTX XYZ - Missing: contact info (confidence: 0.48)

👤 Command: continue
🔄 Resuming enrichment...
```

### Gate 3: Final Approval

```python
📍 GATE 3: FINAL VALIDATION
✅ Total: 100 companies enriched
✅ MECE Compliant: No duplicates detected
✅ Average confidence: 0.81

Quality Summary:
  High confidence:   82 companies
  Medium confidence: 15 companies
  Low confidence:     3 companies

Coverage:
  Provinces: Đắk Lắk (65), Gia Lai (28), Lam Đồng (7)
  Entity types: Cooperatives (42), Private (35), Exporters (23)
  Certifications: 47 certified, 53 uncertified

Commands:
  • approve                - Export results and complete
  • export csv             - Preview CSV format before approving
  • show low quality       - View 3 low-confidence companies
  • re-enrich low quality  - Re-run enrichment for 3 companies
  • redo enrichment        - Restart enrichment phase
  • abort                  - Discard all results

👤 Command: re-enrich low quality
🔄 Re-enriching 3 companies with additional sources...
✅ Re-enrichment complete. New average confidence: 0.85

👤 Command: approve
✅ Results approved! Exporting to vietnam_coffee_research.json
📊 Final report generated: vietnam_coffee_report.pdf
```

---

## Key Features

### 1. Reversibility

Each gate can go back to previous phases:
- **Gate 1**: Redo discovery with different parameters
- **Gate 2**: Pause and adjust processing strategy
- **Gate 3**: Re-run validation or entire enrichment

### 2. Rich Command Sets

Different commands appropriate to each gate:

**Discovery Gate**:
- Information: `show more`, `show sample`
- Filtering: `filter <criteria>`, `limit <N>`
- Expansion: `add province`, `add category`
- Control: `proceed`, `redo`, `abort`

**Progress Gate**:
- Information: `show batch`, `show stats`, `show low quality`
- Control: `continue`, `pause`, `abort`

**Final Gate**:
- Information: `export csv`, `show summary`, `show low quality`
- Refinement: `re-enrich`, `redo enrichment`
- Control: `approve`, `abort`

### 3. Agent-Assisted Analysis

Complex commands use agent reasoning:

```python
👤 Command: show stats

🤖 Agent analyzing results...

📊 Detailed Quality Statistics:

Revenue Field:
  • Verified from government filings: 45 companies
  • Estimated from public data: 38 companies
  • Missing: 17 companies
  • Confidence: High (verified) vs Medium (estimated)

Certifications:
  • Verified certifications: 47 companies
  • Self-reported: 12 companies
  • None found: 41 companies

Export Status:
  • Verified exporters (customs data): 23 companies
  • Claimed exporters (website): 15 companies
  • Domestic only: 62 companies

Recommendations:
  - Consider re-enriching 17 companies missing revenue
  - High confidence overall (81%) - good quality dataset
```

### 4. Session Persistence

Session can be saved and resumed:

```python
# Save session at gate
session_data = {
    "session": self.session.to_dict(),
    "timestamp": datetime.now().isoformat(),
    "gate": "gate2",
}

with open("research_session.json", "w") as f:
    json.dump(session_data, f)

# Resume later
with open("research_session.json", "r") as f:
    saved = json.load(f)

session = SessionState.from_dict(saved["session"])
# Continue from saved gate...
```

---

## When to Use This Pattern

### Ideal Scenarios

✅ **Long-running operations** (> 1 hour)
- Example: Research 1,000 companies (8+ hours)
- Benefit: Can abort after 30 minutes if early results are bad

✅ **High-stakes decisions**
- Example: Medical diagnosis, legal research, financial analysis
- Benefit: Human approval at critical points

✅ **Expensive operations**
- Example: API calls costing $0.01 each × 10,000 items = $100
- Benefit: Validate sample before spending full budget

✅ **Quality-sensitive work**
- Example: Training data generation, content moderation
- Benefit: Spot-check quality during processing

✅ **Iterative refinement needed**
- Example: Tuning search parameters based on actual results
- Benefit: Adjust strategy midway based on real data

✅ **Uncertain requirements**
- Example: Exploratory research where scope emerges
- Benefit: Expand or narrow based on findings

### Not Ideal For

❌ **Real-time operations** - Gates add latency
❌ **Fully automated pipelines** - No human available for gates
❌ **Simple, fast tasks** - Overhead not justified
❌ **Well-defined, tested processes** - Automation is reliable

---

## Benefits

1. **Risk Mitigation**: Abort early if headed wrong direction
2. **Cost Control**: Don't waste resources on bad intermediate results
3. **Quality Assurance**: Human validation at checkpoints
4. **Flexibility**: Adjust parameters based on actual results
5. **Transparency**: Human sees progress and can ask questions
6. **Learning**: Humans learn about data/domain through gates
7. **Trust Building**: Incremental validation builds confidence in agent

---

## Trade-offs

### Advantages

- Early error detection
- Iterative refinement
- Human oversight without micromanagement
- Agent autonomy within phases
- Reversibility and experimentation

### Disadvantages

- Requires human availability
- Adds latency (minutes to hours at each gate)
- More complex implementation
- Session state management overhead
- Not suitable for fully automated pipelines

---

## Implementation Checklist

- [ ] Define phases and their boundaries
- [ ] Create SessionState dataclass
- [ ] Implement gate command handlers
- [ ] Build phased orchestration workflow
- [ ] Add agent methods for interactive commands
- [ ] Design gate UIs (CLI, Web, etc.)
- [ ] Implement reversibility (redo, reset)
- [ ] Add quality metrics computation
- [ ] Create session persistence (save/resume)
- [ ] Write tests for each gate scenario
- [ ] Document gate commands for users

---

## Variations

### Variation 1: Automated Gates with Thresholds

Gates can auto-proceed if quality exceeds threshold:

```python
if gate2_decision.get("quality_score", 0) > 0.8:
    print("✅ Quality threshold met. Auto-proceeding...")
    proceed = True
else:
    proceed = self.gate_handler.present_gate("progress", data)
```

### Variation 2: Asynchronous Gates

For web applications, gates can be asynchronous:

```python
# Backend saves state and sends notification
await notify_user_gate_ready(gate_id="gate2", data=summary)

# User reviews at their convenience (hours later)
# When approved, backend resumes workflow
```

### Variation 3: Multi-User Gates

Different stakeholders approve different gates:

```python
# Technical lead approves Gate 1 (discovery)
gate1_approver = "tech_lead@company.com"

# Domain expert approves Gate 2 (quality)
gate2_approver = "domain_expert@company.com"

# Executive approves Gate 3 (final delivery)
gate3_approver = "executive@company.com"
```

### Variation 4: Conditional Gates

Gates appear only when needed:

```python
# Only show progress gate if low quality detected
if quality_score < 0.7:
    gate2_decision = present_gate("quality_check", data)
```

---

## Related Patterns

- **Workflow Pattern 3: Phased Orchestration** - Foundation for phases
- **Pattern 1: Single Specialist Agent** - Agent providing autonomy within phases
- **Pattern 4: Workflow-Heavy Application** - Strong workflow backbone

---

## Examples in Codebase

- **Full Implementation**: `dana_agent/docs/ai-building-agents/use-cases/vietnam_coffee/`
  - Session: `agents/research_session.py`
  - Interactive example: `scripts/run_interactive_gates.py`
  - Gate commands: See README.md Gate 1/2/3 sections

---

## Further Reading

- [Workflow Design Patterns](./workflow_design_patterns.md) - Phased Orchestration
- [Agent Design Patterns](./agent_design_patterns.md) - Single Specialist, Workflow-Heavy
- [Vietnam Coffee Use Case](../use-cases/vietnam_coffee/README.md) - Full example

---

**Last Updated**: 2025-10-14
**Pattern Status**: Production-Validated (Vietnam Coffee use-case)
**Maintainers**: Dana Framework Team
