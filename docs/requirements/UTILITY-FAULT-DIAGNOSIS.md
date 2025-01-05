# Utility Fault Diagnosis Scenario

This scenario describes how a Domain Expert Agent (DXA) performs root-cause analysis of alarms in an electrical grid base station, supporting grid operators in fault diagnosis and resolution.

## Grid Station Alarm Analysis

**Actor:** Grid Operator + Diagnostic Expert DXA
**Goal:** Determine precise root cause of grid control system alarms

### Context

- Base station environment with grid control equipment
- Alarm triggered by subsystem malfunction
- DXA has access to:
  - Grid configuration knowledge base
  - Equipment blueprints (PDF format)
  - Control system documentation
  - Historical alarm patterns
  - Real-time sensor/telemetry data
  - Grid topology and connection diagrams

### System Architecture

```mermaid
graph TB
    subgraph "Control Room"
        A[Alarm System] --> D[DXA]
        O[Operator] --> D
    end
    
    subgraph "DXA System"
        D <--> KB[Knowledge Base]
        D <--> BP[Blueprint Parser]
        D <--> RT[Real-time Data]
        D <--> RCA[Root Cause Analyzer]
    end
    
    subgraph "Knowledge Sources"
        KB --> GC[Grid Configuration]
        KB --> TD[Topology Data]
        KB --> HP[Historical Patterns]
        KB --> EQ[Equipment Specs]
    end
```

### Root Cause Analysis Process

```mermaid
sequenceDiagram
    participant A as Alarm System
    participant D as DXA
    participant K as Knowledge Base
    participant B as Blueprint Analysis
    participant H as Human Expert

    A->>D: Alarm triggered
    activate D
    D->>K: Query grid configuration
    D->>B: Scan relevant blueprints
    par Analysis
        D->>K: Check historical patterns
        D->>A: Query related alarms
    end
    
    loop Deep Analysis
        D->>D: Cross-reference data
        D->>D: Apply diagnostic rules
        alt Needs Human Input
            D->>H: Request expert judgment
            H-->>D: Provide insight
        end
    end
    
    D-->>O: Present root cause
    deactivate D
```

### Success Criteria

- Single root cause identified (vs probability-ranked list)
- Supporting evidence documented
- Clear fault location specified
- Minimal human expert consultation needed
- Accurate blueprint interpretation
- Rapid analysis completion

### DXA Performance Metrics

- Root cause accuracy rate
- Time to determination
- False positive rate
- Human expert consultation frequency
- Blueprint analysis accuracy
- Knowledge base coverage

### Key Capabilities

- PDF blueprint parsing and interpretation
- Grid topology understanding
- Real-time system state analysis
- Pattern recognition in alarm sequences
- Integration with control systems
- Selective human expert engagement
