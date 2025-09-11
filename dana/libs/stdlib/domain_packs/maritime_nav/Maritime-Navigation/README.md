# Maritime Navigation Collision Avoidance Decision System

## Overview

An intelligent expert agent system for performing collision avoidance analysis and providing specific navigation recommendations for vessels at sea. The system uses hierarchical vessel analysis, situational assessment, and historical incident correlation to provide evidence-based collision avoidance decisions.

## System Architecture

### Core Components

- **Navigation Expert Agent**: Main collision avoidance analysis engine with specialized expertise
- **Vessel Identification**: Expertise module for vessel capability assessment
- **Collision Analysis**: Expertise module for risk assessment and decision recommendation

### Knowledge Resources

The system uses five key knowledge databases that directly correspond to maritime navigation requirements:

1. **`vessel_registry.txt`** - Vessel specifications and capabilities
   - Vessel type, size, maneuverability ratings
   - Right of way classifications
   - Stopping distances and turning radii

2. **`navigation_rules.txt`** - Navigation calculations and rules
   - Collision risk assessment criteria
   - Safe passing distances
   - Relative motion calculations

3. **`environmental_data.txt`** - Environmental conditions database
   - Weather, sea state, visibility conditions
   - Wind, current, and seasonal variations
   - Risk assessment matrix

4. **`colregs_database.txt`** - International collision regulations
   - COLREGS rules and requirements
   - Right of way hierarchy
   - Communication and signal requirements

5. **`historical_incidents.txt`** - Past collision avoidance scenarios
   - Documented historical incidents with outcomes
   - Success patterns by vessel type and scenario
   - Recommended actions and failure analysis

## Usage

### Running the System

```bash
./run-maritime-navigation
```

### Input Format

The system takes vessel encounter parameters directly:

- Vessel A ID and B ID
- Positions, courses, and speeds for both vessels
- System automatically analyzes the situation

### Output

The system generates comprehensive collision avoidance recommendations in `.output/navigation-recommendation.txt` including:

- Vessel capability assessment
- Situation analysis and risk assessment
- Environmental and regulatory context
- Specific course and speed recommendations

## Supported Vessel Types

- **Container Ships**: MV Navigator, MV CargoStar
- **Bulk Carriers**: MV CargoStar, MV TankerPro
- **Oil Tankers**: MV TankerPro
- **Fishing Vessels**: MV FishingBoat
- **Pilot Vessels**: MV PilotBoat
- **Pleasure Craft**: MV Yacht

## Analysis Workflow

The system follows a structured 4-step analysis process:

1. **Vessel Identification & Capability Assessment** - Maps vessel IDs to specifications and capabilities
2. **Current Situation Analysis** - Analyzes relative motion and collision risk
3. **Environmental & Regulatory Context** - Assesses conditions and regulatory requirements
4. **Historical Pattern Correlation & Decision Recommendation** - Searches for similar scenarios and provides specific recommendations

## Example Analysis

The system can handle various collision avoidance scenarios:

- Head-on encounters
- Crossing situations
- Overtaking scenarios
- Restricted visibility conditions
- High traffic density situations

Each analysis provides evidence-based recommendations with clear course and speed actions for the user's vessel.

## Key Features

### **Hierarchical Vessel Analysis**

- Navigates through vessel specifications, capabilities, and limitations
- Provides clear audit trail from vessel identification to collision avoidance decisions
- Enables evidence-based decision making

### **Intelligent Collision Avoidance**

- Combines vessel characteristics with situational data
- Searches historical databases for similar scenarios
- Applies maritime expertise to generate specific recommendations
- Provides clear course and speed actions

### **Comprehensive Reporting**

- Generates structured recommendations with step-by-step analysis
- Includes specific navigation commands and supporting evidence
- Outputs both individual step results and final comprehensive recommendations

## Business Value

This system provides significant value by:

- **Reducing Decision Time**: From minutes to seconds for collision avoidance decisions
- **Improving Safety**: High confidence in recommended actions with supporting evidence
- **Enhancing Compliance**: Clear regulatory compliance verification
- **Supporting Navigation**: Evidence-based course and speed recommendations

## Technical Implementation

### **Dana Language Features Demonstrated**

- Expert Agent Architecture with multiple expertise modules
- Multi-Resource Management with specialized knowledge bases
- Structured Problem-Solving with clear step-by-step analysis
- Resource Query & Synthesis for comprehensive analysis
- Template-Based Workflow System for consistent execution

### **File Structure**

- **`.input/`**: Contains example navigation scenarios
- **`.output/`**: Stores analysis results and recommendations
- **`expertise/`**: Contains specialized workflow modules
- **`resources/`**: Houses the knowledge databases
- **`utils.na`**: Contains analysis templates and workflows

## Conclusion

The Maritime Navigation Collision Avoidance system successfully demonstrates Dana's capabilities for complex domain-specific problem-solving in maritime navigation. The 4-step analysis process successfully generates actionable navigation commands from vessel encounter data to specific course and speed recommendations.
