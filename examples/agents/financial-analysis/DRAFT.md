# Playground Scripts Guide

## Run Order

### 1. `test_observer.py` - **Run First** ⚠️
**Purpose:** Precreates data in `.dana/dana_agent/default`

This script executes a full conversation with the coordinator agent, generating event logs, timeline entries, and learning data that subsequent scripts depend on.

```bash
python examples/agents/financial-analysis/test_observer.py
```

**Creates:**
- Event logs in `.dana/dana_agent/default/FinancialReportCoordinatorAgent__financial_report_coordinator/events/`
- Timeline data in session folders
- Learning data for episodic and acquisitive learning

---

### 2. `learn_playground.py` - Independent Learning Example
**Purpose:** Demonstrates how learning can be executed independently from the agent loop

Shows how to:
- Load acquisitive learnings: `coordinator_learner._load_acquisitive({})`
- Execute episodic reflection: `coordinator_learner._reflect_episodic({})`

**Requires:** Data created by `test_observer.py`

```bash
python examples/agents/financial-analysis/learn_playground.py
```

---

### 3. `event_playground.py` - Event Log & Timeline Access
**Purpose:** Demonstrates how to read event logs and timeline entries

Shows how to:
- Read event log: `coordinator._event_log.read_since(checkpoint=-2)`
- Read timeline: `coordinator._timeline.read_since(checkpoint=-2)`

**Requires:** Data created by `test_observer.py`

```bash
python examples/agents/financial-analysis/event_playground.py
```

---

## Summary

**Must run first:** `test_observer.py` to populate `.dana/dana_agent/default/` with required data.

**Then run:** `learn_playground.py` or `event_playground.py` to explore learning and event/timeline access patterns.

