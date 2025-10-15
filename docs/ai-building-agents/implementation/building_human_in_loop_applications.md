# Building Human-in-the-Loop Applications

## Overview

This guide walks through building applications using the **Human-in-the-Loop Phased Orchestration** pattern. You'll learn how to create multi-phase workflows with interactive approval gates that combine agent autonomy with human oversight.

**Prerequisites**:
- Read [Human-in-the-Loop Pattern](../design/human_in_loop_pattern.md)
- Understand [Workflow Design Patterns](../design/workflow_design_patterns.md)
- Familiar with [Agent Design Patterns](../design/agent_design_patterns.md)

---

## Architecture Overview

A Human-in-the-Loop application has 4 main components:

```
┌─────────────────────────────────────────────────────────────┐
│                    Your Application                         │
│                                                             │
│  1. Session State Manager                                  │
│     - Tracks progress across phases                        │
│     - Enables reversibility (redo, reset)                  │
│     - Stores intermediate results                          │
│                                                             │
│  2. Phase Workflows                                         │
│     - Phase 1: Discovery/Gathering                         │
│     - Phase 2: Processing/Enrichment                       │
│     - Phase 3: Validation/Synthesis                        │
│                                                             │
│  3. Gate Handler                                            │
│     - Presents gates to human                              │
│     - Processes commands                                    │
│     - Delegates complex queries to agent                   │
│                                                             │
│  4. Agent (Optional)                                        │
│     - Autonomous work within phases                        │
│     - Responds to gate commands                            │
│     - Provides analysis and insights                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Step-by-Step Building Guide

### Step 1: Define Your Phases

First, identify the natural phases of your task.

**Example: Research Application**

```python
# phases.md

## Phase 1: Discovery
- **Input**: Research topic, scope, constraints
- **Process**: Search multiple sources, gather candidates
- **Output**: List of candidate items (companies, papers, people, etc.)
- **Gate 1**: Human reviews candidates, filters, adjusts scope

## Phase 2: Enrichment
- **Input**: Filtered candidates from Gate 1
- **Process**: Gather detailed information for each candidate
- **Output**: Enriched dataset with all fields populated
- **Gate 2**: Human reviews quality, pauses if needed

## Phase 3: Validation
- **Input**: Enriched dataset
- **Process**: Validate completeness, remove duplicates, check quality
- **Output**: Final validated dataset
- **Gate 3**: Human approves or requests re-processing
```

**Questions to answer**:
- What are the natural breakpoints in your process?
- Where do you need human review/approval?
- What can be reversed or redone?
- What adjustments might humans make at each gate?

---

### Step 2: Create Session State

Build a dataclass to track progress and enable reversibility.

**File**: `your_app/session.py`

```python
"""
Session state for human-in-the-loop execution.
"""

from dataclasses import dataclass, field
from typing import Literal
from datetime import datetime


@dataclass
class ResearchSession:
    """
    Tracks research session state across phases.

    Enables:
    - Progress tracking
    - Reversibility (redo phases)
    - Session persistence (save/resume)
    - Quality monitoring
    """

    # Current state
    current_phase: Literal["discovery", "enrichment", "validation", "complete"] = "discovery"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Configuration (can be adjusted at gates)
    topic: str = ""
    scope: dict = field(default_factory=dict)
    batch_size: int = 15
    max_items: int | None = None

    # Phase results (for reversibility)
    discovered_items: list[dict] | None = None
    enriched_items: list[dict] = field(default_factory=list)
    validated_items: list[dict] | None = None

    # Progress tracking
    current_batch: int = 0
    total_batches: int = 0
    enriched_batches: list[dict] = field(default_factory=list)

    # Quality metrics
    quality_stats: dict | None = None
    validation_report: dict | None = None

    # Metadata
    gates_passed: list[str] = field(default_factory=list)
    time_per_phase: dict = field(default_factory=dict)

    def can_proceed(self) -> bool:
        """Check if current phase has results to proceed."""
        if self.current_phase == "discovery":
            return self.discovered_items is not None and len(self.discovered_items) > 0
        elif self.current_phase == "enrichment":
            return len(self.enriched_items) > 0
        elif self.current_phase == "validation":
            return self.validated_items is not None
        return False

    def reset_from_phase(self, phase: str):
        """
        Reset all data after a specific phase (for redo).

        Args:
            phase: Phase to reset from
        """
        if phase == "discovery":
            self.discovered_items = None
            self.enriched_items = []
            self.enriched_batches = []
            self.validated_items = None
            self.current_batch = 0
            self.total_batches = 0
            self.current_phase = "discovery"
        elif phase == "enrichment":
            self.enriched_items = []
            self.enriched_batches = []
            self.validated_items = None
            self.current_batch = 0
            self.total_batches = 0
            self.current_phase = "enrichment"
        elif phase == "validation":
            self.validated_items = None
            self.current_phase = "validation"

    def get_summary(self) -> dict:
        """Get current session summary for gates."""
        return {
            "current_phase": self.current_phase,
            "topic": self.topic,
            "discovered_count": len(self.discovered_items) if self.discovered_items else 0,
            "enriched_count": len(self.enriched_items),
            "validated_count": len(self.validated_items) if self.validated_items else 0,
            "batches_completed": len(self.enriched_batches),
            "gates_passed": self.gates_passed,
        }

    def to_dict(self) -> dict:
        """Serialize session for persistence."""
        from dataclasses import asdict
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "ResearchSession":
        """Deserialize session from dict."""
        return cls(**data)

    def save(self, filepath: str):
        """Save session to file."""
        import json
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, filepath: str) -> "ResearchSession":
        """Load session from file."""
        import json
        with open(filepath, "r") as f:
            return cls.from_dict(json.load(f))
```

---

### Step 3: Build Phase Workflows

Create workflows for each phase.

**File**: `your_app/workflows/discovery.py`

```python
"""
Discovery workflow - Phase 1.
"""

from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input, validate_output
from dana.common.protocols import DictParams


class DiscoveryWorkflow(BaseWorkflow):
    """
    Phase 1: Discover candidate items.

    USE FOR:
    - Initial search and candidate gathering
    - Multiple source aggregation
    - Deduplication of candidates

    EXAMPLES:
    - Discover companies in a region
    - Find research papers on a topic
    - Identify experts in a field
    """

    def __init__(self, **kwargs):
        super().__init__(workflow_id="discovery", **kwargs)

        # Initialize resources
        from dana.lib.resources.web_research import SearchResource
        self.search_resource = SearchResource()

    @validate_input(
        topic={"required": True, "type": str, "min_length": 1},
        scope={"type": dict, "default": {}},
        max_items={"type": int, "min_value": 1, "default": 100},
    )
    @validate_output(
        success={"required": True, "type": bool},
        items={"required": True, "type": list},
        sources={"type": list, "default": []},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute discovery phase.

        Args:
            topic: Research topic
            scope: Additional scope parameters (region, timeframe, etc.)
            max_items: Maximum items to discover

        Returns:
            Dictionary with discovered items
        """
        topic = kwargs["topic"]
        scope = kwargs.get("scope", {})
        max_items = kwargs.get("max_items", 100)

        # Step 1: Search multiple sources
        all_items = []
        sources_used = []

        # Source 1: Web search
        search_results = self.search_resource.search_web(
            query=self._build_search_query(topic, scope),
            max_results=max_items * 2  # Search more, then filter
        )

        if search_results.get("success"):
            items = self._extract_candidates(search_results["results"])
            all_items.extend(items)
            sources_used.append("web_search")

        # Source 2: Your domain-specific source
        # domain_results = self.domain_source.search(...)
        # all_items.extend(...)

        # Step 2: Deduplicate
        unique_items = self._deduplicate(all_items)

        # Step 3: Limit to max_items
        final_items = unique_items[:max_items]

        return {
            "success": True,
            "items": final_items,
            "sources": sources_used,
            "total_found": len(all_items),
            "unique_count": len(unique_items),
            "returned_count": len(final_items),
        }

    def _build_search_query(self, topic: str, scope: dict) -> str:
        """Build search query from topic and scope."""
        query = topic
        if "region" in scope:
            query += f" {scope['region']}"
        if "timeframe" in scope:
            query += f" {scope['timeframe']}"
        return query

    def _extract_candidates(self, search_results: list) -> list[dict]:
        """Extract candidate items from search results."""
        # Parse search results into structured candidates
        candidates = []
        for result in search_results:
            candidates.append({
                "name": result.get("title", ""),
                "url": result.get("url", ""),
                "snippet": result.get("snippet", ""),
                "source": "web_search",
            })
        return candidates

    def _deduplicate(self, items: list[dict]) -> list[dict]:
        """Remove duplicate items."""
        # Simple deduplication by name
        seen = set()
        unique = []
        for item in items:
            name = item.get("name", "").lower().strip()
            if name and name not in seen:
                seen.add(name)
                unique.append(item)
        return unique
```

**File**: `your_app/workflows/enrichment.py`

```python
"""
Enrichment workflow - Phase 2.
"""

import asyncio
from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input
from dana.common.protocols import DictParams


class EnrichmentWorkflow(BaseWorkflow):
    """
    Phase 2: Enrich items with detailed information.

    Processes items in batches for efficiency and progress tracking.
    """

    def __init__(self, **kwargs):
        super().__init__(workflow_id="enrichment", **kwargs)

        from dana.lib.resources.web_research import FetchResource, ExtractResource
        self.fetch = FetchResource()
        self.extract = ExtractResource()

    @validate_input(
        items={"required": True, "type": list, "min_length": 1},
        fields_to_enrich={"type": list, "default": ["all"]},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Enrich a batch of items.

        Args:
            items: List of items to enrich (1 batch)
            fields_to_enrich: Which fields to populate

        Returns:
            Enriched items with populated fields
        """
        items = kwargs["items"]
        fields = kwargs.get("fields_to_enrich", ["all"])

        enriched = []

        for item in items:
            enriched_item = self._enrich_single_item(item, fields)
            enriched.append(enriched_item)

        return {
            "success": True,
            "items": enriched,
            "count": len(enriched),
            "average_confidence": self._compute_avg_confidence(enriched),
        }

    def _enrich_single_item(self, item: dict, fields: list) -> dict:
        """
        Enrich a single item.

        Fetches data from sources and populates fields.
        """
        enriched = item.copy()

        # Fetch data from URL if available
        if "url" in item and item["url"]:
            fetch_result = self.fetch.fetch_url(url=item["url"])
            if fetch_result.get("success"):
                # Extract fields from content
                content = fetch_result.get("content_text", "")
                extracted = self._extract_fields(content, fields)
                enriched.update(extracted)

        # Compute confidence score
        enriched["confidence"] = self._compute_confidence(enriched, fields)

        return enriched

    def _extract_fields(self, content: str, fields: list) -> dict:
        """
        Extract fields from content.

        Uses LLM or extraction rules to populate fields.
        """
        # Use ExtractResource or custom extraction logic
        extracted = {}

        # Example: Extract specific fields
        for field in fields:
            if field == "description":
                extracted["description"] = content[:500]  # Simple extraction
            # Add more field extraction logic

        return extracted

    def _compute_confidence(self, item: dict, expected_fields: list) -> float:
        """Compute confidence score based on field completeness."""
        if expected_fields == ["all"]:
            expected_fields = ["name", "description", "url"]

        populated = sum(1 for f in expected_fields if item.get(f))
        return populated / len(expected_fields) if expected_fields else 0.0

    def _compute_avg_confidence(self, items: list) -> float:
        """Compute average confidence across items."""
        if not items:
            return 0.0
        total = sum(item.get("confidence", 0) for item in items)
        return total / len(items)
```

**File**: `your_app/workflows/validation.py`

```python
"""
Validation workflow - Phase 3.
"""

from dana.core.workflow.base_workflow import BaseWorkflow
from dana.core.workflow.validation import validate_input
from dana.common.protocols import DictParams


class ValidationWorkflow(BaseWorkflow):
    """
    Phase 3: Validate and finalize dataset.

    - Remove duplicates
    - Check completeness
    - Generate quality report
    """

    @validate_input(
        items={"required": True, "type": list, "min_length": 1},
    )
    def _do_execute(self, **kwargs) -> DictParams:
        """
        Validate enriched dataset.

        Args:
            items: Enriched items to validate

        Returns:
            Validated dataset with quality report
        """
        items = kwargs["items"]

        # Step 1: Remove duplicates
        unique_items = self._remove_duplicates(items)

        # Step 2: Check completeness
        completeness = self._check_completeness(unique_items)

        # Step 3: Generate quality report
        quality_report = self._generate_quality_report(unique_items)

        return {
            "success": True,
            "items": unique_items,
            "count": len(unique_items),
            "duplicates_removed": len(items) - len(unique_items),
            "completeness": completeness,
            "quality_report": quality_report,
        }

    def _remove_duplicates(self, items: list[dict]) -> list[dict]:
        """Remove duplicate items."""
        seen = set()
        unique = []
        for item in items:
            key = item.get("name", "").lower().strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(item)
        return unique

    def _check_completeness(self, items: list[dict]) -> dict:
        """Check dataset completeness."""
        required_fields = ["name", "description"]

        complete = sum(
            1 for item in items
            if all(item.get(f) for f in required_fields)
        )

        return {
            "total_items": len(items),
            "complete_items": complete,
            "incomplete_items": len(items) - complete,
            "completeness_rate": complete / len(items) if items else 0,
        }

    def _generate_quality_report(self, items: list[dict]) -> dict:
        """Generate quality report."""
        confidences = [item.get("confidence", 0) for item in items]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0

        high = sum(1 for c in confidences if c > 0.8)
        medium = sum(1 for c in confidences if 0.5 <= c <= 0.8)
        low = sum(1 for c in confidences if c < 0.5)

        return {
            "average_confidence": avg_confidence,
            "high_confidence_count": high,
            "medium_confidence_count": medium,
            "low_confidence_count": low,
            "distribution": {
                "high": high / len(items) if items else 0,
                "medium": medium / len(items) if items else 0,
                "low": low / len(items) if items else 0,
            },
        }
```

---

### Step 4: Create Gate Handler

Build the interactive gate interface.

**File**: `your_app/gates.py`

```python
"""
Interactive gate handler for human-in-the-loop workflow.
"""

from typing import Literal
from .session import ResearchSession


class GateHandler:
    """
    Handles interactive approval gates.

    Presents gates to humans and processes their commands.
    """

    def __init__(self, session: ResearchSession, agent=None):
        """
        Initialize gate handler.

        Args:
            session: Research session tracking state
            agent: Optional agent for complex command processing
        """
        self.session = session
        self.agent = agent

    def present_gate(
        self,
        gate_name: Literal["discovery", "progress", "final"],
        data: dict
    ) -> dict:
        """
        Present gate to human and await decision.

        Args:
            gate_name: Name of the gate
            data: Data to present (items, stats, etc.)

        Returns:
            Decision dictionary with action and adjustments
        """
        print("\n" + "=" * 80)
        print(f"📍 GATE: {gate_name.upper()}")
        print("=" * 80)

        self._show_summary(gate_name, data)
        self._show_commands(gate_name)

        while True:
            command = input("\n👤 Command: ").strip().lower()

            if not command:
                continue

            # Process command
            result = self._process_command(gate_name, command, data)

            # If result is a decision (proceed/abort), return it
            if result.get("action") in ["proceed", "abort", "complete", "pause"]:
                # Record gate passage
                self.session.gates_passed.append(gate_name)
                return result

            # Otherwise, command was informational, continue loop

    def _show_summary(self, gate_name: str, data: dict):
        """Display summary for this gate."""
        if gate_name == "discovery":
            items = data.get("items", [])
            print(f"\n✅ Discovered: {len(items)} items")
            print(f"\nSample items (showing first 10):")
            for i, item in enumerate(items[:10], 1):
                name = item.get("name", "Unknown")
                source = item.get("source", "Unknown")
                print(f"  {i}. {name} (source: {source})")

        elif gate_name == "progress":
            current = data.get("current_batch", 0)
            total = data.get("total_batches", 0)
            items = data.get("results_so_far", [])
            stats = data.get("quality_stats", {})

            print(f"\n✅ Progress: {current}/{total} batches")
            print(f"✅ Items enriched: {len(items)}")

            if stats:
                print(f"\n📊 Quality Distribution:")
                print(f"  High confidence (>0.8):   {stats.get('high_confidence_count', 0)}")
                print(f"  Medium confidence (0.5-0.8): {stats.get('medium_confidence_count', 0)}")
                print(f"  Low confidence (<0.5):     {stats.get('low_confidence_count', 0)}")

        elif gate_name == "final":
            items = data.get("items", [])
            report = data.get("quality_report", {})

            print(f"\n✅ Total items: {len(items)}")
            print(f"✅ Average confidence: {report.get('average_confidence', 0):.2f}")
            print(f"\n📊 Final Quality:")
            print(f"  High confidence:   {report.get('high_confidence_count', 0)}")
            print(f"  Medium confidence: {report.get('medium_confidence_count', 0)}")
            print(f"  Low confidence:    {report.get('low_confidence_count', 0)}")

    def _show_commands(self, gate_name: str):
        """Show available commands for this gate."""
        print(f"\n📋 Available Commands:")

        if gate_name == "discovery":
            print("  • proceed              - Start enrichment phase")
            print("  • show more           - View items 11-30")
            print("  • limit <N>           - Enrich only first N items")
            print("  • filter <keyword>    - Remove items matching keyword")
            print("  • redo                - Restart discovery")
            print("  • abort               - Cancel research")

        elif gate_name == "progress":
            print("  • continue            - Continue enrichment")
            print("  • show batch          - View latest batch details")
            print("  • show stats          - Detailed quality statistics")
            print("  • show low            - View low-confidence items")
            print("  • pause               - Stop and export current results")
            print("  • abort               - Cancel remaining work")

        elif gate_name == "final":
            print("  • approve             - Approve and export results")
            print("  • show low            - View low-confidence items")
            print("  • re-enrich low       - Re-process low-confidence items")
            print("  • redo enrichment     - Restart enrichment phase")
            print("  • abort               - Discard all results")

    def _process_command(self, gate_name: str, command: str, data: dict) -> dict:
        """
        Process user command.

        Returns decision dict or continues loop.
        """
        # Simple commands
        if command == "proceed" or command == "continue":
            return {"action": "proceed"}

        if command == "approve":
            return {"action": "complete"}

        if command == "abort":
            confirm = input("⚠️  Are you sure you want to abort? (yes/no): ").strip().lower()
            if confirm == "yes":
                return {"action": "abort"}
            else:
                print("❌ Abort cancelled.")
                return {"action": "continue_loop"}

        if command == "redo":
            return {"action": "redo"}

        if command == "pause":
            return {"action": "pause"}

        # Informational commands
        if command == "show more":
            items = data.get("items", [])
            print(f"\n📋 Items 11-30:")
            for i, item in enumerate(items[10:30], 11):
                print(f"  {i}. {item.get('name', 'Unknown')}")
            return {"action": "continue_loop"}

        if command == "show batch":
            # Show latest batch
            batches = data.get("enriched_batches", [])
            if batches:
                latest = batches[-1]
                print(f"\n📋 Latest Batch (Batch {len(batches)}):")
                for item in latest.get("items", []):
                    print(f"  • {item.get('name')} - Confidence: {item.get('confidence', 0):.2f}")
            return {"action": "continue_loop"}

        if command == "show stats":
            # Use agent for detailed analysis
            if self.agent:
                analysis = self.agent.show_statistics(data)
                print(f"\n{analysis}")
            else:
                print("\n📊 (Agent not available for detailed stats)")
            return {"action": "continue_loop"}

        if command == "show low":
            items = data.get("items", []) or data.get("results_so_far", [])
            low_items = [item for item in items if item.get("confidence", 0) < 0.5]
            print(f"\n📋 Low-confidence items ({len(low_items)}):")
            for item in low_items:
                print(f"  • {item.get('name')} - Confidence: {item.get('confidence', 0):.2f}")
            return {"action": "continue_loop"}

        # Adjustment commands
        if command.startswith("limit "):
            try:
                n = int(command.split()[1])
                return {
                    "action": "proceed",
                    "adjustments": {"max_items": n}
                }
            except:
                print("❌ Invalid limit. Use: limit <number>")
                return {"action": "continue_loop"}

        if command.startswith("filter "):
            keyword = command[7:].strip()
            return {
                "action": "proceed",
                "adjustments": {"filter_keyword": keyword}
            }

        if command == "re-enrich low":
            return {
                "action": "re_enrich",
                "target": "low_confidence"
            }

        if command == "redo enrichment":
            return {"action": "redo_enrichment"}

        # Unknown command
        print(f"❌ Unknown command: {command}")
        print("💡 Type a command from the list above")
        return {"action": "continue_loop"}
```

---

### Step 5: Build Main Orchestration Workflow

Combine phases with gates.

**File**: `your_app/workflows/orchestration.py`

```python
"""
Main orchestration workflow with gates.
"""

from dana.core.workflow.base_workflow import BaseWorkflow
from dana.common.protocols import DictParams

from ..session import ResearchSession
from ..gates import GateHandler
from .discovery import DiscoveryWorkflow
from .enrichment import EnrichmentWorkflow
from .validation import ValidationWorkflow


class ResearchOrchestrationWorkflow(BaseWorkflow):
    """
    Orchestrates research with human-in-the-loop gates.

    Phases:
    1. Discovery → Gate 1 →
    2. Enrichment (batched) → Gate 2 (progress) →
    3. Validation → Gate 3 →
    4. Complete
    """

    def __init__(self, session: ResearchSession | None = None, **kwargs):
        super().__init__(workflow_id="research-orchestration", **kwargs)

        # Session and gates
        self.session = session or ResearchSession()
        self.gate_handler = GateHandler(self.session)

        # Phase workflows
        self.discovery = DiscoveryWorkflow()
        self.enrichment = EnrichmentWorkflow()
        self.validation = ValidationWorkflow()

    def _do_execute(self, **kwargs) -> DictParams:
        """
        Execute research with gates.

        This workflow pauses at gates for human input.
        """
        topic = kwargs.get("topic", "")
        scope = kwargs.get("scope", {})

        self.session.topic = topic
        self.session.scope = scope

        # ========== PHASE 1: DISCOVERY ==========
        print("\n🔄 Phase 1: Discovery...")
        discovery_result = self.discovery.execute(
            topic=topic,
            scope=scope,
            max_items=kwargs.get("max_items", 100)
        )

        inner = discovery_result.get("result", {})
        if not inner.get("success"):
            return {"success": False, "error": "Discovery failed"}

        self.session.discovered_items = inner.get("items", [])
        self.session.current_phase = "discovery"

        # ========== GATE 1: APPROVE DISCOVERY ==========
        gate1_decision = self.gate_handler.present_gate(
            "discovery",
            {"items": self.session.discovered_items}
        )

        if gate1_decision["action"] == "abort":
            return {"success": False, "aborted_at": "gate1"}

        if gate1_decision["action"] == "redo":
            # Restart discovery with potentially adjusted params
            return self._do_execute(**kwargs)

        # Apply adjustments (filters, limits)
        items_to_enrich = self._apply_gate_adjustments(
            self.session.discovered_items,
            gate1_decision.get("adjustments", {})
        )

        # ========== PHASE 2: ENRICHMENT ==========
        print(f"\n🔄 Phase 2: Enrichment ({len(items_to_enrich)} items)...")
        self.session.current_phase = "enrichment"

        batch_size = self.session.batch_size
        batches = self._create_batches(items_to_enrich, batch_size)
        self.session.total_batches = len(batches)

        for i, batch in enumerate(batches):
            print(f"  Processing batch {i+1}/{len(batches)}...")

            # Enrich batch
            batch_result = self.enrichment.execute(items=batch)
            inner = batch_result.get("result", {})

            if inner.get("success"):
                enriched_batch = inner.get("items", [])
                self.session.enriched_items.extend(enriched_batch)
                self.session.enriched_batches.append({
                    "number": i + 1,
                    "items": enriched_batch
                })
                self.session.current_batch = i + 1

            # ========== GATE 2: PROGRESS CHECKPOINT ==========
            # Show gate every 5 batches or at end
            if (i + 1) % 5 == 0 or (i + 1) == len(batches):
                # Compute quality stats
                quality_stats = self._compute_quality_stats(self.session.enriched_items)

                gate2_decision = self.gate_handler.present_gate(
                    "progress",
                    {
                        "current_batch": i + 1,
                        "total_batches": len(batches),
                        "results_so_far": self.session.enriched_items,
                        "quality_stats": quality_stats,
                        "enriched_batches": self.session.enriched_batches,
                    }
                )

                if gate2_decision["action"] == "abort":
                    return {"success": False, "aborted_at": "gate2"}

                if gate2_decision["action"] == "pause":
                    return {
                        "success": True,
                        "paused": True,
                        "items": self.session.enriched_items,
                        "session": self.session.to_dict()
                    }

        # ========== PHASE 3: VALIDATION ==========
        print("\n🔄 Phase 3: Validation...")
        self.session.current_phase = "validation"

        validation_result = self.validation.execute(
            items=self.session.enriched_items
        )

        inner = validation_result.get("result", {})
        if not inner.get("success"):
            return {"success": False, "error": "Validation failed"}

        self.session.validated_items = inner.get("items", [])
        self.session.validation_report = inner.get("quality_report", {})

        # ========== GATE 3: FINAL APPROVAL ==========
        gate3_decision = self.gate_handler.present_gate(
            "final",
            {
                "items": self.session.validated_items,
                "quality_report": self.session.validation_report,
            }
        )

        if gate3_decision["action"] == "abort":
            return {"success": False, "aborted_at": "gate3"}

        if gate3_decision["action"] == "redo_enrichment":
            # Reset and re-run enrichment
            self.session.reset_from_phase("enrichment")
            # Would need to re-run from enrichment phase
            # (Implementation depends on your needs)

        if gate3_decision["action"] == "re_enrich":
            # Re-enrich specific items (e.g., low confidence)
            # (Implementation depends on your needs)
            pass

        # ========== COMPLETE ==========
        self.session.current_phase = "complete"

        return {
            "success": True,
            "items": self.session.validated_items,
            "session_summary": self.session.get_summary(),
            "quality_report": self.session.validation_report,
        }

    def _apply_gate_adjustments(self, items: list, adjustments: dict) -> list:
        """Apply gate adjustments (filters, limits)."""
        filtered = items

        # Apply filter
        if "filter_keyword" in adjustments:
            keyword = adjustments["filter_keyword"].lower()
            filtered = [
                item for item in filtered
                if keyword not in item.get("name", "").lower()
            ]
            print(f"✅ Filtered out items with '{keyword}' ({len(items) - len(filtered)} removed)")

        # Apply limit
        if "max_items" in adjustments:
            max_items = adjustments["max_items"]
            filtered = filtered[:max_items]
            print(f"✅ Limited to {max_items} items")

        return filtered

    def _create_batches(self, items: list, batch_size: int) -> list[list]:
        """Split items into batches."""
        batches = []
        for i in range(0, len(items), batch_size):
            batches.append(items[i:i + batch_size])
        return batches

    def _compute_quality_stats(self, items: list) -> dict:
        """Compute quality statistics."""
        if not items:
            return {}

        confidences = [item.get("confidence", 0) for item in items]
        avg = sum(confidences) / len(confidences)

        high = sum(1 for c in confidences if c > 0.8)
        medium = sum(1 for c in confidences if 0.5 <= c <= 0.8)
        low = sum(1 for c in confidences if c < 0.5)

        return {
            "average_confidence": avg,
            "high_confidence_count": high,
            "medium_confidence_count": medium,
            "low_confidence_count": low,
        }
```

---

### Step 6: Create Application Entry Point

**File**: `your_app/main.py`

```python
"""
Main entry point for research application.
"""

import json
from .session import ResearchSession
from .workflows.orchestration import ResearchOrchestrationWorkflow


def main():
    """Run research with interactive gates."""

    print("=" * 80)
    print("Research Application - Human-in-the-Loop")
    print("=" * 80)

    # Get research parameters
    topic = input("\n📝 Research topic: ").strip()
    if not topic:
        print("❌ Topic required")
        return

    region = input("🌍 Region (optional): ").strip()
    scope = {"region": region} if region else {}

    # Create session
    session = ResearchSession(topic=topic, scope=scope)

    # Create and run orchestration workflow
    workflow = ResearchOrchestrationWorkflow(session=session)

    print("\n🚀 Starting research...")

    result = workflow.execute(topic=topic, scope=scope, max_items=100)

    # Handle result
    inner = result.get("result", {})

    if not inner.get("success"):
        aborted_at = inner.get("aborted_at")
        if aborted_at:
            print(f"\n⚠️  Research aborted at {aborted_at}")
        else:
            print(f"\n❌ Research failed: {inner.get('error')}")
        return

    if inner.get("paused"):
        print("\n⏸️  Research paused. Partial results saved.")
        items = inner.get("items", [])
    else:
        print("\n✅ Research complete!")
        items = inner.get("items", [])

    # Export results
    output_file = "research_results.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "items": items,
            "session": session.to_dict(),
            "quality_report": inner.get("quality_report", {})
        }, f, indent=2, ensure_ascii=False)

    print(f"💾 Results exported to: {output_file}")
    print(f"📊 Total items: {len(items)}")

    # Save session
    session.save("research_session.json")
    print("💾 Session saved to: research_session.json")


if __name__ == "__main__":
    main()
```

---

## Step 7: Testing

Create tests for each component.

**File**: `tests/test_session.py`

```python
"""Test session state management."""

from your_app.session import ResearchSession


def test_session_creation():
    """Test session creation."""
    session = ResearchSession(topic="AI research")
    assert session.current_phase == "discovery"
    assert session.topic == "AI research"


def test_session_can_proceed():
    """Test proceed logic."""
    session = ResearchSession()

    # Cannot proceed without discovered items
    assert not session.can_proceed()

    # Can proceed after discovery
    session.discovered_items = [{"name": "Item 1"}]
    assert session.can_proceed()


def test_session_reset():
    """Test reset functionality."""
    session = ResearchSession()
    session.discovered_items = [{"name": "Item 1"}]
    session.enriched_items = [{"name": "Item 1", "detail": "X"}]

    # Reset from enrichment
    session.reset_from_phase("enrichment")

    assert session.enriched_items == []
    assert session.discovered_items is not None  # Not reset


def test_session_persistence():
    """Test save/load."""
    session = ResearchSession(topic="Test")
    session.discovered_items = [{"name": "Item 1"}]

    # Save
    session.save("/tmp/test_session.json")

    # Load
    loaded = ResearchSession.load("/tmp/test_session.json")
    assert loaded.topic == "Test"
    assert len(loaded.discovered_items) == 1
```

**File**: `tests/test_workflows.py`

```python
"""Test phase workflows."""

from your_app.workflows.discovery import DiscoveryWorkflow
from your_app.workflows.enrichment import EnrichmentWorkflow
from your_app.workflows.validation import ValidationWorkflow


def test_discovery_workflow():
    """Test discovery workflow."""
    workflow = DiscoveryWorkflow()

    result = workflow.execute(
        topic="coffee companies",
        scope={"region": "Vietnam"},
        max_items=10
    )

    inner = result.get("result", {})
    assert inner.get("success")
    assert "items" in inner
    assert len(inner["items"]) <= 10


def test_enrichment_workflow():
    """Test enrichment workflow."""
    workflow = EnrichmentWorkflow()

    items = [
        {"name": "Company A", "url": "https://example.com"},
        {"name": "Company B", "url": "https://example.org"},
    ]

    result = workflow.execute(items=items)

    inner = result.get("result", {})
    assert inner.get("success")
    assert len(inner["items"]) == 2
    assert all("confidence" in item for item in inner["items"])


def test_validation_workflow():
    """Test validation workflow."""
    workflow = ValidationWorkflow()

    items = [
        {"name": "Company A", "description": "Desc A", "confidence": 0.9},
        {"name": "Company B", "description": "Desc B", "confidence": 0.5},
        {"name": "Company A", "description": "Desc A", "confidence": 0.9},  # Duplicate
    ]

    result = workflow.execute(items=items)

    inner = result.get("result", {})
    assert inner.get("success")
    assert inner.get("duplicates_removed") == 1
    assert len(inner["items"]) == 2
```

---

## Step 8: Add Agent (Optional)

For autonomous work within phases and gate command handling.

**File**: `your_app/agent.py`

```python
"""
Research agent with human-in-the-loop support.
"""

from dana.core.agent.base_agent import STARAgent
from .workflows.orchestration import ResearchOrchestrationWorkflow
from .session import ResearchSession


class ResearchAgent(STARAgent):
    """
    <PUBLIC_DESCRIPTION>
    Research agent that conducts investigations with human oversight.

    Provides:
    - Autonomous discovery and enrichment
    - Interactive approval gates
    - Flexible conversation within phases
    - Quality analysis and recommendations
    </PUBLIC_DESCRIPTION>

    <IDENTITY>
    You are a research assistant that helps humans conduct thorough investigations.
    You work autonomously within approved phases, but respect human oversight at gates.
    You provide analysis, answer questions, and adapt to human feedback.
    </IDENTITY>
    """

    def __init__(self, **kwargs):
        super().__init__(
            agent_type="research-agent",
            agent_id="research-agent",
            **kwargs
        )

        self.session = ResearchSession()

        self.with_workflows(
            ResearchOrchestrationWorkflow(session=self.session),
        )

    def research_with_gates(self, topic: str, scope: dict | None = None) -> dict:
        """
        Conduct research with interactive gates.

        Args:
            topic: Research topic
            scope: Additional scope parameters

        Returns:
            Research results
        """
        workflow = ResearchOrchestrationWorkflow(session=self.session)
        workflow.gate_handler.agent = self  # Give gate access to agent

        result = workflow.execute(topic=topic, scope=scope or {})
        return result.get("result", {})

    def show_statistics(self, data: dict) -> str:
        """
        Analyze data and provide statistics.

        Called from gate commands like "show stats".
        Uses agent reasoning to provide insights.
        """
        # Use agent's query method to analyze
        result = self.query(
            caller_message=f"""Analyze this research data and provide detailed statistics:

            Data: {data}

            Provide:
            - Quality breakdown by field
            - Confidence distribution
            - Completeness analysis
            - Recommendations for improvement
            """
        )

        return result.get("content", "No analysis available")
```

---

## Complete File Structure

```
your_app/
├── __init__.py
├── session.py              # Session state management
├── gates.py                # Gate handler
├── agent.py                # Optional agent
├── main.py                 # Entry point
│
├── workflows/
│   ├── __init__.py
│   ├── discovery.py        # Phase 1
│   ├── enrichment.py       # Phase 2
│   ├── validation.py       # Phase 3
│   └── orchestration.py    # Main workflow with gates
│
├── resources/              # Custom resources (optional)
│   ├── __init__.py
│   └── ...
│
├── scripts/
│   ├── simple_run.py       # Simple example
│   └── with_agent.py       # Agent example
│
└── tests/
    ├── test_session.py
    ├── test_workflows.py
    └── test_gates.py
```

---

## Running Your Application

### CLI Mode

```bash
python -m your_app.main
```

### Programmatic Mode

```python
from your_app.session import ResearchSession
from your_app.workflows.orchestration import ResearchOrchestrationWorkflow

# Create session
session = ResearchSession(topic="AI Research", scope={"region": "US"})

# Run workflow
workflow = ResearchOrchestrationWorkflow(session=session)
result = workflow.execute(topic="AI Research", scope={"region": "US"})

# Access results
items = result["result"]["items"]
```

### With Agent

```python
from your_app.agent import ResearchAgent

agent = ResearchAgent()
result = agent.research_with_gates(
    topic="Coffee companies",
    scope={"region": "Vietnam"}
)
```

---

## Advanced Features

### Session Persistence & Resumption

```python
# Save at any gate
session.save("research_session.json")

# Resume later
session = ResearchSession.load("research_session.json")
workflow = ResearchOrchestrationWorkflow(session=session)

# Continue from where you left off
result = workflow.execute(topic=session.topic, scope=session.scope)
```

### Web Interface

Replace CLI gates with web UI:

```python
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/gate/<gate_name>", methods=["GET", "POST"])
def web_gate(gate_name):
    """Present gate in web UI."""
    if request.method == "GET":
        # Show gate UI
        data = get_gate_data(gate_name)
        return render_template("gate.html", gate=gate_name, data=data)
    else:
        # Process command
        command = request.form.get("command")
        decision = process_command(gate_name, command)
        return jsonify(decision)
```

### Automated Gates with Thresholds

```python
def present_gate_with_auto(self, gate_name: str, data: dict, threshold: float = 0.8):
    """Auto-proceed if quality exceeds threshold."""

    quality_score = data.get("quality_stats", {}).get("average_confidence", 0)

    if quality_score >= threshold:
        print(f"✅ Quality threshold met ({quality_score:.2f} >= {threshold}). Auto-proceeding...")
        return {"action": "proceed"}
    else:
        # Present gate for human review
        return self.present_gate(gate_name, data)
```

---

## Next Steps

1. **Customize phases** for your domain
2. **Add domain-specific resources** (data sources, extractors)
3. **Design gate commands** appropriate to your use case
4. **Build quality metrics** specific to your data
5. **Create agent prompts** if using agent mode
6. **Add persistence** for long-running jobs
7. **Build UI** (web or CLI) for gates
8. **Test thoroughly** with real data

---

## References

- [Human-in-the-Loop Pattern](../design/human_in_loop_pattern.md)
- [Workflow Patterns](../design/workflow_design_patterns.md)
- [Vietnam Coffee Example](../use-cases/vietnam_coffee/)
- [Agent Design Patterns](../design/agent_design_patterns.md)

---

**Last Updated**: 2025-10-14
**Status**: Production Guide
**Maintainers**: Dana Framework Team
