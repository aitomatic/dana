"""
PromptEngineer: Handles XML-based prompt files and system prompt generation.

This component provides functionality for:
- Parsing XML prompt files using MRO (Method Resolution Order)
- Section-level inheritance with file-based prompts
- Generating system prompts from templates
- Formatting agent/resource/workflow descriptions
- Locale and environment information
"""

from datetime import datetime
import locale
import os
import platform
import re
import sys

from dana.common.llm.debug_logger import get_debug_logger
from dana.common.llm.types import LLMMessage
from dana.common.observable import observable
from dana.core.agent.star_agent import BaseSTARAgent
from dana.core.agent.timeline import Timeline


class PromptFormatter:
    """Formats prompt sections into different output formats (XML, Markdown, JSON)."""

    @staticmethod
    def format_section(tag: str, content: str, format_type: str = "xml", indent_spaces: int = 2, level: int = 0) -> str:
        """
        Format a prompt section in the specified format.

        Args:
            tag: Section tag name (e.g., "IDENTITY", "CONSTRAINT")
            content: Section content
            format_type: Output format - "xml", "markdown", "json", "minified_xml", "minified_json"
            indent_spaces: Number of spaces per indentation level
            level: Current indentation level

        Returns:
            Formatted section string
        """
        if not content or not content.strip():
            return ""

        indent = " " * (indent_spaces * level)

        if format_type == "xml":
            return f"{indent}<{tag}>\n{content}\n{indent}</{tag}>"
        elif format_type == "minified_xml":
            content_single_line = " ".join(content.split())
            return f"<{tag}>{content_single_line}</{tag}>"
        elif format_type == "markdown":
            # Convert tag to markdown heading
            heading_level = min(level + 1, 6)  # Max heading level is 6
            heading = "#" * heading_level
            formatted_content = PromptFormatter._indent_lines(content, indent_spaces, level + 1)
            return f"{indent}{heading} {tag}\n\n{formatted_content}"
        elif format_type == "json":
            # Return as dict entry (caller will assemble into JSON)
            return content.strip()
        elif format_type == "minified_json":
            # Minified version - single line
            return " ".join(content.split())
        else:
            # Default to XML
            return f"{indent}<{tag}>\n{content}\n{indent}</{tag}>"

    @staticmethod
    def _indent_lines(text: str, spaces: int, level: int) -> str:
        """Indent all lines in text by the specified amount."""
        if not text:
            return ""
        indent = " " * (spaces * level)
        lines = text.split("\n")
        return "\n".join(f"{indent}{line}" if line.strip() else "" for line in lines)

    @staticmethod
    def format_list(items: list[str], format_type: str = "xml", indent_spaces: int = 2, level: int = 0) -> str:
        """
        Format a list of items in the specified format.

        Args:
            items: List of items to format
            format_type: Output format
            indent_spaces: Number of spaces per indentation level
            level: Current indentation level

        Returns:
            Formatted list string
        """
        if not items:
            return "None"

        indent = " " * (indent_spaces * level)

        if format_type in ("xml", "minified_xml"):
            return "\n".join(f"{indent}- {item}" for item in items)
        elif format_type == "markdown":
            return "\n".join(f"{indent}- {item}" for item in items)
        elif format_type in ("json", "minified_json"):
            # Return as JSON array
            import json

            minify = format_type == "minified_json"
            separator = "" if minify else " "
            indent_str = None if minify else indent_spaces * (level + 1)
            return json.dumps(items, indent=indent_str, separators=("," + separator, ":" + separator))
        else:
            return "\n".join(f"{indent}- {item}" for item in items)

    @staticmethod
    def format_dict(data: dict, format_type: str = "xml", indent_spaces: int = 2, level: int = 0) -> str:
        """
        Format a dictionary in the specified format.

        Args:
            data: Dictionary to format
            format_type: Output format
            indent_spaces: Number of spaces per indentation level
            level: Current indentation level

        Returns:
            Formatted dictionary string
        """
        if not data:
            return ""

        import json

        if format_type in ("json", "minified_json"):
            minify = format_type == "minified_json"
            separator = "" if minify else " "
            indent_str = None if minify else indent_spaces
            return json.dumps(data, indent=indent_str, separators=("," + separator, ":" + separator))
        elif format_type == "markdown":
            # Format as markdown list
            indent = " " * (indent_spaces * level)
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    lines.append(f"{indent}**{key}**:")
                    nested = PromptFormatter.format_dict(value, format_type, indent_spaces, level + 1)
                    lines.append(nested)
                elif isinstance(value, list):
                    lines.append(f"{indent}**{key}**:")
                    nested = PromptFormatter.format_list(value, format_type, indent_spaces, level + 1)
                    lines.append(nested)
                else:
                    lines.append(f"{indent}**{key}**: {value}")
            return "\n".join(lines)
        else:  # XML format
            indent = " " * (indent_spaces * level)
            lines = []
            for key, value in data.items():
                if isinstance(value, dict):
                    nested = PromptFormatter.format_dict(value, format_type, indent_spaces, level + 1)
                    lines.append(f"{indent}<{key}>\n{nested}\n{indent}</{key}>")
                elif isinstance(value, list):
                    nested = PromptFormatter.format_list(value, format_type, indent_spaces, level + 1)
                    lines.append(f"{indent}<{key}>\n{nested}\n{indent}</{key}>")
                else:
                    lines.append(f"{indent}<{key}>{value}</{key}>")
            return "\n".join(lines)


class PromptEngineer:
    """Component providing XML-based prompt files with section-level inheritance."""

    # Compiled regex pattern for tag extraction (performance optimization)
    _START_TAG_PATTERN = re.compile(r"<(\w+)>")

    def __init__(self, agent: BaseSTARAgent):
        """
        Initialize the component with a reference to the agent.

        Args:
            agent: The agent instance this component belongs to
        """
        self._agent = agent
        # Cache for raw prompt content (text)
        self._raw_content_cache = None
        # Cache for extracted sections
        self._section_cache = {}
        # File-based prompt support
        self._prompt_file_path = None
        self._file_mtime = None

    def reset(self) -> None:
        """Reset the prompt engineer."""
        self._raw_content_cache = None
        self._section_cache = {}
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
        project_root = self._find_library_root()
        return os.path.join(project_root, "lib", "prompts", f"{class_name}.xml")

    def _get_core_prompt_file(self, class_name: str) -> str:
        """Get core/prompts file path."""
        project_root = self._find_library_root()
        return os.path.join(project_root, "core", "prompts", f"{class_name}.xml")

    def _get_co_located_prompt_file(self, class_name: str) -> str:
        """Get co-located prompt file path - searches multiple locations relative to agent file."""
        module_name = self._agent.__class__.__module__
        module = sys.modules[module_name]
        module_file = module.__file__
        if module_file is None:
            return ""

        module_dir = os.path.dirname(module_file)

        # Try multiple extensions
        extensions = [".xml", ".prt"]

        # Priority 1: Same directory as agent .py
        for ext in extensions:
            path = os.path.join(module_dir, f"{class_name}{ext}")
            if os.path.exists(path):
                return path

        # Priority 2: Under prompts/ subdirectory
        for ext in extensions:
            path = os.path.join(module_dir, "prompts", f"{class_name}{ext}")
            if os.path.exists(path):
                return path

        # Priority 3+: Walk up directories looking for prompts/ folder
        # Stop at project root (look for pyproject.toml, setup.py, or git root)
        current_dir = module_dir
        for _ in range(10):  # Max 10 levels up
            parent_dir = os.path.dirname(current_dir)
            if parent_dir == current_dir:  # Reached filesystem root
                break

            # Check for prompts/ in parent
            for ext in extensions:
                path = os.path.join(parent_dir, "prompts", f"{class_name}{ext}")
                if os.path.exists(path):
                    return path

            # Stop if we hit a project root marker
            if (
                os.path.exists(os.path.join(parent_dir, "pyproject.toml"))
                or os.path.exists(os.path.join(parent_dir, "setup.py"))
                or os.path.exists(os.path.join(parent_dir, ".git"))
            ):
                break

            current_dir = parent_dir

        return ""

    def _find_library_root(self) -> str:
        """Find dana library root (not agent project root) by looking for pyproject.toml or setup.py."""
        module_name = self.__class__.__module__
        depth = module_name.count(".")

        module = sys.modules[module_name]
        module_file = module.__file__
        if module_file is None:
            return os.getcwd()
        current_dir = os.path.dirname(module_file)

        for _ in range(depth - 1):
            current_dir = os.path.dirname(current_dir)

        return current_dir

    def _load_file_content(self, file_path: str) -> str:
        """Load raw text content from a single .xml file."""
        if not file_path or not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, encoding="utf-8") as f:
                return f.read()
        except OSError:
            return ""

    def _load_inherited_prompt_content(self) -> str:
        """Load and concatenate prompt files from inheritance chain (parent to child)."""
        # Get the Method Resolution Order (MRO) for inheritance support
        class_names = [cls.__name__ for cls in self._agent.__class__.__mro__ if issubclass(cls, BaseSTARAgent)]
        content_parts = []

        # Process classes in REVERSE MRO order (parent -> child)
        # Child sections will appear later in text, so searches find child version first
        for class_name in reversed(class_names):
            # Try to find a prompt file for this class (in priority order)
            user_prompt_file = self._get_user_prompt_file(class_name)
            if user_prompt_file and os.path.exists(user_prompt_file):
                content = self._load_file_content(user_prompt_file)
                if content:
                    content_parts.append(content)
                continue

            lib_prompt_file = self._get_lib_prompt_file(class_name)
            if lib_prompt_file and os.path.exists(lib_prompt_file):
                content = self._load_file_content(lib_prompt_file)
                if content:
                    content_parts.append(content)
                continue

            core_prompt_file = self._get_core_prompt_file(class_name)
            if core_prompt_file and os.path.exists(core_prompt_file):
                content = self._load_file_content(core_prompt_file)
                if content:
                    content_parts.append(content)
                continue

            co_located_file = self._get_co_located_prompt_file(class_name)
            if co_located_file and os.path.exists(co_located_file):
                content = self._load_file_content(co_located_file)
                if content:
                    content_parts.append(content)

        # Join with newlines; when searching, later sections override earlier ones
        return "\n\n".join(content_parts)

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
        """
        Extract a section by tag name using direct text search.
        Supports nested tags automatically. Results are cached.
        """
        # Check cache first
        cache_key = f"{tag}:{show_tag}"
        if cache_key in self._section_cache:
            return self._section_cache[cache_key]

        # Extract from raw content
        content = self._extract_section_from_text(self._prompt_content, tag)

        if not content:
            self._section_cache[cache_key] = ""
            return ""

        # Format with tags if requested
        if show_tag:
            if isinstance(show_tag, str):
                content = f"<{show_tag}>\n{content}\n</{show_tag}>"
            else:
                content = f"<{tag}>\n{content}\n</{tag}>"

        self._section_cache[cache_key] = content
        return content

    def _extract_section_from_text(self, content: str, target_tag: str) -> str:
        """
        Extract a section by searching for start/end tags in raw text.
        Tolerant of missing end tags (uses next tag or EOF).
        Searches recursively for nested tags.
        """
        # Look for the opening tag
        start_pattern = f"<{target_tag}>"
        start_pos = content.rfind(start_pattern)  # Use rfind to get last occurrence (child overrides parent)

        if start_pos == -1:
            # Not found at top level - try as nested tag
            return self._search_nested_tag(content, target_tag)

        tag_start = start_pos + len(start_pattern)

        # Look for matching closing tag
        end_pattern = f"</{target_tag}>"
        end_pos = content.find(end_pattern, tag_start)

        if end_pos != -1:
            # Found closing tag
            return content[tag_start:end_pos].strip()

        # No closing tag - find next opening tag or EOF (tolerant parsing)
        next_tag = self._START_TAG_PATTERN.search(content, tag_start)
        if next_tag:
            return content[tag_start : next_tag.start()].strip()

        # No more tags - take rest of content
        return content[tag_start:].strip()

    def _search_nested_tag(self, content: str, target_tag: str) -> str:
        """
        Search for a tag that's nested inside other tags.
        E.g., find CONTEXT_INSTRUCTIONS inside CONTEXT.
        """
        # Search for target tag anywhere in content (use rfind for last occurrence)
        pattern = f"<{target_tag}>"
        pos = content.rfind(pattern)

        if pos == -1:
            return ""

        tag_start = pos + len(pattern)
        end_pattern = f"</{target_tag}>"
        end_pos = content.find(end_pattern, tag_start)

        if end_pos != -1:
            return content[tag_start:end_pos].strip()

        # Tolerant: find next tag
        next_tag = self._START_TAG_PATTERN.search(content, tag_start)
        if next_tag:
            return content[tag_start : next_tag.start()].strip()

        return content[tag_start:].strip()

    @property
    def _prompt_content(self) -> str:
        """Get the raw prompt content (cached) - file-based with section-level inheritance."""
        if self._raw_content_cache is None:
            # Load raw text from all prompt files in inheritance chain
            self._raw_content_cache = self._load_inherited_prompt_content()

        return self._raw_content_cache

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
        """
        return f"""
{self._get_system_first_word_section()}

{self._get_preamble_section()}

{self._get_constraint_section()}

{self._get_identity_section()}

{self._get_decision_tree_section()}

{self._get_examples_section()}

{self._get_available_tools_section()}

{self._get_postscript_section()}

{self._get_system_last_word_section()}
""".strip()

    # ============================================================================
    # SYSTEM PROMPT SECTION METHODS
    # ============================================================================

    def _get_system_first_word_section(self) -> str:
        """Get the system first word section."""
        return self._get_prompt_section_for_tag("SYSTEM_FIRST_WORD", show_tag=False)

    def _get_system_last_word_section(self) -> str:
        """Get the system last word section."""
        return self._get_prompt_section_for_tag("SYSTEM_LAST_WORD", show_tag=False)

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

    def _get_available_tools_section(self) -> str:
        """Get the available tools section (combined agents, resources, workflows)."""
        return f"""<AVAILABLE_TOOLS>
{self._prt_agent_descriptions}
{self._prt_resource_descriptions}
{self._prt_workflow_descriptions}
</AVAILABLE_TOOLS>"""

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
        descriptions = []
        for a in agents:
            desc = a.public_description
            # If using text_flattened format, desc already has hyphens
            descriptions.append(f"- {a.agent_type} (ID: {a.object_id}): {desc}")
        return "\n".join(descriptions)

    @property
    def _prt_resource_descriptions(self) -> str:
        """Get descriptions of available resources."""
        resources = self._agent.available_resources
        if not resources or len(resources) == 0:
            return "None"
        # return "\n".join([f"- {r.resource_type} (ID: {r.object_id}): {r.public_description}" for r in resources]
        descriptions = []
        for r in resources:
            desc = r.public_description
            # If using text_flattened format, don't add extra hyphen prefix
            if desc.startswith("- "):
                descriptions.append(desc)
            else:
                descriptions.append(f"- {desc}")
        return "\n".join(descriptions)

    @property
    def _prt_workflow_descriptions(self) -> str:
        """Get workflow descriptions."""
        workflows = self._agent.available_workflows
        if not workflows or len(workflows) == 0:
            return "None"
        # return "\n".join([f"- {w.workflow_type} (ID: {w.object_id}): {w.public_description}" for w in workflows])
        descriptions = []
        for w in workflows:
            desc = w.public_description
            # If using text_flattened format, don't add extra hyphen prefix
            if desc.startswith("- "):
                descriptions.append(desc)
            else:
                descriptions.append(f"- {desc}")
        return "\n".join(descriptions)

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

            # Get user information
            try:
                username = os.getenv("USER") or os.getenv("USERNAME") or "Unknown"
            except Exception:
                username = "Unknown"

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
            # locale_info.append(f"Python: {python_version}")
            locale_info.append(f"User: {username}")
            # locale_info.append(f"Shell: {shell}")
            # locale_info.append(f"Home Directory: {home_dir}")
            # locale_info.append(f"Working Directory: {working_dir}")
            locale_info.append(f"Location: {location}")

            return "\n".join(locale_info)

        except Exception as e:
            return f"Locale information unavailable: {str(e)}"

    @observable
    def build_llm_request(self, timeline: Timeline) -> list[LLMMessage]:
        """Build LLM messages for the agent using the Timeline's LLM conversion API."""
        messages = []

        # System prompt - use the sophisticated prompt from components
        system_prompt = self._get_system_prompt()
        messages.append(LLMMessage(role="system", content=system_prompt))

        # Use Timeline's LLM conversion with latest user message separation
        if timeline:
            # Get timeline messages with latest user separation
            timeline_messages = timeline.to_llm_messages(separate_latest_user=True)

            # Check if we have a latest user message (last message should be user role)
            if timeline_messages and timeline_messages[-1].role == "user":
                # Separate context from latest user message
                context_messages = timeline_messages[:-1]
                latest_user_message = timeline_messages[-1]

                # Wrap context in structured format if we have context
                if context_messages:
                    timeline_lines = [
                        "<CONTEXT>",
                        self._get_prompt_section_for_tag("CONTEXT_INSTRUCTIONS", show_tag=False),
                        "<TIMELINE>",
                    ]
                    for msg in context_messages:
                        timeline_lines.append(f"<ENTRY>{msg.content}</ENTRY>")
                    timeline_lines.extend(["</TIMELINE>", "</CONTEXT>"])
                    timeline_content = "\n".join(timeline_lines)
                    messages.append(LLMMessage(role="assistant", content=timeline_content))

                # Add latest user message as separate user message
                messages.append(latest_user_message)
            else:
                # No latest user message, use all timeline messages
                messages.extend(timeline_messages)

        # Hack: put the user state/locale here for now
        state_info = ["<STATE_INFO>", "The current state of the user is as follows:", self._get_state_info_section(), "</STATE_INFO>"]
        state_info_content = "\n".join(state_info)
        messages.append(LLMMessage(role="user", content=state_info_content))

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
