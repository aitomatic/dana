# Maritime Navigation Domain Pack

> __AUTHORS__
> William Nguyen (william@aitomatic.com)
> Vinh Luong (vinh@aitomatic.com)

A comprehensive Dana domain pack for maritime navigation, collision avoidance, and vessel management using expert agent systems and COLREGS compliance.

## Overview

This domain pack provides intelligent maritime navigation capabilities through Dana's expert agent architecture. It includes collision avoidance analysis, vessel identification, environmental assessment, and regulatory compliance checking based on international maritime regulations (COLREGS).

## Features

### 🚢 **Core Navigation Capabilities**

- **Collision Avoidance Analysis**: Intelligent risk assessment and decision recommendations
- **Vessel Identification**: Comprehensive vessel capability assessment and classification
- **COLREGS Compliance**: International collision regulations implementation
- **Environmental Analysis**: Weather, sea state, and visibility condition assessment
- **Historical Pattern Matching**: Learning from past incidents and successful scenarios

### 🧠 **Expert Agent Architecture**

- **Hierarchical Analysis**: Multi-step decision process with clear audit trails
- **Resource Integration**: Combines multiple knowledge databases for comprehensive analysis
- **Evidence-Based Decisions**: All recommendations backed by regulatory and historical data
- **Structured Workflows**: Consistent, repeatable analysis processes

## Installation

### Prerequisites

- Python 3.12+
- Dana Framework 0.5.5.dev2+

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd maritime_nav

# Install dependencies using UV
uv sync

# Or using pip
pip install -e .
```

## Quick Start

### Running the Maritime Navigation System

```bash
# Unix/Linux/macOS
./Maritime-Navigation/run-maritime-navigation

# Windows
Maritime-Navigation\run-maritime-navigation.bat
```

### Basic Usage

The system analyzes vessel encounters and provides collision avoidance recommendations:

1. **Input**: Vessel positions, courses, speeds, and environmental conditions
2. **Analysis**: 4-step hierarchical analysis process
3. **Output**: Specific course and speed recommendations with supporting evidence

## Architecture

### Core Components

```
maritime_nav/
├── Maritime-Navigation/           # Main application directory
│   ├── maritime_navigation.na     # Core navigation module
│   ├── utils.na                   # Utility functions and templates
│   ├── expertise/                 # Specialized expertise modules
│   │   ├── collision_analysis.na  # COLREGS compliance and risk assessment
│   │   └── vessel_identification.na # Vessel capability analysis
│   ├── resources/                 # Knowledge databases
│   │   ├── colregs_database.txt   # International collision regulations
│   │   ├── vessel_registry.txt    # Vessel specifications and capabilities
│   │   ├── environmental_data.txt # Weather and sea conditions
│   │   ├── navigation_rules.txt   # Navigation calculations and rules
│   │   └── historical_incidents.txt # Past scenarios and outcomes
│   ├── tests/                     # Test suite
│   ├── .input/                    # Example scenarios
│   └── run-maritime-navigation*   # Execution scripts
├── colreg.na                      # COLREGS rule definitions
├── rel_motion.na                  # Relative motion calculations
└── pyproject.toml                 # Project configuration
```

### Knowledge Resources

The system leverages five specialized knowledge databases:

1. **Vessel Registry** (`vessel_registry.txt`)
   - Vessel specifications, maneuverability ratings
   - Right of way classifications
   - Stopping distances and turning radii

2. **COLREGS Database** (`colregs_database.txt`)
   - International collision regulations
   - Right of way hierarchy
   - Communication and signal requirements

3. **Environmental Data** (`environmental_data.txt`)
   - Weather conditions and sea states
   - Visibility and seasonal variations
   - Risk assessment matrices

4. **Navigation Rules** (`navigation_rules.txt`)
   - Collision risk assessment criteria
   - Safe passing distances
   - Relative motion calculations

5. **Historical Incidents** (`historical_incidents.txt`)
   - Documented collision scenarios
   - Success patterns and failure analysis
   - Recommended actions by vessel type

## Analysis Workflow

The system follows a structured 4-step analysis process:

### 1. **Vessel Identification & Capability Assessment**

- Maps vessel IDs to specifications and capabilities
- Assesses maneuverability and right of way status
- Determines operational limitations

### 2. **Current Situation Analysis**

- Analyzes relative motion and collision risk
- Calculates closest point of approach (CPA)
- Assesses time to closest point of approach (TCPA)

### 3. **Environmental & Regulatory Context**

- Evaluates weather and sea conditions
- Applies COLREGS rules and requirements
- Considers traffic density and visibility

### 4. **Historical Pattern Correlation & Decision Recommendation**

- Searches for similar historical scenarios
- Provides evidence-based recommendations
- Generates specific course and speed actions

## Supported Vessel Types

- **Container Ships**: MV Navigator, MV CargoStar
- **Bulk Carriers**: MV CargoStar, MV TankerPro
- **Oil Tankers**: MV TankerPro
- **Fishing Vessels**: MV FishingBoat
- **Pilot Vessels**: MV PilotBoat
- **Pleasure Craft**: MV Yacht

## Example Scenarios

The system handles various collision avoidance scenarios:

- **Head-on Encounters**: Rule 14 compliance and course alterations
- **Crossing Situations**: Rule 15 right of way and safe passing
- **Overtaking Scenarios**: Rule 13 requirements and safe distances
- **Restricted Visibility**: Rule 19 procedures and sound signals
- **High Traffic Density**: Traffic separation schemes and coordination

## Output Format

The system generates comprehensive recommendations in `.output/navigation-recommendation.txt`:

```
VESSEL CAPABILITY ASSESSMENT:
- Vessel A: [Type, Size, Maneuverability]
- Vessel B: [Type, Size, Maneuverability]

SITUATION ANALYSIS:
- Relative Motion: [Bearing, Speed, CPA, TCPA]
- Risk Level: [Low/Medium/High]
- COLREGS Rule: [Applicable Rule]

RECOMMENDATION:
- Action: [Course alteration, Speed change, or Stand-on]
- Course: [New heading in degrees]
- Speed: [New speed in knots]
- Rationale: [Supporting evidence and reasoning]
```

## Testing

Run the test suite to validate functionality:

```bash
# Run Dana tests
dana test Maritime-Navigation/tests/

# Run Python import tests
python Maritime-Navigation/test_import.py
```

## Development

### Building the Project

```bash
# Using Make
make build

# Using UV
uv build
```

### Adding New Vessel Types

1. Update `vessel_registry.txt` with vessel specifications
2. Add test scenarios in `.input/` directory
3. Update documentation and run tests

### Extending Knowledge Bases

1. Add new data to appropriate resource files
2. Update analysis logic in expertise modules
3. Test with new scenarios

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is part of the Dana Framework and follows the same licensing terms.

## Support

For questions and support:

- Check the [USAGE.md](Maritime-Navigation/USAGE.md) for detailed documentation
- Review example scenarios in the `.input/` directory
- Examine the test suite for usage patterns

## Business Value

This domain pack provides significant value by:

- **Reducing Decision Time**: From minutes to seconds for collision avoidance decisions
- **Improving Safety**: High confidence recommendations with supporting evidence
- **Enhancing Compliance**: Clear regulatory compliance verification
- **Supporting Navigation**: Evidence-based course and speed recommendations
- **Learning from History**: Incorporates lessons from past incidents

---

*Built with Dana Framework - Intelligent Expert Agent Systems for Maritime Navigation*
