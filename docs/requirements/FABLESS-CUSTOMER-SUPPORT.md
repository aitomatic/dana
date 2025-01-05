<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# Fabless Customer Design Support Scenario

This scenario describes how a Field Application Engineer (FAE), supported by a Domain Expert Agent (DXA), assists customers in successfully implementing IC designs through technical consultation and documentation.

<p align="center">
  <img src="https://phisonblog.com/wp-content/uploads/2023/03/1507431_WPICDesignProcess_01_112222.jpg" alt="IC Design Process Flow" width="50%" />
</p>

## Circuit Design Support Consultation

**Actor:** Field Application Engineer (FAE) + Design Expert DXA  
**Goal:** Guide customer to successful system design implementation using company's IC

### Context

- Customer (circuit/system designer) seeks design guidance
- FAE leads customer interaction via call/web meeting
- DXA has access to:
  - Internal IC documentation and application notes
  - Public datasheets and reference designs
  - Historical design consultations
  - Circuit design expertise knowledge base

<p align="center">
  <img src="https://www.powersystemsdesign.com/images/articles/1384946982Illustration_YoleSermaPressrelease_March2013.jpg" alt="Semiconductor Industry Structure" width="50%" />
</p>

### System Architecture

```mermaid
graph TB
    subgraph "Customer Interface"
        C[Customer] --> F[FAE]
    end
    
    subgraph "DXA System"
        F <--> D[Design Expert DXA]
        D <--> KB[Knowledge Base]
        D <--> PE[Parameter Engine]
        D <--> VA[Validation Agent]
    end
    
    subgraph "Knowledge Sources"
        KB --> DOC[Internal Documentation]
        KB --> DS[Datasheets]
        KB --> RD[Reference Designs]
        KB --> HC[Historical Cases]
    end
```

### Consultation Process

```mermaid
sequenceDiagram
    participant C as Customer
    participant F as FAE
    participant D as DXA
    participant K as Knowledge Base

    C->>F: Initiates design consultation
    activate F
    F->>D: Begins discovery conversation
    activate D
    D->>K: Query relevant docs
    K-->>D: Documentation
    loop Consultation
        C->>F: Describes requirements
        F->>D: Forwards technical details
        D->>K: Analyzes requirements
        K-->>D: Validation results
        D-->>F: Suggests questions/solutions
        F->>C: Presents recommendations
    end
    F->>D: Request final documentation
    D->>F: Generate design package
    F->>C: Deliver recommendations
    deactivate D
    deactivate F
```

### Flow

1. Customer initiates design consultation
2. FAE begins discovery conversation
   - DXA actively monitors discussion
   - DXA identifies key design parameters mentioned
3. FAE guides discussion while DXA:
   - Surfaces relevant documentation
   - Suggests technical questions to ask
   - Identifies potential design challenges
4. Customer describes design requirements
   - Operating conditions
   - Performance targets
   - System constraints
5. DXA analyzes requirements in real-time:
   - Validates parameter combinations
   - Flags potential issues
   - Suggests optimal configurations
6. FAE synthesizes DXA insights with expertise:
   - Presents design recommendations
   - Explains trade-offs
   - Provides application examples
7. Interactive problem-solving:
   - Customer asks follow-up questions
   - DXA provides real-time verification
   - FAE translates technical details
8. FAE and DXA collaborate on deliverables:
   - Design recommendations document
   - Reference circuit snippets
   - Parameter calculations
   - Best practices checklist

### Success Criteria

- Customer understands design recommendations
- All critical parameters addressed
- Design approach validated by DXA
- Clear action items documented
- Customer confident in implementation path
- Follow-up requirements identified

### DXA Performance Metrics

- Relevant documentation retrieval speed
- Accuracy of technical recommendations
- Issue prediction success rate
- Knowledge gap identification
- Response latency during live consultation

### Consultation States

```mermaid
stateDiagram-v2
    [*] --> Initial_Contact
    Initial_Contact --> Requirements_Gathering
    
    state Requirements_Gathering {
        [*] --> Collect_Params
        Collect_Params --> Validate_Params
        Validate_Params --> Issues_Found
        Issues_Found --> Collect_Params: Need More Info
        Issues_Found --> [*]: Parameters Valid
    }
    
    Requirements_Gathering --> Solution_Design
    
    state Solution_Design {
        [*] --> Generate_Options
        Generate_Options --> Review_Tradeoffs
        Review_Tradeoffs --> Customer_Feedback
        Customer_Feedback --> Generate_Options: Refinement Needed
        Customer_Feedback --> [*]: Solution Accepted
    }
    
    Solution_Design --> Documentation
    Documentation --> [*]
```

## Demo Script (3 minutes)

### Setup (30s)

- Customer consultation interface
- Split screen showing:
  - FAE video conference window
  - DXA analysis dashboard
  - Circuit design workspace
  - Technical documentation viewer

### Demo Flow

#### 0:00-0:30 - Initial Customer Engagement

- Show FAE starting customer consultation
- DXA actively monitoring discussion
- Display real-time parameter identification:
  - Operating conditions
  - Performance targets
  - System constraints
- Highlight automatic documentation retrieval

#### 0:30-1:30 - Technical Analysis

- Customer describes specific design challenge
- DXA performs multi-faceted analysis:
  - Parameter validation
  - Design rule checking
  - Reference design matching
  - Performance optimization
- Show real-time documentation synthesis
- Display design trade-off analysis

#### 1:30-2:30 - Solution Development

- DXA generates design recommendations
- Show interactive optimization process:
  - Parameter adjustment impacts
  - Performance predictions
  - Design margin analysis
- FAE explains trade-offs with DXA support
- Display reference circuit suggestions

#### 2:30-3:00 - Documentation & Follow-up

- Generate consultation summary
- Show automated documentation package:
  - Design recommendations
  - Parameter calculations
  - Reference circuits
  - Best practices checklist
- Highlight knowledge capture for future cases

### Interactive Elements

- Circuit parameter exploration
- Alternative design scenarios
- Documentation drill-down
- Design trade-off visualization

### Technical Requirements

#### Demo Environment

- Video conferencing system
- Circuit design tools
- DXA analysis interface
- Documentation system

#### Visualization Requirements

- Parameter correlation plots
- Design trade-off matrices
- Performance prediction graphs
- Documentation synthesis display
- Knowledge capture interface

#### Backup Plans

- Pre-recorded consultation scenarios
- Offline analysis results
- Sample design challenges
- Alternative solution paths
