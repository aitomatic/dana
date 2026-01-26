# Agent with Skills Example

A minimal example showing how to create Dana agents with custom skills.

## Quick Start

```bash
cd examples/agents/agent_with_skills
python -m agent.sample_agent_with_skills
```

## Create Your Own Agent

### 1. Create Agent Class

```python
from dana.core.agent.star_agent import STARAgent
from dana.core.skills.dana_skills import SkillLoader, DanaSkillResource
from dana.core.resource.bash import BashResource
from pathlib import Path

class MyAgent(STARAgent):
    def __init__(self, llm_provider: str, model: str, **kwargs):
        super().__init__(
            agent_type="my-agent",
            agent_id="my-agent-001",
            llm_provider=llm_provider,
            model=model,
            **kwargs,
        )

        # Load skills from .dana/skills/
        skill_dirs = [Path(__file__).parent.parent / ".dana" / "skills"]
        skill_loader = SkillLoader(skill_dirs=skill_dirs)

        # Register resources - pass agent=self to enable fork mode
        self.with_resources(
            DanaSkillResource(skill_loader=skill_loader, agent=self),
            BashResource(),
            # Add other resources your skills need
        )
```

### 2. Create Skill Structure

```
your_agent/
├── .dana/
│   └── skills/
│       └── my-skill/
│           ├── SKILL.md      # Skill definition
│           └── scripts/      # Optional helper scripts
│               └── helper.py
└── agent/
    └── my_agent.py
```

### 3. Write SKILL.md

```yaml
---
name: my-skill
description: Brief description (shown to LLM for invocation)
context: main          # or "fork" for isolated execution
allowed-tools: bash:*  # Tools the skill can use
---

# My Skill

Instructions for the agent when this skill is invoked.
```

## SKILL.md Reference

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique skill identifier |
| `description` | Yes | Brief description for LLM to decide when to invoke |
| `context` | No | `main` (default) or `fork` |
| `allowed-tools` | No | Comma-separated tool patterns (e.g., `bash:*, file-io:read`) |

### Context Modes

- **main**: Skill runs in current conversation. Use for quick, interactive tasks.
- **fork**: Skill runs in isolated subagent. Use for complex multi-step tasks where you don't want to pollute main context.

## Included Skills

- **web-search-openai**: Web search using OpenAI's API (main mode)
- **extract-image**: Multi-pass image extraction using vision AI (fork mode)
