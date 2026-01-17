# Claude Skills Integration (Claude Code Subprocess)

## Cognitive Ontology Context

This feature is part of Dana's **Cognitive Ontology** vision - a living knowledge graph that captures not just what an enterprise knows, but how things connect and what capabilities are available.

### Skills as Ontological Elements

In the Cognitive Ontology framework, **Skills** are reusable, composable capabilities that define what an agent can do. They are ontological elements that can be:

- **Discovered**: Automatically found from skill directories
- **Composed**: Combined to create domain-specific agents
- **Filtered**: Narrowed to relevant capabilities for specialized agents
- **Learned**: Refined through the COSTAR Reflect phase (future)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     ENTERPRISE COGNITIVE ONTOLOGY                           │
│                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────┐   │
│   │                        SKILL POOL                                   │   │
│   │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌─────────────┐ ┌───────────┐  │   │
│   │  │ pptx │ │ xlsx │ │ docx │ │ pdf  │ │ domain-     │ │ enterprise│  │   │
│   │  │      │ │      │ │      │ │      │ │ specific    │ │ custom    │  │   │
│   │  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──────┬──────┘ └─────┬─────┘  │   │
│   └─────┼────────┼────────┼────────┼────────────┼───────────────┼───────┘   │
│         │        │        │        │            │               │           │
│         ▼        ▼        ▼        ▼            ▼               ▼           │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐     │
│   │ General Agent   │  │ Doc Specialist  │  │ Domain Agent            │     │
│   │ (all skills)    │  │ (filtered)      │  │ (domain skills)         │     │
│   └─────────────────┘  └─────────────────┘  └─────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Skills are Resources**: Skills are implemented as resources using the existing `with_resources()` pattern. No new abstraction needed.

2. **Greedy Default**: By default, agents discover and expose ALL available skills from `~/.claude/skills/`.

3. **Specialized Agents via Filtering**: Domain-specific agents are created by filtering to relevant skills.

4. **Future: Learned Capabilities**: Through COSTAR's Reflect phase, skill capabilities can be refined based on outcomes (not in MVP).

### Agent Specialization Pattern

```python
# General agent - discovers ALL skills (greedy default)
general_agent = STARAgent(agent_type="general")
# Automatically has ClaudeCodeSkills with all discovered skills

# Document specialist - filtered to document skills only
doc_agent = STARAgent(agent_type="document-specialist", enable_skills=False)
doc_agent.with_resources(ClaudeCodeSkills(skills=["pptx", "docx", "pdf"]))

# Domain agent - custom skill resources
fab_agent = STARAgent(agent_type="fab-analyst", enable_skills=False)
fab_agent.with_resources(
    DefectClassifierSkill(),
    YieldAnalyzerSkill(),
)
```

---

## Problem Statement

STARAgent currently has no mechanism to leverage Claude Skills - packaged instructions and scripts that extend Claude's capabilities for document generation (pptx, xlsx, docx, pdf) and other specialized tasks.

Additionally, STARAgent's LLM has no visibility into what skills are actually available, making it unable to make informed decisions about when to delegate to Claude Code.

Claude Code CLI supports local skill execution with the user's Claude subscription. STARAgent should:
1. Discover available skills from `~/.claude/skills/`
2. Expose skill capabilities to its LLM for informed decision-making
3. Delegate skill execution to Claude Code via subprocess
4. Support skill filtering for specialized agents

## Why This Matters

1. **Capability Gap**: STARAgent cannot currently generate Office documents, process PDFs, or use other skill-based workflows.

2. **Informed Delegation**: Without knowing what skills exist, STARAgent cannot make good decisions about when to use them.

3. **Subscription-Based**: Uses existing Claude subscription (Pro/Max/Team) rather than requiring separate API credits.

4. **Local Skills**: Supports both Anthropic-provided skills and custom SKILL.md files installed in `~/.claude/skills/`.

5. **Agent Specialization**: Enables creation of domain-specific agents by filtering to relevant skills.

6. **Cognitive Ontology Alignment**: Skills as resources aligns with the broader vision of composable, ontology-aware agents.

## User Stories

### Story 1: Generate a Presentation
> As a user, I want to ask my STARAgent to "create a presentation about Q4 results" and have it generate an actual .pptx file using Claude Code's pptx skill.

### Story 2: Context-Aware Skills
> As a user, I want skills to receive context from my conversation, so when I discuss Q4 metrics and then say "create a presentation about that," the presentation includes those metrics.

### Story 3: Zero Configuration (Greedy Default)
> As a developer, I want skills to be automatically discovered and available by default on all my STARAgents.

### Story 4: Specialized Agents
> As a developer, I want to create a "document specialist" agent that only has document-related skills (pptx, docx, pdf), not all 19+ skills.

### Story 5: Informed Decisions
> As an LLM inside STARAgent, I want to see what skills are available so I can decide whether to delegate a task to Claude Code or handle it myself.

## Proposed Solution

### Architecture

```
User: "Our Q4 revenue was $5.2M. Create a presentation about it."
     │
     ▼
STARAgent._think()
     │
     ▼
LLM sees available skills in tool description:
  "Available skills: pptx, xlsx, docx, pdf, ..."
     │
     ▼
LLM decides: "pptx skill exists, delegate to execute()"
     │
     ▼
ClaudeCodeSkills.execute(
    task="Create a Q4 results presentation. Save to ./skill_output/q4.pptx",
    context="Q4 revenue: $5.2M, growth: 23%"
)
     │
     ▼
subprocess.run([
    "claude", "--dangerously-skip-permissions", "-p",
    "Context: Q4 revenue: $5.2M...\n\nTask: Create a Q4 presentation"
])
     │
     ▼
Claude Code (local, uses subscription)
  ├── Loads pptx skill from ~/.claude/skills/
  ├── Generates presentation
  └── Saves to output directory
     │
     ▼
Returns file path + summary to STARAgent
     │
     ▼
Continue STAR loop
```

### Key Design Decisions

1. **Skill Discovery**: At initialization, scan `~/.claude/skills/` and parse SKILL.md files to discover available skills and their descriptions.

2. **Dynamic Capability Statement**: The `execute()` method's docstring dynamically lists discovered skills, giving the LLM visibility into actual capabilities.

3. **Greedy Default**: Without filtering, all discovered skills are exposed. This is the default behavior.

4. **Skill Filtering**: Optional `skills` parameter allows filtering to specific skills for specialized agents.

5. **Subprocess Delegation**: Use Claude Code CLI as subprocess rather than Anthropic API. This uses the subscription instead of API credits.

6. **Context Injection**: The LLM extracts relevant context from the timeline and passes it in the prompt. Skills execute in isolation but receive context explicitly.

7. **Resource-Based**: Implement as `ClaudeCodeSkills` resource that can be attached to any agent via `with_resources()`. Skills ARE resources.

8. **Unset API Key**: Must unset `ANTHROPIC_API_KEY` env var so Claude Code uses subscription auth instead of API credits.

### Skill Discovery

```python
def _discover_skills(self) -> list[dict]:
    """Discover skills from ~/.claude/skills/ directory.

    Parses each SKILL.md file to extract:
    - name: Directory name (e.g., "pptx")
    - description: First paragraph or heading from SKILL.md

    Returns:
        List of skill dicts: [{"name": "pptx", "description": "Create PowerPoint..."}, ...]
    """
    skills = []
    skills_dir = Path("~/.claude/skills").expanduser()

    if not skills_dir.exists():
        return skills

    for skill_path in skills_dir.iterdir():
        if skill_path.is_dir():
            skill_md = skill_path / "SKILL.md"
            if skill_md.exists():
                description = self._parse_skill_description(skill_md)
                skills.append({
                    "name": skill_path.name,
                    "description": description
                })

    return skills
```

### Proven Implementation

Verified working command:
```bash
unset ANTHROPIC_API_KEY && claude --dangerously-skip-permissions -p \
  "Context: Q4 revenue $5.2M, 23% growth, 150 customers.
   Task: Create a 2-slide presentation. Save to /tmp/q4.pptx"
```

Result: Created 83KB .pptx file with correct data.

### Context Handling

Skills execute in separate subprocess - they don't see STARAgent's timeline. Context is passed explicitly:

```python
@tool_use
def execute(self, task: str, context: str = "") -> dict:
    """Execute a task using Claude Code skills.

    Available skills:
    {dynamically populated from discovery}

    Use ONLY when user needs one of these capabilities.
    Do NOT use for general questions or tasks these skills can't handle.

    Args:
        task: What to do (include file output path if needed)
        context: Relevant information from the conversation that the skill needs
    """
    prompt = task
    if context:
        prompt = f"Context from our conversation:\n{context}\n\nTask: {task}"

    # ... subprocess call
```

The LLM calling this method is responsible for extracting and providing relevant context.

## Requirements

### Functional Requirements

1. **FR-1**: `ClaudeCodeSkills` resource wraps Claude Code CLI subprocess calls
2. **FR-2**: Resource discovers available skills from `~/.claude/skills/` at initialization
3. **FR-3**: Resource dynamically generates capability statement listing available skills
4. **FR-4**: Optional `skills` parameter filters to specific skills (for specialized agents)
5. **FR-5**: Resource is added by default to STARAgents when Claude Code is available (greedy)
6. **FR-6**: `execute(task, context)` method invokes Claude Code with injected context
7. **FR-7**: Environment modified to unset `ANTHROPIC_API_KEY` (use subscription)
8. **FR-8**: Uses `--dangerously-skip-permissions` for file operations
9. **FR-9**: Uses `-p` (print) mode for non-interactive execution
10. **FR-10**: Configurable output directory for generated files
11. **FR-11**: Timeout handling for long-running skill executions
12. **FR-12**: Graceful degradation if Claude Code not installed or no skills found

### Non-Functional Requirements

1. **NFR-1**: Check for Claude Code availability once at initialization
2. **NFR-2**: Skill discovery happens once at initialization (not per-call)
3. **NFR-3**: Clear error messages when Claude Code is missing or skills not found
4. **NFR-4**: Default timeout of 5 minutes for skill execution
5. **NFR-5**: Capture both stdout and stderr from subprocess

## API Specification

### ClaudeCodeSkills Resource

```python
from pathlib import Path
import os
import subprocess

from dana.common.protocols.war import tool_use
from dana.core.resource.base_resource import BaseResource


class ClaudeCodeSkills(BaseResource):
    """Execute tasks using Claude Code skills via subprocess.

    This resource discovers available skills from ~/.claude/skills/ and
    exposes them to the agent's LLM for informed decision-making.

    Skills are ontological elements - composable capabilities that can be:
    - Discovered automatically (greedy default)
    - Filtered for specialized agents
    - Combined to create domain-specific agents

    Skills execute in a separate Claude Code process. Context from the
    current conversation must be passed explicitly via the context parameter.
    """

    def __init__(
        self,
        skills: list[str] | None = None,
        skills_dir: str = "~/.claude/skills",
        output_dir: str = "./skill_output",
        timeout: int = 300,
        resource_id: str = "claude-skills",
    ):
        """
        Args:
            skills: List of skill names to expose. None = all discovered (greedy).
                    Example: ["pptx", "xlsx"] for document specialist agent.
            skills_dir: Directory to discover skills from (default: ~/.claude/skills)
            output_dir: Default directory for skill output files
            timeout: Execution timeout in seconds (default: 300)
            resource_id: Resource identifier
        """
        self._skills_dir = Path(skills_dir).expanduser()
        self._output_dir = output_dir
        self._timeout = timeout
        self._available = self._check_claude_available()

        # Discover all skills, then optionally filter
        self._all_skills = self._discover_skills()
        self._skills = self._filter_skills(skills) if skills else self._all_skills

        super().__init__(resource_type="claude-skills", resource_id=resource_id)

    def _check_claude_available(self) -> bool:
        """Check if Claude Code CLI is installed."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _discover_skills(self) -> list[dict]:
        """Discover skills from skills_dir.

        Returns:
            List of skill dicts: [{"name": "pptx", "description": "..."}, ...]
        """
        skills = []

        if not self._skills_dir.exists():
            return skills

        for skill_path in self._skills_dir.iterdir():
            if skill_path.is_dir():
                skill_md = skill_path / "SKILL.md"
                if skill_md.exists():
                    description = self._parse_skill_description(skill_md)
                    skills.append({
                        "name": skill_path.name,
                        "description": description
                    })

        return skills

    def _parse_skill_description(self, skill_md: Path) -> str:
        """Extract description from SKILL.md file."""
        try:
            content = skill_md.read_text()
            # Extract first non-empty line or heading
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    return line[:200]  # Truncate long descriptions
                if line.startswith('# '):
                    return line[2:][:200]
            return "Claude Code skill"
        except Exception:
            return "Claude Code skill"

    def _filter_skills(self, skill_names: list[str]) -> list[dict]:
        """Filter discovered skills to only those in skill_names."""
        return [s for s in self._all_skills if s["name"] in skill_names]

    def _format_skills_for_docstring(self) -> str:
        """Format skills list for inclusion in execute() docstring."""
        if not self._skills:
            return "No skills available."

        lines = []
        for skill in self._skills:
            lines.append(f"- {skill['name']}: {skill['description']}")
        return '\n'.join(lines)

    @property
    def enabled(self) -> bool:
        """Whether Claude Code is available and skills were discovered."""
        return self._available and len(self._skills) > 0

    @property
    def skills(self) -> list[dict]:
        """List of available skills."""
        return self._skills

    @tool_use
    def execute(self, task: str, context: str = "") -> dict:
        """Execute a task using Claude Code skills.

        Available skills:
        {skills_list}

        Use ONLY when user needs one of these specific capabilities.
        Do NOT use for general questions, code generation, or tasks these skills can't handle.

        Args:
            task: What you want done. Include output file path if creating files.
                  Example: "Create a 5-slide presentation about AI. Save to ./skill_output/ai.pptx"
            context: Relevant information from the conversation that the skill needs.
                     Example: "User mentioned: Q4 revenue $5.2M, growth 23%"

        Returns:
            dict with 'success', 'output', and 'error' keys
        """
        if not self._available:
            return {"success": False, "output": "", "error": "Claude Code CLI not installed"}

        if not self._skills:
            return {"success": False, "output": "", "error": "No skills available"}

        prompt = task
        if context:
            prompt = f"Context from our conversation:\n{context}\n\nTask: {task}"

        # Ensure output directory exists
        os.makedirs(self._output_dir, exist_ok=True)

        # Prepare environment - unset API key to use subscription
        env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}

        try:
            result = subprocess.run(
                ["claude", "--dangerously-skip-permissions", "-p", prompt],
                capture_output=True,
                text=True,
                env=env,
                timeout=self._timeout,
                cwd=self._output_dir,
            )
            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr if result.returncode != 0 else ""
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "output": "", "error": f"Timeout after {self._timeout}s"}
        except Exception as e:
            return {"success": False, "output": "", "error": str(e)}
```

**Note**: The `{skills_list}` placeholder in the docstring should be dynamically replaced with the output of `_format_skills_for_docstring()`. This requires either:
1. Dynamic docstring generation (property-based)
2. Custom `@tool_use` decorator handling
3. Override in prompt engineer

### STARAgent Integration

```python
class STARAgent(BaseSTARAgent):
    def __init__(
        self,
        ...
        enable_skills: bool = True,
        skills_output_dir: str = "./skill_output",
        **kwargs,
    ):
        ...
        # Existing default resource
        self.with_resources(ToDoResource(resource_id="todo-resource"))

        # Add Claude Code skills resource (greedy - all discovered skills)
        if enable_skills:
            from dana.core.skills import ClaudeCodeSkills
            skills = ClaudeCodeSkills(output_dir=skills_output_dir)
            if skills.enabled:
                self.with_resources(skills)
```

### Usage Examples

```python
# Default - greedy discovery of ALL skills
agent = STARAgent(agent_type="my-agent")
# Agent sees: "Available skills: pptx, xlsx, docx, pdf, csv-xlsx, ..."

# Custom output directory
agent = STARAgent(
    agent_type="my-agent",
    skills_output_dir="./generated_docs",
)

# Disable skills entirely
agent = STARAgent(
    agent_type="my-agent",
    enable_skills=False,
)

# Specialized agent - document skills only
doc_agent = STARAgent(agent_type="document-specialist", enable_skills=False)
doc_agent.with_resources(
    ClaudeCodeSkills(skills=["pptx", "docx", "pdf"])
)
# Agent sees: "Available skills: pptx, docx, pdf"

# Specialized agent - spreadsheet skills only
data_agent = STARAgent(agent_type="data-analyst", enable_skills=False)
data_agent.with_resources(
    ClaudeCodeSkills(skills=["xlsx", "csv-xlsx"])
)
# Agent sees: "Available skills: xlsx, csv-xlsx"
```

## Future Evolution

### Learned Capabilities (Post-MVP)

Through COSTAR's Reflect phase, skill capabilities can be refined:

```python
# Future: capabilities learned from outcomes
class ClaudeCodeSkills(BaseResource):
    def __init__(self, capabilities_path: str = None, ...):
        self._discovered_skills = self._discover_skills()
        self._learned_capabilities = self._load_learned(capabilities_path)

    def reflect(self, task: str, skill: str, outcome: dict) -> None:
        """Called by Reflect phase to update learned capabilities."""
        # Update capabilities based on success/failure
        # e.g., "pptx struggles with complex charts"
```

### Ontology Integration (Post-MVP)

Skills could be registered in the Cognitive Ontology:

```python
# Future: skills as ontology elements
ontology.register_skill(Skill("pptx", source="claude-code", capabilities=[...]))

# Agents composed from ontology
agent = STARAgent(agent_type="analyst")
agent.with_skills(ontology.skills_for_domain("reporting"))
```

## Prerequisites

### Required
- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- Claude subscription (Pro/Max/Team/Enterprise)
- Logged in (`claude login`)

### Skills Installation
Skills must be installed in `~/.claude/skills/`:
```bash
cd ~/.claude/skills
git clone https://github.com/anthropics/skills.git temp
mv temp/skills/* .
rm -rf temp
```

## Dependencies

- Claude Code CLI v2.1.0+
- Claude subscription (Pro/Max/Team/Enterprise)
- Skills installed in `~/.claude/skills/`

## Out of Scope

- Anthropic API integration (uses Claude Code subprocess instead)
- Session management / context persistence across calls
- Custom skill creation (users install skills separately)
- Interactive permission prompts (uses --dangerously-skip-permissions)
- Learned capabilities via Reflect (future enhancement)
- Ontology registration (future enhancement)

## Success Metrics

1. `ClaudeCodeSkills` resource discovers skills from `~/.claude/skills/`
2. LLM sees available skills in tool description (informed decisions)
3. Skills can generate actual .pptx, .xlsx, .docx, .pdf files
4. Context passed to skills is reflected in output (e.g., Q4 numbers in presentation)
5. Skill filtering works for specialized agents
6. Graceful handling when Claude Code is not installed or no skills found
7. Default enabled with zero configuration when Claude Code is available
8. **E2E via STARAgent**: Given a user query, STARAgent autonomously decides to use Claude skills and generates output files

## File Structure

```
dana_agent/dana/
├── core/
│   ├── agent/
│   │   └── star_agent.py             # Modified: add skills resource
│   └── skills/
│       ├── __init__.py               # New
│       └── claude_code_skills.py     # New: ClaudeCodeSkills resource
└── specs/
    ├── claude-skills-prd.md          # This file
    └── claude-skills-ralph.md        # Implementation spec
```

## Open Questions

1. **Q1**: Should we support `--continue` for session persistence across calls?
   - *Decision*: No - context injection is simpler and more explicit.

2. **Q2**: How to handle large context that exceeds prompt limits?
   - *Tentative*: Truncate with warning, or let LLM summarize before passing.

3. **Q3**: Should output directory be created automatically if it doesn't exist?
   - *Decision*: Yes, create with `os.makedirs(exist_ok=True)`.

4. **Q4**: How to handle dynamic docstring for skill list?
   - *Tentative*: Custom handling in prompt engineer, or property-based docstring.

## References

- Claude Code CLI: `which claude` → `/opt/homebrew/bin/claude`
- Skills location: `~/.claude/skills/`
- Anthropic Skills Repo: https://github.com/anthropics/skills
- STARAgent ToDoResource pattern: `dana_agent/dana/core/agent/star_agent.py:183`
- Dana Cognitive Ontology: https://github.com/aitomatic/dana
