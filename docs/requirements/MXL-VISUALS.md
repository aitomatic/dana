# FAE Customer Device Troubleshooting Scenario

This scenario describes how a Field Application Engineer (FAE), supported by a Domain Expert Agent (DXA), assists customers in troubleshooting device issues through technical consultation and documentation.

## Device Troubleshooting Consultation

**Actors:** Field Application Engineer (FAE) + Troubleshooting Expert DXA + Customer  
**Goal:** Guide customer to successfully resolve device issues using company's expertise

## Context

Customer (device/system user) seeks troubleshooting guidance  
FAE leads customer interaction via call/web meeting

DXA has access to:
* Internal troubleshooting documentation and application notes
* Public datasheets and troubleshooting guides
* Historical troubleshooting consultations
* Device troubleshooting expertise knowledge base
* Visual knowledge base with analyzed images and diagnostics

## System Architecture

### Consultation Process Flow

#### Customer Initiates Request
* Submits troubleshooting request through FAE
* Provides initial problem description
* Uploads relevant images if available

#### DXA Performs Initial Analysis
* Gathers information from knowledge base
* Retrieves relevant documentation
* Analyzes and compares uploaded images with training dataset
* Extracts relevant visual information from knowledge base
* Processes initial problem statement
* Analyzes document relevancy for the case

#### DXA Generates Action Plan
* Creates structured troubleshooting steps
* Incorporates visual analysis and comparison results
* Validates plan feasibility
* Ensures steps are executable
* Sets expected outputs for each step

#### FAE and DXA Execute Plan
* Processes each step sequentially
* References relevant images from knowledge base
* Validates step outputs
* Adjusts steps based on previous results
* Adds new steps if needed

#### Interactive Information Gathering
* FAE requests specific information from customer
* Requests specific images or visual confirmation when needed
* Customer provides required details
* DXA validates user inputs
* Processes and analyzes new images
* Adjusts analysis based on new information

#### Solution Development
* DXA processes accumulated information
* Integrates visual analysis results
* Validates solution completeness
* Regenerates plan if needed
* Confirms solution viability

#### Documentation Generation
* Compiles step results
* Includes relevant analyzed images and visual comparisons
* Formats final output
* Generates recommendations
* Creates comprehensive report

## DXA Performance Metrics
* Number of plan regeneration attempts
* Step execution success rate
* Document retrieval accuracy
* Image analysis accuracy
* Information gathering efficiency
* Plan validation success rate
* Response time for each step
* Solution completion time

## System Constraints
* Maximum step limit (MAX_STEP)
* Plan regeneration threshold
* Question matching threshold
* Document retrieval limits
* Image processing limits
* Execution timeout parameters

## Interactive Features
* Real-time plan adjustment
* Dynamic step validation
* Information request handling
* Solution verification workflow

## Technical Requirements

### Demo Environment
* Troubleshooting console interface
* Image processing and analysis system
* Knowledge base integration
* Real-time reporting system

### Visualization Components
* Problem analysis dashboard
* Step execution monitor
* Documentation generation preview
* Solution validation display
* Visual knowledge base browser
* Backup Scenarios
