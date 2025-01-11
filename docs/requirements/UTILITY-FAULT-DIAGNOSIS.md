<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# Utility Fault Diagnosis Scenario

This scenario describes how a Domain Expert Agent (DXA) performs root-cause analysis of alarms in an electrical grid base station, supporting grid operators in fault diagnosis and resolution.

<p align="center">
  <img src="https://www.electricaltechnology.org/wp-content/uploads/2021/10/Classification-of-Electric-Power-Distribution-Network-Systems.png" alt="Grid Distribution System" width="70%" />
</p>

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

<p align="center">
  <img src="https://i.ytimg.com/vi/Na-7jCAwUBY/hq720.jpg?sqp=-oaymwEhCK4FEIIDSFryq4qpAxMIARUAAAAAGAElAADIQj0AgKJD&rs=AOn4CLABpvlXlngGliKP9hKajbKHyzltTA" alt="Grid Utility Station Context" width="50%" />
</p>

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

## Demo Script (3 minutes)

### Setup (30s)

- Grid control room view showing base station monitoring interface
- Split screen displaying:
  - Alarm notification system
  - DXA analysis interface
  - Grid topology visualization
  - Blueprint analysis window

### Demo Flow

#### 0:00-0:30 - Normal Operation & Alarm

- Show normal grid monitoring state
- Trigger alarm from critical subsystem
- DXA immediately begins data collection:
  - Real-time sensor readings
  - Related alarms/events
  - Equipment state

#### 0:30-1:30 - Root Cause Analysis

- DXA performs multi-source analysis:
  - Parse relevant blueprints
  - Query grid configuration
  - Analyze historical patterns
  - Cross-reference documentation
- Show real-time reasoning process
- Display confidence levels for potential causes

#### 1:30-2:30 - Expert Consultation & Resolution

- DXA identifies need for human expertise
- Show targeted question generation
- Expert provides input
- DXA incorporates feedback and finalizes diagnosis
- Present definitive root cause with evidence

#### 2:30-3:00 - Value Summary

- Show time saved vs traditional diagnosis
- Display accuracy metrics
- Highlight knowledge capture for future cases
- Demonstrate blueprint analysis accuracy

### Interactive Elements

- Drill-down into blueprint analysis
- Alternative fault scenario exploration
- Historical case comparison
- Expert feedback integration

### Technical Requirements

#### Demo Environment

- Grid control system simulation
- Blueprint parsing system
- Real-time data streams
- Expert interface mockup

#### Visualization Requirements

- Alarm visualization
- Blueprint analysis overlay
- Reasoning process display
- Root cause confidence metrics
- Knowledge base updates

#### Backup Plans

- Pre-recorded analysis sequence
- Offline blueprint analysis results
- Sample expert consultation workflow
- Alternative fault scenarios
