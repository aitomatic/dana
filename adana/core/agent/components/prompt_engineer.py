"""
PromptEngineer: Handles XML-based prompt files and system prompt generation.

This component provides functionality for:
- Parsing XML prompt files using MRO (Method Resolution Order)
- Section-level inheritance with file-based prompts
- Generating system prompts from templates
- Formatting agent/resource/workflow descriptions
- Locale and environment information
"""

import locale
import os
import platform
import re
import sys
from datetime import datetime

from adana.common.llm.debug_logger import get_debug_logger
from adana.common.llm.types import LLMMessage
from adana.common.observable import observable
from adana.common.protocols import DictParams
from adana.core.agent.star_agent import BaseSTARAgent
from adana.core.agent.timeline import Timeline


class PromptEngineer:
    """Component providing XML-based prompt files with section-level inheritance."""

    def __init__(self, agent: BaseSTARAgent):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        self._agent = agent
        # Cache for prompt sections from files
        self._prompt_sections_cache = None
        # File-based prompt support
        self._prompt_file_path = None
        self._file_mtime = None

    def reset(self) -> None:
        """Reset the prompt engineer."""
        del self._prompt_sections_cache
        self._prompt_sections_cache = None
        # Don't reset file path - let discovery happen again
        # self._prompt_file_path = None
        self._file_mtime = None

    # ============================================================================
    # FILE-BASED PROMPT DISCOVERY SYSTEM
    # ============================================================================

    def _get_user_prompt_file(self, class_name: str) -> str:
        """Get user-specific prompt file path."""
        home_dir = os.path.expanduser("~")
        return os.path.join(home_dir, ".dana", "prompts", f"{class_name}.xml")

    def _get_lib_prompt_file(self, class_name: str) -> str:
        """Get lib/prompts file path."""
        project_root = self._find_project_root()
        return os.path.join(project_root, "adana/lib/prompts", f"{class_name}.xml")

    def _get_core_prompt_file(self, class_name: str) -> str:
        """Get core/prompts file path."""
        project_root = self._find_project_root()
        return os.path.join(project_root, "core", "prompts", f"{class_name}.xml")

    def _get_co_located_prompt_file(self, class_name: str) -> str:
        """Get co-located prompt file path."""
        module_name = self._agent.__class__.__module__
        module = sys.modules[module_name]
        module_file = module.__file__
        if module_file is None:
            return ""
        module_dir = os.path.dirname(module_file)
        return os.path.join(module_dir, f"{class_name}.xml")

    def _find_project_root(self) -> str:
        """Find project root by looking for pyproject.toml or setup.py."""
        module_name = self._agent.__class__.__module__
        module = sys.modules[module_name]
        module_file = module.__file__
        if module_file is None:
            return os.getcwd()
        current_dir = os.path.dirname(module_file)

        while current_dir != os.path.dirname(current_dir):  # Not at filesystem root
            if os.path.exists(os.path.join(current_dir, "pyproject.toml")):
                return current_dir
            current_dir = os.path.dirname(current_dir)

        return current_dir

    def _get_file_sections(self, file_path: str) -> DictParams:
        """Extract all sections from a single .xml file."""
        if not file_path or not os.path.exists(file_path):
            return {}

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except OSError:
            return {}

        # Same regex pattern as docstring parsing - works for XML tags!
        result = {}
        matches = re.findall(r"<(.*?)>(.*?)</\1>", content, re.DOTALL)
        for match in matches:
            tag_name = match[0]
            content = match[1].strip()
            result[tag_name] = content

        return result

    def _get_inherited_file_sections(self) -> DictParams:
        """Get sections from all prompt files in inheritance chain with proper merging."""
        # Get the Method Resolution Order (MRO) for inheritance support
        class_names = [cls.__name__ for cls in self._agent.__class__.__mro__ if issubclass(cls, BaseSTARAgent)]
        result = {}

        # Process classes in REVERSE MRO order (parent -> child) so child sections override parent
        for class_name in reversed(class_names):
            # Try to find a prompt file for this class (in priority order)
            user_prompt_file = self._get_user_prompt_file(class_name)
            if user_prompt_file and os.path.exists(user_prompt_file):
                file_sections = self._get_file_sections(user_prompt_file)
                result.update(file_sections)  # Child sections override parent
                continue

            lib_prompt_file = self._get_lib_prompt_file(class_name)
            if lib_prompt_file and os.path.exists(lib_prompt_file):
                file_sections = self._get_file_sections(lib_prompt_file)
                result.update(file_sections)  # Child sections override parent
                continue

            core_prompt_file = self._get_core_prompt_file(class_name)
            if core_prompt_file and os.path.exists(core_prompt_file):
                file_sections = self._get_file_sections(core_prompt_file)
                result.update(file_sections)  # Child sections override parent
                continue

            co_located_file = self._get_co_located_prompt_file(class_name)
            if co_located_file and os.path.exists(co_located_file):
                file_sections = self._get_file_sections(co_located_file)
                result.update(file_sections)  # Child sections override parent

        return result

    def _check_file_modified(self) -> bool:
        """Check if prompt file has been modified since last load."""
        if not self._prompt_file_path or not os.path.exists(self._prompt_file_path):
            return False

        current_mtime = os.path.getmtime(self._prompt_file_path)
        if self._file_mtime is None or current_mtime > self._file_mtime:
            self._file_mtime = current_mtime
            return True
        return False

    def get_prompt_file_info(self) -> dict:
        """Get information about the prompt files in inheritance chain."""
        # Get the Method Resolution Order (MRO) for inheritance support
        class_names = [cls.__name__ for cls in self._agent.__class__.__mro__]
        discovered_files = []

        # Find files in inheritance order
        for class_name in class_names:
            if class_name == "object":
                continue

            # Try to find a prompt file for this class (in priority order)
            user_prompt_file = self._get_user_prompt_file(class_name)
            if user_prompt_file and os.path.exists(user_prompt_file):
                discovered_files.append(user_prompt_file)
                continue

            lib_prompt_file = self._get_lib_prompt_file(class_name)
            if lib_prompt_file and os.path.exists(lib_prompt_file):
                discovered_files.append(lib_prompt_file)
                continue

            core_prompt_file = self._get_core_prompt_file(class_name)
            if core_prompt_file and os.path.exists(core_prompt_file):
                discovered_files.append(core_prompt_file)
                continue

            co_located_file = self._get_co_located_prompt_file(class_name)
            if co_located_file and os.path.exists(co_located_file):
                discovered_files.append(co_located_file)

        if not discovered_files:
            return {"source": "file", "files": [], "exists": False}

        file_info = []
        for file_path in discovered_files:
            file_info.append(
                {
                    "path": file_path,
                    "exists": os.path.exists(file_path),
                    "modified": os.path.getmtime(file_path) if os.path.exists(file_path) else None,
                }
            )

        return {
            "source": "file",
            "files": file_info,
            "exists": len(discovered_files) > 0,
            "inheritance": "section-level",  # Indicates section-level inheritance
        }

    def _get_prompt_section_for_tag(self, tag: str, show_tag: bool | str = True) -> str:
        """Extract a section from the formatted prompt for a given tag."""
        content = self._prompt_sections.get(tag, "")
        if len(content) == 0:
            return ""

        if show_tag:
            if isinstance(show_tag, str):
                content = f"<{show_tag}>\n{content}\n</{show_tag}>"
            else:
                content = f"<{tag}>\n{content}\n</{tag}>"
        return content

    @property
    def _prompt_sections(self) -> DictParams:
        """Get the prompt sections (cached) - file-based with section-level inheritance."""
        # Check if we need to reload (no cache or files modified)
        if not hasattr(self, "_prompt_sections_cache") or not self._prompt_sections_cache:
            # Load sections from all prompt files in inheritance chain
            self._prompt_sections_cache = self._get_inherited_file_sections()

        return self._prompt_sections_cache

    @_prompt_sections.setter
    def _prompt_sections(self, value: DictParams) -> None:
        """Set the prompt sections."""
        self._prompt_sections_cache = value

    # ============================================================================
    # PUBLIC INTERFACE PROPERTIES
    # ============================================================================

    @property
    def public_description(self) -> str:
        """Get the public description of the agent."""
        return self._get_prompt_section_for_tag("PUBLIC_DESCRIPTION")

    @property
    def identity(self) -> str:
        """Get the private identity of the agent."""
        return self._get_prompt_section_for_tag("IDENTITY")

    @property
    def system_prompt(self) -> str:
        """Get the system prompt of the agent."""
        return self._get_system_prompt()

    # ============================================================================
    # SYSTEM PROMPT GENERATION
    # ============================================================================

    def _get_system_prompt(self) -> str:
        """
        Generate system prompt with optimal section ordering for context engineering.

        Order rationale:
        1. CONSTRAINT - Critical enforcement rule (primacy). Contains the RESPONSE_SCHEMA.
        2. IDENTITY - Who the agent is
        3. DECISION_TREE - How to decide actions
        4. EXAMPLES - Learn by demonstration (middle for max impact)
        6. AVAILABLE_TARGETS - Unified registry
        7. STATE_INFO - Current environment (recency)
        """
        return f"""
{self._get_preamble_section()}

{self._get_constraint_section()}

{self._get_identity_section()}

{self._get_decision_tree_section()}

{self._get_examples_section()}

{self._get_available_targets_section()}

{self._get_state_info_section()}

{self._get_postscript_section()}
""".strip()

    # ============================================================================
    # SYSTEM PROMPT SECTION METHODS
    # ============================================================================

    def _get_preamble_section(self) -> str:
        """Get the preamble section."""
        return self._get_prompt_section_for_tag("PREAMBLE")

    def _get_constraint_section(self) -> str:
        """Get the constraint section."""
        return self._get_prompt_section_for_tag("CONSTRAINT")

    def _get_identity_section(self) -> str:
        """Get the identity section."""
        return self._get_prompt_section_for_tag("IDENTITY")

    def _get_public_description_section(self) -> str:
        """Get the public description section."""
        return self._get_prompt_section_for_tag("PUBLIC_DESCRIPTION")

    def _get_decision_tree_section(self) -> str:
        """Get the decision tree section."""
        return self._get_prompt_section_for_tag("DECISION_TREE")

    def _get_examples_section(self) -> str:
        """Get the examples section."""
        return self._get_prompt_section_for_tag("EXAMPLES")

    def _get_response_schema_section(self) -> str:
        """Get the response schema section."""
        return self._get_prompt_section_for_tag("RESPONSE_SCHEMA")

    def _get_domain_knowledge_section(self) -> str:
        """Get the domain knowledge section."""
        return self._get_prompt_section_for_tag("DOMAIN_KNOWLEDGE")

    def _get_state_info_section(self) -> str:
        """Get the state info section."""
        return f"""<STATE_INFO>
{self._prt_state_info}
</STATE_INFO>"""

    def _get_postscript_section(self) -> str:
        """Get the postscript section."""
        return self._get_prompt_section_for_tag("POSTSCRIPT")

    def _get_available_targets_section(self) -> str:
        """Get the available targets section (agents, resources, workflows)."""
        return f"""<AVAILABLE_TARGETS>
  <AGENTS>
    {self._get_prompt_section_for_tag("AGENT_GUIDELINES")}
    <AVAILABLE_AGENTS>
    {self._prt_agent_descriptions}
    </AVAILABLE_AGENTS>
  </AGENTS>

<RESOURCES>
{self._get_prompt_section_for_tag("RESOURCE_GUIDELINES")}
<AVAILABLE_RESOURCES>
{self._prt_resource_descriptions}
</AVAILABLE_RESOURCES>
</RESOURCES>

<WORKFLOWS>
{self._get_prompt_section_for_tag("WORKFLOW_GUIDELINES")}
<AVAILABLE_WORKFLOWS>
{self._prt_workflow_descriptions}
</AVAILABLE_WORKFLOWS>
</WORKFLOWS>
</AVAILABLE_TARGETS>"""

    # ============================================================================
    # TEMPLATE FORMATTING PROPERTIES
    # ============================================================================

    @property
    def _prt_state_info(self) -> str:
        """Get current state information including locale details."""
        return self._get_locale_info()

    @property
    def _prt_agent_descriptions(self) -> str:
        """Get descriptions of available agents."""
        agents = self._agent.available_agents
        if not agents or len(agents) == 0:
            return "None"
        return "\n".join([f"- {a.agent_type} (ID: {a.object_id}): {a.public_description}" for a in agents])

    @property
    def _prt_resource_descriptions(self) -> str:
        """Get descriptions of available resources."""
        resources = self._agent.available_resources
        if not resources or len(resources) == 0:
            return "None"
        # return "\n".join([f"- {r.resource_type} (ID: {r.object_id}): {r.public_description}" for r in resources]
        return "\n".join([f"- {r.public_description}" for r in resources])

    @property
    def _prt_workflow_descriptions(self) -> str:
        """Get workflow descriptions."""
        workflows = self._agent.available_workflows
        if not workflows or len(workflows) == 0:
            return "None"
        # return "\n".join([f"- {w.workflow_type} (ID: {w.object_id}): {w.public_description}" for w in workflows])
        return "\n".join([f"- {w.public_description}" for w in workflows])

    @property
    def _prt_usage_examples(self) -> str:
        """Get usage examples."""
        return ""

    # ============================================================================
    # LOCALE AND ENVIRONMENT INFORMATION
    # ============================================================================

    def _get_locale_info(self) -> str:
        """Get locale-specific information including time, location, and system details."""
        try:
            # Get current time information
            now = datetime.now()
            current_time = now.strftime("%Y-%m-%d %H:%M:%S %Z")
            current_date = now.strftime("%A, %B %d, %Y")

            # Get locale information
            try:
                system_locale = locale.getlocale()
                locale_str = f"{system_locale[0] or 'Unknown'}"
            except Exception:
                locale_str = "Unknown"

            # Get timezone information
            try:
                import time

                timezone = time.tzname[time.daylight] if time.daylight else time.tzname[0]
            except Exception:
                timezone = "Unknown"

            # Get system information
            system_info = f"{platform.system()} {platform.release()}"
            python_version = platform.python_version()

            # Get working directory
            working_dir = os.getcwd()

            # Get user information
            try:
                username = os.getenv("USER") or os.getenv("USERNAME") or "Unknown"
            except Exception:
                username = "Unknown"

            # Get additional environment info
            try:
                shell = os.getenv("SHELL", "Unknown")
                home_dir = os.path.expanduser("~")
            except Exception:
                shell = "Unknown"
                home_dir = "Unknown"

            # Get location information
            try:
                import requests

                response = requests.get("http://ip-api.com/json/", timeout=3)
                if response.status_code == 200:
                    data = response.json()
                    location = f"{data.get('city', 'Unknown')}, {data.get('regionName', 'Unknown')}, {data.get('country', 'Unknown')}"
                else:
                    location = "Unknown"
            except Exception:
                location = "Unknown"

            # Build locale info string
            locale_info = []
            locale_info.append(f"Current Time: {current_time}")
            locale_info.append(f"Date: {current_date}")
            locale_info.append(f"Timezone: {timezone}")
            locale_info.append(f"Locale: {locale_str}")
            locale_info.append(f"System: {system_info}")
            locale_info.append(f"Python: {python_version}")
            locale_info.append(f"User: {username}")
            locale_info.append(f"Shell: {shell}")
            locale_info.append(f"Home Directory: {home_dir}")
            locale_info.append(f"Working Directory: {working_dir}")
            locale_info.append(f"Location: {location}")

            return "\n".join(locale_info)

        except Exception as e:
            return f"Locale information unavailable: {str(e)}"

    @observable
    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        """Build LLM messages for the agent with simple timeline_used logic."""
        messages = []

        # System prompt - use the sophisticated prompt from components
        system_prompt = self._get_system_prompt()
        messages.append(LLMMessage(role="system", content=system_prompt))

        # Walk through timeline entries and assign roles based on is_latest_user_message
        if timeline:
            # Build timeline content (excluding latest user message)
            timeline_entries = [entry for entry in timeline.timeline if not entry.is_latest_user_message]
            if timeline_entries:
                timeline_lines = [
                    "<CONTEXT>",
                    self._get_prompt_section_for_tag("CONTEXT_INSTRUCTIONS", show_tag=False),
                    "<TIMELINE>",
                ]
                for entry in timeline_entries:
                    # Use the entry's to_string() method to include all fields
                    timeline_lines.append(f"<ENTRY>{entry.to_string()}</ENTRY>")
                timeline_lines.extend(["</TIMELINE>", "</CONTEXT>"])
                timeline_content = "\n".join(timeline_lines)
                messages.append(LLMMessage(role="system", content=timeline_content))

            # Add latest user message as separate user message, and mark it as not latest
            latest_user_entry = next((entry for entry in timeline.timeline if entry.is_latest_user_message), None)
            if latest_user_entry:
                messages.append(LLMMessage(role="user", content=latest_user_entry.content))
                latest_user_entry.is_latest_user_message = False

        # Debug logging - log message building
        debug_logger = get_debug_logger()
        system_prompt = self._get_system_prompt()
        system_prompt_length = len(system_prompt)
        debug_logger.log_agent_interaction(
            agent_id=self._agent.object_id,
            agent_type=self._agent.agent_type,
            interaction_type="build_llm_request",
            content=f"Built {len(messages)} messages for LLM request",
            metadata={
                "message_count": len(messages),
                "system_prompt_length": system_prompt_length,
                "timeline_entries": len(timeline.timeline) if timeline else 0,
            },
        )

        return messages
