# Dana Reflection Framework: Design Document

## Executive Summary

The Reflection Framework enables Dana STARAgents to learn from experience through a dual-mode architecture: **OPERATE** mode for real-time execution and **LEARN** mode for asynchronous knowledge mutation. This document outlines the architecture for the HVAC autonomous agent use case with an 8-day implementation plan.

## Architecture Overview

```mermaid
graph TB
    subgraph "STARAgent Dual Modes"
        OM[OPERATE Mode<br/>See-Think-Act<br/>READ Knowledge<br/>WRITE Observations]
        LM[LEARN Mode<br/>Reflect-Consolidate<br/>READ Observations<br/>WRITE Knowledge]
    end
    
    OM -->|append| OB[Observation Buffer<br/>events.jsonl]
    OM -->|read-only| KS[Knowledge Store<br/>embeddings + patterns]
    
    OB -->|consume| LM
    LM -->|mutate| KS
    
    SIM[Simulation<br/>Dreaming] -.->|synthetic observations| LM
    
    subgraph "Learning Pipeline"
        LM --> ACQ[Acquisitive<br/>Real-time]
        LM --> EPI[Episodic<br/>Session]
        LM --> INT[Integrative<br/>Cross-session]
        LM --> CON[Consolidative<br/>Long-term]
    end
    
    ACQ --> KS
    EPI --> KS
    INT --> KS
    CON --> KS
```

## Core Concepts

### Agent Operating Modes

```mermaid
stateDiagram-v2
    [*] --> OPERATE
    OPERATE --> LEARN: Trigger<br/>(schedule/threshold)
    LEARN --> OPERATE: Complete
    
    state OPERATE {
        [*] --> See
        See --> Think
        Think --> Act
        Act --> Record
        Record --> See
    }
    
    state LEARN {
        [*] --> ConsumeObs
        ConsumeObs --> ProcessScopes
        ProcessScopes --> MutateKnowledge
        MutateKnowledge --> Consolidate
        Consolidate --> [*]
    }
```

**OPERATE Mode:**
- Synchronous, latency-sensitive
- Read-only knowledge access
- Append observations to buffer
- Never blocks on learning

**LEARN Mode:**
- Asynchronous, can be slow
- Processes observation backlog
- Mutates knowledge store
- Runs simulation campaigns (dreaming)

### Event Sourcing Pattern

All observations and feedback stored as typed events in append-only log:

```json
{"type": "hvac_observation", "timestamp": "2024-10-31T10:00:00", "zone": "floor_2_west", "temp": 72.5, "setpoint": 72, "occupancy": 12}
{"type": "action_taken", "timestamp": "2024-10-31T10:00:05", "zone": "floor_2_west", "action": "increase_cooling", "magnitude": 0.5}
{"type": "feedback", "timestamp": "2024-10-31T10:15:00", "ref_event_id": "action_123", "outcome": "comfort_complaint", "source": "occupant"}
```

### Sessions and Learning Scopes (KISS Mapping)

- Session = episodic unit (1:1). All events in a session carry `session_id`.
- Per-STAR loop: micro-acquisitions (system prompt timeline updates) in hot cache.
- Per-query (may span multiple STAR loops): acquisitive artifact in working memory.
- Integrative: runs across sessions (e.g., daily) to extract cross-session patterns.
- Consolidative: promotes stable knowledge (e.g., weekly), session-agnostic but with provenance.

Prompt Learning:
- Prompt versions are persisted under `knowledge/prompts` with provenance and metrics.
- Prompt learning for resources and workflows is explicitly deferred to the next sprint.

Triggers:
- On STAR loop end → update acquisitive hot cache.
- On query completion → write/roll up acquisitive artifact.
- On session end → write episodic summary (embedding + metadata + provenance).
- Daily → run integrative consolidation across recent sessions.
- Weekly → run consolidative promotion of validated rules/prompts.

## Directory Structure

```
dana_data/
├── events/
│   ├── production/
│   │   └── events.jsonl                    # Append-only event log
│   └── simulation/
│       └── dream_campaign_001.jsonl        # Simulated experiences
│
├── knowledge/
│   ├── acquisitive/
│   │   └── working_memory.json             # Hot cache (TTL: 1 hour), keyed by query_id/session_id
│   │
│   ├── episodic/
│   │   ├── embeddings.npy                  # Session-level summary embeddings (1:1 with session_id)
│   │   ├── metadata.jsonl                  # Per-session metadata (provenance, counts, timebounds)
│   │   └── stats.json                      # Count, last_consolidation
│   │
│   ├── integrative/
│   │   ├── patterns.json                   # Extracted patterns
│   │   ├── clusters.npy                    # Cluster centroids
│   │   ├── cluster_metadata.json           # Cluster semantics
│   │   └── consolidation_log.jsonl         # Audit trail
│   │
│   ├── prompts/                            # Prompt learning (this sprint)
│   │   ├── versions/
│   │   │   ├── v0001.txt
│   │   │   └── v0002.txt
│   │   ├── changelog.jsonl                 # Prompt diffs, provenance, metrics
│   │   ├── active.json                     # Pointer to active version
│   │   └── NOTE.txt                        # Resource/Workflow prompt learning deferred to next sprint
│   │
│   └── consolidative/
│       ├── rules/
│       │   └── validated_rules.json        # High-confidence rules
│       ├── prompts/
│       │   └── system_prompt_v2.txt        # Global prompt refinements (deprecated by prompts store)
│       └── baselines/
│           └── performance_metrics.json    # Expected performance
│
└── meta/
    └── agent_state.json                    # Mode, last_learn_time, etc.
```

## Learning Scopes

```mermaid
graph LR
    OBS[Observations] --> ACQ[Acquisitive<br/>Minutes<br/>Hot cache]
    ACQ --> EPI[Episodic<br/>Days<br/>Vector store]
    EPI --> INT[Integrative<br/>Weeks<br/>Patterns]
    INT --> CON[Consolidative<br/>Permanent<br/>Rules/Prompts]
    
    style ACQ fill:#ff9999
    style EPI fill:#ffcc99
    style INT fill:#99ccff
    style CON fill:#99ff99
```

| Scope | Timeframe | Storage | Purpose | Demo Status |
|-------|-----------|---------|---------|-------------|
| **Acquisitive** | Minutes-Hours | In-memory JSON | Immediate adaptation | Stubbed |
| **Episodic** | Days-Weeks | NumPy vectors | Similarity-based retrieval | **Full Implementation** |
| **Integrative** | Weeks-Months | Clusters + Patterns | Synthesized rules | **Prototype** |
| **Consolidative** | Permanent | Validated rules | Production knowledge | Stubbed |

## HVAC Use Case Specifics

### Learning Opportunities

**1. Zone-Specific Thermal Characteristics**
- Learning: Each zone's thermal mass, airflow patterns, sun exposure
- Source: Temperature sensor data, HVAC response times
- Destination: Episodic → Integrative patterns

**2. Occupancy Pattern Prediction**
- Learning: When zones are occupied, density patterns
- Source: Occupancy sensors, calendar data, historical patterns
- Destination: Integrative patterns → Predictive models

**3. Comfort vs Efficiency Tradeoffs**
- Learning: Acceptable temperature ranges per zone/time
- Source: Comfort complaints, energy consumption, occupant feedback
- Destination: Consolidative rules

**4. Anomaly Detection Improvement**
- Learning: What's normal for THIS building
- Source: Equipment sensor data, maintenance logs
- Destination: Episodic → Integrative baselines

### Demo Scenario

**Before Learning:**
```
Zone overheating → Generic response → Energy waste + discomfort
Anomaly detected → 10 possible causes → Slow diagnosis
```

**After Learning (Session 1-10):**
```
Zone overheating → Retrieve similar episodes → Optimized response
Anomaly detected → "Similar to episode #47" → Fast root cause
```

**Metrics:**
- Energy consumption reduction: 15-25%
- Comfort complaint reduction: 40%
- Anomaly diagnosis time: 60% faster

## Core Interfaces

```python
# Agent mode enumeration
class AgentMode(Enum):
    OPERATE = "operate"
    LEARN = "learn"

# Event types
@dataclass
class Event:
    type: str
    timestamp: datetime
    agent_id: str
    data: dict
    metadata: dict

# Knowledge with provenance
@dataclass  
class Knowledge:
    content: Any
    scope: Scope
    confidence: float
    provenance: dict
    created: datetime
    ttl: Optional[timedelta]

# Agent with dual modes
class STARAgent:
    def operate(self, environment) -> Action
    def learn(self, duration: Optional[timedelta] = None)
    def dream(self, simulator: SimulationEnvironment, n_episodes: int)

# Storage interfaces
class EventLog:
    def append(self, event: Event)
    def read_since(self, checkpoint: int) -> Iterator[Event]

class KnowledgeStore:
    def retrieve(self, query, scope: Scope, k: int) -> List[Knowledge]
    def write(self, knowledge: Knowledge, scope: Scope)

# Prompt persistence and APIs
@dataclass
class PromptVersion:
    version: str
    content: str
    created: datetime
    provenance: dict
    metrics: dict

class LocalPromptStore:  # directory-based persistence under knowledge/prompts
    def get_active(self) -> PromptVersion
    def list_versions(self) -> List[PromptVersion]
    def set_active(self, version: str)
    def create_version(self, content: str, provenance: dict) -> PromptVersion

class PromptsAPI:
    def render(self, template_name: str, context: dict) -> str
    def learn(self, signal: dict) -> PromptVersion  # creates new version when warranted
```

## Team Structure & Coordination

## Team Structure & Coordination

```mermaid
graph TB
    PM[annieha<br/>Project Manager]
    
    MAIN[lam<br/>Main SWE<br/>1.0 FTE]
    APP[william<br/>Application SWE<br/>0.5 FTE]
    INT[zooey<br/>Llama-Stack<br/>0.5 FTE]
    
    PM --> MAIN
    PM --> APP
    PM --> INT
    
    MAIN -->|Framework Core| FC[Event Log<br/>Knowledge Store<br/>Learning Scopes]
    APP -->|HVAC Logic| HL[Agent<br/>Simulator<br/>Domain Rules]
    INT -->|LLM Integration| LI[Llama-Stack<br/>Model Calls<br/>Prompt Management]
    
    FC <-.->|Integration| HL
    FC <-.->|Integration| LI
    HL <-.->|Integration| LI
```

**Coordination Strategy:**
- Daily 15-min standups (9:00 AM)
- Sync integration sessions (Wed, Fri afternoons)
- Async: Slack for quick questions, PRs for code review
- AI coding: Each dev uses AI pair programming to 2x velocity

## 8-Day Implementation Plan

### Day 1 - Friday, Oct 31, 2025 - Foundation & Setup (Lam unavailable until Day 2)

**@annieha (PM):**
- Kickoff (30 min): review design, assign roles, define success metrics
- Set up tracking (Jira/Linear) and demo milestones

**All-hands (Architectural Review - 60 min):**
- Review architecture and interfaces (`EventLog`, `KnowledgeStore`, `STARAgent`)
- Confirm Llama-Stack integration points: `Inference API`, `Agent API` (primary focus); `Storage API`, `Conversation API`, `RAG` deferred to focus on packaging/installation (Prompts is local filesystem-based)
- Align on simulator requirements: expose environment state outputs/telemetry, not just accept inputs; simulated HVAC data (no real building data yet)
- Align on web application requirements: lightweight demo app to drive HVAC use case and demonstrate learning
- Note: Lam unavailable Day 1; foundational work shifts to Day 2

**@lam (Main SWE):** Not available - work shifts to Day 2

**@william (Application) - 4 hours:**
- [ ] HVAC simulator design (zones, thermal dynamics, environment state outputs/telemetry)
- [ ] Simulator skeleton generated with AI assistant
- [ ] Define web app integration points with agent framework, simulator, and LLM APIs
- **Deliverable:** Simulator stub with basic zone dynamics and observable environment state; Web app integration points defined

**@zooey (Integration) - 4 hours:**
 - [ ] Llama-Stack dev environment ready
 - [ ] LLM client wrapper created and tested
 - [ ] Define and sequence API contracts: `Inference`, `Agent` (primary focus for packaging); `Storage`, `Conversation`, `RAG` deferred (Finetuning deferred)
 - **Deliverable:** Baseline connectivity + API contract plan (focusing on Inference/Agent APIs for packaging deliverable)

**Sync:** 4:30 PM - Blockers and priorities

Deliverables by role:
- @annieha: Success metrics, tracking/milestones defined
- All-hands: Architecture reviewed, integration points agreed (Lam's foundational work deferred to Day 2)
- @william: Simulator stub with observable environment state; Web app integration points defined
- @zooey: Llama-Stack connectivity + API contract plan

---

### Day 2 - Monday, Nov 3, 2025 - Foundation & Core Learning Loop

**@lam (Main SWE) - 8 hours:**
- [ ] Project structure and tooling
- [ ] Implement `EventLog` (append-only JSONL)
- [ ] Implement `KnowledgeStore` interfaces + filesystem backend
- [ ] Initialize directory-based prompts store; scaffold `LocalPromptStore` and `PromptsAPI`
- **Deliverable:** Event log + knowledge store scaffolding (Day 1 work shifted)

**@william - 4 hours:**
- [ ] Complete simulator (temperature dynamics, setpoint control, environment outputs)
- [ ] Create test scenarios (overheating, occupancy changes)
- [ ] Web application structure/skeleton (lightweight framework: Streamlit/Flask/FastAPI) - using Day 1 integration points
- [ ] Web app: Basic UI layout and simulator integration scaffolding
- **Deliverable:** Runnable simulator with realistic behavior and exported state/telemetry; Web app structure + basic UI with simulator connection

**@zooey - 4 hours:**
 - [ ] Implement `Inference API` integration (model selection, health check)
 - [ ] Stub `Agent API` (decision call surface)
 - **Deliverable:** `Inference API` live; `Agent` stub

**Sync:** 4:30 PM - Review foundational progress

Deliverables by role:
- @lam: Event log + knowledge store scaffolding; prompts directory scaffolded (Day 1 shifted work)
- @william: Runnable simulator with exported state/telemetry; Web app structure + basic UI with simulator connection
- @zooey: Inference API live; Agent stub

---

### Day 3 - Tuesday, Nov 4, 2025 - Core Learning Loop (cont'd)

**@lam - 8 hours:**
- [ ] Implement Episodic scope (events → embeddings)
- [ ] Retrieval via cosine similarity
- [ ] `STARAgent` skeleton (operate/learn modes)
- [ ] Implement end-of-session write trigger (episodic summary on session close)
- [ ] Local prompts service (filesystem): render + learn (MVP prompt learning)
- [ ] Create testable interfaces/harness for episodic learning (William can use to test HVAC integration)
- **Deliverable:** Working episodic learning pipeline with testable interfaces/harness (Day 2 work shifted)

**@william - 4 hours:**
- [ ] Add simulator observability (logging, metrics)
- [ ] Prepare episodic learning scenarios/test cases
- [ ] Ensure simulator/agent integration ready for episodic learning (verify agent can receive and process HVAC events)
- **Deliverable:** Enhanced simulator with observability; Integration ready for episodic learning

**@zooey - 4 hours:**
 - [ ] Wire `Agent API` to decision loop; connect to `Inference API`
 - [ ] Ensure LLM/Inference API is functional for agent decisions
 - **Deliverable:** Agent decisions using `Inference` API (foundation for Day 4 packaging)

**Sync:** 4:30 PM - Review episodic pipeline progress; prepare for Day 4 episodic learning and packaging

Deliverables by role:
 - @lam: Episodic pipeline functional with end-of-session write trigger; Testable interfaces/harness ready for William
 - @william: Simulator with observability added; Integration ready for episodic learning
- @zooey: Agent wired to Inference API; decisions flowing (foundation for packaging)

---

### Day 4 - Wednesday, Nov 5, 2025 - Episodic Learning & LlamaStack Packaging

**@lam - 8 hours:**
- [ ] Framework-level validation: test episodic learning pipeline with synthetic scenarios (prove learning works at framework level)
- [ ] Create test utilities/demo notebook showing learning curve (for William to use as reference)
- [ ] Implement per-query acquisitive artifact write on query completion
- [ ] Provide validation tools/test harness that William can use for HVAC-specific testing
- **Deliverable:** Framework-level learning validation complete; Test utilities and validation tools ready for William

**@william - 4 hours:**
- [ ] Wire episodic learning functionality into HVAC agent/simulator (use Lam's episodic pipeline and test harness from Day 3)
- [ ] Configure agent to retrieve episodic memories for HVAC decisions (query episodic knowledge store during decision-making)
- [ ] Run basic HVAC test scenarios using Lam's test utilities (from Day 3 preparation) - verify agent can retrieve and use episodic memories
- [ ] Validate HVAC integration: agent retrieves relevant past episodes and uses them in HVAC decision-making
- **Deliverable:** Episodic learning wired into HVAC agent/simulator; Agent successfully retrieves and uses episodic memories in HVAC test scenarios

**@zooey - 4 hours:**
 - [ ] LlamaStack packaging/installation setup (dev environment, deployment configuration, packaging scripts)
 - [ ] Package LLM/Inference API integration (from Day 3) into installable format
 - [ ] Basic installation verification and testing
 - [ ] Create initial installation documentation
 - **Deliverable:** LlamaStack packaging/installation working with LLM/Inference API packaged and installable

**Sync:** 4:00 PM - Review episodic learning progress and packaging status

Deliverables by role:
- @lam: Framework-level learning validation complete; Test utilities and validation tools ready for William; per-query acquisitive write
- @william: Episodic learning wired into HVAC agent/simulator; Agent successfully retrieves and uses episodic memories in HVAC test scenarios
- @zooey: LlamaStack packaging/installation working with LLM/Inference API packaged and installable

---

### Day 5 - Thursday, Nov 6, 2025 - Integration & Learning Proof

**@lam - 8 hours:**
- [ ] Implement Integrative scope (clustering, pattern extraction)
- [ ] Consolidation trigger logic
- [ ] Production hardening (error handling)
- **Deliverable:** Integrative learning working

**@william - 4 hours:**
- [ ] Run HVAC-specific learning proof: multiple episodes with same scenario repeated (determine number of episodes needed to show improvement)
- [ ] Create before/after demo scenarios: compare agent performance in first episode vs. later episodes
- [ ] Measure and document learning proof: collect metrics showing agent improvement (e.g., faster response, better decisions, lower energy)
- [ ] Prepare learning curve visualization/data: show how agent performance improves over episodes (using Lam's Day 4 test utilities as reference)
- **Deliverable:** HVAC learning proof demonstrated with metrics; Before/after scenarios ready; Learning curve data collected

**@zooey - 4 hours:**
- [ ] Expand LlamaStack packaging/installation documentation (deployment guides, installation steps, troubleshooting)
- [ ] Packaging verification and testing across different environments
- [ ] Installation verification scripts and test procedures
- **Deliverable:** Comprehensive LlamaStack packaging/installation documentation and verification procedures

Operational cadence notes:
- Integrative runs daily across sessions (batch job).

**Sync:** 4:30 PM - Integration review and learning proof demonstration

Deliverables by role:
- @lam: Integrative scope working + consolidation trigger logic
- @william: HVAC learning proof demonstrated with metrics; Before/after scenarios ready; Learning curve data collected
- @zooey: Comprehensive LlamaStack packaging/installation documentation and verification procedures

---

### Day 6 - Friday, Nov 7, 2025 - End-to-End Polish & Observability

**@lam - 8 hours:**
- [ ] Performance optimization (retrieval speed)
- [ ] Metrics collection (energy, comfort, accuracy)
- [ ] Integration sweep across components
- **Deliverable:** Polished core framework

**@william - 4 hours:**
- [ ] Enhance simulator realism (improve thermal dynamics, add more realistic scenarios)
- [ ] Wire simulated HVAC data through full pipeline (events → episodic learning → agent decisions)
- [ ] Validate metrics collection and observability (energy, comfort, accuracy) in pipeline
- [ ] Test end-to-end with enhanced simulator: verify learning pipeline works with more realistic simulated scenarios
- **Deliverable:** Enhanced simulated HVAC data flowing end-to-end through learning pipeline; Metrics collection validated

**@zooey - 4 hours:**
- [ ] Polish LlamaStack packaging/installation (error handling, edge cases, user experience)
- [ ] Installation verification across different environments (Linux, macOS, Windows if applicable)
- [ ] Complete deployment guides and troubleshooting documentation
- [ ] Create installation quick-start guide
- **Deliverable:** Production-ready LlamaStack packaging/installation with comprehensive documentation

**Sync:** 3:00 PM - Full team integration

Deliverables by role:
- @lam: Optimized retrieval + metrics collection integrated
- @william: Enhanced simulated HVAC data flowing end-to-end through learning pipeline; Metrics collection validated
- @zooey: Production-ready LlamaStack packaging/installation with comprehensive documentation

---

### Day 7 - Monday, Nov 10, 2025 - Demo Prep & Inspection Tools

**@lam - 8 hours:**
- [ ] Knowledge inspection tools (episodic memory inspection - show what agent learned, retrieve similar episodes)
- [ ] Integration support for demo: ensure inspection tools work with William's web app
- [ ] Final framework polish for demo readiness
- **Deliverable:** Knowledge inspection tools ready for demo; Framework demo-ready

**@william - 6 hours:**
- [ ] Polish web application: Complete UI/UX for HVAC demo
- [ ] Ensure web app demonstrates episodic learning functionality (show episodic memories, session boundaries, learning improvements)
- [ ] Integrate Lam's inspection tools into web app (display episodic memories retrieved, learning progress)
- [ ] Interactive controls: Start/stop episodes, scenario selection, parameter adjustment
- [ ] Display HVAC performance metrics and learning progress (comfort, energy efficiency, learning curve)
- **Deliverable:** Complete driving application ready for demo with episodic learning functionality demonstrated

**@zooey - 2 hours:**
 - [ ] Final LlamaStack packaging/installation validation
 - [ ] Installation guide final review and polish
 - [ ] Verify all installation paths work correctly
 - **Deliverable:** Finalized and validated LlamaStack packaging/installation

Operational cadence notes:
- Consolidative runs weekly to promote stable rules/prompts (versioned, with rollback plan).

**Sync:** 4:30 PM - Demo dry run #2

Deliverables by role:
- @lam: Knowledge inspection tools ready for demo; Framework demo-ready
- @william: Complete driving application ready for demo with episodic learning functionality demonstrated
- @zooey: Finalized and validated LlamaStack packaging/installation

---

### Day 8 - Tuesday, Nov 11, 2025 - Robustness, Demo Prep, and Handoff

**@lam - 8 hours:**
- [ ] Error handling, edge cases, recovery (corrupt files)
- [ ] Performance tests (≥1000 observations latency)
- [ ] Documentation polish (README, API docs, diagrams)
- **Deliverable:** Production-grade codebase ready for demo

**@william - 4 hours:**
- [ ] Demo script (narrative, timing) and environment setup
- [ ] Final practice run with web application demo
- [ ] Create one-pager handout
- **Deliverable:** Demo materials ready; Web application demo polished

**@zooey - 4 hours:**
- [ ] Complete LlamaStack deployment guide (production deployment procedures)
- [ ] Performance benchmarks for packaged installation (installation time, resource usage, API latency)
- [ ] Final validation of LLM/Inference API integration within packaged installation
- [ ] Create installation troubleshooting guide and FAQ
- **Deliverable:** Complete LlamaStack deployment guide, performance benchmarks, and final packaging validation

**Note:** Finetuning API is explicitly deferred to the next sprint. RAG, Conversation API, and Storage API are deferred to focus on packaging/installation as the primary LlamaStack deliverable.

**All team (2 hours):**
- [ ] Final rehearsal and handoff meeting (how to extend)
- **Deliverable:** Complete handoff package

**Demo Day:** Ready for presentation!

Deliverables by role:
- @lam: Production-grade codebase, docs/diagrams
- @william: Demo script, environment setup, handout; Complete web application for HVAC demo
- @zooey: Complete LlamaStack deployment guide, performance benchmarks, and final packaging validation
- All team: Final rehearsal + handoff package

---

## Success Metrics

### Technical Metrics
- **Learning works:** Agent improves over multiple episodes (number determined by testing)
- **Retrieval speed:** <10ms for episodic queries
- **Consolidation:** Patterns extracted from 100+ observations
- **Integration:** All components work together end-to-end
- **Prompt learning:** New prompt versions correlate with improved decision metrics (win rate/latency)

### Product Metrics (HVAC Demo)
- **Energy efficiency:** 15-25% improvement after learning
- **Comfort:** 40% fewer complaints
- **Anomaly diagnosis:** 60% faster root cause identification
- **Adaptation:** Agent learns building-specific patterns

### Team Velocity
- **AI coding boost:** 2x faster implementation vs manual
- **Integration overhead:** 20% of time (acceptable for team size)
- **Demo readiness:** Day 8

## Risk Mitigation

| Risk | Mitigation | Owner |
|------|------------|-------|
| Integration complexity | Daily sync sessions, clear interfaces | @annieha |
| HVAC simulator realism | Start simple, iterate based on feedback | @william |
| LLM reliability | Implement fallbacks, caching | @zooey |
| Learning doesn't work | Tune parameters early (Day 4 checkpoint) | @lam |
| Demo failure | Pre-record backup, save notebook outputs | @annieha |

## Extension Roadmap (Post-Demo)

**Phase 4: Multi-Agent (Weeks 3-4)**
- Distributed agents per building zone
- Knowledge consolidation across agents
- Centralized orchestration

**Phase 5: Production Deployment (Weeks 5-8)**
- Replace filesystem with vector DB
- Add monitoring/alerting
- Deploy to real building pilot

**Phase 6: Other Use Cases (Weeks 9-12)**
- Semiconductor RCA
- Financial fraud detection
- Framework generalization

---

**Document Version:** 1.2  
**Last Updated:** 2025-11-01  
**Owners:** @annieha (PM), @lam (Tech Lead)
**Note:** Updated scope and timing: (1) Zooey focuses on packaging/installation using LlamaStack as primary deliverable; RAG, Conversation API, and Storage API deferred. LLM/Inference API integration included. (2) William's integration/learning proof moved from Nov 5 to Nov 6; Nov 5 focuses on episodic learning functionality. Plan maintains 8-day timeline without extension.

## Gantt: 8-Day Schedule

```mermaid
gantt
  title 8-Day Implementation Schedule
  dateFormat  YYYY-MM-DD
  excludes    weekends

  section All Hands
  Architectural Review (Day 1) – arch, APIs, sim outputs :milestone, m1, 2025-10-31, 0d

  section lam (Main SWE)
  Day 2: EventLog+KnowledgeStore + prompts scaffold (Day 1 shifted) :d2_lam, 2025-11-03, 1d
  Day 3: Episodic pipeline + session close + local prompts MVP :d3_lam, after d2_lam, 1d
  Day 4: Framework validation + test utilities + acquisitive write :d4_lam, after d3_lam, 1d
  Day 5: Integrative scope + triggers       :d5_lam, after d4_lam, 1d
  Day 6: Retrieval perf + metrics wiring    :d6_lam, after d5_lam, 1d
  Day 7: Inspection tools + demo prep :d7_lam, after d6_lam, 1d
  Day 8: Robustness + docs/diagrams         :d8_lam, after d7_lam, 1d

  section william (Application)
  Day 1: Simulator stub + integration points :d1_w, 2025-10-31, 1d
  Day 2: Complete sim + web app structure+UI :d2_w, after d1_w, 1d
  Day 3: Observability + web app framework :d3_w, after d2_w, 1d
  Day 4: Episodic learning functionality    :d4_w, after d3_w, 1d
  Day 5: Integration + learning proof  :d5_w, after d4_w, 1d
  Day 6: Realistic data + web app metrics  :d6_w, after d5_w, 1d
  Day 7: Complete driving app + polish    :d7_w, after d6_w, 1d
  Day 8: Demo script + final web app prep  :d8_w, after d7_w, 1d

  section zooey (Llama-Stack)
  Day 1: Env + API contracts plan          :d1_z, 2025-10-31, 1d
  Day 2: Inference live; Agent stub        :d2_z, after d1_z, 1d
  Day 3: Wire Agent+Inference              :d3_z, after d2_z, 1d
  Day 4: Packaging/installation + LLM API :d4_z, after d3_z, 1d
  Day 5: Packaging docs + verification :d5_z, after d4_z, 1d
  Day 6: Packaging polish + deployment guides   :d6_z, after d5_z, 1d
  Day 7: Final packaging checks        :d7_z, after d6_z, 1d
  Day 8: Deploy guide + benchmarks        :d8_z, after d7_z, 1d

  section Milestones
  Demo Ready                        :milestone, m_demo, after d8_lam, 0d
```