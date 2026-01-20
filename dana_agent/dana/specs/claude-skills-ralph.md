**Status: ⚠️ IN PROGRESS**

# Claude Skills Integration - Implementation Spec

## Cognitive Ontology Context

This implementation is part of Dana's **Cognitive Ontology** vision. Skills are **ontological elements** - reusable, composable capabilities that define what an agent can do.

### Key Principles

1. **Skills are Resources**: No new abstraction needed. Skills use the existing `with_resources()` pattern.
2. **Greedy Default**: Agents discover and expose ALL available skills from `~/.claude/skills/` by default.
3. **Specialized Agents via Filtering**: Domain-specific agents are created by filtering to relevant skills.
4. **Informed Decisions**: LLM sees available skills in tool description, enabling informed delegation decisions.

### Agent Specialization Pattern

```python
# General agent - all skills (greedy default)
agent = STARAgent(agent_type="general")

# Document specialist - filtered skills
doc_agent = STARAgent(agent_type="doc-specialist", enable_skills=False)
doc_agent.with_resources(ClaudeCodeSkills(skills=["pptx", "docx", "pdf"]))
```

---

## Goal

Implement `ClaudeCodeSkills` resource that:
1. Discovers available skills from `~/.claude/skills/`
2. Exposes skill capabilities to the agent's LLM for informed decision-making
3. Delegates task execution to Claude Code CLI via subprocess
4. Supports skill filtering for specialized agents

## Demo

### Without Claude Skills (The Problem)

```
User: "Create a presentation about our Q4 results"
Agent: "I cannot create PowerPoint files. I can only provide text-based content."
```

The agent has no way to generate actual Office documents or leverage Claude Skills.

### With Claude Skills (The Solution)

```python
# Agent automatically discovers and has skills available
agent = STARAgent(agent_type="my-agent")

# User asks for a presentation
agent.query(message="Our Q4 revenue was $5.2M. Create a presentation about it.")
```

The agent's LLM sees available skills and decides to use the resource:
```xml
<tool_call>
  <function>call_resource</function>
  <arguments>
    <resource_id>claude-skills</resource_id>
    <method>execute</method>
    <parameters>
      <task>Create a 3-slide presentation about Q4 results. Save to ./skill_output/q4.pptx</task>
      <context>Q4 revenue: $5.2M, growth: 23%, 150 new customers</context>
    </parameters>
  </arguments>
</tool_call>
```

### What You'll See

```
Agent: I'll create a presentation about your Q4 results.

[Skill execution: Claude Code generating presentation...]

Agent: Done! I've created a presentation at ./skill_output/q4.pptx with:
- Slide 1: Q4 Highlights - $5.2M revenue
- Slide 2: Growth metrics - 23% increase
- Slide 3: Customer acquisition - 150 new customers
```

Output file: `./skill_output/q4.pptx` (actual PowerPoint file)

## MVP Requirements

### ClaudeCodeSkills Resource

- [x] Create `dana_agent/dana/core/skills/__init__.py`
- [x] Create `dana_agent/dana/core/skills/claude_code_skills.py` with `ClaudeCodeSkills` class
- [x] Inherit from `BaseResource` (like `ToDoResource`)
- [x] Use `@tool_use` decorator on `execute()` method
- [x] Implement `_check_claude_available()` to verify CLI exists

### Skill Discovery

- [x] Implement `_discover_skills()` to scan `~/.claude/skills/` directory
- [x] Parse each `SKILL.md` file to extract skill name and description
- [x] Store discovered skills as list of dicts: `[{"name": "pptx", "description": "..."}]`
- [x] Implement `_parse_skill_description()` to extract first line/heading from SKILL.md
- [x] Implement `_format_skills_for_docstring()` to generate skill list for LLM

### Skill Filtering

- [x] Accept optional `skills: list[str] | None` parameter in `__init__`
- [x] If `skills=None`, expose all discovered skills (greedy default)
- [x] If `skills=["pptx", "xlsx"]`, filter to only those skills
- [x] Implement `_filter_skills()` to filter discovered skills by name

### Execute Method

- [x] Accept `task: str` parameter (what to do, including output path)
- [x] Accept `context: str = ""` parameter (conversation context to inject)
- [x] Build prompt: `f"Context from our conversation:\n{context}\n\nTask: {task}"`
- [x] Run subprocess with: `["claude", "--dangerously-skip-permissions", "-p", prompt]`
- [x] Unset `ANTHROPIC_API_KEY` in subprocess environment (use subscription auth)
- [x] Set `cwd` to `output_dir` for file output
- [x] Handle timeout (default 300 seconds)
- [x] Return dict with `success`, `output`, `error` keys

### Dynamic Docstring

- [x] The `execute()` method's docstring must include discovered skills
- [x] Implement mechanism to inject `_format_skills_for_docstring()` output into docstring
- [x] Option 2 (post-init docstring update) implemented

### STARAgent Integration

- [x] Add `enable_skills: bool = True` parameter to `STARAgent.__init__`
- [x] Add `skills_output_dir: str = "./skill_output"` parameter
- [x] Create `ClaudeCodeSkills` instance when `enable_skills=True`
- [x] Only add resource if `skills.enabled` is True (Claude available AND skills discovered)
- [x] Add resource via existing `self.with_resources()` pattern

### Error Handling

- [x] Graceful failure if Claude Code CLI not installed
- [x] Graceful failure if no skills discovered
- [x] Timeout handling with clear error message
- [x] Capture stderr on failures
- [x] Create output directory if it doesn't exist

## Files Implemented

```
dana/
└── __init__.py                              ✅ (new: local import shim + structlog fallback)
dana_agent/dana/
├── common/
│   ├── __init__.py                          ✅ (lazy LLM imports)
│   ├── base_war.py                          ✅ (lazy LLM import in property)
│   ├── config.py                            ✅ (safe logging fallback)
│   └── observable.py                        ✅ (optional langfuse dependency)
├── core/
│   ├── __init__.py                          ✅ (lazy STARAgent import)
│   ├── agent/
│   │   └── star_agent.py                    ✅ (modify: add skills resource)
│   └── skills/
│       ├── __init__.py                      ✅ (new)
│       └── claude_code_skills.py            ✅ (new)
├── repositories/
│   └── __init__.py                          ✅ (optional langfuse repository)
└── specs/
    └── claude-skills-ralph.md               ✅ (this file)
tests/
└── conftest.py                              ✅ (new: add dana_agent to sys.path for tests)
```

### File: `dana_agent/dana/core/skills/__init__.py`

```python
"""Claude Skills integration via Claude Code CLI.

Skills are ontological elements - reusable, composable capabilities that
define what an agent can do. This module provides the ClaudeCodeSkills
resource which discovers and exposes Claude Code skills to STARAgents.
"""

from .claude_code_skills import ClaudeCodeSkills

__all__ = ["ClaudeCodeSkills"]
```

### File: `dana_agent/dana/core/skills/claude_code_skills.py`

```python
"""
ClaudeCodeSkills - Execute tasks using Claude Code skills via subprocess.

This resource discovers available skills from ~/.claude/skills/ and exposes
them to the agent's LLM for informed decision-making. Skills are ontological
elements that can be composed to create domain-specific agents.

Part of Dana's Cognitive Ontology vision.
"""

import os
import subprocess
from pathlib import Path

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

    Usage:
        # Greedy default - all discovered skills
        skills = ClaudeCodeSkills()

        # Filtered - document skills only
        skills = ClaudeCodeSkills(skills=["pptx", "docx", "pdf"])

        # Custom skills directory
        skills = ClaudeCodeSkills(skills_dir="~/my-skills")
    """

    def __init__(
        self,
        skills: list[str] | None = None,
        skills_dir: str = "~/.claude/skills",
        output_dir: str = "./skill_output",
        timeout: int = 300,
        resource_id: str = "claude-skills",
        **kwargs,
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

        super().__init__(resource_type="claude-skills", resource_id=resource_id, **kwargs)

    def _check_claude_available(self) -> bool:
        """Check if Claude Code CLI is installed."""
        try:
            result = subprocess.run(
                ["claude", "--version"],
                capture_output=True,
                timeout=5,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _discover_skills(self) -> list[dict]:
        """Discover skills from skills_dir.

        Scans the skills directory for subdirectories containing SKILL.md files.
        Parses each SKILL.md to extract the skill name and description.

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
                        "description": description,
                    })

        return skills

    def _parse_skill_description(self, skill_md: Path) -> str:
        """Extract description from SKILL.md file.

        Looks for the first non-empty, non-heading line or the first heading.

        Args:
            skill_md: Path to SKILL.md file

        Returns:
            Description string (truncated to 200 chars)
        """
        try:
            content = skill_md.read_text()
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#"):
                    return line[:200]
                if line.startswith("# "):
                    return line[2:][:200]
            return "Claude Code skill"
        except Exception:
            return "Claude Code skill"

    def _filter_skills(self, skill_names: list[str]) -> list[dict]:
        """Filter discovered skills to only those in skill_names.

        Args:
            skill_names: List of skill names to include

        Returns:
            Filtered list of skill dicts
        """
        return [s for s in self._all_skills if s["name"] in skill_names]

    def _format_skills_for_docstring(self) -> str:
        """Format skills list for inclusion in execute() docstring.

        Returns:
            Formatted string listing available skills
        """
        if not self._skills:
            return "No skills available."

        lines = []
        for skill in self._skills:
            lines.append(f"- {skill['name']}: {skill['description']}")
        return "\n".join(lines)

    @property
    def enabled(self) -> bool:
        """Whether Claude Code is available and skills were discovered."""
        return self._available and len(self._skills) > 0

    @property
    def skills(self) -> list[dict]:
        """List of available skills."""
        return self._skills

    @property
    def all_skills(self) -> list[dict]:
        """List of all discovered skills (before filtering)."""
        return self._all_skills

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
            dict with:
            - success (bool): Whether the task completed successfully
            - output (str): Output from Claude Code (summary of what was done)
            - error (str): Error message if failed, empty string if successful
        """
        if not self._available:
            return {
                "success": False,
                "output": "",
                "error": "Claude Code CLI is not installed. Install with: npm install -g @anthropic-ai/claude-code",
            }

        if not self._skills:
            return {
                "success": False,
                "output": "",
                "error": "No skills available. Install skills in ~/.claude/skills/",
            }

        # Build prompt with context injection
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
                "error": result.stderr if result.returncode != 0 else "",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {self._timeout} seconds",
            }
        except Exception as e:
            return {
                "success": False,
                "output": "",
                "error": str(e),
            }

    # Override to provide dynamic docstring with skills list
    # This is called by the prompt engineer to get the tool description
    def get_execute_docstring(self) -> str:
        """Get the execute method's docstring with skills list populated."""
        base_doc = """Execute a task using Claude Code skills.

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
    dict with:
    - success (bool): Whether the task completed successfully
    - output (str): Output from Claude Code (summary of what was done)
    - error (str): Error message if failed, empty string if successful
"""
        return base_doc.format(skills_list=self._format_skills_for_docstring())
```

### Modification: `dana_agent/dana/core/agent/star_agent.py`

Add to `__init__` parameters (before `**kwargs`, around line 60):

```python
enable_skills: bool = True,
skills_output_dir: str = "./skill_output",
```

Add after line 183 (after the ToDoResource):

```python
# Add Claude Code skills resource (greedy - all discovered skills)
if enable_skills:
    from dana.core.skills import ClaudeCodeSkills
    skills = ClaudeCodeSkills(output_dir=skills_output_dir)
    if skills.enabled:
        self.with_resources(skills)
```

## Dynamic Docstring Implementation Note

The `{skills_list}` placeholder in the `execute()` docstring needs to be populated with actual discovered skills. Options:

1. **Override in prompt engineer**: The `ResourcePromptEngineer` could check for a `get_execute_docstring()` method and use that instead of `execute.__doc__`.

2. **Post-init docstring update**: After `__init__`, update `execute.__doc__` dynamically (Python allows this).

3. **Custom `@tool_use` handling**: Modify the decorator to support dynamic docstrings.

For MVP, option 2 (post-init update) is simplest:

```python
def __init__(self, ...):
    # ... existing init code ...

    # Update execute docstring with discovered skills
    self.execute.__func__.__doc__ = self.get_execute_docstring()
```

## Tests Required

### Unit Tests: `tests/unit/core/skills/test_claude_code_skills.py`

- [x] `test_init_default_values` - Verify default output_dir, timeout, resource_id, skills_dir
- [x] `test_init_custom_values` - Verify custom parameters are set
- [x] `test_init_with_skill_filter` - Verify skills parameter filters discovered skills
- [x] `test_check_claude_available_when_installed` - Mock subprocess to return success
- [x] `test_check_claude_available_when_not_installed` - Mock FileNotFoundError
- [x] `test_discover_skills_finds_skills` - Mock skills directory with SKILL.md files
- [x] `test_discover_skills_empty_dir` - Returns empty list when no skills
- [x] `test_discover_skills_missing_dir` - Returns empty list when dir doesn't exist
- [x] `test_parse_skill_description_first_line` - Extracts first non-heading line
- [x] `test_parse_skill_description_heading` - Extracts heading text
- [x] `test_parse_skill_description_truncates` - Truncates long descriptions
- [x] `test_filter_skills` - Filters to only specified skills
- [x] `test_format_skills_for_docstring` - Formats skills as bullet list
- [x] `test_enabled_property_true` - True when available AND skills found
- [x] `test_enabled_property_false_no_claude` - False when Claude not available
- [x] `test_enabled_property_false_no_skills` - False when no skills discovered
- [x] `test_execute_returns_error_when_not_available` - Verify error dict when CLI missing
- [x] `test_execute_returns_error_when_no_skills` - Verify error dict when no skills
- [x] `test_execute_builds_prompt_with_context` - Verify prompt construction
- [x] `test_execute_builds_prompt_without_context` - Verify task-only prompt
- [x] `test_execute_unsets_api_key` - Verify ANTHROPIC_API_KEY removed from env
- [x] `test_execute_creates_output_dir` - Verify makedirs called
- [x] `test_execute_handles_timeout` - Mock TimeoutExpired, verify error response
- [x] `test_execute_handles_success` - Mock successful subprocess, verify response
- [x] `test_execute_handles_failure` - Mock failed subprocess, verify stderr in error

### Integration Tests: `tests/integration/core/skills/test_claude_code_skills_integration.py`

- [x] `test_star_agent_has_skills_by_default` - Verify resource added when Claude available
- [x] `test_star_agent_skills_disabled` - Verify resource not added when enable_skills=False
- [x] `test_star_agent_custom_output_dir` - Verify custom output_dir passed through
- [x] `test_specialized_agent_filtered_skills` - Verify filtered skills work

### Live Tests: `tests/live/core/skills/test_claude_code_skills_live.py`

These tests use **real Claude Code CLI** and require:
- Claude Code installed and authenticated
- Skills installed in `~/.claude/skills/`
- Active Claude subscription

**Marked with `@pytest.mark.live`** - excluded from CI, run manually.

```python
"""
Live E2E tests for ClaudeCodeSkills.

These tests actually invoke Claude Code CLI and generate real files.
Run manually with: pytest -m live tests/live/core/skills/ -v

Requirements:
- Claude Code CLI installed and authenticated
- Skills installed in ~/.claude/skills/
- Active Claude subscription
"""

import os
import tempfile

import pytest

from dana.core.skills import ClaudeCodeSkills


@pytest.mark.live
class TestClaudeCodeSkillsLive:
    """Live tests that actually invoke Claude Code."""

    def test_discover_real_skills(self):
        """Verify skill discovery works with actual ~/.claude/skills/ directory."""
        skills = ClaudeCodeSkills()

        # Should find skills if they're installed
        assert skills.enabled, "Claude Code should be available"
        assert len(skills.skills) > 0, "Should discover at least one skill"

        # Check expected skills exist
        skill_names = [s["name"] for s in skills.skills]
        print(f"Discovered skills: {skill_names}")

        # At minimum, pptx should exist if skills are installed
        assert "pptx" in skill_names, "pptx skill should be available"

    def test_execute_pptx_skill_creates_file(self):
        """E2E: Actually generate a .pptx file via Claude Code."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = ClaudeCodeSkills(output_dir=tmpdir)

            assert skills.enabled, "Claude Code should be available"

            output_path = os.path.join(tmpdir, "test_presentation.pptx")
            result = skills.execute(
                task=f"Create a simple 2-slide presentation about testing. "
                     f"Slide 1: Title 'Test Presentation'. "
                     f"Slide 2: One bullet point saying 'This is a test'. "
                     f"Save to {output_path}",
                context="This is an automated test of the Claude Skills integration."
            )

            print(f"Result: {result}")

            # Verify execution succeeded
            assert result["success"], f"Execution failed: {result['error']}"

            # Verify file was created
            assert os.path.exists(output_path), f"Output file not created: {output_path}"

            # Verify file has content (not empty)
            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes), likely empty or corrupt"

            print(f"Successfully created {output_path} ({file_size} bytes)")

    def test_execute_with_context_injection(self):
        """E2E: Verify context is passed to Claude Code and reflected in output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            skills = ClaudeCodeSkills(output_dir=tmpdir)

            assert skills.enabled, "Claude Code should be available"

            output_path = os.path.join(tmpdir, "q4_results.pptx")
            result = skills.execute(
                task=f"Create a 2-slide presentation about Q4 results. "
                     f"Include the revenue and growth numbers from context. "
                     f"Save to {output_path}",
                context="Q4 revenue: $5.2M, growth: 23%, new customers: 150"
            )

            print(f"Result: {result}")

            assert result["success"], f"Execution failed: {result['error']}"
            assert os.path.exists(output_path), f"Output file not created: {output_path}"

            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes)"

            print(f"Successfully created {output_path} ({file_size} bytes)")

    def test_filtered_skills(self):
        """E2E: Verify skill filtering works with real skills."""
        # All skills
        all_skills = ClaudeCodeSkills()
        all_count = len(all_skills.skills)

        # Filtered to just pptx
        filtered = ClaudeCodeSkills(skills=["pptx"])

        assert len(filtered.skills) == 1, "Should have exactly one skill"
        assert filtered.skills[0]["name"] == "pptx", "Should be pptx skill"
        assert len(filtered.skills) < all_count, "Filtered should have fewer skills"
```

### E2E Live Tests via STARAgent: `tests/live/core/skills/test_star_agent_skills_e2e.py`

These tests verify the **full E2E flow**: STARAgent receives a query → LLM decides to use skills → file is generated.

**This is the critical test** that validates the entire integration works as designed.

```python
"""
E2E tests for STARAgent with Claude Skills integration.

These tests verify the FULL flow:
1. STARAgent receives a user query
2. Agent's LLM sees available skills and decides to use them
3. Agent autonomously calls ClaudeCodeSkills.execute()
4. Actual file is generated

Run manually with: pytest -m live tests/live/core/skills/test_star_agent_skills_e2e.py -v

Requirements:
- Claude Code CLI installed and authenticated
- Skills installed in ~/.claude/skills/
- Active Claude subscription
- LLM API key configured (for STARAgent's LLM)
"""

import os
import tempfile

import pytest

from dana.core.agent.star_agent import STARAgent


@pytest.mark.live
class TestSTARAgentSkillsE2E:
    """E2E tests: STARAgent query → skill execution → file output."""

    def test_star_agent_creates_presentation_from_query(self):
        """E2E: STARAgent receives query and autonomously creates .pptx file.

        This is the primary E2E test validating the full integration:
        User query → LLM decision → skill execution → file output
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create agent with skills enabled (default)
            agent = STARAgent(
                agent_type="test-skills-agent",
                skills_output_dir=tmpdir,
            )

            # Verify skills resource is attached
            resource_ids = [r.resource_id for r in agent._resources]
            assert "claude-skills" in resource_ids, "Skills resource should be attached"

            output_path = os.path.join(tmpdir, "test_e2e.pptx")

            # Send query that should trigger skill usage
            response = agent.query(
                message=f"Create a simple 2-slide presentation about software testing. "
                        f"Slide 1 should have the title 'Testing Fundamentals'. "
                        f"Slide 2 should list 3 types of testing. "
                        f"Save the file to {output_path}"
            )

            print(f"Agent response: {response}")

            # Verify file was created
            assert os.path.exists(output_path), (
                f"Output file not created at {output_path}. "
                f"Agent may not have used the skills resource. Response: {response}"
            )

            # Verify file has content
            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes)"

            print(f"SUCCESS: STARAgent created {output_path} ({file_size} bytes)")

    def test_star_agent_uses_context_in_skill_execution(self):
        """E2E: STARAgent passes conversation context to skill execution.

        Verifies that when user provides context and then asks for a document,
        the agent extracts and passes relevant context to the skill.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = STARAgent(
                agent_type="test-context-agent",
                skills_output_dir=tmpdir,
            )

            output_path = os.path.join(tmpdir, "q4_report.pptx")

            # Query with embedded context that should appear in output
            response = agent.query(
                message=f"Our Q4 results: Revenue was $5.2 million, up 23% year-over-year. "
                        f"We acquired 150 new enterprise customers. "
                        f"Create a 2-slide executive summary presentation with these numbers. "
                        f"Save to {output_path}"
            )

            print(f"Agent response: {response}")

            # Verify file was created
            assert os.path.exists(output_path), (
                f"Output file not created. Agent response: {response}"
            )

            file_size = os.path.getsize(output_path)
            assert file_size > 1000, f"File too small ({file_size} bytes)"

            print(f"SUCCESS: Context-aware presentation created ({file_size} bytes)")

    def test_star_agent_with_filtered_skills(self):
        """E2E: Specialized agent with filtered skills works correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            from dana.core.skills import ClaudeCodeSkills

            # Create agent without default skills
            agent = STARAgent(
                agent_type="doc-specialist",
                enable_skills=False,
            )

            # Add filtered skills (documents only)
            filtered_skills = ClaudeCodeSkills(
                skills=["pptx", "docx"],
                output_dir=tmpdir,
            )
            agent.with_resources(filtered_skills)

            # Verify only filtered skills are available
            skill_names = [s["name"] for s in filtered_skills.skills]
            assert "pptx" in skill_names
            assert "xlsx" not in skill_names, "xlsx should be filtered out"

            output_path = os.path.join(tmpdir, "filtered_test.pptx")

            response = agent.query(
                message=f"Create a simple 1-slide presentation titled 'Filtered Skills Test'. "
                        f"Save to {output_path}"
            )

            print(f"Agent response: {response}")

            assert os.path.exists(output_path), f"File not created: {response}"
            print(f"SUCCESS: Filtered skills agent created presentation")
```

Command to run tests:
```bash
# Unit tests (mocked, fast, run in CI)
pytest tests/unit/core/skills/test_claude_code_skills.py -v

# Integration tests (mocked dependencies, run in CI)
pytest tests/integration/core/skills/test_claude_code_skills_integration.py -v

# Live tests (real Claude Code, run manually, NOT in CI)
pytest -m live tests/live/core/skills/test_claude_code_skills_live.py -v
```

**CI Configuration**: Live tests are excluded by default. GitHub Actions should use:
```yaml
pytest -m "not live and not harness" --ignore=tests/live/
```

## Success Criteria

1. `ClaudeCodeSkills` resource discovers skills from `~/.claude/skills/`
2. LLM sees available skills in tool description (informed decisions)
3. `execute()` method correctly builds prompts with context injection
4. Subprocess call correctly unsets `ANTHROPIC_API_KEY`
5. Skill filtering works for specialized agents
6. Timeout handling returns appropriate error message
7. Graceful degradation when Claude Code CLI is not installed
8. Graceful degradation when no skills are discovered
9. STARAgent has skills enabled by default when Claude Code is available
10. All unit tests pass
11. All integration tests pass
12. **All live tests pass** (actual file generation via Claude Code)
13. **E2E via STARAgent**: Given a user query, STARAgent autonomously decides to use Claude skills and generates output files

## Before Marking Complete

- [x] All unit tests pass
- [x] All integration tests pass
- [ ] **All live tests pass** (direct ClaudeCodeSkills execution)
- [ ] **All E2E STARAgent tests pass** (query → LLM decision → skill execution → file output)
- [x] Code follows existing patterns (matches `ToDoResource` style)
- [x] Skill discovery works with actual `~/.claude/skills/` directory
- [x] Dynamic docstring shows discovered skills
- [x] No unnecessary complexity (KISS)
- [x] No over-engineering (YAGNI)
- [x] Code is documented where non-obvious

## When Complete

**Test execution is sequential and gated:**

```
┌─────────────────┐     ┌─────────────────────┐     ┌─────────────────┐     ┌─────────────────────┐
│  1. Unit Tests  │────▶│ 2. Integration Tests│────▶│  3. Live Tests  │────▶│ 4. E2E STARAgent    │
│    (mocked)     │     │      (mocked)       │     │  (real Claude)  │     │    (full flow)      │
│                 │     │                     │     │                 │     │                     │
│  MUST PASS to   │     │   MUST PASS to      │     │  MUST PASS to   │     │  MUST PASS to       │
│  continue       │     │   continue          │     │  continue       │     │  mark complete      │
└─────────────────┘     └─────────────────────┘     └─────────────────┘     └─────────────────────┘
```

Run these commands **in order** - stop if any step fails:

```bash
# Step 1: Unit tests (fast, mocked)
pytest tests/unit/core/skills/test_claude_code_skills.py -v
# STOP if this fails

# Step 2: Integration tests (mocked dependencies)
pytest tests/integration/core/skills/test_claude_code_skills_integration.py -v
# STOP if this fails

# Step 3: Verify imports work
python -c "from dana.core.skills import ClaudeCodeSkills; print('Import OK')"

# Step 4: Verify skill discovery (real ~/.claude/skills/)
python -c "from dana.core.skills import ClaudeCodeSkills; s = ClaudeCodeSkills(); print(f'Found {len(s.skills)} skills:', [sk['name'] for sk in s.skills])"

# Step 5: Verify STARAgent integration
python -c "from dana.core.agent.star_agent import STARAgent; a = STARAgent(agent_type='test', enable_skills=False); print('STARAgent OK')"

# Step 6: Verify filtered skills
python -c "from dana.core.skills import ClaudeCodeSkills; s = ClaudeCodeSkills(skills=['pptx', 'xlsx']); print(f'Filtered to {len(s.skills)} skills:', [sk['name'] for sk in s.skills])"

# Step 7: LIVE TESTS - direct Claude Code execution (ONLY after steps 1-6 pass)
pytest -m live tests/live/core/skills/test_claude_code_skills_live.py -v
# This actually generates .pptx files via Claude Code
# STOP if this fails

# Step 8: E2E STARAgent TESTS - full flow (ONLY after step 7 passes)
pytest -m live tests/live/core/skills/test_star_agent_skills_e2e.py -v
# This tests: user query → STARAgent LLM decision → skill execution → file output
```

**What "live tests pass" means:**
- `test_discover_real_skills`: Finds skills in `~/.claude/skills/`
- `test_execute_pptx_skill_creates_file`: Actually creates a .pptx file (>1KB)
- `test_execute_with_context_injection`: Creates .pptx with injected context
- `test_filtered_skills`: Filtering works with real skills

**What "E2E STARAgent tests pass" means:**
- `test_star_agent_creates_presentation_from_query`: STARAgent receives query, LLM decides to use skills, .pptx file created
- `test_star_agent_uses_context_in_skill_execution`: Context from query is passed to skill
- `test_star_agent_with_filtered_skills`: Specialized agent with filtered skills works

Only if ALL tests pass (including live AND E2E STARAgent), write this exact line to the ralph.md file:
```
<promise>$task_complete$</promise>
```
except replace "$task_complete$" with "TASK COMPLETE"

## References

- PRD: [claude-skills-prd.md](./claude-skills-prd.md)
- ToDoResource pattern: `dana_agent/dana/core/resource/todo.py`
- BaseResource: `dana_agent/dana/core/resource/base_resource.py`
- STARAgent: `dana_agent/dana/core/agent/star_agent.py:183` (ToDoResource attachment)
- @tool_use decorator: `dana_agent/dana/common/protocols/war.py:33`
- Dana Cognitive Ontology: https://github.com/aitomatic/dana
