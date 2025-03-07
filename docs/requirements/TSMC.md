<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# Taiwan Semiconductor Manufacturing Company (TSMC) DXA Requirements

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/TSMC_Logo.svg/2560px-TSMC_Logo.svg.png" alt="TSMC Logo" width="50%" />
</p>

## Scenario Overview

This document outlines the requirements for the Domain Expert Agent (DXA) implementation with Taiwan Semiconductor Manufacturing Company (TSMC). The current implementation falls short of TSMC's original expectation for "a generic agentic solution that offers reasoning and troubleshooting capabilities, easily applicable to various tool models." The requirements are organized by priority to address critical gaps, significant functionality gaps, and necessary improvements.

## Strategic Priorities

### 1. High Priority - Critical Gaps (Value/Effort: 4.0-4.4)

```mermaid
graph TB
    subgraph "Core Framework Components"
        MCP[MCP Integration]
        AL[Agentic Loop]
        SK[Enhanced SemiKong]
    end
    
    subgraph "TSMC Systems"
        DS1[Data Source 1]
        DS2[Data Source 2]
        DS3[Data Source 3]
        Apps[TSMC Applications]
    end
    
    MCP --> DS1
    MCP --> DS2
    MCP --> DS3
    AL --> Apps
    SK --> Apps
```

#### Key Requirements:
- **MCP Implementation** (Value/Effort: 4.4)
  - Deliver DXA Framework with Message Communication Protocol
  - Develop comprehensive integration between DXA and MCP
  - Ensure seamless data flow between components
  - Create robust error handling and recovery mechanisms
  - Implement performance optimization for large-scale deployments

- **Agentic Loop Support** (Value/Effort: 4.0)
  - Ensure framework properly implements the "Agentic Loop"
  - Design and implement complete agentic loop architecture
  - Create monitoring and feedback mechanisms
  - Develop tools for visualizing and debugging the agentic loop
  - Implement performance metrics for loop efficiency

- **Enhanced SemiKong Performance** (Value/Effort: 0.8 → 3.5)
  - Improve LLM to outperform standard models in QA tasks with domain-specific knowledge
  - Implement domain adaptation techniques for TSMC-specific knowledge
  - Create comprehensive evaluation framework comparing to standard LLMs
  - Develop continuous improvement mechanisms
  - Integrate TSMC's domain knowledge into the model

### 2. Medium Priority - Significant Functionality Gaps (Value/Effort: 1.0-2.5)

```mermaid
graph TB
    subgraph "Advanced Capabilities"
        Extract[Advanced Extraction]
        Workflow[Workflow Generation]
        Anomaly[Anomaly Detection]
        Interview[Knowledge Interview]
    end
    
    subgraph "Data Sources"
        Images[Images/Charts]
        PDFs[PDF Documents]
        PPTs[Presentations]
        Sensors[IoT Sensors]
    end
    
    Extract --> Images
    Extract --> PDFs
    Extract --> PPTs
    Workflow --> Sensors
    Anomaly --> Sensors
```

#### Key Requirements:
- **Advanced Extraction Capabilities** (Value/Effort: 1.2 → 2.5)
  - Enable extraction from non-text formats (PPT/Image/PDF with charts)
  - Implement chart and diagram recognition
  - Develop PDF parsing with layout understanding
  - Create PowerPoint slide extraction capabilities
  - Build image analysis for technical diagrams and schematics

- **Workflow Generation** (Value/Effort: 1.3 → 2.3)
  - Expand beyond basic checking of sensors, maintenance, and parts lifetime data
  - Implement more sophisticated workflow patterns
  - Create workflow validation mechanisms
  - Develop workflow optimization capabilities
  - Enable complex multi-step troubleshooting workflows

- **Anomaly Detection** (Value/Effort: 1.0 → 2.0)
  - Implement independent anomaly detection without relying on external APIs
  - Develop multiple anomaly detection algorithms
  - Create visualization tools for detected anomalies
  - Implement feedback mechanism for false positives/negatives
  - Design self-learning capabilities for improved detection over time

- **Knowledge Interview Flexibility** (Value/Effort: 1.0 → 2.0)
  - Remove rigid fixed templates that can't be skipped
  - Redesign interview template to be more flexible
  - Implement skippable sections
  - Create customizable interview flows
  - Develop better UI/UX for interview process

### 3. Technical Improvements (Value/Effort: 1.4-1.7)

```mermaid
sequenceDiagram
    participant T as TSMC Data
    participant D as DXA Framework
    participant R as Release Pipeline
    
    T->>D: Provide Uncleaned Data
    D->>D: Process & Clean Data
    D->>D: Analyze Data
    D->>R: Implement Changes
    R->>R: Automated Testing
    R->>R: Integration Testing
    R->>T: Deploy Solution
```

#### Key Requirements:
- **Debug/Release Cycle** (Value/Effort: 1.7)
  - Reduce the "excessively long" cycle and high integration effort with actual data
  - Streamline development and release processes
  - Implement automated testing frameworks
  - Create efficient debugging tools
  - Design incremental release strategy
  - Develop better integration testing with actual data
  - Target milestone: Release 2 date: 2025/02/24 Beta w/ stopping bugs

- **Data Handling** (Value/Effort: 1.5)
  - Improve performance with uncleaned actual data
  - Develop robust data cleaning pipelines
  - Implement data validation mechanisms
  - Create data quality assessment tools
  - Design fallback mechanisms for poor quality data

- **Data Source Connectivity** (Value/Effort: 1.4)
  - Enable connection with any kind of data source inside TSMC
  - Develop universal connector framework
  - Implement adapters for common TSMC data sources
  - Create data transformation pipeline
  - Design secure authentication mechanisms
  - Implement data validation and quality checks

### 4. Process Improvements (Value/Effort: 1.4-2.6)

```mermaid
graph LR
    A[Aitomatic] <--> B[TSMC]
    A --> C[Framework Development]
    A --> D[Knowledge Transfer]
    B --> E[Use Case Definition]
    B --> F[Domain Expertise]
    C --> G[Joint Development]
    D --> G
    E --> G
    F --> G
```

#### Key Requirements:
- **Collaborative Effectiveness** (Value/Effort: 2.6)
  - Make collaboration more effective
  - Establish regular communication channels and cadence
  - Create shared project management tools and processes
  - Develop clear roles and responsibilities
  - Implement feedback mechanisms for continuous improvement

- **Knowledge Extraction** (Value/Effort: 1.4)
  - Better extraction of workflows from existing TSMC documents
  - Develop document processing pipeline
  - Create knowledge extraction algorithms
  - Implement workflow identification and extraction
  - Design knowledge validation mechanisms
  - Create knowledge organization system

- **Packaging** (Value/Effort: 1.6)
  - Create better packaging with smooth experience for using and updating
  - Design intuitive packaging system for DXA components
  - Create streamlined installation process
  - Develop comprehensive documentation
  - Implement version control and dependency management
  - Design update and rollback mechanisms

### 5. Core Framework Delivery (Value/Effort: 1.2-1.3)

```mermaid
graph TB
    subgraph "DXA Framework"
        Core[Core Components]
        KB[Knowledge Base]
        UC[Use Case Implementations]
    end
    
    subgraph "6NOs Resolution"
        NO1[No.1]
        NO2[No.2]
        NO3[No.3]
        NO4[No.4]
        NO5[No.5]
        NO6[No.6]
    end
    
    Core --> NO1
    Core --> NO2
    Core --> NO3
    KB --> NO4
    KB --> NO5
    UC --> NO6
```

#### Key Requirements:
- **Deliver the framework to resolve the 6NOs with priorities agreed** (Value/Effort: 1.3)
  - Implement solutions for each of the 6NOs
  - Create prioritization framework
  - Develop tracking system for resolution progress
  - Design validation mechanisms for solutions

- **Framework that works for the usecase** (Value/Effort: 1.2)
  - Develop use case specific implementations
  - Create customization capabilities
  - Implement performance optimizations for specific use cases
  - Design validation framework for use case success

- **Deliver Workable DXA that solves TSMC problem** (Value/Effort: 1.2)
  - Implement problem-specific solutions
  - Create validation mechanisms
  - Develop performance metrics
  - Design feedback and improvement system

- **Deliver the DXA Framework as a core of Agent** (Value/Effort: 1.3)
  - Develop modular architecture for easy extension
  - Create comprehensive API documentation
  - Implement reference implementations for common patterns
  - Design flexible configuration system

## Implementation Timeline

```mermaid
gantt
    title TSMC DXA Implementation Timeline
    dateFormat  YYYY-MM-DD
    section Critical Gaps
    MCP implementation :2024-03-01, 90d
    Agentic loop implementation :2024-03-15, 75d
    SemiKong enhancement :2024-04-01, 90d
    section Functionality Gaps
    Advanced extraction :2024-04-15, 75d
    Workflow generation :2024-05-01, 60d
    Anomaly detection :2024-05-15, 60d
    Knowledge interview redesign :2024-04-01, 45d
    section Technical Improvements
    Debug/release cycle optimization :2024-03-15, 60d
    Data handling improvements :2024-04-15, 60d
    Data source connectivity :2024-05-01, 75d
    section Process Improvements
    Collaboration framework :2024-03-01, 30d
    Knowledge extraction :2024-04-01, 60d
    Packaging improvements :2024-06-01, 45d
    section Core Delivery
    6NOs resolution :2024-03-15, 120d
    Use case implementations :2024-04-15, 90d
    section Releases
    Alpha release :milestone, 2024-07-15, 0d
    Beta testing :2024-07-15, 60d
    Bug fixing :2024-08-15, 30d
    Release 2 :milestone, 2025-02-24, 0d
```

## Success Metrics

### Critical Gap Resolution
- MCP successfully integrated with DXA Framework
- Agentic Loop implemented and validated against TSMC requirements
- SemiKong demonstrably outperforms standard LLMs on TSMC-specific tasks

### Functionality Gap Closure
- Successful extraction from multiple non-text formats demonstrated
- Complex workflow generation capabilities validated
- Independent anomaly detection implemented and verified
- Knowledge interview system redesigned with positive user feedback

### Technical Improvement Validation
- Debug/release cycle time reduced by at least 50%
- Successful handling of uncleaned TSMC data demonstrated
- Connection to all required TSMC data sources validated

### Process Improvement Metrics
- Collaboration effectiveness metrics show positive trend
- Knowledge extraction from TSMC documents validated
- Packaging system receives positive user feedback

### Core Delivery Validation
- All 6NOs addressed according to agreed priorities
- Use case implementations meet success criteria
- Framework successfully solves TSMC's specific problems
- Framework architecture validated as extensible and modular 