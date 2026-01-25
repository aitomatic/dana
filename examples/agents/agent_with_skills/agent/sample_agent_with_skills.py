"""
Sample Agent with Skills - A STAR agent demonstrating Dana's skill system.

This example shows how to create an agent with custom skills that can be
invoked via the DanaSkillResource.
"""

from dotenv import load_dotenv

load_dotenv()

from pathlib import Path
from typing import Any

from dana.core.agent.star_agent import STARAgent
from dana.core.resource.bash import BashResource
from dana.core.resource.file_io_resource import FileIOResource
from dana.core.resource.file_edit_resource import FileEditResource
from dana.core.resource.search_resource import SearchResource
from dana.core.skills.dana_skills import SkillLoader, DanaSkillResource
from dana.core.knowledge.prompts.codecs import CSXMLCodec, AbstractCodec, NativeToolsCodec
from dana.core.resource.todo_resource import ToDoResource


class SampleAgent(STARAgent):
    """
    Sample STAR Agent demonstrating the Dana skill system.

    This agent has access to:
    - DanaSkillResource: To discover and invoke custom skills
    - BashResource: To execute skill scripts
    - FileIOResource, FileEditResource: For file operations
    - SearchResource: For search capabilities

    Example usage:
        agent = SampleAgent(llm_provider="anthropic", model="claude-sonnet-4-20250514")
        result = agent.converse(initial_message="Search the web for Python best practices")
    """

    def __init__(
        self,
        agent_id: str | None = None,
        llm_provider: str | None = None,
        model: str | None = None,
        codec: type[AbstractCodec] = CSXMLCodec,
        max_context_tokens: int = 100000,
        enable_skills: bool = False,
        **kwargs: Any,
    ):
        """
        Initialize the Sample Agent with Skills.

        Args:
            agent_id: Unique identifier for this agent instance.
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai').
            model: Model name to use (e.g., 'claude-sonnet-4-20250514', 'gpt-4o').
            codec: Codec for tool encoding (CSXMLCodec or NativeToolsCodec).
            max_context_tokens: Maximum context window size.
            enable_skills: Whether to enable skill discovery.
            **kwargs: Additional arguments passed to STARAgent.
        """
        super().__init__(
            agent_type="sample-agent-with-skills",
            agent_id=agent_id or "sample-agent-with-skills-001",
            llm_provider=llm_provider,
            model=model,
            codec=codec,
            max_context_tokens=max_context_tokens,
            enable_skills=enable_skills,
            **kwargs,
        )

        # Custom skill directory for this agent (relative to this file's location)
        skill_dirs = [Path(__file__).parent.parent / ".dana" / "skills"]
        skill_loader = SkillLoader(skill_dirs=skill_dirs)

        # Agent needs both SkillResource (to discover/invoke skills)
        # and BashResource (to execute skill scripts)
        # Pass agent=self to SkillResource to enable fork mode (subagent creation)
        self.with_resources(
            ToDoResource(resource_id="todo"),
            DanaSkillResource(skill_loader=skill_loader, agent=self, resource_id="skills"),
            BashResource(resource_id="bash"),
            FileIOResource(resource_id="file-io"),
            FileEditResource(resource_id="file-edit"),
            SearchResource(resource_id="search"),
        )


if __name__ == "__main__":
    codec = CSXMLCodec
    codec = NativeToolsCodec
    # Skills work with both NativeToolsCodec and CSXMLCodec
    agent = SampleAgent(llm_provider="openai", model="gpt-4o", enable_assistant=False, codec=codec)

    # Example 1: Web search (uses web-search-openai skill)
    result = agent.converse(
        initial_message="Compute the average of 5 US cities current temperatures, weighted by number of letters in each city"
    )
    print(result)

    # Example 2: Image extraction (uses extract-image skill)
    # Uncomment and set a valid image path to test
    # image_path = "/path/to/your/diagram.png"
    # result = agent.converse(
    #     initial_message=f"Extract all rooms and equipment from the image: {image_path}"
    # )
