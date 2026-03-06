# Physical Ontology Agent

A STAR agent specialized for extracting physical ontologies from building diagrams, floor plans, and HVAC schematics.

## Overview

This agent demonstrates Dana's **skill-based architecture** where agents extend their capabilities through composable task templates (skills). The agent uses AI vision to extract equipment, relationships, and spatial hierarchies from technical drawings.

## Architecture

```
PhysicalOntologyAgent (STARAgent)
├── Resources
│   ├── SkillResource       # Discovers and invokes skills
│   ├── BashResource        # Executes skill scripts
│   ├── FileIOResource      # Read/write files
│   ├── FileEditResource    # Edit files
│   └── SearchResource      # Search codebase
│
└── Skills (.dana/skills/)
    ├── extract-image/      # Vision-based extraction (fork mode)
    │   ├── SKILL.md        # Skill instructions
    │   └── scripts/        # Python extraction scripts
    │
    └── ontology/           # Schema management (main mode)
        ├── SKILL.md        # CLI documentation
        └── scripts/        # Ontology CLI tools
```

## Skills Concept in Dana

Skills are **reusable task templates** defined in `SKILL.md` files with YAML frontmatter:

```yaml
---
name: extract-image
description: Extract content from images using AI vision
context: fork           # main | fork
allowed-tools: bash:*, file-io:read, file-io:write
---

# Skill Instructions
Detailed instructions the agent follows when skill is invoked...
```

### Context Modes

| Mode | Behavior | Use When |
|------|----------|----------|
| `main` | Instructions returned to current conversation | Short tasks, need follow-up |
| `fork` | Isolated subagent executes, only result returns | Long tasks, complex workflows |

### Tool Restrictions

Skills can whitelist which tools the agent may use:
- `bash:*` - All bash operations
- `file-io:read` - Only file reading
- `*:read` - Read on any resource

## Quick Start

```python
from examples.agents.physical_ontology_agent.agent import PhysicalOntologyAgent

agent = PhysicalOntologyAgent(
    llm_provider="anthropic",
    model="claude-sonnet-4-20250514"
)

result = agent.converse(
    initial_message="Extract equipment from /path/to/floor_plan.png"
)
```

## Workflow

1. **Image Extraction** - `extract-image` skill analyzes diagrams iteratively
2. **Schema Validation** - `ontology` skill validates asset types against TTL schema
3. **Instance Creation** - CLI tools create validated YAML instances
4. **Relationship Mapping** - Equipment connections established with proper semantics

## Output

The agent produces structured data:
- **Equipment inventory** with IDs, types, locations
- **Relationships** (supplies, is_part_of, is_connected_to, etc.)
- **Spatial hierarchy** (rooms, zones, floors)

See `extraction.md` for example output format.
