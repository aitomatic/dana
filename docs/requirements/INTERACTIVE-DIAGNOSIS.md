<!-- markdownlint-disable MD041 -->
<!-- markdownlint-disable MD033 -->
<p align="center">
  <img src="https://cdn.prod.website-files.com/62a10970901ba826988ed5aa/62d942adcae82825089dabdb_aitomatic-logo-black.png" alt="Aitomatic Logo" width="400" style="border: 2px solid #666; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);"/>
</p>

# FAE Customer Device Troubleshooting Scenario

This scenario describes how a Field Application Engineer (FAE), supported by a Domain Expert Agent (DXA), assists customers in troubleshooting device issues through technical consultation and documentation.


## Device Troubleshooting Consultation

**Actor:** Field Application Engineer (FAE) + Troubleshooting Expert DXA  
**Goal:** Guide customer to successfully resolve device issues using company's expertise

### Context

- Customer (device/system user) seeks troubleshooting guidance
- FAE leads customer interaction via call/web meeting
- DXA has access to:
  - Internal troubleshooting documentation and application notes
  - Public datasheets and troubleshooting guides
  - Historical troubleshooting consultations
  - Device troubleshooting expertise knowledge base

<p align="center">
  <img src="https://cdn.shopify.com/s/files/1/0217/1112/6600/files/banner-plc-troubleshooting-guide_1.jpg?v=1672758990" alt="" width="50%" />
</p>

### System Architecture

```mermaid
stateDiagram-v2
    [*] --> Initial_Contact
    Initial_Contact --> Problem_Analysis

    state Problem_Analysis {
        [*] --> Information_Gathering
        Information_Gathering --> Document_Retrieval
        Document_Retrieval --> Analysis_Output
        Analysis_Output --> [*]: Analysis Complete
    }

    Problem_Analysis --> Plan_Generation

    state Plan_Generation {
        [*] --> Generate_Initial_Plan
        Generate_Initial_Plan --> Parse_Steps
        Parse_Steps --> Validate_Plan
        Validate_Plan --> Generate_Initial_Plan: Plan Not Valid
        Validate_Plan --> [*]: Plan Validated
    }

    Plan_Generation --> Plan_Execution

    state Plan_Execution {
        [*] --> Execute_Step
        Execute_Step --> Step_Validation
        Step_Validation --> Adjust_Step: Previous Steps Exist
        Adjust_Step --> Execute_Step
        Step_Validation --> Add_Step: Need Additional Step
        Add_Step --> Execute_Step
        Step_Validation --> [*]: Steps Complete
    }

    Plan_Execution --> Solution_Validation

    state Solution_Validation {
        [*] --> Check_Completion
        Check_Completion --> Generate_New_Plan: Not Complete
        Generate_New_Plan --> Plan_Generation
        Check_Completion --> Final_Answer: Complete
        Final_Answer --> [*]
    }

    Solution_Validation --> Documentation_Generation
    
    state Documentation_Generation {
        [*] --> Generate_Final_Report
        Generate_Final_Report --> Compile_Steps
        Compile_Steps --> Format_Output
        Format_Output --> [*]
    }

    Documentation_Generation --> [*]
```

### Consultation Process

```mermaid
sequenceDiagram
    participant C as Customer
    participant F as FAE
    participant D as DXA
    participant K as Knowledge Base
    
    C->>F: Initiates troubleshooting request
    activate F
    F->>D: Forward request to DXA
    activate D
    
    rect rgb(200, 220, 240)
        Note right of D: Initial Analysis Phase
        D->>K: analyze_problem_for_gathering_data
        K-->>D: Return relevant docs
        D->>K: select_information_for_analysis
        K-->>D: Analysis information
    end

    rect rgb(220, 240, 200)
        Note right of D: Plan Generation
        D->>D: generate_plan
        D->>K: Query for plan validation
        K-->>D: Validation info
        D->>D: parse_steps
    end

    loop Plan Execution
        D->>D: execute_step
        D->>K: Query knowledge base
        K-->>D: Retrieved information
        D->>F: Request user input if needed
        F->>C: Ask for information
        C-->>F: Provide information
        F-->>D: Forward user input
        D->>D: validate_step
        alt Step Needs Adjustment
            D->>D: adjust_step
        else Need Additional Step
            D->>D: add_step
        end
    end

    D->>D: Check solution completion
    alt Solution Complete
        D->>D: Generate final answer
    else Need New Plan
        D->>D: Regenerate plan
    end

    D->>F: Provide final solution
    F->>C: Present recommendations
    deactivate D
    deactivate F
```

### Flow



#### Customer Initiates Request

Submits troubleshooting request through FAE
Provides initial problem description


#### DXA Performs Initial Analysis

Gathers information from knowledge base
Retrieves relevant documentation
Processes initial problem statement
Analyzes document relevancy for the case


#### DXA Generates Action Plan

Creates structured troubleshooting steps
Validates plan feasibility
Ensures steps are executable
Sets expected outputs for each step


#### FAE and DXA Execute Plan

Processes each step sequentially
Validates step outputs
Adjusts steps based on previous results
Adds new steps if needed


#### Interactive Information Gathering

FAE requests specific information from customer
Customer provides required details
DXA validates user inputs
Adjusts analysis based on new information


#### Solution Development

DXA processes accumulated information
Validates solution completeness
Regenerates plan if needed
Confirms solution viability


#### Documentation Generation

Compiles step results
Formats final output
Generates recommendations
Creates comprehensive report


#### Solution Delivery

FAE presents final recommendations
Reviews implementation steps
Ensures customer understanding
Documents follow-up items



#### Success Criteria

All execution steps completed successfully
Solution validated by DXA
Clear documentation generated
Required user inputs obtained
Plan execution completed within threshold attempts
Solution matches original request requirements

#### DXA Performance Metrics

Number of plan regeneration attempts
Step execution success rate
Document retrieval accuracy
Information gathering efficiency
Plan validation success rate
Response time for each step
Solution completion time

#### System Constraints

Maximum step limit (MAX_STEP);
Plan regeneration threshold;
Question matching threshold;
Document retrieval limits;
Execution timeout parameters.


## Demo Flow

### 0:00-0:30 - Initial Problem Analysis
- FAE receives customer troubleshooting request
- DXA begins information gathering:
  - Real-time document retrieval
  - Context analysis activation
  - Knowledge base querying
- Display automatic parameter extraction:
  - Device configurations
  - Error conditions
  - System status

### 0:30-1:30 - Troubleshooting Process
- Customer describes device issues
- DXA executes analysis pipeline:
  - Problem decomposition
  - Step validation
  - Plan generation and parsing
  - Solution path identification
- Show dynamic plan adjustment:
  - Step refinement
  - Execution validation
  - Knowledge base correlation

### 1:30-2:30 - Interactive Resolution
- DXA generates solution recommendations:
  - Step-by-step execution
  - Real-time validation
  - Plan adjustment based on feedback
- Demonstrate adaptive workflow:
  - Information request handling
  - User input processing
  - Solution verification
- Display solution optimization

### 2:30-3:00 - Documentation Generation
- Generate final solution package:
  - Troubleshooting steps taken
  - Validation results
  - Recommended actions
  - Best practices applied
- Show automated report compilation

## Interactive Features
- Real-time plan adjustment
- Dynamic step validation
- Information request handling
- Solution verification workflow

## Technical Requirements

### Demo Environment
- Troubleshooting console interface
- DXA analysis system
- Knowledge base integration
- Real-time reporting system

### Visualization Components
- Problem analysis dashboard
- Step execution monitor
- Documentation generation preview
- Solution validation display

### Backup Scenarios
- Pre-configured test cases
- Offline troubleshooting workflows
- Sample device issues
- Alternative solution paths

## Error Handling
- Plan regeneration demonstration
- Step adjustment scenarios
- Invalid input recovery
- Threshold management examples

## Key Highlights
- Real-time document retrieval
- Dynamic plan generation
- Interactive step execution
- Automated solution validation
- Comprehensive documentation
