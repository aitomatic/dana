"""
Physical Ontology Agent - A STAR agent for physical ontology extraction.

This agent specializes in extracting and analyzing physical ontologies from
images, diagrams, and documents using AI vision capabilities.
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


class PhysicalOntologyAgent(STARAgent):
    """
    STAR Agent specialized for physical ontology extraction.

    This agent has access to:
    - SkillResource: To discover and invoke skills (like extract-image)
    - BashResource: To execute skill scripts

    Example usage:
        agent = PhysicalOntologyAgent(llm_provider="anthropic", model="claude-sonnet-4-20250514")
        result = agent.query(message="Extract text from /path/to/diagram.png")
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
        Initialize the Physical Ontology Agent.

        Args:
            agent_id: Unique identifier for this agent instance.
                     Defaults to "physical-ontology-001".
            llm_provider: LLM provider name (e.g., 'anthropic', 'openai').
            model: Model name to use (e.g., 'claude-sonnet-4-20250514').
            **kwargs: Additional arguments passed to STARAgent.
        """
        super().__init__(
            agent_type="physical-ontology",
            agent_id=agent_id or "physical-ontology-001",
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
    agent = PhysicalOntologyAgent(llm_provider="openai", model="gpt-5", enable_assistant=False)
    result = agent.converse(
        initial_message="Extract all rooms and equipments from the image : /Users/lam/Desktop/repos/opendxa/examples/agents/physical_ontology_agent/data/p1_b11b52a9bc1f042e.png and help us create a physical ontology for the building"
    )
    # result = agent.converse(
    #     initial_message="Compute the average of 5 US cities current temperatures, weighted by number of letters in each city"
    # )
    print(result)
