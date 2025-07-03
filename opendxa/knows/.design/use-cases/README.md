# KNOWS CORRAL Simulations

This directory contains complete CORRAL lifecycle simulations for two use cases:

1. **Semiconductor Packaging Vision Alignment** - Setting up vision system calibration for non-standard fiducial patterns
2. **IC Design FAE Customer Support** - Supporting medical device customers with power management IC implementation

## Directory Structure

Each use case has its own directory with the following structure:

```
use-case-name/
├── corral_simulation.py      # Main simulation orchestrator
├── curate.py                 # Curate phase implementation
├── organize.py               # Organize phase implementation
├── retrieve.py               # Retrieve phase implementation
├── reason.py                 # Reason phase implementation
├── act.py                    # Act phase implementation
├── learn.py                  # Learn phase implementation
└── common/
    ├── knowledge_units.py    # Knowledge unit data structures
    └── storage_types.py      # Storage system implementations
```

## Running the Simulations

### Semiconductor Packaging Vision Alignment

```bash
cd semiconductor-packaging-vision-alignment
python corral_simulation.py
```

This simulation demonstrates:
- Vision system calibration for BGA packages with non-standard fiducial patterns
- Achieving ±0.1mm accuracy requirements
- High-Tg FR4 substrate material considerations
- Optimization techniques for unique requirements

### IC Design FAE Customer Support

```bash
cd ic-design-fae-customer-support
python corral_simulation.py
```

This simulation demonstrates:
- Power management IC implementation for medical devices
- FDA Class III medical device compliance
- Ultra-low power requirements for implantable devices
- Customer support workflow optimization

## CORRAL Phase Overview

Each simulation implements the complete CORRAL lifecycle:

1. **Curate** - Analyze use case requirements and generate knowledge content
2. **Organize** - Create knowledge units and store in appropriate systems
3. **Retrieve** - Select relevant knowledge for current task
4. **Reason** - Compose knowledge into actionable reasoning
5. **Act** - Execute task using composed knowledge
6. **Learn** - Analyze outcomes and update knowledge base

## Key Features Demonstrated

- **P-T Classification System** - Phase (Prior/Documentary/Experiential) + Type (Topical/Procedural)
- **Multi-Storage Architecture** - Relational, Semi-structured, Vector, and Time Series storage
- **Task-Driven Retrieval** - Intelligent knowledge selection based on current task
- **Structured Reasoning** - Composition of knowledge for actionable insights
- **Execution Simulation** - Realistic task execution with performance metrics
- **Continuous Learning** - Knowledge evolution through outcome analysis

## Expected Output

Each simulation will output:
- Detailed phase-by-phase execution
- Knowledge base statistics
- Performance metrics
- Learning outcomes
- Knowledge evolution summary

## Customization

To create new use cases:
1. Copy an existing use case directory
2. Modify the use case definition in `corral_simulation.py`
3. Update knowledge requirements in `curate.py`
4. Adjust retrieval logic in `retrieve.py`
5. Customize execution simulation in `act.py`

The simulations provide a foundation for understanding how KNOWS transforms knowledge-intensive processes into systematic, learning-based optimization systems. 