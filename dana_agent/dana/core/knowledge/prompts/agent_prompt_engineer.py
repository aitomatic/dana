import inspect
from typing import TYPE_CHECKING, override

from dana.common.storage import AbstractStorage
from dana.common.utils.misc import Misc

from .base_prompt_engineer import BasePromptEngineer
from .codecs import AbstractCodec, CSXMLCodec


if TYPE_CHECKING:
    from dana.core.agent.base_agent import BaseAgent


class AgentPromptEngineer(BasePromptEngineer):
    """
    Prompt engineer for agents that formats the query method.
    
    Uses the configured codec (CSXMLCodec or KLXMLCodec) to format the
    query method into the appropriate XML format.
    """

    def __init__(
        self,
        component: "BaseAgent",
        storage: AbstractStorage | None = None,
        codec: type[AbstractCodec] | None = None,
        force_generate: bool = False,
        check_conflicts: bool = False,
        **kwargs
    ):
        """
        Initialize the AgentPromptEngineer.
        
        Args:
            component: The agent component to generate prompts for
            storage: Storage instance (optional)
            codec: Codec class to use (optional, defaults to CSXMLCodec)
            force_generate: Whether to force regeneration
            check_conflicts: Whether to check for conflicts
        """
        # Default to CSXMLCodec if not provided
        codec = codec if codec is not None else CSXMLCodec
        super().__init__(component, storage, codec, force_generate, check_conflicts)
        # Store codec class for use in construct_prompt
        self._codec = codec

    @override
    def construct_prompt(self) -> str:
        """
        Construct the prompt for the agent by formatting the query method.
        
        Returns:
            Formatted prompt string with the query method using the configured codec
        """
        # Extract agent description from docstring
        agent_class = self._component.__class__
        agent_description = self._extract_agent_description(agent_class)
        
        # Find query method directly (not decorated with @tool_use)
        query_method = getattr(agent_class, 'query', None)
        
        if query_method is None:
            # No query method found - return just the description
            return agent_description or ""
        
        # Parse query method signature
        signature = Misc.parse_method_signature(query_method)
        
        # Use codec to format the method signature
        formatted = self._codec.construct(signature)
        
        # Combine agent description and formatted query method
        prompt_parts = []
        if agent_description:
            prompt_parts.append(agent_description)
            prompt_parts.append("")  # Empty line separator
        
        prompt_parts.append(formatted)
        
        return "\n".join(prompt_parts)
    
    def _extract_agent_description(self, agent_class) -> str:
        """
        Extract agent description from class docstring.
        
        Args:
            agent_class: The agent class
            
        Returns:
            Agent description string
        """
        docstring = inspect.getdoc(agent_class)
        if not docstring:
            return f"{agent_class.__name__} agent."
        
        # Parse docstring sections
        sections = Misc.parse_docstring_sections(docstring)
        description = sections.get('description', '')
        
        if description:
            # Get first paragraph
            first_para = description.split('\n\n')[0].strip()
            return first_para
        
        return f"{agent_class.__name__} agent."

    @override
    def check_conflicts(self) -> bool:
        """
        Check for conflicts in the agent prompt.
        
        Agents only have one method (query), so no conflicts are possible.
        
        Returns:
            Always returns False (no conflicts possible)
        """
        return False

